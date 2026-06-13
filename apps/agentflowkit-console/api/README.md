# AgentFlowKit Console API

FastAPI backend for the local AgentFlowKit workflow console.

## Run

```bash
uv sync --group dev
uv run uvicorn agentflowkit_console_api.main:app --reload --port 8000
```

The local mode uses deterministic skills/tools by default. DeepSeek and Grok
modes use OpenAI-compatible settings. The API reads process environment
variables first, then `apps/agentflowkit-console/api/.env`.

```bash
AGENTFLOWKIT_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
AGENTFLOWKIT_DEEPSEEK_API_KEY=your-key
AGENTFLOWKIT_DEEPSEEK_MODEL=deepseek-chat

OPENAI_API_KEY=grokapi
OPENAI_BASE_URL=https://grok.11231213.xyz/v1
OPENAI_MODEL=grok-4.3
```

Do not commit real API keys. If a key was pasted into a chat, issue tracker, or
public log, rotate it in the DeepSeek console before using it again.
