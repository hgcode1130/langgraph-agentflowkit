import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Database,
  Download,
  FlaskConical,
  Play,
  RefreshCw,
  Server,
  UsersRound,
} from "lucide-react";
import "./styles.css";

const DEFAULT_INPUTS = {
  topic: "LangGraph 多智能体工作流中间件",
  requirements: "任务规划、ReAct 工具调用、技能注册、模型路由、执行轨迹记录",
};

const FALLBACK_AGENTS = {
  research_skill: {
    agent_name: "研究 Agent",
    role: "资料分析与事实提取",
    responsibility: "负责理解任务背景、提取关键事实，并形成研究要点。",
    order: 1,
  },
  write_skill: {
    agent_name: "写作 Agent",
    role: "实验报告组织与生成",
    responsibility: "负责将研究要点组织为实验报告草稿。",
    order: 2,
  },
  review_skill: {
    agent_name: "审查 Agent",
    role: "质量审查与需求覆盖检查",
    responsibility: "负责从学术性、结构性、需求覆盖度和可验证性角度审查输出。",
    order: 3,
  },
};

const STATUS_LABELS = {
  completed: "已完成",
  failed: "失败",
  pending: "执行中",
};

const EVENT_LABELS = {
  plan: "任务规划",
  route: "模型路由",
  skill: "Agent 执行",
  thought: "思考",
  action: "工具调用",
  observation: "工具反馈",
  finish: "完成",
};

const MODE_LABELS = {
  local: "本地确定性演示",
  deepseek: "DeepSeek 大模型验证",
  grok: "Grok 大模型验证",
};

function App() {
  const [templates, setTemplates] = useState([]);
  const [agents, setAgents] = useState([]);
  const [models, setModels] = useState(null);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [objective, setObjective] = useState(
    "生成一份关于 LangGraph 多智能体工作流中间件的简明实验报告。",
  );
  const [templateId, setTemplateId] = useState("middleware_report");
  const [mode, setMode] = useState("local");
  const [inputsText, setInputsText] = useState(JSON.stringify(DEFAULT_INPUTS, null, 2));
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    setError("");
    const [templatesData, modelsData, runsData] = await Promise.all([
      apiGet("/api/templates"),
      apiGet("/api/models"),
      apiGet("/api/runs"),
    ]);
    setTemplates(templatesData.templates);
    setAgents(templatesData.agents || []);
    setModels(modelsData);
    setRuns(runsData.runs);
    if (!selectedRun && runsData.runs.length > 0) {
      setSelectedRun(runsData.runs[0]);
    }
  }

  async function runWorkflow() {
    setLoading(true);
    setError("");
    try {
      const inputs = JSON.parse(inputsText);
      const run = await apiPost("/api/runs", {
        objective,
        template_id: templateId,
        mode,
        inputs,
      });
      setSelectedRun(run);
      const runsData = await apiGet("/api/runs");
      setRuns(runsData.runs);
    } catch (err) {
      setError(err.message || "工作流运行失败");
    } finally {
      setLoading(false);
    }
  }

  async function exportSelectedRun() {
    if (!selectedRun) {
      return;
    }
    setExporting(true);
    setError("");
    try {
      const exportedRun = await apiPost(`/api/runs/${selectedRun.run_id}/export`);
      setSelectedRun(exportedRun);
      const runsData = await apiGet("/api/runs");
      setRuns(runsData.runs);
    } catch (err) {
      setError(err.message || "导出运行结果失败");
    } finally {
      setExporting(false);
    }
  }

  async function selectRun(runId) {
    setError("");
    const detail = await apiGet(`/api/runs/${runId}`);
    setSelectedRun(detail);
  }

  const selectedTemplate = useMemo(
    () => templates.find((template) => template.template_id === templateId),
    [templates, templateId],
  );
  const chainAgents = useMemo(
    () => [...agents].sort((left, right) => left.order - right.order),
    [agents],
  );
  const events = selectedRun?.result?.events || [];
  const stepResults = selectedRun?.result?.step_results || [];

  return (
    <main className="console">
      <aside className="sidebar">
        <div className="brand">
          <FlaskConical size={23} />
          <div>
            <h1>AgentFlowKit</h1>
            <span>多 Agent 工作流中间件控制台</span>
          </div>
        </div>

        <button className="ghost-button" type="button" onClick={refreshAll}>
          <RefreshCw size={16} />
          刷新状态
        </button>

        <section className="panel compact">
          <h2>运行历史</h2>
          <div className="run-list">
            {runs.length === 0 ? (
              <p className="muted">暂无运行记录。</p>
            ) : (
              runs.map((run) => (
                <button
                  key={run.run_id}
                  className={`run-item ${
                    selectedRun?.run_id === run.run_id ? "active" : ""
                  }`}
                  type="button"
                  onClick={() => selectRun(run.run_id)}
                >
                  <StatusIcon status={run.status} />
                  <span>
                    <strong>{STATUS_LABELS[run.status] || run.status}</strong>
                    <small>
                      {MODE_LABELS[run.request?.mode || "local"]} /{" "}
                      {formatDate(run.created_at)}
                    </small>
                  </span>
                  <ChevronRight size={15} />
                </button>
              ))
            )}
          </div>
        </section>

        <section className="panel compact">
          <h2>运行环境</h2>
          <InfoLine icon={<Server size={15} />} label="后端服务" value="FastAPI" />
          <InfoLine icon={<Database size={15} />} label="记录存储" value="内存" />
          <ProviderLine name="DeepSeek" provider={models?.deepseek} />
          <ProviderLine name="Grok" provider={models?.grok} />
          <p className="config-note">
            配置读取顺序：进程环境变量优先，其次读取 api/.env 文件。
          </p>
        </section>
      </aside>

      <section className="workspace">
        <section className="panel form-panel">
          <div className="section-heading">
            <div>
              <h2>新建多 Agent 工作流实验</h2>
              <p>提交任务，观察 Planner、Agent 分工、模型路由和执行轨迹。</p>
            </div>
            <button
              className="primary-button"
              type="button"
              onClick={runWorkflow}
              disabled={loading}
            >
              <Play size={17} />
              {loading ? "运行中" : "开始运行"}
            </button>
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="form-grid">
            <label>
              <span>任务目标</span>
              <textarea
                value={objective}
                rows={4}
                onChange={(event) => setObjective(event.target.value)}
              />
            </label>
            <div className="stacked-fields">
              <label>
                <span>工作流模板</span>
                <select
                  value={templateId}
                  onChange={(event) => setTemplateId(event.target.value)}
                >
                  {templates.map((template) => (
                    <option key={template.template_id} value={template.template_id}>
                      {template.template_id}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>运行模式</span>
                <select value={mode} onChange={(event) => setMode(event.target.value)}>
                  <option value="local">本地确定性演示</option>
                  <option value="deepseek">DeepSeek 大模型验证</option>
                  <option value="grok">Grok 大模型验证</option>
                </select>
              </label>
            </div>

            <label className="wide">
              <span>输入参数 JSON</span>
              <textarea
                className="code-input"
                value={inputsText}
                rows={8}
                onChange={(event) => setInputsText(event.target.value)}
              />
            </label>
          </div>
        </section>

        <AgentChain agents={chainAgents} />

        {selectedTemplate ? (
          <section className="panel">
            <div className="section-heading tight">
              <div>
                <h2>模板中的 Agent 分工</h2>
                <p>底层仍由 Skill 执行，展示层将其包装为 Agent 协作单元。</p>
              </div>
            </div>
            <div className="template-steps">
              {selectedTemplate.steps.map((step, index) => {
                const agent = step.agent || FALLBACK_AGENTS[step.skill_name];
                return (
                  <article key={step.step_id} className="template-agent-card">
                    <strong>
                      {index + 1}. {agent?.agent_name || step.skill_name}
                    </strong>
                    <span>{agent?.role || step.capability}</span>
                    <p>{agent?.responsibility || step.title}</p>
                    <code>{step.skill_name}</code>
                  </article>
                );
              })}
            </div>
          </section>
        ) : null}

        <section className="content-grid">
          <section className="panel">
            <div className="section-heading tight">
              <div>
                <h2>Agent 协作结果</h2>
                <p>{selectedRun ? selectedRun.run_id : "尚未选择运行记录"}</p>
              </div>
              {selectedRun ? <StatusPill status={selectedRun.status} /> : null}
            </div>
            <ExportPanel
              run={selectedRun}
              exporting={exporting}
              onExport={exportSelectedRun}
            />
            {selectedRun ? (
              <>
                {selectedRun.error ? (
                  <div className="error-banner">{selectedRun.error}</div>
                ) : null}
                <div className="step-results">
                  {stepResults.map((step, index) => {
                    const agent = step.agent || FALLBACK_AGENTS[step.skill_name];
                    return (
                      <article key={step.step_id} className="step-card">
                        <div className="step-meta">
                          <strong>
                            {index + 1}. {agent?.agent_name || step.step_id}
                          </strong>
                          <small>路由模型：{step.model_id}</small>
                        </div>
                        <div className="agent-detail-line">
                          <span>绑定技能：{step.skill_name}</span>
                          <span>职责：{agent?.role || "未声明"}</span>
                        </div>
                        <p>{String(step.output)}</p>
                      </article>
                    );
                  })}
                  {stepResults.length === 0 ? (
                    <p className="muted">当前运行暂无 Agent 输出。</p>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="muted">运行一个工作流后将在此展示 Agent 输出。</p>
            )}
          </section>

          <section className="panel">
            <div className="section-heading tight">
              <div>
                <h2>执行轨迹</h2>
                <p>{events.length} 条事件记录</p>
              </div>
              <Clock3 size={18} />
            </div>
            <div className="timeline">
              {events.map((event) => (
                <article key={event.index} className="event-row">
                  <span className="event-index">{event.index}</span>
                  <div>
                    <strong>
                      {EVENT_LABELS[event.kind] || event.kind}
                      <em>{event.kind}</em>
                    </strong>
                    <p>{event.message}</p>
                    <code>{JSON.stringify(event.payload)}</code>
                  </div>
                </article>
              ))}
              {events.length === 0 ? (
                <p className="muted">当前运行暂无执行轨迹。</p>
              ) : null}
            </div>
          </section>
        </section>

        <section className="panel json-panel">
          <div className="section-heading tight">
            <div>
              <h2>原始运行数据</h2>
              <p>用于调试与实验复现的完整 JSON 记录</p>
            </div>
          </div>
          <pre>{selectedRun ? JSON.stringify(selectedRun, null, 2) : "{}"}</pre>
        </section>
      </section>
    </main>
  );
}

function ProviderLine({ name, provider }) {
  const configured = Boolean(provider?.configured);
  return (
    <>
      <InfoLine
        icon={<Activity size={15} />}
        label={name}
        value={configured ? "已配置" : "未配置"}
      />
      <p className="config-note">
        {configured
          ? `${provider?.model} / ${provider?.base_url}`
          : `${name} 缺少 API Key，无法使用该模式。`}
      </p>
    </>
  );
}

function ExportPanel({ run, exporting, onExport }) {
  if (!run) {
    return null;
  }
  if (run.status !== "completed") {
    return <div className="export-panel muted">当前状态不可导出。</div>;
  }
  if (run.exports) {
    return (
      <div className="export-panel exported">
        <strong>结果已导出</strong>
        <span>目录：{run.exports.directory}</span>
        <span>JSON：{run.exports.json_path}</span>
        <span>Markdown：{run.exports.markdown_path}</span>
      </div>
    );
  }
  return (
    <div className="export-panel">
      <span>尚未导出。点击后将在项目 result 目录下生成本次运行文件夹。</span>
      <button
        className="secondary-button"
        type="button"
        onClick={onExport}
        disabled={exporting}
      >
        <Download size={16} />
        {exporting ? "导出中" : "导出到本地"}
      </button>
    </div>
  );
}

function AgentChain({ agents }) {
  return (
    <section className="panel agent-chain-panel">
      <div className="section-heading tight">
        <div>
          <h2>Agent 协作链路</h2>
          <p>用户任务经 Planner 拆解后，交由多个 Agent 分工执行并汇总。</p>
        </div>
        <UsersRound size={19} />
      </div>
      <div className="agent-chain">
        <div className="chain-node input-node">
          <strong>用户任务</strong>
          <span>实验目标输入</span>
        </div>
        <ChainArrow />
        <div className="chain-node planner-node">
          <strong>Planner</strong>
          <span>任务规划与步骤拆解</span>
        </div>
        {agents.map((agent) => (
          <React.Fragment key={agent.agent_id}>
            <ChainArrow />
            <div className="chain-node agent-node">
              <strong>{agent.agent_name}</strong>
              <span>{agent.role}</span>
            </div>
          </React.Fragment>
        ))}
        <ChainArrow />
        <div className="chain-node output-node">
          <strong>最终结果</strong>
          <span>结构化报告与轨迹</span>
        </div>
      </div>
    </section>
  );
}

function ChainArrow() {
  return <span className="chain-arrow">-&gt;</span>;
}

function StatusIcon({ status }) {
  if (status === "completed") {
    return <CheckCircle2 className="ok" size={17} />;
  }
  if (status === "failed") {
    return <AlertCircle className="bad" size={17} />;
  }
  return <Clock3 className="pending" size={17} />;
}

function StatusPill({ status }) {
  return <span className={`status-pill ${status}`}>{STATUS_LABELS[status] || status}</span>;
}

function InfoLine({ icon, label, value }) {
  return (
    <div className="info-line">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

async function apiGet(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`GET ${path} failed: ${response.status}`);
  }
  return response.json();
}

async function apiPost(path, body = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed: ${response.status}`);
  }
  return response.json();
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

createRoot(document.getElementById("root")).render(<App />);
