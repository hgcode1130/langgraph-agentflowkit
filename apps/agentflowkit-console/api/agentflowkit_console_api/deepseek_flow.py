from __future__ import annotations

from collections.abc import Callable, Mapping

from agentflowkit import (
    AgentFlow,
    AgentFlowComponents,
    CapabilityRouter,
    ChatModel,
    LLMPlanner,
    ModelProfile,
    SkillContext,
    SkillRegistry,
    SkillSpec,
    TaskRequest,
    ToolRegistry,
)

from agentflowkit_console_api.agents import agent_profile_for_skill
from agentflowkit_console_api.config import (
    ProviderSettings,
    create_deepseek_chat_model,
    create_grok_chat_model,
    deepseek_settings,
    grok_settings,
)


class ProviderNotConfiguredError(RuntimeError):
    pass


class DeepSeekNotConfiguredError(ProviderNotConfiguredError):
    pass


class GrokNotConfiguredError(ProviderNotConfiguredError):
    pass


def build_deepseek_flow(request: TaskRequest, model: ChatModel | None = None) -> AgentFlow:
    try:
        return _build_llm_flow(
            request=request,
            settings=deepseek_settings(),
            model_factory=create_deepseek_chat_model,
            model=model,
        )
    except ProviderNotConfiguredError as exc:
        raise DeepSeekNotConfiguredError(str(exc)) from exc


def build_grok_flow(request: TaskRequest, model: ChatModel | None = None) -> AgentFlow:
    try:
        return _build_llm_flow(
            request=request,
            settings=grok_settings(),
            model_factory=create_grok_chat_model,
            model=model,
        )
    except ProviderNotConfiguredError as exc:
        raise GrokNotConfiguredError(str(exc)) from exc


def _build_llm_flow(
    *,
    request: TaskRequest,
    settings: ProviderSettings,
    model_factory: Callable[[], ChatModel | None],
    model: ChatModel | None = None,
) -> AgentFlow:
    chat_model = model or model_factory()
    if chat_model is None:
        raise ProviderNotConfiguredError(f"{settings.label} 未配置，请设置项目 .env 文件或环境变量。")

    skills = _build_llm_skills(request, chat_model, settings)
    planner = LLMPlanner(chat_model, skills)
    router = CapabilityRouter(_provider_profiles(settings))
    return AgentFlow(
        AgentFlowComponents(
            planner=planner,
            skills=skills,
            tools=ToolRegistry(),
            router=router,
        )
    )


def _provider_profiles(settings: ProviderSettings) -> tuple[ModelProfile, ...]:
    return (
        ModelProfile(
            model_id=settings.model or settings.provider_id,
            capabilities=frozenset({"research", "write", "review", "code", "tool"}),
            max_complexity=5,
            cost_rank=1,
        ),
    )


def _build_llm_skills(
    request: TaskRequest, model: ChatModel, settings: ProviderSettings
) -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        SkillSpec(
            name="research_skill",
            description=agent_profile_for_skill("research_skill").responsibility,
            handler=lambda context: _run_llm_agent(
                context,
                model,
                request,
                settings,
                "research_skill",
                "请围绕任务目标和输入参数生成结构化研究要点，突出 LangGraph 功能增改如何被验证。",
            ),
        )
    )
    registry.register(
        SkillSpec(
            name="write_skill",
            description=agent_profile_for_skill("write_skill").responsibility,
            handler=lambda context: _run_llm_agent(
                context,
                model,
                request,
                settings,
                "write_skill",
                "请生成一份简明实验报告草稿，包含背景、方法、执行链路、结果解释和结论。",
            ),
        )
    )
    registry.register(
        SkillSpec(
            name="review_skill",
            description=agent_profile_for_skill("review_skill").responsibility,
            handler=lambda context: _run_llm_agent(
                context,
                model,
                request,
                settings,
                "review_skill",
                "请从学术性、结构性、需求覆盖度和可验证性四个角度审查输出，并给出改进建议。",
            ),
        )
    )
    return registry


def _run_llm_agent(
    context: SkillContext,
    model: ChatModel,
    request: TaskRequest,
    settings: ProviderSettings,
    skill_name: str,
    instruction: str,
) -> str:
    profile = agent_profile_for_skill(skill_name)
    context.think(f"{profile.agent_name} 正在调用 {settings.label} 生成当前 Agent 的实验内容。")
    content = model.complete(
        (
            {
                "role": "system",
                "content": (
                    "你是 AgentFlowKit 多智能体工作流系统中的一个专门 Agent。"
                    f"当前身份：{profile.agent_name}。"
                    f"角色定位：{profile.role}。"
                    f"职责边界：{profile.responsibility}"
                    "请始终使用中文回答，表达应清晰、学术化、结构化、可验证。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"任务目标：{request.objective}\n"
                    f"工作流模板：{request.template_id}\n"
                    f"输入参数：\n{_format_inputs(request.inputs)}\n"
                    f"当前 Agent 指令：{instruction}\n"
                    "请明确体现你作为当前 Agent 的分工，不要泛泛回答。"
                ),
            },
        )
    )
    return str(context.finish(content))


def _format_inputs(inputs: Mapping[str, object]) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in inputs.items())
