"""Voice coverage and facegen completeness for any measured mod.

Standalone so importing it never drags another script's module-level output
along with it.
"""
import sys, os, io, glob, struct, zlib, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import modasset as M, esp
from worldspace import sources

FACE_SUBS = {b'NAM9', b'NAMA', b'TINI', b'TINC', b'TIAS'}


def scan(plug):
    d = open(plug, 'rb').read()
    infos, faces = [], set()

    def walk(start, end):
        pos = start
        while pos + 24 <= end:
            typ = d[pos:pos + 4]
            size = struct.unpack_from('<I', d, pos + 4)[0]
            if typ == b'GRUP':
                walk(pos + 24, min(pos + size, end)); pos += size; continue
            flags = struct.unpack_from('<I', d, pos + 8)[0]
            formid = struct.unpack_from('<I', d, pos + 12)[0]
            if typ in (b'INFO', b'NPC_'):
                body = d[pos + 24:pos + 24 + size]
                if flags & 0x00040000 and len(body) > 4:
                    try: body = zlib.decompress(body[4:])
                    except zlib.error: body = b''
                if typ == b'INFO':
                    infos.append(formid & 0xFFFFFF)
                elif {st for st, _p in esp._subrecords(body)} & FACE_SUBS:
                    faces.add(formid & 0xFFFFFF)
            pos += 24 + size

    walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))
    return infos, faces


def check(mid, label, cache=None):
    root = os.path.join(M.CACHE, cache or
                        [x for x in os.listdir(M.CACHE) if x.startswith(f'x{mid}-')][0])
    plug = sorted(glob.glob(root + '/**/*.es[pm]', recursive=True),
                  key=lambda p: -os.path.getsize(p))[0]
    infos, faces = scan(plug)
    names, _a = sources(root)
    voiced, geom = set(), set()
    for n, _x, _y in names:
        m = re.search(r'_([0-9a-fA-F]{8})_1\.fuz$', n)
        if m:
            voiced.add(int(m.group(1), 16) & 0xFFFFFF)
        g = re.search(r'facegeom/[^/]+/([0-9a-fA-F]{8})\.nif$', n)
        if g:
            geom.add(int(g.group(1), 16) & 0xFFFFFF)
    ids = set(infos)
    print(f'{label}:')
    print(f'   {len(ids):,} INFO records, {len(ids & voiced):,} voiced '
          f'({100*len(ids & voiced)/max(1,len(ids)):.0f}%)')
    miss = faces - geom
    print(f'   {len(faces)} NPCs with an authored face, {len(geom)} facegeom shipped, '
          f'{len(miss)} missing')


if __name__ == '__main__':
    for a in sys.argv[1:]:
        parts = a.split(':')
        try:
            check(int(parts[0]), parts[1] if len(parts) > 1 else parts[0],
                  parts[2] if len(parts) > 2 else None)
        except Exception as e:
            print(f'{a}: failed {str(e)[:90]}')
