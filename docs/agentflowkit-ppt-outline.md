# 基于 LangGraph 的多 Agent 工作流中间件扩展研究与实现：PPT 大纲

## 汇报定位

本 PPT 用于约 8 分钟项目讲解，重点说明本项目如何在 LangGraph 的图执行能力基础上，扩展实现一个具备任务规划、多 Agent 协作、ReAct-like 工具调用、模型路由、Agent 输出传递和执行轨迹可视化能力的工作流中间件原型系统。

---

## 第 1 页：项目标题与研究目标

### 标题

基于 LangGraph 的多 Agent 工作流中间件扩展研究与实现

### 页面内容

- 项目目标：在 LangGraph 基础上实现一个可规划、可路由、可追踪、可视化的多 Agent 工作流中间件。
- 核心关键词：
  - LangGraph
  - 多 Agent 协作
  - Planner 任务拆解
  - ReAct 工具调用
  - Skill/Tool 注册
  - 模型路由
  - 执行轨迹可视化
- 最终成果：
  - AgentFlowKit 中间件
  - FastAPI 后端
  - React 前端工作流控制台
  - DeepSeek/Grok 大模型验证模式

### 建议图示

```text
用户任务 -> Planner -> 多 Agent 协作 -> 工具调用/模型路由 -> 执行轨迹 -> 结果输出
```

### 讲解重点

本项目不是简单调用大模型，而是在 LangGraph 之上扩展出一个多 Agent 工作流中间件层。

---

## 第 2 页：研究背景：为什么选择 LangGraph

### 标题

LangGraph：面向有状态智能体工作流的图执行框架

### 页面内容

- LangGraph 的核心能力：
  - 使用图结构组织节点和状态流转
  - 支持有状态执行
  - 支持 checkpoint、stream、interrupt 等复杂工作流能力
  - 适合构建长流程、可恢复、可观测的 Agent 系统
- LangGraph 的基础抽象：
  - `StateGraph`
  - Node
  - Edge
  - State
  - Pregel 执行模型
  - Checkpoint

### 项目中的体现

- 项目保留 LangGraph 核心框架能力。
- 在 `libs/agentflowkit/agentflowkit/graph.py` 中提供 `build_langgraph_workflow`。
- 可以将 AgentFlow 包装为 LangGraph `StateGraph`。

### 讲解重点

LangGraph 提供的是底层图执行能力，但多 Agent 协作中的角色分工、规划、工具集、模型路由、过程追踪需要上层中间件进一步补充。

---

## 第 3 页：原始 LangGraph 的不足与扩展动机

### 标题

从图执行框架到多 Agent 工作流中间件

### 页面内容

原始 LangGraph 更偏底层：

- 关注节点如何连接。
- 关注状态如何流转。
- 关注执行如何持久化。
- 不直接规定多 Agent 系统中的角色、工具、路由和协作协议。

本项目希望补充：

- 任务如何自动拆解。
- 每个任务步骤由哪个 Agent 执行。
- Agent 能使用哪些工具。
- 不同 Agent 的输出如何传递。
- 复杂度不同的步骤如何选择模型。
- 整个过程如何可视化追踪。

### 对比表

| 能力 | LangGraph 原有能力 | 本项目扩展 |
|---|---|---|
| 图执行 | 有 | 复用 |
| 状态流转 | 有 | 复用 |
| Agent 角色 | 弱 | 新增 |
| 任务规划 | 需要用户构造 | 新增 Planner |
| 工具注册 | 需自行组织 | 新增 ToolRegistry |
| 模型路由 | 需自行实现 | 新增 CapabilityRouter |
| 执行轨迹 | 有基础事件 | 新增 Agent Trace/Handoff |

### 讲解重点

我们的工作不是替代 LangGraph，而是在 LangGraph 上增加一层多 Agent 工作流中间件。

---

## 第 4 页：系统总体架构

### 标题

AgentFlowKit 中间件总体架构

### 页面内容

系统分为三层：

1. LangGraph 基础层
   - 图执行
   - 状态管理
   - checkpoint 能力
2. AgentFlowKit 中间件层
   - Planner
   - Agent/Skill Registry
   - Tool Registry
   - Capability Router
   - Execution Tracer
   - Agent Handoff
3. Web 控制台层
   - 任务输入
   - 运行模式选择
   - Agent 协作链路展示
   - 执行轨迹展示
   - 结果导出

### 架构图

```text
前端控制台
  |
FastAPI API
  |
AgentFlowKit
  |-- Planner / LLMPlanner
  |-- Agent Profiles
  |-- SkillRegistry
  |-- ToolRegistry
  |-- CapabilityRouter
  |-- ExecutionTracer
  |-- AgentHandoffState
  |
LangGraph
  |-- StateGraph
  |-- Pregel Runtime
  |-- Checkpoint
```

### 讲解重点

AgentFlowKit 是连接 LangGraph 和实际多 Agent 应用场景的中间层。

---

## 第 5 页：多 Agent 设计：Agent = 模型 + 角色 + 工具 + 执行逻辑

### 标题

多 Agent 的显式建模

### 页面内容

本项目中 Agent 定义为：

```text
Agent = 大模型 + 角色提示词 + 可用工具 + 执行逻辑
```

当前实现了三个 Agent：

| Agent | 角色 | 可用工具 | 产出 |
|---|---|---|---|
| 研究 Agent | 资料分析与事实提取 | `lookup`, `extract_research_notes` | `research_notes` |
| 写作 Agent | 实验报告组织与生成 | `compose_report`, `structure_report` | `report_draft` |
| 审查 Agent | 质量审查与需求覆盖检查 | `check_requirements`, `score_report` | `review_result` |

### 项目中的体现

- `AgentProfile`
- `agent_profiles`
- `SkillSpec`
- `SkillRegistry`
- `AgentHandoffState`

### 讲解重点

底层执行仍然使用 Skill，但在 API 和前端展示层，我们将 Skill 明确包装为 Agent，使系统具备清晰的多 Agent 语义。

---

## 第 6 页：Planner：任务规划智能体

### 标题

Planner：从用户目标到 Agent 执行计划

### 页面内容

输入：

```text
生成一份关于 LangGraph 多智能体工作流中间件的简明实验报告
```

Planner 输出：

```text
1. research -> 研究 Agent
2. write -> 写作 Agent
3. review -> 审查 Agent
```

项目中支持两类 Planner：

- `TemplatePlanner`
  - 基于预设模板
  - 稳定、可控、适合教学演示
- `LLMPlanner`
  - 调用 DeepSeek/Grok 生成 JSON 计划
  - 校验 step_id、skill_name、capability、complexity、inputs

### 页面展示重点

```text
用户任务
  ↓
Planner
  ↓
研究 Agent -> 写作 Agent -> 审查 Agent
```

### 讲解重点

Planner 是系统从用户自然语言目标进入结构化多 Agent 工作流的关键入口。

---

## 第 7 页：工作流-任务-Skill-Tool 执行机制

### 标题

从 Workflow 到 Skill/Tool 的执行链路

### 页面内容

执行链路：

```text
WorkflowTemplate
  -> Plan
  -> PlanStep
  -> Skill
  -> Tool
  -> ToolResult
  -> SkillResult
```

项目中的核心对象：

- `TaskRequest`
- `WorkflowTemplate`
- `Plan`
- `PlanStep`
- `SkillSpec`
- `ToolSpec`
- `WorkflowResult`

本地模式示例：

```text
研究 Agent:
lookup -> extract_research_notes

写作 Agent:
compose_report -> structure_report

审查 Agent:
check_requirements -> score_report
```

### 讲解重点

这是项目中 ReAct-like 循环和多 Agent 执行逻辑的基础。Agent 不是直接输出结果，而是根据角色、工具和上下文逐步执行。

---

## 第 8 页：ReAct 循环与执行轨迹追踪

### 标题

ReAct-like 执行循环：Thought -> Action -> Observation -> Finish

### 页面内容

本项目实现了简化但可观测的 ReAct-like 执行过程：

```text
thought：Agent 思考
action：调用工具
observation：工具返回
finish：Agent 完成当前步骤
handoff：将输出传递给下一个 Agent
```

示例 trace：

```text
plan：Planner 生成步骤
route：模型路由
skill：Agent 执行
thought：研究 Agent 正在生成 research_notes
action：调用 lookup
observation：工具返回事实材料
action：调用 extract_research_notes
handoff：研究 Agent 将 research_notes 传递给 写作 Agent
finish：研究 Agent 完成
```

### 项目中的体现

- `ExecutionTracer`
- `SkillContext.think`
- `SkillContext.call_tool`
- `SkillContext.finish`
- `record_handoff`

### 讲解重点

Trace 让整个 Agent 工作流从黑盒调用模型变成可解释、可复现、可观察的执行过程。

---

## 第 9 页：Agent 输出传递与协作链路

### 标题

Agent Handoff：让上游输出进入下游输入

### 页面内容

数据流：

```text
研究 Agent
  -> research_notes

写作 Agent
  receives: research_notes
  -> report_draft

审查 Agent
  receives: report_draft
  -> review_result
```

实现机制：

- `AgentHandoffState`
  - 维护内存 artifact
  - 提供 artifact 读写
- `record_handoff`
  - 记录 Agent 输出传递事件
- step result 增加：
  - `artifact`
  - `received_artifacts`
  - `handoff`

### 前端展示

- Agent 数据流：
  - `research_notes -> report_draft -> review_result`
- 执行轨迹：
  - `Agent 输出传递`

### 讲解重点

这一步是项目从多个步骤升级为多个 Agent 协作的关键，因为下一个 Agent 真正接收并使用了上一个 Agent 的输出。

---

## 第 10 页：模型路由与多模型验证

### 标题

CapabilityRouter：按能力与复杂度选择模型

### 页面内容

模型路由依据：

- `capability`
  - research
  - write
  - review
  - code
  - tool
- `complexity`
  - 1 到 5
- `cost_rank`
  - 成本优先级

示例：

```text
research step
capability = research
complexity = 3
候选模型 = DeepSeek / Grok / local profile
Router 选择满足能力和复杂度的模型
```

运行模式：

- 本地确定性演示
- DeepSeek 大模型验证
- Grok 大模型验证

### 项目中的体现

- `CapabilityRouter`
- `ModelProfile`
- `RouteDecision`
- `/api/models`
- 前端运行模式选择

### 讲解重点

模型路由使系统不是固定调用某一个模型，而是可以根据任务类型和复杂度选择合适模型，这是多 Agent 中间件的重要能力。

---

## 第 11 页：Web 控制台与新增功能场景

### 标题

从代码框架到可交互的 Agent 工作流控制台

### 页面内容

前端控制台能力：

- 输入任务目标。
- 编辑输入参数 JSON。
- 选择工作流模板。
- 选择运行模式。
- 查看 Agent 协作链路。
- 查看 Agent 工具集。
- 查看 Agent 数据流。
- 查看执行轨迹。
- 查看原始 JSON。
- 导出运行结果。

新增功能场景：

1. 多 Agent 实验报告生成
   - 研究 -> 写作 -> 审查
2. 大模型能力验证
   - DeepSeek/Grok 模式
3. 工作流教学演示
   - 展示 Planner、Agent、Tool、Router、Trace
4. Agent 过程可观测
   - 每一步输入、输出、工具和 handoff 可追踪
5. 可扩展任务模板
   - 未来可扩展代码审查、资料分析、方案生成等工作流

### 讲解重点

前端不是简单 UI，而是把中间件能力可视化，使多 Agent 工作流可以被观察、解释和演示。

---

## 第 12 页：总结与后续工作

### 标题

总结：基于 LangGraph 的多 Agent 工作流中间件扩展

### 页面内容

本项目完成的核心工作：

- 研究 LangGraph 图执行和状态流转机制。
- 在 LangGraph 之上实现 AgentFlowKit 中间件。
- 实现 Planner 任务拆解。
- 实现 Agent/Skill/Tool 注册体系。
- 实现独立 Agent 工具集。
- 实现 Agent 输出传递。
- 实现 ReAct-like 执行循环。
- 实现模型路由。
- 实现执行轨迹和前端可视化。
- 接入 DeepSeek/Grok 进行大模型验证。

项目定位：

```text
一个基于 LangGraph 的多 Agent 工作流中间件原型系统
```

后续可扩展方向：

- 原生 function calling 工具调用。
- 更复杂的 Agent 间通信协议。
- 长期记忆和数据库持久化。
- 更多工作流模板。
- 更细粒度的 LangGraph checkpoint 展示。
- 多模型性能与成本对比实验。

### 结束语

本项目将 LangGraph 从底层图执行框架扩展为一个具备规划、协作、路由、工具调用和可视化追踪能力的多 Agent 工作流中间件。

---

## 8 分钟时间分配建议

| 页码 | 内容 | 时间 |
|---|---|---|
| 1 | 项目目标 | 40 秒 |
| 2 | LangGraph 背景 | 45 秒 |
| 3 | 扩展动机 | 45 秒 |
| 4 | 系统架构 | 50 秒 |
| 5 | 多 Agent 建模 | 55 秒 |
| 6 | Planner | 45 秒 |
| 7 | Workflow-Skill-Tool | 50 秒 |
| 8 | ReAct 与 Trace | 55 秒 |
| 9 | Agent Handoff | 55 秒 |
| 10 | 模型路由 | 45 秒 |
| 11 | Web 控制台与场景 | 50 秒 |
| 12 | 总结 | 45 秒 |

总计约 8 分钟。
