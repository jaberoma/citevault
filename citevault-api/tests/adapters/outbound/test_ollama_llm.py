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
def test_complete_with_schema_sets_response_format_json_object() -> None:
    route = respx.post(_CHAT_URL).mock(
        return_value=_chat_response(json.dumps({"answer": "yes"}))
    )
    llm = OllamaLLM(base_url="http://localhost:11434", model="gemma4:e4b")
    llm.complete("Q?", schema={"type": "object", "properties": {"answer": {"type": "string"}}})
    body = json.loads(route.calls[0].request.content)
    assert body.get("response_format") == {"type": "json_object"}
