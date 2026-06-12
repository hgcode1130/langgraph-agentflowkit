from __future__ import annotations

from typing import Any, TypedDict

from agentflowkit.engine import AgentFlow
from agentflowkit.models import Plan, TaskRequest, WorkflowResult


class GraphState(TypedDict, total=False):
    request: TaskRequest
    plan: Plan
    result: WorkflowResult


def build_langgraph_workflow(flow: AgentFlow) -> Any:
    from langgraph.graph import END, StateGraph

    graph = StateGraph(GraphState)
    graph.add_node("plan", lambda state: {"plan": flow.planner.plan(state["request"])})
    graph.add_node("execute", lambda state: {"result": flow.run_plan(state["plan"])})
    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", END)
    return graph.compile()
