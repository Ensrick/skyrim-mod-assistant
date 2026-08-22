"""Which NPCs actually need facegen, and do they have it?

A raw NPC count overstates the need: creature records never use facegen, and
templated NPCs inherit a face. The reliable marker is the face-morph and
tint-layer subrecords (NAM9 / NAMA / TINI), which only humanoid NPCs with an
authored face carry. Missing facegen for those is the dark-face bug.
"""
import sys, os, glob, struct, zlib, io, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import modasset as M, esp
from worldspace import sources

FACE_SUBS = {b'NAM9', b'NAMA', b'TINI', b'TINC', b'TIAS'}


def check(mid, label, cache=None):
    root = os.path.join(M.CACHE, cache or
                        [x for x in os.listdir(M.CACHE) if x.startswith(f'x{mid}-')][0])
    plug = sorted(glob.glob(root + '/**/*.es[pm]', recursive=True),
                  key=lambda p: -os.path.getsize(p))[0]
    d = open(plug, 'rb').read()
    need = set()
    total = 0

    def walk(start, end):
        nonlocal total
        pos = start
        while pos + 24 <= end:
            typ = d[pos:pos + 4]
            size = struct.unpack_from('<I', d, pos + 4)[0]
            if typ == b'GRUP':
                walk(pos + 24, min(pos + size, end)); pos += size; continue
            flags = struct.unpack_from('<I', d, pos + 8)[0]
            formid = struct.unpack_from('<I', d, pos + 12)[0]
            if typ == b'NPC_':
                total += 1
                body = d[pos + 24:pos + 24 + size]
                if flags & 0x00040000 and len(body) > 4:
                    try: body = zlib.decompress(body[4:])
                    except zlib.error: body = b''
                subs = {st for st, _p in esp._subrecords(body)}
                if subs & FACE_SUBS:
                    need.add(formid & 0xFFFFFF)
            pos += 24 + size

    walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))
    names, _a = sources(root)
    have = set()
    for n, _x, _y in names:
        m = re.search(r'facegeom/[^/]+/([0-9a-fA-F]{8})\.nif$', n)
        if m:
            have.add(int(m.group(1), 16) & 0xFFFFFF)
    missing = need - have
    print(f'{label}: {total} NPC records, {len(need)} carry an authored face, '
          f'{len(have)} facegeom shipped')
    print(f'   missing facegen for {len(missing)} of them'
          + ('  <- dark-face candidates' if missing else '  (complete)'))


for mid, label, cache in ((45565, 'Wyrmstooth', None),
                          (2057, 'Falskaar', 'x2057-23605'),
                          (3008, 'Beyond Reach', 'x3008-626299')):
    try:
        check(mid, label, cache)
    except Exception as e:
        print(f'{label}: failed {str(e)[:90]}')
