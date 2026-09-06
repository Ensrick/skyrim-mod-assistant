import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import window_focus_guard as gate


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.instance, self.repo, self.data = [self.root / name for name in ('instance', 'repo', 'Data')]
        self.write(self.instance / 'profiles/Default/modlist.txt', '+' + gate.MOD + '\n+Config\n+Vendor\n')
        self.write(self.instance / 'mods' / gate.MOD / 'SKSE/Plugins/WindowFocusGuard.dll', b'owned')
        self.write(self.instance / 'mods/Vendor/SKSE/Plugins/MediaKeysFix.dll', b'vendor')
        self.write(self.instance / 'mods/Vendor/SKSE/Plugins/SSEDisplayTweaks.ini', '[Window]\nLockCursor=true\n')
        self.write(self.instance / 'mods/Config/SKSE/Plugins/SSEDisplayTweaks_Custom.ini', '[Window]\nLockCursor=false\n')
        self.write(self.instance / 'mods/Config/SKSE/Plugins/MediaKeysFix.ini', '[General]\nDisableWindowsKey=false\nBackgroundAccess=false\n')
        self.write(self.repo / 'records/source-builds/window-focus-guard-0.1.0.json', json.dumps({'dllSha256': hashlib.sha256(b'owned').hexdigest()}))

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())

    def check(self):
        return gate.check(self.instance, self.repo, self.data)

    def test_reviewed_pair(self):
        self.assertEqual([], self.check())

    def test_overwrite_is_actual_winner(self):
        self.write(self.instance / 'overwrite/SKSE/Plugins/SSEDisplayTweaks_Custom.ini', '[Window]\nLockCursor=true\n')
        self.assertTrue(any('Two cursor owners' in item for item in self.check()))

    def test_foreign_dll_winner_rejected(self):
        self.write(self.instance / 'overwrite/SKSE/Plugins/WindowFocusGuard.dll', b'unknown')
        self.assertTrue(any('winning DLL' in item for item in self.check()))

    def test_disabled_guard(self):
        self.write(self.instance / 'profiles/Default/modlist.txt', '-' + gate.MOD + '\n+Config\n+Vendor\n')
        self.assertTrue(any('disabled' in item for item in self.check()))

    def test_background_access_rejected(self):
        self.write(self.instance / 'overwrite/SKSE/Plugins/MediaKeysFix.ini', '[General]\nDisableWindowsKey=false\nBackgroundAccess=true\n')
        self.assertTrue(any('BackgroundAccess' in item for item in self.check()))

    def test_config_without_media_dll_rejected(self):
        (self.instance / 'mods/Vendor/SKSE/Plugins/MediaKeysFix.dll').unlink()
        self.assertTrue(any('DLL missing' in item for item in self.check()))


if __name__ == '__main__':
    unittest.main()
