# AutoAi Roadmap

## v0.1 — Clean Foundation (current)

**Goal**: Establish a clean, working project skeleton with proper architecture.

- [ ] Backend: FastAPI project with SQLAlchemy + SQLite, clean API structure
- [ ] Frontend: React + Vite + TypeScript + Tailwind + shadcn/ui scaffold
- [ ] Electron shell launching backend + frontend
- [ ] Multi-theme support (light/dark/system) with CSS variables
- [ ] Basic Board page with static Kanban columns
- [ ] Basic Agents page with card grid
- [ ] Basic Settings page with theme toggle

**Exit criteria**: App launches, theme switching works, all pages render with mock data.

## v0.2 — Task Board MVP

**Goal**: Functional Kanban board with CRUD operations.

- [ ] Full task CRUD API
- [ ] Board drag-and-drop between columns
- [ ] Task detail panel (title, description, priority, assignee)
- [ ] Task creation form
- [ ] SQLite persistence for all task operations

**Exit criteria**: Can create, move, edit, and delete tasks. Survives app restart.

## v0.3 — Agent Management

**Goal**: Define, configure, and manage agent roles.

- [ ] Agent CRUD API
- [ ] Role-based agent templates (PM, developer, tester)
- [ ] Agent configuration form (model, provider, API key)
- [ ] Agents page with status indicators
- [ ] Agent assignment on tasks

**Exit criteria**: Can create agents, assign them to tasks, see agent status.

## v0.4 — Runtime Engine

**Goal**: Execute agents and stream real-time output.

- [ ] subprocess runner with stdout/stderr capture
- [ ] WebSocket real-time log streaming
- [ ] Run start/stop/resume
- [ ] Run history and session logs
- [ ] Runtime Console page with live log viewer

**Exit criteria**: Can start an agent run, see live logs, stop/resume.

## v0.5 — Model Providers

**Goal**: Support multiple LLM providers.

- [ ] Provider model (OpenAI, Anthropic, DeepSeek, local)
- [ ] Provider configuration UI with API key management
- [ ] Agent → provider binding
- [ ] Provider health check

**Exit criteria**: Can configure providers and assign them to agents.

## v0.6 — Polish & Test

- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] UI polish and animations

## v0.7 — Desktop Packaging

- [ ] Electron builder configuration
- [ ] Auto-update mechanism
- [ ] Windows/Mac/Linux installers

## v1.0 — Release

- [ ] Documentation complete
- [ ] All tests passing
- [ ] Signed installers for all platforms
