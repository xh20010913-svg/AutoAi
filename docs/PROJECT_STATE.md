# Project State

## Current Phase: v0.2 — Task Board MVP + UI Enhancement

**Started**: 2026-05-04
**Status**: v0.1 complete. v0.2 core done, UI enhancements in progress.

## Phase Goal

Functional Kanban board with CRUD + unique UI style + i18n + pixel animations.

## Task Status

| ID | Task | Assignee | Status |
|----|------|----------|--------|
| AUT-142 | [v0.1] FastAPI backend skeleton | 后端开发 | done |
| AUT-143 | [v0.1] React frontend scaffold | 前端开发 | done |
| AUT-145 | [v0.2] Task CRUD API | 后端开发 | done |
| AUT-146 | [v0.2] Board UI — drag-and-drop + detail panel | 前端开发 | done |
| AUT-152 | [v0.2] UI 重新设计 — 独特像素风格 | 前端开发 | in_progress |
| AUT-153 | [v0.2] 多语言支持 — 中文/英文切换 | 后端开发2 | in_progress |
| AUT-154 | [v0.2] 像素小人动画组件 | 后端开发3 | in_progress |

## Agent Plan

- 后端开发 (208acdf3): idle
- 后端开发2 (b8c65682): AUT-153 — i18n
- 后端开发3 (b3183a17): AUT-154 — 像素动画
- 前端开发 (65682ad4): AUT-152 — UI 改版
- 测试工程师 (329269a9): idle
- 测试开发2 (d7d57347): idle
- 测试开发3 (47ce74db): idle

## Automation

- 旧 autopilot 已暂停 (解决弹窗问题)
- 新 dispatch 脚本: `scripts/dispatch.py`
- 运行: `python scripts/dispatch.py --loop 30` 或 `wscript scripts/run-dispatch-silent.vbs`

## Rules

- 每个任务必须包含项目名 "AutoAi" 和仓库 URL
- Agent 先 checkout repo 再开工
- 不重复创建任务
- 测试任务等开发 in_review 后再创建
- PM 统一合并代码到 master

## Completed Milestones

### v0.1 — Clean Foundation (done)
- FastAPI backend skeleton with health check (AUT-142)
- React frontend with 5 pages of real UI (AUT-143)
- Theme system (light/dark/system)
- Tailwind CSS v4 + shadcn/ui components

### v0.2 — Task Board MVP (core done)
- Task CRUD API — 7 endpoints + 9 passing tests (AUT-145)
- Board UI with drag-and-drop + detail panel (AUT-146)
- Auto-dispatch script for agent management
