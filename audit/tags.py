"""Query the tag index built up by inspect_mod.

  py -3 tags.py                      what is indexed, and the tag vocabulary
  py -3 tags.py touches:clutter      everything writing into that domain
  py -3 tags.py flag:upscaled-textures
  py -3 tags.py --collisions         mods writing the same Data paths
  py -3 tags.py --collisions 5795    just this mod's collisions, file by file
"""
import sys, os, io, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter
import tagger


def show_index(idx):
    print(f'{len(idx)} mods indexed\n')
    for m, r in sorted(idx.items(), key=lambda x: -(x[1].get('size_mb') or 0)):
        print(f"  {m:<8}{r['size_mb']:>7} MB  {len(r['paths']):>5} files  {r['label'] or ''}")
    vocab = Counter(t for r in idx.values() for t in r['tags'])
    print(f'\ntag vocabulary ({len(vocab)} tags):')
    for grp in ('role', 'touches', 'tech', 'slot', 'flag'):
        row = [(t, n) for t, n in vocab.most_common() if t.startswith(grp + ':')]
        if row:
            print(f'  {grp}: ' + ', '.join(f'{t.split(":",1)[1]}({n})' for t, n in row))


def show_tag(idx, tag):
    hits = [(m, r) for m, r in idx.items() if any(t == tag or t.startswith(tag) for t in r['tags'])]
    print(f'{len(hits)} mods tagged {tag}\n')
    for m, r in sorted(hits, key=lambda x: -(x[1].get('size_mb') or 0)):
        print(f"  {m:<8}{r['label'] or '':<44}{r['size_mb']:>7} MB")
        others = [t for t in r['tags'] if t.startswith(('flag:', 'tech:parallax', 'tech:pbr'))]
        if others:
            print(f"           {' '.join(others)}")


def show_collisions(mid=None):
    pairs, shared, idx = tagger.collisions(mid)
    if not pairs:
        print('no path collisions among the indexed mods'
              + (f' involving {mid}' if mid else ''))
        return
    print(f'{len(pairs)} colliding pairs\n')
    for (a, b), n in pairs.most_common(20):
        la = idx[a]['label'] or a
        lb = idx[b]['label'] or b
        print(f'  {n:>5} shared files   {la[:32]:<34} vs  {lb[:32]}')
        if mid:
            files = [p for p, ms in shared.items() if a in ms and b in ms]
            for f in sorted(files)[:14]:
                print(f'            {f}')
            if len(files) > 14:
                print(f'            ... and {len(files)-14} more')


if __name__ == '__main__':
    args = sys.argv[1:]
    idx = tagger.load()
    if not args:
        show_index(idx)
    elif args[0] == '--collisions':
        show_collisions(args[1] if len(args) > 1 else None)
    else:
        show_tag(idx, args[0])
