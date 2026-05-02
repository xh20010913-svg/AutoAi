import shutil
import tempfile
import unittest
from pathlib import Path

from autoai.db import close_db
from autoai.help_requests import (
    answer_help_request,
    close_help_request,
    create_help_request,
    help_context_summary,
    list_help_requests,
    open_help_requests,
)


class HelpRequestTests(unittest.TestCase):
    def test_create_answer_and_close_help_request(self):
        tmp = tempfile.mkdtemp()
        try:
            root = Path(tmp)

            request = create_help_request(root, "Need login", detail="Please log into GitHub.")
            self.assertEqual(len(open_help_requests(root)), 1)

            answered = answer_help_request(root, request["id"], "Logged in.")
            self.assertEqual(answered["status"], "answered")
            self.assertEqual(open_help_requests(root), [])
            self.assertIn("Logged in.", help_context_summary(root))

            closed = close_help_request(root, request["id"])
            self.assertEqual(closed["status"], "closed")
            self.assertEqual(list_help_requests(root)[0]["status"], "closed")
        finally:
            close_db()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
