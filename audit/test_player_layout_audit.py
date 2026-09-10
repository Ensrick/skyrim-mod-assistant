import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import player_layout_audit as audit


class LayoutTests(unittest.TestCase):
    def fixture(self):
        count = max(audit.IDS) + 1
        data = bytearray(96 + count*4)
        struct.pack_into('<5I', data, 0, 5, 1, 7, 104, 0)
        struct.pack_into('<ii', data, 84, 8, 0)
        struct.pack_into('<i', data, 92, count)
        for key, value in audit.IDS.items():
            struct.pack_into('<I', data, 96 + key*4, value)
        return data

    def test_dense_lookup(self):
        self.assertEqual(audit.library_offsets(self.fixture()), audit.IDS)

    def test_short_header(self):
        for length in (0, 19, 95):
            with self.assertRaises(ValueError):
                audit.library_offsets(bytes(length))

    def test_unknown_version(self):
        data = self.fixture()
        struct.pack_into('<I', data, 12, 105)
        with self.assertRaises(ValueError):
            audit.library_offsets(data)

    def test_bad_counts(self):
        for count in (-1, 0, max(audit.IDS), 0x7fffffff):
            data = self.fixture()
            struct.pack_into('<i', data, 92, count)
            with self.assertRaises(ValueError):
                audit.library_offsets(data)

    def test_unknown_pointer_size_or_format(self):
        for size, fmt in ((4, 0), (8, 1), (0, 0)):
            data = self.fixture()
            struct.pack_into('<ii', data, 84, size, fmt)
            with self.assertRaises(ValueError):
                audit.library_offsets(data)

    def test_bounded_read(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'synthetic.bin'
            path.write_bytes(b'12345')
            self.assertEqual(audit.bounded_read(path, 5), b'12345')
            with self.assertRaises(ValueError):
                audit.bounded_read(path, 4)

    def test_truncated_or_trailing_table(self):
        data = self.fixture()
        for value in (data[:-1], data + b'\0'):
            with self.assertRaises(ValueError):
                audit.library_offsets(value)

    def test_unknown_engine_and_library_never_interpreted(self):
        with patch.object(audit, 'span', side_effect=AssertionError('must not read')), \
             patch.object(audit, 'library_offsets', side_effect=AssertionError('must not parse')):
            checks = audit.verify(b'unknown engine', b'unknown library')
        self.assertEqual(len(checks), 2)
        self.assertFalse(any(c['pass'] for c in checks))


if __name__ == '__main__':
    unittest.main()
