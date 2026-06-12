from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTFLOWKIT_SRC = REPO_ROOT / "libs" / "agentflowkit"
if str(AGENTFLOWKIT_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTFLOWKIT_SRC))

from agentflowkit import (  # noqa: E402
    LLMPlanner,
    OpenAICompatibleChatModel,
    SkillContext,
    SkillRegistry,
    SkillSpec,
    TaskRequest,
)
from agentflowkit.tracing import to_jsonable  # noqa: E402


def main() -> None:
    skills = _skills()
    planner = LLMPlanner(OpenAICompatibleChatModel.from_env(), skills)
    plan = planner.plan(
        TaskRequest(
            objective=(
                "Plan a richer AgentFlowKit course demo that shows planning, "
                "model routing, ReAct tool use, and execution tracing."
            ),
            template_id="grok_dynamic_plan",
            inputs={
                "audience": "middleware course evaluator",
                "available_minutes": 2,
            },
        )
    )
    print(json.dumps(to_jsonable(plan), ensure_ascii=False, indent=2))


def _skills() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        SkillSpec(
            name="research_skill",
            description="Collect compact technical facts.",
            handler=_finish_only,
        )
    )
    registry.register(
        SkillSpec(
            name="write_skill",
            description="Draft concise output.",
            handler=_finish_only,
        )
    )
    registry.register(
        SkillSpec(
            name="review_skill",
            description="Check requirement fit.",
            handler=_finish_only,
        )
    )
    return registry


def _finish_only(context: SkillContext) -> str:
    return str(context.finish("not executed in planner-only demo"))


if __name__ == "__main__":
    main()
