# AutoAI

本地桌面应用，用于管理长时间运行的 AI Agent 任务。参照 [multica](https://github.com/multica-ai/multica) 的设计理念，提供看板式任务管理、Agent 自动执行、角色系统和实时进度追踪。

## 架构

- **前端**: Electron（暗色主题，看板 UI）
- **后端**: Python FastAPI + WebSocket
- **存储**: SQLite（本地单文件数据库）
- **Agent**: 通过 subprocess 调用 Claude Code 等 CLI 工具

## 快速开始

### 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy websockets
cd frontend && npm install
```

### 启动应用

```bash
# 方式一：直接启动 Electron（会自动启动 Python 后端）
cd frontend && npm start

# 方式二：分别启动
python -m autoai serve --port 18765    # 启动后端
# 然后在浏览器打开 http://127.0.0.1:18765

# 方式三：CLI 命令行
python -m autoai init --project-dir ./my-project --goal "Build something" --agent-command "claude -p"
python -m autoai run --project-dir ./my-project --max-iterations 3
```

## 核心功能

### 看板视图（Board）
- 6 列 Kanban：Backlog → Todo → In Progress → In Review → Done → Blocked
- 拖拽改变任务状态
- 按优先级和角色筛选
- 实时更新

### Agent 运行
- 点击 Run 启动 harness，自动循环执行 Agent session
- WebSocket 实时推送进度
- 支持断点恢复（从 `.autoai/run_state.json` 继续）

### 角色系统
- 根据项目目标自动生成角色（project-manager、implementer、tester、reviewer 等）
- 每个角色可配置模型、API key、成本等级
- 自动生成 `.claude/agents/*.md` 供 Claude Code subagents 使用

### Session 日志
- 查看每轮 session 的 prompt、stdout、stderr
- 完整的执行历史

## 项目结构

```
autoai/
├── autoai/                  # Python 后端
│   ├── api/                 # FastAPI 路由
│   │   ├── tasks.py         # 任务 CRUD
│   │   ├── agents.py        # 角色管理
│   │   ├── sessions.py      # Session 查看
│   │   ├── help.py          # Help 请求
│   │   └── run.py           # Harness 运行控制
│   ├── server.py            # FastAPI 主应用 + WebSocket
│   ├── harness.py           # 核心调度循环
│   ├── runner.py            # Agent 子进程执行
│   ├── features.py          # Feature list 管理
│   ├── prompts.py           # Prompt 模板渲染
│   ├── db.py                # SQLite 数据层
│   ├── models.py            # SQLAlchemy ORM 模型
│   ├── config.py            # 项目配置
│   ├── state.py             # 运行状态
│   ├── tasks.py             # 任务管理（ORM）
│   ├── help_requests.py     # Help 请求（ORM）
│   ├── roles.py             # 角色系统
│   ├── agents.py            # Agent 定义
│   ├── cli.py               # CLI 入口
│   └── templates/           # Prompt 模板
├── frontend/                # Electron 前端
│   ├── main.js              # Electron 主进程
│   ├── preload.js           # 安全桥接
│   └── renderer/            # 渲染进程
│       ├── index.html       # 主页面
│       ├── app.js           # SPA 逻辑
│       ├── api.js           # API + WebSocket 客户端
│       └── style.css        # 暗色主题样式
├── tests/                   # 单元测试
└── pyproject.toml           # Python 包配置
```

## CLI 命令

```bash
python -m autoai init --project-dir <dir> --goal <goal> --agent-command <cmd>
python -m autoai run --project-dir <dir> --max-iterations <n>
python -m autoai serve --port 18765
python -m autoai status --project-dir <dir>
python -m autoai validate --project-dir <dir>
python -m autoai prompt --project-dir <dir> --kind coding
```

## 测试

```bash
python -m unittest discover -s tests
```

## 设计思路

参考 Anthropic 的 [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)，核心机制：

- 每轮 session 使用 fresh context，通过磁盘文件交接进度
- `feature_list.json` 作为唯一事实源，防止 agent 跳过或偷改功能
- 通过 git commit 和进度文件防止断片
- 通过不变性校验防止后续 agent 篡改 feature 定义

## License

MIT
