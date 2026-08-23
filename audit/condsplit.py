"""How much vanilla dialogue keys on faction versus quest state?

This decides how well a multi-protagonist save can work. Under Proteus the
player's factions are swapped per character, so faction-gated dialogue follows
whoever you are playing. Quest stages are global game state, so quest-gated
dialogue leaks: every character sees the world as though one of them did
everything.

Rather than rely on a table of condition-function indices, this resolves the
FormIDs each condition references back to their record type in Skyrim.esm. A
condition pointing at a FACT record is faction logic; one pointing at a QUST
record is quest logic. That is self-verifying and needs no external mapping.
"""
import sys, os, io, struct, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter
import esp

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
d = open(os.path.join(DATA, 'Skyrim.esm'), 'rb').read()

types = {}          # formid -> record type
infos = []          # (formid, [raw CTDA blocks])


def walk(start, end):
    pos = start
    while pos + 24 <= end:
        typ = d[pos:pos + 4]
        size = struct.unpack_from('<I', d, pos + 4)[0]
        if typ == b'GRUP':
            walk(pos + 24, min(pos + size, end))
            pos += size
            continue
        flags = struct.unpack_from('<I', d, pos + 8)[0]
        formid = struct.unpack_from('<I', d, pos + 12)[0]
        types[formid] = typ
        if typ == b'INFO':
            body = d[pos + 24:pos + 24 + size]
            if flags & 0x00040000 and len(body) > 4:
                try: body = zlib.decompress(body[4:])
                except zlib.error: body = b''
            ctdas = [pay for st, pay in esp._subrecords(body) if st == b'CTDA']
            if ctdas:
                infos.append((formid, ctdas))
        pos += 24 + size


walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))
print(f'{len(types):,} records indexed, {len(infos):,} dialogue lines carry conditions')

# CTDA: flags(1) unused(3) value(4) function(2) pad(2) param1(4) param2(4)
#       runOn(4) reference(4) unknown(4)
per_info = Counter()
cond_kinds = Counter()
for formid, ctdas in infos:
    kinds = set()
    for c in ctdas:
        if len(c) < 20:
            continue
        for off in (12, 16):
            p = struct.unpack_from('<I', c, off)[0]
            t = types.get(p)
            if t in (b'FACT', b'QUST'):
                kinds.add(t)
                cond_kinds[t] += 1
    if kinds == {b'FACT'}:
        per_info['faction only'] += 1
    elif kinds == {b'QUST'}:
        per_info['quest only'] += 1
    elif kinds == {b'FACT', b'QUST'}:
        per_info['both'] += 1
    else:
        per_info['neither'] += 1

total = sum(per_info.values())
print(f'\nconditioned dialogue lines by what they key on:')
for k in ('faction only', 'quest only', 'both', 'neither'):
    n = per_info[k]
    print(f'   {k:<14}{n:>7,}  {100*n/total:>5.1f}%')
print(f'\nindividual condition references: '
      f'FACT {cond_kinds[b"FACT"]:,}, QUST {cond_kinds[b"QUST"]:,}')

follows = per_info['faction only']
leaks = per_info['quest only'] + per_info['both']
print(f'\nof the {follows+leaks:,} lines that key on either:')
print(f'   {100*follows/(follows+leaks):.0f}% follow the character (faction, swapped by Proteus)')
print(f'   {100*leaks/(follows+leaks):.0f}% follow the save (quest state, shared by everyone)')
