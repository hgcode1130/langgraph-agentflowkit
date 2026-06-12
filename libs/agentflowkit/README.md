# AgentFlowKit

AgentFlowKit is a LangGraph extension package for course experiments around
multi-agent workflow middleware.

It focuses on four middleware capabilities:

- Planner-worker task decomposition.
- ReAct-style tool execution.
- Skill and tool registry.
- Model routing and execution tracing.

The package is intentionally isolated from LangGraph core so it can be reviewed
or reverted without changing upstream framework behavior.

## Run

Run tests:

```bash
cd libs/agentflowkit
PYTHONPATH=. python -m pytest tests
```

Run the deterministic demo:

```bash
cd examples/agentflowkit
python planner_react_demo.py
```

The demo does not require a model API key. It uses deterministic tools and
model profiles so the workflow can be recorded in a classroom environment.

## API surface

- `TemplatePlanner`: converts a task request into explicit workflow steps.
- `ToolRegistry`: registers callable tools.
- `SkillRegistry`: registers skill handlers that can call tools.
- `CapabilityRouter`: selects a model profile by capability and complexity.
- `ExecutionTracer`: records plan, route, thought, action, observation, and finish events.
- `AgentFlow`: executes the planned workflow and returns a structured result.
