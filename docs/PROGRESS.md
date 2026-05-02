# AutoAI 项目进度日志

## 2026-05-02 — 项目当前状态

### 当前版本: v0.2.0

### 状态摘要

- **架构:** Electron 前端 + FastAPI 后端 + SQLite 存储
- **核心功能:** 项目初始化、Harness 自动循环、WebSocket 实时推送、角色系统、任务队列、Session 日志
- **测试:** 19 个单元测试通过，API 集成测试覆盖 tasks/job/roles/help/WebSocket
- **前端:** 暗色主题桌面工作台，模块化 SPA（Overview、Spec、Progress、Sessions、Agents、Tasks、Job Log、Settings）

---

## 里程碑时间线

### Phase 0: 项目基础 (v0.1.0)

- 初始化为本地桌面应用：Electron + FastAPI + SQLite
- 实现项目初始化流程（`autoai project init` → `POST /api/init`）
- 实现 Harness 核心循环（渲染 prompt → 验证 → 执行 agent → 记录进度）
- CLI 命令：`init`, `run`, `serve`, `status`, `validate`, `prompt`
- Prompt 模板系统：initializer / coding 两种模式
- Feature list 不变性校验
- Session 日志持久化（prompt + stdout + stderr）
- Git 集成（auto commit per session）

### Phase 1: 前端工作台 (v0.1.5)

- Electron 前端重写为现代桌面工作台风格
- 暗色主题设计，紧凑单页布局
- 多标签页：Overview、Prompt、Spec、Progress、Sessions、Agents、Tasks、Job Log
- WebSocket 实时事件推送（session_started, session_finished, run_blocked）

### Phase 2: 运行可靠性 (v0.2.0)

- RunJob 模型和 `/api/job` / `/api/run` / `/api/run/stop` 端点
- 进程终止支持：`/api/run/stop` 可终止 agent 子进程
- Agent timeout 控制和多 provider 支持
- 断点恢复（从 run_state 继续）
- Stop 按钮状态反馈和实时 WebSocket 日志展示
- API 集成测试

### Phase 3: 角色系统 (v0.2.0+)

- 角色目录（8 个）：project-manager, agent-orchestrator, frontend-developer, backend-developer, implementer, tester, security-reviewer, reviewer
- 角色根据项目目标自动生成
- 三级预算体系：high / medium / low（prompt chars, output chars, max files, timeout）
- 角色 authority 控制：can_decompose_tasks, can_assign_tasks, can_change_architecture, can_mark_done
- 角色 scope 控制：write_paths, read_paths
- 角色与 Claude Code subagents 自动同步（`.claude/agents/*.md`）
- 角色 API key 安全存储（role_secrets 表）

### Phase 4: 设置与配置

- Settings 页面：Provider/Model 配置管理
- Provider/Model 配置持久化 API
- Claude Code settings 管理（skip dangerous mode prompt）

### Phase 5: 前端重构

- app.js 模块化重构
- XSS 安全修复
- 移除内联 onclick 和样式
- 代码组织：Board、SpecEditor、PromptViewer、ProgressViewer、SessionsList、AgentsList、TasksPanel、JobLog、Settings 等模块

---

## 当前任务统计

| 指标 | 数值 |
|------|------|
| 总 feature 数 | 39 |
| 当前通过 | 14 |
| 测试用例 | 19 |
| 角色数 | 8（5 个强制） |
| 默认 Agent | 5（team-lead, architect, implementer, tester, reviewer） |
| API 端点 | 27 |
| WebSocket 事件类型 | 5+ |

---

## 下一步计划

1. **Task Decomposition (Phase 2)** — planner.py + 自动拆任务 + task_graph.json
2. **Dispatcher (Phase 3)** — 从任务队列选择任务并分配合适角色
3. **Communication Log (Phase 4)** — messages.jsonl 完整通信日志
4. **Boundary Enforcement (Phase 5)** — git diff 越权检查
5. **Budget Accounting (Phase 6)** — token 消耗账本
6. **Daemon / Autopilot (Phase 7)** — 全天运行、定时触发

详见 `docs/ROADMAP.md`。

---

## 已知问题

- 多 agent 协作尚不支持 task_graph 依赖管理
- 越权检测仅限 prompt 约束，未实现 git diff 检查
- 缺少 token 消耗的实际计费账本
- 前端 Roles 页、Team 页、Messages 页、Budget 页尚未实现
