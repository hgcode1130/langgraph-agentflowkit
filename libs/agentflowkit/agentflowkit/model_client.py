from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol
from urllib import request
from urllib.error import HTTPError, URLError

from agentflowkit.errors import ModelClientError

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_TEMPERATURE = 0.0


class ChatModel(Protocol):
    def complete(self, messages: tuple[dict[str, str], ...]) -> str:
        """Return model text for chat messages."""


@dataclass(frozen=True, kw_only=True, slots=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    temperature: float = DEFAULT_TEMPERATURE


class OpenAICompatibleChatModel:
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self._config = config

    @classmethod
    def from_env(
        cls,
        *,
        base_url_var: str = "AGENTFLOWKIT_OPENAI_BASE_URL",
        api_key_var: str = "AGENTFLOWKIT_OPENAI_API_KEY",
        model_var: str = "AGENTFLOWKIT_OPENAI_MODEL",
    ) -> "OpenAICompatibleChatModel":
        return cls(
            OpenAICompatibleConfig(
                base_url=_required_env(base_url_var),
                api_key=_required_env(api_key_var),
                model=_required_env(model_var),
            )
        )

    def complete(self, messages: tuple[dict[str, str], ...]) -> str:
        body = {
            "model": self._config.model,
            "messages": list(messages),
            "temperature": self._config.temperature,
        }
        data = json.dumps(body).encode("utf-8")
        req = request.Request(
            url=self._endpoint(),
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AgentFlowKit/0.1",
            },
        )
        return _parse_chat_response(self._open(req))

    def _endpoint(self) -> str:
        return self._config.base_url.rstrip("/") + "/chat/completions"

    def _open(self, req: request.Request) -> bytes:
        try:
            with request.urlopen(req, timeout=self._config.timeout_seconds) as response:
                return response.read()
        except HTTPError as exc:
            raise ModelClientError(_http_error_message(exc)) from exc
        except URLError as exc:
            raise ModelClientError(f"Model provider connection failed: {exc}") from exc


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ModelClientError(f"Missing required environment variable: {name}")
    return value


def _parse_chat_response(raw: bytes) -> str:
    text = raw.decode("utf-8")
    if text.lstrip().startswith("data:"):
        return _parse_sse_response(text)
    try:
        payload = json.loads(text)
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ModelClientError("Model provider returned invalid chat payload") from exc
    if not isinstance(content, str) or not content.strip():
        raise ModelClientError("Model provider returned empty content")
    return content


def _parse_sse_response(text: str) -> str:
    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line.removeprefix("data:").strip()
        if chunk == "[DONE]":
            break
        parts.append(_parse_sse_chunk(chunk))
    content = "".join(parts).strip()
    if not content:
        raise ModelClientError("Model provider returned empty streamed content")
    return content


def _parse_sse_chunk(chunk: str) -> str:
    try:
        payload = json.loads(chunk)
        delta = payload["choices"][0].get("delta", {})
        content = delta.get("content", "")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ModelClientError("Model provider returned invalid stream payload") from exc
    if not isinstance(content, str):
        raise ModelClientError("Model provider returned invalid streamed content")
    return content


def _http_error_message(exc: HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    return f"Model provider HTTP {exc.code}: {body}"
