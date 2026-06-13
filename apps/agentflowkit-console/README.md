# AgentFlowKit Console

Lightweight local workflow console for AgentFlowKit.

## Start the API

```bash
cd apps/agentflowkit-console/api
uv sync --group dev
uv run uvicorn agentflowkit_console_api.main:app --reload --port 8000
```

## Start the web app

```bash
cd apps/agentflowkit-console/web
npm install
npm run dev
```

Open `http://localhost:5173`.

## Model configuration

The console supports deterministic local mode, DeepSeek mode, and Grok mode.
Model settings can be provided through environment variables or
`apps/agentflowkit-console/api/.env`. Environment variables take precedence.

```bash
AGENTFLOWKIT_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
AGENTFLOWKIT_DEEPSEEK_API_KEY=your-key
AGENTFLOWKIT_DEEPSEEK_MODEL=deepseek-chat

OPENAI_API_KEY=grokapi
OPENAI_BASE_URL=https://grok.11231213.xyz/v1
OPENAI_MODEL=grok-4.3
```

Do not store real API keys in source files. If a key was exposed in chat or
logs, rotate it in the DeepSeek console.
