"""Read-only exact-build evidence for player observation, not gameplay proof.

No engine calls, remote writes or observer deployment. Native byte spans confirm
the narrowly named fields, not every Actor method or the whole CommonLib ABI.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from skse_load_arguments import ENGINE_MD5, span

LIBRARY_SHA256 = '8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842'
IDS = {403521: 0x3230778, 208040: 0x19296C0, 208715: 0x19351C8,
       19790: 0x2F0EF0, 208694: 0x1935070}

# These fragments are instruction-aligned and manually reviewed in the exact
# executable. Names deliberately distinguish layout from semantic conclusions.
SITES = (
    ('reference parent-cell read', 0x2F0F1A, '488b4360'),
    ('cell interior-flag test', 0x2F0F3B, 'f6404001'),
    ('cell worldspace read', 0x2F0F41, '488bb028010000'),
    ('position x comparison', 0x2F0F65, '0f2e4354'),
    ('position y comparison', 0x2F0F71, '0f2e4358'),
    ('position z comparison', 0x2F0F7D, '0f2e435c'),
    ('position x assignment', 0x2F0F8B, '418b06894354'),
    ('position y assignment', 0x2F0F91, '418b4604894358'),
    ('position z assignment', 0x2F0F98, '418b460889435c'),
    ('native player life-state mask', 0x7ADA57,
     '488b0d1a2da802f781c80000000000e001'),
    ('native actor-state receiver and mask call', 0x7B0436,
     '488b0d3b03a802ba000400004881c1c0000000e8e210f3ff'),
    ('actor-state flag reader', 0x6E1530,
     '8b4108440fb7c24123c025ff3f0000413bc00f94c0c3'),
    ('input-packet movement-vector initialization', 0x7AD930,
     'f30f100520edb602f30f114124f30f100d17edb602f30f114928'),
    ('forward handler writes positive move y', 0x7B380A,
     'c747040000803fc6472400'),
)


def library_offsets(data):
    if len(data) < 96 or struct.unpack_from('<5I', data) != (5, 1, 7, 104, 0):
        raise ValueError('Unsupported/truncated address-library header')
    if struct.unpack_from('<ii', data, 84) != (8, 0):
        raise ValueError('Unsupported pointer size or dense format')
    count = struct.unpack_from('<i', data, 92)[0]
    if count <= max(IDS) or len(data) != 96 + count * 4:
        raise ValueError('Invalid dense offset count/length')
    return {i: struct.unpack_from('<I', data, 96 + 4*i)[0] for i in IDS}


def bounded_read(path, limit):
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'Input exceeds {limit} byte limit')
    return data


def verify(engine, library):
    checks = [
        {'name': 'exact engine identity', 'pass': hashlib.md5(engine).hexdigest() == ENGINE_MD5},
        {'name': 'exact library identity', 'pass': hashlib.sha256(library).hexdigest() == LIBRARY_SHA256},
    ]
    if not all(c['pass'] for c in checks):
        return checks  # Never interpret an unreviewed executable/library.
    try:
        offsets = library_offsets(library)
        checks.extend({'name': f'address ID {i}', 'pass': offsets[i] == rva} for i, rva in IDS.items())
        for name, rva, expected in SITES:
            raw = bytes.fromhex(expected)
            checks.append({'name': name, 'pass': span(engine, rva, len(raw)) == raw})
        for name, vtable, slot, target in (
            ('MovementHandler CanProcess', 0x19351C8, 1, 0x7B4FB0),
            ('MovementHandler ProcessButton', 0x19351C8, 6, 0x7B37C0),
            ('PlayerControls input sink', 0x1935070, 1, 0x7AD900),
        ):
            address = struct.unpack('<Q', span(engine, vtable + slot*8, 8))[0]
            checks.append({'name': name, 'pass': address == 0x140000000 + target})
    except (ValueError, struct.error) as error:
        checks.append({'name': 'bounded format interpretation', 'pass': False, 'error': str(error)})
    return checks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('executable', type=Path)
    p.add_argument('library', type=Path)
    a = p.parse_args()
    try:
        checks = verify(bounded_read(a.executable, 64*1024*1024),
                        bounded_read(a.library, 16*1024*1024))
    except (OSError, ValueError) as error:
        checks = [{'name': 'bounded input read', 'pass': False, 'error': str(error)}]
    passed = all(c['pass'] for c in checks)
    print(json.dumps({'verdict': 'LAYOUT-BYTES-OK' if passed else 'REFUSED', 'checks': checks,
                     'scope': 'Exact named native fields only. Not health virtual-call safety, movement success, save compatibility or gameplay certification.'}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
