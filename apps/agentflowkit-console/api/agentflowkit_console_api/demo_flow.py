from __future__ import annotations

from collections.abc import Mapping

from agentflowkit import (
    AgentFlow,
    AgentFlowComponents,
    CapabilityRouter,
    ModelProfile,
    SkillContext,
    SkillRegistry,
    SkillSpec,
    StepTemplate,
    TemplatePlanner,
    ToolCall,
    ToolRegistry,
    ToolSpec,
    WorkflowTemplate,
)
from agentflowkit_console_api.agents import agent_profile_for_skill

TEMPLATE_ID = "middleware_report"


def build_demo_flow() -> AgentFlow:
    planner = TemplatePlanner()
    planner.register(middleware_report_template())

    tools = ToolRegistry()
    tools.register(ToolSpec(name="lookup", description="Find compact facts.", handler=_lookup))
    tools.register(ToolSpec(name="compose", description="Compose text.", handler=_compose))

    skills = SkillRegistry()
    skills.register(
        SkillSpec(
            name="research_skill",
            description=agent_profile_for_skill("research_skill").responsibility,
            handler=_research,
        )
    )
    skills.register(
        SkillSpec(
            name="write_skill",
            description=agent_profile_for_skill("write_skill").responsibility,
            handler=_write,
        )
    )
    skills.register(
        SkillSpec(
            name="review_skill",
            description=agent_profile_for_skill("review_skill").responsibility,
            handler=_review,
        )
    )

    router = CapabilityRouter(model_profiles())
    return AgentFlow(
        AgentFlowComponents(
            planner=planner,
            skills=skills,
            tools=tools,
            router=router,
        )
    )


def middleware_report_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        template_id=TEMPLATE_ID,
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


def model_profiles() -> tuple[ModelProfile, ...]:
    return (
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


def _research(context: SkillContext) -> str:
    context.think("研究 Agent 正在收集写作前所需的事实材料。")
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
    context.think("写作 Agent 正在将中间件能力组织为报告主线。")
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
    context.think("审查 Agent 正在检查输出是否覆盖实验要求。")
    return str(context.finish("PASS: covers Planner-ReAct, skill/tool, routing, trace."))


def _lookup(arguments: object) -> str:
    args = dict(arguments) if isinstance(arguments, Mapping) else {}
    return f"{args['topic']} is represented as a workflow with {args['focus']}."


def _compose(arguments: object) -> str:
    args = dict(arguments) if isinstance(arguments, Mapping) else {}
    return f"{args['title']}: {args['points']}"
