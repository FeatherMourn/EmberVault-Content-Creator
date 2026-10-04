import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from embervault_sdk import ModuleContext
from src.module import validate_design
from src.content import bed_template


class ContentCreatorTests(unittest.TestCase):
    def test_furniture_design_is_design_only(self):
        result = validate_design(ModuleContext("embervault.content-creator", "research", "EV-OP-1"),
                                 "furniture", ["assets/chair.png"])
        self.assertEqual(result.status, "ready")
        self.assertFalse(result.data["touches_live_game"])

    def test_asset_escape_is_blocked(self):
        result = validate_design(ModuleContext("embervault.content-creator", "research", "EV-OP-2"),
                                 "furniture", ["../outside.png"])
        self.assertEqual(result.status, "blocked")

    def test_bed_template_is_a_design_only_furniture_project(self):
        project = bed_template()
        self.assertEqual(project.category, "bed")
        self.assertEqual(project.source_template, "tested-bed-workflow")
        self.assertEqual(project.donor_item_id, 2940001508)
        self.assertEqual(project.donor_recipe_id, 3531872774)
        self.assertEqual(project.verification["registration"], "verified")
        self.assertEqual(project.verification["visuals"], "unverified")
        self.assertEqual(len(project.evidence), 1)
        self.assertFalse(project.manifest()["live_game_files_touched"])
        self.assertEqual(project.manifest()["schema_id"], "https://embervault.dev/contracts/content-project-export.schema.json")

    def test_furniture_manifest_exports(self):
        with TemporaryDirectory() as folder:
            destination = bed_template().export(Path(folder) / "bed.json")
            self.assertTrue(destination.is_file())

    def test_project_save_and_load_preserves_identity_and_design_data(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "project.json"
            project = bed_template()
            project.save(source)
            loaded = project.load(source)
            self.assertEqual(loaded.project_id, project.project_id)
            self.assertEqual(loaded.donor_recipe_id, project.donor_recipe_id)
            self.assertEqual(loaded.verification, project.verification)

    def test_project_load_rejects_unknown_version(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "project.json"
            source.write_text(json.dumps({"project_schema_version": 99}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                bed_template().load(source)


if __name__ == "__main__":
    unittest.main()
