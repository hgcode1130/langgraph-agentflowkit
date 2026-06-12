from __future__ import annotations

from dataclasses import dataclass

from agentflowkit.models import Plan, PlanStep, SkillResult, TaskRequest, WorkflowResult
from agentflowkit.planner import TemplatePlanner
from agentflowkit.registry import (
    SkillContext,
    SkillContextConfig,
    SkillRegistry,
    ToolRegistry,
)
from agentflowkit.router import CapabilityRouter
from agentflowkit.tracing import ExecutionTracer


@dataclass(frozen=True, kw_only=True, slots=True)
class AgentFlowComponents:
    planner: TemplatePlanner
    skills: SkillRegistry
    tools: ToolRegistry
    router: CapabilityRouter


class AgentFlow:
    def __init__(self, components: AgentFlowComponents) -> None:
        self.planner = components.planner
        self.skills = components.skills
        self.tools = components.tools
        self.router = components.router

    def run(self, request: TaskRequest) -> WorkflowResult:
        plan = self.planner.plan(request)
        return self.run_plan(plan)

    def run_plan(self, plan: Plan) -> WorkflowResult:
        tracer = ExecutionTracer()
        tracer.record(
            "plan",
            "Planner produced workflow steps",
            {"template_id": plan.template_id, "step_count": len(plan.steps)},
        )
        results = tuple(self._run_step(step, tracer) for step in plan.steps)
        return WorkflowResult(
            objective=plan.objective,
            template_id=plan.template_id,
            step_results=results,
            events=tracer.events,
        )

    def _run_step(self, step: PlanStep, tracer: ExecutionTracer) -> SkillResult:
        route = self.router.route(step)
        tracer.record("route", route.reason, {"step_id": step.step_id})
        skill = self.skills.get(step.skill_name)
        context = self._context_for(step, route.model_id, tracer)
        tracer.record("skill", f"Executing skill: {skill.name}", {"step_id": step.step_id})
        output = skill.handler(context)
        return SkillResult(
            step_id=step.step_id,
            skill_name=skill.name,
            output=output,
            model_id=route.model_id,
        )

    def _context_for(
        self, step: PlanStep, model_id: str, tracer: ExecutionTracer
    ) -> SkillContext:
        return SkillContext(
            SkillContextConfig(
                step_id=step.step_id,
                model_id=model_id,
                tools=self.tools,
                trace=tracer.record,
            )
        )
