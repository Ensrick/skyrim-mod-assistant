import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zlib
from biped_slot_audit import runtime_plugins, scan_plugin, scan_profile, subrecords


def subrecord(tag, body):
    return struct.pack("<4sH", tag, len(body)) + body


def record(tag, body, flags=0, form_id=0):
    return struct.pack("<4sIIIII", tag, len(body), flags, form_id, 0, 0) + body


def plugin(*records, masters=()):
    header = subrecord(b"HEDR", struct.pack("<fII", 1.7, len(records), 0x800))
    for master in masters:
        header += subrecord(b"MAST", master.encode("cp1252") + b"\0")
        header += subrecord(b"DATA", b"\0" * 8)
    return record(b"TES4", header) + b"".join(records)


class MemoryPlugin:
    name = "Fixture.esp"

    def __init__(self, data):
        self.data = data

    def read_bytes(self):
        return self.data


class BipedReaderTests(unittest.TestCase):
    def test_tes4_body_cannot_exceed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Truncated.esp"
            path.write_bytes(struct.pack("<4sIIIII", b"TES4", 1000000, 0, 0, 0, 0))
            with self.assertRaisesRegex(ValueError, "TES4 body exceeds"):
                scan_plugin(path)

    def test_missing_hedr_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Empty.esp"
            path.write_bytes(struct.pack("<4sIIIII", b"TES4", 0, 0, 0, 0, 0))
            with self.assertRaisesRegex(ValueError, "valid HEDR"):
                scan_plugin(path)

    def test_subrecords_reject_bad_boundaries(self):
        for blob in (b"abc", b"EDID\x08\x00short", b"XXXX\x04\x00\x01\x00\x00\x00"):
            with self.assertRaises(ValueError):
                list(subrecords(blob))

    def test_extended_subrecord_and_nested_group(self):
        edid = b"FullCloak\0"
        body = subrecord(b"XXXX", struct.pack("<I", len(edid))) + b"EDID\0\0" + edid
        body += subrecord(b"BOD2", struct.pack("<II", 1 << 28, 2))
        armo = record(b"ARMO", body, form_id=0x800)
        group = struct.pack("<4sIIIII", b"GRUP", 24 + len(armo), 0, 0, 0, 0) + armo
        _, rows = scan_plugin(MemoryPlugin(plugin(group)))
        self.assertEqual(rows[0]["mask"], 1 << 28)
        self.assertEqual(rows[0]["editorId"], "FullCloak")

    def test_trailing_or_partial_records_rejected(self):
        for body in (b"X", record(b"ARMO", b"")[:-1],
                     struct.pack("<4sIIIII", b"GRUP", 23, 0, 0, 0, 0),
                     struct.pack("<4sIIIII", b"GRUP", 200, 0, 0, 0, 0)):
            with self.subTest(body=body), self.assertRaises(ValueError):
                scan_plugin(MemoryPlugin(plugin() + body))

    def test_compressed_record_framing(self):
        body = subrecord(b"BOD2", struct.pack("<II", 1 << 28, 2))
        stream = zlib.compress(body)
        valid = struct.pack("<I", len(body)) + stream
        _, rows = scan_plugin(MemoryPlugin(plugin(record(b"ARMO", valid, 0x40000, 0x800))))
        self.assertEqual(rows[0]["mask"], 1 << 28)
        for malformed in (b"", valid[:-1], valid + b"extra", valid + stream,
                          struct.pack("<I", len(body) - 1) + stream,
                          struct.pack("<I", len(body) + 1) + stream):
            with self.subTest(body=malformed), self.assertRaises((ValueError, zlib.error)):
                scan_plugin(MemoryPlugin(plugin(record(b"ARMO", malformed, 0x40000, 0x800))))

    def test_duplicate_masks_cannot_hide_reserved_bit(self):
        body = subrecord(b"BOD2", struct.pack("<II", 1 << 28, 2))
        body += subrecord(b"BOD2", struct.pack("<II", 0, 2))
        with self.assertRaisesRegex(ValueError, "Duplicate biped"):
            scan_plugin(MemoryPlugin(plugin(record(b"ARMO", body, form_id=0x800))))

    def test_armature_and_model_names_preserved(self):
        armo = record(b"ARMO", subrecord(b"MODL", struct.pack("<I", 0x800)), form_id=0x01000800)
        arma_body = subrecord(b"MOD2", b"Armor\\Cloak.NIF\0") + subrecord(b"MODL", struct.pack("<I", 0x13746))
        arma = record(b"ARMA", arma_body, form_id=0x801)
        _, rows = scan_plugin(MemoryPlugin(plugin(armo, arma, masters=("Skyrim.esm",))))
        self.assertEqual(rows[0]["armatures"], ["000800:Skyrim.esm"])
        self.assertEqual(rows[0]["formKey"], "000800:Fixture.esp")
        self.assertEqual(rows[1]["models"], ["armor/cloak.nif"])

    def test_malformed_form_links_and_names_fail_closed(self):
        bodies = [(b"ARMO", subrecord(b"MODL", b"123")),
                  (b"ARMO", subrecord(b"MODL", struct.pack("<I", 0x05000800))),
                  (b"ARMA", subrecord(b"MOD2", b"Cloak.nif")),
                  (b"ARMA", subrecord(b"MOD2", b"Cloak\0.nif\0")),
                  (b"ARMO", subrecord(b"EDID", b"Name\0junk")),
                  (b"ARMO", subrecord(b"BOD2", b"12"))]
        for tag, body in bodies:
            with self.subTest(tag=tag, body=body), self.assertRaises(ValueError):
                scan_plugin(MemoryPlugin(plugin(record(tag, body, form_id=0x800))))

    def test_master_names_must_be_unambiguous(self):
        for masters in (("",), ("../Some.esp",), ("Fixture.esp",), ("Skyrim.esm", "skyrim.esm")):
            with self.subTest(masters=masters), self.assertRaises(ValueError):
                scan_plugin(MemoryPlugin(plugin(masters=masters)))

    def test_profile_retains_losing_and_winning_declarations(self):
        first = {"formKey": "000800:Base.esm", "type": "ARMO", "editorId": "Cloak",
                 "mask": 1 << 28, "models": [], "armatures": ["000801:Base.esm"]}
        last = {**first, "mask": 0}
        paths = [Path("Base.esm"), Path("Later.esp")]
        with patch("biped_slot_audit.runtime_plugins", return_value=paths), \
             patch("biped_slot_audit.scan_plugin", side_effect=[("FIRST", [first]), ("LAST", [last])]):
            result = scan_profile(Path("instance"), Path("Data"), 58)
        self.assertEqual(len(result["declarations"]), 2)
        self.assertEqual([row["provider"] for row in result["declarations"]], ["Base.esm", "Later.esp"])
        self.assertEqual(len(result["collisions"]), 1)


class RuntimeResolverTests(unittest.TestCase):
    def test_implicit_plugins_and_file_winner_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            instance, data = base / "instance", base / "game" / "Data"
            profile = instance / "profiles" / "Default"
            profile.mkdir(parents=True)
            data.mkdir(parents=True)
            for name in ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm",
                         "Dragonborn.esm", "_ResourcePack.esl", "Implicit.esl", "Active.esp", "Inactive.esp"):
                (data / name).touch()
            (data.parent / "Skyrim.ccc").write_text("# official content\nImplicit.esl\n", encoding="utf-8")
            profile.joinpath("plugins.txt").write_text("*Active.esp\nInactive.esp\n*IMPLICIT.esl\n", encoding="utf-8")
            profile.joinpath("modlist.txt").write_text("+High\n+Low\n-Disabled\n", encoding="utf-8")
            for name in ("High", "Low", "Disabled"):
                folder = instance / "mods" / name
                folder.mkdir(parents=True)
                (folder / "Active.esp").touch()
            resolved = runtime_plugins(instance, data)
            self.assertEqual(len(resolved), 8)
            self.assertEqual(resolved[-1], (instance / "mods" / "High" / "Active.esp").resolve())
            self.assertEqual(sum(path.name.lower() == "implicit.esl" for path in resolved), 1)
            overwrite = instance / "overwrite"
            overwrite.mkdir()
            (overwrite / "Active.esp").touch()
            self.assertEqual(runtime_plugins(instance, data)[-1], (overwrite / "Active.esp").resolve())
            (data / "Implicit.esl").unlink()
            with self.assertRaisesRegex(ValueError, "Unresolved runtime plugins"):
                runtime_plugins(instance, data)


if __name__ == "__main__":
    unittest.main()
