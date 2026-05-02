import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.agents import list_agents, sync_agents_from_roles
from autoai.db import close_db
from autoai.roles import (
    generate_roles,
    role_context_summary,
    roles_for_api,
    save_roles,
    save_roles_from_api,
)


class RoleTests(unittest.TestCase):
    def test_generate_roles_from_project_requirements(self):
        roles = generate_roles(
            "Build a web UI with multi-agent orchestration, permissions, and API keys.",
            "Need dashboard, backend API, role budget, and security review.",
        )
        ids = {role["id"] for role in roles}

        self.assertIn("project-manager", ids)
        self.assertIn("frontend-developer", ids)
        self.assertIn("agent-orchestrator", ids)
        self.assertIn("security-reviewer", ids)

    def test_role_api_key_is_stored_as_secret(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            roles = save_roles(root, generate_roles("Build a web UI", ""))
            roles[0]["model"] = "claude-opus"
            roles[0]["api_key"] = "secret-value"

            payload = save_roles_from_api(root, roles)

            self.assertTrue(payload[0]["has_api_key"])
            self.assertEqual(payload[0]["api_key"], "")
            self.assertIn("claude-opus", role_context_summary(root))
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sync_agents_from_roles_writes_claude_agents(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)
            save_roles(root, generate_roles("Build an agent UI", ""))

            sync_agents_from_roles(root)

            names = {agent["name"] for agent in list_agents(root)}
            self.assertIn("project-manager", names)
            self.assertIn("implementer", names)
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
