"""Read-only BTPS fixed-offset audit against the installed Skyrim 1.7.104 PE.

This checks bytes and instruction boundaries, not gameplay compatibility.
Run the separate native selection_trampoline test as well. No game is started.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def audit(exe, library):
    data, ids = exe.read_bytes(), library.read_bytes()
    assert struct.unpack_from('<i', ids)[0] == 5, 'expected Address Library v5'
    assert struct.unpack_from('<4I', ids, 4) == (1, 7, 104, 0), 'wrong runtime library'
    pe = struct.unpack_from('<I', data, 60)[0]
    assert data[pe:pe+4] == b'PE\0\0'
    machine, count = struct.unpack_from('<HH', data, pe+4)
    assert machine == 0x8664, 'expected x64 executable'
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    sections = [struct.unpack_from('<8sIIII', data, pe+24+optional_size+i*40)
                for i in range(count)]

    def rva(identifier):
        return struct.unpack_from('<I', ids, 96+identifier*4)[0]

    def read(address, length):
        for _, _, va, size, raw in sections:
            if va <= address and address+length <= va+size:
                return data[raw+address-va:raw+address-va+length]
        raise ValueError(f'RVA not backed by file: {address:x}')

    checks = []
    def exact(name, address, expected):
        actual = read(address, len(expected))
        assert actual == expected, f'{name}: {actual.hex()} != {expected.hex()}'
        checks.append({'name': name, 'rva': hex(address), 'bytes': actual.hex()})

    selection = rva(26127)
    exact('selection: handle store + mov rcx,rbx (7-byte span)',
          selection+0xE38, bytes.fromhex('41894504488bcb'))
    exact('selection resume begins CALL', selection+0xE3F, b'\xe8')
    # Eight pushes followed by sub rsp,0x968 align the caller's stack to 16;
    # the large allocation includes the existing outgoing-call shadow space.
    exact('selection prologue stack reservation', selection+0x22,
          bytes.fromhex('4881ec68090000'))
    exact('horseback skip: complete JNE + MOV (13-byte span)', rva(40621)+0xAA,
          bytes.fromhex('0f8519020000488b0d71dba402'))
    exact('horseback resume begins CALL', rva(40621)+0xB7, b'\xe8')
    for name, identifier, offset, expected_target in [
        ('dismount call', 37864, 0xE2, rva(37906)),
        ('crosshair UI call', 40621, 0x280, 0x1B47F0),
    ]:
        address = rva(identifier)+offset
        exact(name, address, b'\xe8')
        target = address+5+struct.unpack('<i', read(address+1, 4))[0]
        assert target == expected_target, f'{name}: unexpected target {target:x}'
        checks[-1]['targetRva'] = hex(target)
    return {'result': 'PASS', 'runtime': '1.7.104.0', 'checks': checks,
            'exeSha256': hashlib.sha256(data).hexdigest(),
            'addressLibrarySha256': hashlib.sha256(ids).hexdigest(),
            'limitation': 'On-disk hook sites only; not proof of in-game stability or other plugins.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('library', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.exe, args.library), indent=2))
