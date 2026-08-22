"""Index everything the game itself ships, from its own BSAs plus loose Data files.

This is the baseline every replacer is measured against: it says which paths are
vanilla assets (so a mod touching them is a replacer, not new content) and what
the vanilla resolution / triangle count is, so "4K" and "higher poly" become
checkable numbers instead of marketing.
"""
import json, os, sys, io, glob, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import modasset as M

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
OUT = os.path.join(SP, 'vanilla_index.json')
DEEP = {'.dds', '.nif'}

def main():
    idx = {}
    t0 = time.time()
    for p in sorted(glob.glob(os.path.join(DATA, '*.bsa'))):
        try:
            b = M.BSA(p)
        except Exception as e:
            print(f'  !! {os.path.basename(p)}: {e}'); continue
        base = os.path.basename(p)
        deep = ok = err = 0
        for i, (name, _o, szf) in enumerate(b.entries):
            key = name.replace('\\', '/').lower()
            ext = os.path.splitext(key)[1]
            rec = {'src': base, 'size': szf & 0x3FFFFFFF}
            if ext in DEEP:
                try:
                    blob = b.read(i, head=True)
                    if ext == '.dds':
                        d = M.dds_info(blob[:148])
                        if d: rec.update(d)
                    else:
                        # meshes are small; a head read usually holds the whole file
                        full = blob if len(blob) >= (szf & 0x3FFFFFFF) else b.read(i)
                        n = M.nif_info(full)
                        if n: rec.update({'shapes': n['shapes'], 'tris': n['tris'], 'verts': n['verts']})
                    ok += 1
                except Exception:
                    err += 1
                deep += 1
            idx[key] = rec
        print(f'  {base:<44}{len(b.entries):>7} entries  deep={deep} ok={ok} err={err}  [{time.time()-t0:.0f}s]', flush=True)

    loose = 0
    for f in glob.glob(os.path.join(DATA, '**', '*'), recursive=True):
        if os.path.isdir(f): continue
        rel = os.path.relpath(f, DATA).replace('\\', '/').lower()
        if rel.endswith(('.bsa', '.esm', '.esp', '.esl', '.ini', '.txt')): continue
        idx.setdefault(rel, {'src': 'loose', 'size': os.path.getsize(f)})
        loose += 1
    print(f'  loose Data files: {loose}')

    json.dump(idx, open(OUT, 'w'), separators=(',', ':'))
    tex = sum(1 for k in idx if k.endswith('.dds'))
    nif = sum(1 for k in idx if k.endswith('.nif'))
    print(f'\nvanilla index: {len(idx):,} paths ({tex:,} dds, {nif:,} nif) -> {OUT}')
    print(f'elapsed {time.time()-t0:.0f}s')

main()
