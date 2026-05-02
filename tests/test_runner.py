import unittest

from autoai.runner import apply_permission_mode


class RunnerPermissionModeTests(unittest.TestCase):
    def test_injects_auto_mode_after_claude_binary(self):
        command = apply_permission_mode("claude -p", "auto")
        self.assertEqual(command, "claude --permission-mode auto -p")

    def test_injects_bypass_mode_after_claude_binary(self):
        command = apply_permission_mode("claude -p", "bypassPermissions")
        self.assertEqual(command, "claude --dangerously-skip-permissions -p")

    def test_does_not_duplicate_existing_permission_flags(self):
        command = apply_permission_mode("claude --permission-mode auto -p", "bypassPermissions")
        self.assertEqual(command, "claude --permission-mode auto -p")


if __name__ == "__main__":
    unittest.main()
