# AgentFlowKit Console

Local web console for designing, running, and observing AgentFlowKit workflows.

Run:

```bash
cd apps/agentflowkit-console
PYTHONPATH=../.. python run_console.py
```

Open:

```text
http://127.0.0.1:8765
```

Optional Grok planner:

```bash
export AGENTFLOWKIT_OPENAI_BASE_URL="https://api.x.ai/v1"
export AGENTFLOWKIT_OPENAI_API_KEY="your-key"
export AGENTFLOWKIT_OPENAI_MODEL="grok-4.3-high"
```
