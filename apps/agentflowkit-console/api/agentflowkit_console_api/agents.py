from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class AgentProfile:
    agent_id: str
    agent_name: str
    skill_name: str
    role: str
    responsibility: str
    capability: str
    tools: tuple[str, ...]
    order: int

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["tools"] = list(self.tools)
        return data


AGENT_PROFILES: tuple[AgentProfile, ...] = (
    AgentProfile(
        agent_id="research_agent",
        agent_name="研究 Agent",
        skill_name="research_skill",
        role="资料分析与事实提取",
        responsibility="负责理解任务背景、提取关键事实，并形成可供后续写作使用的研究要点。",
        capability="research",
        tools=("lookup", "extract_research_notes"),
        order=1,
    ),
    AgentProfile(
        agent_id="write_agent",
        agent_name="写作 Agent",
        skill_name="write_skill",
        role="实验报告组织与生成",
        responsibility="负责将研究要点组织为结构清晰、表达规范的实验报告草稿。",
        capability="write",
        tools=("compose_report", "structure_report"),
        order=2,
    ),
    AgentProfile(
        agent_id="review_agent",
        agent_name="审查 Agent",
        skill_name="review_skill",
        role="质量审查与需求覆盖检查",
        responsibility="负责从学术性、结构性、需求覆盖度和可验证性角度审查输出。",
        capability="review",
        tools=("check_requirements", "score_report"),
        order=3,
    ),
)


def agent_profiles() -> tuple[AgentProfile, ...]:
    return AGENT_PROFILES


def agent_profile_for_skill(skill_name: str) -> AgentProfile:
    for profile in AGENT_PROFILES:
        if profile.skill_name == skill_name:
            return profile
    raise KeyError(f"Unknown agent skill: {skill_name}")


def agent_dict_for_skill(skill_name: str) -> dict[str, object] | None:
    try:
        return agent_profile_for_skill(skill_name).to_dict()
    except KeyError:
        return None
