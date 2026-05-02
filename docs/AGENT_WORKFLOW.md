# Agent 协作流程

AutoAI 是一个多 agent 协作的自主开发平台，支持单 agent、subagents 和 Agent Teams 三种协作模式。

## 核心概念

### Harness 循环

AutoAI 的核心是一个长时间运行的 harness 循环：

1. **检查阻塞** — 如果有未答复的 Help 请求，停止运行等待人工介入
2. **渲染 prompt** — 根据 session 类型（initializer / coding）和当前项目状态生成 prompt
3. **运行 verify 命令**（可选）— 在 agent 运行前执行验证脚本
4. **执行 agent** — 通过 subprocess 调用 Claude Code CLI，传入 prompt
5. **验证结果** — 检查 feature_list.json 不变性
6. **记录进度** — 更新 autoai-progress.md 和 run_state
7. **判断是否继续** — 所有 feature 通过或达到最大迭代数则停止
8. **等待并循环** — 间隔指定秒数后开始下一轮

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 渲染     │───▶│ 验证     │───▶│ 执行     │───▶│ 记录     │
│ Prompt   │    │ (verify) │    │ Agent    │    │ 进度     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      ▲                                               │
      │         ◀─── 间隔等待 ◀──                       │
      │                                               │
      └───────────────────────────────────────────────┘
```

### Session 类型

| 类型 | 触发条件 | 职责 |
|------|---------|------|
| `initializer` | `feature_list.json` 不存在 | 创建 feature list，初始化项目环境 |
| `coding` | `feature_list.json` 已存在 | 推进 feature 状态 |

每轮 session 使用 **fresh context**，agent 通过磁盘文件恢复项目状态，不依赖上一轮的模型记忆。

---

## 角色体系

### 默认角色目录 (8 个)

| 角色 ID | 显示名 | 成本等级 | 任务类型 | 工具 |
|---------|--------|---------|---------|------|
| `project-manager` | Project Manager | high | planning, architecture, coordination, final-review | Read, Grep, Glob, Bash |
| `agent-orchestrator` | Agent Orchestrator | high | agent-orchestration, dispatcher, workflow | Read, Grep, Glob, Bash, Edit, Write |
| `frontend-developer` | Frontend Developer | medium | frontend, ui, ux, dashboard | Read, Grep, Glob, Bash, Edit, Write |
| `backend-developer` | Backend Developer | medium | backend, api, persistence, daemon | Read, Grep, Glob, Bash, Edit, Write |
| `implementer` | Implementer | medium | implementation, bugfix | Read, Grep, Glob, Bash, Edit, Write |
| `tester` | Tester | medium | testing, verification, qa | Read, Grep, Glob, Bash, Edit, Write |
| `security-reviewer` | Security Reviewer | medium | security, permissions, secrets, policy-review | Read, Grep, Glob, Bash |
| `reviewer` | Reviewer | high | review, quality, risk | Read, Grep, Glob, Bash |

`project-manager`、`implementer`、`tester`、`reviewer` 为强制角色（always），始终包含。

### 角色自动生成

项目初始化时，系统根据 goal 和 spec 文本中的关键词匹配角色目录，最多生成 8 个角色。生成的角色配置会写入数据库并同步为 `.claude/agents/*.md` 文件。

### 角色属性

每个角色拥有以下配置：

- **token_budget** — `max_prompt_chars`, `max_output_chars`, `max_files`, `timeout_seconds`
- **authority** — `can_decompose_tasks`, `can_assign_tasks`, `can_change_architecture`, `can_mark_done`
- **scope** — `write_paths`（允许修改的路径）、`read_paths`（允许读取的路径）
- **task_types** — 该角色可以执行的任务类型列表
- **tools** — 允许使用的工具列表

### 预算等级

| 等级 | max_prompt_chars | max_output_chars | max_files | timeout_seconds |
|------|-----------------|------------------|-----------|-----------------|
| high | 60,000 | 12,000 | 30 | 7,200 |
| medium | 32,000 | 8,000 | 14 | 3,600 |
| low | 14,000 | 4,000 | 6 | 1,800 |

---

## 默认 Subagents

AutoAI 为 Claude Code 提供 5 个默认项目 subagent：

| Agent | 用途 | 工具 |
|-------|------|------|
| `team-lead` | 任务分解、分配所有权、协调团队、汇总结果 | Read, Grep, Glob, Bash, Edit, Write |
| `architect` | 系统设计、边界划分、数据流分析、实施计划 | Read, Grep, Glob, Bash |
| `implementer` | 在明确文件所有权边界内实现分配的模块 | Read, Grep, Glob, Bash, Edit, Write |
| `tester` | 验证计划、测试实现、回归检查、证据捕获 | Read, Grep, Glob, Bash, Edit, Write |
| `reviewer` | 代码审查、可靠性审查、安全检查、缺失测试检查 | Read, Grep, Glob, Bash |

---

## 协作模式

### Single（默认）

单 agent 模式。Agent 独自完成所有工作，可参考 `.claude/agents/` 中的角色指导，但保持简单执行。

### Subagents

启用 Claude Code 项目 subagents。工作流程：

1. 制定简短的执行计划
2. 将边界清晰的子任务委派给对应角色
3. 保持文件所有权明确
4. 整合并验证结果

### Agent Team

启用 Claude Code Agent Teams（实验性）。Harness 会设置 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 环境变量。

- 使用小团队（2-4 人）
- 先计划，再分配独立的文件所有权
- 监控进度，汇总最终结果
- 若 Agent Teams 不可用，回退到 subagents 模式

---

## 任务生命周期

```
backlog ──▶ todo ──▶ in_progress ──▶ in_review ──▶ done
                         │                │
                         ▼                ▼
                      blocked          cancelled
```

| 状态 | 含义 |
|------|------|
| `backlog` | 积压，尚未纳入当前迭代 |
| `todo` | 待开始 |
| `in_progress` | 正在执行 |
| `in_review` | 等待审查 |
| `done` | 已完成 |
| `blocked` | 被阻塞，需要外部介入 |
| `cancelled` | 已取消 |

---

## Feature List 管理

`feature_list.json` 是整个系统的 **唯一事实源（Source of Truth）**：

- 由 initializer session 创建
- 后续 session 只能修改 `passes` 字段
- harness 每轮运行后执行不变性校验，防止 agent 篡改 feature 定义
- 若 feature 被修改，会被标记为 `validation failed`
- 可通过 `POST /api/validate` 手动校验或刷新 baseline

---

## Human-in-the-Loop (Help 请求)

当 agent 遇到无法自行处理的情况时，创建 Help 请求：

- **open** — 等待人工答复，harness 停止运行
- **answered** — 人工已答复，agent 可继续
- **closed** — 已关闭

所有 Help 请求和答复都记录在 `messages` 表中，形成完整的通信日志。

---

## 权限模式

Agent 运行时可通过 `permission_mode` 控制 Claude Code 的权限行为：

| 模式 | CLI 参数 | 说明 |
|------|---------|------|
| `default` | (无) | 默认交互行为 |
| `acceptEdits` | `--permission-mode acceptEdits` | 接受编辑 |
| `auto` | `--permission-mode auto` | 自动模式 |
| `bypassPermissions` | `--dangerously-skip-permissions` | 跳过权限检查 |

---

## 项目文件协议

每个被 AutoAI 管理的项目包含以下文件：

| 文件 | 用途 |
|------|------|
| `task_spec.md` | 用户需求和项目规格 |
| `feature_list.json` | 功能清单（唯一事实源） |
| `autoai-progress.md` | 每轮 session 的进度日志 |
| `.autoai/autoai.db` | SQLite 数据库（配置、任务、角色、状态） |
| `.autoai/sessions/` | 每轮 prompt、stdout、stderr 日志 |
| `.claude/agents/*.md` | Claude Code subagent 定义 |
| `verification/` | 测试证据 |

---

## 通信规则

- Worker 不能直接改 task graph，只能发 `blocker` 或 `handoff`
- Reviewer 不能直接改业务代码（除非任务明确是修复 review finding）
- Project Manager 可以重排任务，但不能直接标记 feature 完成
- Tester 可以建议 `passes=true`，但最终由 harness 验证后允许更新
- 每个 assignment 必须包含 `allowed_write_paths` 和 acceptance criteria
