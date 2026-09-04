#!/usr/bin/env python3
"""Validate and package the owned RMB Core duplicate-outfit shadow (#200).

The game-data fix is the hand-authored, comment-only INI in the existing
``Ensrick - Cloak Distribution Balance`` overlay.  This tool does not generate
that configuration.  It fails closed unless the two RMB Core 6.3.0 vendor
inputs still match the audited duplicate byte-for-byte, validates that the
owned overlay contains exactly the pinned files, and writes a deterministic
MO2-installable ZIP containing owned bytes only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OVERLAY_ROOT = REPO / "overlays" / "ensrick-cloak-distribution-balance"
ISSUE = "https://github.com/Ensrick/skyrim-mod-assistant/issues/200"
VERSION = "2026-09-04.1"
FIXED_ZIP_TIME = (2000, 1, 1, 0, 0, 0)

VENDOR_PATHS = (
    "SKSE/Plugins/SkyPatcher/outfit/Cloaks/RMB SPID - Core Definitions.esp.ini",
    "SKSE/Plugins/SkyPatcher/outfit/Headgear/RMB SPID - Core Definitions.esp.ini",
)
VENDOR_SHA256 = "B3AA37FA441FCBA10BB4CB219866F9B9C312DDD2CCF746F78ECE580D2AA9D9EA"
VENDOR_BYTES = 9623
VENDOR_OUTFIT_DIRECTIVES = 58

SHADOW_PATH = VENDOR_PATHS[1]
OWNED_FILES = {
    "SKSE/Plugins/SkyPatcher/leveledList/zz Ensrick Cloak Balance/Ensrick - Cloak Balance.ini": {
        "bytes": 11305,
        "sha256": "6A51AA41BD0B4E5B5102141171785B7CACD34DBB8EF60EBB8B246ABA5AA1E47A",
    },
    SHADOW_PATH: {
        "bytes": 1060,
        "sha256": "A8AC4627CAF91DB255295F0EA54AD79748DF695897E84F4D94AFBF34E21BF2D9",
    },
}


class ValidationError(RuntimeError):
    """The audited input or owned output no longer matches its pin."""


@dataclass(frozen=True)
class VendorPin:
    paths: tuple[str, str] = VENDOR_PATHS
    sha256: str = VENDOR_SHA256
    size: int = VENDOR_BYTES
    outfit_directives: int = VENDOR_OUTFIT_DIRECTIVES


@dataclass(frozen=True)
class OwnedSnapshot:
    """One immutable read of the validated files that will enter the ZIP."""

    entries: tuple[tuple[str, bytes], ...]

    def names(self) -> list[str]:
        return [rel for rel, _data in self.entries]

    def details(self) -> list[dict]:
        return [
            {"path": rel, "bytes": len(data), "sha256": sha256(data)}
            for rel, data in self.entries
        ]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def active_lines(data: bytes) -> list[bytes]:
    """Return non-empty, non-comment SkyPatcher lines without decoding."""
    return [
        line.strip()
        for line in data.splitlines()
        if line.strip() and not line.lstrip().startswith((b";", b"#"))
    ]


def validate_vendor(vendor_root: Path, pin: VendorPin = VendorPin()) -> dict:
    """Validate that both exact vendor paths are the pinned accidental copy."""
    payloads: list[bytes] = []
    details = []
    for rel in pin.paths:
        path = vendor_root / Path(rel)
        if not path.is_file():
            raise ValidationError(f"missing pinned vendor input: {path}")
        data = path.read_bytes()
        payloads.append(data)
        details.append({"path": rel, "bytes": len(data), "sha256": sha256(data)})

    if payloads[0] != payloads[1]:
        raise ValidationError(
            "the Cloaks and Headgear vendor files are no longer byte-identical; "
            "the upstream defect changed and this shadow must be re-audited"
        )

    data = payloads[0]
    got_hash = sha256(data)
    if len(data) != pin.size or got_hash != pin.sha256.upper():
        raise ValidationError(
            f"vendor duplicate mismatch: {len(data)} bytes sha256 {got_hash}; "
            f"expected {pin.size} bytes sha256 {pin.sha256.upper()}"
        )

    count = sum(line.lower().startswith(b"filterbyoutfits=") for line in active_lines(data))
    if count != pin.outfit_directives:
        raise ValidationError(
            f"vendor duplicate has {count} filterByOutfits directives; "
            f"expected {pin.outfit_directives}"
        )

    return {
        "provider": "RMB SPIDified - Core Framework",
        "version": "6.3.0",
        "files": details,
        "byteIdentical": True,
        "filterByOutfitsDirectivesPerFile": count,
    }


def validate_owned(overlay_root: Path = OVERLAY_ROOT) -> OwnedSnapshot:
    """Read once, validate, and return the exact immutable bytes to package."""
    actual = {
        path.relative_to(overlay_root).as_posix()
        for path in overlay_root.rglob("*")
        if path.is_file()
    }
    expected = set(OWNED_FILES)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValidationError(f"owned overlay file set changed; missing={missing}, extra={extra}")

    entries = []
    for rel in sorted(OWNED_FILES):
        data = (overlay_root / Path(rel)).read_bytes()
        if rel == SHADOW_PATH:
            directives = active_lines(data)
            if directives:
                preview = directives[0][:120].decode("ascii", "replace")
                raise ValidationError(
                    f"owned Headgear shadow is not comment-only; first active line: {preview}"
                )
            if VENDOR_SHA256.encode("ascii") not in data:
                raise ValidationError("owned Headgear shadow does not state the audited vendor SHA-256 pin")
        wanted = OWNED_FILES[rel]
        got_hash = sha256(data)
        if len(data) != wanted["bytes"] or got_hash != wanted["sha256"]:
            raise ValidationError(
                f"owned file mismatch for {rel}: {len(data)} bytes sha256 {got_hash}; "
                f"expected {wanted['bytes']} bytes sha256 {wanted['sha256']}"
            )
        entries.append((rel, data))
    return OwnedSnapshot(tuple(entries))


def write_archive(output: Path, snapshot: OwnedSnapshot) -> dict:
    """Write and verify a ZIP using only the already-validated byte snapshot."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for rel, data in snapshot.entries:
            info = zipfile.ZipInfo(rel, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)

    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        if names != snapshot.names():
            raise ValidationError(f"archive member set/order mismatch: {names}")
        if archive.testzip() is not None:
            raise ValidationError("archive CRC verification failed")
        for rel, data in snapshot.entries:
            if archive.read(rel) != data:
                raise ValidationError(f"archive payload mismatch: {rel}")

    return {"path": output.name, "bytes": output.stat().st_size, "sha256": sha256(output.read_bytes())}


def build(vendor_root: Path, output: Path, overlay_root: Path = OVERLAY_ROOT,
          pin: VendorPin = VendorPin()) -> dict:
    vendor = validate_vendor(vendor_root, pin)
    owned = validate_owned(overlay_root)
    artifact = write_archive(output, owned)
    manifest = {
        "schemaVersion": 1,
        "component": "Ensrick - Cloak Distribution Balance",
        "version": VERSION,
        "issue": ISSUE,
        "purpose": "Shadow the erroneous second RMB Core cloak outfit injector at its exact Headgear virtual path.",
        "vendorInput": vendor,
        "ownedFiles": owned.details(),
        "artifact": artifact,
        "containsVendorBytes": False,
    }
    sidecar = output.with_name(output.name + ".manifest.json")
    sidecar.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vendor-root", type=Path, required=True,
                        help="installed/extracted RMB Core 6.3.0 Data-root folder (read-only input)")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "dist" / "issue-200" / f"Ensrick-Cloak-Distribution-Balance-{VERSION}.zip",
        help="MO2-installable ZIP path (default: dist/issue-200/...)",
    )
    parser.add_argument("--verify-only", action="store_true",
                        help="validate pins and payload without writing an archive")
    args = parser.parse_args(argv)

    try:
        vendor = validate_vendor(args.vendor_root)
        owned = validate_owned()
        if args.verify_only:
            print(json.dumps({"vendorInput": vendor, "ownedFiles": owned.details()}, indent=2))
            return 0
        manifest = build(args.vendor_root, args.output)
        print(json.dumps(manifest, indent=2))
        print(f"manifest: {args.output.with_name(args.output.name + '.manifest.json')}")
        return 0
    except (OSError, ValidationError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
