"""Mip-retention: how much texture detail survives at mid and far camera distance.

Motivation (CURATION_POLICY.md, "Textures are judged at distance"): a texture is
sampled at mip 0 only when the camera is close. At normal play distance the GPU
samples mip 2-4, and a replacer whose fine detail lives entirely in mip 0 reads
matte and single-tone there even though the close-up is excellent. The stored
mip chain is what the game sees, so this module measures the chain as shipped
(texconv decompresses every level; nothing is regenerated for the measurement).

Metrics per mip level, on luminance (0-255 scale):
  hf    high-frequency energy: RMS of the 4-neighbour Laplacian. Pores, grain,
        fabric weave and edge micro-contrast live here.
  tone  tonal variation: standard deviation of the whole level. "Single-tone"
        at distance means this collapses.
  hf_rel  hf / mean luminance, so a dark and a bright texture compare fairly.

Two comparisons are reported:
  retention   hf(mip k) / hf(mip 0) for the same texture (mip index axis).
  vs vanilla  hf and tone at MATCHED RESOLUTION against the vanilla texture the
              file replaces. The GPU picks a mip by screen texel density, so a
              4K replacer at mip 3 (512 px) competes with vanilla 2K at mip 2
              (512 px). Ratios below 1.0 mean the replacer shows less detail at
              that distance than the vanilla texture it displaced.

Command line:
  py -3 audit/mip_retention.py <texture.dds> [vanilla.dds] [--json]
  py -3 audit/mip_retention.py <texture.dds> --resharpen out.dds [--unsharp 1.0] [--radius 1.0]
        regenerate the mip chain from mip 0 with Lanczos + unsharp mask per level,
        write an uncompressed RGBA DDS, then recompress to the source format with
        texconv (the recipe form; nothing is written outside the given path).
"""
import io, os, struct, subprocess, sys, tempfile, json

TEXCONV = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                       r'Microsoft\WinGet\Packages\Microsoft.DirectXTex.Texconv_Microsoft.Winget.Source_8wekyb3d8bbwe\texconv.exe')

# DXGI formats texconv can be asked for when recompressing a regenerated chain.
FMT_TO_DXGI = {'BC1': 'BC1_UNORM', 'BC2': 'BC2_UNORM', 'BC3': 'BC3_UNORM', 'BC4': 'BC4_UNORM',
               'BC5': 'BC5_UNORM', 'BC6H': 'BC6H_UF16', 'BC7': 'BC7_UNORM',
               'uncompressed': 'B8G8R8A8_UNORM', 'raw': 'B8G8R8A8_UNORM'}


# ------------------------------------------------------------------ decoding
def _parse_rgba_dds(blob):
    """Split an R8G8B8A8_UNORM DDS (as texconv writes it) into its mip levels."""
    import numpy as np
    if blob[:4] != b'DDS ':
        raise ValueError('not a DDS')
    h = blob[4:128]
    height, width = struct.unpack_from('<II', h, 8)
    mips = struct.unpack_from('<I', h, 24)[0] or 1
    fourcc = h[80:84]
    off = 128 + (20 if fourcc == b'DX10' else 0)
    levels = []
    w, hh = width, height
    for _ in range(mips):
        n = w * hh * 4
        arr = np.frombuffer(blob[off:off + n], dtype=np.uint8).reshape(hh, w, 4)
        levels.append(arr)
        off += n
        w, hh = max(1, w // 2), max(1, hh // 2)
    return levels


def decode_mips(src, tmpname='mr.dds'):
    """DDS path or bytes -> list of (H,W,4) uint8 arrays, one per stored mip level.

    Uses texconv to decompress to R8G8B8A8_UNORM while keeping the chain exactly
    as stored; texconv only regenerates mips when asked, and it is not asked."""
    if not os.path.exists(TEXCONV):
        raise RuntimeError('texconv not found at ' + TEXCONV)
    work = os.path.join(tempfile.gettempdir(), 'mipret')
    os.makedirs(work, exist_ok=True)
    tmp_in = None
    if isinstance(src, (bytes, bytearray)):
        # Input goes to a sub-folder: texconv names its output after the input
        # basename inside -o, and an input sitting in -o itself would be its
        # own output (texconv then refuses, or the guard below trips).
        indir = os.path.join(work, 'in')
        os.makedirs(indir, exist_ok=True)
        path = tmp_in = os.path.join(indir, tmpname)
        open(path, 'wb').write(src)
    else:
        path = src
    r = subprocess.run([TEXCONV, '-nologo', '-y', '-f', 'R8G8B8A8_UNORM', '-ft', 'dds',
                        '-o', work, path], capture_output=True, text=True)
    out = os.path.join(work, os.path.splitext(os.path.basename(path))[0] + '.dds')
    if not os.path.exists(out) or os.path.abspath(out) == os.path.abspath(path):
        raise RuntimeError('texconv failed: ' + (r.stdout or '') + (r.stderr or ''))
    blob = open(out, 'rb').read()
    for p in (out, tmp_in):
        try:
            if p:
                os.remove(p)
        except OSError:
            pass
    return _parse_rgba_dds(blob)


# ------------------------------------------------------------------- metrics
def luminance(rgba):
    """Luminance in 0-255. A single-channel source (BC4 specular, R-only) decodes
    with G and B all zero; use R directly so the scale matches a grey BC1/BC3."""
    import numpy as np
    if rgba.shape[-1] >= 3 and not rgba[..., 1].any() and not rgba[..., 2].any():
        return rgba[..., 0].astype(np.float32)
    return np.dot(rgba[..., :3].astype(np.float32), [0.299, 0.587, 0.114])


def map_kind(path):
    p = str(path).lower()
    for suf, kind in (('_msn.dds', 'model-normal'), ('_n.dds', 'normal'), ('_s.dds', 'specular'),
                      ('_sk.dds', 'subsurface'), ('_g.dds', 'glow'), ('_p.dds', 'parallax'),
                      ('_e.dds', 'environment'), ('_m.dds', 'envmask')):
        if p.endswith(suf):
            return kind
    return 'diffuse'


def masked_by_default(path):
    """Only colour maps get the black-padding mask; specular, subsurface and
    normal maps legitimately hold dark or flat texels."""
    return map_kind(path) == 'diffuse'


BACKGROUND_LUM = 10.0   # UV-island padding is black in many replacers; never sampled in game


def content_mask(gray, erode=2):
    """True where the texel is real content. Near-black padding between UV islands
    (Reverie, TNG hands) is excluded, then eroded so island seams do not count as
    'detail'. Skin has no legitimate near-black texels except eye openings, which
    are far brighter than the threshold."""
    import numpy as np
    m = gray >= BACKGROUND_LUM
    for _ in range(erode):
        e = m.copy()
        e[1:, :] &= m[:-1, :]; e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        m = e
    return m


def hf_energy(gray, mask=None):
    """RMS of the 4-neighbour Laplacian (float32 luminance in), over mask if given."""
    import numpy as np
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    g = gray
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    if mask is not None:
        mm = mask[1:-1, 1:-1]
        if mm.sum() < 4:
            return 0.0
        lap = lap[mm]
    return float(np.sqrt(np.mean(lap * lap)))


def level_stats(levels, max_levels=6, masked=True):
    """Per-mip metrics for the first max_levels levels of a decoded chain."""
    import numpy as np
    out = []
    for i, arr in enumerate(levels[:max_levels]):
        g = luminance(arr)
        m = content_mask(g) if masked else None
        if m is not None and m.sum() < 16:
            m = None
        hf = hf_energy(g, m)
        sel = g[m] if m is not None else g
        mean = float(sel.mean())
        out.append({'mip': i, 'w': int(arr.shape[1]), 'h': int(arr.shape[0]),
                    'hf': round(hf, 3), 'tone': round(float(sel.std()), 3),
                    'mean': round(mean, 2), 'hf_rel': round(hf / mean, 5) if mean > 1e-3 else 0.0,
                    'coverage': round(float(m.mean()), 3) if m is not None else 1.0})
    base = out[0]['hf'] if out and out[0]['hf'] > 1e-6 else None
    for r in out:
        r['retention'] = round(r['hf'] / base, 4) if base else None
    return out


def compare(mod_levels, van_levels, masked=True):
    """Matched-resolution ratios mod/vanilla for every width both chains contain."""
    ms = {r['w']: r for r in level_stats(mod_levels, 16, masked)}
    vs = {r['w']: r for r in level_stats(van_levels, 16, masked)}
    rows = []
    for w in sorted(set(ms) & set(vs), reverse=True):
        m, v = ms[w], vs[w]
        rows.append({'w': w, 'mod_mip': m['mip'], 'van_mip': v['mip'],
                     'hf_mod': m['hf'], 'hf_van': v['hf'],
                     'hf_ratio': round(m['hf'] / v['hf'], 3) if v['hf'] > 1e-6 else None,
                     'hf_rel_ratio': round(m['hf_rel'] / v['hf_rel'], 3) if v['hf_rel'] > 1e-9 else None,
                     'tone_mod': m['tone'], 'tone_van': v['tone'],
                     'tone_ratio': round(m['tone'] / v['tone'], 3) if v['tone'] > 1e-6 else None})
    return rows


def distance_verdict(rows, widths=(512, 256, 128)):
    """Summarise the mid/far mips (512-128 px is where a body or head texture sits
    at conversation to across-the-room distance). Returns (min hf ratio, min tone
    ratio) over those widths, or None when the chains do not overlap there."""
    sel = [r for r in rows if r['w'] in widths and r['hf_ratio'] is not None]
    if not sel:
        return None
    return (min(r['hf_ratio'] for r in sel), min(r['tone_ratio'] for r in sel if r['tone_ratio'] is not None))


# ------------------------------------------------------------- regeneration
def regenerate_chain(mip0, unsharp=1.0, radius=1.0, threshold=0, filt='lanczos'):
    """Rebuild a full mip chain from mip 0 with Lanczos downsampling from the source
    level each time (no cumulative blur) and an unsharp mask on every level below
    mip 0. unsharp is the mask strength (1.0 = 100 percent), radius in pixels."""
    import numpy as np
    from PIL import Image, ImageFilter
    resample = {'lanczos': Image.LANCZOS, 'bicubic': Image.BICUBIC, 'box': Image.BOX,
                'hamming': Image.HAMMING}[filt]
    im0 = Image.fromarray(mip0, 'RGBA')
    w, h = im0.size
    levels = [mip0]
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        im = im0.resize((w, h), resample)
        if unsharp > 0 and min(w, h) >= 4:
            rgb = im.convert('RGB').filter(ImageFilter.UnsharpMask(radius=radius, percent=int(unsharp * 100), threshold=threshold))
            im = Image.merge('RGBA', (*rgb.split(), im.split()[3]))
        levels.append(np.asarray(im, dtype=np.uint8))
    return levels


def write_rgba_dds(levels, path):
    """Write an uncompressed R8G8B8A8 DDS (DX10 header) carrying the given chain."""
    h0, w0 = levels[0].shape[:2]
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x8   # caps|height|width|pixelformat|mipmapcount|pitch
    hdr = struct.pack('<4sIIIIIII', b'DDS ', 124, flags, h0, w0, w0 * 4, 0, len(levels))
    hdr += b'\0' * 44                                     # reserved1[11]
    hdr += struct.pack('<II4sIIIII', 32, 0x4, b'DX10', 0, 0, 0, 0, 0)   # DDPF_FOURCC
    caps = 0x1000 | (0x400000 | 0x8 if len(levels) > 1 else 0)          # texture | mipmap | complex
    hdr += struct.pack('<IIIII', caps, 0, 0, 0, 0)
    dx10 = struct.pack('<IIIII', 28, 3, 0, 1, 0)         # R8G8B8A8_UNORM, texture2D
    with open(path, 'wb') as f:
        f.write(hdr + dx10)
        for lv in levels:
            f.write(lv.tobytes())


def resharpen(src_path, out_path, unsharp=1.0, radius=1.0, fmt=None, filt='lanczos'):
    """Full recipe: decode mip 0, regenerate a sharpened chain, write RGBA DDS, and
    recompress with texconv to fmt (default: the source's own block format).
    Returns the path of the recompressed file."""
    import modasset as M
    levels = decode_mips(src_path)
    if fmt is None:
        info = M.dds_info(open(src_path, 'rb').read(148)) or {}
        fmt = FMT_TO_DXGI.get(info.get('fmt'), 'BC7_UNORM')
    chain = regenerate_chain(levels[0], unsharp=unsharp, radius=radius, filt=filt)
    raw = out_path[:-4] + '.rgba.dds'
    write_rgba_dds(chain, raw)
    outdir = os.path.dirname(os.path.abspath(out_path)) or '.'
    r = subprocess.run([TEXCONV, '-nologo', '-y', '-f', fmt, '-ft', 'dds', '-bc', 'x',
                        '-o', outdir, raw], capture_output=True, text=True)
    produced = os.path.join(outdir, os.path.basename(raw)[:-4] + '.dds')
    if not os.path.exists(produced):
        raise RuntimeError('texconv recompress failed: ' + (r.stdout or '') + (r.stderr or ''))
    if os.path.abspath(produced) != os.path.abspath(out_path):
        if os.path.exists(out_path):
            os.remove(out_path)
        os.replace(produced, out_path)
    return out_path


# ---------------------------------------------------------------- reporting
def table(stats, rows=None, label=''):
    lines = [f'{label}  mip  width   hf      tone    mean    hf_rel    retention']
    for r in stats:
        lines.append(f"      {r['mip']:>3}  {r['w']:>5}  {r['hf']:>6.2f}  {r['tone']:>6.2f}  {r['mean']:>6.1f}  {r['hf_rel']:.5f}  {r['retention']}")
    if rows:
        lines.append('   vs vanilla at matched resolution (mod/vanilla):')
        lines.append('      width  hf_mod  hf_van  hf_ratio  hf_rel_ratio  tone_mod  tone_van  tone_ratio')
        for r in rows:
            lines.append(f"      {r['w']:>5}  {r['hf_mod']:>6.2f}  {r['hf_van']:>6.2f}  {str(r['hf_ratio']):>8}  {str(r['hf_rel_ratio']):>12}  {r['tone_mod']:>8.2f}  {r['tone_van']:>8.2f}  {str(r['tone_ratio']):>10}")
    return '\n'.join(lines)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    src = argv[0]
    if '--resharpen' in argv:
        out = argv[argv.index('--resharpen') + 1]
        us = float(argv[argv.index('--unsharp') + 1]) if '--unsharp' in argv else 1.0
        rad = float(argv[argv.index('--radius') + 1]) if '--radius' in argv else 1.0
        filt = argv[argv.index('--filter') + 1] if '--filter' in argv else 'lanczos'
        fmt = argv[argv.index('--format') + 1] if '--format' in argv else None
        p = resharpen(src, out, unsharp=us, radius=rad, fmt=fmt, filt=filt)
        print('wrote', p)
        print(table(level_stats(decode_mips(p), masked=masked_by_default(src)), label=os.path.basename(p)))
        return 0
    van = argv[1] if len(argv) > 1 and not argv[1].startswith('--') else None
    masked = masked_by_default(src)
    stats = level_stats(decode_mips(src), masked=masked)
    rows = compare(decode_mips(src), decode_mips(van), masked) if van else None
    if '--json' in argv:
        print(json.dumps({'file': src, 'levels': stats, 'vs_vanilla': rows}, indent=1))
    else:
        print(table(stats, rows, label=os.path.basename(src)))
        if rows:
            v = distance_verdict(rows)
            if v:
                print(f'   mid/far (512-128 px) minimum vs vanilla: hf x{v[0]:.2f}, tone x{v[1]:.2f}')
    return 0


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
