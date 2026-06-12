import pytest

from agentflowkit import LLMPlanner, SkillRegistry, SkillSpec, TaskRequest
from agentflowkit.errors import PlanningError


class FakeModel:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages = ()

    def complete(self, messages):
        self.messages = messages
        return self.content


def test_llm_planner_builds_plan_from_json() -> None:
    model = FakeModel(
        """
        {
          "steps": [
            {
              "step_id": "research",
              "title": "Research topic",
              "skill_name": "research_skill",
              "capability": "research",
              "complexity": 3,
              "inputs": {"topic": "LangGraph"}
            }
          ]
        }
        """
    )
    planner = LLMPlanner(model, _skills())

    plan = planner.plan(_request())

    assert plan.steps[0].skill_name == "research_skill"
    assert plan.steps[0].inputs["topic"] == "LangGraph"
    assert "Available skills: research_skill" in model.messages[1]["content"]


def test_llm_planner_accepts_json_code_fence() -> None:
    model = FakeModel(
        """```json
        {"steps":[{"step_id":"s1","title":"T","skill_name":"research_skill","capability":"research","complexity":1,"inputs":{}}]}
        ```"""
    )

    plan = LLMPlanner(model, _skills()).plan(_request())

    assert plan.steps[0].step_id == "s1"


def test_llm_planner_rejects_unknown_skill() -> None:
    model = FakeModel(
        '{"steps":[{"step_id":"s1","title":"T","skill_name":"missing",'
        '"capability":"research","complexity":1,"inputs":{}}]}'
    )

    with pytest.raises(PlanningError):
        LLMPlanner(model, _skills()).plan(_request())


def test_llm_planner_rejects_invalid_complexity() -> None:
    model = FakeModel(
        '{"steps":[{"step_id":"s1","title":"T","skill_name":"research_skill",'
        '"capability":"research","complexity":6,"inputs":{}}]}'
    )

    with pytest.raises(PlanningError):
        LLMPlanner(model, _skills()).plan(_request())


def _skills() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        SkillSpec(
            name="research_skill",
            description="research",
            handler=lambda context: context.finish("ok"),
        )
    )
    return registry


def _request() -> TaskRequest:
    return TaskRequest(
        objective="make a plan",
        template_id="dynamic",
        inputs={"topic": "LangGraph"},
    )
