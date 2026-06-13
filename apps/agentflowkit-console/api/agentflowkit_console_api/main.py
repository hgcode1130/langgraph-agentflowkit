from __future__ import annotations

from typing import Any, Literal

from agentflowkit import TaskRequest
from agentflowkit.tracing import to_jsonable
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agentflowkit_console_api.agents import (
    agent_dict_for_skill,
    agent_profiles,
)
from agentflowkit_console_api.config import deepseek_settings, grok_settings
from agentflowkit_console_api.deepseek_flow import build_deepseek_flow, build_grok_flow
from agentflowkit_console_api.demo_flow import (
    TEMPLATE_ID,
    build_demo_flow,
    middleware_report_template,
    model_profiles,
)
from agentflowkit_console_api.exporter import export_run
from agentflowkit_console_api.store import InMemoryRunStore

app = FastAPI(title="AgentFlowKit Console API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = InMemoryRunStore()


class RunRequest(BaseModel):
    objective: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["local", "deepseek", "grok"] = "local"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/templates")
def templates() -> dict[str, object]:
    template = middleware_report_template()
    return {
        "agents": [profile.to_dict() for profile in agent_profiles()],
        "templates": [
            {
                "template_id": template.template_id,
                "description": template.description,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "title": step.title,
                        "skill_name": step.skill_name,
                        "agent": agent_dict_for_skill(step.skill_name),
                        "capability": step.capability,
                        "complexity": step.complexity,
                        "input_keys": list(step.input_keys),
                    }
                    for step in template.steps
                ],
            }
        ],
    }


@app.get("/api/models")
def models() -> dict[str, object]:
    deepseek = deepseek_settings()
    grok = grok_settings()
    return {
        "profiles": [
            {
                "model_id": profile.model_id,
                "capabilities": sorted(profile.capabilities),
                "max_complexity": profile.max_complexity,
                "cost_rank": profile.cost_rank,
            }
            for profile in model_profiles()
        ],
        "deepseek": deepseek.public_dict(),
        "grok": grok.public_dict(),
        "modes": [
            {"id": "local", "label": "本地确定性演示"},
            {"id": "deepseek", "label": "DeepSeek 大模型验证"},
            {"id": "grok", "label": "Grok 大模型验证"},
        ],
    }


@app.post("/api/runs")
def create_run(request: RunRequest) -> dict[str, object]:
    record = store.create_pending(request.model_dump())
    try:
        if request.template_id != TEMPLATE_ID:
            raise ValueError(f"Unknown workflow template: {request.template_id}")
        task = TaskRequest(
            objective=request.objective,
            template_id=request.template_id,
            inputs=request.inputs,
        )
        if request.mode == "deepseek":
            flow = build_deepseek_flow(task)
        elif request.mode == "grok":
            flow = build_grok_flow(task)
        else:
            flow = build_demo_flow()
        result = flow.run(task)
    except Exception as exc:
        return store.fail(record["run_id"], str(exc))
    return store.complete(record["run_id"], _with_agent_metadata(to_jsonable(result)))


@app.get("/api/runs")
def runs() -> dict[str, object]:
    return {"runs": store.list()}


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, object]:
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@app.post("/api/runs/{run_id}/export")
def export_run_result(run_id: str) -> dict[str, object]:
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if record.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Only completed runs can be exported")
    if record.get("exports"):
        return record
    exports = export_run(record)
    return store.set_exports(run_id, exports)


def _with_agent_metadata(result: object) -> object:
    if not isinstance(result, dict):
        return result
    step_results = result.get("step_results")
    if not isinstance(step_results, list):
        return result
    for step in step_results:
        if not isinstance(step, dict):
            continue
        skill_name = step.get("skill_name")
        if isinstance(skill_name, str):
            step["agent"] = agent_dict_for_skill(skill_name)
    return result
