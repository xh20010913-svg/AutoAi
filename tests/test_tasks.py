import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.db import close_db
from autoai.tasks import create_task, list_tasks, open_task_summary, update_task_status


class TaskTests(unittest.TestCase):
    def test_create_and_update_task(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            task = create_task(root, "Build queue", priority="high", assignee="implementer")
            updated = update_task_status(root, task["id"], "in_progress")

            self.assertEqual(updated["status"], "in_progress")
            self.assertEqual(list_tasks(root)[0]["title"], "Build queue")
            self.assertIn("Build queue", open_task_summary(root))
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
