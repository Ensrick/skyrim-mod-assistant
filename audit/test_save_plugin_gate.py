"""Synthetic, redistributable fixtures. No vendor assets or player saves."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import save_plugin_gate as gate


def n(fmt, value):
    return struct.pack('<' + fmt, value)


def s(value):
    data = value.encode('utf-8')
    return n('H', len(data)) + data


def fixture(compression=0, full=('Skyrim.esm',), light=('TrueHUD.esl',)):
    header = (n('I', 12) + n('I', 1) + s('Test') + n('I', 1)
              + s('Unbound') + s('000.00.01') + s('NordRace')
              + bytes(18) + n('I', 1) + n('I', 1) + n('H', compression))
    plugins = (n('B', len(full)) + b''.join(map(s, full))
               + n('H', len(light)) + b''.join(map(s, light)))
    body = bytes([78]) + n('I', len(plugins)) + plugins + bytes(16)
    if compression == 1:
        packed = zlib.compress(body)
    elif compression == 2:
        # Raw LZ4 final literal-only sequence, independently encoded fixture.
        remainder = len(body) - 15
        extension = bytes([255]) * (remainder // 255) + bytes([remainder % 255])
        packed = bytes([0xf0]) + extension + body
    if compression:
        body = n('I', len(body)) + n('I', len(packed)) + packed
    return b'TESV_SAVEGAME' + n('I', len(header)) + header + bytes(4) + body


class SaveGateTests(unittest.TestCase):
    def test_all_compressions(self):
        for c in (0, 1, 2):
            with self.subTest(c=c):
                result = gate.parse(fixture(c))
                self.assertEqual(result['light'], ['TrueHUD.esl'])
                self.assertEqual(result['compression'], c)

    def test_missing_case_insensitive(self):
        result = gate.parse(fixture())
        self.assertEqual(gate.compare(result, {'skyrim.esm'}), ['TrueHUD.esl'])
        self.assertEqual(gate.compare(result, {'skyrim.esm', 'truehud.esl'}), [])

    def test_bad_header(self):
        with self.assertRaises(gate.InvalidSave):
            gate.parse(b'bad header')

    def test_truncated_compressed(self):
        for c in (1, 2):
            with self.assertRaises(gate.InvalidSave):
                gate.parse(fixture(c)[:-1])

    def test_trailing_compressed(self):
        with self.assertRaises(gate.InvalidSave):
            gate.parse(fixture(1) + b'extra')

    def test_duplicate_table(self):
        with self.assertRaises(gate.InvalidSave):
            gate.parse(fixture(light=('SkyRim.esm',)))

    def test_lz4_overlap(self):
        self.assertEqual(gate.lz4_decode(b'\x15a\x01\x00', 10), b'a' * 10)

    def test_lz4_rejects_invalid(self):
        for data, expected in [(b'\x00\x00\x00', 4), (b'\xf0', 20),
                               (b'\x15a\x01\x00', 9), (b'\x10a', 2)]:
            with self.subTest(data=data), self.assertRaises(gate.InvalidSave):
                gate.lz4_decode(data, expected)

    def test_local_saves_reads_settings_ini(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'settings.ini').write_text('[General]\nLocalSaves=true\n')
            self.assertEqual(gate.saves_directory(root, '/global'), root / 'saves')
            (root / 'settings.ini').write_text('[General]\nLocalSaves=false\n')
            self.assertEqual(gate.saves_directory(root, '/global'), Path('/global'))

    def test_ccc_and_starred_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'plugins.txt').write_text('*Active.esp\nDisabled.esp\n')
            (root / 'Data').mkdir()
            (root / 'Skyrim.ccc').write_text('ccTest.esl\nccMissing.esl\n')
            (root / 'Data' / 'ccTest.esl').touch()
            active = gate.active_plugins(root, root)
            self.assertIn('cctest.esl', active)
            self.assertIn('active.esp', active)
            self.assertNotIn('ccmissing.esl', active)
            self.assertNotIn('disabled.esp', active)

    def test_read_only_and_failure_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save = root / 'test.ess'
            save.write_bytes(fixture(2))
            digest = hashlib.sha256(save.read_bytes()).hexdigest()
            (root / 'plugins.txt').write_text('# empty\n')
            self.assertIn('TrueHUD.esl', gate.check_save(root, save)[0])
            self.assertEqual(digest, hashlib.sha256(save.read_bytes()).hexdigest())
            self.assertTrue(gate.check_save(root, root / 'missing.ess'))
            self.assertEqual(gate.check_save(root, None), [])


if __name__ == '__main__':
    unittest.main()
