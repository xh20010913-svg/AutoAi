import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.db import close_db
from autoai.dispatcher import (
    assign_task,
    load_task_graph,
    save_task_graph,
    select_next_task,
)
from autoai.roles import save_roles
from autoai.tasks import create_task


def _make_graph():
    """Return a sample task graph with dependencies."""
    return [
        {
            "id": "T-001",
            "title": "Design schema",
            "status": "done",
            "priority": "high",
            "suggested_role": "backend-developer",
            "depends_on": [],
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": "T-002",
            "title": "Implement API",
            "status": "todo",
            "priority": "high",
            "suggested_role": "backend-developer",
            "depends_on": ["T-001"],
            "created_at": "2026-01-01T00:01:00Z",
        },
        {
            "id": "T-003",
            "title": "Build UI",
            "status": "todo",
            "priority": "medium",
            "suggested_role": "frontend-developer",
            "depends_on": ["T-002"],
            "created_at": "2026-01-01T00:02:00Z",
        },
        {
            "id": "T-004",
            "title": "Write docs",
            "status": "todo",
            "priority": "low",
            "suggested_role": "implementer",
            "depends_on": [],
            "created_at": "2026-01-01T00:03:00Z",
        },
    ]


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp)

    def tearDown(self):
        close_db()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- select_next_task ---------------------------------------------------

    def test_selects_task_with_satisfied_deps(self):
        graph = _make_graph()
        result = select_next_task(self.root, task_graph=graph)
        self.assertIsNotNone(result)
        # T-002 has priority high and deps satisfied (T-001 is done)
        self.assertEqual(result["id"], "T-002")

    def test_skips_tasks_with_unsatisfied_deps(self):
        graph = _make_graph()
        graph[0]["status"] = "todo"  # T-001 no longer done
        result = select_next_task(self.root, task_graph=graph)
        # T-001 has no deps and is todo → highest priority candidate
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "T-001")
        # T-002 depends on T-001 which is no longer done, so it should NOT be selected
        all_results = []
        remaining = [t for t in graph if t["id"] != result["id"]]
        # drain candidates
        while True:
            pick = select_next_task(self.root, task_graph=remaining)
            if pick is None:
                break
            all_results.append(pick["id"])
            for t in remaining:
                if t["id"] == pick["id"]:
                    t["status"] = "done"
        # T-002 should never appear before T-001 is done
        self.assertNotIn("T-002", all_results[:1])

    def test_returns_none_when_no_candidates(self):
        graph = _make_graph()
        for t in graph:
            t["status"] = "done"
        result = select_next_task(self.root, task_graph=graph)
        self.assertIsNone(result)

    def test_priority_ordering(self):
        graph = [
            {"id": "A", "title": "low", "status": "todo", "priority": "low", "depends_on": [], "created_at": "2026-01-01T00:00:00Z"},
            {"id": "B", "title": "urgent", "status": "todo", "priority": "urgent", "depends_on": [], "created_at": "2026-01-01T00:01:00Z"},
            {"id": "C", "title": "high", "status": "todo", "priority": "high", "depends_on": [], "created_at": "2026-01-01T00:02:00Z"},
        ]
        result = select_next_task(self.root, task_graph=graph)
        self.assertEqual(result["id"], "B")

    def test_loads_graph_from_disk(self):
        graph = _make_graph()
        save_task_graph(self.root, graph)
        result = select_next_task(self.root)
        self.assertEqual(result["id"], "T-002")

    def test_accepts_dict_wrapped_graph(self):
        graph = {"tasks": _make_graph()}
        result = select_next_task(self.root, task_graph=graph)
        self.assertEqual(result["id"], "T-002")

    # -- assign_task --------------------------------------------------------

    def test_assign_updates_graph_and_db(self):
        graph = _make_graph()
        save_task_graph(self.root, graph)
        # Create matching DB task
        create_task(self.root, "Implement API", assignee="", status="todo")
        # Get the auto-generated task id
        from autoai.tasks import list_tasks
        db_tasks = list_tasks(self.root)
        db_tid = db_tasks[0]["id"]

        # Use the graph task id for assignment
        ok = assign_task(self.root, "T-002", "backend-developer")
        self.assertTrue(ok)

        # Verify graph updated
        updated_graph = load_task_graph(self.root)
        t002 = next(t for t in updated_graph if t["id"] == "T-002")
        self.assertEqual(t002["suggested_role"], "backend-developer")
        self.assertEqual(t002["status"], "in_progress")

    def test_assign_returns_false_for_missing_task(self):
        graph = _make_graph()
        ok = assign_task(self.root, "T-999", "nobody")
        self.assertFalse(ok)

    # -- integration: next after assign -------------------------------------

    def test_next_skips_in_progress(self):
        graph = _make_graph()
        save_task_graph(self.root, graph)
        assign_task(self.root, "T-002", "backend-developer")
        result = select_next_task(self.root)
        # T-002 is now in_progress; next should be T-004 (independent todo)
        self.assertEqual(result["id"], "T-004")


if __name__ == "__main__":
    unittest.main()
