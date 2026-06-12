from __future__ import annotations

from agentflowkit.errors import ModelRoutingError
from agentflowkit.models import ModelProfile, PlanStep, RouteDecision


class CapabilityRouter:
    def __init__(self, profiles: tuple[ModelProfile, ...]) -> None:
        if not profiles:
            raise ModelRoutingError("At least one model profile is required")
        self._profiles = tuple(profiles)

    def route(self, step: PlanStep) -> RouteDecision:
        candidates = self._eligible_profiles(step)
        if not candidates:
            raise ModelRoutingError(
                f"No model can handle step {step.step_id}: "
                f"capability={step.capability}, complexity={step.complexity}"
            )
        profile = sorted(candidates, key=lambda item: item.cost_rank)[0]
        return RouteDecision(
            step_id=step.step_id,
            model_id=profile.model_id,
            reason=self._reason(step, profile),
        )

    def _eligible_profiles(self, step: PlanStep) -> tuple[ModelProfile, ...]:
        return tuple(
            profile
            for profile in self._profiles
            if step.capability in profile.capabilities
            and step.complexity <= profile.max_complexity
        )

    def _reason(self, step: PlanStep, profile: ModelProfile) -> str:
        return (
            f"Selected {profile.model_id} for {step.capability} "
            f"at complexity {step.complexity}"
        )
