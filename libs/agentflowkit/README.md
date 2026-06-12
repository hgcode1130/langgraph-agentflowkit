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
