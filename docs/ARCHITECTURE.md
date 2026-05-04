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

## Reference Projects

- **shadcn/ui** — Component primitives, theme system
- **Lobe Chat** — Modern React + shadcn chat UI, multi-provider, multi-theme
- **Linear** — Board UX, task management patterns
- **Cursor** — Electron + React desktop app architecture
- **CrewAI** — Multi-agent role definition and orchestration
- **FastAPI official** — API patterns, WebSocket usage
