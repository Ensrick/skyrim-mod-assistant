r"""Build the local Bloodskal Blade 4 static-glow overlay from the vendor MAIN mesh.

Bloodskal Blade 4 (Nexus 120399, Billyro, file 505407 "MAIN") animates the
blade's glow with three controllers whose key curves live in three data blocks:

    [22]/[23] NiFloatData  brightness  3 keys, 0.3 -> 0.8 -> 0.0 (quadratic)
    [24]/[25] NiPosData    colour      3 keys, red -> yellow -> red (quadratic)
    [32]/[33] NiFloatData  ember V     2 keys, 0.0 -> 1.0 (quadratic)

User ruling 2026-08-30: "The pulse looks bad on Bloodskal Blade, so no to that.
Just the simple glow version."  The page ships no static-glow option, so this
overlay freezes every curve IN PLACE instead of deleting blocks and renumbering
references: each key's value is pinned to the curve's first key (rounded to six
decimals, which is how the original edit was made) and every forward/backward
tangent is zeroed.  Key times, the block table, the type table and the string
table are untouched, so the file length stays 429,837 bytes and no reference
can dangle.  Exactly 42 bytes change.

This is a vendor-derived mesh.  The Nexus page (read 2026-09-02) allows
modification and re-upload with credit to Billyro, so the output is
distributable with credit; the recipe exists so an installer can regenerate it
from the user's own download instead.  Nothing vendor-derived is committed.

    py -3 overlays/ensrick-bloodskal-blade-4-static-glow/build.py <vendor bloodsword.nif> [--out DIR]

<vendor bloodsword.nif> is the untouched MAIN mesh, normally
``<MO2 mods>/Bloodskal Blade 4/meshes/dlc02/weapons/bloodsword/bloodsword.nif``.
The script refuses any input whose SHA-256 is not the recorded vendor hash,
refuses to overwrite the input, and fails unless the output SHA-256 equals the
hash of the installed overlay mesh.  Outputs ``payload/`` (Data-root tree) and
``ensrick-bloodskal-blade-4-static-glow.zip`` under --out (default: ``work/``
beside this script, which is not tracked).
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

VENDOR_SHA256 = "A8CC952DC0A759DDE710DF0385AE5D16E7810B4DC7EFF1BE1578DB58E2890605"
VENDOR_BYTES = 429837
OUTPUT_SHA256 = "C743F18D3630685950894C8CCB564CF3FF4FA0181549D00D1F4673B81E975051"
EXPECTED_CHANGED_BYTES = 42
RELATIVE_PATH = "meshes/dlc02/weapons/bloodsword/bloodsword.nif"

QUADRATIC_KEY = 2

# (label, offset of the numKeys field, number of keys, floats per value)
# Key layout for interpolation 2 (QUADRATIC_KEY): time, value, forward, backward,
# each `floats per value` wide except time.  Offsets were measured on the vendor
# file above and are asserted against the header fields before any write.
CURVES = (
    ("brightness (BSLightingShaderPropertyFloatController -> NiFloatData)", 0x510DA, 3, 1),
    ("emissive colour (BSLightingShaderPropertyColorController -> NiPosData)", 0x51122, 3, 3),
    ("ember V offset (BSEffectShaderPropertyFloatController -> NiFloatData)", 0x5E552, 2, 1),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def freeze(buf: bytearray) -> int:
    """Pin every curve to its first key and zero the tangents. Returns changed byte count."""
    before = bytes(buf)
    for label, header, num_keys, width in CURVES:
        n, interpolation = struct.unpack_from("<II", buf, header)
        if n != num_keys or interpolation != QUADRATIC_KEY:
            raise SystemExit(f"{label}: header at 0x{header:X} reads numKeys={n} interp={interpolation}, "
                             f"expected {num_keys}/{QUADRATIC_KEY}; wrong input file")
        key_size = 4 * (1 + 3 * width)
        first = header + 8
        pinned = [round(v, 6) for v in struct.unpack_from(f"<{width}f", buf, first + 4)]
        for k in range(num_keys):
            key = first + k * key_size
            struct.pack_into(f"<{width}f", buf, key + 4, *pinned)                 # value
            struct.pack_into(f"<{2 * width}f", buf, key + 4 + 4 * width, *([0.0] * 2 * width))  # tangents
        print(f"  {label}: {num_keys} keys pinned to {pinned}, tangents zeroed")
    return sum(1 for a, b in zip(before, buf) if a != b)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vendor_nif", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "work")
    args = parser.parse_args()

    data = args.vendor_nif.read_bytes()
    if len(data) != VENDOR_BYTES or sha256(data) != VENDOR_SHA256:
        raise SystemExit(f"input is not the recorded vendor mesh: {len(data)} bytes, SHA-256 {sha256(data)}")
    print(f"vendor mesh OK: {args.vendor_nif} SHA-256 {VENDOR_SHA256}")

    buf = bytearray(data)
    changed = freeze(buf)
    if changed != EXPECTED_CHANGED_BYTES:
        raise SystemExit(f"changed {changed} bytes, expected {EXPECTED_CHANGED_BYTES}")
    if len(buf) != VENDOR_BYTES:
        raise SystemExit("length changed; refusing to write")
    digest = sha256(bytes(buf))
    if digest != OUTPUT_SHA256:
        raise SystemExit(f"output SHA-256 {digest} does not match the recorded overlay {OUTPUT_SHA256}")

    payload = args.out / "payload"
    target = payload / Path(RELATIVE_PATH)
    if target.resolve() == args.vendor_nif.resolve():
        raise SystemExit("refusing to overwrite the vendor file")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bytes(buf))

    archive = args.out / "ensrick-bloodskal-blade-4-static-glow.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(target, RELATIVE_PATH)
    print(f"wrote {target} ({changed} bytes changed) SHA-256 {digest}")
    print(f"wrote {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
