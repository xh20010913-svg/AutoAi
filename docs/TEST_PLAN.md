# AutoAI 测试计划

## 测试层次

```
┌─────────────────────────────────────┐
│           E2E / 手动测试            │
│   (Electron 前端 + 后端完整流程)     │
├─────────────────────────────────────┤
│         集成测试 (API)              │
│   (FastAPI TestClient + 真实 DB)    │
├─────────────────────────────────────┤
│           单元测试                   │
│   (纯 Python 模块，mock 外部依赖)    │
└─────────────────────────────────────┘
```

## 当前测试覆盖

### 单元测试 (12 文件, 19 用例)

| 测试文件 | 用例数 | 覆盖模块 |
|---------|--------|---------|
| `test_project.py` | 1 | `autoai/project.py` — 项目初始化，控制文件创建 |
| `test_harness.py` | 2 | `autoai/harness.py` — Initializer 校验，Help 请求暂停 |
| `test_features.py` | 2 | `autoai/features.py` — Feature 不变性校验，passes 修改 |
| `test_prompts.py` | 1 | `autoai/prompts.py` — Prompt 渲染，模板变量替换 |
| `test_runner.py` | 3 | `autoai/runner.py` — 权限模式注入 |
| `test_tasks.py` | 1 | `autoai/tasks.py` — 任务创建与状态更新 |
| `test_help_requests.py` | 1 | `autoai/help_requests.py` — Help 创建/答复/关闭 |
| `test_roles.py` | 3 | `autoai/roles.py` — 角色生成、API key 存储、Agent 同步 |
| `test_agents.py` | 1 | `autoai/agents.py` — 默认 Agent 安装 |
| `test_spec_upload.py` | 1 | Spec 上传与 task_spec.md 生成 |
| `test_ui_server.py` | 2 | `autoai/server.py` — Status payload，Prompt endpoint |
| `test_claude_settings.py` | 1 | `autoai/claude_settings.py` — Skip bypass 开关 |

### API 集成测试

通过 FastAPI TestClient 测试完整 API 流程：
- `GET /api/status` — 项目状态
- `POST /api/init` — 项目初始化
- `POST /api/tasks` / `PATCH /api/tasks/{id}` — 任务 CRUD
- `POST /api/run` / `GET /api/job` — Harness 运行
- `GET /api/roles` / `PUT /api/roles` — 角色管理
- `POST /api/help` / `POST /api/help/{id}/answer` — Help 请求
- `WS /ws` — WebSocket 事件推送

## 建议新增测试

### 高优先级

| 测试内容 | 类型 | 说明 |
|---------|------|------|
| Session 日志读取 | 单元/集成 | 验证 `/api/sessions` 和 `/api/sessions/{id}` 返回正确日志文件 |
| 角色越权检测 | 单元 | 验证 role authority 字段在任务分配时的校验逻辑 |
| 前端 API 客户端 | 单元 | `frontend/renderer/api.js` 中各 API 函数的 mock 测试 |
| 预算超限处理 | 单元 | 验证 prompt chars / output chars 超限时的行为 |

### 中优先级

| 测试内容 | 类型 | 说明 |
|---------|------|------|
| Harness 连续失败计数 | 集成 | 验证 `consecutive_failures` 在多次失败后正确递增 |
| 多 session 循环 | 集成 | 模拟多轮 coding session 的执行流程 |
| Feature 完成检测 | 单元 | 验证所有 feature passes=true 时 harness 停止 |
| 并发 run 冲突 | 集成 | 验证同时启动多个 run job 的行为 |
| 角色 secrets 不泄露 | 单元 | 验证 api_key 不出现在 API 响应中 |

### 低优先级

| 测试内容 | 类型 | 说明 |
|---------|------|------|
| Git 集成 | 单元 | Mock git 命令，验证 commit_all 行为 |
| Windows 进程终止 | 集成 | 验证 `_force_kill` 在 Windows 上的行为 |
| 大文件 prompt 渲染 | 单元 | 验证大量 feature 时 prompt 不会溢出 |
| 前端组件渲染 | E2E | 使用 Electron 测试框架 |

## 测试命令

```bash
# 运行所有测试
python -m unittest discover -s tests

# 运行单个测试文件
python -m unittest tests.test_tasks

# 运行单个用例
python -m unittest tests.test_tasks.TestTasks.test_create_and_update_task

# 运行集成测试
python -m unittest tests.test_ui_server
```

## CI/CD

建议在 GitHub Actions 中配置：
- `push` 触发：运行 `python -m unittest discover -s tests`
- `pull_request` 触发：同上 + 前端静态检查 (`node --check autoai/ui_static/app.js`)
- 矩阵测试：Python 3.11 / 3.12 / 3.13
