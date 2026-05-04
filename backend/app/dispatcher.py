"""
AutoAi Dispatcher — 自动任务分配引擎

从 .autoai/task_graph.json 读取任务列表，
从 .autoai/roles.json 读取角色配置，
按依赖关系和角色负载选择下一个可执行任务。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TaskNode:
    id: str
    title: str
    status: str = "todo"
    suggested_role: str = ""
    dependencies: list[str] = field(default_factory=list)
    priority: str = "medium"

    @classmethod
    def from_dict(cls, d: dict) -> "TaskNode":
        return cls(
            id=d["id"],
            title=d.get("title", ""),
            status=d.get("status", "todo"),
            suggested_role=d.get("suggested_role", ""),
            dependencies=d.get("dependencies", []),
            priority=d.get("priority", "medium"),
        )


@dataclass
class RoleConfig:
    name: str
    max_concurrent: int = 3
    skills: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "RoleConfig":
        return cls(
            name=d["name"],
            max_concurrent=d.get("max_concurrent", 3),
            skills=d.get("skills", []),
        )


class Dispatcher:
    """任务调度器：从 task graph 中选出下一个可执行任务并分配角色。"""

    def __init__(
        self,
        task_graph_path: str | Path = ".autoai/task_graph.json",
        roles_path: str | Path = ".autoai/roles.json",
    ):
        self._task_graph_path = Path(task_graph_path)
        self._roles_path = Path(roles_path)
        self._tasks: dict[str, TaskNode] = {}
        self._roles: dict[str, RoleConfig] = {}

    def load(self) -> "Dispatcher":
        """加载 task graph 和角色配置。"""
        if self._task_graph_path.exists():
            raw = json.loads(self._task_graph_path.read_text(encoding="utf-8"))
            tasks_list = raw if isinstance(raw, list) else raw.get("tasks", [])
            for t in tasks_list:
                node = TaskNode.from_dict(t)
                self._tasks[node.id] = node

        if self._roles_path.exists():
            raw = json.loads(self._roles_path.read_text(encoding="utf-8"))
            roles_list = raw if isinstance(raw, list) else raw.get("roles", [])
            for r in roles_list:
                role = RoleConfig.from_dict(r)
                self._roles[role.name] = role

        return self

    @property
    def tasks(self) -> dict[str, TaskNode]:
        return self._tasks

    @property
    def roles(self) -> dict[str, RoleConfig]:
        return self._roles

    def set_tasks(self, tasks: list[dict]) -> "Dispatcher":
        """Programmatically set tasks (for testing)."""
        self._tasks = {}
        for t in tasks:
            node = TaskNode.from_dict(t)
            self._tasks[node.id] = node
        return self

    def set_roles(self, roles: list[dict]) -> "Dispatcher":
        """Programmatically set roles (for testing)."""
        self._roles = {}
        for r in roles:
            role = RoleConfig.from_dict(r)
            self._roles[role.name] = role
        return self

    def get_ready_tasks(self) -> list[TaskNode]:
        """返回所有依赖已满足、状态为 todo 的任务。"""
        done_ids = {tid for tid, t in self._tasks.items() if t.status == "done"}
        ready = []
        for task in self._tasks.values():
            if task.status != "todo":
                continue
            if all(dep in done_ids for dep in task.dependencies):
                ready.append(task)
        return ready

    def _role_load(self, role_name: str) -> int:
        """统计角色当前正在执行的任务数。"""
        return sum(
            1
            for t in self._tasks.values()
            if t.status == "in_progress" and t.suggested_role == role_name
        )

    def _can_assign(self, role_name: str) -> bool:
        """检查角色是否还有容量接收新任务。"""
        role = self._roles.get(role_name)
        if not role:
            return True  # 无配置的角色不限制
        return self._role_load(role_name) < role.max_concurrent

    def dispatch_one(self, role: str | None = None) -> dict | None:
        """
        选择下一个任务并分配角色。

        Args:
            role: 可选，指定只调度该角色的任务。

        Returns:
            dict with keys: task_id, title, assigned_role, priority
            or None if no task is available.
        """
        ready = self.get_ready_tasks()

        if role:
            ready = [t for t in ready if t.suggested_role == role]

        # 按 priority 排序: high > medium > low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        ready.sort(key=lambda t: priority_order.get(t.priority, 1))

        for task in ready:
            if task.suggested_role and not self._can_assign(task.suggested_role):
                continue
            return {
                "task_id": task.id,
                "title": task.title,
                "assigned_role": task.suggested_role,
                "priority": task.priority,
            }

        return None

    def dispatch_batch(self, max_count: int | None = None) -> list[dict]:
        """
        连续调度多个任务，直到没有可用任务或达到 max_count。

        Returns:
            list of dispatch results.
        """
        results = []
        dispatched_ids: set[str] = set()

        while True:
            if max_count is not None and len(results) >= max_count:
                break

            # 临时标记已派发的任务为 in_progress 以正确计算负载
            for r in results:
                tid = r["task_id"]
                if tid in self._tasks:
                    self._tasks[tid].status = "in_progress"

            result = self.dispatch_one()
            # 回滚临时状态
            for r in results:
                tid = r["task_id"]
                if tid in self._tasks and tid not in dispatched_ids:
                    self._tasks[tid].status = "todo"

            if not result:
                break

            results.append(result)
            dispatched_ids.add(result["task_id"])

        return results

    def dispatch_by_role(self, role_name: str) -> list[dict]:
        """调度指定角色的所有可用任务。"""
        return self.dispatch_batch_for_role(role_name)

    def dispatch_batch_for_role(self, role_name: str) -> list[dict]:
        """调度指定角色的所有可用任务。"""
        results = []
        while True:
            for r in results:
                tid = r["task_id"]
                if tid in self._tasks:
                    self._tasks[tid].status = "in_progress"

            result = self.dispatch_one(role=role_name)

            for r in results:
                tid = r["task_id"]
                if tid in self._tasks:
                    self._tasks[tid].status = "todo"

            if not result:
                break
            results.append(result)
        return results

    def mark_done(self, task_id: str) -> bool:
        """将任务标记为 done。"""
        if task_id in self._tasks:
            self._tasks[task_id].status = "done"
            return True
        return False

    def mark_in_progress(self, task_id: str) -> bool:
        """将任务标记为 in_progress。"""
        if task_id in self._tasks:
            self._tasks[task_id].status = "in_progress"
            return True
        return False

    def get_blocked_tasks(self) -> list[TaskNode]:
        """返回依赖未满足的任务。"""
        done_ids = {tid for tid, t in self._tasks.items() if t.status == "done"}
        return [
            t
            for t in self._tasks.values()
            if t.status == "todo" and not all(dep in done_ids for dep in t.dependencies)
        ]

    def get_task_graph_summary(self) -> dict:
        """返回任务图的摘要统计。"""
        by_status: dict[str, int] = {}
        for t in self._tasks.values():
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "total": len(self._tasks),
            "by_status": by_status,
            "ready": len(self.get_ready_tasks()),
            "blocked": len(self.get_blocked_tasks()),
            "roles": list(self._roles.keys()),
        }
