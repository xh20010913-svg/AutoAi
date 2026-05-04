# AutoAi Architecture v1.0

## Overview

AutoAi is a local desktop application for managing autonomous AI coding agents. Users configure agent teams, assign tasks, and monitor real-time execution through a modern board-based UI.

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Desktop Shell | Electron 33 | Cross-platform (Win/Mac/Linux) |
| Frontend | React 18 + TypeScript | Component model, ecosystem, type safety |
| Build Tool | Vite | Fast HMR, optimized builds |
| UI Components | shadcn/ui (Radix primitives) | Accessible, customizable, multi-theme |
| Styling | Tailwind CSS 4 | Utility-first, theme via CSS variables |
| Backend | Python FastAPI | Async, type-safe (Pydantic v2), performant |
| Database | SQLite via SQLAlchemy 2 | Zero-config, single-file, local-first |
| Real-time | WebSocket (FastAPI native) | Bidirectional push for run logs |
| Agent Runtime | subprocess (Claude Code CLI) | Fresh context per session |

## Project Structure

```
AutoAi/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, lifespan
│   │   ├── config.py          # Settings (env vars, defaults)
│   │   ├── database.py        # SQLAlchemy async engine + session
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── project.py     # Project, Agent, Task
│   │   │   ├── run.py         # RunJob, RunEvent
│   │   │   └── provider.py    # ModelProvider
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── api/               # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── projects.py
│   │   │   ├── agents.py
│   │   │   ├── tasks.py
│   │   │   ├── run.py
│   │   │   └── providers.py
│   │   ├── services/          # Business logic
│   │   ├── ws/                # WebSocket manager
│   │   └── agent_runtime/     # subprocess runner, harness
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic/               # DB migrations
├── frontend/                   # Electron + React app
│   ├── electron/              # Electron main + preload
│   │   ├── main.ts
│   │   └── preload.ts
│   ├── src/                   # React app
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── routes/            # Page components
│   │   │   ├── Board.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Runtime.tsx
│   │   │   ├── Models.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/        # Shared UI components
│   │   │   ├── layout/        # Sidebar, Topbar, Shell
│   │   │   ├── board/         # Kanban columns, cards
│   │   │   ├── console/       # Runtime log viewer
│   │   │   └── ui/            # shadcn/ui components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # Utils, API client, WS client
│   │   ├── stores/            # State management (zustand)
│   │   └── styles/            # Global CSS, theme vars
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md        # This file
│   ├── ROADMAP.md             # Phase plan
│   ├── PROJECT_STATE.md       # Current progress
│   ├── API.md                 # API reference
│   └── AGENT_WORKFLOW.md      # How agents work together
└── README.md
```

## Key Design Decisions

### 1. Local-first, file-based state
- SQLite stores all structured data (tasks, agents, runs, sessions)
- Project files (.autoai/) store config and prompts
- No cloud dependency — everything works offline

### 2. Fresh context per agent session
- Each agent run gets a clean subprocess with its own context
- State handoff via disk files (feature_list.json, progress.md)
- Invariant validation prevents agents from corrupting shared state

### 3. Real-time WebSocket push
- Single `/ws` endpoint for all live updates
- Events: task_updated, run_started, stdout, stderr, run_finished, agent_status
- Frontend subscribes to filtered event types

### 4. Multi-theme support
- shadcn/ui theme provider with light/dark/system modes
- CSS custom properties for all colors
- Theme persisted in localStorage, applied on mount

### 5. Agent Runtime
- Agents are defined as roles with model, provider, budget, permissions
- Runner executes agent command via subprocess
- Real-time stdout/stderr piped through WebSocket
- Stop signal sends SIGTERM, force kill after timeout

## API Design

### REST Endpoints
```
GET    /api/v1/projects          List projects
POST   /api/v1/projects          Create project
GET    /api/v1/projects/:id      Get project
DELETE /api/v1/projects/:id      Delete project

GET    /api/v1/projects/:id/agents     List agents
POST   /api/v1/projects/:id/agents     Create agent
PATCH  /api/v1/projects/:id/agents/:aid  Update agent
DELETE /api/v1/projects/:id/agents/:aid  Delete agent

GET    /api/v1/projects/:id/tasks      List tasks (filterable)
POST   /api/v1/projects/:id/tasks      Create task
PATCH  /api/v1/projects/:id/tasks/:tid Update task (status, assignee)
DELETE /api/v1/projects/:id/tasks/:tid Delete task

POST   /api/v1/projects/:id/run        Start agent run
POST   /api/v1/projects/:id/run/stop   Stop running agent

GET    /api/v1/projects/:id/providers  List model providers
POST   /api/v1/projects/:id/providers  Add provider
PATCH  /api/v1/projects/:id/providers/:pid  Update provider

GET    /api/v1/projects/:id/sessions   List run sessions
GET    /api/v1/projects/:id/sessions/:sid  Get session detail

WS     /ws/:project_id                 Real-time event stream
```

## UI Layout

```
+--------+------------------------------------------+
|        |  Top Bar (project name, run button)      |
| Sidebar|------------------------------------------+
|        |                                          |
| Board  |  Main Content Area                       |
| Agents |  (Board / Agents / Runtime /             |
| Runtime|   Models / Settings pages)               |
| Models |                                          |
|Settings|                                          |
|        |                                          |
+--------+------------------------------------------+
|  Status Bar (connection, agent status, version)    |
+---------------------------------------------------+
```

## Automation: Task Dispatch System

### Architecture
```
scripts/dispatch.py          # Python 调度脚本 (核心)
scripts/run-dispatch.bat     # Windows 静默启动 (pythonw)
scripts/run-dispatch-silent.vbs  # 完全无窗口启动

运行方式:
  python scripts/dispatch.py              # 单次扫描
  python scripts/dispatch.py --loop 30    # 每 30s 循环
  wscript scripts/run-dispatch-silent.vbs # 后台静默运行
```

### 调度逻辑
1. 扫描 Multica 工作区 issue 状态
2. in_review 任务 → 标记为 done
3. 空闲 agent (in_progress < 2) → 从任务池派发新任务
4. 防重复: 检查标题关键词匹配已有任务
5. 通过 subprocess + CREATE_NO_WINDOW 运行，不弹窗

### 任务池
- 后端: auth → project CRUD → WebSocket
- 前端: UI 改版 → i18n → 像素动画
- 测试: 等开发 in_review 后自动创建

## Internationalization (i18n)

- 使用 react-i18next + i18next
- 支持中文 / English 切换
- 语言选择存 localStorage
- 所有 UI 文字通过 useTranslation() 获取

## Pixel Character Animations

- Agents 页面展示像素小人工作状态
- CSS div 拼像素，不依赖外部图片
- 工作状态: 敲键盘动画
- 空闲状态: 沙发休息
- 参考: claude-quest (github.com/Michaelliv/claude-quest)

## UI Design Direction

### 独特风格 (区别于 Motica/Linear)
- 像素风格 + 现代感混搭
- 暖色调 (amber/orange) 为主
- 等宽字体标题 + sans-serif 正文
- 卡片有轻微像素边框效果
- 侧边栏带像素风格品牌元素

## Reference Projects

- **shadcn/ui** — Component primitives, theme system
- **Lobe Chat** — Modern React + shadcn chat UI, multi-provider, multi-theme
- **Linear** — Board UX, task management patterns
- **Cursor** — Electron + React desktop app architecture
- **CrewAI** — Multi-agent role definition and orchestration
- **FastAPI official** — API patterns, WebSocket usage
- **claude-quest** — Pixel art character animations for agent states
