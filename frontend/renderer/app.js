// AutoAI Desktop App - Main SPA
let currentPage = "board";
let projectDir = "";
let statusData = null;
let currentJobId = null;

// --- Navigation ---
document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    const page = item.dataset.page;
    navigateTo(page);
  });
});

function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.remove("active"));
  const active = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (active) active.classList.add("active");
  renderPage();
}

// --- Project State ---
async function loadStatus() {
  if (!projectDir) return;
  try {
    statusData = await AutoAIAPI.getStatus(projectDir);
    updateTopBar();
    updateRunStatus();
  } catch (e) {
    console.error("Failed to load status:", e);
  }
}

function updateTopBar() {
  if (!statusData) return;
  document.getElementById("project-name").textContent =
    statusData.goal ? statusData.goal.slice(0, 50) : t("topbar.noProject");
  const fp = statusData.features;
  if (fp && fp.total > 0) {
    document.getElementById("feature-progress").textContent = t("topbar.features", { passing: fp.passing, total: fp.total });
  } else {
    document.getElementById("feature-progress").textContent = "";
  }
}

function updateRunStatus() {
  const el = document.getElementById("run-status");
  const rawStatus = currentJobId ? "running" : (statusData ? statusData.last_status : "idle");
  el.className = `run-status ${rawStatus}`;
  const statusKey = rawStatus === "idle" ? "idle" : rawStatus;
  el.querySelector(".status-text").textContent = t("status." + statusKey) || (rawStatus.charAt(0).toUpperCase() + rawStatus.slice(1));

  const btnRun = document.getElementById("btn-run");
  const btnStop = document.getElementById("btn-stop");
  if (rawStatus === "running") {
    btnRun.style.display = "none";
    btnStop.style.display = "";
  } else {
    btnRun.style.display = "";
    btnStop.style.display = "none";
  }
}

// --- Run Controls ---
async function handleRun() {
  if (!projectDir) {
    openInitModal();
    return;
  }
  try {
    const result = await AutoAIAPI.startRun({
      project_dir: projectDir,
      max_iterations: 1,
      stop_on_error: true,
    });
    currentJobId = result.job.id;
    updateRunStatus();
    pollJob(currentJobId);
  } catch (e) {
    alert(t("errors.failedStart", { msg: e.message }));
  }
}

async function handleStop() {
  if (!currentJobId) return;
  try {
    await AutoAIAPI.stopRun({ job_id: currentJobId });
  } catch (e) {}
  currentJobId = null;
  updateRunStatus();
}

async function pollJob(jobId) {
  try {
    const result = await AutoAIAPI.getJob(jobId);
    const job = result.job;
    if (["finished", "failed", "blocked", "stopped"].includes(job.status)) {
      currentJobId = null;
      await loadStatus();
      renderPage();
    } else {
      setTimeout(() => pollJob(jobId), 1000);
    }
  } catch (e) {
    currentJobId = null;
    updateRunStatus();
  }
}

// --- Init Modal ---
function openInitModal() {
  document.getElementById("init-modal").classList.remove("hidden");
}

function closeInitModal() {
  document.getElementById("init-modal").classList.add("hidden");
}

async function handleInit(e) {
  e.preventDefault();
  try {
    statusData = await AutoAIAPI.initProject({
      project_dir: document.getElementById("init-project-dir").value,
      goal: document.getElementById("init-goal").value,
      feature_count: parseInt(document.getElementById("init-feature-count").value) || 50,
      agent_command: document.getElementById("init-agent-command").value || "claude -p",
      permission_mode: document.getElementById("init-permission-mode").value,
      collaboration_mode: document.getElementById("init-collaboration-mode").value,
    });
    projectDir = statusData.project_dir;
    closeInitModal();
    await loadStatus();
    renderPage();
  } catch (e) {
    alert(t("errors.initFailed", { msg: e.message }));
  }
}

// --- Task Detail Panel ---
function openTaskDetail(task) {
  const panel = document.getElementById("task-detail-panel");
  const content = document.getElementById("task-detail-content");
  panel.classList.remove("hidden");

  const statuses = ["backlog", "todo", "in_progress", "in_review", "done", "blocked"];
  const priorities = ["low", "medium", "high", "urgent"];

  content.innerHTML = `
    <div class="form-group">
      <label>${t("task.title")}</label>
      <input type="text" id="detail-title" value="${escHtml(task.title)}">
    </div>
    <div class="form-group">
      <label>${t("task.description")}</label>
      <textarea id="detail-desc">${escHtml(task.description)}</textarea>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>${t("task.status")}</label>
        <select id="detail-status">
          ${statuses.map((s) => `<option value="${s}" ${s === task.status ? "selected" : ""}>${t("board." + s.replace("in_progress", "inProgress").replace("in_review", "inReview"))}</option>`).join("")}
        </select>
      </div>
      <div class="form-group">
        <label>${t("task.priority")}</label>
        <select id="detail-priority">
          ${priorities.map((p) => `<option value="${p}" ${p === task.priority ? "selected" : ""}>${t("task.priority" + p.charAt(0).toUpperCase() + p.slice(1))}</option>`).join("")}
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>${t("task.assignee")}</label>
      <input type="text" id="detail-assignee" value="${escHtml(task.assignee)}">
    </div>
    <div class="form-actions">
      <button class="btn btn-primary" onclick="saveTaskDetail('${task.id}')">${t("task.save")}</button>
    </div>
  `;
}

function closeTaskDetail() {
  document.getElementById("task-detail-panel").classList.add("hidden");
}

async function saveTaskDetail(taskId) {
  try {
    await AutoAIAPI.updateTask(taskId, {
      project_dir: projectDir,
      title: document.getElementById("detail-title").value,
      description: document.getElementById("detail-desc").value,
      status: document.getElementById("detail-status").value,
      priority: document.getElementById("detail-priority").value,
      assignee: document.getElementById("detail-assignee").value,
    });
    closeTaskDetail();
    await loadStatus();
    renderPage();
  } catch (e) {
    alert(t("errors.failedSave", { msg: e.message }));
  }
}

// --- Page Router ---
async function renderPage() {
  const content = document.getElementById("page-content");
  switch (currentPage) {
    case "board":
      await renderBoard(content);
      break;
    case "agents":
      await renderAgents(content);
      break;
    case "sessions":
      await renderSessions(content);
      break;
    case "help":
      await renderHelp(content);
      break;
    case "settings":
      await renderSettings(content);
      break;
  }
}

// --- Board Page ---
async function renderBoard(container) {
  if (!projectDir) {
    container.innerHTML = `<div class="empty-state"><h3>${t("board.noProject")}</h3><p>${t("board.noProjectHint")}</p><br><button class="btn btn-primary" onclick="openInitModal()">${t("board.initButton")}</button></div>`;
    return;
  }
  let tasks = [];
  try {
    const result = await AutoAIAPI.getTasks(projectDir);
    tasks = result.tasks;
  } catch (e) {}

  const statuses = ["backlog", "todo", "in_progress", "in_review", "done", "blocked"];
  const statusLabels = {
    backlog: t("board.backlog"),
    todo: t("board.todo"),
    in_progress: t("board.inProgress"),
    in_review: t("board.inReview"),
    done: t("board.done"),
    blocked: t("board.blocked"),
  };

  let html = '<div class="board">';
  for (const status of statuses) {
    const statusTasks = tasks.filter((tr) => tr.status === status);
    html += `<div class="board-column" data-status="${status}">
      <div class="column-header">
        <span>${statusLabels[status]}</span>
        <span class="column-count">${statusTasks.length}</span>
      </div>
      <div class="column-body" ondragover="onDragOver(event)" ondrop="onDrop(event, '${status}')">`;
    for (const task of statusTasks) {
      html += `<div class="task-card" draggable="true" ondragstart="onDragStart(event, '${task.id}')" onclick="openTaskDetail(${escJsonAttr(task)})">
        <div class="task-title">${escHtml(task.title)}</div>
        <div class="task-meta">
          <span class="priority-badge priority-${task.priority}">${t("task.priority" + task.priority.charAt(0).toUpperCase() + task.priority.slice(1))}</span>
          ${task.assignee ? `<span class="assignee-badge">${escHtml(task.assignee)}</span>` : ""}
        </div>
      </div>`;
    }
    html += `</div></div>`;
  }
  html += "</div>";

  // Add new task form at top
  html = `<div style="margin-bottom: 16px;">
    <form onsubmit="handleCreateTask(event)" style="display: flex; gap: 8px;">
      <input type="text" id="new-task-title" data-i18n-placeholder="task.newPlaceholder" placeholder="New task title..." style="flex:1; padding: 8px 10px; background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 6px; color: #e0e0e0; font-size: 13px;">
      <select id="new-task-priority" style="padding: 8px; background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 6px; color: #e0e0e0; font-size: 13px;">
        <option value="medium">${t("task.priorityMedium")}</option>
        <option value="low">${t("task.priorityLow")}</option>
        <option value="high">${t("task.priorityHigh")}</option>
        <option value="urgent">${t("task.priorityUrgent")}</option>
      </select>
      <button type="submit" class="btn btn-primary">${t("task.add")}</button>
    </form>
  </div>` + html;

  container.innerHTML = html;
  applyTranslations();
}

let dragTaskId = null;
function onDragStart(e, taskId) { dragTaskId = taskId; e.target.classList.add("dragging"); }
function onDragOver(e) { e.preventDefault(); e.currentTarget.classList.add("drag-over"); }
async function onDrop(e, newStatus) {
  e.preventDefault();
  e.currentTarget.classList.remove("drag-over");
  document.querySelectorAll(".dragging").forEach((el) => el.classList.remove("dragging"));
  if (dragTaskId) {
    try {
      await AutoAIAPI.updateTask(dragTaskId, { project_dir: projectDir, status: newStatus });
      await loadStatus();
      renderPage();
    } catch (e) { alert(t("errors.failed", { msg: e.message })); }
  }
  dragTaskId = null;
}

async function handleCreateTask(e) {
  e.preventDefault();
  const title = document.getElementById("new-task-title").value.trim();
  if (!title) return;
  try {
    await AutoAIAPI.createTask({
      project_dir: projectDir,
      title: title,
      priority: document.getElementById("new-task-priority").value,
    });
    document.getElementById("new-task-title").value = "";
    await loadStatus();
    renderPage();
  } catch (e) { alert(t("errors.failed", { msg: e.message })); }
}

// --- Agents Page ---
async function renderAgents(container) {
  if (!projectDir) {
    container.innerHTML = `<div class="empty-state"><h3>${t("common.noProject")}</h3><p>${t("common.initFirst")}</p></div>`;
    return;
  }
  let roles = [];
  try {
    const result = await AutoAIAPI.getRoles(projectDir);
    roles = result.roles;
  } catch (e) {}

  let html = `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
    <h2 style="font-size: 18px;">${t("agents.title")}</h2>
    <div>
      <button class="btn" onclick="handleGenerateRoles()">${t("agents.generate")}</button>
    </div>
  </div>`;

  for (const role of roles) {
    html += `<div class="agent-card">
      <h4>${escHtml(role.display_name || role.id)}</h4>
      <div class="agent-desc">${escHtml(role.description)}</div>
      <div class="agent-meta">
        <span>${t("agents.model", { value: escHtml(role.model || t("common.default")) })}</span>
        <span>${t("agents.tier", { value: role.cost_tier })}</span>
        <span>${t("agents.provider", { value: escHtml(role.provider) })}</span>
        ${role.has_api_key ? `<span style='color:#4ade80'>${t("agents.apiKeySet")}</span>` : ""}
      </div>
    </div>`;
  }

  if (!roles.length) {
    html += `<div class="empty-state"><h3>${t("agents.noRoles")}</h3><p>${t("agents.noRolesHint")}</p></div>`;
  }

  container.innerHTML = html;
}

async function handleGenerateRoles() {
  try {
    await AutoAIAPI.generateRoles({ project_dir: projectDir });
    renderPage();
  } catch (e) { alert(t("errors.failed", { msg: e.message })); }
}

// --- Sessions Page ---
async function renderSessions(container) {
  if (!projectDir) {
    container.innerHTML = `<div class="empty-state"><h3>${t("common.noProject")}</h3></div>`;
    return;
  }
  let sessions = [];
  try {
    const result = await AutoAIAPI.getSessions(projectDir);
    sessions = result.sessions;
  } catch (e) {}

  let html = `<h2 style="font-size: 18px; margin-bottom: 16px;">${t("sessions.title")}</h2>`;
  html += `<table class="data-table"><thead><tr><th>${t("sessions.colId")}</th><th>${t("sessions.colKind")}</th><th>${t("sessions.colFiles")}</th><th>${t("sessions.colUpdated")}</th></tr></thead><tbody>`;
  for (const s of sessions) {
    const date = new Date(s.updated_at * 1000).toLocaleString();
    html += `<tr onclick="openSessionDetail('${s.id}')"><td>${escHtml(s.id)}</td><td>${s.kind}</td><td>${s.files.length}</td><td>${date}</td></tr>`;
  }
  html += "</tbody></table>";
  if (!sessions.length) {
    html += `<div class="empty-state"><h3>${t("sessions.noSessions")}</h3><p>${t("sessions.noSessionsHint")}</p></div>`;
  }
  container.innerHTML = html;
}

async function openSessionDetail(sessionId) {
  const container = document.getElementById("page-content");
  try {
    const result = await AutoAIAPI.getSession(sessionId, projectDir);
    const session = result.session;
    let html = `<div style="margin-bottom: 12px;"><button class="btn" onclick="renderPage()">${t("sessions.back")}</button></div>`;
    html += `<h3 style="margin-bottom: 12px;">${escHtml(sessionId)}</h3>`;
    html += '<div class="session-tabs">';
    const fileKeys = Object.keys(session.files);
    fileKeys.forEach((key, i) => {
      html += `<div class="session-tab ${i === 0 ? "active" : ""}" onclick="switchSessionTab(this, '${key}')">${key}</div>`;
    });
    html += "</div>";
    html += `<div id="session-file-content"><div class="session-log">${escHtml(session.files[fileKeys[0]] || t("sessions.empty"))}</div></div>`;
    container.innerHTML = html;
    container._sessionFiles = session.files;
  } catch (e) {
    alert(t("errors.failedLoadSession", { msg: e.message }));
  }
}

function switchSessionTab(el, key) {
  document.querySelectorAll(".session-tab").forEach((tr) => tr.classList.remove("active"));
  el.classList.add("active");
  const container = document.getElementById("page-content");
  const files = container._sessionFiles || {};
  document.getElementById("session-file-content").innerHTML = `<div class="session-log">${escHtml(files[key] || t("sessions.empty"))}</div>`;
}

// --- Help Page ---
async function renderHelp(container) {
  if (!projectDir) {
    container.innerHTML = `<div class="empty-state"><h3>${t("common.noProject")}</h3></div>`;
    return;
  }
  let requests = [];
  try {
    const result = await AutoAIAPI.getHelp(projectDir);
    requests = result.help_requests;
  } catch (e) {}

  let html = `<h2 style="font-size: 18px; margin-bottom: 16px;">${t("help.title")}</h2>`;

  for (const req of requests) {
    html += `<div class="help-card severity-${req.severity}">
      <div style="display:flex; justify-content:space-between; align-items:start">
        <h4>${escHtml(req.title)}</h4>
        <span class="priority-badge priority-${req.severity === "blocking" ? "urgent" : req.severity}">${req.status}</span>
      </div>
      ${req.detail ? `<div class="help-detail">${escHtml(req.detail)}</div>` : ""}
      ${req.answer ? `<div class="help-answer"><strong>${t("help.answerLabel")}</strong> ${escHtml(req.answer)}</div>` : ""}
      ${req.status === "open" ? `<div style="margin-top: 8px; display:flex; gap:6px;">
        <input type="text" id="answer-${req.id}" data-i18n-placeholder="help.answerPlaceholder" placeholder="Your answer..." style="flex:1; padding: 6px 8px; background: #0f0f1a; border: 1px solid #2a2a3e; border-radius: 4px; color: #e0e0e0; font-size: 12px;">
        <button class="btn btn-sm btn-primary" onclick="handleAnswerHelp('${req.id}')">${t("help.answer")}</button>
        <button class="btn btn-sm" onclick="handleCloseHelp('${req.id}')">${t("help.close")}</button>
      </div>` : ""}
    </div>`;
  }

  if (!requests.length) {
    html += `<div class="empty-state"><h3>${t("help.noRequests")}</h3><p>${t("help.noRequestsHint")}</p></div>`;
  }

  container.innerHTML = html;
  applyTranslations();
}

async function handleAnswerHelp(id) {
  const answer = document.getElementById(`answer-${id}`).value.trim();
  if (!answer) return;
  try {
    await AutoAIAPI.answerHelp(id, { project_dir: projectDir, answer });
    renderPage();
  } catch (e) { alert(t("errors.failed", { msg: e.message })); }
}

async function handleCloseHelp(id) {
  try {
    await AutoAIAPI.closeHelp(id, { project_dir: projectDir });
    renderPage();
  } catch (e) { alert(t("errors.failed", { msg: e.message })); }
}

// --- Settings Page ---
async function renderSettings(container) {
  if (!projectDir) {
    container.innerHTML = `<div class="empty-state"><h3>${t("settings.noProject")}</h3></div>`;
    return;
  }
  let spec = "";
  try {
    const result = await AutoAIAPI.getSpec(projectDir);
    spec = result.spec;
  } catch (e) {}

  let html = `<h2 style="font-size: 18px; margin-bottom: 16px;">${t("settings.title")}</h2>`;

  // Language switcher
  html += `<div class="agent-card">
    <h4>${t("settings.language")}</h4>
    <div style="margin-top: 8px;">
      <select id="lang-switcher" onchange="switchLang(this.value)" style="padding: 8px 10px; background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 6px; color: #e0e0e0; font-size: 13px; min-width: 140px;">
        <option value="en" ${getLang() === "en" ? "selected" : ""}>English</option>
        <option value="zh" ${getLang() === "zh" ? "selected" : ""}>中文</option>
      </select>
    </div>
  </div>`;

  if (statusData) {
    html += `<div class="agent-card">
      <h4>${t("settings.projectInfo")}</h4>
      <div class="agent-meta" style="flex-direction: column; gap: 4px;">
        <span>${t("settings.directory", { value: escHtml(statusData.project_dir) })}</span>
        <span>${t("settings.goal", { value: escHtml(statusData.goal) })}</span>
        <span>${t("settings.agentCommand", { value: escHtml(statusData.agent_command) })}</span>
        <span>${t("settings.permissionMode", { value: statusData.permission_mode })}</span>
        <span>${t("settings.collaborationMode", { value: statusData.collaboration_mode })}</span>
        <span>${t("settings.nextSession", { value: statusData.next_session })}</span>
        <span>${t("settings.lastStatus", { value: statusData.last_status })}</span>
      </div>
    </div>`;
  }
  html += `<div class="agent-card">
    <h4>${t("settings.taskSpec")}</h4>
    <div class="session-log" style="max-height: 300px;">${escHtml(spec || t("sessions.empty"))}</div>
  </div>`;

  container.innerHTML = html;
}

// --- Language Switch ---
async function switchLang(lang) {
  await loadLang(lang);
  applyTranslations();
  renderPage();
}

// --- WebSocket Events ---
wsClient.onEvent(async (event) => {
  console.log("WS event:", event);
  if (event.type === "session_finished" || event.type === "run_finished") {
    await loadStatus();
    renderPage();
  }
  if (event.type === "run_finished") {
    currentJobId = null;
    updateRunStatus();
  }
});

// --- Utilities ---
function escHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escJsonAttr(obj) {
  return "'" + JSON.stringify(obj).replace(/'/g, "\\'") + "'";
}

// --- Bootstrap ---
async function init() {
  // Initialize i18n first
  await initI18n();

  // Try to detect project dir from URL or stored value
  const stored = localStorage.getItem("autoai_project_dir");
  if (stored) {
    projectDir = stored;
  }
  wsClient.connect();
  if (projectDir) {
    await loadStatus();
  }
  renderPage();
}

init();
