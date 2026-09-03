#!/usr/bin/env python3
"""Validate and create the deterministic MO2 archive."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "package"
VERSION = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]
OUTPUT = ROOT / "work" / f"Ensrick-Regional-Currency-Integration-{VERSION}.zip"
FIXED_TIME = (2000, 1, 1, 0, 0, 0)


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "validate.py")], check=True)
    files = sorted(path for path in PACKAGE.rglob("*") if path.is_file())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(PACKAGE).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest().upper()
    print(f"{OUTPUT}\nfiles={len(files)} bytes={OUTPUT.stat().st_size} sha256={digest}")


if __name__ == "__main__":
    main()
