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
from agentflowkit_console_api.agent_collaboration import (
    AgentHandoffState,
    record_handoff,
)
from agentflowkit_console_api.agents import agent_profile_for_skill

TEMPLATE_ID = "middleware_report"


def build_demo_flow() -> AgentFlow:
    handoff = AgentHandoffState()
    planner = TemplatePlanner()
    planner.register(middleware_report_template())

    tools = ToolRegistry()
    tools.register(ToolSpec(name="lookup", description="检索主题相关事实。", handler=_lookup))
    tools.register(
        ToolSpec(
            name="extract_research_notes",
            description="从事实和需求中提取研究要点。",
            handler=_extract_research_notes,
        )
    )
    tools.register(
        ToolSpec(
            name="compose_report",
            description="基于研究要点生成报告草稿。",
            handler=_compose_report,
        )
    )
    tools.register(
        ToolSpec(
            name="structure_report",
            description="整理报告结构。",
            handler=_structure_report,
        )
    )
    tools.register(
        ToolSpec(
            name="check_requirements",
            description="检查报告是否覆盖需求。",
            handler=_check_requirements,
        )
    )
    tools.register(
        ToolSpec(
            name="score_report",
            description="给报告可验证性评分。",
            handler=_score_report,
        )
    )

    skills = SkillRegistry()
    skills.register(
        SkillSpec(
            name="research_skill",
            description=agent_profile_for_skill("research_skill").responsibility,
            handler=lambda context: _research(context, handoff),
        )
    )
    skills.register(
        SkillSpec(
            name="write_skill",
            description=agent_profile_for_skill("write_skill").responsibility,
            handler=lambda context: _write(context, handoff),
        )
    )
    skills.register(
        SkillSpec(
            name="review_skill",
            description=agent_profile_for_skill("review_skill").responsibility,
            handler=lambda context: _review(context, handoff),
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
                title="收集并整理研究要点",
                skill_name="research_skill",
                capability="research",
                complexity=2,
                input_keys=("topic", "requirements"),
            ),
            StepTemplate(
                step_id="write",
                title="基于研究要点生成报告草稿",
                skill_name="write_skill",
                capability="write",
                complexity=3,
                input_keys=("topic",),
            ),
            StepTemplate(
                step_id="review",
                title="审查报告质量和需求覆盖",
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


def _research(context: SkillContext, handoff: AgentHandoffState) -> dict[str, object]:
    profile = agent_profile_for_skill("research_skill")
    context.think("研究 Agent 使用 lookup 和 extract_research_notes 生成 research_notes。")
    facts = context.call_tool(
        ToolCall(
            tool_name="lookup",
            arguments={
                "topic": "LangGraph 多智能体工作流中间件",
                "focus": "Planner、Agent 分工、工具集、模型路由、执行轨迹",
            },
            reason="收集主题事实，供研究 Agent 提取研究要点。",
        )
    )
    notes = context.call_tool(
        ToolCall(
            tool_name="extract_research_notes",
            arguments={
                "facts": facts.output,
                "requirements": "任务规划、ReAct 工具调用、技能注册、模型路由、执行轨迹记录",
            },
            reason="将检索事实整理为可传递给写作 Agent 的研究要点。",
        )
    )
    handoff_meta = record_handoff(
        context,
        from_agent=profile.agent_name,
        to_agent=agent_profile_for_skill("write_skill").agent_name,
        artifact="research_notes",
    )
    output = handoff.output(
        artifact="research_notes",
        content=notes.output,
        received_artifacts=(),
        handoff=handoff_meta,
    )
    return context.finish(output)


def _write(context: SkillContext, handoff: AgentHandoffState) -> dict[str, object]:
    profile = agent_profile_for_skill("write_skill")
    research_notes = handoff.read("research_notes")
    context.think("写作 Agent 接收 research_notes，并使用 compose_report 和 structure_report 生成 report_draft。")
    draft = context.call_tool(
        ToolCall(
            tool_name="compose_report",
            arguments={
                "title": "AgentFlowKit 多 Agent 工作流中间件实验报告",
                "research_notes": research_notes,
            },
            reason="基于研究 Agent 输出生成报告草稿。",
        )
    )
    structured = context.call_tool(
        ToolCall(
            tool_name="structure_report",
            arguments={"draft": draft.output},
            reason="将报告草稿整理为实验报告结构。",
        )
    )
    handoff_meta = record_handoff(
        context,
        from_agent=profile.agent_name,
        to_agent=agent_profile_for_skill("review_skill").agent_name,
        artifact="report_draft",
    )
    output = handoff.output(
        artifact="report_draft",
        content=structured.output,
        received_artifacts=("research_notes",),
        handoff=handoff_meta,
    )
    return context.finish(output)


def _review(context: SkillContext, handoff: AgentHandoffState) -> dict[str, object]:
    profile = agent_profile_for_skill("review_skill")
    report_draft = handoff.read("report_draft")
    context.think("审查 Agent 接收 report_draft，并使用 check_requirements 和 score_report 生成 review_result。")
    check = context.call_tool(
        ToolCall(
            tool_name="check_requirements",
            arguments={
                "draft": report_draft,
                "requirements": "Planner、Agent 分工、工具集、模型路由、执行轨迹记录",
            },
            reason="检查报告是否覆盖实验需求。",
        )
    )
    score = context.call_tool(
        ToolCall(
            tool_name="score_report",
            arguments={"draft": report_draft, "check": check.output},
            reason="评估报告的可验证性。",
        )
    )
    review = f"{check.output}\n{score.output}"
    handoff_meta = record_handoff(
        context,
        from_agent=profile.agent_name,
        to_agent="最终结果",
        artifact="review_result",
    )
    output = handoff.output(
        artifact="review_result",
        content=review,
        received_artifacts=("report_draft",),
        handoff=handoff_meta,
    )
    return context.finish(output)


def _lookup(arguments: object) -> str:
    args = _args(arguments)
    return (
        f"{args['topic']} 的实验重点包括 {args['focus']}。"
        "该中间件在 LangGraph 图执行基础上增加了 Agent 编排语义。"
    )


def _extract_research_notes(arguments: object) -> str:
    args = _args(arguments)
    return (
        "research_notes:\n"
        f"- 事实基础：{args['facts']}\n"
        f"- 需求约束：{args['requirements']}\n"
        "- 关键观察：系统通过 Planner 拆解任务，通过 Agent 分工执行，并通过 trace 记录过程。"
    )


def _compose_report(arguments: object) -> str:
    args = _args(arguments)
    return (
        f"{args['title']}\n\n"
        "一、实验背景\n"
        "本实验关注如何在 LangGraph 之上构建多 Agent 工作流中间件。\n\n"
        "二、研究要点\n"
        f"{args['research_notes']}\n\n"
        "三、初步结论\n"
        "AgentFlowKit 将任务规划、Agent 分工、工具调用、模型路由和轨迹记录组合为可观察工作流。"
    )


def _structure_report(arguments: object) -> str:
    args = _args(arguments)
    return f"report_draft:\n{args['draft']}\n\n四、结构化说明\n报告已按背景、方法、结果和结论组织。"


def _check_requirements(arguments: object) -> str:
    args = _args(arguments)
    return (
        "requirements_check:\n"
        f"- 待覆盖需求：{args['requirements']}\n"
        "- 覆盖结论：报告覆盖 Planner、Agent 分工、工具集、模型路由和执行轨迹。"
    )


def _score_report(arguments: object) -> str:
    args = _args(arguments)
    return (
        "review_result:\n"
        "- 可验证性评分：92/100\n"
        f"- 依据：{args['check']}\n"
        "- 建议：在前端继续突出 Agent 输出传递链路。"
    )


def _args(arguments: object) -> dict[str, object]:
    return dict(arguments) if isinstance(arguments, Mapping) else {}
