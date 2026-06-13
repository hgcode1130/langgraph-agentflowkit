from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def export_run(record: Mapping[str, Any], repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or _find_repo_root()
    run_id = str(record["run_id"])
    timestamp = _timestamp_for_path(record.get("completed_at") or record.get("created_at"))
    export_dir = root / "result" / f"{timestamp}_{run_id[:8]}"
    export_dir.mkdir(parents=True, exist_ok=True)

    json_path = export_dir / "run.json"
    markdown_path = export_dir / "实验报告.md"

    export_record = dict(record)
    export_record["exported_at"] = datetime.now(UTC).isoformat()
    json_path.write_text(
        json.dumps(export_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(export_record), encoding="utf-8")

    return {
        "directory": str(export_dir),
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "AGENTS.md").exists() and (parent / "libs").exists():
            return parent
    raise RuntimeError("Unable to locate repository root for result export")


def _timestamp_for_path(value: object) -> str:
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).strftime("%Y%m%d-%H%M%S")
        except ValueError:
            pass
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _render_markdown(record: Mapping[str, Any]) -> str:
    request = _mapping(record.get("request"))
    result = _mapping(record.get("result"))
    step_results = _list(result.get("step_results"))
    events = _list(result.get("events"))

    lines = [
        "# AgentFlowKit 实验报告",
        "",
        "## 基本信息",
        "",
        f"- Run ID: `{record.get('run_id', '')}`",
        f"- 状态: `{record.get('status', '')}`",
        f"- 创建时间: `{record.get('created_at', '')}`",
        f"- 完成时间: `{record.get('completed_at', '')}`",
        f"- 运行模式: `{request.get('mode', 'local')}`",
        f"- 工作流模板: `{request.get('template_id', '')}`",
        "",
        "## 任务目标",
        "",
        str(request.get("objective", "")),
        "",
        "## 输入参数",
        "",
        "```json",
        json.dumps(request.get("inputs", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## 步骤输出",
        "",
    ]

    if not step_results:
        lines.extend(["暂无步骤输出。", ""])
    for index, step_obj in enumerate(step_results, start=1):
        step = _mapping(step_obj)
        agent = _mapping(step.get("agent"))
        lines.extend(
            [
                f"### {index}. {agent.get('agent_name') or step.get('step_id', '')}",
                "",
                f"- 步骤 ID: `{step.get('step_id', '')}`",
                f"- 技能: `{step.get('skill_name', '')}`",
                f"- 模型: `{step.get('model_id', '')}`",
                f"- Agent 角色: {agent.get('role', '未声明')}",
                "",
                str(step.get("output", "")),
                "",
            ]
        )

    lines.extend(["## 执行轨迹", ""])
    if not events:
        lines.extend(["暂无执行轨迹。", ""])
    for event_obj in events:
        event = _mapping(event_obj)
        payload = json.dumps(event.get("payload", {}), ensure_ascii=False)
        lines.extend(
            [
                f"- `{event.get('index', '')}` **{event.get('kind', '')}**: {event.get('message', '')}",
                f"  - Payload: `{payload}`",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
