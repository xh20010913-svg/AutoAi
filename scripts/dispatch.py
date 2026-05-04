"""
AutoAi Task Dispatcher v2 — 本地扫描派发器

完全本地化运行，不弹窗、不调 git。
通过本地缓存文件追踪 agent 状态，只在必要时调 multica。

用法:
    python scripts/dispatch.py              # 单次扫描
    python scripts/dispatch.py --loop 120   # 每 120 秒循环
    python scripts/dispatch.py --sync       # 先同步远程状态再派发
    python scripts/dispatch.py --dry-run    # 只看不干
"""

import json
import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# ─── 路径 ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_FILE = SCRIPT_DIR / ".dispatch_cache.json"
STATE_FILE = SCRIPT_DIR / ".dispatch_state.json"

# ─── Agent 配置 ──────────────────────────────────────────────────────────────

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

# ─── 任务池 ──────────────────────────────────────────────────────────────────

TASK_POOL = {
    "backend": [
        {
            "title": "[v0.2] Project CRUD API",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "实现 Project 增删改查 API.\n"
                    "1. Project 模型: name, description, owner_id, status\n"
                    "2. POST/GET/PUT/DELETE /api/v1/projects\n"
                    "3. 测试\n\n"
                    "完成后提交到分支 feat/project-api, 推送, 评论报告.",
            "priority": "high",
        },
        {
            "title": "[v0.2] WebSocket 实时推送",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "实现 WebSocket 端点, 实时推送任务变更.\n"
                    "1. WS /api/v1/ws\n"
                    "2. ConnectionManager\n"
                    "3. 任务变更广播\n\n"
                    "完成后提交到分支 feat/websocket, 推送, 评论报告.",
            "priority": "medium",
        },
        {
            "title": "[v0.3] Agent CRUD API",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "实现 Agent 增删改查 API.\n"
                    "1. Agent 模型: name, role, model, status\n"
                    "2. CRUD 端点\n"
                    "3. 测试\n\n"
                    "完成后提交到分支 feat/agent-api, 推送, 评论报告.",
            "priority": "medium",
        },
        {
            "title": "[v0.3] Provider 配置 API",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "实现模型提供商配置 API.\n"
                    "1. Provider 模型: name, type, base_url, api_key\n"
                    "2. CRUD + 健康检查\n\n"
                    "完成后提交到分支 feat/provider-api, 推送, 评论报告.",
            "priority": "medium",
        },
    ],
    "frontend": [
        {
            "title": "[v0.2] 多语言 i18n 中英文切换",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "实现 i18n: react-i18next, zh.json/en.json, Settings 语言切换器.\n"
                    "所有页面文字翻译, localStorage 持久化.\n\n"
                    "完成后提交到分支 feat/i18n, 推送, 评论报告.",
            "priority": "high",
        },
        {
            "title": "[v0.2] 像素办公室大场景",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "创建像素办公室大场景组件 (详见 AUT-167 详细规格).\n"
                    "参考: rolandal/pixel-agents-standalone, W17ant/Claude-Office\n\n"
                    "完成后提交到分支 feat/pixel-office, 推送, 评论报告.",
            "priority": "high",
        },
        {
            "title": "[v0.3] 前端集成认证 API",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "前端对接 JWT 认证: 登录页/注册页, token 存储, Axios 拦截器.\n\n"
                    "完成后提交到分支 feat/frontend-auth, 推送, 评论报告.",
            "priority": "medium",
        },
        {
            "title": "[v0.3] Board 页面连接真实 API",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "Board 从 API 加载任务, 拖拽更新状态, WebSocket 实时同步.\n\n"
                    "完成后提交到分支 feat/board-api, 推送, 评论报告.",
            "priority": "medium",
        },
    ],
    "tester": [
        {
            "title": "[测试] Auth API 测试",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "测试 JWT 认证: 注册/登录/me, 边界条件, 安全性.\n\n"
                    "完成后提交到分支 test/auth, 推送, 评论报告.",
            "priority": "medium",
        },
        {
            "title": "[测试] Task CRUD 测试",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "测试 Task CRUD 全部端点, 边界条件, 并发.\n\n"
                    "完成后提交到分支 test/task-api, 推送, 评论报告.",
            "priority": "medium",
        },
        {
            "title": "[测试] 前端组件测试",
            "desc": "项目: AutoAi | 仓库: https://github.com/xh20010913-svg/AutoAi\n\n"
                    "Vitest + RTL 测试像素动画/i18n/UI 回归.\n\n"
                    "完成后提交到分支 test/frontend, 推送, 评论报告.",
            "priority": "medium",
        },
    ],
}


def hidden_subprocess(args: list, **kwargs) -> subprocess.CompletedResult:
    """运行子进程，完全隐藏窗口 (Windows 专用)."""
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    return subprocess.run(args, **kwargs)


def load_cache() -> dict:
    """加载本地缓存."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {"issues": [], "last_sync": None, "dispatched": []}


def save_cache(cache: dict):
    """保存本地缓存."""
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_from_multica() -> dict:
    """从 multica 同步 issue 状态到本地缓存 (只调用一次)."""
    cache = load_cache()

    # 只调一次 multica 获取所有 issue
    result = hidden_subprocess(
        ["multica", "issue", "list", "--output", "json", "--limit", "200"]
    )
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            cache["issues"] = data.get("issues", [])
            cache["last_sync"] = datetime.now().isoformat()
            save_cache(cache)
            print(f"  [SYNC] 已同步 {len(cache['issues'])} 个 issues")
        except json.JSONDecodeError:
            print("  [WARN] 同步失败, 使用本地缓存")
    else:
        print("  [WARN] multica 调用失败, 使用本地缓存")

    return cache


def get_agent_status(agent_id: str, issues: list[dict]) -> dict:
    """从本地缓存获取 agent 状态."""
    agent_issues = [i for i in issues if i.get("assignee_id") == agent_id]
    return {
        "todo": len([i for i in agent_issues if i.get("status") == "todo"]),
        "in_progress": len([i for i in agent_issues if i.get("status") == "in_progress"]),
        "in_review": len([i for i in agent_issues if i.get("status") == "in_review"]),
        "done": len([i for i in agent_issues if i.get("status") == "done"]),
    }


def close_reviewed_issues(cache: dict, dry_run: bool) -> int:
    """关闭 in_review 状态的任务."""
    closed = 0
    review_issues = [i for i in cache["issues"] if i.get("status") == "in_review"]

    for issue in review_issues:
        iid = issue["id"]
        ident = issue["identifier"]
        print(f"  [CLOSE] {ident}: {issue['title'][:40]}")

        if not dry_run:
            result = hidden_subprocess(
                ["multica", "issue", "status", iid, "done"]
            )
            if result.returncode == 0:
                issue["status"] = "done"
                closed += 1
                print(f"    -> done")
        else:
            print(f"    -> [DRY] would close")

    return closed


def dispatch_to_agent(agent: dict, task: dict, dry_run: bool) -> bool:
    """派发任务给单个 agent."""
    if dry_run:
        print(f"    [DRY] -> {agent['name']}: {task['title'][:40]}")
        return True

    # 创建 issue
    result = hidden_subprocess(
        ["multica", "issue", "create",
         "--title", task["title"],
         "--priority", task["priority"],
         "--assignee", agent["name"],
         "--status", "todo",
         "--description-stdin"],
        input=task["desc"],
    )
    if result.returncode != 0:
        print(f"    [FAIL] 创建 issue 失败: {result.stderr[:100]}")
        return False

    try:
        data = json.loads(result.stdout)
        issue_id = data.get("id", "")
    except:
        print(f"    [FAIL] 解析响应失败")
        return False

    if not issue_id:
        return False

    # 触发 agent
    comment = f"[@{agent['name']}](mention://agent/{agent['id']}) 请开始执行。完成后推送分支并评论报告。"
    hidden_subprocess(
        ["multica", "issue", "comment", "add", issue_id, "--content-stdin"],
        input=comment,
    )

    print(f"    [OK] -> {agent['name']}: {task['title'][:40]} (ID: {issue_id[:8]}...)")
    return True


def scan_and_dispatch(sync: bool = False, dry_run: bool = False):
    """主扫描逻辑."""
    print(f"\n{'='*50}")
    print(f"  AutoAi Dispatcher v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # 获取状态 (优先本地缓存)
    if sync:
        cache = sync_from_multica()
    else:
        cache = load_cache()
        if cache["last_sync"]:
            print(f"  使用本地缓存 (同步于: {cache['last_sync'][:19]})")
        else:
            cache = sync_from_multica()

    issues = cache.get("issues", [])

    # 统计
    by_status = {}
    for i in issues:
        s = i.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    print(f"\n  Issues: {json.dumps(by_status, ensure_ascii=False)}")

    # 关闭 in_review
    closed = close_reviewed_issues(cache, dry_run)
    if closed:
        save_cache(cache)

    # 并行派发 — 所有空闲 agent 都拿到任务
    print(f"\n  派发任务:")
    dispatched = 0

    for role, tasks in TASK_POOL.items():
        if not tasks:
            continue

        agents = AGENTS.get(role, [])
        for agent in agents:
            status = get_agent_status(agent["id"], issues if not closed else cache["issues"])

            # 空闲判断: in_progress < 3 (提高上限，多派任务)
            if status["in_progress"] >= 3:
                print(f"  {agent['name']}: 忙碌 ({status['in_progress']} in_progress)")
                continue

            # 找一个还没派的任务
            dispatched_titles = set(cache.get("dispatched", []))
            for task in tasks[:]:
                if task["title"] in dispatched_titles:
                    continue

                if dispatch_to_agent(agent, task, dry_run):
                    dispatched += 1
                    cache.setdefault("dispatched", []).append(task["title"])
                    tasks.remove(task)
                    save_cache(cache)
                    break

    print(f"\n  本次派发: {dispatched} 个任务")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="AutoAi 任务自动派发器 v2")
    parser.add_argument("--loop", type=int, default=0, help="循环间隔 (秒)")
    parser.add_argument("--sync", action="store_true", help="先从 multica 同步状态")
    parser.add_argument("--dry-run", action="store_true", help="只看不干")
    parser.add_argument("--reset", action="store_true", help="清除缓存重新开始")
    args = parser.parse_args()

    if args.reset:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        print("缓存已清除")

    if args.loop > 0:
        print(f"自动派发: 每 {args.loop} 秒扫描 (Ctrl+C 停止)")
        try:
            while True:
                scan_and_dispatch(sync=args.sync, dry_run=args.dry_run)
                time.sleep(args.loop)
        except KeyboardInterrupt:
            print("\n停止")
    else:
        scan_and_dispatch(sync=args.sync, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
