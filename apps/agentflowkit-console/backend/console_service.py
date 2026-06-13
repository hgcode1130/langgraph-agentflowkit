from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTFLOWKIT_SRC = REPO_ROOT / "libs" / "agentflowkit"
if str(AGENTFLOWKIT_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTFLOWKIT_SRC))

from agentflowkit import (  # noqa: E402
    AgentFlow,
    AgentFlowComponents,
    CapabilityRouter,
    LLMPlanner,
    ModelProfile,
    OpenAICompatibleChatModel,
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

DEFAULT_OBJECTIVE = "Generate a concise middleware experiment report."
DEFAULT_TOPIC = "LangGraph multi-agent middleware"
DEFAULT_REQUIREMENTS = "Planner-ReAct, skill/tool registry, model routing, tracing"


def capabilities() -> dict[str, Any]:
    return {
        "planners": ["template", "grok"],
        "skills": list(_skills().names()),
        "tools": list(_tools().names()),
        "models": [profile.model_id for profile in _model_profiles()],
        "events": ["plan", "route", "skill", "thought", "action", "observation", "finish"],
    }


def preview_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    request = _request(payload)
    planner_name = str(payload.get("planner", "template"))
    if planner_name == "template":
        plan = _template_planner().plan(request)
        return {"planner": planner_name, "plan": to_jsonable(plan)}
    if planner_name == "grok":
        plan = _grok_planner().plan(request)
        return {"planner": planner_name, "plan": to_jsonable(plan)}
    raise ValueError(f"Unknown planner: {planner_name}")


def run_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    request = _request(payload)
    planner_name = str(payload.get("planner", "template"))
    if planner_name == "template":
        result = _template_flow().run(request)
        return {"planner": planner_name, "result": to_jsonable(result)}
    if planner_name == "grok":
        plan = _grok_planner().plan(request)
        result = _manual_flow().run_plan(plan)
        return {"planner": planner_name, "plan": to_jsonable(plan), "result": to_jsonable(result)}
    raise ValueError(f"Unknown planner: {planner_name}")


def grok_smoke_test() -> dict[str, Any]:
    content = OpenAICompatibleChatModel.from_env().complete(
        (
            {"role": "system", "content": "Return strict JSON only."},
            {
                "role": "user",
                "content": (
                    "Return {\"ok\": true, \"provider\": \"grok\"} if this "
                    "OpenAI-compatible chat completion request works."
                ),
            },
        )
    )
    return {"raw_content": content}


def provider_status() -> dict[str, Any]:
    return {
        "base_url": _configured("AGENTFLOWKIT_OPENAI_BASE_URL"),
        "api_key": _configured("AGENTFLOWKIT_OPENAI_API_KEY"),
        "model": os.getenv("AGENTFLOWKIT_OPENAI_MODEL", ""),
    }


def _request(payload: dict[str, Any]) -> TaskRequest:
    return TaskRequest(
        objective=str(payload.get("objective") or DEFAULT_OBJECTIVE),
        template_id=str(payload.get("template_id") or "middleware_report"),
        inputs={
            "topic": str(payload.get("topic") or DEFAULT_TOPIC),
            "requirements": str(payload.get("requirements") or DEFAULT_REQUIREMENTS),
            "audience": str(payload.get("audience") or "middleware course evaluator"),
            "available_minutes": int(payload.get("available_minutes") or 2),
        },
    )


def _template_flow() -> AgentFlow:
    return AgentFlow(
        AgentFlowComponents(
            planner=_template_planner(),
            skills=_skills(),
            tools=_tools(),
            router=_router(),
        )
    )


def _manual_flow() -> AgentFlow:
    planner = TemplatePlanner()
    planner.register(
        WorkflowTemplate(template_id="manual", description="Manual plan container.", steps=())
    )
    return AgentFlow(
        AgentFlowComponents(
            planner=planner,
            skills=_skills(),
            tools=_tools(),
            router=_router(),
        )
    )


def _template_planner() -> TemplatePlanner:
    planner = TemplatePlanner()
    planner.register(_template())
    return planner


def _grok_planner() -> LLMPlanner:
    return LLMPlanner(OpenAICompatibleChatModel.from_env(), _skills())


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


def _tools() -> ToolRegistry:
    tools = ToolRegistry()
    tools.register(ToolSpec(name="lookup", description="Find compact facts.", handler=_lookup))
    tools.register(ToolSpec(name="compose", description="Compose text.", handler=_compose))
    return tools


def _skills() -> SkillRegistry:
    skills = SkillRegistry()
    skills.register(SkillSpec(name="research_skill", description="Collect facts.", handler=_research))
    skills.register(SkillSpec(name="write_skill", description="Write summary.", handler=_write))
    skills.register(SkillSpec(name="review_skill", description="Check output.", handler=_review))
    return skills


def _router() -> CapabilityRouter:
    return CapabilityRouter(_model_profiles())


def _model_profiles() -> tuple[ModelProfile, ...]:
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
    context.think("Need facts before drafting the report.")
    result = context.call_tool(
        ToolCall(
            tool_name="lookup",
            arguments={"topic": DEFAULT_TOPIC, "focus": "planner, ReAct, registry, routing, trace"},
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


def _lookup(arguments: dict[str, object]) -> str:
    return f"{arguments['topic']} is represented as a workflow with {arguments['focus']}."


def _compose(arguments: dict[str, object]) -> str:
    return f"{arguments['title']}: {arguments['points']}"


def _configured(name: str) -> bool:
    return bool(os.getenv(name))
