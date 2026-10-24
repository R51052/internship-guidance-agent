"""Bounded, read-only tool orchestration; database results always remain canonical."""
import json

from fastapi import HTTPException
from pydantic import ValidationError

from backend.agent_tools import execute_tool, tool_schemas
from backend.services.llm_service import LLMService, LLMUnavailable, SYSTEM_PROMPT


class AgentService:
    def __init__(self, repository, settings, llm=None):
        self.repository = repository
        self.llm = llm or LLMService(settings)

    def chat(self, profile, request):
        trace = []

        def run(name, arguments):
            result = execute_tool(name, arguments, self.repository, profile)
            trace.append({"tool": name, "arguments": arguments, "result": result})
            return result

        recommendations = run("explain_recommendations", {"limit": 5})["recommendations"]
        text = request.message.casefold()
        ids = request.internship_ids
        if len(ids) >= 2 and any(word in text for word in ("compare", "versus", " vs ")):
            run("compare_internships", {"internship_ids": ids})
        elif ids:
            for identifier in ids:
                run("internship_details", {"internship_id": identifier})
                if any(word in text for word in ("skill", "learn", "gap", "improve")):
                    run("skill_analysis", {"internship_id": identifier})
        elif any(word in text for word in ("skill", "learn", "gap")) and recommendations:
            run("skill_analysis", {"internship_id": recommendations[0]["internship"]["id"]})
        else:
            # Simple keyword retrieval in mock mode, with a general search otherwise.
            tokens = request.message.casefold().split()
            keyword = next((skill for skill in profile.skills if skill.casefold() in tokens), "")
            run("search_internships", {"query": keyword, "limit": 5})

        mode = self.llm.mode
        warning = None
        guidance = self.llm.mock_guidance()
        if mode in {"openai", "gemini", "groq"}:
            # Only career-relevant fields are sent, never name/email/password/session data.
            context = {"profile": profile.model_dump(mode="json", exclude={"full_name", "bio"}), "tool_results": trace}
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps({"request": request.message, "context": context})}]
            try:
                # Groq's reasoning models can emit invalid tool names when JSON
                # output and multiple function declarations are combined. The
                # deterministic tools above already gathered canonical facts,
                # so Groq receives those facts directly and only writes guidance.
                provider_tools = None if mode == "groq" else tool_schemas()
                for _ in range(3):
                    message = self.llm.complete(messages, tools=provider_tools)
                    calls = message.get("tool_calls") or []
                    if not calls:
                        guidance = self.llm.parse_guidance(message)
                        break
                    if not isinstance(calls, list) or len(calls) > 5:
                        raise LLMUnavailable("AI tool-call budget exceeded")
                    messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": calls})
                    for call in calls:
                        if not isinstance(call, dict) or not isinstance(call.get("id"), str):
                            raise LLMUnavailable("Invalid AI tool call")
                        tool_name = None
                        try:
                            function = call["function"]
                            tool_name = function["name"]
                            arguments = json.loads(function["arguments"])
                            result = run(tool_name, arguments)
                        except (KeyError, TypeError, ValueError, ValidationError, HTTPException):
                            result = {"error": "Invalid tool request; use only supplied IDs and validated arguments."}
                        messages.append({"role": "tool", "tool_call_id": call["id"],
                                         "name": tool_name or call["id"], "content": json.dumps(result)})
                else:
                    raise LLMUnavailable("AI tool-call budget exceeded")
            except LLMUnavailable as exc:
                mode = "mock"
                warning = str(exc)

        if not warning:
            mode = self.llm.mode
        summaries = []
        for entry in trace:
            result = entry["result"]
            if entry["tool"] == "skill_analysis":
                missing = result["missing_skills"]
                summaries.append(f"Skill gap for {result['internship_id']}: " +
                                 (", ".join(missing) if missing else "all listed required skills are on your profile") + ".")
            elif entry["tool"] == "compare_internships":
                summaries.append("Comparison: " + "; ".join(
                    f"{item['internship']['title']}: {item['score']:g}/100, " +
                    ("eligible" if item["eligible"] else "ineligible") for item in result["comparisons"]) + ".")
                if result["best_match_id"]:
                    summaries.append(f"Best eligible fit by score: {result['best_match_id']}.")
        if recommendations:
            facts = [f"{item['internship']['title']} at {item['internship']['company']} "
                     f"(ID {item['internship']['id']}): {item['score']:g}/100 match."
                     for item in recommendations[:3]]
            summaries.append("Database-backed matches:\n" + "\n".join(facts))
        else:
            summaries.append("No eligible internships were found in the database for your current profile.")
        database_summary = "\n\n".join(summaries)
        answer = database_summary + "\n\n" + guidance
        return {"message": answer, "answer": answer, "mode": mode, "mock": mode == "mock",
                "guidance": guidance, "database_summary": database_summary,
                "warning": warning, "recommendations": recommendations, "tool_calls": trace,
                "data_source": self.repository.mode, "is_demo": self.repository.mode == "demo"}
