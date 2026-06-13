from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


RunRecord = dict[str, Any]


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: OrderedDict[str, RunRecord] = OrderedDict()

    def create_pending(self, request: dict[str, Any]) -> RunRecord:
        now = _utc_now()
        run_id = str(uuid4())
        record: RunRecord = {
            "run_id": run_id,
            "status": "pending",
            "created_at": now,
            "completed_at": None,
            "request": request,
            "result": None,
            "error": None,
            "exports": None,
        }
        self._runs[run_id] = record
        return record

    def complete(self, run_id: str, result: object) -> RunRecord:
        record = self._runs[run_id]
        record["status"] = "completed"
        record["completed_at"] = _utc_now()
        record["result"] = result
        return record

    def fail(self, run_id: str, error: str) -> RunRecord:
        record = self._runs[run_id]
        record["status"] = "failed"
        record["completed_at"] = _utc_now()
        record["error"] = error
        return record

    def list(self) -> list[RunRecord]:
        return list(reversed(self._runs.values()))

    def get(self, run_id: str) -> RunRecord | None:
        return self._runs.get(run_id)

    def set_exports(self, run_id: str, exports: dict[str, object]) -> RunRecord:
        record = self._runs[run_id]
        record["exports"] = exports
        return record

    def clear(self) -> None:
        self._runs.clear()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
