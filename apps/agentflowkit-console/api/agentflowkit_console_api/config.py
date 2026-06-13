from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from agentflowkit import OpenAICompatibleChatModel, OpenAICompatibleConfig


DEEPSEEK_BASE_URL_VAR = "AGENTFLOWKIT_DEEPSEEK_BASE_URL"
DEEPSEEK_API_KEY_VAR = "AGENTFLOWKIT_DEEPSEEK_API_KEY"
DEEPSEEK_MODEL_VAR = "AGENTFLOWKIT_DEEPSEEK_MODEL"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

GROK_BASE_URL_VAR = "OPENAI_BASE_URL"
GROK_API_KEY_VAR = "OPENAI_API_KEY"
GROK_MODEL_VAR = "OPENAI_MODEL"
DEFAULT_GROK_BASE_URL = "https://grok.11231213.xyz/v1"
DEFAULT_GROK_MODEL = "grok-4.3"


@dataclass(frozen=True, kw_only=True, slots=True)
class ProviderSettings:
    provider_id: str
    label: str
    base_url: str | None
    api_key: str | None
    model: str | None

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def public_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "label": self.label,
            "configured": self.configured,
            "base_url": self.base_url,
            "api_key_configured": self.api_key_configured,
            "model": self.model,
        }


DeepSeekSettings = ProviderSettings


def deepseek_settings() -> ProviderSettings:
    return ProviderSettings(
        provider_id="deepseek",
        label="DeepSeek",
        base_url=_config_value(DEEPSEEK_BASE_URL_VAR) or DEFAULT_DEEPSEEK_BASE_URL,
        api_key=_config_value(DEEPSEEK_API_KEY_VAR),
        model=_config_value(DEEPSEEK_MODEL_VAR) or DEFAULT_DEEPSEEK_MODEL,
    )


def grok_settings() -> ProviderSettings:
    return ProviderSettings(
        provider_id="grok",
        label="Grok",
        base_url=_config_value(GROK_BASE_URL_VAR) or DEFAULT_GROK_BASE_URL,
        api_key=_config_value(GROK_API_KEY_VAR),
        model=_config_value(GROK_MODEL_VAR) or DEFAULT_GROK_MODEL,
    )


def create_deepseek_chat_model() -> OpenAICompatibleChatModel | None:
    return create_chat_model(deepseek_settings())


def create_grok_chat_model() -> OpenAICompatibleChatModel | None:
    return create_chat_model(grok_settings())


def create_chat_model(settings: ProviderSettings) -> OpenAICompatibleChatModel | None:
    if not settings.configured:
        return None
    return OpenAICompatibleChatModel(
        OpenAICompatibleConfig(
            base_url=settings.base_url or "",
            api_key=settings.api_key or "",
            model=settings.model or "",
        )
    )


def _config_value(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    return _dotenv_values().get(name)


def _dotenv_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in _dotenv_paths():
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in values:
                values[key] = value
    return values


def _dotenv_paths() -> tuple[Path, ...]:
    api_dir = Path(__file__).resolve().parents[1]
    repo_root = _find_repo_root()
    return (api_dir / ".env", repo_root / ".env")


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "AGENTS.md").exists() and (parent / "libs").exists():
            return parent
    return current.parents[1]
