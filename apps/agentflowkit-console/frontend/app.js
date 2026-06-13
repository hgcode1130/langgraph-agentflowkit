const state = {
  planner: "template",
  plan: null,
  result: null,
};

const el = (id) => document.getElementById(id);

function payload() {
  return {
    planner: state.planner,
    objective: el("objective").value,
    topic: el("topic").value,
    requirements: el("requirements").value,
    template_id: "middleware_report",
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `Request failed: ${path}`);
  }
  return data;
}

async function refreshHealth() {
  try {
    const [health, caps] = await Promise.all([
      api("/api/health"),
      api("/api/capabilities"),
    ]);
    el("healthDot").className = "dot ok";
    el("healthText").textContent = health.service;
    el("providerBadge").textContent = providerText(caps.provider);
  } catch (error) {
    el("healthDot").className = "dot bad";
    el("healthText").textContent = error.message;
  }
}

function providerText(provider) {
  const key = provider?.api_key ? "key ready" : "no key";
  const model = provider?.model || "model unset";
  return `${model} · ${key}`;
}

function setPlanner(planner) {
  state.planner = planner;
  el("templateMode").classList.toggle("active", planner === "template");
  el("grokMode").classList.toggle("active", planner === "grok");
  el("plannerBadge").textContent = planner;
}

async function preview() {
  setBusy("planning");
  const data = await api("/api/workflows/preview", {
    method: "POST",
    body: JSON.stringify(payload()),
  });
  state.plan = data.plan;
  state.result = null;
  renderGraph(data.plan?.steps || []);
  renderTrace([]);
  renderOutput(data);
  setReady("plan ready");
}

async function run() {
  setBusy("running");
  const data = await api("/api/workflows/run", {
    method: "POST",
    body: JSON.stringify(payload()),
  });
  const result = data.result;
  state.plan = data.plan || {
    objective: result.objective,
    template_id: result.template_id,
    steps: result.step_results || [],
  };
  state.result = result;
  renderGraphFromResult(data);
  renderTrace(result.events || []);
  renderOutput(data);
  setReady("run complete");
}

async function smokeTest() {
  setBusy("testing provider");
  const data = await api("/api/providers/grok/smoke-test", { method: "POST" });
  renderOutput(data);
  setReady("provider ok");
}

function renderGraphFromResult(data) {
  const steps = data.plan?.steps || resultSteps(data.result);
  renderGraph(steps, data.result?.step_results || []);
}

function resultSteps(result) {
  return (result?.step_results || []).map((step) => ({
    step_id: step.step_id,
    title: step.step_id,
    skill_name: step.skill_name,
    capability: "executed",
    complexity: "",
    model_id: step.model_id,
  }));
}

function renderGraph(steps, results = []) {
  if (!steps.length) {
    el("graph").innerHTML = `<div class="trace-empty">Generate a plan to populate the workflow graph.</div>`;
    return;
  }
  const resultByStep = Object.fromEntries(results.map((item) => [item.step_id, item]));
  el("graph").innerHTML = steps
    .map((step, index) => {
      const result = resultByStep[step.step_id] || {};
      const model = result.model_id || step.model_id || "pending";
      return `
        <article class="node">
          <div class="node-index">${index + 1}</div>
          <div>
            <p class="node-title">${escapeHtml(step.title || step.step_id)}</p>
            <div class="node-meta">
              <span class="pill">${escapeHtml(step.skill_name || "skill")}</span>
              <span class="pill">${escapeHtml(step.capability || "capability")}</span>
              <span class="pill">complexity ${escapeHtml(String(step.complexity || "-"))}</span>
            </div>
          </div>
          <span class="badge">${escapeHtml(model)}</span>
        </article>
      `;
    })
    .join("");
}

function renderTrace(events) {
  el("eventCount").textContent = `${events.length} events`;
  if (!events.length) {
    el("trace").className = "trace-empty";
    el("trace").innerHTML = "Run a workflow to inspect trace events.";
    return;
  }
  el("trace").className = "trace-list";
  el("trace").innerHTML = events
    .map(
      (event) => `
      <article class="event">
        <div class="event-top">
          <span class="event-kind">${event.index}. ${escapeHtml(event.kind)}</span>
          <span class="badge">${escapeHtml(event.payload?.step_id || "workflow")}</span>
        </div>
        <p class="event-message">${escapeHtml(event.message)}</p>
        <pre>${escapeHtml(JSON.stringify(event.payload || {}, null, 2))}</pre>
      </article>
    `,
    )
    .join("");
}

function renderOutput(data) {
  el("output").textContent = JSON.stringify(data, null, 2);
}

function setBusy(text) {
  el("outputBadge").textContent = text;
}

function setReady(text) {
  el("outputBadge").textContent = text;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function bind() {
  el("templateMode").addEventListener("click", () => setPlanner("template"));
  el("grokMode").addEventListener("click", () => setPlanner("grok"));
  el("previewBtn").addEventListener("click", () => preview().catch(showError));
  el("runBtn").addEventListener("click", () => run().catch(showError));
  el("smokeBtn").addEventListener("click", () => smokeTest().catch(showError));
}

function showError(error) {
  setReady("error");
  renderOutput({ ok: false, error: error.message });
}

bind();
refreshHealth();
renderGraph([]);
