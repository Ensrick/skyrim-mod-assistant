#!/usr/bin/env python3
"""Normalize path-dependent PEX header metadata for reproducible owned builds."""

from __future__ import annotations

import argparse
from pathlib import Path


PEX_MAGIC = bytes.fromhex("FA57C0DE")
FIXED_UNIX_TIME = 946684800  # 2000-01-01T00:00:00Z


def replace_header_string(data: bytearray, offset: int,
                          replacement: str | None, label: str) -> int:
    if offset + 2 > len(data):
        raise SystemExit(f"truncated Skyrim PEX {label} header field")
    original_length = int.from_bytes(data[offset:offset + 2], "big")
    original_end = offset + 2 + original_length
    if original_end > len(data):
        raise SystemExit(f"invalid Skyrim PEX {label} header length")
    if replacement is None:
        return original_end
    normalized = replacement.encode("utf-8")
    if len(normalized) > 0xFFFF:
        raise SystemExit(f"normalized PEX {label} exceeds 65535 bytes")
    data[offset:original_end] = len(normalized).to_bytes(2, "big") + normalized
    return offset + 2 + len(normalized)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pex", type=Path)
    parser.add_argument("--source-name")
    parser.add_argument("--user-name")
    parser.add_argument("--machine-name")
    args = parser.parse_args()
    path = args.pex.resolve()
    data = bytearray(path.read_bytes())
    if len(data) < 16 or data[:4] != PEX_MAGIC:
        raise SystemExit(f"not a Skyrim PEX file: {path}")
    data[8:16] = FIXED_UNIX_TIME.to_bytes(8, "big")
    offset = replace_header_string(data, 16, args.source_name, "source-name")
    offset = replace_header_string(data, offset, args.user_name, "user-name")
    replace_header_string(data, offset, args.machine_name, "machine-name")
    path.write_bytes(data)
    print(f"normalized PEX header timestamp/source/user/machine metadata: {path}")


if __name__ == "__main__":
    main()
