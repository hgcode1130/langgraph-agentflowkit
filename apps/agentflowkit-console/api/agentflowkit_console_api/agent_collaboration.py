from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentflowkit import SkillContext


@dataclass(slots=True)
class AgentHandoffState:
    artifacts: dict[str, Any] = field(default_factory=dict)

    def read(self, artifact: str) -> Any:
        return self.artifacts.get(artifact)

    def write(self, artifact: str, value: Any) -> None:
        self.artifacts[artifact] = value

    def output(
        self,
        *,
        artifact: str,
        content: Any,
        received_artifacts: tuple[str, ...],
        handoff: dict[str, object],
    ) -> dict[str, object]:
        self.write(artifact, content)
        return {
            "artifact": artifact,
            "content": content,
            "received_artifacts": list(received_artifacts),
            "handoff": handoff,
        }


def record_handoff(
    context: SkillContext,
    *,
    from_agent: str,
    to_agent: str,
    artifact: str,
) -> dict[str, object]:
    payload = {
        "step_id": context.step_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "artifact": artifact,
    }
    message = f"{from_agent} 将 {artifact} 传递给 {to_agent}"
    trace = getattr(context, "_trace")
    trace("handoff", message, payload)
    return payload
