#!/usr/bin/env python3
"""Normalize the PEX compile timestamp for reproducible owned builds."""

from __future__ import annotations

import sys
from pathlib import Path


PEX_MAGIC = bytes.fromhex("FA57C0DE")
FIXED_UNIX_TIME = 946684800  # 2000-01-01T00:00:00Z


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize_pex.py SCRIPT.pex")
    path = Path(sys.argv[1]).resolve()
    data = bytearray(path.read_bytes())
    if len(data) < 16 or data[:4] != PEX_MAGIC:
        raise SystemExit(f"not a Skyrim PEX file: {path}")
    data[8:16] = FIXED_UNIX_TIME.to_bytes(8, "big")
    path.write_bytes(data)
    print(f"normalized PEX timestamp to {FIXED_UNIX_TIME}: {path}")


if __name__ == "__main__":
    main()
