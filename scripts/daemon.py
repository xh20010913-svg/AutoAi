"""
AutoAi 后台守护进程
用 pythonw 运行，完全无窗口，持续循环派发任务。

启动: pythonw scripts/daemon.py
停止: 删除 scripts\.daemon_stop 文件
状态: 查看 scripts\.daemon_status.json
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
STATUS_FILE = SCRIPT_DIR / ".daemon_status.json"
STOP_FILE = SCRIPT_DIR / ".daemon_stop"
CACHE_FILE = SCRIPT_DIR / ".dispatch_cache.json"
PID_FILE = SCRIPT_DIR / ".daemon_pid"

INTERVAL = 120  # 秒


def hidden_run(args: list, **kwargs):
    """隐藏窗口运行子进程."""
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    return subprocess.run(args, **kwargs)


def write_status(running: bool, last_run: str, dispatched: int, errors: list):
    """写状态文件，供前端或用户查看."""
    STATUS_FILE.write_text(json.dumps({
        "running": running,
        "pid": os.getpid(),
        "last_run": last_run,
        "total_dispatched": dispatched,
        "errors": errors[-5:],
        "interval_seconds": INTERVAL,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_issues() -> list:
    """同步 issue 列表."""
    result = hidden_run(["multica", "issue", "list", "--output", "json", "--limit", "200"])
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            issues = data.get("issues", [])
            # 同时保存到本地缓存
            CACHE_FILE.write_text(json.dumps({
                "issues": issues,
                "last_sync": datetime.now().isoformat()
            }, ensure_ascii=False), encoding="utf-8")
            return issues
        except:
            pass
    # 同步失败，用本地缓存
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8")).get("issues", [])
        except:
            pass
    return []


def close_reviewed(issues: list) -> list:
    """关闭 in_review 的任务."""
    for issue in issues:
        if issue.get("status") == "in_review":
            hidden_run(["multica", "issue", "status", issue["id"], "done"])
            issue["status"] = "done"
    return issues


def get_agent_workload(agent_id: str, issues: list) -> int:
    return len([i for i in issues if i.get("assignee_id") == agent_id and i.get("status") in ("todo", "in_progress")])


def dispatch_one(agent: dict, title: str, desc: str, priority: str) -> bool:
    """给一个 agent 派一个任务."""
    result = hidden_run(
        ["multica", "issue", "create",
         "--title", title,
         "--priority", priority,
         "--assignee", agent["name"],
         "--status", "todo",
         "--description-stdin"],
        input=desc,
    )
    if result.returncode != 0:
        return False
    try:
        issue_id = json.loads(result.stdout).get("id", "")
    except:
        return False
    if not issue_id:
        return False
    comment = f"[@{agent['name']}](mention://agent/{agent['id']}) 请开始执行。"
    hidden_run(
        ["multica", "issue", "comment", "add", issue_id, "--content-stdin"],
        input=comment,
    )
    return True


# 任务池
TASKS = {
    "backend": [
        ("[v0.2] Project CRUD API",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n实现 Project 增删改查。\n完成后提交 feat/project-api, 推送, 评论。",
         "high"),
        ("[v0.2] WebSocket 实时推送",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n实现 WS 端点推送任务变更。\n完成后提交 feat/websocket, 推送, 评论。",
         "medium"),
        ("[v0.3] Agent CRUD API",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n实现 Agent 增删改查。\n完成后提交 feat/agent-api, 推送, 评论。",
         "medium"),
    ],
    "frontend": [
        ("[v0.2] 多语言 i18n",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\nreact-i18next 中英文切换。\n完成后提交 feat/i18n, 推送, 评论。",
         "high"),
        ("[v0.2] 像素办公室场景",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\nCanvas 2D 像素办公室，办公区+休息区+小黑板+行走动画。\n参考 rolandal/pixel-agents-standalone。\n完成后提交 feat/pixel-office, 推送, 评论。",
         "high"),
        ("[v0.3] 前端集成认证",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n登录页/注册页, JWT token, Axios 拦截器。\n完成后提交 feat/frontend-auth, 推送, 评论。",
         "medium"),
    ],
    "tester": [
        ("[测试] Auth API 测试",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\nJWT 认证测试。\n完成后提交 test/auth, 推送, 评论。",
         "medium"),
        ("[测试] Task CRUD 测试",
         "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\nTask API 全覆盖测试。\n完成后提交 test/task-api, 推送, 评论。",
         "medium"),
    ],
}

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


def run_cycle():
    """一轮扫描+派发."""
    errors = []
    dispatched_total = 0

    # 1. 同步
    issues = sync_issues()

    # 2. 关闭 in_review
    issues = close_reviewed(issues)

    # 3. 派发
    for role, agents in AGENTS.items():
        tasks = TASKS.get(role, [])
        if not tasks:
            continue
        for agent in agents:
            workload = get_agent_workload(agent["id"], issues)
            if workload >= 3:
                continue
            # 找一个没派过的任务
            for i, (title, desc, pri) in enumerate(tasks):
                # 检查是否已存在
                if any(title.lower() in existing.get("title", "").lower() for existing in issues):
                    continue
                if dispatch_one(agent, title, desc, pri):
                    dispatched_total += 1
                    tasks.pop(i)
                    break

    return dispatched_total, errors


def main():
    # 写 PID 文件
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    # 删除旧的 stop 文件
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    total = 0
    cycle = 0

    while True:
        # 检查 stop 信号
        if STOP_FILE.exists():
            STOP_FILE.unlink()
            write_status(False, datetime.now().isoformat(), total, ["手动停止"])
            break

        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")

        try:
            n, errs = run_cycle()
            total += n
            write_status(True, datetime.now().isoformat(), total, errs)
        except Exception as e:
            write_status(True, datetime.now().isoformat(), total, [str(e)])

        # 等待下一轮
        time.sleep(INTERVAL)

    # 清理
    if PID_FILE.exists():
        PID_FILE.unlink()


if __name__ == "__main__":
    main()
