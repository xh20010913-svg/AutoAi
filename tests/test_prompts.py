import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.config import load_config
from autoai.db import close_db
from autoai.project import init_project
from autoai.prompts import render_prompt


class PromptTests(unittest.TestCase):
    def test_initializer_prompt_renders_without_placeholders(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build something useful.",
                feature_count=20,
                agent_command=None,
                verify_command=None,
                permission_mode="default",
                init_git=False,
            )
            prompt = render_prompt("initializer", root, load_config(root))
            self.assertIn("Initializer Agent", prompt)
            self.assertIn("Collaboration", prompt)
            self.assertIn("Role Policy", prompt)
            self.assertIn("Task Queue", prompt)
            self.assertIn("Human Help", prompt)
            self.assertNotIn("{{", prompt)
            self.assertNotIn("}}", prompt)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
