from __future__ import annotations

import json

from agentflowkit.errors import PlanningError
from agentflowkit.model_client import ChatModel
from agentflowkit.models import Plan, PlanStep, TaskRequest
from agentflowkit.registry import SkillRegistry

MIN_COMPLEXITY = 1
MAX_COMPLEXITY = 5


class LLMPlanner:
    def __init__(self, model: ChatModel, skills: SkillRegistry) -> None:
        self._model = model
        self._skills = skills

    def plan(self, request: TaskRequest) -> Plan:
        response = self._model.complete(self._messages(request))
        return Plan(
            objective=request.objective,
            template_id=request.template_id,
            steps=self._parse_steps(response),
        )

    def _messages(self, request: TaskRequest) -> tuple[dict[str, str], ...]:
        skill_names = ", ".join(self._skills.names())
        user = (
            f"Objective: {request.objective}\n"
            f"Template id: {request.template_id}\n"
            f"Inputs JSON: {json.dumps(dict(request.inputs), ensure_ascii=False)}\n"
            f"Available skills: {skill_names}"
        )
        return (
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": user},
        )

    def _parse_steps(self, content: str) -> tuple[PlanStep, ...]:
        data = _loads_json_object(content)
        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise PlanningError("LLM planner response must contain non-empty steps")
        return tuple(_parse_step(item, self._skills) for item in raw_steps)


def _system_prompt() -> str:
    return (
        "You are a workflow planner. Return only strict JSON. "
        "Schema: {\"steps\":[{\"step_id\":\"...\",\"title\":\"...\","
        "\"skill_name\":\"...\",\"capability\":\"research|write|review|code|tool\","
        "\"complexity\":1,\"inputs\":{}}]}. "
        "Use only available skill names. Complexity is an integer from 1 to 5."
    )


def _loads_json_object(content: str) -> dict[str, object]:
    try:
        data = json.loads(_strip_code_fence(content))
    except json.JSONDecodeError as exc:
        raise PlanningError("LLM planner returned non-JSON content") from exc
    if not isinstance(data, dict):
        raise PlanningError("LLM planner response must be a JSON object")
    return data


def _strip_code_fence(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) < 3:
        return text
    return "\n".join(lines[1:-1]).strip()


def _parse_step(item: object, skills: SkillRegistry) -> PlanStep:
    if not isinstance(item, dict):
        raise PlanningError("Each LLM planner step must be an object")
    step = _required_step_fields(item)
    skill_name = _as_string(step["skill_name"], "skill_name")
    if skill_name not in skills.names():
        raise PlanningError(f"LLM planner selected unknown skill: {skill_name}")
    return PlanStep(
        step_id=_as_string(step["step_id"], "step_id"),
        title=_as_string(step["title"], "title"),
        skill_name=skill_name,
        capability=_as_string(step["capability"], "capability"),
        complexity=_as_complexity(step["complexity"]),
        inputs=_as_inputs(step["inputs"]),
    )


def _required_step_fields(item: dict[str, object]) -> dict[str, object]:
    required = ("step_id", "title", "skill_name", "capability", "complexity", "inputs")
    missing = [key for key in required if key not in item]
    if missing:
        raise PlanningError(f"LLM planner step missing fields: {', '.join(missing)}")
    return item


def _as_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlanningError(f"LLM planner field must be a non-empty string: {field}")
    return value


def _as_complexity(value: object) -> int:
    if not isinstance(value, int):
        raise PlanningError("LLM planner complexity must be an integer")
    if value < MIN_COMPLEXITY or value > MAX_COMPLEXITY:
        raise PlanningError("LLM planner complexity must be between 1 and 5")
    return value


def _as_inputs(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PlanningError("LLM planner inputs must be an object")
    return dict(value)
