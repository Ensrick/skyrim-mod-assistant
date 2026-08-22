"""Inspect what a mod actually ships and report findings. No verdicts.

Output is a findings sheet: inventory, which modern features are supported,
concrete warning signs with the offending file named, and any community patches
that already fill the gaps. Whether that adds up to a keep is the user's call.

Every finding must name evidence. "Looks dated" is not a finding; "42 of 47
normal maps are BC1, which bands" is.
"""
import json, os, re, sys, io, glob, struct, subprocess, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modasset as M
import esp
import tagger

SP = os.path.dirname(os.path.abspath(__file__))
TEXCONV = os.path.join(os.environ['LOCALAPPDATA'],
                       r'Microsoft\WinGet\Packages\Microsoft.DirectXTex.Texconv_Microsoft.Winget.Source_8wekyb3d8bbwe\texconv.exe')

# ------------------------------------------------------------------ decoding
def decode_dds(blob, tmpname='t.dds'):
    """DDS bytes -> numpy array (H,W,C) uint8. Pillow first, texconv as fallback
    for BC7 and other formats Pillow will not touch."""
    import numpy as np
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(blob))
        im.load()
        return np.asarray(im.convert('RGBA'))
    except Exception:
        pass
    if not os.path.exists(TEXCONV):
        return None
    work = os.path.join(os.environ['TEMP'], 'ddsdec')
    os.makedirs(work, exist_ok=True)
    src = os.path.join(work, tmpname)
    open(src, 'wb').write(blob)
    subprocess.run([TEXCONV, '-ft', 'png', '-o', work, '-y', '-nologo', src],
                   capture_output=True)
    png = os.path.splitext(src)[0] + '.PNG'
    if not os.path.exists(png):
        png = os.path.splitext(src)[0] + '.png'
    if not os.path.exists(png):
        return None
    import numpy as np
    a = np.asarray(Image.open(png).convert('RGBA'))
    try: os.remove(png)
    except OSError: pass
    return a


# ------------------------------------------------------- texture diagnostics
def effective_resolution(gray):
    """How much real detail is present, independent of stored size.

    Halve the image, scale it back up, and see how much differs. Authored detail
    is destroyed by that round trip; upscaled or blurry content survives it
    almost unchanged, which is what exposes a '4K' texture carrying 1K of
    information."""
    import numpy as np
    from PIL import Image
    im = Image.fromarray(gray)
    w, h = im.size
    if min(w, h) < 64:
        return None
    small = im.resize((w // 2, h // 2), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    d = np.abs(np.asarray(small, dtype=np.int16) - gray.astype(np.int16))
    return float(d.mean())


def jpeg_blocking(gray):
    """Energy at the 8-pixel grid versus its neighbours. JPEG sources leave a
    periodic seam that survives recompression to DDS."""
    import numpy as np
    g = gray.astype(np.float32)
    dv = np.abs(np.diff(g, axis=1))
    if dv.shape[1] < 24:
        return None
    cols = dv.mean(axis=0)
    grid = cols[7::8].mean()
    off = np.delete(cols, np.s_[7::8]).mean()
    return float(grid / off) if off > 0.01 else None


def sharpen_halo(gray):
    """Unsharp masking leaves symmetric over/undershoot either side of an edge.
    Authored detail does not ring like that, so this catches the upscale-then-
    sharpen trick that the detail index alone cannot separate from real work."""
    import numpy as np
    from scipy import ndimage
    g = gray.astype(np.float32)
    if min(g.shape) < 64:
        return None
    blur = ndimage.uniform_filter(g, 3)
    hi = g - blur
    edges = ndimage.sobel(ndimage.gaussian_filter(g, 1.2))
    strong = np.abs(edges) > np.percentile(np.abs(edges), 97)
    if strong.sum() < 64:
        return None
    near = ndimage.binary_dilation(strong, iterations=2) & ~strong
    if near.sum() < 64:
        return None
    # ringing shows up as high-frequency energy hugging edges, signed both ways
    ring = hi[near]
    pos = float((ring > 3).mean()); neg = float((ring < -3).mean())
    flat = hi[~ndimage.binary_dilation(strong, iterations=4)]
    base = float(np.abs(flat).mean()) if flat.size else 0.0
    if base < 0.01:
        return None
    return {'ring_ratio': float(np.abs(ring).mean() / base),
            'symmetry': float(min(pos, neg) / max(pos, neg)) if max(pos, neg) > 0 else 0.0}


def normal_map_facts(rgba):
    """Is this a real normal map, a flat placeholder, or embossed from a diffuse?"""
    import numpy as np
    r = rgba[..., 0].astype(np.float32) / 127.5 - 1
    g = rgba[..., 1].astype(np.float32) / 127.5 - 1
    b = rgba[..., 2].astype(np.float32) / 127.5 - 1
    mag = np.sqrt(r * r + g * g + b * b)
    flat = float(((rgba[..., 0] > 120) & (rgba[..., 0] < 136) &
                  (rgba[..., 1] > 120) & (rgba[..., 1] < 136) &
                  (rgba[..., 2] > 245)).mean())
    # embossed normals derive X and Y from the same luminance, so they correlate
    rr, gg = r.ravel()[::7], g.ravel()[::7]
    corr = 0.0
    if rr.std() > 1e-4 and gg.std() > 1e-4:
        corr = float(abs(np.corrcoef(rr, gg)[0, 1]))
    alpha = rgba[..., 3]
    return {'flat_frac': flat, 'unit_dev': float(abs(mag - 1).mean()),
            'xy_corr': corr, 'alpha_solid': float((alpha > 250).mean()),
            'alpha_range': int(alpha.max()) - int(alpha.min())}


def histogram_facts(gray):
    import numpy as np
    h = np.bincount(gray.ravel(), minlength=256)
    n = gray.size
    return {'clip_black': float(h[0] / n), 'clip_white': float(h[255] / n),
            'mean': float(gray.mean()), 'std': float(gray.std())}


# ---------------------------------------------------------------- classifying
def map_kind(path):
    p = path.lower()
    if p.endswith('_n.dds'): return 'normal'
    if p.endswith('_msn.dds'): return 'model-normal'
    if p.endswith('_s.dds'): return 'specular'
    if p.endswith('_sk.dds'): return 'subsurface'
    if p.endswith('_g.dds'): return 'glow-mask'
    if p.endswith('_p.dds'): return 'parallax'
    if p.endswith('_e.dds'): return 'environment'
    if p.endswith('_m.dds'): return 'envmask'
    if p.endswith(('_rmaos.dds', '_rmaos.dds')): return 'pbr-rmaos'
    return 'diffuse'


BODY_HINTS = [
    ('CBBE',   r'cbbe|femalebody_1\.nif|caliente'),
    ('3BA',    r'3ba|3bbb|cbbe 3d'),
    ('BHUNP',  r'bhunp|unp\b|uunp'),
    ('HIMBO',  r'himbo'),
    ('SOS',    r'\bsos\b|schlong'),
    ('Vanilla', r'femalebody|malebody'),
]

FEATURE_PATHS = [
    ('OAR (current animation framework)', r'openanimationreplacer'),
    ('DAR (superseded by OAR)',           r'dynamicanimationreplacer'),
    ('HDT-SMP physics',                   r'hdtskinnedmeshconfigs|hdtsmp|\.xml$'),
    ('CBPC physics',                      r'cbpconfig|cbpc'),
    ('TruePBR / Community Shaders PBR',   r'^textures/pbr/|^materials/.*\.json$'),
    ('Nemesis behaviour',                 r'nemesis'),
    ('Pandora behaviour',                 r'pandora'),
    ('SPID distribution',                 r'_distr\.ini$'),
    ('KID keywords',                      r'_kid\.ini$'),
    ('SkyPatcher',                        r'skypatcher'),
    ('Papyrus scripts',                   r'^scripts/.*\.pex$'),
    ('facegen (NPC visuals)',             r'facegendata'),
    ('LOD assets',                        r'lodsettings|_lod\.nif$|/lod/'),
]

JUNK = re.compile(r'(^|/)(thumbs\.db|desktop\.ini|__macosx|\.ds_store)|\.(psd|xcf|blend|max|zip|rar|7z|bak|tmp)$', re.I)


def inspect(mid, prefer=None, label=None, sample=48, vanilla=None):
    import numpy as np
    d = M.index_mod(mid, prefer=prefer, label=label, deep=True)
    ents = d['entries']
    out = {'modId': mid, 'label': label, 'file': d['file'], 'size_mb': d['size_mb'],
           'findings': [], 'features': [], 'inventory': {}, 'notes': []}

    by_ext = Counter(os.path.splitext(k)[1] for k in ents)
    out['inventory'] = {k: v for k, v in by_ext.most_common(12) if k}

    # ---------------- features present
    for name, pat in FEATURE_PATHS:
        rx = re.compile(pat, re.I)
        hits = [k for k in ents if rx.search(k)]
        if name.startswith('HDT-SMP'):
            hits = [k for k in hits if 'hdt' in k.lower() or 'smp' in k.lower()]
        if hits:
            out['features'].append(f'{name} ({len(hits)} files, e.g. {hits[0]})')

    blob_names = ' '.join(ents)
    for name, pat in BODY_HINTS:
        if re.search(pat, blob_names, re.I):
            out['features'].append(f'body/skeleton hint: {name}')
            break

    # ---------------- packaging
    junk = [k for k in ents if JUNK.search(k)]
    if junk:
        out['findings'].append(f'{len(junk)} junk files shipped in the archive: ' +
                               ', '.join(junk[:4]))
    plugins = [k for k in ents if k.endswith(('.esp', '.esl', '.esm'))]
    if plugins:
        out['notes'].append(f'plugins: {", ".join(plugins)}')

    # ---------------- meshes
    nifs = {k: v for k, v in ents.items() if k.endswith('.nif')}
    if nifs:
        # SSE meshes report NIF user version 100; Oldrim ones report 11/34/83 and
        # use NiTriShape rather than BSTriShape. That is a hard fact, not a guess.
        legacy = [k for k, v in nifs.items() if v.get('ver') and v['ver'] != '100']
        # Skinned meshes keep their geometry in NiSkinPartition, which this does
        # not parse, so their triangles are unknown rather than zero. Counting
        # them as zero would understate the budget badly.
        skinned = [k for k, v in nifs.items() if v.get('skinned')]
        tris = sum(v.get('tris', 0) for v in nifs.values())
        if skinned:
            out['notes'].append(f'{len(nifs)} meshes: {tris:,} triangles across the '
                                f'{len(nifs)-len(skinned)} static ones, plus {len(skinned)} '
                                f'skinned meshes whose counts are not read')
        else:
            out['notes'].append(f'{len(nifs)} meshes, {tris:,} triangles total')
        para = [k for k, v in nifs.items() if v.get('parallax')]
        if para:
            has_p = [k for k in ents if k.endswith('_p.dds')]
            if not has_p:
                out['findings'].append(
                    f'{len(para)} meshes reference parallax maps but no _p.dds ships '
                    f'(e.g. {para[0]}); needs a separate parallax texture set')
            else:
                out['features'].append(f'parallax-ready meshes ({len(para)})')
        if legacy:
            vers = Counter(nifs[k]['ver'] for k in legacy)
            out['findings'].append(
                f'{len(legacy)} of {len(nifs)} meshes are unconverted Oldrim format '
                f'(NIF user version {", ".join(vers)} instead of 100, NiTriShape instead of '
                f'BSTriShape): {legacy[0]}')

    # ---------------- equipment: what the items are and where they sit
    root0 = os.path.join(M.CACHE, [x for x in os.listdir(M.CACHE)
                                   if x.startswith(f'x{mid}-')][0])
    items, parsed = [], []
    for pf in glob.glob(root0 + '/**/*.es[pml]', recursive=True):
        try:
            pl = esp.Plugin(pf)
        except Exception:
            continue
        parsed.append(pl)
        items += pl.armo
        if pl.esl:
            out['notes'].append(f'{os.path.basename(pf)} is ESL-flagged (no load-order slot)')
    if items:
        kinds = Counter(esp.classify(r) for r in items)
        out['notes'].append(f'{len(items)} equippable items: ' +
                            ', '.join(f'{v} {k}' for k, v in kinds.most_common(6)))
        slots = Counter()
        for r in items:
            for s in r['slots']:
                slots[s] += 1
        out['notes'].append('biped slots used: ' + ', '.join(
            f'{s} {esp.SLOTS.get(s, "?")} ({n})' for s, n in slots.most_common(6)))
        contested = [s for s in slots if s in (45, 46, 47, 44, 55)]
        if contested:
            out['notes'].append('slots ' + ', '.join(str(s) for s in contested) +
                                ' are the commonly contested ones; anything else using them '
                                'will not equip at the same time')

        cloth = [r for r in items if esp.cloth_relevant(r)]
        if cloth:
            feat = ' '.join(out['features'])
            nifs_all = {k: v for k, v in ents.items() if k.endswith('.nif')}
            custom = [k for k, v in nifs_all.items() if v.get('custom_bones')]
            skirt = [k for k, v in nifs_all.items() if v.get('skirt_chain')]
            rigid = [k for k, v in nifs_all.items()
                     if v.get('skinned') is False and v.get('shapes')]
            kindstr = ', '.join(f'{v} {k}' for k, v in
                                Counter(esp.classify(r) for r in cloth).most_common(3))
            has_smp = 'HDT-SMP' in feat
            if custom and not has_smp:
                sample = nifs_all[custom[0]].get('custom_bones', [])[:4]
                out['findings'].append(
                    f'{len(custom)} meshes are weighted to bones outside the vanilla skeleton '
                    f'({", ".join(sample)}) but no HDT-SMP config ships, so that rig does nothing '
                    f'without a separate physics patch')
            elif skirt and not has_smp:
                out['findings'].append(
                    f'{len(cloth)} cloth items ({kindstr}) are weighted to the vanilla skirt bone '
                    f'chain, which only moves with the canned skirt animation. No HDT-SMP config '
                    f'ships, so there is no simulation and no response to wind or movement')
            elif not custom and not skirt and not has_smp:
                out['findings'].append(
                    f'{len(cloth)} cloth items ({kindstr}) carry no cloth bones at all and no '
                    f'physics config, so they are rigid geometry welded to the body')
            if 'CBPC' in feat and not has_smp:
                out['findings'].append(
                    'physics here is CBPC only, which is bone jiggle without collision rather '
                    'than cloth simulation')
        else:
            out['notes'].append('no loose-cloth items here (rings, headgear, boots and the like '
                                'do not need physics)')
        if not any('PBR' in f for f in out['features']):
            out['notes'].append('no PBR material set (only matters under TruePBR)')

    # ---------------- textures
    out['_replaced'] = sum(1 for k in ents if k in (vanilla or {}))
    dds = {k: v for k, v in ents.items() if k.endswith('.dds')}
    if not dds:
        return _finish(out, ents, parsed, items)
    kinds = Counter(map_kind(k) for k in dds)
    out['notes'].append('texture map types: ' + ', '.join(f'{k}={v}' for k, v in kinds.most_common()))

    # a diffuse with no normal beside it leaves the surface flat, or falls back
    # to whatever normal the vanilla asset had, which rarely matches new art
    diffuse = [k for k in dds if map_kind(k) == 'diffuse' and not k.endswith(('_em.dds', '_bl.dds'))]
    missing_n = [k for k in diffuse if (k[:-4] + '_n.dds') not in dds]
    if diffuse and len(missing_n) > len(diffuse) * 0.25:
        in_vanilla = sum(1 for k in missing_n if (vanilla or {}).get(k[:-4] + '_n.dds'))
        out['findings'].append(
            f'{len(missing_n)} of {len(diffuse)} diffuse textures ship with no matching normal map, '
            f'so those surfaces get no authored bump detail' +
            (f' ({in_vanilla} would fall back to the vanilla normal, which will not match the new art)'
             if in_vanilla else '') + f' (e.g. {missing_n[0]})')

    raw = [k for k, v in dds.items() if v.get('fmt') in ('uncompressed', 'raw', 'DXGI28', 'DXGI87')]
    if raw:
        mb = sum(dds[k].get('size', 0) for k in raw) / 1048576
        out['findings'].append(
            f'{len(raw)} textures shipped uncompressed rather than BC-compressed, costing roughly '
            f'{mb:.0f} MB of VRAM for no visual gain (e.g. {raw[0]})')

    nomip = [k for k, v in dds.items() if v.get('mips') in (0, 1) and max(v.get('w', 0), v.get('h', 0)) >= 256]
    if nomip:
        out['findings'].append(f'{len(nomip)} of {len(dds)} textures ship without mipmaps, '
                               f'which shimmers in motion (e.g. {nomip[0]})')

    bc1n = [k for k, v in dds.items() if map_kind(k) in ('normal', 'model-normal') and v.get('fmt') == 'BC1']
    if bc1n:
        out['findings'].append(f'{len(bc1n)} normal maps stored as BC1, which bands on smooth '
                               f'surfaces; BC5/BC7 is the correct choice (e.g. {bc1n[0]})')

    npot = [k for k, v in dds.items()
            if v.get('w') and (v['w'] & (v['w'] - 1) or v['h'] & (v['h'] - 1))]
    if npot:
        out['findings'].append(f'{len(npot)} textures are not power-of-two: {npot[0]}')

    # diffuse/normal resolution mismatch: author did the pretty map only
    pairs = 0
    mism = []
    for k, v in dds.items():
        if map_kind(k) != 'diffuse' or not v.get('w'):
            continue
        n = k[:-4] + '_n.dds'
        if n in dds and dds[n].get('w'):
            pairs += 1
            if v['w'] >= dds[n]['w'] * 2:
                mism.append(f"{os.path.basename(k)} {v['w']}px vs normal {dds[n]['w']}px")
    if mism:
        out['findings'].append(f'{len(mism)} of {pairs} texture sets have a much lower-res normal '
                               f'than diffuse: ' + '; '.join(mism[:3]))

    if vanilla:
        replaced = [k for k in dds if k in vanilla]
        out['notes'].append(f'{len(replaced)} of {len(dds)} textures replace a vanilla asset '
                            f'({len(dds)-len(replaced)} are new content)')
        downgrade = [(k, dds[k]['w'], vanilla[k]['w']) for k in replaced
                     if dds[k].get('w') and vanilla[k].get('w') and dds[k]['w'] < vanilla[k]['w']]
        if downgrade:
            out['findings'].append(
                f'{len(downgrade)} textures ship LOWER resolution than the vanilla asset they '
                f'replace: ' + ', '.join(f'{os.path.basename(k)} {a}px vs vanilla {b}px'
                                         for k, a, b in downgrade[:3]))

    res = Counter(f"{v['w']}x{v['h']}" for v in dds.values() if v.get('w'))
    out['notes'].append('resolutions: ' + ', '.join(f'{k}({n})' for k, n in res.most_common(5)))
    fmts = Counter(v.get('fmt') for v in dds.values() if v.get('fmt'))
    out['notes'].append('formats: ' + ', '.join(f'{k}({n})' for k, n in fmts.most_common(6)))

    # ---------------- pixel-level sampling
    root = os.path.join(M.CACHE, [x for x in os.listdir(M.CACHE)
                                  if x.startswith(f'x{mid}-')][0])
    files = {}
    for f in glob.glob(os.path.join(root, '**', '*.dds'), recursive=True):
        files[M.data_rel(os.path.relpath(f, root))] = f
    bsas = glob.glob(os.path.join(root, '**', '*.bsa'), recursive=True)
    bsa_lookup = {}
    for bp in bsas:
        try:
            b = M.BSA(bp)
        except Exception:
            continue
        for i, (n, _o, _s) in enumerate(b.entries):
            bsa_lookup[M.data_rel(n)] = (b, i)

    def get_bytes(key):
        if key in files:
            return open(files[key], 'rb').read()
        if key in bsa_lookup:
            b, i = bsa_lookup[key]
            return b.read(i)
        return None

    keys = sorted(dds)
    step = max(1, len(keys) // sample)
    picked = keys[::step][:sample]
    eff, blocky, flatn, embossed, solidgloss, upscaled = [], [], [], [], [], []
    for k in picked:
        try:
            raw = get_bytes(k)
            if not raw:
                continue
            arr = decode_dds(raw, tmpname=f'{mid}.dds')
            if arr is None or arr.size == 0:
                continue
            gray = np.asarray(np.dot(arr[..., :3], [0.299, 0.587, 0.114]), dtype=np.uint8)
            kind = map_kind(k)
            if kind in ('normal', 'model-normal'):
                nf = normal_map_facts(arr)
                if nf['flat_frac'] > 0.9:
                    flatn.append(k)
                elif nf['xy_corr'] > 0.75:
                    embossed.append((k, round(nf['xy_corr'], 2)))
                if nf['alpha_solid'] > 0.98:
                    solidgloss.append(k)
            elif kind in ('glow-mask', 'envmask', 'environment', 'parallax'):
                pass          # these are meant to be flat; detail checks do not apply
            else:
                e = effective_resolution(gray)
                if e is not None:
                    eff.append((k, e, dds[k].get('w')))
                jb = jpeg_blocking(gray)
                if jb and jb > 1.35:
                    blocky.append((k, round(jb, 2)))
            if vanilla is not None and k in vanilla:
                vb = vanilla_bytes(vanilla, k)
                if vb is not None:
                    va = decode_dds(vb, tmpname=f'van{mid}.dds')
                    if va is not None and va.size:
                        s = upscale_similarity(arr, va)
                        # 0.95 measured: hand-authored retextures of the same
                        # object peak at 0.91, sharpened upscales bottom at 0.96
                        if s is not None and s > 0.95:
                            upscaled.append((k, round(s, 4), dds[k].get('w'), va.shape[1]))
        except Exception:
            continue

    if flatn:
        out['findings'].append(f'{len(flatn)}/{len(picked)} sampled normal maps are flat placeholders '
                               f'carrying no surface detail (e.g. {flatn[0]})')
    if embossed:
        out['findings'].append(f'{len(embossed)} sampled normal maps look embossed from the diffuse '
                               f'rather than authored (X/Y correlation {embossed[0][1]}): {embossed[0][0]}')
    if solidgloss:
        out['findings'].append(f'{len(solidgloss)} normal maps have a solid alpha channel, so gloss is '
                               f'uniform and surfaces read flat/plastic (e.g. {solidgloss[0]})')
    if blocky:
        out['findings'].append(f'{len(blocky)} sampled textures show JPEG blocking, meaning a compressed '
                               f'source: {blocky[0][0]} (grid ratio {blocky[0][1]})')
    if upscaled:
        major = [x for x in upscaled if map_kind(x[0]) in ('diffuse', 'normal', 'model-normal')]
        # an upscaled glow or env mask is trivia; an upscaled diffuse is the
        # whole mod being vanilla in a bigger container
        out.setdefault('_flags', []).append(
            'flag:upscaled-textures' if major else 'flag:upscaled-masks-only')
        out['findings'].append(
            f'{len(upscaled)} sampled textures are near-identical to the vanilla asset at higher '
            f'stored resolution, i.e. upscaled vanilla ({len(major)} of them diffuse/normal maps, '
            f'the rest masks where it matters less): ' +
            ', '.join(f'{os.path.basename(a)} [{map_kind(a)}] {c}px vs vanilla {d}px'
                      for a, b, c, d in (major or upscaled)[:3]))
    if eff:
        low = [(k, e, w) for k, e, w in eff if w and w >= 2048 and e < 1.6]
        if low:
            out['findings'].append(
                f'{len(low)}/{len(eff)} sampled textures carry far less detail than their stored size '
                f'suggests (soft or upscaled): ' +
                ', '.join(f'{os.path.basename(k)} {w}px detail={e:.2f}' for k, e, w in low[:3]))
        out['notes'].append(f'detail index (higher = more real texture information): ' +
                            f'{sum(e for _k, e, _w in eff)/len(eff):.2f} mean over {len(eff)} sampled')
    return _finish(out, ents, parsed, items)


def _finish(out, ents, plugins, items):
    """Tag from contents and record both tags and the path set in the index."""
    out['tags'] = tagger.derive(out, ents, plugins, items)
    n = tagger.save(out['modId'], out['label'], out['tags'], list(ents),
                    out['findings'], out['size_mb'])
    out['_indexed'] = n
    return out


def vanilla_bytes(vanilla, key):
    rec = vanilla.get(key)
    if not rec or rec.get('src') in (None, 'loose'):
        return None
    p = os.path.join(VDATA, rec['src'])
    try:
        b = M.BSA(p)
    except Exception:
        return None
    for i, (n, _o, _s) in enumerate(b.entries):
        if n.replace('\\', '/').lower() == key:
            return b.read(i)
    return None


def upscale_similarity(mod_arr, van_arr):
    """Downscale the mod texture to the vanilla size and correlate. ~1.0 means the
    mod texture contains no information the vanilla one did not already have."""
    import numpy as np
    from PIL import Image
    if mod_arr.shape[0] < van_arr.shape[0]:
        return None
    m = Image.fromarray(mod_arr[..., :3]).convert('L').resize(
        (van_arr.shape[1], van_arr.shape[0]), Image.LANCZOS)
    a = np.asarray(m, dtype=np.float32).ravel()
    b = np.asarray(Image.fromarray(van_arr[..., :3]).convert('L'), dtype=np.float32).ravel()
    if a.std() < 1e-3 or b.std() < 1e-3:
        return None
    return float(np.corrcoef(a, b)[0, 1])


VDATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'


def patches_for(mid, name=None):
    """What the community has built on top of this mod: retextures, physics
    conversions, PBR sets, SPID distribution, fixes.

    Nexus exposes no reverse-dependency edge, so this searches by name instead.
    That over-matches (translations, unrelated mods sharing words) and the
    caller filters."""
    import urllib.request
    if not name:
        q = '{ legacyMods(ids:[{gameId:1704, modId:%d}]) { nodes { name } } }' % mid
        try:
            r = urllib.request.Request('https://api.nexusmods.com/v2/graphql',
                                       data=json.dumps({'query': q}).encode(),
                                       headers={'Content-Type': 'application/json',
                                                'User-Agent': 'SkyrimModAssistant/0.1'})
            name = json.load(urllib.request.urlopen(r, timeout=60))['data']['legacyMods']['nodes'][0]['name']
        except Exception:
            return []
    stem = re.sub(r'\s*[-(].*$', '', name).strip()[:40]
    q = ('{ mods(filter:{ gameDomainName:[{value:"skyrimspecialedition",op:EQUALS}], '
         'name:[{value:"%s", op:WILDCARD}] }, sort:{ endorsements:{direction:DESC} }, '
         'count:40){ nodes { modId name summary endorsements updatedAt } } }'
         % stem.replace('"', ''))
    try:
        r = urllib.request.Request('https://api.nexusmods.com/v2/graphql',
                                   data=json.dumps({'query': q}).encode(),
                                   headers={'Content-Type': 'application/json',
                                            'User-Agent': 'SkyrimModAssistant/0.1'})
        d = json.load(urllib.request.urlopen(r, timeout=60))
        return [n for n in ((d.get('data') or {}).get('mods') or {}).get('nodes', [])
                if n['modId'] != mid]
    except Exception:
        return []


def report(res, dependents=None):
    print(f"\n{'='*78}\n{res['label'] or ''}  (mod {res['modId']})")
    print(f"  file: {res['file']}  [{res['size_mb']} MB]")
    print(f"  contents: " + ', '.join(f'{v} {k}' for k, v in res['inventory'].items()))
    if res.get('tags'):
        print('  TAGS: ' + '  '.join(res['tags']))
    for n in res['notes']:
        print(f'  - {n}')
    if res['features']:
        print('  SUPPORTS:')
        for f in res['features']:
            print(f'    + {f}')
    if res['findings']:
        print('  WARNING SIGNS:')
        for f in res['findings']:
            print(f'    ! {f}')
    else:
        print('  WARNING SIGNS: none detected')
    if dependents:
        skip = re.compile(r'translat|russian|deutsch|spanish|polish|italian|chinese|português|'
                          r'portugu|turkish|\bchs\b|\bcht\b|korean|japanese|français', re.I)
        want = re.compile(r'pbr|parallax|smp|hdt|physics|patch|fix|retextur|\bhd\b|4k|2k|'
                          r'3ba|himbo|cbbe|bhunp|complex|spid|mesh|addon|tweak', re.I)
        rel = [x for x in dependents
               if want.search(x['name'] + ' ' + (x.get('summary') or ''))
               and not skip.search(x['name'])]
        if rel:
            print(f'  COMMUNITY ADDONS (fills gaps above, or replaces parts of it):')
            for x in sorted(rel, key=lambda y: -(y.get('endorsements') or 0))[:10]:
                print(f"    * {x['modId']:<7}{(x.get('updatedAt') or '')[:7]}  "
                      f"{x['name'][:56]:<58}{x.get('endorsements')} end")


if __name__ == '__main__':
    van = None
    vp = os.path.join(SP, 'vanilla_index.json')
    if os.path.exists(vp):
        van = json.load(open(vp))
    for a in sys.argv[1:]:
        # modId[:label[:file-name regex, for mods that ship 1K/2K/4K variants]]
        parts = a.split(':')
        mid = int(parts[0])
        lab = parts[1] if len(parts) > 1 else None
        pref = parts[2] if len(parts) > 2 else None
        try:
            r = inspect(mid, label=lab, prefer=pref, vanilla=van)
            report(r, patches_for(mid))
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f'{mid}: FAILED {str(e)[:120]}')
