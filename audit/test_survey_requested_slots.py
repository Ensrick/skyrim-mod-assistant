"""Offline parser checks: no networking, game files, or profile writes."""
import unittest
from survey_requested_slots import match_rows, main_mods, normalize_folder, census_markdown


class SurveyRowsTest(unittest.TestCase):
    def test_folder_states_and_separators(self):
        hits, inventory = match_rows([{"clean_name": "modlist.txt", "content": [
            "# High Poly Project", "+High Poly Project_separator", "+High Poly Project",
            "-Convenient Horses", "+Convenient Horses - Patch", "*Animation Queue Fix"]}])
        self.assertEqual([hit["state"] for hit in hits], ["enabled", "disabled", "enabled", "unmanaged"])
        self.assertEqual(hits[0]["line"], 3)
        self.assertEqual(inventory[0]["lines"], 6)
        self.assertEqual(len(hits), 4)  # Patch remains evidence, never automatic main adoption.

    def test_plugins_do_not_inherit_mo2_states(self):
        hits, _ = match_rows([
            {"clean_name": "plugins.txt", "content": "*Ars Metallica.esp\nConvenient Horses.esp"},
            {"clean_name": "loadorder.txt", "content": ["Convenient Horses.esp"]}])
        self.assertEqual([hit["state"] for hit in hits], ["enabled", "unmarked", "ordered-not-proof-enabled"])

    def test_unrelated_hpp_source_and_empty_export(self):
        hits, _ = match_rows([{"clean_name": "modlist.txt", "content": ["+source.hpp", "+Horse Armor"]}])
        self.assertEqual(hits, [])
        self.assertEqual(match_rows([]), ([], []))

    def test_bad_content_fails_closed(self):
        with self.assertRaises(ValueError):
            match_rows([{"clean_name": "modlist.txt", "content": [None]}])

    def test_main_aliases_do_not_count_patches(self):
        hits, _ = match_rows([{"clean_name": "modlist.txt", "content": [
            "+High Poly Project", "+High Poly Project(Less poly coal)",
            "+MIC - Embers XD Patch", "+Icy Windhelm - Mesh Improvement Compilation",
            "+Vigilant - Book Covers", "-Convenient Horses", "+1 Simplest Horses 54225"]}])
        found = main_mods({"matches": hits})
        self.assertEqual(len(found["HPP"]), 1)
        self.assertEqual(len(found["SH"]), 1)
        for key in ("MIC", "BCS", "CH"):
            self.assertEqual(found[key], [])
        self.assertEqual(normalize_folder("+34 Animation Queue Fix 82395"), "animation queue fix")

    def test_bundled_books_require_base_not_lotd_patch(self):
        hits, _ = match_rows([{"clean_name": "modlist.txt", "content": [
            "+1 Legacy of the Dragonborn v6 11802", "+Legacy of the Dragonborn Patches (Official)",
            "+Horse-Slaying Saber - Legacy of the Dragonborn LOTD"]}])
        found = main_mods({"matches": hits})
        self.assertEqual(len(found["LOTD"]), 1)
        self.assertEqual(found["BCS"], [])

    def test_census_null_author_and_excluded_exports(self):
        hits, files = match_rows([{"clean_name": "modlist.txt", "content": [
            "+Animation Queue Fix", "+Book Covers Skyrim", "+Legacy of the Dragonborn"]}])
        base = dict(slug="sample", name="Sample", page="https://example.org", url="https://example.org/api",
                    author=None, files=files, matches=hits)
        report = census_markdown({"retrieved_utc": "2026-09-06T00:00:00Z", "exports": [
            dict(base, updated="2026-09-01"), dict(base, updated="2024-01-01"),
            dict(base, updated="2026-09-01", files=[{"file": "loadorder.txt"}]),
            {"slug": "failed", "url": "https://example.org", "error": "failed"}]})
        self.assertIn("**Total / 1**", report)
        self.assertIn("**2026-only / 1**", report)
        self.assertIn("uploader: not supplied", report)
        self.assertIn("pre-2025 export", report)
        self.assertIn("plugin/load-order only", report)
        self.assertIn("(union, not double-counted): **1/1**", report)


if __name__ == "__main__":
    unittest.main()
