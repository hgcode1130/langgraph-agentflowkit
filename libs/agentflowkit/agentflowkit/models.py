from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from agentflowkit._immutability import freeze_mapping, freeze_tuple


@dataclass(frozen=True, kw_only=True, slots=True)
class TaskRequest:
    objective: str
    template_id: str
    inputs: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", freeze_mapping(self.inputs))


@dataclass(frozen=True, kw_only=True, slots=True)
class StepTemplate:
    step_id: str
    title: str
    skill_name: str
    capability: str
    complexity: int
    input_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_keys", freeze_tuple(self.input_keys))


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkflowTemplate:
    template_id: str
    description: str
    steps: tuple[StepTemplate, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", freeze_tuple(self.steps))


@dataclass(frozen=True, kw_only=True, slots=True)
class PlanStep:
    step_id: str
    title: str
    skill_name: str
    capability: str
    complexity: int
    inputs: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", freeze_mapping(self.inputs))


@dataclass(frozen=True, kw_only=True, slots=True)
class Plan:
    objective: str
    template_id: str
    steps: tuple[PlanStep, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", freeze_tuple(self.steps))


@dataclass(frozen=True, kw_only=True, slots=True)
class ToolCall:
    tool_name: str
    arguments: Mapping[str, object]
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", freeze_mapping(self.arguments))


@dataclass(frozen=True, kw_only=True, slots=True)
class ToolResult:
    tool_name: str
    output: object


@dataclass(frozen=True, kw_only=True, slots=True)
class ModelProfile:
    model_id: str
    capabilities: frozenset[str]
    max_complexity: int
    cost_rank: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))


@dataclass(frozen=True, kw_only=True, slots=True)
class RouteDecision:
    step_id: str
    model_id: str
    reason: str


@dataclass(frozen=True, kw_only=True, slots=True)
class SkillResult:
    step_id: str
    skill_name: str
    output: object
    model_id: str


@dataclass(frozen=True, kw_only=True, slots=True)
class TraceEvent:
    index: int
    kind: str
    message: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", freeze_mapping(self.payload))


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkflowResult:
    objective: str
    template_id: str
    step_results: tuple[SkillResult, ...]
    events: tuple[TraceEvent, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_results", freeze_tuple(self.step_results))
        object.__setattr__(self, "events", freeze_tuple(self.events))
