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
        self.assertFalse(project.manifest()["live_game_files_touched"])

    def test_furniture_manifest_exports(self):
        with TemporaryDirectory() as folder:
            destination = bed_template().export(Path(folder) / "bed.json")
            self.assertTrue(destination.is_file())


if __name__ == "__main__":
    unittest.main()
