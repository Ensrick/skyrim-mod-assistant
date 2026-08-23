"""Per-questline: how much recognition dialogue follows the character?

Aggregates hide the answer. What matters is, for each guild you might assign to
one character, whether the NPCs who greet you check faction membership (which
Proteus swaps) or quest progress (which every character shares).
"""
import sys, os, io, struct, zlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter, defaultdict
import esp

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
d = open(os.path.join(DATA, 'Skyrim.esm'), 'rb').read()

edid = {}
rtype = {}
infos = []


def walk(start, end):
    pos = start
    while pos + 24 <= end:
        typ = d[pos:pos + 4]
        size = struct.unpack_from('<I', d, pos + 4)[0]
        if typ == b'GRUP':
            walk(pos + 24, min(pos + size, end)); pos += size; continue
        flags = struct.unpack_from('<I', d, pos + 8)[0]
        formid = struct.unpack_from('<I', d, pos + 12)[0]
        rtype[formid] = typ
        body = d[pos + 24:pos + 24 + size]
        if flags & 0x00040000 and len(body) > 4:
            try: body = zlib.decompress(body[4:])
            except zlib.error: body = b''
        if typ in (b'FACT', b'QUST'):
            for st, pay in esp._subrecords(body):
                if st == b'EDID':
                    edid[formid] = pay.split(b'\x00')[0].decode('cp1252', 'replace')
                    break
        elif typ == b'INFO':
            c = [pay for st, pay in esp._subrecords(body) if st == b'CTDA']
            if c:
                infos.append(c)
        pos += 24 + size


walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))

GUILDS = [
    ('Thieves Guild',    r'^TG|Thieves'),
    ('Dark Brotherhood', r'^DB|DarkBrotherhood'),
    ('Companions',       r'^C0|Companions'),
    ('College of Winterhold', r'^MG|College'),
    ('Main quest / Dragonborn', r'^MQ|Dragonborn|Greybeard|Blades'),
    ('Civil War',        r'^CW|Stormcloak|Imperial'),
]

# which FormIDs belong to each guild, split by record type
groups = {name: {'FACT': set(), 'QUST': set()} for name, _p in GUILDS}
for fid, name in edid.items():
    for label, pat in GUILDS:
        if re.search(pat, name):
            t = rtype[fid].decode()
            if t in ('FACT', 'QUST'):
                groups[label][t].add(fid)
            break

tally = {name: Counter() for name, _p in GUILDS}
for ctdas in infos:
    hit = defaultdict(set)
    for c in ctdas:
        if len(c) < 20:
            continue
        for off in (12, 16):
            p = struct.unpack_from('<I', c, off)[0]
            for label, _pat in GUILDS:
                if p in groups[label]['FACT']:
                    hit[label].add('FACT')
                elif p in groups[label]['QUST']:
                    hit[label].add('QUST')
    for label, kinds in hit.items():
        if kinds == {'FACT'}:
            tally[label]['follows character'] += 1
        elif kinds == {'QUST'}:
            tally[label]['follows save'] += 1
        else:
            tally[label]['both'] += 1

print(f"{'questline':<26}{'char':>7}{'save':>7}{'both':>7}{'  % that follows the character'}")
for label, _pat in GUILDS:
    t = tally[label]
    tot = sum(t.values())
    if not tot:
        continue
    safe = t['follows character']
    print(f"{label:<26}{safe:>7}{t['follows save']:>7}{t['both']:>7}   {100*safe/tot:>5.0f}%")
