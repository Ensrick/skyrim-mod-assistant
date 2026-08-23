"""How much of a mod sits inside vanilla Skyrim rather than its own space?

This decides whether a shared-quest-state leak is actually visible. A mod whose
NPCs all live in its own worldspace only over-recognises characters who travel
there. A mod that plants NPCs in Whiterun and Riften greets everyone, every
time they walk past.
"""
import sys, os, io, glob, struct, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter
import modasset as M, esp


def measure(mid, label, cache=None):
    root = os.path.join(M.CACHE, cache or
                        [x for x in os.listdir(M.CACHE) if x.startswith(f'x{mid}-')][0])
    plug = sorted(glob.glob(root + '/**/*.es[pm]', recursive=True),
                  key=lambda p: -os.path.getsize(p))[0]
    p = esp.Plugin(plug)
    d = open(plug, 'rb').read()
    nmast = len(p.masters)
    counts = Counter()

    def walk(start, end, cell=None):
        pos = start
        while pos + 24 <= end:
            typ = d[pos:pos + 4]
            size = struct.unpack_from('<I', d, pos + 4)[0]
            if typ == b'GRUP':
                gtype = struct.unpack_from('<I', d, pos + 12)[0]
                lbl = d[pos + 8:pos + 12]
                nxt = struct.unpack_from('<I', lbl, 0)[0] if gtype in (6, 7, 8, 9) else cell
                walk(pos + 24, min(pos + size, end), nxt)
                pos += size
                continue
            if typ in (b'ACHR', b'REFR'):
                # a cell whose FormID belongs to a master is vanilla Skyrim
                where = 'vanilla cell' if (cell is not None and (cell >> 24) < nmast) \
                        else 'own space'
                counts[(typ.decode(), where)] += 1
            pos += 24 + size

    walk(24 + struct.unpack_from('<I', d, 4)[0], len(d))
    achr_v = counts[('ACHR', 'vanilla cell')]
    achr_o = counts[('ACHR', 'own space')]
    refr_v = counts[('REFR', 'vanilla cell')]
    refr_o = counts[('REFR', 'own space')]
    tot_a = achr_v + achr_o
    print(f'{label:<24}NPCs placed: {achr_v:>5} in vanilla Skyrim, {achr_o:>6} in its own space'
          f'   ({100*achr_v/max(1,tot_a):>4.0f}% visible without travelling there)')
    print(f'{"":<24}objects:     {refr_v:>5} in vanilla Skyrim, {refr_o:>6} in its own space')


for mid, label, cache in ((11849, 'Vigilant', None), (45565, 'Wyrmstooth', None),
                          (3008, 'Beyond Reach', 'x3008-626299'),
                          (4341, 'Moonpath', None), (1179, 'Forgotten City', None)):
    try:
        measure(mid, label, cache)
    except Exception as e:
        print(f'{label}: failed {str(e)[:80]}')
