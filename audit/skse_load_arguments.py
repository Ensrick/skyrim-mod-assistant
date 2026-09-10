"""Read-only exact-build verification of the audited 1.7.104 load ABI repair.

This is a pinned byte/identity audit, not a general disassembler or runtime test.
Unknown builds fail closed even when they might be functionally correct.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ENGINE_MD5 = '113faeb71fd8f62b26d0c8627299ab40'
DLL_SHA256 = 'cc2f98a4189e1980b216e0c10c15dbdb65827b44028fbad11a129ff6d2094591'

def span(data, rva, count):
    if data[:2] != b'MZ':
        raise ValueError('Not a PE file')
    pe, = struct.unpack_from('<I', data, 60)
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    n, = struct.unpack_from('<H', data, pe+6)
    opt, = struct.unpack_from('<H', data, pe+20)
    for i in range(n):
        _, _, va, size, raw = struct.unpack_from('<8sIIII', data, pe+24+opt+i*40)
        if va <= rva and rva+count <= va+size:
            result = data[raw+rva-va:raw+rva-va+count]
            if len(result) == count:
                return result
    raise ValueError('Span not backed by file')

def verify(executable, dll):
    engine = Path(executable).read_bytes()
    candidate = Path(dll).read_bytes()
    checks = []
    def check(name, result):
        checks.append({'name': name, 'pass': bool(result)})
    check('exact engine identity', hashlib.md5(engine).hexdigest() == ENGINE_MD5)
    check('exact audited DLL identity', hashlib.sha256(candidate).hexdigest() == DLL_SHA256)
    if not all(c['pass'] for c in checks):
        return checks
    for name, data, rva, expected in (
        ('engine sixth outgoing byte', engine, 0x62810C, '88442428'),
        ('engine call to audited target', engine, 0x62812F, 'e83c08ffff'),
        ('engine sixth incoming byte', engine, 0x618A9D, '0fb69d88030000'),
        ('hook frame eight pushes and 78h allocation', candidate, 0x103A0,
         '405355565741544155415641574883ec78'),
        ('hook sixth incoming byte to ESI', candidate, 0x10442, '0fb6b424e8000000'),
        ('hook sixth outgoing byte from SIL', candidate, 0x10482, '4088742428'),
        ('hook target address adjustment', candidate, 0x1047C, '480570896100'),
        ('hook target call', candidate, 0x1049C, 'ffd0'),
    ):
        wanted = bytes.fromhex(expected)
        check(name, span(data, rva, len(wanted)) == wanted)
    return checks

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('dll', type=Path)
    args = parser.parse_args()
    try:
        checks = verify(args.executable, args.dll)
        passed = all(c['pass'] for c in checks)
        print(json.dumps({'pass': passed, 'checks': checks,
                          'scope': 'Exact audited bytes only; not save health, load admission or crash closure.'}, indent=2))
        raise SystemExit(0 if passed else 1)
    except (OSError, ValueError, struct.error) as error:
        print(json.dumps({'pass': False, 'error': str(error)}))
        raise SystemExit(1)
