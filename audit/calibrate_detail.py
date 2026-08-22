"""Calibrate the detail index against controls, so the threshold is measured
rather than asserted.

Controls, cheapest first:
  * vanilla textures at their native size   - the floor the game already meets
  * the same textures upscaled 2x and 4x    - exactly what a lazy "4K" pack is
  * the same textures sharpened after upscale - the 2012 "HD" pack trick, which
    raises apparent contrast without adding information

If the index cannot separate a real 2K texture from vanilla-upscaled-to-2K,
it is not a usable signal and I should stop quoting it.
"""
import os, sys, io, json, glob, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import modasset as M
from inspect_mod import decode_dds, effective_resolution, map_kind

DATA = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data'
random.seed(7)

def sample_vanilla(n=40):
    out = []
    for name in ['Skyrim - Textures0.bsa', 'Skyrim - Textures1.bsa', 'Skyrim - Textures5.bsa']:
        p = os.path.join(DATA, name)
        if not os.path.exists(p):
            continue
        b = M.BSA(p)
        cand = [i for i, (k, _o, _s) in enumerate(b.entries)
                if k.lower().endswith('.dds') and map_kind(k.replace('\\', '/').lower()) == 'diffuse'
                and 'lod' not in k.lower()]
        random.shuffle(cand)
        for i in cand[:n // 3 + 1]:
            try:
                raw = b.read(i)
                arr = decode_dds(raw, tmpname='cal.dds')
                if arr is None or min(arr.shape[:2]) < 512:
                    continue
                out.append((b.entries[i][0], arr))
            except Exception:
                continue
    return out

def gray(a):
    return np.asarray(np.dot(a[..., :3], [0.299, 0.587, 0.114]), dtype=np.uint8)

def upscale(g, f):
    im = Image.fromarray(g)
    return np.asarray(im.resize((im.width * f, im.height * f), Image.LANCZOS))

def sharpened(g, f):
    im = Image.fromarray(upscale(g, f))
    return np.asarray(im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=3)))

def main():
  rows = {'vanilla native': [], 'vanilla x2': [], 'vanilla x4': [],
        'vanilla x2 + sharpen': []}
  samples = sample_vanilla()
  print(f'controls built from {len(samples)} vanilla diffuse textures\n')
  for _name, arr in samples:
    g = gray(arr)
    rows['vanilla native'].append(effective_resolution(g))
    rows['vanilla x2'].append(effective_resolution(upscale(g, 2)))
    rows['vanilla x4'].append(effective_resolution(upscale(g, 4)))
    rows['vanilla x2 + sharpen'].append(effective_resolution(sharpened(g, 2)))

  print(f"{'control':<24}{'n':>4}{'mean':>9}{'median':>9}{'p90':>9}")
  for k, v in rows.items():
    v = [x for x in v if x is not None]
    if not v:
        continue
    a = np.array(v)
    print(f'{k:<24}{len(a):>4}{a.mean():>9.2f}{np.median(a):>9.2f}{np.percentile(a,90):>9.2f}')

  json.dump({k: [x for x in v if x is not None] for k, v in rows.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detail_controls.json'), 'w'))


if __name__ == '__main__':
    main()
