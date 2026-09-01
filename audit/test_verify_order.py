"""Synthetic regression tests for verify_order's activation semantics."""

import os
import struct
import tempfile
import unittest

import verify_order


def write_plugin(path, masters=()):
    body = b"".join(
        b"MAST"
        + struct.pack("<H", len(name.encode("cp1252")) + 1)
        + name.encode("cp1252")
        + b"\x00"
        for name in masters
    )
    with open(path, "wb") as stream:
        stream.write(b"TES4" + struct.pack("<I", len(body)) + (b"\x00" * 16))
        stream.write(body)


class VerifyOrderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        self.game_root = os.path.join(self.root, "game")
        self.game_data = os.path.join(self.game_root, "Data")
        os.makedirs(self.game_data)
        self.ccc = os.path.join(self.game_root, "Skyrim.ccc")

    def index(self, *names):
        result = {}
        for name in names:
            path = os.path.join(self.game_data, name)
            if not os.path.exists(path):
                write_plugin(path)
            result[name.lower()] = path
        return result

    def test_only_base_and_ccc_entries_are_implicit(self):
        with open(self.ccc, "w", encoding="utf-8") as stream:
            stream.write("ccExample.esl\n")
        implicit = verify_order.implicit_masters(self.ccc)
        self.assertIn("skyrim.esm", implicit)
        self.assertIn("ccexample.esl", implicit)
        self.assertNotIn("loosemaster.esm", implicit)

    def test_physical_loose_master_is_inactive_not_implicit(self):
        dependent = os.path.join(self.game_data, "Dependent.esp")
        write_plugin(dependent, ["Skyrim.esm", "LooseMaster.esm"])
        index = self.index("Skyrim.esm", "LooseMaster.esm")
        index["dependent.esp"] = dependent

        findings = verify_order.evaluate_load_order(
            ["Dependent.esp"], index, set(verify_order.OFFICIAL_BASE_MASTERS)
        )
        self.assertEqual(
            findings["inactive_master"], [("Dependent.esp", "LooseMaster.esm")]
        )
        self.assertEqual(findings["missing_master"], [])

    def test_creation_club_entry_is_implicitly_active(self):
        dependent = os.path.join(self.game_data, "Dependent.esp")
        write_plugin(dependent, ["ccExample.esl"])
        index = self.index("ccExample.esl")
        index["dependent.esp"] = dependent

        findings = verify_order.evaluate_load_order(
            ["Dependent.esp"], index, {"ccexample.esl"}
        )
        self.assertFalse(any(findings.values()))

    def test_missing_ccc_provider_fails_even_when_implicitly_declared(self):
        dependent = os.path.join(self.game_data, "Dependent.esp")
        write_plugin(dependent, ["ccMissing.esl"])
        findings = verify_order.evaluate_load_order(
            ["Dependent.esp"], {"dependent.esp": dependent}, {"ccmissing.esl"}
        )
        self.assertEqual(
            findings["missing_master"], [("Dependent.esp", "ccMissing.esl")]
        )

    def test_late_master_is_reported(self):
        dependent = os.path.join(self.game_data, "Dependent.esp")
        master = os.path.join(self.game_data, "Master.esm")
        write_plugin(dependent, ["Master.esm"])
        write_plugin(master)
        findings = verify_order.evaluate_load_order(
            ["Dependent.esp", "Master.esm"],
            {"dependent.esp": dependent, "master.esm": master},
            set(),
        )
        self.assertEqual(
            findings["order_violation"], [("Dependent.esp", "Master.esm")]
        )

    def test_earlier_active_master_is_clean(self):
        dependent = os.path.join(self.game_data, "Dependent.esp")
        master = os.path.join(self.game_data, "Master.esm")
        write_plugin(dependent, ["Master.esm"])
        write_plugin(master)
        findings = verify_order.evaluate_load_order(
            ["Master.esm", "Dependent.esp"],
            {"dependent.esp": dependent, "master.esm": master},
            set(),
        )
        self.assertFalse(any(findings.values()))

    def test_malformed_ccc_entry_is_rejected(self):
        with open(self.ccc, "w", encoding="utf-8") as stream:
            stream.write("Data/ccExample.esl\n")
        with self.assertRaisesRegex(ValueError, "invalid Skyrim.ccc entry"):
            verify_order.creation_club_masters(self.ccc)

    def test_truncated_master_subrecord_is_unreadable(self):
        broken = os.path.join(self.game_data, "Broken.esp")
        body = b"MAST" + struct.pack("<H", 20) + b"short"
        with open(broken, "wb") as stream:
            stream.write(b"TES4" + struct.pack("<I", len(body)) + (b"\x00" * 16))
            stream.write(body)
        findings = verify_order.evaluate_load_order(
            ["Broken.esp"], {"broken.esp": broken}, set()
        )
        self.assertEqual(len(findings["unreadable"]), 1)

    def test_extended_size_subrecord_preserves_master_alignment(self):
        path = os.path.join(self.game_data, "Extended.esp")
        master_name = b"Skyrim.esm\x00"
        oversized_payload = b"x" * 70000
        body = (
            b"MAST"
            + struct.pack("<H", len(master_name))
            + master_name
            + b"XXXX"
            + struct.pack("<H", 4)
            + struct.pack("<I", len(oversized_payload))
            + b"ONAM"
            + struct.pack("<H", 0)
            + oversized_payload
        )
        with open(path, "wb") as stream:
            stream.write(b"TES4" + struct.pack("<I", len(body)) + (b"\x00" * 16))
            stream.write(body)
        self.assertEqual(verify_order.masters_of(path), ["Skyrim.esm"])


if __name__ == "__main__":
    unittest.main()
