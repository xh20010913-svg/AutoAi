import json
import tempfile
import unittest
from pathlib import Path

from autoai.constants import FEATURE_FILE
from autoai.features import lock_feature_baseline, validate_feature_invariants


class FeatureInvariantTests(unittest.TestCase):
    def test_passes_change_is_allowed_after_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            features = [
                {
                    "id": "F001",
                    "priority": 1,
                    "category": "functional",
                    "description": "First feature",
                    "steps": ["Do it", "Check it"],
                    "passes": False,
                }
            ]
            (root / FEATURE_FILE).write_text(json.dumps(features), encoding="utf-8")
            self.assertTrue(lock_feature_baseline(root))

            features[0]["passes"] = True
            (root / FEATURE_FILE).write_text(json.dumps(features), encoding="utf-8")

            result = validate_feature_invariants(root)
            self.assertTrue(result.ok, result.messages)

    def test_description_change_is_rejected_after_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            features = [
                {
                    "id": "F001",
                    "priority": 1,
                    "category": "functional",
                    "description": "First feature",
                    "steps": ["Do it", "Check it"],
                    "passes": False,
                }
            ]
            (root / FEATURE_FILE).write_text(json.dumps(features), encoding="utf-8")
            self.assertTrue(lock_feature_baseline(root))

            features[0]["description"] = "Edited feature"
            (root / FEATURE_FILE).write_text(json.dumps(features), encoding="utf-8")

            result = validate_feature_invariants(root)
            self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
