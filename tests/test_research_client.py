import json
import tempfile
import unittest
from pathlib import Path

from src.research_client import load_research_handoff, search_research_handoff


class ResearchClientTests(unittest.TestCase):
    def test_loads_design_only_research_handoff(self):
        payload = {
            "schema_version": 1,
            "application_state": "design-only",
            "live_game_files_touched": False,
            "records": [{"id": "donor-1", "kind": "donor-item", "identity": {"item_id": "1"}}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "handoff.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            records = load_research_handoff(path)
        self.assertEqual(search_research_handoff(records, "donor")[0]["id"], "donor-1")

    def test_rejects_runtime_touching_handoff(self):
        payload = {"schema_version": 1, "application_state": "runtime", "live_game_files_touched": True, "records": []}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_research_handoff(path)


if __name__ == "__main__":
    unittest.main()
