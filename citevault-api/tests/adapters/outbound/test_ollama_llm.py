"""Ollama LLM adapter tests using HTTP mocking."""

import json

import httpx
import respx

from citevault.adapters.outbound.ollama_llm import OllamaLLM

_CHAT_URL = "http://localhost:11434/v1/chat/completions"


def _chat_response(content: str) -> httpx.Response:
    return httpx.Response(200, json={
        "choices": [{"message": {"content": content}}]
    })


@respx.mock
def test_complete_calls_chat_completions_endpoint() -> None:
    route = respx.post(_CHAT_URL).mock(return_value=_chat_response("Hello back"))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    out = llm.complete("Hello?")
    assert out == "Hello back"
    assert route.called


@respx.mock
def test_complete_without_system_sends_only_user_message() -> None:
    route = respx.post(_CHAT_URL).mock(return_value=_chat_response("ok"))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    llm.complete("Hi")
    body = json.loads(route.calls[0].request.content)
    assert body["messages"] == [{"role": "user", "content": "Hi"}]


@respx.mock
def test_complete_with_system_prepends_system_message() -> None:
    route = respx.post(_CHAT_URL).mock(return_value=_chat_response("ok"))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    llm.complete("Hi", system="You are a verifier.")
    body = json.loads(route.calls[0].request.content)
    assert body["messages"] == [
        {"role": "system", "content": "You are a verifier."},
        {"role": "user", "content": "Hi"},
    ]


@respx.mock
def test_complete_with_schema_does_not_set_response_format() -> None:
    """Grammar-constrained sampling (response_format json_object) is removed because
    it causes pathological slowness with Gemma 4 when the model would return short/empty
    JSON (GitHub issue #15260). Prompt-only JSON enforcement is used instead."""
    route = respx.post(_CHAT_URL).mock(
        return_value=_chat_response(json.dumps({"answer": "yes"}))
    )
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    llm.complete("Q?", schema={"type": "object", "properties": {"answer": {"type": "string"}}})
    body = json.loads(route.calls[0].request.content)
    assert "response_format" not in body


@respx.mock
def test_complete_with_schema_strips_markdown_fences() -> None:
    """Without grammar enforcement the model may wrap JSON in markdown code fences."""
    respx.post(_CHAT_URL).mock(
        return_value=_chat_response('```json\n{"claims": []}\n```')
    )
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    result = llm.complete("Q?", schema={"type": "object"})
    assert result == '{"claims": []}'


@respx.mock
def test_complete_without_schema_does_not_strip_content() -> None:
    """Non-JSON calls (cover letter, naive résumé) must come back verbatim."""
    respx.post(_CHAT_URL).mock(return_value=_chat_response("Dear Hiring Manager,\n\n..."))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    result = llm.complete("Write a cover letter.")
    assert result == "Dear Hiring Manager,\n\n..."


@respx.mock
def test_complete_with_schema_repairs_invalid_json_escapes() -> None:
    """Model may emit bare backslashes in explanation text (e.g. \\Kubernetes path)
    that are invalid JSON escape sequences. They must be escaped before returning."""
    raw = '{"verdict": "SUPPORTS", "confidence": 0.9, "explanation": "Used \\Kubernetes on the project."}'
    respx.post(_CHAT_URL).mock(return_value=_chat_response(raw))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    result = llm.complete("Verify.", schema={"type": "object"})
    parsed = json.loads(result)
    assert parsed["explanation"] == "Used \\Kubernetes on the project."


@respx.mock
def test_complete_without_schema_does_not_repair_escapes() -> None:
    """Escape repair must not run on free-text calls."""
    raw = "Path is C:\\Users\\javi"
    respx.post(_CHAT_URL).mock(return_value=_chat_response(raw))
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    result = llm.complete("What is the path?")
    assert result == raw
