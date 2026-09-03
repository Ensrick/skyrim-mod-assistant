r"""Build the CC Madness longsword env-mask path overlay (#159 sweep follow-up).

Creation Club "Saints & Seducers" (bgssse025, archive ``ccbgssse025-advdsgs.bsa``)
ships the Madness longsword's environment mask as

    textures\creationclub\bgssse025\weapons\madness\madness_longsword01_em.dds

but both its own meshes (``1stpersonmadnesssword.nif``, ``3rdpersonmadnesssword.nif``,
BSLightingShaderProperty [24], EnvironmentMap, EnvMapScale 0.25, cubemap
``opal_e``) and Believable Weapons 37737's loose replacements of those meshes
(same slot 5, plus a second shape [27] with ``Ore_Moonstone_e``) ask for

    textures\creationclub\bgssse025\weapons\madness\Madness_LongSword_01em.dds

The underscore sits on the wrong side of "01"; nothing in the load order ships
the asked-for name (records/envmask-missing-scan-2026-09-02.md), so the blade
renders with whatever the engine substitutes for a missing env mask. The typo
is Bethesda's (parsed from the CC BSA), Believable Weapons inherited it.

This overlay copies the CC texture, byte for byte, to the path the meshes ask
for. Vendor bytes (Bethesda Creation Club): ledger ``distribution: recipe``,
never committed or redistributed; the recipe is this script.

    py -3 overlays/ensrick-cc-madness-longsword-envmask-path-fix/build.py [--out DIR]

Reads the source straight out of the BSA with audit/modasset.py, verifies its
SHA-256 against the pinned value, writes ``payload/`` and the zip, prints the
hashes. Refuses on any hash mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "audit"))
import modasset as M  # noqa: E402

BSA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\ccbgssse025-advdsgs.bsa")
SOURCE_ENTRY = r"textures\creationclub\bgssse025\weapons\madness\madness_longsword01_em.dds"
SOURCE_SHA256 = "813B130D72E8A23FFFA60CF53FC7EA27CCDF60319192580132FC2F0A319C66FF"
SOURCE_BYTES = 2796336
TARGET_REL = "textures/creationclub/bgssse025/weapons/madness/madness_longsword_01em.dds"
ZIP_NAME = "ensrick-cc-madness-longsword-envmask-path-fix.zip"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_source() -> bytes:
    bsa = M.BSA(str(BSA))
    for i, (name, _off, _sz) in enumerate(bsa.entries):
        if name.lower() == SOURCE_ENTRY.lower():
            return bsa.read(i)
    raise SystemExit(f"{SOURCE_ENTRY} not found in {BSA}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE,
                    help="directory receiving payload/ and the zip (default: this overlay dir)")
    args = ap.parse_args(argv)

    data = read_source()
    got = sha256(data)
    if len(data) != SOURCE_BYTES or got != SOURCE_SHA256:
        raise SystemExit(f"source mismatch: {len(data)} B sha256 {got}; expected {SOURCE_BYTES} B {SOURCE_SHA256}")
    info = M.dds_info(data[:148])
    payload = args.out / "payload"
    dst = payload / Path(TARGET_REL)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    zip_path = args.out / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(dst, TARGET_REL.replace("/", "\\"))
    print(f"source:  {BSA.name}::{SOURCE_ENTRY}  {len(data)} B  sha256={got}  {info}")
    print(f"output:  {TARGET_REL}  sha256={sha256(dst.read_bytes())}")
    print(f"payload: {payload}")
    print(f"zip:     {zip_path}  sha256={sha256(zip_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
