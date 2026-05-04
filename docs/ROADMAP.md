# AutoAI 路线图

## 当前版本: v0.2.0

---

## Phase 1: Role Policy & Agent Sync (已完成)

- [x] `autoai/roles.py` — 角色目录和自动生成
- [x] `.autoai/roles.json` — 角色策略持久化
- [x] 三级预算体系 (high/medium/low)
- [x] 角色 authority 和 scope 控制
- [x] 角色 API key 安全存储
- [x] `sync_agents_from_roles()` → `.claude/agents/*.md`
- [x] UI Roles 页
- [x] Prompt 渲染中加入角色上下文

## Phase 2: Task Decomposition (进行中)

目标：v0.3.0

- [ ] `autoai/planner.py` — 从 `task_spec.md` 和 `feature_list.json` 自动拆分任务
- [ ] `.autoai/task_graph.json` — 任务依赖图
- [ ] 每个任务自动配置 `suggested_role`, `allowed_write_paths`, `depends_on`, `acceptance`
- [ ] `POST /api/tasks/decompose` — 一键拆分 API
- [ ] UI: Tasks 页新增"一键拆分需求"按钮
- [ ] Prompt 按任务裁剪（只带当前任务相关信息）
- [ ] 测试: `test_planner.py`

## Phase 3: Dispatcher

目标：v0.4.0

- [x] `autoai/dispatcher.py` — 根据任务状态、依赖和角色预算选择下一项工作
- [ ] 支持单任务运行、连续运行、按角色运行
- [ ] Harness 从 task graph 而非 feature list 驱动
- [x] `POST /api/tasks/assign` — 手动分配任务给角色
- [ ] UI: 任务分配面板
- [x] 测试: `test_dispatcher.py`

## Phase 4: Communication Log

目标：v0.5.0

- [ ] `autoai/comm.py` — messages.jsonl 读写
- [ ] 消息类型: plan, assignment, ack, progress, blocker, handoff, review, decision, heartbeat
- [ ] `GET /api/messages` / `POST /api/messages`
- [ ] UI: Messages 页，按 task/role 过滤
- [ ] 测试: `test_comm.py`

## Phase 5: Boundary Enforcement

目标：v0.6.0

- [ ] `autoai/policy.py` — 越权检测
- [ ] 每轮运行后检查 git diff，阻止未授权路径修改
- [ ] 严格模式：worker 独立 worktree
- [ ] Policy violation 记录
- [ ] `GET /api/policy-violations`
- [ ] UI: Policy 页
- [ ] 测试: `test_policy.py`

## Phase 6: Budget Accounting

目标：v0.7.0

- [ ] `autoai/budget.py` — 预算计算和账本
- [ ] `.autoai/budget_ledger.jsonl` — token 消耗记录
- [ ] 记录 prompt chars, output chars, timeout, estimated cost
- [ ] `GET /api/budget`
- [ ] UI: Budget 页
- [ ] 测试: `test_budget.py`

## Phase 7: Daemon / Autopilot

目标：v0.8.0

- [ ] 本地 runtime loop：定时扫描项目、领取任务、heartbeat、执行、写回
- [ ] Autopilot 模式：每天、每小时、工作日、手动触发
- [ ] Heartbeat 机制
- [ ] UI: Autopilot 创建和管理
- [ ] 测试: `test_daemon.py`

## Phase 8: Polish & Release

目标：v1.0.0

- [ ] UI 完善：Team 页、角色状态、预算消耗、heartbeat
- [ ] 错误恢复增强
- [ ] 性能优化（数据库索引、前端代码分割）
- [ ] 完整测试覆盖（目标 80%+）
- [ ] 文档完善
- [ ] 发布到 PyPI

---

## 版本里程碑

| 版本 | 主题 | 关键交付 |
|------|------|---------|
| v0.1.0 | 基础架构 | Electron + FastAPI + SQLite, Harness 循环, CLI |
| v0.1.5 | 前端工作台 | 暗色主题, 多标签 UI, WebSocket 实时推送 |
| v0.2.0 | 运行 & 角色 | RunJob, 进程终止, 超时控制, 角色系统, 预算体系 |
| v0.3.0 | 任务拆分 | Planner, Task Graph, 一键拆分 |
| v0.4.0 | 任务调度 | Dispatcher, 按角色运行 |
| v0.5.0 | 通信日志 | Messages, Agent 间通信 |
| v0.6.0 | 越权防护 | Policy enforcement, Git diff 检查 |
| v0.7.0 | 预算账本 | Token 计费, 成本追踪 |
| v0.8.0 | 后台驻留 | Daemon, Autopilot, Heartbeat |
| v1.0.0 | 正式发布 | 完整测试, 文档, PyPI |
