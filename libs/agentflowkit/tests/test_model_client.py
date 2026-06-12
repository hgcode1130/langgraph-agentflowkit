import json
from urllib.error import HTTPError, URLError

import pytest

from agentflowkit import OpenAICompatibleChatModel, OpenAICompatibleConfig
from agentflowkit.errors import ModelClientError


def test_openai_compatible_client_parses_chat_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "agentflowkit.model_client.request.urlopen",
        lambda req, timeout: FakeResponse(
            {"choices": [{"message": {"content": "hello"}}]}
        ),
    )
    client = OpenAICompatibleChatModel(
        OpenAICompatibleConfig(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="grok-test",
        )
    )

    assert client.complete(({"role": "user", "content": "hi"},)) == "hello"


def test_openai_compatible_client_parses_streamed_chat_response(monkeypatch) -> None:
    raw = (
        'data: {"choices":[{"delta":{"content":"he"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n'
        "data: [DONE]\n\n"
    ).encode("utf-8")
    monkeypatch.setattr(
        "agentflowkit.model_client.request.urlopen",
        lambda req, timeout: RawResponse(raw),
    )
    client = OpenAICompatibleChatModel(
        OpenAICompatibleConfig(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="grok-test",
        )
    )

    assert client.complete(({"role": "user", "content": "hi"},)) == "hello"


def test_openai_compatible_client_requires_env(monkeypatch) -> None:
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_MODEL", raising=False)

    with pytest.raises(ModelClientError):
        OpenAICompatibleChatModel.from_env()


def test_openai_compatible_client_exposes_http_error(monkeypatch) -> None:
    def fail(req, timeout):
        raise HTTPError(req.full_url, 401, "Unauthorized", {}, ErrorBody())

    monkeypatch.setattr("agentflowkit.model_client.request.urlopen", fail)
    client = OpenAICompatibleChatModel(
        OpenAICompatibleConfig(
            base_url="https://api.example.com/v1",
            api_key="bad-key",
            model="grok-test",
        )
    )

    with pytest.raises(ModelClientError, match="HTTP 401"):
        client.complete(({"role": "user", "content": "hi"},))


def test_openai_compatible_client_exposes_connection_error(monkeypatch) -> None:
    def fail(req, timeout):
        raise URLError("network down")

    monkeypatch.setattr("agentflowkit.model_client.request.urlopen", fail)
    client = OpenAICompatibleChatModel(
        OpenAICompatibleConfig(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="grok-test",
        )
    )

    with pytest.raises(ModelClientError, match="connection failed"):
        client.complete(({"role": "user", "content": "hi"},))


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class RawResponse:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self.raw


class ErrorBody:
    def read(self) -> bytes:
        return b'{"error":"bad key"}'

    def close(self) -> None:
        return None
