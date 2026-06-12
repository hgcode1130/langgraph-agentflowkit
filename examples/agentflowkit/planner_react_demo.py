from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTFLOWKIT_SRC = REPO_ROOT / "libs" / "agentflowkit"
if str(AGENTFLOWKIT_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTFLOWKIT_SRC))

from agentflowkit import (  # noqa: E402
    AgentFlow,
    AgentFlowComponents,
    CapabilityRouter,
    ModelProfile,
    SkillContext,
    SkillRegistry,
    SkillSpec,
    StepTemplate,
    TaskRequest,
    TemplatePlanner,
    ToolCall,
    ToolRegistry,
    ToolSpec,
    WorkflowTemplate,
)
from agentflowkit.tracing import to_jsonable  # noqa: E402


def main() -> None:
    flow = build_demo_flow()
    request = TaskRequest(
        objective="Generate a concise middleware experiment report.",
        template_id="middleware_report",
        inputs={
            "topic": "LangGraph multi-agent middleware",
            "requirements": "Planner-ReAct, skill/tool registry, model routing, tracing",
        },
    )
    result = flow.run(request)

    print("=== AgentFlowKit demo result ===")
    print(json.dumps(to_jsonable(result), ensure_ascii=False, indent=2))


def build_demo_flow() -> AgentFlow:
    planner = TemplatePlanner()
    planner.register(_template())

    tools = ToolRegistry()
    tools.register(ToolSpec(name="lookup", description="Find compact facts.", handler=_lookup))
    tools.register(ToolSpec(name="compose", description="Compose text.", handler=_compose))

    skills = SkillRegistry()
    skills.register(
        SkillSpec(name="research_skill", description="Collect facts.", handler=_research)
    )
    skills.register(
        SkillSpec(name="write_skill", description="Write summary.", handler=_write)
    )
    skills.register(
        SkillSpec(name="review_skill", description="Check output.", handler=_review)
    )

    router = CapabilityRouter(
        (
            ModelProfile(
                model_id="local-mini",
                capabilities=frozenset({"research", "write", "review"}),
                max_complexity=2,
                cost_rank=1,
            ),
            ModelProfile(
                model_id="planner-pro",
                capabilities=frozenset({"research", "write", "review"}),
                max_complexity=5,
                cost_rank=5,
            ),
        )
    )
    return AgentFlow(
        AgentFlowComponents(
            planner=planner,
            skills=skills,
            tools=tools,
            router=router,
        )
    )


def _template() -> WorkflowTemplate:
    return WorkflowTemplate(
        template_id="middleware_report",
        description="Research, write, and review a middleware report.",
        steps=(
            StepTemplate(
                step_id="research",
                title="Collect middleware facts",
                skill_name="research_skill",
                capability="research",
                complexity=2,
                input_keys=("topic", "requirements"),
            ),
            StepTemplate(
                step_id="write",
                title="Draft report summary",
                skill_name="write_skill",
                capability="write",
                complexity=3,
                input_keys=("topic",),
            ),
            StepTemplate(
                step_id="review",
                title="Review delivery fit",
                skill_name="review_skill",
                capability="review",
                complexity=1,
                input_keys=("requirements",),
            ),
        ),
    )


def _research(context: SkillContext) -> str:
    context.think("Need facts before drafting the report.")
    result = context.call_tool(
        ToolCall(
            tool_name="lookup",
            arguments={
                "topic": "LangGraph multi-agent middleware",
                "focus": "planner, ReAct, registry, routing, trace",
            },
            reason="Collect deterministic demo facts.",
        )
    )
    return str(context.finish(result.output))


def _write(context: SkillContext) -> str:
    context.think("Use the required middleware capabilities as the report spine.")
    result = context.call_tool(
        ToolCall(
            tool_name="compose",
            arguments={
                "title": "AgentFlowKit",
                "points": "Planner decomposes tasks; skills call tools; router selects models; trace records execution.",
            },
            reason="Generate a compact report summary.",
        )
    )
    return str(context.finish(result.output))


def _review(context: SkillContext) -> str:
    context.think("Verify that the output maps to the assignment requirements.")
    return str(context.finish("PASS: covers Planner-ReAct, skill/tool, routing, trace."))


def _lookup(arguments) -> str:
    return (
        f"{arguments['topic']} is represented as a workflow with "
        f"{arguments['focus']}."
    )


def _compose(arguments) -> str:
    return f"{arguments['title']}: {arguments['points']}"


if __name__ == "__main__":
    main()
