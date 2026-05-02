import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.constants import SPEC_FILE
from autoai.db import close_db
from autoai.project import init_project


class SpecUploadTests(unittest.TestCase):
    def test_uploaded_markdown_becomes_task_spec(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Uploaded project",
                feature_count=5,
                agent_command=None,
                verify_command=None,
                permission_mode="default",
                init_git=False,
                spec_text="# Detailed Requirements\n\nBuild the thing carefully.",
                spec_filename="requirements.md",
            )

            text = (root / SPEC_FILE).read_text(encoding="utf-8")

            self.assertIn("requirements.md", text)
            self.assertIn("Detailed Requirements", text)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
