# AutoAI Development Handoff

本文档给下一位开发者或 AI 接手使用。目标是把当前 AutoAI 从“单项目长跑 harness + Web UI”推进到“可调角色预算、自动拆任务、多 agent 协同、全天自动化运行”的本地系统。

## 1. 产品目标

AutoAI 要做的是一个本地优先的长期自动化 agent 系统：

- 用户可以通过 Web UI 创建新项目，上传 Markdown 需求文档，或加载已有项目。
- 系统把长任务拆成多轮 fresh-context agent session，每轮都能靠磁盘文件恢复上下文。
- 系统支持单 agent、项目 subagents、Claude Agent Teams 三种协同模式。
- 系统可以全天运行，有任务队列、会话日志、进度日志、角色状态和错误恢复。
- 系统能自动拆分任务，并给每个任务选择合适角色。
- 不同角色使用不同 token 预算、模型等级、上下文数量和工具权限。项目经理/架构角色可以用更高预算，重复性执行角色用更低预算。
- 角色必须有明确职责边界，不能随意越权改别人的文件、做没有授权的决策，或绕过任务分配。

## 2. 参考来源和吸收点

Anthropic long-running harness:

- 核心思想是“清空模型上下文，但不清空项目状态”。
- durable state 写进文件：规格、feature list、progress、git history、session logs。
- 每轮 agent 只推进一个小而可验证的 slice。
- 用 invariant validation 防止后续 agent 偷改事实源。

Anthropic quickstart autonomous-coding:

- 第一轮 initializer agent 创建 source of truth 和项目环境。
- 后续 coding agent 从文件恢复，不依赖上一轮模型记忆。

`wshobson/agents`:

- 角色和技能分层加载，避免一次性把所有内容塞进上下文。
- 插件/agent/skill 都要边界清晰。
- Agent Teams 插件强调 plan-first、小团队、文件所有权、监控状态、优雅 shutdown。
- 典型角色包括 lead、reviewer、debugger、implementer。

`multica-ai/multica`:

- 把 agent 当作 teammate，任务像 issue 一样分配。
- daemon/runtime 负责检测 agent CLI、领取任务、执行、回传状态。
- 有任务生命周期、执行历史、run messages、heartbeat、autopilot。
- UI 不是只看聊天，而是看 issue board、agent runtime、执行日志和状态流。

## 3. 当前代码状态

当前已经实现：

- Python package: `autoai-longrun`。
- Web UI: `python -m autoai ui`，默认 `http://127.0.0.1:8765`。
- 项目初始化：`autoai/project.py`。
- 长跑 harness: `autoai/harness.py`。
- prompt 渲染：`autoai/prompts.py` 和 `autoai/templates/`。
- 权限参数注入：`autoai/runner.py`。
- Web API: `autoai/ui_server.py`。
- UI 静态文件：`autoai/ui_static/index.html`、`styles.css`、`app.js`。
- 默认项目角色：`autoai/agents.py`，写入 `.claude/agents/*.md`。
- 角色策略：`autoai/roles.py`，根据项目需求生成 `.autoai/roles.json`，支持每个角色配置成本等级、模型、API key 环境变量、本地 API key、预算和边界，并同步生成 `.claude/agents/*.md`。
- 任务队列：`autoai/tasks.py`，写入 `.autoai/tasks.json`。
- Human-in-the-loop：`autoai/help_requests.py`，写入 `.autoai/help_requests.json` 和 `.autoai/messages.jsonl`；Web UI 的 Help 页可以答复，harness 在有未答复请求时会暂停为 `blocked`。
- 测试：`tests/`，当前 19 个单元测试通过。

重要约束：

- 项目没有“项目语言”配置。之前用户明确要求不要加。只有 Web UI 自身有界面语言切换。
- UI 语言只存在浏览器 `localStorage["autoai.uiLanguage"]`。
- 权限模式可以注入 Claude Code 参数，但无法绕过 Claude Code 或系统本身不允许绕过的确认。

## 4. 当前项目文件协议

每个被 AutoAI 管理的项目应该包含：

- `task_spec.md`: 用户需求和项目规格。
- `feature_list.json`: durable source of truth。初始化 agent 创建，后续只能改 `passes`。
- `autoai-progress.md`: 每轮交接日志。
- `.autoai/config.json`: harness 配置。
- `.autoai/run_state.json`: 下一轮 session、最近状态、连续失败次数。
- `.autoai/tasks.json`: 任务队列。
- `.autoai/roles.json`: 角色策略、模型配置、预算和边界。
- `.autoai/role_secrets.json`: 本地角色 API key secrets。新项目 `.gitignore` 会忽略它。
- `.autoai/help_requests.json`: agent 无法继续时向用户求助。
- `.autoai/messages.jsonl`: 求助、答复、关闭等通信事件。
- `.autoai/sessions/`: 每轮 prompt、stdout、stderr、verify logs。
- `.claude/agents/*.md`: Claude Code 项目 subagents。
- `verification/`: 测试证据。

下一阶段建议新增：
- `.autoai/task_graph.json`: 自动拆分出来的任务依赖图。
- `.autoai/messages.jsonl`: agent 间通信日志。当前已经用于 Help 请求和用户答复，后续可扩展为完整 team communication。
- `.autoai/team_state.json`: 当前团队、成员状态、分配任务、heartbeat。
- `.autoai/budget_ledger.jsonl`: token 预算和实际消耗账本。
- `.autoai/decision_log.md`: 高层设计决策和越权审批记录。

## 5. 角色预算设计

用户想要的“工资不同”在系统里应该映射为“预算不同”：

- 高工资角色：项目经理、架构师、最终 reviewer。使用更强模型、更长上下文、更高输出预算、更长 timeout。
- 中等角色：实现者、测试者。使用平衡模型和中等上下文。
- 低工资角色：重复性执行者、格式整理、简单迁移、文档同步。使用低预算模型、少量文件上下文、短 timeout。

建议新增 `.autoai/roles.json`：

```json
[
  {
    "id": "project-manager",
    "display_name": "Project Manager",
    "model_tier": "high",
    "cost_tier": "high",
    "token_budget": {
      "max_prompt_chars": 60000,
      "max_output_chars": 12000,
      "max_files": 30
    },
    "authority": {
      "can_decompose_tasks": true,
      "can_assign_tasks": true,
      "can_change_architecture": true,
      "can_mark_done": false
    },
    "scope": {
      "allowed_task_types": ["planning", "architecture", "coordination", "final-review"],
      "write_paths": [".autoai/tasks.json", ".autoai/task_graph.json", "autoai-progress.md"],
      "read_paths": ["**/*"]
    },
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "default_assignees": ["architect", "implementer", "tester", "reviewer"]
  },
  {
    "id": "implementer",
    "display_name": "Implementer",
    "model_tier": "medium",
    "cost_tier": "medium",
    "token_budget": {
      "max_prompt_chars": 30000,
      "max_output_chars": 8000,
      "max_files": 12
    },
    "authority": {
      "can_decompose_tasks": false,
      "can_assign_tasks": false,
      "can_change_architecture": false,
      "can_mark_done": false
    },
    "scope": {
      "allowed_task_types": ["implementation", "bugfix"],
      "write_paths": ["assigned_only"],
      "read_paths": ["assigned_area", "task_spec.md", "autoai-progress.md"]
    },
    "tools": ["Read", "Grep", "Glob", "Bash", "Edit", "Write"]
  },
  {
    "id": "routine-worker",
    "display_name": "Routine Worker",
    "model_tier": "low",
    "cost_tier": "low",
    "token_budget": {
      "max_prompt_chars": 12000,
      "max_output_chars": 4000,
      "max_files": 5
    },
    "authority": {
      "can_decompose_tasks": false,
      "can_assign_tasks": false,
      "can_change_architecture": false,
      "can_mark_done": false
    },
    "scope": {
      "allowed_task_types": ["repetitive-edit", "formatting", "simple-doc-update"],
      "write_paths": ["assigned_only"],
      "read_paths": ["assigned_area"]
    },
    "tools": ["Read", "Grep", "Glob", "Edit"]
  }
]
```

注意：Claude Code subagents 的真实 token 计费不一定能被本项目逐 token 控制。可靠方案是由 harness 控制每个角色看到多少上下文、用哪个 command/model、跑多久、能改哪些文件。若某个 CLI 支持输出 token telemetry，就把它记录到 `.autoai/budget_ledger.jsonl`。

## 6. Token 预算执行方案

预算不要只写在 prompt 里，要由 harness 执行。

第一层：上下文裁剪

- 根据角色 `max_files` 和 `max_prompt_chars` 决定本轮 prompt 附带多少文件摘要。
- 项目经理拿到全局摘要、任务图、进度和关键文件索引。
- 实现者只拿到自己的任务、分配文件、相关接口摘要。
- routine-worker 只拿到明确输入输出和被允许文件。

第二层：模型/命令选择

- 在 `.autoai/roles.json` 中配置每个角色的 `agent_command_template`。
- 高预算角色可以用强模型。
- 低预算角色可以用便宜模型或更短 timeout。
- 如果 CLI 不支持 max output 参数，就通过 prompt、timeout 和任务粒度限制。

第三层：运行时限制

- `timeout_seconds` 按角色设置。
- `max_iterations_per_task` 按角色设置。
- 对重复性任务使用更小任务 slice，而不是让一个低预算角色读全项目。

第四层：预算账本

`.autoai/budget_ledger.jsonl` 每行一条：

```json
{
  "time": "2026-05-02T12:00:00+08:00",
  "session_id": "0007-coding-...",
  "role_id": "implementer",
  "task_id": "T-1234abcd",
  "model_tier": "medium",
  "prompt_chars": 18200,
  "output_chars": 4100,
  "timeout_seconds": 1800,
  "estimated_cost_units": 2.1,
  "actual_tokens": null
}
```

## 7. 自动拆分任务设计

新增模块建议：

- `autoai/roles.py`: 读取和校验 `.autoai/roles.json`。
- `autoai/planner.py`: 任务拆解、依赖图、角色推荐。
- `autoai/dispatcher.py`: 从任务队列选择任务，分配角色，启动执行。
- `autoai/team_state.py`: 团队成员、heartbeat、状态机。
- `autoai/comm.py`: messages.jsonl 读写。
- `autoai/budget.py`: 预算计算和账本。
- `autoai/policy.py`: 越权检测。

自动拆任务流程：

1. Project Manager 读取 `task_spec.md`、`feature_list.json`、`.autoai/tasks.json`、`autoai-progress.md`。
2. 如果任务太大，拆成 `task_graph.json`：

```json
{
  "tasks": [
    {
      "id": "T-frontend-ui",
      "title": "Build task board UI",
      "type": "implementation",
      "priority": "high",
      "depends_on": [],
      "suggested_role": "implementer",
      "allowed_write_paths": ["autoai/ui_static/index.html", "autoai/ui_static/app.js", "autoai/ui_static/styles.css"],
      "acceptance": ["User can create a task", "Task appears without refresh"]
    }
  ]
}
```

3. 角色选择器给每个任务打分：

- `allowed_task_types` 是否匹配。
- 是否需要架构判断。
- 修改文件数量。
- 风险等级。
- 重复程度。
- 是否需要浏览器验证。
- 当前角色预算是否足够。

4. Dispatcher 把任务写入 `.autoai/tasks.json`，并更新 assignee。
5. 低预算角色只执行明确 assigned task。复杂或越界时必须发 `blocker` 给 Project Manager。

## 8. 越界控制设计

“角色不能做越界工作”不能只靠文字约束。建议做三层控制。

Prompt 层：

- 每个角色 prompt 明确列出职责、禁止事项、允许文件、允许工具、任务边界。
- 角色遇到越界必须输出 blocker，不得自行扩大范围。

Harness 层：

- 每个任务都有 `allowed_write_paths`。
- 运行前把允许路径放进 prompt 和环境变量。
- 运行后读取 git diff，检查是否改了未授权文件。
- 如果发现越界，标记 session `policy-failed`，不要把任务标记完成。

工作区层：

- 严格模式下每个 worker 在独立 worktree 或临时副本里跑。
- Dispatcher 只合并允许路径里的 diff。
- Reviewer 负责检查跨任务冲突。

建议新增 policy violation 结构：

```json
{
  "session_id": "0008-coding-...",
  "role_id": "routine-worker",
  "task_id": "T-1234abcd",
  "violation": "write_path_not_allowed",
  "path": "autoai/harness.py",
  "allowed_write_paths": ["docs/**/*.md"],
  "action": "blocked"
}
```

## 9. Agent 通信协议

参考 Agent Teams 的 `team-status`、`team-delegate`、plan-first 和 Multica 的 run messages，建议用 append-only JSONL：

`.autoai/messages.jsonl`

```json
{
  "id": "M-000001",
  "time": "2026-05-02T12:00:00+08:00",
  "from": "project-manager",
  "to": "implementer",
  "task_id": "T-frontend-ui",
  "type": "assignment",
  "body": "Build the task board UI. Only edit ui_static files.",
  "references": ["task_spec.md", ".autoai/task_graph.json"],
  "requires_ack": true
}
```

消息类型：

- `plan`: Project Manager 输出拆解方案。
- `assignment`: 给角色分配任务。
- `ack`: 角色确认边界。
- `progress`: 执行进度。
- `blocker`: 角色发现越权、信息不足、测试失败。
- `handoff`: 角色交接结果。
- `review`: reviewer 输出发现。
- `decision`: Project Manager 或用户确认高层决策。
- `heartbeat`: 全天运行时的健康状态。

通信规则：

- Worker 不能直接改 task graph，只能发 `blocker` 或 `handoff`。
- Reviewer 不能直接改业务代码，除非任务明确是“修复 review finding”。
- Project Manager 可以重排任务，但不能直接把 feature 标记完成。
- Tester 可以建议 `passes=true`，但最终由 harness 在验证通过后允许更新。
- 每个 assignment 必须包含 `allowed_write_paths` 和 acceptance criteria。

## 10. UI 设计计划

当前 UI 已有：

- Overview
- Prompt
- Spec
- Progress
- Sessions
- Agents
- Tasks
- Job Log

下一阶段 UI：

- Roles 页：编辑 `.autoai/roles.json`。
  - role id
  - display name
  - model tier
  - token budget
  - allowed task types
  - allowed write paths
  - tools
  - can delegate / can assign / can mark done
- Task Board：从列表升级为 backlog/todo/in progress/in review/done/blocked 看板。
- Team 页：显示 active team、角色状态、heartbeat、当前任务、预算消耗。
- Messages 页：显示 `.autoai/messages.jsonl`，按 task 或 role 过滤。
- Budget 页：显示每个角色估算 token/cost、失败率、平均完成时间。
- Policy 页：显示越权事件和需要用户确认的决策。

## 11. API 计划

当前已有：

- `GET /api/status`
- `GET /api/prompt`
- `GET /api/progress`
- `GET /api/spec`
- `GET /api/sessions`
- `GET /api/session`
- `GET /api/agents`
- `GET /api/tasks`
- `POST /api/init`
- `POST /api/run`
- `POST /api/agents/install-defaults`
- `POST /api/tasks`
- `POST /api/tasks/status`

建议新增：

- `GET /api/roles`
- `POST /api/roles`
- `PUT /api/roles/:id`
- `DELETE /api/roles/:id`
- `POST /api/tasks/decompose`
- `POST /api/tasks/assign`
- `GET /api/task-graph`
- `GET /api/messages`
- `POST /api/messages`
- `GET /api/team-state`
- `POST /api/team/shutdown`
- `GET /api/budget`
- `GET /api/policy-violations`
- `POST /api/job/stop`

`POST /api/job/stop` 很重要，因为全天运行必须能从 UI 停止。

## 12. 开发阶段路线图

Phase 1: Role Policy (done)

- 已新增 `autoai/roles.py`。
- 初始化项目时会根据目标和 Markdown requirements 生成 `.autoai/roles.json`。
- UI 已新增 Roles 页。
- prompt 渲染中已加入角色预算、模型/API key 来源和边界。
- 保存角色会同步 `.claude/agents/*.md`。
- API key 不回显，写入 `.autoai/role_secrets.json`。
- 已新增角色 JSON、secret、agent sync 测试。

Phase 2: Task Decomposition

- 新增 `autoai/planner.py`。
- `POST /api/tasks/decompose` 调用 Project Manager prompt 生成任务图。
- 任务自动带 `suggested_role`、`allowed_write_paths`、acceptance criteria。
- UI 添加“一键拆分需求”按钮。

Phase 3: Dispatcher

- 新增 `autoai/dispatcher.py`。
- 根据任务状态、依赖和角色预算挑选下一项工作。
- 让 harness 不只是“最高优先级 feature”，而是从 task graph 中取任务。
- 支持单任务运行、连续运行、按角色运行。

Phase 4: Communication Log

- 新增 `autoai/comm.py`。
- 每次 assignment、progress、handoff、review 都写入 `.autoai/messages.jsonl`。
- UI 展示消息流。

Phase 5: Boundary Enforcement

- 新增 `autoai/policy.py`。
- 每轮运行后检查 git diff。
- 不允许角色改未授权路径。
- 严格模式使用临时 worktree，合并前验证。

Phase 6: Budget Accounting

- 新增 `autoai/budget.py`。
- 记录 prompt chars、output chars、timeout、估算 cost units。
- 如果 CLI 返回真实 token usage，就写入 actual tokens。
- UI 显示每个角色消耗。

Phase 7: Daemon / Autopilot

- 参考 Multica daemon。
- 做本地 runtime loop：定时扫描项目、领取任务、heartbeat、执行、写回。
- UI 可以创建 autopilot：每天、每小时、工作日、手动触发。
- 先本地单机，不急着做云端。

## 13. 下一位 AI 的建议任务

优先做 Phase 2: Task Decomposition。不要先重构整个系统。

具体步骤：

1. 阅读 `README.md` 和本文档。
2. 运行：

```powershell
python -m unittest discover -s tests
node --check autoai\ui_static\app.js
```

3. 新增 `autoai/planner.py`，实现从 `task_spec.md`、`feature_list.json`、`.autoai/roles.json` 自动拆分任务。
4. 生成 `.autoai/task_graph.json`，每个任务包含 `suggested_role`、`allowed_write_paths`、依赖和 acceptance criteria。
5. 修改 `ui_server.py`，添加 `/api/tasks/decompose`。
6. 修改 UI，在 Tasks 页添加“一键拆分需求”。
7. prompt 每轮只带当前任务相关角色和边界，不要把全部历史都塞进去。
8. 添加 `tests/test_planner.py`，并更新 prompt/UI server 测试。

完成后再做 dispatcher 和越权 diff 检查。

## 14. 关键设计判断

- 不要让历史聊天变成主要记忆。聊天可展示，但长期记忆必须是项目文件。
- 不要把所有角色说明都塞进每一轮 prompt。只放当前模式、相关角色、当前任务。
- 不要让低预算角色读全项目。低预算的本质是少上下文、小任务、短输出。
- 不要只靠 prompt 禁止越权。最终要检查 git diff 和 allowed paths。
- 不要把多 agent 做成一堆并发进程后不管。必须有 team state、messages、heartbeat、review。
- 不要新增项目语言设置。用户已经明确反对。

## 15. 给下一位 AI 的接手提示词

可以直接把下面这段发给下一位 AI：

```text
你接手的是 D:\code\aiskill\autoai。先读 README.md 和 docs/DEVELOPMENT.md。
当前系统已经有本地 Web UI、长跑 harness、Claude 权限模式注入、Markdown 需求上传、session 历史、Help 人工协助、.autoai/tasks.json 任务队列，以及已经实现的 .autoai/roles.json 角色策略。角色可根据需求自动生成，并可配置 cost_tier、model、api_key_env、本地 API key、token_budget、authority、scope、tools；保存后会同步 .claude/agents。

用户下一步要的是：自动拆分细分任务，然后根据角色策略分配合适角色。请优先实现 Phase 2 Task Decomposition：
1. 新增 autoai/planner.py。
2. 生成 .autoai/task_graph.json。
3. 每个任务必须包含 suggested_role、allowed_write_paths、depends_on、acceptance。
4. UI Tasks 页增加“一键拆分需求”按钮。
5. prompt 每轮使用当前任务 + 相关角色边界，不要塞全部角色和全部任务。
6. 加测试并跑 python -m unittest discover -s tests。
不要重新加“项目语言”设置，UI 语言只能是界面本地设置。
```
