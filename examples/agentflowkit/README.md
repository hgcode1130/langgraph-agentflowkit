# AgentFlowKit demo

Run the deterministic demo without any model API key:

```bash
PYTHONPATH=../../libs/agentflowkit python planner_react_demo.py
```

The demo shows:

- Template-based planning.
- Skill/tool registration.
- Capability-aware model routing.
- ReAct-style thought/action/observation trace.
- Final workflow result aggregation.

## Optional Grok/OpenAI-compatible tests

AgentFlowKit can call a real Grok/xAI-compatible chat endpoint through the
OpenAI-compatible `/chat/completions` shape. Configure it with environment
variables:

```bash
export AGENTFLOWKIT_OPENAI_BASE_URL="https://api.x.ai/v1"
export AGENTFLOWKIT_OPENAI_API_KEY="your-key"
export AGENTFLOWKIT_OPENAI_MODEL="grok-4.3-high"
```

If your gateway exposes a different model id, set that exact id, for example
`grok-4.30-high`.

Smoke test:

```bash
python grok_smoke_test.py
```

Dynamic planner demo:

```bash
python grok_llm_planner_demo.py
```

Missing keys or provider errors are raised explicitly.
