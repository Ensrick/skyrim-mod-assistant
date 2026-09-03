r"""Build the local Skyking Signs env-mask overlay (fallback fix, not the preferred one).

Skyking Signs 112902's "03 Parallax" option (chosen in
records/fomod-plans/112902-skyking-signs.json) rewrites the wooden post /
bracket shape of every sign mesh from a Default shader to an EnvironmentMap
shader (EnvMapScale 1.0) whose cubemap slot is the 1x1 black
``textures\cubemaps\dynamic1pxcubemap_black.dds`` and whose env-mask slot is
a city-wood ``_m`` texture that NOTHING in the stack ships:

    textures\architecture\whiterun\wrwoodbeam01_m.dds     (8 Whiterun signs)
    textures\architecture\farmhouse\woodpost02_m.dds      (14 inn / Riverwood signs)
    textures\architecture\riften\riftencanalwood01_m.dds  (9 Riften signs)
    textures\architecture\windhelm\whwoodbase01_m.dds     (5 Windhelm signs)

and, added 2026-09-02 after the load-order sweep (audit/envmask_scan.py,
records/envmask-missing-scan-2026-09-02.md), the seven remaining masks the
same option references on the same terms (EnvironmentMap, EnvMapScale 1.0,
black 1x1 cubemap), read from the installed Skyking NIFs:

    textures\architecture\markarth\mrkdeco01_m.dds        (mrkalchemysign; carved stone;
                                                           also Skyking Unique Signs' signthehagscure)
    textures\architecture\markarth\mrkinnwindows01_m.dds  (mrksigngeneralgoods01, silverbloodinn;
                                                           stone window frame; also Unique Signs' signarnleifandsons)
    textures\architecture\riften\riftenlogdetails01_m.dds (signrtorphanage01; wood)
    textures\landscape\fieldgrass01_m.dds                 (loadscreenblackbriar01 ground)
    textures\landscape\mountains\mountainslab02_m.dds     (loadscreenblackbriar01 rock; also
                                                           ERM - Fix and Addon's minecboulderl02)
    textures\landscape\rocks01_m.dds                      (loadscreenblackbriar01 rock)
    textures\landscape\tundra01_m.dds                     (loadscreenblackbriar01 ground)

Vanilla ships no ``_m`` for any of these eleven diffuse textures and renders
the same surfaces with the Default shader (the vanilla loadscreenblackbriar01
was parsed from Skyrim - Meshes1.bsa: all four landscape shapes Default, no
slot 4/5), so a black mask reproduces the vanilla look. Every mask is a
matte material class (wood, carved stone, ground, rock); nothing here is an
intended metal / glass / water reflection.

Verified absent on 2026-09-01 across the 306-row Default modlist (loose), the
92 vanilla BSAs and the 58 enabled-mod BSAs; re-verified 2026-09-02 by the
sweep (207 enabled mods, 59 mod BSAs, 92 vanilla BSAs, 353,526 archive
entries). Community Shaders' Dynamic
Cubemaps treats the 1x1 black cubemap as "reflect the live environment" with
F0 = 1.0 and roughness 1/8 (package/Shaders/Lighting.hlsl ~1905-1950), scaled
by the env mask - and with the mask file missing the engine substitutes a
default texture, which is what paints the posts as slick, wet-looking wood.

This overlay supplies a 4x4 solid-black, alpha-1 uncompressed env mask at each
of the eleven paths. Black mask -> envMask == 0 -> the whole reflection block is
skipped; alpha == 1 and grayscale RGB -> Extended Materials does NOT treat it
as a complex material. The post shape then shades like the standard "01"
meshes (plain specular wood). Only meshes that reference those exact paths are
affected, and today no mesh finds them at all. If a future texture pack ships
real complex-material masks at any of these paths, disable this overlay (it
sits at the top of the priority list and would shadow them).

Nothing vendor-derived is touched or copied. The payload is generated from
this script alone and is safe to redistribute, but stays local by convention.

    py -3 overlays/ensrick-skyking-signs-envmask-fix/build.py [--out DIR]

Outputs ``payload/`` (Data-root tree) and ``ensrick-skyking-signs-envmask-fix.zip``
for a MO2Headless install, and prints SHA-256 per file.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

MASK_PATHS = (
    # 2026-09-01: the four sign-post masks (#159)
    "textures/architecture/whiterun/wrwoodbeam01_m.dds",
    "textures/architecture/farmhouse/woodpost02_m.dds",
    "textures/architecture/riften/riftencanalwood01_m.dds",
    "textures/architecture/windhelm/whwoodbase01_m.dds",
    # 2026-09-02: the seven remaining masks the same option references
    "textures/architecture/markarth/mrkdeco01_m.dds",
    "textures/architecture/markarth/mrkinnwindows01_m.dds",
    "textures/architecture/riften/riftenlogdetails01_m.dds",
    "textures/landscape/fieldgrass01_m.dds",
    "textures/landscape/mountains/mountainslab02_m.dds",
    "textures/landscape/rocks01_m.dds",
    "textures/landscape/tundra01_m.dds",
)

DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PITCH, DDSD_PIXELFORMAT, DDSD_MIPMAPCOUNT = 0x1, 0x2, 0x4, 0x8, 0x1000, 0x20000
DDPF_ALPHAPIXELS, DDPF_RGB = 0x1, 0x40
DDSCAPS_COMPLEX, DDSCAPS_TEXTURE, DDSCAPS_MIPMAP = 0x8, 0x1000, 0x400000


def black_mask_dds(size: int = 4) -> bytes:
    """Uncompressed A8R8G8B8 DDS, `size`x`size` with a full mip chain, every texel (0,0,0,255)."""
    mips = size.bit_length()  # 4 -> 3 mips (4,2,1)
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PITCH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT
    header = struct.pack(
        "<4sIIIIIII11I",
        b"DDS ", 124, flags, size, size, size * 4, 0, mips, *([0] * 11),
    )
    pixelformat = struct.pack(
        "<IIIIIIII",
        32, DDPF_RGB | DDPF_ALPHAPIXELS, 0, 32,
        0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000,
    )
    caps = struct.pack("<IIIII", DDSCAPS_COMPLEX | DDSCAPS_TEXTURE | DDSCAPS_MIPMAP, 0, 0, 0, 0)
    texel = bytes((0x00, 0x00, 0x00, 0xFF))  # B G R A in memory for A8R8G8B8
    body = b"".join(texel * ((size >> level) ** 2) for level in range(mips))
    out = header + pixelformat + caps + body
    assert len(header) + len(pixelformat) + len(caps) == 128
    return out


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent,
                    help="directory receiving payload/ and the zip (default: this overlay dir)")
    args = ap.parse_args(argv)

    payload = args.out / "payload"
    zip_path = args.out / "ensrick-skyking-signs-envmask-fix.zip"
    data = black_mask_dds()
    written = []
    for rel in MASK_PATHS:
        dst = payload / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        written.append(rel)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in written:
            zf.write(payload / Path(rel), rel.replace("/", "\\"))
    print(f"payload: {payload}")
    print(f"zip:     {zip_path}  sha256={sha256(zip_path.read_bytes())}")
    print(f"mask:    {len(data)} bytes, sha256={sha256(data)}")
    for rel in written:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
