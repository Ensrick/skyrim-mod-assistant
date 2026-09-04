#!/usr/bin/env python3
"""Read-only oracle for the six ECE null-Location script corrections."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMMENT = "    ; Ensrick compatibility fix: Location may validly be None during transitions.\n"
FUNCTION = "function OnLocationChange(location akOldLoc, location akNewLoc)\n\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def normalized(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def replace_once(text: str, before: str, after: str, label: str) -> str:
    require(text.count(before) == 1, f"{label}: expected one exact source occurrence")
    return text.replace(before, after, 1)


def expected_single_region(source: str, keyword: str, label: str) -> str:
    source = replace_once(
        source,
        FUNCTION,
        FUNCTION + COMMENT + "    Bool newIsRegion = false\n    Bool oldWasRegion = false\n\n",
        f"{label} function",
    )
    source = replace_once(
        source,
        f'    if akNewLoc.hasKeywordString("{keyword}")',
        (
            "    if akNewLoc\n"
            f'        newIsRegion = akNewLoc.hasKeywordString("{keyword}")\n'
            "    endIf\n"
            "    if akOldLoc\n"
            f'        oldWasRegion = akOldLoc.hasKeywordString("{keyword}")\n'
            "    endIf\n"
            "    if newIsRegion"
        ),
        f"{label} new-location dereference",
    )
    return replace_once(
        source,
        f'        if !akOldLoc.hasKeywordString("{keyword}")',
        "        if !oldWasRegion",
        f"{label} old-location dereference",
    )


def expected_regional_default(source: str, label: str) -> str:
    new_expression = (
        '    if !akNewLoc.hasKeywordString("isUlfmoney") && '
        '!akNewLoc.hasKeywordString("isDramMoney") && '
        '!akNewLoc.hasKeywordString("isDrakrMoney") && '
        '!akNewLoc.hasKeywordString("isMedeMoney") && '
        '!akNewLoc.hasKeywordString("isOshMoney") && '
        '!akNewLoc.hasKeywordString("isOhzermoney") && '
        '!akNewLoc.hasKeywordString("isVarkenMoney")'
    )
    old_expression = (
        '        if akOldLoc.hasKeywordString("isUlfmoney") || '
        'akOldLoc.hasKeywordString("isDramMoney") || '
        'akOldLoc.hasKeywordString("isDrakrMoney") || '
        'akOldLoc.hasKeywordString("isMedeMoney") || '
        'akOldLoc.hasKeywordString("isOshMoney") || '
        'akOldLoc.hasKeywordString("isOhzermoney") || '
        'akOldLoc.hasKeywordString("isVarkenMoney")'
    )
    guarded_new_expression = (
        new_expression.removeprefix("    if !")
        .replace("!akNewLoc", "akNewLoc")
        .replace(" && ", " || ")
    )
    guarded_old_expression = old_expression.removeprefix("        if ")
    source = replace_once(
        source,
        FUNCTION,
        FUNCTION + COMMENT +
        "    Bool newUsesRegionalCurrency = false\n"
        "    Bool oldUsedRegionalCurrency = false\n\n",
        f"{label} function",
    )
    source = replace_once(
        source,
        new_expression,
        (
            "    if akNewLoc\n"
            f"        newUsesRegionalCurrency = {guarded_new_expression}\n"
            "    endIf\n"
            "    if akOldLoc\n"
            f"        oldUsedRegionalCurrency = {guarded_old_expression}\n"
            "    endIf\n"
            "    if !newUsesRegionalCurrency"
        ),
        f"{label} new-location dereferences",
    )
    return replace_once(
        source,
        old_expression,
        "        if oldUsedRegionalCurrency",
        f"{label} old-location dereferences",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-root", required=True, type=Path)
    args = parser.parse_args()
    inputs = json.loads((ROOT / "build-inputs.json").read_text(encoding="utf-8"))
    specs = inputs["eceLocationGuardSources"]
    require(len(specs) == 6, "expected exactly six ECE location-handler scripts")
    require({item["script"]: item["expectedCompilerWarnings"] for item in specs} == {
                "EC_septimsScript": 13,
                "EC_drakrsScript": 1,
                "EC_dramsScript": 1,
                "EC_medesScript": 1,
                "EC_oshkasScript": 1,
                "EC_ulfricsScript": 1,
            }, "pinned unchanged-vendor compiler-warning budget changed")

    for spec in specs:
        source_path = args.instance_root / spec["sourceRelativePathFromInstance"]
        patched_path = ROOT / spec["patchedRelativePath"]
        source_bytes = source_path.read_bytes()
        require(len(source_bytes) == spec["sourceBytes"],
                f"{spec['script']}: vendor source byte count changed")
        require(hashlib.sha256(source_bytes).hexdigest().upper() == spec["sourceSha256"],
                f"{spec['script']}: vendor source hash changed")
        source = normalized(source_bytes.decode("utf-8-sig"))
        if spec["mode"] == "singleRegion":
            expected = expected_single_region(source, spec["keyword"], spec["script"])
        else:
            require(spec["mode"] == "regionalDefault",
                    f"{spec['script']}: unsupported guard mode")
            expected = expected_regional_default(source, spec["script"])
        actual = normalized(patched_path.read_text(encoding="utf-8-sig"))
        require(actual == expected,
                f"{spec['script']}: patched source differs beyond the exact null guards")

    print("PASS: six pinned ECE 4.1.1 scripts differ only by explicit old/new Location guards")


if __name__ == "__main__":
    main()
