import tempfile
import unittest
from pathlib import Path

from autoai.claude_settings import claude_settings_status, set_skip_dangerous_mode_prompt


class ClaudeSettingsTests(unittest.TestCase):
    def test_can_enable_skip_dangerous_mode_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            status = set_skip_dangerous_mode_prompt(True, home=home)

            self.assertTrue(status["skipDangerousModePermissionPrompt"])
            self.assertTrue((home / ".claude" / "settings.json").exists())

            loaded = claude_settings_status(home=home)
            self.assertTrue(loaded["skipDangerousModePermissionPrompt"])


if __name__ == "__main__":
    unittest.main()
