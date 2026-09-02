r"""Find env-mapped shapes whose env-mask (or cubemap) texture nothing in the load order ships.

Born from #159: Skyking Signs' "03 Parallax" meshes give sign posts an
EnvironmentMap shader whose env-mask slot names a texture that no mod, no
enabled-mod BSA and no vanilla/CC BSA contains. With Community Shaders'
Dynamic Cubemaps that paints the wood as slick, wet-looking gloss. This tool
sweeps every enabled mod's LOOSE meshes for the same defect class.

For each loose ``meshes/**/*.nif`` in every enabled mod of the profile (MO2
priority order, ``overwrite/`` on top), every ``BSLightingShaderProperty``
that is EnvironmentMap-typed (shader type 1), EyeEnvmap-typed (15) or carries
SLSF1 ``Environment_Mapping`` (bit 7) is decoded together with its
``BSShaderTextureSet``; slot 4 (cubemap) and slot 5 (env mask) are resolved
against, in this order:

1. loose files of ``overwrite/`` and every enabled mod (priority order),
2. every ``*.bsa`` inside an enabled mod folder or ``overwrite/``,
3. the game's own ``Data\*.bsa`` (vanilla + Creation Club) and loose Data files.

Scope: only LOOSE NIFs are parsed. NIFs packed in mod BSAs and in the vanilla
BSAs are not opened on this pass (the record says so). Texture resolution
does cover all BSAs by name.

    py -3 audit/envmask_scan.py [--json OUT.json] [--md OUT.md] [--index CACHE.json]

``--index`` caches the BSA name tables (one JSON) so a re-run does not re-read
150 archives. Exit 0 always; the report is the product.
"""
from __future__ import annotations

import argparse
import ctypes
import glob
import io
import json
import os
import struct
import sys
import time
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import modasset as M  # noqa: E402

INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = 'Default'
DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'

SHADER_TYPE = {0: 'Default', 1: 'EnvironmentMap', 2: 'GlowShader', 3: 'Parallax',
               4: 'FaceTint', 5: 'SkinTint', 6: 'HairTint', 7: 'ParallaxOcc',
               8: 'MultitextureLandscape', 9: 'LODLandscape', 10: 'Snow',
               11: 'MultiLayerParallax', 12: 'TreeAnim', 13: 'LODObjects',
               14: 'SparkleSnow', 15: 'EyeEnvmap', 16: 'Cloud',
               17: 'LODLandscapeNoise', 18: 'MultitextureLandscapeLODBlend', 19: 'FX'}
SLSF1_ENVIRONMENT_MAPPING = 1 << 7      # nif.xml SkyrimShaderPropertyFlags1 bit 7
SLSF1_EYE_ENVIRONMENT_MAPPING = 1 << 17
SLOT_CUBEMAP, SLOT_ENVMASK = 4, 5


def low_priority():
    try:
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)   # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        pass


# ---------------------------------------------------------------- NIF blocks
def nif_blocks(data):
    """(strings, [(block type, block bytes)]) for a Skyrim SE / LE NIF, else None."""
    if not data.startswith(b'Gamebryo File Format'):
        return None
    nl = data.index(b'\n')
    p = nl + 1
    _ver, _endian, _uver, nblocks, uver2 = struct.unpack_from('<IBIII', data, p)
    p += 17
    for _ in range(2):
        ln = data[p]; p += 1 + ln
    ln = data[p]; p += 1 + ln
    if uver2 >= 130:
        ln = struct.unpack_from('<I', data, p)[0]; p += 4 + ln
    ntypes = struct.unpack_from('<H', data, p)[0]; p += 2
    types = []
    for _ in range(ntypes):
        n = struct.unpack_from('<I', data, p)[0]
        types.append(data[p + 4:p + 4 + n].decode('cp1252', 'replace')); p += 4 + n
    idx = struct.unpack_from('<%dH' % nblocks, data, p); p += 2 * nblocks
    sizes = struct.unpack_from('<%dI' % nblocks, data, p); p += 4 * nblocks
    nstr, _m = struct.unpack_from('<II', data, p); p += 8
    strings = []
    for _ in range(nstr):
        n = struct.unpack_from('<I', data, p)[0]
        strings.append(data[p + 4:p + 4 + n].decode('cp1252', 'replace')); p += 4 + n
    ngroups = struct.unpack_from('<I', data, p)[0]; p += 4 + 4 * ngroups
    out = []
    for i, bi in enumerate(idx):
        out.append((types[bi], data[p:p + sizes[i]]))
        p += sizes[i]
    return strings, out


def texture_set(b):
    n = struct.unpack_from('<I', b, 0)[0]
    q = 4
    paths = []
    for _ in range(n):
        ln = struct.unpack_from('<I', b, q)[0]
        paths.append(b[q + 4:q + 4 + ln].decode('cp1252', 'replace')); q += 4 + ln
    return paths


def lighting_shader(b, strings):
    """shaderType, name, SLSF1, SLSF2, texture-set block ref, EnvMapScale.

    Layout (Skyrim SE, BSLightingShaderProperty): shaderType u32, name (string
    index i32), extra-data count + refs, controller ref, SLSF1, SLSF2, UV
    offset (2f), UV scale (2f), textureSet ref, emissive (3f), emissive mult,
    texture clamp, alpha, refraction strength, glossiness, specular (3f),
    specular strength, lighting effect 1/2, then type-specific: for type 1 the
    next float is Environment Map Scale."""
    styp = struct.unpack_from('<I', b, 0)[0]
    nref = struct.unpack_from('<i', b, 4)[0]
    name = strings[nref] if 0 <= nref < len(strings) else ''
    q = 8
    ne = struct.unpack_from('<I', b, q)[0]; q += 4 + 4 * ne
    q += 4                                        # controller
    sf1, sf2 = struct.unpack_from('<II', b, q); q += 8
    q += 16                                       # uv offset + scale
    tsref = struct.unpack_from('<i', b, q)[0]; q += 4
    q += 12 + 4 + 4                               # emissive colour, mult, clamp
    q += 12                                       # alpha, refraction, glossiness
    q += 12 + 4                                   # specular colour, strength
    q += 8                                        # lighting effect 1, 2
    envscale = None
    if styp == 1 and q + 4 <= len(b):
        envscale = struct.unpack_from('<f', b, q)[0]
    return styp, name, sf1, sf2, tsref, envscale


def norm_tex(p):
    """Engine-style key: lowercase, forward slashes, 'textures/' prefixed."""
    k = p.replace('\\', '/').strip().lower().lstrip('/')
    if k.startswith('data/'):
        k = k[5:]
    if k and not k.startswith('textures/'):
        k = 'textures/' + k
    return k


# ---------------------------------------------------------------- load order
def enabled_mods():
    """Enabled mod names, highest priority first (MO2 modlist.txt order)."""
    ml = os.path.join(INSTANCE, 'profiles', PROFILE, 'modlist.txt')
    out = []
    for line in open(ml, encoding='utf-8-sig'):
        line = line.rstrip('\r\n')
        if line.startswith('+'):
            out.append(line[1:])
    return out


def walk_sources():
    """[(label, root dir)] highest priority first; overwrite on top."""
    srcs = [('overwrite', os.path.join(INSTANCE, 'overwrite'))]
    for m in enabled_mods():
        srcs.append((m, os.path.join(INSTANCE, 'mods', m)))
    return srcs


def index_loose(sources):
    """path key -> winning source label; also nif list per source and BSAs found."""
    win = {}
    nifs = defaultdict(list)
    bsas = []
    for label, root in sources:
        if not os.path.isdir(root):
            continue
        rl = len(root) + 1
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith('.')]
            for f in fn:
                full = os.path.join(dp, f)
                rel = full[rl:].replace('\\', '/').lower()
                if rel.endswith('.bsa') and '/' not in rel:
                    bsas.append((label, full))
                    continue
                if rel not in win:
                    win[rel] = label
                if rel.startswith('meshes/') and rel.endswith('.nif'):
                    nifs[label].append((rel, full))
    return win, nifs, bsas


def index_bsas(paths, cache=None):
    """path key -> archive label for every entry of every archive."""
    idx = {}
    cached = {}
    if cache and os.path.exists(cache):
        try:
            cached = json.load(open(cache, encoding='utf-8'))
        except Exception:
            cached = {}
    fresh = {}
    for label, p in paths:
        st = os.stat(p)
        key = f'{p}|{st.st_size}|{int(st.st_mtime)}'
        names = cached.get(key)
        if names is None:
            try:
                names = M.BSA(p).names()
            except Exception as e:
                print(f'  !! {p}: {e}', file=sys.stderr)
                names = []
        fresh[key] = names
        for n in names:
            k = n.replace('\\', '/').lower()
            idx.setdefault(k, label)
    if cache:
        json.dump(fresh, open(cache, 'w', encoding='utf-8'), separators=(',', ':'))
    return idx


# ---------------------------------------------------------------- main
def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', help='write full results here')
    ap.add_argument('--md', help='write the markdown table here')
    ap.add_argument('--index', help='BSA name-table cache (JSON)')
    ap.add_argument('--all-shapes', action='store_true',
                    help='also list env-mapped shapes whose mask resolves (for calibration)')
    args = ap.parse_args(argv)
    low_priority()
    t0 = time.time()

    sources = walk_sources()
    win, nifs, mod_bsas = index_loose(sources)
    t1 = time.time()
    print(f'loose: {len(sources)} sources, {len(win)} files, '
          f'{sum(len(v) for v in nifs.values())} loose NIFs, {len(mod_bsas)} mod BSAs  [{t1 - t0:.0f}s]')

    vanilla_bsas = [(f'vanilla:{os.path.basename(p)}', p)
                    for p in sorted(glob.glob(os.path.join(DATA, '*.bsa')))]
    bsa_idx = index_bsas([(f'bsa:{l}:{os.path.basename(p)}', p) for l, p in mod_bsas] + vanilla_bsas,
                         cache=args.index)
    # vanilla loose Data files (rare, but they resolve too)
    vloose = 0
    for f in glob.glob(os.path.join(DATA, 'textures', '**', '*'), recursive=True):
        if os.path.isfile(f):
            rel = os.path.relpath(f, DATA).replace('\\', '/').lower()
            bsa_idx.setdefault(rel, 'vanilla:loose')
            vloose += 1
    t2 = time.time()
    print(f'bsa index: {len(mod_bsas)} mod + {len(vanilla_bsas)} vanilla archives, '
          f'{len(bsa_idx)} entries (+{vloose} vanilla loose)  [{t2 - t1:.0f}s]')

    def resolve(key):
        if key in win:
            return 'loose:' + win[key]
        if key in bsa_idx:
            return bsa_idx[key]
        return None

    missing = []          # one row per (nif, shape) with an unresolved slot
    resolved_rows = []
    counts = defaultdict(lambda: defaultdict(int))
    parsed = failed = envshapes = 0
    for label, lst in nifs.items():
        for rel, full in lst:
            try:
                data = open(full, 'rb').read()
                r = nif_blocks(data)
            except Exception:
                failed += 1
                continue
            if r is None:
                failed += 1
                continue
            parsed += 1
            strings, blks = r
            for i, (t, b) in enumerate(blks):
                if t != 'BSLightingShaderProperty':
                    continue
                try:
                    styp, name, sf1, sf2, tsref, envscale = lighting_shader(b, strings)
                except Exception:
                    continue
                envmapped = styp in (1, 15) or bool(sf1 & (SLSF1_ENVIRONMENT_MAPPING | SLSF1_EYE_ENVIRONMENT_MAPPING))
                if not envmapped or not (0 <= tsref < len(blks)) or blks[tsref][0] != 'BSShaderTextureSet':
                    continue
                paths = texture_set(blks[tsref][1])
                envshapes += 1
                mask = paths[SLOT_ENVMASK] if len(paths) > SLOT_ENVMASK else ''
                cube = paths[SLOT_CUBEMAP] if len(paths) > SLOT_CUBEMAP else ''
                diffuse = paths[0] if paths else ''
                row = {'mod': label, 'nif': rel, 'block': i, 'shaderType': SHADER_TYPE.get(styp, str(styp)),
                       'envMapScale': None if envscale is None else round(envscale, 3),
                       'diffuse': diffuse, 'cubemap': cube, 'mask': mask,
                       'winner': win.get(rel), 'shadowed': win.get(rel) != label}
                bad = False
                if mask:
                    mk = norm_tex(mask)
                    row['maskSource'] = resolve(mk)
                    if row['maskSource'] is None:
                        bad = True
                        counts[label]['mask'] += 1
                else:
                    row['maskSource'] = '(empty slot)'
                if cube:
                    ck = norm_tex(cube)
                    row['cubemapSource'] = resolve(ck)
                    if row['cubemapSource'] is None:
                        bad = True
                        counts[label]['cubemap'] += 1
                else:
                    row['cubemapSource'] = '(empty slot)'
                if bad:
                    missing.append(row)
                elif args.all_shapes:
                    resolved_rows.append(row)
    t3 = time.time()
    print(f'parsed {parsed} loose NIFs ({failed} unreadable), {envshapes} env-mapped shapes, '
          f'{len(missing)} shapes with an unresolved slot  [{t3 - t2:.0f}s]')

    # group by mod -> missing mask path -> nif list
    by_mod = defaultdict(lambda: defaultdict(set))
    for r in missing:
        if r['mask'] and r['maskSource'] is None:
            by_mod[r['mod']][('mask', norm_tex(r['mask']))].add(r['nif'])
        if r['cubemap'] and r['cubemapSource'] is None:
            by_mod[r['mod']][('cubemap', norm_tex(r['cubemap']))].add(r['nif'])

    lines = []
    lines.append('| Mod | Slot | Missing texture | NIFs | Shadowed | Example NIF |')
    lines.append('|---|---|---|---:|---|---|')
    for mod in sorted(by_mod, key=str.lower):
        for (slot, tex), nset in sorted(by_mod[mod].items()):
            shadowed = all(win.get(n) != mod for n in nset)
            lines.append(f'| {mod} | {slot} | `{tex}` | {len(nset)} | '
                         f'{"all" if shadowed else ("some" if any(win.get(n) != mod for n in nset) else "no")} | '
                         f'`{sorted(nset)[0]}` |')
    table = '\n'.join(lines)
    print()
    print(table)
    summary = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'instance': INSTANCE, 'profile': PROFILE,
        'sources': len(sources), 'looseFiles': len(win),
        'looseNifs': sum(len(v) for v in nifs.values()), 'parsed': parsed, 'unreadable': failed,
        'modBsas': len(mod_bsas), 'vanillaBsas': len(vanilla_bsas), 'bsaEntries': len(bsa_idx),
        'envMappedShapes': envshapes, 'shapesMissing': len(missing),
        'modsMissing': {m: dict(c) for m, c in counts.items()},
        'seconds': {'loose': round(t1 - t0, 1), 'bsa': round(t2 - t1, 1), 'nif': round(t3 - t2, 1),
                    'total': round(t3 - t0, 1)},
    }
    print()
    print(json.dumps(summary, indent=1))
    if args.json:
        json.dump({'summary': summary, 'missing': missing, 'resolved': resolved_rows,
                   'modBsas': [p for _l, p in mod_bsas]},
                  open(args.json, 'w', encoding='utf-8'), indent=1)
    if args.md:
        open(args.md, 'w', encoding='utf-8').write(table + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
