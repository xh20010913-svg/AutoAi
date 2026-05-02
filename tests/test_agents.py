import tempfile
import unittest
from pathlib import Path

from autoai.agents import install_default_agents, list_agents
from autoai.constants import claude_agents_dir


class AgentTests(unittest.TestCase):
    def test_install_default_agents_writes_project_subagents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            agents = install_default_agents(root)

            self.assertGreaterEqual(len(agents), 5)
            self.assertTrue((claude_agents_dir(root) / "team-lead.md").exists())
            names = {agent["name"] for agent in list_agents(root)}
            self.assertIn("team-lead", names)
            self.assertIn("implementer", names)


if __name__ == "__main__":
    unittest.main()
