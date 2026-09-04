"""Regression tests for the owned RMB Core duplicate-outfit shadow (#200)."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

import cloak_duplicate_shadow as subject


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class CloakDuplicateShadowTests(unittest.TestCase):
    def make_vendor(self, root: Path, data: bytes) -> None:
        for rel in subject.VENDOR_PATHS:
            path = root / Path(rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    @staticmethod
    def copy_owned(root: Path) -> None:
        for rel in subject.OWNED_FILES:
            source = subject.OVERLAY_ROOT / Path(rel)
            target = root / Path(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    @staticmethod
    def fixture(directives: int = 58) -> bytes:
        rules = [f"filterByOutfits=Fixture.esm|{index:03X}:formsToAdd=Fixture.esm|001"
                 for index in range(directives)]
        return ("; synthetic test input only\n" + "\n".join(rules) + "\n").encode("ascii")

    def pin_for(self, data: bytes, directives: int = 58) -> subject.VendorPin:
        return subject.VendorPin(
            paths=subject.VENDOR_PATHS,
            sha256=digest(data),
            size=len(data),
            outfit_directives=directives,
        )

    def test_accepts_only_the_exact_duplicate_pair(self) -> None:
        data = self.fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_vendor(root, data)
            result = subject.validate_vendor(root, self.pin_for(data))
            self.assertTrue(result["byteIdentical"])
            self.assertEqual(58, result["filterByOutfitsDirectivesPerFile"])

    def test_rejects_nonidentical_vendor_paths_before_packaging(self) -> None:
        data = self.fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_vendor(root, data)
            second = root / Path(subject.VENDOR_PATHS[1])
            second.write_bytes(data + b"; upstream changed\n")
            with self.assertRaisesRegex(subject.ValidationError, "no longer byte-identical"):
                subject.validate_vendor(root, self.pin_for(data))

    def test_rejects_identical_pair_hash_drift(self) -> None:
        original = self.fixture()
        changed = original.replace(b"synthetic", b"synthetiC")
        self.assertEqual(len(original), len(changed))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_vendor(root, changed)
            with self.assertRaisesRegex(subject.ValidationError, "vendor duplicate mismatch"):
                subject.validate_vendor(root, self.pin_for(original))

    def test_rejects_directive_count_drift(self) -> None:
        data = self.fixture(57)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_vendor(root, data)
            with self.assertRaisesRegex(subject.ValidationError, "has 57 filterByOutfits"):
                subject.validate_vendor(root, self.pin_for(data, directives=58))

    def test_owned_shadow_is_pinned_comment_only_and_exact_tree(self) -> None:
        details = subject.validate_owned().details()
        self.assertEqual(sorted(subject.OWNED_FILES), [entry["path"] for entry in details])
        shadow = (subject.OVERLAY_ROOT / Path(subject.SHADOW_PATH)).read_bytes()
        self.assertEqual([], subject.active_lines(shadow))

    def test_rejects_active_directive_in_owned_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_owned(root)
            shadow = root / Path(subject.SHADOW_PATH)
            shadow.write_bytes(shadow.read_bytes() + b"filterByOutfits=Bad.esm|1:formsToAdd=Bad.esm|2\n")
            with self.assertRaisesRegex(subject.ValidationError, "not comment-only"):
                subject.validate_owned(root)

    def test_archive_uses_validated_snapshot_not_later_filesystem_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_owned(root)
            snapshot = subject.validate_owned(root)
            expected_shadow = dict(snapshot.entries)[subject.SHADOW_PATH]
            shadow = root / Path(subject.SHADOW_PATH)
            shadow.write_bytes(b"filterByOutfits=Bad.esm|1:formsToAdd=Bad.esm|2\n")
            output = root / "snapshot.zip"
            subject.write_archive(output, snapshot)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(expected_shadow, archive.read(subject.SHADOW_PATH))
                self.assertNotEqual(shadow.read_bytes(), archive.read(subject.SHADOW_PATH))

    def test_archive_is_reproducible_and_contains_owned_bytes_only(self) -> None:
        vendor = self.fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_vendor(root, vendor)
            pin = self.pin_for(vendor)
            first = root / "first.zip"
            second = root / "second.zip"
            subject.build(root, first, pin=pin)
            subject.build(root, second, pin=pin)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(sorted(subject.OWNED_FILES), archive.namelist())
                for name in archive.namelist():
                    self.assertEqual(
                        (subject.OVERLAY_ROOT / Path(name)).read_bytes(),
                        archive.read(name),
                    )
                    self.assertNotIn(vendor, archive.read(name))


if __name__ == "__main__":
    unittest.main()
