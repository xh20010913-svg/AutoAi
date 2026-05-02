import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.config import load_config
from autoai.constants import PROGRESS_FILE, SPEC_FILE
from autoai.db import close_db, ensure_db, get_session
from autoai.models import Role
from autoai.project import init_project


class ProjectInitTests(unittest.TestCase):
    def test_init_project_creates_control_files(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            init_project(
                project_dir=root,
                goal="Build a durable demo.",
                feature_count=12,
                agent_command="echo ok",
                verify_command=None,
                permission_mode="default",
                init_git=False,
            )

            self.assertTrue((root / SPEC_FILE).exists())
            self.assertTrue((root / PROGRESS_FILE).exists())
            self.assertTrue((root / ".autoai" / "autoai.db").exists())

            config = load_config(root)
            self.assertEqual(config.feature_count, 12)
            self.assertEqual(config.agent_command, "echo ok")
            self.assertEqual(config.collaboration_mode, "single")

            ensure_db(root)
            with get_session() as session:
                self.assertGreater(session.query(Role).count(), 0)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
