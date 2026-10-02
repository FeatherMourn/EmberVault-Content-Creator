import unittest

from embervault_sdk import ModuleContext
from src.module import validate_design


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


if __name__ == "__main__":
    unittest.main()
