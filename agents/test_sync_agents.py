"""The sync replaces only the managed block and refuses to guess where it goes.

Run: python3 -m unittest discover agents
"""

import unittest

from sync_agents import sync

GUIDE = ("# Guide\n\nLocal intro.\n\n<!-- FIDES:BEGIN version=0.3. old -->\n"
         "old rules\n<!-- FIDES:END -->\n\nLocal notes.\n")


class SyncTest(unittest.TestCase):
    def test_replaces_the_block_and_keeps_everything_else(self) -> None:
        result = sync("new rules\n", GUIDE, "v0.4")
        self.assertIn("<!-- FIDES:BEGIN version=v0.4.", result)
        self.assertIn("\nnew rules\n<!-- FIDES:END -->", result)
        self.assertNotIn("old rules", result)
        self.assertTrue(result.startswith("# Guide\n\nLocal intro.\n\n"))
        self.assertTrue(result.endswith("\n\nLocal notes.\n"))

    def test_empty_markers_are_filled(self) -> None:
        result = sync("rules", "<!-- FIDES:BEGIN -->\n<!-- FIDES:END -->\n", "v0.4")
        self.assertIn("\nrules\n<!-- FIDES:END -->", result)

    def test_same_version_and_rules_change_nothing(self) -> None:
        once = sync("rules", GUIDE, "v0.4")
        self.assertEqual(sync("rules", once, "v0.4"), once)

    def test_a_guide_without_markers_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            sync("rules", "# Guide\n", "v0.4")

    def test_two_blocks_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            sync("rules", GUIDE + GUIDE, "v0.4")


if __name__ == "__main__":
    unittest.main()
