from __future__ import annotations

from agentflowkit.errors import DuplicateRegistrationError, MissingInputError, PlanningError
from agentflowkit.models import Plan, PlanStep, StepTemplate, TaskRequest, WorkflowTemplate


class TemplatePlanner:
    def __init__(self) -> None:
        self._templates: dict[str, WorkflowTemplate] = {}

    def register(self, template: WorkflowTemplate) -> None:
        if template.template_id in self._templates:
            raise DuplicateRegistrationError(
                f"Template already registered: {template.template_id}"
            )
        self._templates[template.template_id] = template

    def plan(self, request: TaskRequest) -> Plan:
        if request.template_id not in self._templates:
            raise PlanningError(f"Unknown workflow template: {request.template_id}")
        template = self._templates[request.template_id]
        steps = tuple(self._build_step(step, request) for step in template.steps)
        return Plan(
            objective=request.objective,
            template_id=template.template_id,
            steps=steps,
        )

    def templates(self) -> tuple[str, ...]:
        return tuple(sorted(self._templates))

    def _build_step(self, step: StepTemplate, request: TaskRequest) -> PlanStep:
        missing = [key for key in step.input_keys if key not in request.inputs]
        if missing:
            missing_text = ", ".join(missing)
            raise MissingInputError(f"Step {step.step_id} missing inputs: {missing_text}")
        inputs = {key: request.inputs[key] for key in step.input_keys}
        return PlanStep(
            step_id=step.step_id,
            title=step.title,
            skill_name=step.skill_name,
            capability=step.capability,
            complexity=step.complexity,
            inputs=inputs,
        )
