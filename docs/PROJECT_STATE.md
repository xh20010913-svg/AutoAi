# Project State

## Current Phase: v0.2 — Task Board MVP

**Started**: 2026-05-04
**Status**: v0.1 complete. v0.2 in progress.

## Phase Goal

Functional Kanban board with CRUD operations. Can create, move, edit, and delete tasks. Survives app restart.

## Tech Stack

- **Backend**: Python FastAPI + SQLAlchemy 2 (async) + SQLite + Pydantic v2
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS 4 + shadcn/ui
- **Desktop**: Electron 33
- **Real-time**: WebSocket

## Task Status

| ID | Task | Assignee | Status |
|----|------|----------|--------|
| AUT-142 | [v0.1] FastAPI backend skeleton | 后端开发 | done |
| AUT-143 | [v0.1] React frontend scaffold | 前端开发 | done |
| AUT-145 | [v0.2] Task CRUD API | 后端开发 | in_progress |
| AUT-146 | [v0.2] Board UI — drag-and-drop + detail panel | 前端开发 | in_progress |

## Agent Plan

- 后端开发 (208acdf3): AUT-145 — Task CRUD API
- 后端开发2 (b8c65682): idle
- 后端开发3 (b3183a17): idle
- 前端开发 (65682ad4): AUT-146 — Board UI
- 测试工程师 (329269a9): idle (waiting for dev tasks to complete)
- 测试开发2 (d7d57347): idle
- 测试开发3 (47ce74db): idle

All agents work in their own Multica workdirs via `multica repo checkout`.
PM (项目经理) merges all code to master.

## Rules

- Each task must include project name "AutoAi" and repo URL
- Agents must checkout repo before starting work
- No duplicate tasks
- Test tasks only created after dev tasks are in_review/done
- PM is the only one who pushes to master

## Completed Milestones

### v0.1 — Clean Foundation (done)
- FastAPI backend skeleton with health check (AUT-142)
- React frontend with 5 pages of real UI (AUT-143)
- Theme system (light/dark/system)
- Tailwind CSS v4 + shadcn/ui components
