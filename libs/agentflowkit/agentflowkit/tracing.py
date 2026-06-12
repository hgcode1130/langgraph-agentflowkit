from __future__ import annotations

from dataclasses import fields, is_dataclass
from types import MappingProxyType
from typing import Mapping

from agentflowkit.models import TraceEvent


class ExecutionTracer:
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        kind: str,
        message: str,
        payload: Mapping[str, object] | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            index=len(self._events) + 1, kind=kind, message=message, payload=payload or {}
        )
        self._events.append(event)
        return event


def to_jsonable(value: object) -> object:
    if isinstance(value, MappingProxyType):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [to_jsonable(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)
        }
    return value
