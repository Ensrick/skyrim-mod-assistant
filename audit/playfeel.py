"""Detect the failure mode that acclaim hides: a mod that reviews well and
plays badly.

Calibrated against The Forgotten City, which the user played, disliked for
exactly these reasons, and excluded. Four signals, all read from the files:

  confinement  - scripts that take fast travel or player control away, and how
                 much of the mod's space you are locked inside while they hold
  navigation   - quest objectives with no targeted alias. An objective with no
                 target puts no marker on the compass, which is the "search the
                 whole area for the one person you need" complaint
  traversal    - cells and placed references per quest, i.e. how much walking
                 the content is spread across
  visual       - authored art, so "bland next to the rest of my game" has a
                 number

None of this judges writing. It judges whether the thing is pleasant to move
through, which is what acclaim tends to overlook.
"""
import sys, os, re, io, glob, struct, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter
import modasset as M, esp
from worldspace import sources

GEN = ('facegeom', 'facetint', '/terrain/')
# Papyrus calls that take agency away from the player
CONFINE = [
    (b'EnableFastTravel',   'fast travel toggled off'),
    (b'SetPlayerAIDriven',  'player control handed to AI'),
    (b'ForceThirdPerson',   'camera forced'),
    (b'DisablePlayerControls', 'player controls disabled'),
    (b'SetRestrained',      'player restrained'),
    (b'LockDoor',           'doors locked by script'),
    (b'SetDestroyed',       'exits destroyed'),
    (b'BlockActivation',    'activation blocked'),
]


def measure(mid, label, cache=None):
    root = os.path.join(M.CACHE, cache or
                        [x for x in os.listdir(M.CACHE) if x.startswith(f'x{mid}-')][0])
    names, _a = sources(root)
    plug = sorted(glob.glob(root + '/**/*.es[pm]', recursive=True),
                  key=lambda p: -os.path.getsize(p))[0]
    p = esp.Plugin(plug)
    d = open(plug, 'rb').read()

    # ---- navigation: objectives and whether they have targets
    objectives = targeted = 0

    def walk(start, end):
        nonlocal objectives, targeted
        pos = start
        while pos + 24 <= end:
            typ = d[pos:pos + 4]
            size = struct.unpack_from('<I', d, pos + 4)[0]
            if typ == b'GRUP':
                walk(pos + 24, min(pos + size, end)); pos += size; continue
            flags = struct.unpack_from('<I', d, pos + 8)[0]
            if typ == b'QUST':
                body = d[pos + 24:pos + 24 + size]
                if flags & 0x00040000 and len(body) > 4:
                    try: body = zlib.decompress(body[4:])
                    except zlib.error: body = b''
                cur = None
                for st, pay in esp._subrecords(body):
                    if st == b'QOBJ':
                        if cur is not None:
                            objectives += 1
                            targeted += 1 if cur else 0
                        cur = False
                    elif st == b'QSTA' and cur is not None:
                        cur = True          # this objective points at an alias
                if cur is not None:
                    objectives += 1
                    targeted += 1 if cur else 0
            pos += 24 + size

    walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))

    # ---- confinement
    hits = Counter()
    pex = [(n, a, i) for n, a, i in names if n.endswith('.pex')]
    for n, a, i in pex:
        try:
            b = a.read(i) if a else open(i, 'rb').read()
        except Exception:
            continue
        for needle, desc in CONFINE:
            if needle in b:
                hits[desc] += 1

    # ---- traversal and shape
    ext = [c for c in p.cells.values() if c['interior'] is False and c['refs'] > 0]
    inte = [c for c in p.cells.values() if c['interior'] is True and c['refs'] > 0]
    quests = max(1, len(p.quests))
    auth_t = [n for n, _x, _y in names
              if n.endswith('.dds') and not any(g in n for g in GEN)]
    auth_m = [n for n, _x, _y in names
              if n.endswith('.nif') and not any(g in n for g in GEN)]
    fuz = [n for n, _x, _y in names if n.endswith('.fuz')]

    print(f'\n{"="*72}\n{label} (mod {mid})')
    print(f'   {len(p.quests)} quests, {len(inte)} built interiors, {len(ext)} built exteriors, '
          f'{p.refs:,} placed refs')
    print(f'   per quest: {(len(inte)+len(ext))/quests:.1f} cells, {p.refs/quests:.0f} refs')
    if objectives:
        print(f'   NAVIGATION: {objectives} quest objectives, {targeted} point at a target '
              f'({100*targeted/objectives:.0f}%); {objectives-targeted} put no marker on your compass')
    print(f'   CONFINEMENT: {len(pex)} scripts; ' +
          (', '.join(f'{k} ({v})' for k, v in hits.most_common()) if hits else 'no control-removal calls'))
    print(f'   ART: {len(auth_t)} authored textures, {len(auth_m)} authored meshes, '
          f'{len(fuz)} voice files')


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        mid, label = arg.split(':', 1)
        try:
            measure(int(mid), label)
        except Exception as e:
            print(f'{label}: failed {str(e)[:110]}')
