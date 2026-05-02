# AutoAI API 文档

AutoAI 后端基于 FastAPI，默认运行在 `http://127.0.0.1:18765`。所有需要 `project_dir` 的端点通过 query string 传递项目根目录路径。

## 通用约定

- 需要 `project_dir` 的端点通过 query string 传递：`?project_dir=/path/to/project`
- 写操作的 `project_dir` 在 JSON body 中传递
- 响应均为 JSON 格式
- 时间戳使用 ISO 8601 UTC 格式

---

## 项目状态与初始化

### `GET /api/status`

获取项目完整状态。

**参数:** `project_dir` (query, required)

**响应:**
```json
{
  "project_dir": "/path/to/project",
  "exists": true,
  "configured": true,
  "goal": "项目目标描述",
  "feature_count": 50,
  "agent_command": "claude -p",
  "verify_command": null,
  "permission_mode": "default",
  "collaboration_mode": "single",
  "next_session": 3,
  "last_status": "ok",
  "last_session_id": "0002-coding-20260502T120000",
  "consecutive_failures": 0,
  "features": { "total": 12, "passing": 8, "failing": 4, "complete": false },
  "first_run_pending": false,
  "validation": { "ok": true, "messages": [] },
  "help": { "open": 0 },
  "roles": { "total": 5, "custom_models": 0, "custom_keys": 0 },
  "sessions_dir": "/path/to/project/.autoai/sessions"
}
```

### `POST /api/init`

初始化一个新的 AutoAI 项目。

**Body:**
```json
{
  "project_dir": "/path/to/project",
  "goal": "Build a task management app",
  "feature_count": 50,
  "agent_command": "claude -p",
  "verify_command": null,
  "permission_mode": "default",
  "init_git": true,
  "collaboration_mode": "single",
  "spec_text": null,
  "spec_filename": null,
  "install_agents": true
}
```

**响应:** 同 `GET /api/status` 格式

### `GET /api/spec`

获取 `task_spec.md` 内容。

**参数:** `project_dir` (query, required)

**响应:** `{ "spec": "markdown content..." }`

### `GET /api/progress`

获取 `autoai-progress.md` 内容。

**参数:** `project_dir` (query, required)

**响应:** `{ "progress": "markdown content..." }`

### `GET /api/prompts/{kind}`

获取渲染后的 agent prompt。

**参数:** `project_dir` (query, required), `kind` (path: `initializer` 或 `coding`)

**响应:** `{ "prompt": "rendered prompt text..." }`

### `GET /api/validate`

校验 `feature_list.json` 不变性。

**参数:** `project_dir` (query, required)

**响应:** `{ "ok": true, "messages": ["Feature invariants OK."] }`

---

## Claude Code 设置

### `GET /api/claude-settings`

获取 Claude Code 设置状态（skip dangerous mode prompt 等）。

**响应:** `{ "settings": { ... } }`

### `POST /api/claude-settings/skip-bypass`

切换 skip dangerous mode prompt 开关。

**Body:** `{ "enabled": true }`

**响应:** `{ "settings": { ... } }`

---

## 任务管理 `/api/tasks`

### `GET /api/tasks`

列出所有任务。

**参数:** `project_dir` (query, required)

**响应:**
```json
{
  "tasks": [
    {
      "id": "T-a1b2c3d4",
      "title": "Build task board UI",
      "description": "Create a Kanban-style board",
      "status": "in_progress",
      "priority": "high",
      "assignee": "frontend-developer",
      "created_at": "2026-05-02T12:00:00+00:00",
      "updated_at": "2026-05-02T12:30:00+00:00"
    }
  ]
}
```

**任务状态:** `backlog`, `todo`, `in_progress`, `in_review`, `done`, `blocked`, `cancelled`

**优先级:** `low`, `medium`, `high`, `urgent`

### `POST /api/tasks`

创建任务。

**Body:**
```json
{
  "project_dir": "/path/to/project",
  "title": "Task title",
  "description": "Task description",
  "priority": "medium",
  "assignee": "implementer",
  "status": "todo"
}
```

**响应:** `{ "task": { ... } }`

### `PATCH /api/tasks/{task_id}`

更新任务字段。

**Body:** 包含要更新的字段 (`title`, `description`, `status`, `priority`, `assignee` 中的任意组合) 和 `project_dir`

**响应:** `{ "task": { ... } }`

---

## Help 请求 `/api/help`

### `GET /api/help`

列出所有 Help 请求。

**参数:** `project_dir` (query, required)

**响应:** `{ "help_requests": [ ... ] }`

Help 请求状态: `open`, `answered`, `closed`
严重程度: `low`, `medium`, `high`, `blocking`

### `POST /api/help`

创建 Help 请求（agent 遇到无法自行处理的情况时使用）。

**Body:**
```json
{
  "project_dir": "/path/to/project",
  "title": "Need API key for deployment",
  "detail": "Cannot proceed without AWS credentials",
  "severity": "blocking",
  "task_id": "T-a1b2c3d4",
  "role_id": "implementer",
  "session_id": "0003-coding-20260502T120000"
}
```

**响应:** `{ "help_request": { ... } }`

### `POST /api/help/{request_id}/answer`

答复 Help 请求。

**Body:** `{ "project_dir": "...", "answer": "Use the key from 1Password" }`

**响应:** `{ "help_request": { ... } }`

### `POST /api/help/{request_id}/close`

关闭 Help 请求。

**Body:** `{ "project_dir": "..." }`

**响应:** `{ "help_request": { ... } }`

---

## 角色与 Agent `/api`

### `GET /api/roles`

列出项目的角色配置。

**参数:** `project_dir` (query, required)

**响应:** `{ "roles": [ ... ] }`

### `POST /api/roles/generate`

根据项目 spec 自动生成角色。

**Body:** `{ "project_dir": "..." }`

**响应:** `{ "roles": [ ... ], "generated": 5 }`

### `PUT /api/roles`

保存角色配置（同时同步 `.claude/agents/*.md`）。

**Body:** `{ "project_dir": "...", "roles": [ ... ] }`

**响应:** `{ "roles": [ ... ] }`

### `GET /api/agents`

列出已安装的 Claude Code subagents。

**参数:** `project_dir` (query, required)

**响应:** `{ "agents": [ { "name": "...", "description": "...", "tools": "...", "model": "...", "path": "..." } ] }`

### `POST /api/agents/install-defaults`

安装/同步默认 agent 定义到 `.claude/agents/`。

**Body:** `{ "project_dir": "...", "overwrite": true }`

**响应:** `{ "agents": [ ... ] }`

---

## Session 日志 `/api/sessions`

### `GET /api/sessions`

列出所有 session 历史。

**参数:** `project_dir` (query, required)

**响应:**
```json
{
  "sessions": [
    {
      "id": "0002-coding-20260502T120000",
      "kind": "coding",
      "updated_at": 1714651200.0,
      "files": [
        { "name": "0002-coding-...prompt.md", "kind": "prompt", "size": 3200 },
        { "name": "0002-coding-...agent.stdout.log", "kind": "agent_stdout", "size": 15000 }
      ]
    }
  ]
}
```

### `GET /api/sessions/{session_id}`

获取单个 session 的完整日志（含 prompt、stdout、stderr 内容）。

**参数:** `project_dir` (query, required)

**响应:** `{ "session": { "id": "...", "kind": "coding", "files": { "prompt": "...", "agent_stdout": "...", "agent_stderr": "..." } } }`

---

## Harness 运行 `/api`

### `GET /api/job`

获取运行中 job 的状态。

**参数:** `id` (query, required)

**响应:** `{ "job": { "id": "...", "project_dir": "...", "status": "running", "returncode": null, "log": "...", "error": null } }`

Job 状态: `queued`, `running`, `finished`, `blocked`, `failed`, `stopped`

### `POST /api/run`

启动 harness 运行。

**Body:**
```json
{
  "project_dir": "/path/to/project",
  "max_iterations": null,
  "continuous": false,
  "sleep_seconds": 3,
  "timeout_seconds": null,
  "stop_on_error": true,
  "agent_command": null,
  "permission_mode": "",
  "collaboration_mode": ""
}
```

- 若 `continuous` 为 true 且未指定 `max_iterations`，则无限循环运行
- 默认 `max_iterations=1`（单次运行）

**响应:** `{ "job": { ... } }`

### `POST /api/run/stop`

停止正在运行的 job。

**Body:** `{ "job_id": "..." }`

**响应:** `{ "job": { ... } }`

---

## WebSocket

### `WS /ws`

实时推送 harness 运行事件。

**事件格式:**
```json
{
  "job_id": "abc123def456",
  "type": "session_started",
  "session_id": "0003-coding-20260502T120000",
  "kind": "coding",
  "session_num": 3
}
```

**事件类型:**
- `run_started` / `run_finished` — 整体运行状态
- `session_started` / `session_finished` — 单轮 session
- `run_blocked` — 有未答复的 Help 请求，运行暂停

---

## 数据库模型

所有持久化数据存储在项目目录的 `.autoai/autoai.db` (SQLite)。核心表：

| 表名 | 用途 |
|------|------|
| `tasks` | 任务队列 (id, title, status, priority, assignee) |
| `help_requests` | Help 请求 (id, title, status, severity, answer) |
| `roles` | 角色配置 (id, model, cost_tier, token_budget, authority, scope) |
| `role_secrets` | 角色 API key (role_id, api_key) |
| `messages` | 通信日志 (id, type, sender, recipient, payload) |
| `config` | 项目配置 KV (key, value) |
| `run_state` | 运行状态 (next_session, last_status, consecutive_failures) |
