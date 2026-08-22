"""Measure a new-worldspace mod on the things that separate a built world from
a big empty one.

Two numbers do most of the work:

  built    - share of the mod's exterior cells that have anything placed in
             them, against vanilla Skyrim's 43% measured the same way. A large
             map with a low figure is the "empty and generic" feeling, quantified.
  authored - textures and meshes the author actually made, as opposed to
             facegen and terrain LOD, which the Creation Kit generates. A mod
             whose art is almost entirely generated is building with vanilla
             kit pieces, which is the other half of "generic".

Neither judges writing or quest design. Those need playing.
"""
import sys, os, glob, struct, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import modasset as M, esp

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
GENERATED = ('facegeom', 'facetint', '/terrain/')
LODEXT = ('.btr', '.bto', '.btt', '.lod')


def sources(root):
    """Every asset the mod ships, whether loose or inside its BSAs."""
    names, archives = [], []
    for f in glob.glob(root + '/**/*', recursive=True):
        if os.path.isdir(f):
            continue
        if f.lower().endswith('.bsa'):
            try:
                a = M.BSA(f)
            except Exception:
                continue
            archives.append(a)
            names += [(n.replace('\\', '/').lower(), a, i)
                      for i, (n, _o, _s) in enumerate(a.entries)]
        else:
            names.append((M.data_rel(os.path.relpath(f, root)), None, f))
    return names, archives


def measure(mid, label, cache_prefix=None):
    root = os.path.join(M.CACHE, cache_prefix or
                        [x for x in os.listdir(M.CACHE) if x.startswith(f'x{mid}-')][0])
    plugins = sorted(glob.glob(root + '/**/*.es[pm]', recursive=True))
    if not plugins:
        print(f'{label}: no plugin found'); return
    plugins.sort(key=lambda p: -os.path.getsize(p))
    p = esp.Plugin(plugins[0])

    ext = [c['refs'] for c in p.cells.values() if c['interior'] is False]
    inte = [c['refs'] for c in p.cells.values() if c['interior'] is True]
    live = sorted(c for c in ext if c > 0)
    print(f'\n{"="*72}\n{label}  (mod {mid})')
    print(f'   plugin {os.path.basename(plugins[0])} '
          f'{os.path.getsize(plugins[0])/1048576:.1f} MB, masters {p.masters}')
    print(f'   {len(p.formids):,} records, {len(p.overrides):,} override the base game, '
          f'{len(p.deleted)} deleted (UDR)')
    print(f'   {len(ext):,} exterior cells, {len(live):,} built '
          f'({100*len(live)/max(1,len(ext)):.0f}%; vanilla Skyrim is 43%)')
    if live:
        print(f'   refs per built cell: median {live[len(live)//2]}, '
              f'mean {sum(live)/len(live):.0f}   (vanilla median 24, mean 41)')
    print(f'   {len(inte):,} interiors, {p.navmesh:,} navmeshes, '
          f'{len(p.quests)} quests / {sum(n for _f, n in p.quests)} aliases')

    names, _arcs = sources(root)
    tex = [n for n, _a, _i in names if n.endswith('.dds')]
    nif = [n for n, _a, _i in names if n.endswith('.nif')]
    lod = [n for n, _a, _i in names if n.endswith(LODEXT)]
    fuz = [n for n, _a, _i in names if n.endswith('.fuz')]
    gen_t = [n for n in tex if any(g in n for g in GENERATED)]
    gen_m = [n for n in nif if any(g in n for g in GENERATED)]
    print(f'   assets: {len(tex):,} textures ({len(tex)-len(gen_t):,} authored, '
          f'{len(gen_t):,} generated), {len(nif):,} meshes '
          f'({len(nif)-len(gen_m):,} authored, {len(gen_m):,} generated), '
          f'{len(lod):,} LOD files')
    if fuz:
        voices = Counter(n.split('/')[3] for n in fuz if len(n.split('/')) > 3)
        print(f'   voice: {len(fuz):,} files across {len(voices)} voice types')
    else:
        print('   voice: none shipped')

    # mesh format, authored meshes only
    vers = Counter()
    for n, a, i in names:
        if not n.endswith('.nif') or any(g in n for g in GENERATED):
            continue
        try:
            blob = a.read(i) if a else open(i, 'rb').read()
            info = M.nif_info(blob)
        except Exception:
            continue
        if info:
            vers[info['ver']] += 1
    if vers:
        old = sum(v for k, v in vers.items() if k != '100')
        print(f'   authored mesh format: ' + ', '.join(f'v{k}({v})' for k, v in vers.most_common())
              + (f'   -> {old} still Oldrim' if old else '   -> all SSE format'))


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        mid, label = arg.split(':', 1)
        try:
            measure(int(mid), label)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f'{label}: failed {str(e)[:120]}')
