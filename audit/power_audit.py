"""List every Power and Lesser Power added by the active load order.

The question behind it is not "which mods add powers" but "which mods put a
utility button in the Powers menu" - a scene-unstick, a tent-pitch, a config
opener. Those are indistinguishable from real powers in the record, so this
produces the candidate list and the names do the sorting.

SPEL/SPIT layout (SSE): baseCost u32, flags u32, type u32, chargeTime f32,
castType u32, delivery u32, castDuration f32, range f32, perk formid.
type: 0 Spell, 1 Disease, 2 Power, 3 LesserPower, 4 Ability, 5 Poison,
6 Addiction, 7 Voice.
"""
import glob
import io
import os
import struct
import sys
import zlib

MODS = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\mods'
DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
PROF = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se\profiles\Default'

TYPE_NAME = {2: 'Power', 3: 'LesserPower'}
COMPRESSED = 0x00040000

VANILLA = {
    'skyrim.esm', 'update.esm', 'dawnguard.esm', 'hearthfires.esm',
    'dragonborn.esm', 'ccbgssse001-fish.esm', 'ccbgssse025-advdsgs.esm',
    'ccbgssse037-curios.esl', 'ccqdrsse001-survivalmode.esl',
}


def subrecords(body):
    p = 0
    size_override = 0
    while p + 6 <= len(body):
        tag = body[p:p + 4]
        size = struct.unpack_from('<H', body, p + 4)[0]
        p += 6
        if tag == b'XXXX':
            size_override = struct.unpack_from('<I', body, p)[0]
            p += size
            continue
        if size_override:
            size = size_override
            size_override = 0
        yield tag, body[p:p + size]
        p += size


def scan(path):
    d = open(path, 'rb').read()
    hs = struct.unpack_from('<I', d, 4)[0]
    out = []

    def walk(p, end):
        while p + 24 <= end:
            typ = d[p:p + 4]
            size = struct.unpack_from('<I', d, p + 4)[0]
            if typ == b'GRUP':
                walk(p + 24, p + size)
                p += size
                continue
            if typ == b'SPEL':
                flags = struct.unpack_from('<I', d, p + 8)[0]
                fid = struct.unpack_from('<I', d, p + 12)[0]
                body = d[p + 24:p + 24 + size]
                if flags & COMPRESSED:
                    try:
                        body = zlib.decompress(body[4:])
                    except Exception:
                        body = b''
                edid = full = None
                spell_type = None
                for tag, payload in subrecords(body):
                    if tag == b'EDID':
                        edid = payload.rstrip(b'\x00').decode('latin-1')
                    elif tag == b'FULL':
                        full = payload.rstrip(b'\x00').decode('latin-1')
                    elif tag == b'SPIT' and len(payload) >= 12:
                        spell_type = struct.unpack_from('<I', payload, 8)[0]
                if spell_type in TYPE_NAME:
                    out.append((TYPE_NAME[spell_type], fid, edid or '', full or ''))
            p += 24 + size

    walk(24 + hs, len(d))
    return out


def main():
    active = []
    with io.open(os.path.join(PROF, 'plugins.txt'), encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('*'):
                active.append(line[1:])

    order = []
    with io.open(os.path.join(PROF, 'modlist.txt'), encoding='utf-8') as fh:
        for line in fh:
            line = line.rstrip('\n')
            if line.startswith('+') and not line.endswith('_separator'):
                order.append(line[1:])

    index = {}
    for mod in order:
        for p in glob.glob(os.path.join(MODS, mod, '*.es[pml]')):
            index.setdefault(os.path.basename(p).lower(), (p, mod))
    for p in glob.glob(os.path.join(DATA, '*.es[pml]')):
        index.setdefault(os.path.basename(p).lower(), (p, '<game folder>'))

    only_named = '--named' in sys.argv
    total = 0
    for name in active:
        if name.lower() in VANILLA:
            continue
        hit = index.get(name.lower())
        if not hit:
            continue
        path, mod = hit
        try:
            rows = scan(path)
        except Exception as exc:
            print('  !! %s: %s' % (name, exc))
            continue
        if only_named:
            rows = [r for r in rows if r[3]]
        if not rows:
            continue
        total += len(rows)
        print('%s   [%s]' % (name, mod))
        for kind, fid, edid, full in rows:
            print('    %-11s %08X  %-44s %s' % (kind, fid, edid[:44], full))
    print()
    print('total: %d power records across the active non-vanilla load order' % total)


if __name__ == '__main__':
    main()
