r"""Build the Skyland AIO Solitude manhole texture-path overlay (#159 sweep follow-up).

Skyland AIO 1K 34179 (v4.32) replaces ``meshes\architecture\solitude\smanhole.nif``
with a mesh whose manhole-cover shape (BSLightingShaderProperty [10]) is an
EnvironmentMap shader, EnvMapScale 1.5, asking for

    textures\arechitecture\solitude\smanhole_e.dds   (slot 4, cubemap)
    textures\arechitecture\solitude\smanhole_m.dds   (slot 5, env mask)

"arechitecture" is misspelled; Skyland ships both files under the correctly
spelled ``textures\architecture\solitude\`` and nothing in the load order
ships the misspelled paths (records/envmask-missing-scan-2026-09-02.md). Vanilla's
``smanhole.nif`` is a plain Default shader with no slot 4/5, so the reflection
is Skyland's own authoring and a black mask would be wrong; the fix is to
supply the author's textures where the mesh looks for them.

This overlay copies Skyland's two textures, byte for byte, to the misspelled
folder. Vendor bytes (Skyland terms are restrictive): ledger ``distribution:
recipe``, never committed or redistributed; the recipe is this script.

    py -3 overlays/ensrick-skyland-smanhole-texture-path-fix/build.py [--out DIR]

Reads the installed vendor files, verifies each SHA-256 against the pinned
value, writes ``payload/`` and the zip, prints the hashes. Refuses on mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "audit"))
import modasset as M  # noqa: E402

VENDOR = Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se\mods\Skyland AIO 1K")
FILES = (
    # (vendor relative path, sha256, bytes, target relative path the mesh asks for)
    ("textures/architecture/solitude/smanhole_m.dds",
     "D8F956EF9DF817509D721025BDF4376F9D8A3E362C5DEF78E4B9859E5ECC739F", 699192,
     "textures/arechitecture/solitude/smanhole_m.dds"),
    ("textures/architecture/solitude/smanhole_e.dds",
     "4522140D77612BFC33B1CECA88F5DC3E8AD4B4D36435B43246E69CD1E8F2995A", 65744,
     "textures/arechitecture/solitude/smanhole_e.dds"),
)
ZIP_NAME = "ensrick-skyland-smanhole-texture-path-fix.zip"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=HERE,
                    help="directory receiving payload/ and the zip (default: this overlay dir)")
    args = ap.parse_args(argv)

    payload = args.out / "payload"
    zip_path = args.out / ZIP_NAME
    written = []
    for src_rel, want, size, dst_rel in FILES:
        src = VENDOR / Path(src_rel)
        data = src.read_bytes()
        got = sha256(data)
        if len(data) != size or got != want:
            raise SystemExit(f"source mismatch for {src_rel}: {len(data)} B sha256 {got}; expected {size} B {want}")
        dst = payload / Path(dst_rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        written.append(dst_rel)
        print(f"source:  Skyland AIO 1K/{src_rel}  {len(data)} B  sha256={got}  {M.dds_info(data[:148])}")
        print(f"output:  {dst_rel}  sha256={sha256(dst.read_bytes())}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in written:
            zf.write(payload / Path(rel), rel.replace("/", "\\"))
    print(f"payload: {payload}")
    print(f"zip:     {zip_path}  sha256={sha256(zip_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
