import pytest

from agentflowkit import (
    AgentFlow,
    AgentFlowComponents,
    CapabilityRouter,
    ModelProfile,
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
from agentflowkit.errors import (
    DuplicateRegistrationError,
    MissingInputError,
    ModelRoutingError,
)


def test_template_planner_builds_explicit_plan() -> None:
    planner = TemplatePlanner()
    planner.register(_workflow_template())

    plan = planner.plan(_request())

    assert plan.objective == "produce a short technical report"
    assert [step.step_id for step in plan.steps] == ["research", "summarize"]
    assert plan.steps[0].inputs["topic"] == "agent middleware"


def test_template_planner_requires_declared_inputs() -> None:
    planner = TemplatePlanner()
    planner.register(_workflow_template())

    with pytest.raises(MissingInputError):
        planner.plan(
            TaskRequest(
                objective="bad request",
                template_id="report",
                inputs={},
            )
        )


def test_registry_rejects_duplicate_names() -> None:
    tools = ToolRegistry()
    spec = ToolSpec(
        name="echo",
        description="return arguments",
        handler=lambda args: args,
    )
    tools.register(spec)

    with pytest.raises(DuplicateRegistrationError):
        tools.register(spec)


def test_router_selects_cheapest_eligible_model() -> None:
    router = CapabilityRouter(
        (
            ModelProfile(
                model_id="large",
                capabilities=frozenset({"research"}),
                max_complexity=5,
                cost_rank=20,
            ),
            ModelProfile(
                model_id="small",
                capabilities=frozenset({"research"}),
                max_complexity=3,
                cost_rank=5,
            ),
        )
    )
    step = _workflow_template().steps[0]
    plan_step = TemplatePlanner()._build_step(step, _request())

    decision = router.route(plan_step)

    assert decision.model_id == "small"


def test_router_raises_when_no_model_matches() -> None:
    router = CapabilityRouter(
        (
            ModelProfile(
                model_id="small",
                capabilities=frozenset({"write"}),
                max_complexity=1,
                cost_rank=1,
            ),
        )
    )
    step = TemplatePlanner()._build_step(_workflow_template().steps[0], _request())

    with pytest.raises(ModelRoutingError):
        router.route(step)


def test_agent_flow_runs_react_skill_and_records_trace() -> None:
    flow = _flow()

    result = flow.run(_request())

    assert result.step_results[0].output == "facts about agent middleware"
    assert result.step_results[1].output == "summary: agent middleware"
    assert [event.kind for event in result.events] == [
        "plan",
        "route",
        "skill",
        "thought",
        "action",
        "observation",
        "finish",
        "route",
        "skill",
        "thought",
        "finish",
    ]


def test_request_inputs_are_immutable() -> None:
    request = _request()

    with pytest.raises(TypeError):
        request.inputs["topic"] = "mutated"


def _flow() -> AgentFlow:
    planner = TemplatePlanner()
    planner.register(_workflow_template())
    tools = ToolRegistry()
    tools.register(
        ToolSpec(
            name="lookup",
            description="Look up compact facts for a topic.",
            handler=lambda args: f"facts about {args['topic']}",
        )
    )
    skills = SkillRegistry()
    skills.register(
        SkillSpec(
            name="research_skill",
            description="research",
            handler=_research_skill,
        )
    )
    skills.register(
        SkillSpec(
            name="summary_skill",
            description="summary",
            handler=_summary_skill,
        )
    )
    router = CapabilityRouter(
        (
            ModelProfile(
                model_id="mini",
                capabilities=frozenset({"research", "write"}),
                max_complexity=3,
                cost_rank=1,
            ),
            ModelProfile(
                model_id="pro",
                capabilities=frozenset({"research", "write"}),
                max_complexity=5,
                cost_rank=10,
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


def _research_skill(context):
    context.think("Need source facts before writing.")
    result = context.call_tool(
        ToolCall(
            tool_name="lookup",
            arguments={"topic": "agent middleware"},
            reason="Collect compact facts.",
        )
    )
    return context.finish(result.output)


def _summary_skill(context):
    context.think("Compress the facts into a report summary.")
    return context.finish("summary: agent middleware")


def _request() -> TaskRequest:
    return TaskRequest(
        objective="produce a short technical report",
        template_id="report",
        inputs={"topic": "agent middleware"},
    )


def _workflow_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        template_id="report",
        description="Research and summarize a technical topic.",
        steps=(
            StepTemplate(
                step_id="research",
                title="Research topic",
                skill_name="research_skill",
                capability="research",
                complexity=2,
                input_keys=("topic",),
            ),
            StepTemplate(
                step_id="summarize",
                title="Summarize findings",
                skill_name="summary_skill",
                capability="write",
                complexity=1,
            ),
        ),
    )
