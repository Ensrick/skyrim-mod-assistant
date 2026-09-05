"""Front-end safety tests: synthetic archives only, no game/tool invocation."""
import importlib.util
import argparse
import contextlib
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

spec = importlib.util.spec_from_file_location("tcoss_frontend", Path(__file__).with_name("convert.py"))
frontend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frontend)


def archive(extra=(), prefix=""):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as packed:
        for name in frontend.REQUIRED_FILES:
            packed.writestr(prefix + name, b"synthetic-test-data")
        for name in extra:
            packed.writestr(name, b"test")
    buffer.seek(0)
    return zipfile.ZipFile(buffer)


class SafetyTests(unittest.TestCase):
    def test_root_sources(self):
        with archive() as packed:
            self.assertEqual(set(frontend.source_members(packed)), frontend.REQUIRED_FILES)

    def test_wrapper_directory_and_unneeded_payload(self):
        with archive(["release/README.txt", "release/unused.exe"], prefix="release/") as packed:
            self.assertEqual(len(frontend.source_members(packed)), 4)

    def test_unsafe_paths(self):
        for name in ("../escape", "/absolute", "C:/escape", "safe/../../escape", "a\\..\\escape"):
            with self.subTest(name=name), archive([name]) as packed:
                with self.assertRaises(ValueError):
                    frontend.source_members(packed)

    def test_case_collision(self):
        with archive(["tcoss.esm"]) as packed:
            with self.assertRaises(ValueError):
                frontend.source_members(packed)

    def test_ambiguous_wrappers(self):
        with archive(["other/TCOSS.esm"]) as packed:
            with self.assertRaises(ValueError):
                frontend.source_members(packed)

    def test_missing_required(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as packed:
            packed.writestr("readme.txt", "incomplete")
        data.seek(0)
        with zipfile.ZipFile(data) as packed:
            with self.assertRaises(ValueError):
                frontend.source_members(packed)

    def test_symlink(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with archive([link]) as packed:
            with self.assertRaises(ValueError):
                frontend.source_members(packed)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tcoss-converter-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        game = self.root / "Game" / "Data"
        game.mkdir(parents=True)
        for name in ("Skyrim.esm", "Skyrim - Meshes0.bsa", "Skyrim - Textures0.bsa"):
            (game / name).write_bytes(b"synthetic-data")
        self.download = self.root / "source.zip"
        with zipfile.ZipFile(self.download, "w") as packed:
            for name in frontend.REQUIRED_FILES:
                packed.writestr(name, b"synthetic-data")
        helper = self.root / "never-executed.exe"
        helper.write_bytes(b"synthetic-helper")
        config = self.root / "tools.json"
        config.write_text(json.dumps({"tools": {name: {"path": str(helper), "sha256": frontend.sha256(helper)}
                                                for name in frontend.TOOL_FLAGS}}), encoding="utf-8")
        self.args = argparse.Namespace(archive=self.download, game_data=game,
                                       output=self.root / "output", toolchain=config, bsarch=None)
        for patcher in (mock.patch.object(frontend, "ARCHIVE_SHA256", frontend.sha256(self.download)),
                        mock.patch.object(frontend.shutil, "disk_usage", return_value=argparse.Namespace(free=9 * 1024**3))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_valid_preflight_is_read_only(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        frontend.preflight(self.args)
        self.assertFalse(self.args.output.exists())
        after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_existing_output_preserved(self):
        self.args.output.mkdir()
        marker = self.args.output / "keep.txt"
        marker.write_text("preserve", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            frontend.preflight(self.args)
        self.assertEqual(marker.read_text(), "preserve")

    def test_game_overlap_refused(self):
        self.args.output = self.args.game_data / "do-not-write-here"
        with self.assertRaisesRegex(ValueError, "overlap"):
            frontend.preflight(self.args)
        self.assertFalse(self.args.output.exists())

    def test_wrong_source_refused(self):
        with mock.patch.object(frontend, "ARCHIVE_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "Wrong source"):
                frontend.preflight(self.args)
        self.assertFalse(self.args.output.exists())

    def test_tool_hash_mismatch_refused(self):
        config = json.loads(self.args.toolchain.read_text())
        config["tools"]["spriggit"]["sha256"] = "0" * 64
        self.args.toolchain.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "tool hash mismatch"):
            frontend.preflight(self.args)
        self.assertFalse(self.args.output.exists())

    def test_check_only_never_executes_or_writes(self):
        command = ["convert.py", "--archive", str(self.args.archive), "--output", str(self.args.output),
                   "--game-data", str(self.args.game_data), "--toolchain", str(self.args.toolchain), "--check-only"]
        with mock.patch.object(frontend.sys, "argv", command), mock.patch.object(frontend, "execute") as execute:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                frontend.main()
        execute.assert_not_called()
        self.assertFalse(self.args.output.exists())
        self.assertEqual(json.loads(output.getvalue())["preflight"], "PASS")

    def test_unavailable_anchor_terminates(self):
        anchor = mock.Mock()
        anchor.exists.return_value = False
        anchor.parent = anchor
        with self.assertRaisesRegex(ValueError, "unavailable"):
            frontend.existing_ancestor(anchor)


if __name__ == "__main__":
    unittest.main()
