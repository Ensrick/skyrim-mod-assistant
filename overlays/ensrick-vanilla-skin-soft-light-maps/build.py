r"""Build the vanilla skin soft-light (subsurface `_sk`) map overlay (#165 / #166).

The vanilla skin shader adds a wrapped "soft light" term,
``diffuse += light * GetSoftLightMultiplier(NdotL) * rimSoftLightColor``
(Community Shaders ``Common/LightingEval.hlsli:119``), where
``rimSoftLightColor`` is the texel of the ``_sk`` map bound in slot 2 of every
skin and facegen shape. Both decided skin sets replace those maps with
stubs: Reverie 1.11.2 ships 4x4 black ``FemaleHead_SK / FemaleBody_1_SK /
FemaleHands_1_SK``, The New Gentleman 4.2.5 ships 4x4 black
``malehead_sk / malebody_1_sk / malehands_1_sk``; CBBE's are near-black
(mean 0.03-0.06 vs vanilla 0.37). With the term zeroed, shadowed skin is lit
by direct diffuse only: matte bodies (#166) and hard eye sockets (#165);
Advanced Skin (#144, off) is not there to fill in.

This overlay puts Bethesda's own six ``_sk`` maps back, byte for byte, from
``Skyrim - Textures0.bsa`` so they win over every loose stub. Vanilla bytes:
ledger ``distribution: recipe``; never committed, never redistributed. The
recipe is this script, pinned to the BSA entries' SHA-256.

    py -3 overlays/ensrick-vanilla-skin-soft-light-maps/build.py [--out DIR] [--json]

Reads the game's BSA read-only, verifies each extracted entry against the
pinned hash and size, writes ``payload/`` (Data-root tree) and the zip under
--out (default: this overlay dir), prints the hashes. Refuses on mismatch.
A/B in game: enable or disable this one mod; nothing else changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "audit"))
import modasset as M  # noqa: E402

BSA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\Skyrim - Textures0.bsa")
# (path inside the BSA and in the payload, sha256, bytes) - pinned 2026-09-02 from the
# user's own install; every entry is 256-512 px BC1 with a full mip chain.
FILES = (
    ("textures/actors/character/female/femalehead_sk.dds",
     "56886605023D4E2A7BF336A1A313A8AB78238498928341164C247490064BD1F6", 43824),     # 256x256 BC1, 8 mips
    ("textures/actors/character/female/femalebody_1_sk.dds",
     "5E8011B972B8C32457041570E84F33CACEB5A204D198921BE781CCDDD7DB231C", 43824),     # 256x256 BC1, 8 mips
    ("textures/actors/character/female/femalehands_1_sk.dds",
     "A25C247D4663E7CFD06B609172BDCB258F61474731FE9B4626C5D1D6CCE06071", 21976),     # 256x128 BC1, 7 mips
    ("textures/actors/character/male/malehead_sk.dds",
     "E1F64ECC18D564FB1CA2F076A3647C40F70FBC1BB4A7061AB6487BC0E8E9F731", 174896),    # 512x512 BC1, 9 mips
    ("textures/actors/character/male/malebody_1_sk.dds",
     "DCE2DDD647BD7B573D0AD2BF638D48125A601923CC9E145EE606149900175892", 43824),     # 256x256 BC1, 8 mips
    ("textures/actors/character/male/malehands_1_sk.dds",
     "0EBB020F1C281AD2FC06A3366F8EA074C5199D02DCE320EEAF68E8FF1713A438", 21976),     # 256x128 BC1, 7 mips
)
ZIP_NAME = "ensrick-vanilla-skin-soft-light-maps.zip"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def bsa_entries() -> dict[str, bytes]:
    arc = M.BSA(str(BSA))
    want = {p for p, _h, _b in FILES}
    out: dict[str, bytes] = {}
    for i, (name, _off, _szf) in enumerate(arc.entries):
        key = name.replace("\\", "/").lower()
        if key in want and key not in out:
            out[key] = arc.read(i)
    missing = sorted(want - set(out))
    if missing:
        raise SystemExit("not in %s: %s" % (BSA.name, ", ".join(missing)))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE,
                    help="directory receiving payload/ and the zip (default: this overlay dir)")
    ap.add_argument("--json", action="store_true", help="print a machine-readable hash report")
    ap.add_argument("--pin", action="store_true",
                    help="print the hashes read from the BSA instead of enforcing the pins (first run only)")
    args = ap.parse_args(argv)
    if not BSA.exists():
        print(f"missing {BSA}")
        return 2
    data = bsa_entries()
    report = []
    problems = []
    for rel, pinned, size in FILES:
        blob = data[rel]
        h = sha256(blob)
        info = M.dds_info(blob[:148]) or {}
        report.append({"path": rel, "sha256": h, "bytes": len(blob), "dds": info})
        if args.pin:
            continue
        if len(blob) != size:
            problems.append(f"{rel}: {len(blob)} bytes, expected {size}")
        if pinned != h:
            problems.append(f"{rel}: sha256 {h} != pinned {pinned}")
    if args.pin:
        print(json.dumps(report, indent=1))
        return 0
    if problems:
        print("REFUSING - BSA content does not match the pinned vanilla maps:")
        for p in problems:
            print("  " + p)
        return 3
    payload = args.out / "payload"
    for rel, _p, _s in FILES:
        dst = payload / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data[rel])
    zip_path = args.out / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, _p, _s in FILES:
            zf.write(payload / Path(rel), rel)
    zip_hash = sha256(zip_path.read_bytes())
    if args.json:
        print(json.dumps({"files": report, "payload": str(payload), "zip": str(zip_path),
                          "zipSha256": zip_hash, "zipBytes": zip_path.stat().st_size, "bsa": str(BSA)}, indent=1))
    else:
        for r in report:
            print(f"{r['path']}  {r['bytes']} B  {r['dds'].get('w')}x{r['dds'].get('h')} {r['dds'].get('fmt')} mips={r['dds'].get('mips')}  sha256={r['sha256']}")
        print(f"payload: {payload}")
        print(f"zip:     {zip_path}  sha256={zip_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
