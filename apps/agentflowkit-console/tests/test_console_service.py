import pytest

from backend import console_service
from agentflowkit.errors import ModelClientError


def test_capabilities_include_console_primitives() -> None:
    caps = console_service.capabilities()

    assert "template" in caps["planners"]
    assert "grok" in caps["planners"]
    assert "research_skill" in caps["skills"]
    assert "lookup" in caps["tools"]


def test_preview_template_workflow() -> None:
    data = console_service.preview_workflow({"planner": "template"})

    assert data["planner"] == "template"
    assert len(data["plan"]["steps"]) == 3
    assert data["plan"]["steps"][0]["skill_name"] == "research_skill"


def test_run_template_workflow_records_trace() -> None:
    data = console_service.run_workflow({"planner": "template"})
    events = data["result"]["events"]

    assert data["planner"] == "template"
    assert data["result"]["step_results"][2]["output"].startswith("PASS")
    assert [event["kind"] for event in events][:3] == ["plan", "route", "skill"]


def test_unknown_planner_is_explicit_error() -> None:
    with pytest.raises(ValueError):
        console_service.preview_workflow({"planner": "missing"})


def test_grok_smoke_requires_environment(monkeypatch) -> None:
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENTFLOWKIT_OPENAI_MODEL", raising=False)

    with pytest.raises(ModelClientError):
        console_service.grok_smoke_test()
