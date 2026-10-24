import json

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.agent_tools import execute_tool, tool_schemas
from backend.config import Settings
from backend.database import MemoryRepository
from backend.models import ChatRequest, Profile
from backend.scripts.seed_demo_data import seed_repository
from backend.services.agent_service import AgentService
from backend.services.llm_service import LLMService, LLMUnavailable, SYSTEM_PROMPT


def test_mock_chat_is_labelled_and_uses_only_database(client, app, headers, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline mock mode must not make an HTTP request")
    monkeypatch.setattr(httpx.Client, "post", forbidden)
    response = client.post("/api/agent/chat", headers=headers, json={"message": "Recommend internships and explain the match"})
    assert response.status_code == 200
    result = response.json()
    assert result["mode"] == "mock" and result["mock"] is True
    assert "Mock AI mode" in result["message"]
    known_ids = {record["id"] for record in app.state.repository.find("internships")}
    assert {item["internship"]["id"] for item in result["recommendations"]} <= known_ids
    assert result["tool_calls"][0]["tool"] == "explain_recommendations"


def test_skill_gap_and_compare_return_profile_based_results(client, headers, profile_data):
    client.put("/api/profile", headers=headers, json=profile_data)
    gap = client.post("/api/agent/skill-gap", headers=headers, json={"internship_id": "demo-data"})
    assert gap.status_code == 200
    assert gap.json()["matched_skills"] == ["Python"]
    assert gap.json()["missing_skills"] == ["SQL", "Excel"]
    assert len(gap.json()["learning_plan"]) == 2
    comparison = client.post("/api/agent/compare", headers=headers, json={"internship_ids": ["demo-python", "demo-data"]})
    assert comparison.status_code == 200
    assert comparison.json()["best_match_id"] == "demo-python"
    assert len(comparison.json()["comparisons"]) == 2


@pytest.mark.parametrize("path,payload,status", [
    ("chat", {"message": "  "}, 422),
    ("chat", {"message": "compare", "internship_ids": ["demo-python", "demo-python"]}, 422),
    ("chat", {"message": "details", "internship_ids": ["not-real"]}, 404),
    ("compare", {"internship_ids": ["demo-python"]}, 422),
    ("compare", {"internship_ids": ["demo-python", "demo-python"]}, 422),
    ("compare", {"internship_ids": ["demo-python", "not-real"]}, 404),
    ("skill-gap", {"internship_id": "not-real"}, 404),
    ("skill-gap", {"internship_id": {"$ne": None}}, 422),
])
def test_agent_rejects_invalid_inputs(client, headers, path, payload, status):
    assert client.post(f"/api/agent/{path}", headers=headers, json=payload).status_code == status


def test_chat_uses_selected_skills_and_compare_tools(client, headers):
    response = client.post("/api/agent/chat", headers=headers, json={"message": "Show my skill gap", "internship_ids": ["demo-python"]})
    assert "skill_analysis" in [entry["tool"] for entry in response.json()["tool_calls"]]
    response = client.post("/api/agent/chat", headers=headers, json={"message": "Compare these", "internship_ids": ["demo-python", "demo-data"]})
    assert "compare_internships" in [entry["tool"] for entry in response.json()["tool_calls"]]


def test_rate_limit_is_shared_across_ai_endpoints(client, app, headers):
    app.state.rate_limiter.limit = 2
    assert client.post("/api/agent/chat", headers=headers, json={"message": "Help"}).status_code == 200
    assert client.post("/api/agent/skill-gap", headers=headers, json={"internship_id": "demo-python"}).status_code == 200
    response = client.post("/api/agent/compare", headers=headers, json={"internship_ids": ["demo-python", "demo-data"]})
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0
    assert client.get("/api/recommendations", headers=headers).status_code == 200


def test_tools_reject_unknown_names_untrusted_scope_and_invalid_types():
    repo = MemoryRepository()
    seed_repository(repo)
    profile = Profile()
    with pytest.raises(ValueError, match="Unknown tool"):
        execute_tool("delete_database", {}, repo, profile)
    for arguments in ({"limit": 1000}, {"query": {"$ne": None}}, {"user_id": "other-user"}, {"include_expired": True}):
        with pytest.raises(ValidationError):
            execute_tool("search_internships", arguments, repo, profile)
    with pytest.raises(HTTPException) as error:
        execute_tool("internship_details", {"internship_id": "nonexistent"}, repo, profile)
    assert error.value.status_code == 404
    schemas = tool_schemas()
    assert len(schemas) == 5
    assert all(schema["function"]["parameters"]["additionalProperties"] is False for schema in schemas)


def test_openai_compatible_http_integration_uses_official_request_shape():
    def handler(request):
        assert str(request.url) == "https://api.openai.com/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-not-real"
        payload = json.loads(request.content)
        assert payload["store"] is False
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["role"] == "user"
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": '{"guidance":"Build a project."}'}}]})
    service = LLMService(Settings(openai_api_key="test-not-real"), transport=httpx.MockTransport(handler))
    message = service.complete([{"role": "user", "content": "Help"}])
    assert service.parse_guidance(message) == "Build a project."


def test_groq_openai_compatible_http_integration():
    def handler(request):
        assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer groq-test"
        payload = json.loads(request.content)
        assert payload["model"] == "openai/gpt-oss-120b"
        assert "response_format" not in payload
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": '{"guidance":"Use Groq."}'}}]})

    settings = Settings(groq_api_key="groq-test", llm_mode="groq")
    service = LLMService(settings, transport=httpx.MockTransport(handler))
    message = service.complete([{"role": "user", "content": "Help"}])
    assert service.parse_guidance(message) == "Use Groq."


def test_gemini_http_integration_uses_generate_content_shape():
    def handler(request):
        assert str(request.url) == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
        assert request.headers["x-goog-api-key"] == "test-not-real"
        payload = json.loads(request.content)
        assert payload["systemInstruction"]["parts"][0]["text"]
        assert payload["tools"][0]["functionDeclarations"]
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"guidance":"Build a project."}'}]}}]})

    settings = Settings(gemini_api_key="test-not-real", llm_mode="gemini")
    service = LLMService(settings, transport=httpx.MockTransport(handler))
    message = service.complete([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "Help"}], tools=tool_schemas())
    assert service.parse_guidance(message) == "Build a project."


def test_auto_mode_falls_back_from_openai_to_gemini():
    def handler(request):
        if "/chat/completions" in str(request.url):
            return httpx.Response(429, json={"error": {"message": "quota"}})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"guidance":"Use Gemini."}'}]}}]})

    settings = Settings(openai_api_key="openai-test", gemini_api_key="gemini-test", llm_mode="auto")
    service = LLMService(settings, transport=httpx.MockTransport(handler))
    message = service.complete([{"role": "user", "content": "Help"}])
    assert service.mode == "gemini"
    assert service.parse_guidance(message) == "Use Gemini."


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"message": None}]}])
def test_provider_invalid_response_is_safe(body):
    service = LLMService(Settings(openai_api_key="test-not-real"), transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
    with pytest.raises(LLMUnavailable):
        service.complete([])


def test_provider_failure_is_labelled_mock_with_real_results(settings):
    repo = MemoryRepository()
    seed_repository(repo)
    settings.openai_api_key = "not-real"
    settings.llm_mode = "openai"
    transport = httpx.MockTransport(lambda request: httpx.Response(503, json={"private": "provider-secret-data"}))
    result = AgentService(repo, settings, llm=LLMService(settings, transport=transport)).chat(Profile(), ChatRequest(message="Help"))
    assert result["mode"] == "mock"
    assert "provider-secret-data" not in str(result)
    assert result["warning"]
    assert result["recommendations"]


def test_real_agent_executes_validated_tools_and_rejects_hallucinated_ids(settings):
    calls = []
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                {"id": "tool-1", "type": "function", "function": {"name": "internship_details", "arguments": '{"internship_id":"imaginary-id"}'}}
            ]}}]})
        assert "Invalid tool request" in body["messages"][-1]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": '{"guidance":"Practice the skills in your learning plan."}'}}]})
    repo = MemoryRepository()
    seed_repository(repo)
    settings.openai_api_key = "test-not-real"
    settings.llm_mode = "openai"
    result = AgentService(repo, settings, llm=LLMService(settings, transport=httpx.MockTransport(handler))).chat(
        Profile(full_name="Private Student", bio="private bio"), ChatRequest(message="Help"))
    assert result["mode"] == "openai"
    assert len(calls) == 2
    assert "Private Student" not in json.dumps(calls)
    assert "private bio" not in json.dumps(calls)
    assert "imaginary-id" not in result["message"]
    assert all(entry["arguments"].get("internship_id") != "imaginary-id" for entry in result["tool_calls"])


@pytest.mark.parametrize("content", ["not json", "{}", '{"guidance":12}', '{"guidance":"ok","invented_internships":[]}'])
def test_invalid_generated_guidance_is_rejected(content):
    with pytest.raises(LLMUnavailable):
        LLMService.parse_guidance({"content": content})


@pytest.mark.parametrize("calls", ["invalid", [None], [{"id": 12}], [{"function": {}}]])
def test_malformed_provider_tool_calls_fall_back_safely(settings, calls):
    settings.openai_api_key = "not-real"
    settings.llm_mode = "openai"
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        "choices": [{"message": {"role": "assistant", "tool_calls": calls}}]}))
    repo = MemoryRepository()
    result = AgentService(repo, settings, llm=LLMService(settings, transport=transport)).chat(Profile(), ChatRequest(message="Help"))
    assert result["mode"] == "mock"
    assert result["warning"]
    assert result["recommendations"] == []
