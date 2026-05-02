import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.db import close_db
from autoai.project import init_project
from autoai.server import prompt_text, status_payload


class UIServerTests(unittest.TestCase):
    def test_status_payload_for_initialized_project(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build a UI demo.",
                feature_count=7,
                agent_command="more",
                verify_command=None,
                permission_mode="auto",
                init_git=False,
            )

            payload = status_payload(root)

            self.assertTrue(payload["configured"])
            self.assertEqual(payload["goal"], "Build a UI demo.")
            self.assertEqual(payload["permission_mode"], "auto")
            self.assertEqual(payload["collaboration_mode"], "single")
            self.assertEqual(payload["help"]["open"], 0)
            self.assertGreaterEqual(payload["roles"]["total"], 4)
            self.assertEqual(payload["features"]["total"], 0)
            self.assertTrue(payload["first_run_pending"])
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_prompt_endpoint_helper_renders_initializer(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build a UI demo.",
                feature_count=7,
                agent_command="more",
                verify_command=None,
                permission_mode="default",
                init_git=False,
            )

            text = prompt_text(root, "initializer")

            self.assertIn("Initializer Agent", text)
            self.assertIn("Target feature count: `7`", text)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
