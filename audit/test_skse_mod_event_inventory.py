"""Synthetic format tests; no game assets or player saves are fixtures."""
import struct
import unittest
from skse_mod_event_inventory import inspect


def string(value):
    raw = value.encode('utf-8')
    return struct.pack('<H', len(raw)) + raw


def chunk(kind, version, payload=b''):
    return struct.pack('<III', int.from_bytes(kind.encode(), 'big'), version, len(payload)) + payload


def core(records, uid=0):
    payload = b''.join(records)
    return struct.pack('<III', uid, len(records), len(payload)) + payload


def wrapper(blocks):
    return b'SKSE' + struct.pack('<IIII', 1, 0x02030010, 0x01070680, len(blocks)) + b''.join(blocks)


def records():
    plugins = struct.pack('<H', 2) + b'\0' + string('Skyrim.esm')
    plugins += b'\xfe' + struct.pack('<H', 0x51) + string('Missing.esl')
    events = string('Ready') + struct.pack('<I', 3)
    for handle in (0xFFFFFE051800, 0xFFFF00000014, 0xFFFFFF000800):
        events += struct.pack('<Q', handle) + string('OnReady')
    return [chunk('PLGN', 0, plugins), chunk('MCBR', 1), chunk('REGS', 1, events), chunk('REGE', 1)]


class InventoryTests(unittest.TestCase):
    def test_exact_saved_origin_and_dynamic(self):
        result = inspect(wrapper([core(records())]))
        self.assertEqual(result['savedPlugins'], 2)
        a, b, c = result['registrations']
        self.assertEqual((a['savedIndex'], a['savedPlugin'], a['dynamic']), ('FE051', 'Missing.esl', False))
        self.assertEqual((b['formID'], b['savedPlugin']), ('00000014', 'Skyrim.esm'))
        self.assertTrue(c['dynamic'])
        self.assertIsNone(c['savedPlugin'])

    def test_every_truncation_rejected(self):
        raw = wrapper([core(records())])
        for length in range(len(raw)):
            with self.subTest(length=length), self.assertRaises(ValueError):
                inspect(raw[:length])

    def test_trailing_bytes(self):
        with self.assertRaises(ValueError):
            inspect(wrapper([core(records())]) + b'x')

    def test_duplicate_core(self):
        with self.assertRaises(ValueError):
            inspect(wrapper([core(records()), core(records())]))

    def test_missing_core(self):
        with self.assertRaises(ValueError):
            inspect(wrapper([core([], uid=123)]))

    def test_vendor_chunks_ignored(self):
        self.assertEqual(inspect(wrapper([core([chunk('TEST', 42, b'abc')], 1), core(records())]))['savedPlugins'], 2)

    def test_malformed_event_groups(self):
        original = records()
        variants = [original[:-1], original + [chunk('MCBR', 1)],
                    [original[0], chunk('MCBR', 2)] + original[2:],
                    [original[0], chunk('MCBR', 1, b'x')] + original[2:],
                    original[:-1] + [chunk('TEST', 1)],
                    [original[0], chunk('MCBR', 1), chunk('REGS', 1, string('Ready') + struct.pack('<I', 999)), original[-1]]]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect(wrapper([core(value)]))

    def test_bad_plugin_tables(self):
        variants = [chunk('PLGN', 1, b'\0\0'), chunk('MODS', 0),
                    chunk('PLGN', 0, b'\1\0\xff' + string('Bad.esm')),
                    chunk('PLGN', 0, b'\1\0\xfe\0\x10' + string('Bad.esl')),
                    chunk('PLGN', 0, b'\1\0\0' + string('Bad\0.esm')),
                    chunk('PLGN', 0, b'\2\0' + (b'\0' + string('Skyrim.esm')) * 2)]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect(wrapper([core([value] + records()[1:])]))


if __name__ == '__main__':
    unittest.main()
