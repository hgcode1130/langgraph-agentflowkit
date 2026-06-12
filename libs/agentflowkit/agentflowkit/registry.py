from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from agentflowkit.errors import DuplicateRegistrationError, RegistryLookupError
from agentflowkit.models import ToolCall, ToolResult

ToolHandler = Callable[[Mapping[str, object]], object]
SkillHandler = Callable[["SkillContext"], object]


@dataclass(frozen=True, kw_only=True, slots=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler


@dataclass(frozen=True, kw_only=True, slots=True)
class SkillSpec:
    name: str
    description: str
    handler: SkillHandler


@dataclass(frozen=True, kw_only=True, slots=True)
class SkillContextConfig:
    step_id: str
    model_id: str
    tools: ToolRegistry
    trace: Callable[[str, str, Mapping[str, object] | None], object]


class ToolRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._items:
            raise DuplicateRegistrationError(f"Tool already registered: {spec.name}")
        self._items[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._items:
            raise RegistryLookupError(f"Unknown tool: {name}")
        return self._items[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


class SkillRegistry:
    def __init__(self) -> None:
        self._items: dict[str, SkillSpec] = {}

    def register(self, spec: SkillSpec) -> None:
        if spec.name in self._items:
            raise DuplicateRegistrationError(f"Skill already registered: {spec.name}")
        self._items[spec.name] = spec

    def get(self, name: str) -> SkillSpec:
        if name not in self._items:
            raise RegistryLookupError(f"Unknown skill: {name}")
        return self._items[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


class SkillContext:
    def __init__(self, config: SkillContextConfig) -> None:
        self.step_id = config.step_id
        self.model_id = config.model_id
        self._tools = config.tools
        self._trace = config.trace

    def think(self, message: str) -> None:
        self._trace("thought", message, {"step_id": self.step_id})

    def call_tool(self, call: ToolCall) -> ToolResult:
        self._trace(
            "action",
            call.reason,
            {"step_id": self.step_id, "tool": call.tool_name},
        )
        output = self._tools.get(call.tool_name).handler(call.arguments)
        result = ToolResult(tool_name=call.tool_name, output=output)
        self._trace(
            "observation",
            f"Tool completed: {call.tool_name}",
            {"step_id": self.step_id, "output": output},
        )
        return result

    def finish(self, output: object) -> object:
        self._trace("finish", "Skill produced final output", {"step_id": self.step_id})
        return output
