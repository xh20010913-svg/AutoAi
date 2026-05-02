// API client for AutoAI backend
const API_BASE = (window.autoai && window.autoai.backendUrl) || "http://127.0.0.1:18765";

async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const opts = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  if (opts.body && typeof opts.body === "object") {
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || err.detail || res.statusText);
  }
  return res.json();
}

// REST helpers
const AutoAIAPI = {
  // Status
  getStatus: (projectDir) => api(`/api/status?project_dir=${encodeURIComponent(projectDir)}`),
  initProject: (data) => api("/api/init", { method: "POST", body: data }),

  // Tasks
  getTasks: (projectDir) => api(`/api/tasks?project_dir=${encodeURIComponent(projectDir)}`),
  createTask: (data) => api("/api/tasks", { method: "POST", body: data }),
  updateTask: (taskId, data) => api(`/api/tasks/${taskId}`, { method: "PATCH", body: data }),

  // Roles
  getRoles: (projectDir) => api(`/api/roles?project_dir=${encodeURIComponent(projectDir)}`),
  generateRoles: (data) => api("/api/roles/generate", { method: "POST", body: data }),
  saveRoles: (data) => api("/api/roles", { method: "PUT", body: data }),

  // Agents
  getAgents: (projectDir) => api(`/api/agents?project_dir=${encodeURIComponent(projectDir)}`),
  installAgents: (data) => api("/api/agents/install-defaults", { method: "POST", body: data }),

  // Sessions
  getSessions: (projectDir) => api(`/api/sessions?project_dir=${encodeURIComponent(projectDir)}`),
  getSession: (sessionId, projectDir) => api(`/api/sessions/${sessionId}?project_dir=${encodeURIComponent(projectDir)}`),

  // Help
  getHelp: (projectDir) => api(`/api/help?project_dir=${encodeURIComponent(projectDir)}`),
  createHelp: (data) => api("/api/help", { method: "POST", body: data }),
  answerHelp: (id, data) => api(`/api/help/${id}/answer`, { method: "POST", body: data }),
  closeHelp: (id, data) => api(`/api/help/${id}/close`, { method: "POST", body: data }),

  // Run
  startRun: (data) => api("/api/run", { method: "POST", body: data }),
  stopRun: (data) => api("/api/run/stop", { method: "POST", body: data }),
  getJob: (jobId) => api(`/api/job?id=${encodeURIComponent(jobId)}`),

  // Spec & Progress
  getSpec: (projectDir) => api(`/api/spec?project_dir=${encodeURIComponent(projectDir)}`),
  getProgress: (projectDir) => api(`/api/progress?project_dir=${encodeURIComponent(projectDir)}`),
  getPrompt: (kind, projectDir) => api(`/api/prompts/${kind}?project_dir=${encodeURIComponent(projectDir)}`),
  validate: (projectDir) => api(`/api/validate?project_dir=${encodeURIComponent(projectDir)}`),
};

// WebSocket client
class WSClient {
  constructor() {
    this.ws = null;
    this.listeners = [];
    this.reconnectTimer = null;
  }

  connect() {
    try {
      const wsUrl = API_BASE.replace("http", "ws") + "/ws";
      this.ws = new WebSocket(wsUrl);
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((fn) => fn(data));
        } catch (e) {}
      };
      this.ws.onclose = () => {
        this.reconnectTimer = setTimeout(() => this.connect(), 2000);
      };
      this.ws.onerror = () => {};
    } catch (e) {
      this.reconnectTimer = setTimeout(() => this.connect(), 2000);
    }
  }

  onEvent(fn) {
    this.listeners.push(fn);
  }

  disconnect() {
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

const wsClient = new WSClient();
