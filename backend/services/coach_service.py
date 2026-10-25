"""Student-facing coaching flows with safe deterministic fallbacks."""
import re

from backend.services.internship_service import InternshipService
from backend.services.llm_service import LLMService, LLMUnavailable
from backend.services.matching import rank_internships
from backend.services.student_plan import build_student_plan


COACH_PROMPTS = {
    "interview": """You are a careful interview coach. Review the student's answer to the supplied question.
Give concise feedback with: one strength, two improvements, and one specific practice suggestion.
Do not invent employer facts or claim the student passed an interview. Return JSON exactly as
{\"guidance\": \"feedback only\"}.""",
    "resume": """You are a careful student resume coach. Review the supplied resume text against the
student profile and target role context. Give concise, practical feedback on clarity, evidence,
skills, and project bullets. Do not invent experience, metrics, employers, or qualifications.
Return JSON exactly as {\"guidance\": \"resume feedback only\"}.""",
}


class CoachService:
    def __init__(self, repository, settings, llm=None):
        self.repository = repository
        self.llm = llm or LLMService(settings)

    def _target(self, profile, internship_id=None):
        service = InternshipService(self.repository)
        if internship_id:
            return service.get(internship_id)
        ranked = rank_internships(profile, service.search())
        return service.get(ranked[0]["internship"]["id"]) if ranked else None

    def _guidance(self, mode, profile, content, context):
        messages = [
            {"role": "system", "content": COACH_PROMPTS[mode]},
            {"role": "user", "content": str({"profile": profile.model_dump(mode="json", exclude={"full_name", "bio"}),
                                                 "context": context, "content": content})},
        ]
        try:
            return self.llm.parse_guidance(self.llm.complete(messages)), self.llm.mode, None
        except LLMUnavailable as exc:
            return None, "mock", str(exc)

    @staticmethod
    def _interview_fallback(answer):
        words = len(answer.split())
        strengths = []
        improvements = []
        if words >= 35:
            strengths.append("You gave enough detail to discuss in a real interview.")
        else:
            improvements.append("Use a short situation, action, and result instead of a one-line answer.")
        if re.search(r"\b(I|we)\b", answer, re.I):
            strengths.append("You described your own contribution.")
        else:
            improvements.append("Make your personal contribution explicit with 'I'.")
        if not re.search(r"\b(result|improv|reduc|increase|learn|measur)\w*\b", answer, re.I):
            improvements.append("End with a result, lesson, or measurable outcome.")
        return {
            "strengths": strengths or ["You attempted the question and created a starting point."],
            "improvements": improvements or ["Add one technical detail and one measurable result."],
            "practice": "Answer again in 60–90 seconds using Situation, Action, Result, and Learning.",
        }

    @staticmethod
    def _resume_checks(content):
        text = content.casefold()
        sections = {
            "education": bool(re.search(r"\beducation\b|\bdegree\b|\bb\.tech\b|\bb\.e\b", text)),
            "skills": bool(re.search(r"\bskills?\b|\bpython\b|\bjava(script)?\b|\bsql\b", text)),
            "projects": bool(re.search(r"\bprojects?\b|\bgithub\b", text)),
            "experience": bool(re.search(r"\bexperience\b|\bemployment\b|\bwork history\b|\bprofessional\b", text)),
        }
        missing = [name.title() for name, present in sections.items() if not present]
        checks = [f"{name.title()} section detected" for name, present in sections.items() if present]
        checks.extend(f"Add or clarify your {name.lower()} section" for name in missing)
        score = round(100 * sum(sections.values()) / len(sections))
        return score, checks

    def coach(self, profile, request):
        target = self._target(profile, request.internship_id)
        recommendations = []
        if target:
            recommendations = rank_internships(profile, [target])
        plan = build_student_plan(profile, recommendations)
        if request.mode == "interview":
            questions = plan["interview_questions"]
            index = request.question_index
            if request.content.casefold().strip() in {"start", "begin", "next"}:
                return {"mode": "interview", "question": questions[index], "question_index": index,
                        "next_question_index": index, "total_questions": len(questions),
                        "score": None, "feedback": None, "provider_mode": self.llm.mode,
                        "target_role": plan["target_role"]}
            score = min(100, 35 + min(35, len(request.content.split())) + (20 if re.search(r"\b(result|impact|learn)\w*\b", request.content, re.I) else 0))
            context = {"question": questions[index], "target_role": plan["target_role"], "missing_skills": plan["focus_skills"]}
            guidance, provider_mode, warning = self._guidance("interview", profile, request.content, context)
            fallback = self._interview_fallback(request.content)
            next_index = index + 1 if index + 1 < len(questions) else None
            return {"mode": "interview", "question": questions[index], "question_index": index,
                    "next_question_index": next_index, "total_questions": len(questions),
                    "score": score, "feedback": guidance or fallback, "feedback_text": guidance,
                    "provider_mode": provider_mode, "warning": warning, "target_role": plan["target_role"]}

        score, checks = self._resume_checks(request.content)
        context = {"target_role": plan["target_role"], "focus_skills": plan["focus_skills"]}
        guidance, provider_mode, warning = self._guidance("resume", profile, request.content, context)
        return {"mode": "resume", "score": score, "checks": checks,
                "feedback": guidance or "Use the detected sections as a checklist, add evidence to each project, and keep every listed skill interview-ready.",
                "provider_mode": provider_mode, "warning": warning, "target_role": plan["target_role"]}
