import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.db import close_db
from autoai.harness import AutoAIHarness, HarnessOptions
from autoai.help_requests import create_help_request
from autoai.project import init_project
from autoai.state import load_state


class HarnessTests(unittest.TestCase):
    def test_initializer_without_feature_list_is_failed(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build a demo.",
                feature_count=5,
                agent_command="more",
                verify_command=None,
                permission_mode="default",
                init_git=False,
            )

            code = AutoAIHarness(
                root,
                HarnessOptions(max_iterations=1, stop_on_error=True),
            ).run()

            self.assertNotEqual(code, 0)
            state = load_state(root)
            self.assertEqual(state.last_status, "failed")
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_open_help_request_pauses_before_running_agent(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build a demo.",
                feature_count=5,
                agent_command="more",
                verify_command=None,
                permission_mode="default",
                init_git=False,
            )
            create_help_request(root, "Need confirmation")

            code = AutoAIHarness(
                root,
                HarnessOptions(max_iterations=1, stop_on_error=True),
            ).run()

            self.assertEqual(code, 2)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
