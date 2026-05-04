"""
AutoAi Task Dispatcher — 自动任务派发脚本

扫描 Multica 工作区，当 agent 完成任务后自动派发新任务。
不弹窗、不启动 git cmd，通过 HTTP API 直接通信。

用法:
    python scripts/dispatch.py              # 单次扫描
    python scripts/dispatch.py --loop 60    # 每 60 秒循环扫描
    python scripts/dispatch.py --dry-run    # 只看不干
"""

import json
import subprocess
import sys
import time
import argparse
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────────────────────────

WORKSPACE_ID = "95da582a-1d61-47b4-9400-52660c39e8a1"
PROJECT_NAME = "AutoAi"
REPO_URL = "https://github.com/xh20010913-svg/AutoAi"

# Agent 角色分配
AGENTS = {
    "backend": [
        {"id": "208acdf3-d3f0-480b-9855-64435925081b", "name": "后端开发"},
        {"id": "b8c65682-90bc-4945-9b61-906e34c2cfd0", "name": "后端开发2"},
        {"id": "b3183a17-125c-44f8-a425-2f21f62950b4", "name": "后端开发3"},
    ],
    "frontend": [
        {"id": "65682ad4-7929-4dd2-9395-7683d92fd206", "name": "前端开发"},
    ],
    "tester": [
        {"id": "329269a9-e5b4-4b62-8ddc-a0b06a8d1cc7", "name": "测试工程师"},
        {"id": "d7d57347-edd8-44ce-804b-0b08794e8075", "name": "测试开发2"},
        {"id": "47ce74db-52c0-44fc-b0a3-bc0d8f2da8c0", "name": "测试开发3"},
    ],
}

# 后端任务池 (按顺序派发)
BACKEND_TASKS = [
    {
        "title": "[v0.2] 后端用户认证 — JWT 注册/登录",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
实现用户注册、登录、JWT token 签发。

## 要求
1. User 模型: username, email, hashed_password, created_at
2. auth schemas: UserCreate, UserLogin, UserResponse, Token
3. API 端点:
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login → JWT token
   - GET /api/v1/auth/me → 当前用户
4. 密码 bcrypt 哈希, JWT 24h 过期
5. 测试覆盖注册和登录流程

## 完成后
提交到分支 feat/auth, 推送到 GitHub, 评论报告完成.""",
        "priority": "high",
    },
    {
        "title": "[v0.2] 后端 Project CRUD API",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
实现 Project 的增删改查 API。

## 要求
1. Project 模型: name, description, owner_id, status, created_at, updated_at
2. API 端点:
   - POST /api/v1/projects
   - GET /api/v1/projects (分页)
   - GET /api/v1/projects/:id
   - PUT /api/v1/projects/:id
   - DELETE /api/v1/projects/:id
3. 测试

## 完成后
提交到分支 feat/project-api, 推送到 GitHub, 评论报告完成.""",
        "priority": "high",
    },
    {
        "title": "[v0.2] WebSocket 实时推送",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
实现 WebSocket 端点，实时推送任务变更。

## 要求
1. WS /api/v1/ws 端点
2. ConnectionManager 管理连接
3. 任务 CRUD 时广播事件
4. 前端可订阅接收

## 完成后
提交到分支 feat/websocket, 推送到 GitHub, 评论报告完成.""",
        "priority": "medium",
    },
]

# 前端任务池
FRONTEND_TASKS = [
    {
        "title": "[v0.2] UI 重新设计 — 独特像素风格",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
重新设计 UI，使其有独特风格，区别于 Motica/Linear 等产品。

## 设计方向
- 像素风格 + 现代感的混搭
- 暖色调为主 (amber/orange 系列)，不用纯 zinc 灰
- 字体用等宽字体作为标题，正文用 sans-serif
- 卡片有轻微的像素边框效果
- 侧边栏带像素风格图标

## 要求
1. 更新 index.css 的 CSS 变量 — 暖色调主题
2. 更新 Sidebar — 像素风格 logo, 更好的视觉层次
3. 更新 Topbar — 品牌感更强
4. 每个页面的卡片组件加像素风格边框
5. 保持 shadcn/ui 组件但自定义样式

## 完成后
提交到分支 feat/ui-redesign, 推送到 GitHub, 评论报告完成.""",
        "priority": "high",
    },
    {
        "title": "[v0.2] 多语言支持 — 中文/英文切换",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
实现 i18n 国际化，Settings 页面可以切换中文/英文。

## 要求
1. 安装 react-i18next + i18next
2. 创建语言文件:
   - src/i18n/zh.json — 中文翻译
   - src/i18n/en.json — 英文翻译
3. 覆盖所有页面的硬编码文字:
   - Sidebar 导航文字
   - 页面标题
   - 按钮文字
   - Settings 页面所有选项
4. Settings 页面加语言切换器:
   - 下拉选择: 中文 / English
   - 选择后立即生效，存 localStorage
5. 创建 useTranslation hook 使用

## 完成后
提交到分支 feat/i18n, 推送到 GitHub, 评论报告完成.""",
        "priority": "high",
    },
    {
        "title": "[v0.2] 像素小人动画组件",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
创建像素小人动画组件，在 Agents 页面展示每个 agent 的工作状态。

## 参考
- claude-quest (github.com/Michaelliv/claude-quest) — RPG 风格像素动画
- react-pixel-motion — React 像素精灵动画组件

## 要求
1. 创建 PixelCharacter 组件:
   - 用 CSS 动画实现简单像素小人 (不需要精灵图，用 CSS div 拼像素)
   - 工作状态: 坐在桌子前敲键盘的动画 (手臂上下动)
   - 空闲状态: 坐在沙发上休息 (轻微晃动)
   - 出错状态: 红色闪烁
2. 创建场景组件:
   - 办公桌场景 (工作时)
   - 沙发场景 (空闲时)
3. 集成到 AgentsPage:
   - 每个 agent card 中显示像素小人
   - 根据 agent.status 切换场景
4. 用纯 CSS + HTML 实现像素风格 (不依赖外部图片)

## 完成后
提交到分支 feat/pixel-characters, 推送到 GitHub, 评论报告完成.""",
        "priority": "medium",
    },
]

# 测试任务 — 等开发完成后再派发
TESTER_TASKS = [
    {
        "title": "[测试] 验证 Task CRUD API 全部端点",
        "description": """项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi
操作: 先 multica repo checkout https://github.com/xh20010913-svg/AutoAi

## 目标
全面测试 Task CRUD API 的所有端点。

## 要求
1. 测试所有 CRUD 操作
2. 测试边界条件 (空标题、超长描述、无效状态)
3. 测试并发安全性
4. 生成测试报告

## 完成后
提交到分支 test/task-api, 推送到 GitHub, 评论报告完成.""",
        "priority": "medium",
    },
]


def run_multica(args: list[str], capture: bool = True) -> str:
    """运行 multica CLI 命令，静默不弹窗。"""
    result = subprocess.run(
        ["multica"] + args,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return result.stdout.strip() if capture else ""


def get_issues(status: str = None) -> list[dict]:
    """获取 issue 列表。"""
    cmd = ["issue", "list", "--output", "json", "--limit", "100"]
    if status:
        cmd.extend(["--status", status])
    try:
        output = run_multica(cmd)
        data = json.loads(output)
        return data.get("issues", [])
    except (json.JSONDecodeError, Exception) as e:
        print(f"  [WARN] Failed to get issues: {e}")
        return []


def get_agent_workload(agent_id: str) -> int:
    """获取 agent 当前进行中的任务数。"""
    issues = get_issues("in_progress")
    return sum(1 for i in issues if i.get("assignee_id") == agent_id)


def get_existing_titles() -> set[str]:
    """获取所有已有任务标题关键词，防止重复。"""
    issues = get_issues()
    titles = set()
    for issue in issues:
        title = issue.get("title", "")
        # 提取关键词
        for word in title.replace("[v0.2]", "").replace("[v0.3]", "").replace("[测试]", "").split():
            if len(word) > 2:
                titles.add(word.lower())
    return titles


def create_task(title: str, description: str, priority: str, assignee_name: str) -> str:
    """创建任务并分配给 agent。"""
    output = run_multica([
        "issue", "create",
        "--title", title,
        "--priority", priority,
        "--assignee", assignee_name,
        "--status", "todo",
        "--description-stdin",
    ])
    # 通过 stdin 传入 description
    result = subprocess.run(
        ["multica", "issue", "create",
         "--title", title,
         "--priority", priority,
         "--assignee", assignee_name,
         "--status", "todo",
         "--description-stdin"],
        input=description,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    try:
        data = json.loads(result.stdout)
        return data.get("id", "")
    except:
        return ""


def trigger_agent(issue_id: str, agent_id: str, agent_name: str):
    """通过 comment @mention 触发 agent。"""
    comment = f"[@{agent_name}](mention://agent/{agent_id}) 请开始执行此任务。完成后推送到分支并评论报告。"
    subprocess.run(
        ["multica", "issue", "comment", "add", issue_id, "--content-stdin"],
        input=comment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def find_idle_agent(role: str) -> dict | None:
    """找到空闲的 agent (最多同时 2 个 in_progress)。"""
    agents = AGENTS.get(role, [])
    for agent in agents:
        workload = get_agent_workload(agent["id"])
        if workload < 2:
            return agent
    return None


def scan_and_dispatch(dry_run: bool = False):
    """扫描并派发任务。"""
    print(f"\n{'='*60}")
    print(f"  AutoAi Dispatcher — 扫描开始")
    print(f"{'='*60}")

    # 1. 获取当前所有 issue 状态
    todo_issues = get_issues("todo")
    in_progress_issues = get_issues("in_progress")
    in_review_issues = get_issues("in_review")

    print(f"\n  状态统计:")
    print(f"    Todo:       {len(todo_issues)}")
    print(f"    In Progress: {len(in_progress_issues)}")
    print(f"    In Review:   {len(in_review_issues)}")

    # 2. 检查 in_review 的任务 → 标记为 done
    for issue in in_review_issues:
        # 检查是否有运行记录
        issue_id = issue["id"]
        identifier = issue["identifier"]
        title = issue["title"][:40]
        print(f"\n  [REVIEW] {identifier}: {title}")

        # 检查是否有分支推送
        runs_output = run_multica(["issue", "runs", issue_id, "--output", "json"])
        try:
            runs = json.loads(runs_output)
            completed_runs = [r for r in runs if r.get("status") == "completed"]
            if completed_runs and not dry_run:
                run_multica(["issue", "status", issue_id, "done"])
                print(f"    → 标记为 done [OK]")
            elif completed_runs:
                print(f"    → [DRY RUN] 会标记为 done")
        except:
            pass

    # 3. 检查空闲 agent → 派发新任务
    print(f"\n  检查空闲 agent:")

    # 后端 agent
    for role, task_pool, agent_role in [
        ("backend", BACKEND_TASKS, "backend"),
        ("frontend", FRONTEND_TASKS, "frontend"),
        ("tester", TESTER_TASKS, "tester"),
    ]:
        if not task_pool:
            continue

        agent = find_idle_agent(agent_role)
        if not agent:
            print(f"    {role}: 所有 agent 都在忙")
            continue

        # 检查是否还有待派发的任务
        existing_titles = get_existing_titles()
        for task in task_pool:
            # 检查标题是否已存在
            task_keywords = set(task["title"].lower().split())
            if task_keywords & existing_titles:
                continue  # 跳过已存在的任务

            print(f"    → 派发给 {agent['name']}: {task['title'][:40]}")
            if not dry_run:
                issue_id = create_task(
                    task["title"],
                    task["description"],
                    task["priority"],
                    agent["name"],
                )
                if issue_id:
                    trigger_agent(issue_id, agent["id"], agent["name"])
                    print(f"      Issue ID: {issue_id} [OK]")
                    # 从池中移除
                    task_pool.remove(task)
                    break
            else:
                print(f"      [DRY RUN] 不实际创建")

    print(f"\n{'='*60}")
    print(f"  扫描完成")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="AutoAi 任务自动派发器")
    parser.add_argument("--loop", type=int, help="循环间隔 (秒)")
    parser.add_argument("--dry-run", action="store_true", help="只看不干")
    args = parser.parse_args()

    if args.loop:
        print(f"自动派发模式: 每 {args.loop} 秒扫描一次 (Ctrl+C 停止)")
        try:
            while True:
                scan_and_dispatch(dry_run=args.dry_run)
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n停止扫描")
    else:
        scan_and_dispatch(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
