from __future__ import annotations

import json

from fastapi.testclient import TestClient

from agentflowkit import TaskRequest
from agentflowkit.tracing import to_jsonable
from agentflowkit_console_api.config import grok_settings
from agentflowkit_console_api.deepseek_flow import build_deepseek_flow, build_grok_flow
from agentflowkit_console_api.main import app, store


def setup_function() -> None:
    store.clear()


def test_health() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_templates_include_agents_and_tool_sets() -> None:
    client = TestClient(app)

    response = client.get("/api/templates")

    assert response.status_code == 200
    payload = response.json()
    agents = payload["agents"]
    assert [agent["agent_name"] for agent in agents] == [
        "研究 Agent",
        "写作 Agent",
        "审查 Agent",
    ]
    assert agents[0]["tools"] == ["lookup", "extract_research_notes"]
    steps = payload["templates"][0]["steps"]
    assert steps[0]["agent"]["agent_name"] == "研究 Agent"
    assert steps[1]["agent"]["tools"] == ["compose_report", "structure_report"]


def test_create_run_completes_with_agent_handoffs() -> None:
    client = TestClient(app)

    response = client.post("/api/runs", json=_valid_local_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    steps = payload["result"]["step_results"]
    assert steps[0]["agent"]["agent_name"] == "研究 Agent"
    assert steps[0]["artifact"] == "research_notes"
    assert steps[1]["received_artifacts"] == ["research_notes"]
    assert steps[1]["artifact"] == "report_draft"
    assert steps[2]["received_artifacts"] == ["report_draft"]
    assert steps[2]["artifact"] == "review_result"
    assert steps[0]["tools"] == ["lookup", "extract_research_notes"]

    handoffs = [
        event for event in payload["result"]["events"] if event["kind"] == "handoff"
    ]
    assert [event["payload"]["artifact"] for event in handoffs] == [
        "research_notes",
        "report_draft",
        "review_result",
    ]


def test_export_completed_run_creates_json_and_markdown(tmp_path, monkeypatch) -> None:
    client = TestClient(app)
    response = client.post("/api/runs", json=_valid_local_request())
    run_id = response.json()["run_id"]

    monkeypatch.setattr(
        "agentflowkit_console_api.main.export_run",
        lambda record: _fake_export(record, tmp_path),
    )
    export_response = client.post(f"/api/runs/{run_id}/export")

    assert export_response.status_code == 200
    payload = export_response.json()
    exports = payload["exports"]
    json_path = tmp_path / "run.json"
    markdown_path = tmp_path / "实验报告.md"
    assert exports["json_path"] == str(json_path)
    assert exports["markdown_path"] == str(markdown_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["run_id"] == run_id
    assert "AgentFlowKit 实验报告" in markdown_path.read_text(encoding="utf-8")


def test_export_completed_run_is_idempotent(tmp_path, monkeypatch) -> None:
    client = TestClient(app)
    response = client.post("/api/runs", json=_valid_local_request())
    run_id = response.json()["run_id"]
    calls = {"count": 0}

    def fake_export(record):
        calls["count"] += 1
        return _fake_export(record, tmp_path)

    monkeypatch.setattr("agentflowkit_console_api.main.export_run", fake_export)

    first = client.post(f"/api/runs/{run_id}/export").json()
    second = client.post(f"/api/runs/{run_id}/export").json()

    assert calls["count"] == 1
    assert first["exports"] == second["exports"]


def test_export_failed_run_returns_400() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/runs",
        json={
            "objective": "Bad run",
            "template_id": "middleware_report",
            "mode": "local",
            "inputs": {},
        },
    )
    run_id = response.json()["run_id"]

    export_response = client.post(f"/api/runs/{run_id}/export")

    assert export_response.status_code == 400


def test_export_unknown_run_returns_404() -> None:
    client = TestClient(app)

    response = client.post("/api/runs/missing/export")

    assert response.status_code == 404


def test_deepseek_mode_reports_missing_configuration(monkeypatch) -> None:
    monkeypatch.delenv("AGENTFLOWKIT_DEEPSEEK_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/runs",
        json={
            "objective": "生成一份实验报告",
            "template_id": "middleware_report",
            "mode": "deepseek",
            "inputs": {
                "topic": "LangGraph",
                "requirements": "规划、路由、轨迹",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert "DeepSeek 未配置" in payload["error"]


def test_models_never_expose_api_keys(monkeypatch) -> None:
    monkeypatch.setenv("AGENTFLOWKIT_DEEPSEEK_API_KEY", "secret-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-grok-key")
    client = TestClient(app)

    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["deepseek"]["api_key_configured"] is True
    assert payload["grok"]["api_key_configured"] is True
    assert "secret-test-key" not in str(payload)
    assert "secret-grok-key" not in str(payload)


def test_deepseek_flow_passes_artifacts_and_tool_sets_to_prompts() -> None:
    model = FakeChatModel("DeepSeek fake output")
    request = _task_request()

    result = build_deepseek_flow(request, model).run(request)
    payload = to_jsonable(result)

    assert [step["step_id"] for step in payload["step_results"]] == [
        "research",
        "write",
        "review",
    ]
    prompt_text = "\n".join(model.prompts)
    assert "可用工具：lookup, extract_research_notes" in prompt_text
    assert "可用工具：compose_report, structure_report" in prompt_text
    assert "可用工具：check_requirements, score_report" in prompt_text
    assert "research_notes" in model.prompts[2]
    assert "report_draft" in model.prompts[3]


def test_grok_flow_can_run_with_fake_model() -> None:
    request = _task_request()

    result = build_grok_flow(request, FakeChatModel("Grok fake output")).run(request)
    payload = to_jsonable(result)

    assert [step["step_id"] for step in payload["step_results"]] == [
        "research",
        "write",
        "review",
    ]


def test_grok_settings_can_read_project_env_file(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=file-key\nOPENAI_BASE_URL=https://example.test/v1\nOPENAI_MODEL=grok-test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentflowkit_console_api.config._dotenv_paths",
        lambda: (env_file,),
    )

    settings = grok_settings()

    assert settings.configured is True
    assert settings.base_url == "https://example.test/v1"
    assert settings.model == "grok-test"


def _valid_local_request() -> dict[str, object]:
    return {
        "objective": "生成一份关于 LangGraph 多智能体工作流中间件的简明实验报告。",
        "template_id": "middleware_report",
        "mode": "local",
        "inputs": {
            "topic": "LangGraph 多智能体工作流中间件",
            "requirements": "任务规划、技能注册、模型路由、执行轨迹",
        },
    }


def _task_request() -> TaskRequest:
    return TaskRequest(
        objective="生成一份实验报告",
        template_id="middleware_report",
        inputs={
            "topic": "LangGraph 多智能体工作流中间件",
            "requirements": "任务规划、模型路由、执行轨迹",
        },
    )


def _fake_export(record, directory):
    json_path = directory / "run.json"
    markdown_path = directory / "实验报告.md"
    json_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text("# AgentFlowKit 实验报告\n", encoding="utf-8")
    return {
        "directory": str(directory),
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


class FakeChatModel:
    def __init__(self, output_prefix: str) -> None:
        self.calls = 0
        self.output_prefix = output_prefix
        self.prompts: list[str] = []

    def complete(self, messages):
        self.calls += 1
        self.prompts.append("\n".join(message["content"] for message in messages))
        if self.calls == 1:
            return """
            {
              "steps": [
                {
                  "step_id": "research",
                  "title": "研究功能增改",
                  "skill_name": "research_skill",
                  "capability": "research",
                  "complexity": 3,
                  "inputs": {"topic": "LangGraph"}
                },
                {
                  "step_id": "write",
                  "title": "撰写实验报告",
                  "skill_name": "write_skill",
                  "capability": "write",
                  "complexity": 3,
                  "inputs": {"topic": "LangGraph"}
                },
                {
                  "step_id": "review",
                  "title": "审查实验报告",
                  "skill_name": "review_skill",
                  "capability": "review",
                  "complexity": 2,
                  "inputs": {"topic": "LangGraph"}
                }
              ]
            }
            """
        return f"{self.output_prefix} {self.calls}"
