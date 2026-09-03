"""Build the local VHR SMP NPC compatibility overlay.

Two independent corrections are deliberately kept above the unmodified VHR
NPC BSA:

* VHR 1.0.1's NPC BSA contains three Dawnguard Snow Elf FaceGen meshes that
  still reference the removed ``darkelf01.xml``.  The current 1.0.3 main
  ships the sex-specific replacement ``darkelf01m.xml``.
* VHR's archive otherwise wins 29 FaceGen paths also supplied by USSEP.  Some
  of those accompany deliberate race, sex, head-part, or morph corrections.
  The author says head-changing mods should win rather than be combined, so
  this overlay preserves the exact USSEP meshes at all 29 paths.

No vendor file is modified.  The generated loose files remain local and are
not suitable for redistribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


XML_FIX_TARGETS = (
    r"meshes\actors\character\facegendata\facegeom\dawnguard.esm\00002b44.nif",
    r"meshes\actors\character\facegendata\facegeom\dawnguard.esm\00003788.nif",
    r"meshes\actors\character\facegendata\facegeom\dawnguard.esm\0000a8b0.nif",
)
OLD_XML = r"meshes\actors\character\character assets\hair\smp\darkelf01.xml"
NEW_XML = r"meshes\actors\character\character assets\hair\smp\darkelf01m.xml"
EXPECTED_USSEP_OVERLAPS = 29


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write(output: Path, relative: str, data: bytes) -> None:
    destination = output / Path(relative.replace("\\", "/"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vhr_bsa", type=Path)
    parser.add_argument("ussep_bsa", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo / "audit"))
    import modasset  # pylint: disable=import-error,import-outside-toplevel

    vhr = modasset.BSA(str(args.vhr_bsa.resolve()))
    ussep = modasset.BSA(str(args.ussep_bsa.resolve()))
    vhr_names = {name.lower(): index for index, name in enumerate(vhr.names())}
    ussep_names = {name.lower(): index for index, name in enumerate(ussep.names())}
    overlaps = sorted(set(vhr_names) & set(ussep_names))
    if len(overlaps) != EXPECTED_USSEP_OVERLAPS:
        raise SystemExit(
            f"expected {EXPECTED_USSEP_OVERLAPS} VHR/USSEP FaceGen overlaps, "
            f"found {len(overlaps)}"
        )
    if any(
        not path.startswith("meshes\\actors\\character\\facegendata\\facegeom\\")
        or not path.endswith(".nif")
        for path in overlaps
    ):
        raise SystemExit("VHR/USSEP overlap set contains a non-FaceGen path")

    manifest = []
    for relative in overlaps:
        data = ussep.read(ussep_names[relative])
        if not modasset.nif_info(data):
            raise SystemExit(f"USSEP NIF validation failed for {relative}")
        write(args.output, relative, data)
        manifest.append(
            {
                "path": relative,
                "action": "preserve-ussep-facegen",
                "outputSha256": sha256(data),
                "outputBytes": len(data),
            }
        )

    old_record = struct.pack("<I", len(OLD_XML)) + OLD_XML.encode("ascii")
    new_record = struct.pack("<I", len(NEW_XML)) + NEW_XML.encode("ascii")
    for relative in XML_FIX_TARGETS:
        index = vhr_names.get(relative.lower())
        if index is None:
            raise SystemExit(f"VHR BSA is missing {relative}")
        source = vhr.read(index)
        if source.count(old_record) != 1:
            raise SystemExit(f"expected one obsolete XML string in {relative}")
        result = source.replace(old_record, new_record)
        info = modasset.nif_info(result)
        if not info or NEW_XML not in info["strings"] or OLD_XML in info["strings"]:
            raise SystemExit(f"post-edit NIF validation failed for {relative}")
        write(args.output, relative, result)
        manifest.append(
            {
                "path": relative,
                "action": "repair-vhr-xml-reference",
                "sourceSha256": sha256(source),
                "outputSha256": sha256(result),
                "sourceBytes": len(source),
                "outputBytes": len(result),
            }
        )

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
