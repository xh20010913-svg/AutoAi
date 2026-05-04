# Agent Workflow

## How We Work

This is a multi-agent development team. Each agent has a specific role and works on one task at a time.

## Workflow

```
PM creates task → Assigns to agent → Agent works → Agent submits PR → Test engineer reviews → PM accepts → Done
```

## Rules for All Agents

1. **Read ARCHITECTURE.md first** — understand the project structure before writing code
2. **One task at a time** — finish current task before starting another
3. **Small, concrete changes** — each task should be completable in one session
4. **Code deliverables required** — every completed task must have a PR, branch, or diff
5. **Comment on your task** — when done, post a summary comment with what you changed
6. **Follow the tech stack** — React+TS+Tailwind+shadcn/ui for frontend, FastAPI+SQLAlchemy for backend
7. **Don't touch files outside your scope** — frontend devs don't modify backend code, and vice versa

## Task Lifecycle

```
Todo → In Progress → In Review → Done
                         ↓
                      Blocked (if issues found)
```

## Agent Roles

### 项目经理 (Project Manager)
- Plans phases, splits tasks, assigns work
- Maintains docs (ARCHITECTURE, ROADMAP, PROJECT_STATE, API)
- Final acceptance of completed work
- Does NOT write production code directly

### 后端开发 (Backend Developer)
- FastAPI routes, Pydantic schemas, SQLAlchemy models
- WebSocket handlers, agent runtime, subprocess management
- Database migrations, API documentation
- Must provide: working API, tests, API docs

### 前端开发 (Frontend Developer)
- React components, pages, hooks, stores
- Tailwind styling, shadcn/ui integration, theme system
- Electron main/preload, WebSocket client
- Must provide: working UI, responsive layout, multi-theme support

### 算法设计工程师 (Algorithm Engineer)
- Complex logic: task scheduling, agent orchestration, prompt templates
- Performance optimization, resource allocation strategies

### 测试工程师 (Test Engineer)
- Backend API tests, frontend component tests
- End-to-end testing, WebSocket testing
- PR review before merge
- Must provide: test results, bug reports, acceptance sign-off

## Communication

- Each task is a Multica issue
- Post progress in the issue comments
- Mention other agents only when truly need their input
- PM monitors all issues and coordinates
