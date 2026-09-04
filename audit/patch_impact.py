r"""Identify owned patches/artifacts which must be reviewed for a mod change.

The scanner is conservative by design.  It proves candidate relationships from
hard masters, declared source-build inputs, normalized record overlap,
record-type selectors and asset globs.  A missing impact policy is a manual
review requirement, never evidence that an artifact is unaffected (#228).

It does not mutate a patch and it does not make a taste decision.

    py -3 audit/patch_impact.py --operation install --changed-mod "Some Mod"
    py -3 audit/patch_impact.py --operation update --changed-root C:\staged\mod
    py -3 audit/patch_impact.py --selftest
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esp import Plugin


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
LEDGER = REPO / "records" / "installed-mods.json"
GAME_DATA = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"
)
PLUGIN_SUFFIXES = {".esm", ".esp", ".esl"}


def key(value: object) -> str:
    return str(value or "").strip().casefold()


def enabled_mods(instance: pathlib.Path, profile: str) -> list[str]:
    path = instance / "profiles" / profile / "modlist.txt"
    if not path.exists():
        return []
    return [
        line[1:].strip() for line in path.read_text(
            encoding="utf-8-sig", errors="replace"
        ).splitlines()
        if line.startswith("+") and line[1:].strip()
    ]


def plugin_inventory(root: pathlib.Path) -> list[pathlib.Path]:
    if not root.is_dir():
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES),
        key=lambda p: p.name.casefold(),
    )


def relative_assets(root: pathlib.Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(
        (p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()),
        key=str.casefold,
    )


def effective_plugins(instance: pathlib.Path, profile: str,
                      game_data: pathlib.Path = GAME_DATA) -> dict[str, pathlib.Path]:
    """MO2 modlist is highest-priority first in this instance."""
    winners: dict[str, pathlib.Path] = {}
    for mod_name in enabled_mods(instance, profile):
        for path in plugin_inventory(instance / "mods" / mod_name):
            winners.setdefault(key(path.name), path)
    overwrite = instance / "overwrite"
    for path in plugin_inventory(overwrite):
        winners.setdefault(key(path.name), path)
    if game_data.is_dir():
        for path in plugin_inventory(game_data):
            winners.setdefault(key(path.name), path)
    return winners


def record_keys(path: pathlib.Path) -> tuple[set[tuple[str, str, int]], set[str], list[str]]:
    plugin = Plugin(str(path))
    records: set[tuple[str, str, int]] = set()
    types: set[str] = set()
    for record_type, form_id, _size in plugin.formids:
        record_name = record_type.decode("ascii", "replace")
        types.add(record_name)
        index = form_id >> 24
        origin = plugin.masters[index] if index < len(plugin.masters) else plugin.name
        records.add((record_name, key(origin), form_id & 0x00FFFFFF))
    return records, types, plugin.masters


def source_record_for(row: dict, records_dir: pathlib.Path) -> tuple[pathlib.Path | None, dict | None]:
    candidates: list[str] = []
    recipe = row.get("recipe")
    if isinstance(recipe, dict) and recipe.get("record"):
        candidates.append(str(recipe["record"]))
    for field in (row.get("note"), row.get("distributionBasis")):
        if field:
            candidates += re.findall(r"records/source-builds/[A-Za-z0-9_.-]+\.json", str(field))
    for candidate in candidates:
        path = pathlib.Path(candidate)
        if not path.is_absolute():
            path = REPO / path
        if path.exists():
            try:
                return path, json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue

    normalized_name = re.sub(r"[^a-z0-9]+", "", key(row.get("modName")))
    best = None
    for path in records_dir.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        component = re.sub(r"[^a-z0-9]+", "", key(document.get("component")))
        if component and (component == normalized_name or component in normalized_name or normalized_name in component):
            if best is None or len(component) > best[0]:
                best = (len(component), path, document)
    return (best[1], best[2]) if best else (None, None)


def owned_rows(ledger_path: pathlib.Path) -> list[dict]:
    document = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    out = []
    for row in document.get("mods", []):
        if row.get("enabled") is not True:
            continue
        name = str(row.get("modName") or "")
        try:
            mod_id = int(row.get("modId") or 0)
        except (TypeError, ValueError):
            mod_id = -1
        own = (mod_id == 0 and (
            name.startswith("Ensrick") or name.endswith("- Ensrick") or
            "Source Build" in name or name in {"LaunchProbe", "MenuPilot", "Period Underlayers - SPID"}
        )) or bool(row.get("distribution"))
        if own:
            out.append(row)
    return sorted(out, key=lambda row: key(row.get("modName")))


def evaluate_policy(policy: dict | None, changed_names: set[str],
                    changed_types: set[str], changed_assets: list[str]) -> tuple[list[str], bool]:
    if not policy:
        return ["impactPolicy missing"], True
    reasons: list[str] = []
    manual = False
    mode = key(policy.get("mode"))
    allowed_modes = {"declared-inputs", "record-types", "full-profile", "asset-paths", "manual"}
    if mode not in allowed_modes:
        reasons.append(f"impactPolicy has invalid mode: {mode or '(blank)'}")
        manual = True
    if mode == "full-profile":
        reasons.append("impactPolicy is full-profile")
    if mode == "manual":
        reasons.append("impactPolicy requires manual review")
        manual = True
    declared = {key(item) for item in policy.get("inputs", [])}
    matched = sorted(declared & changed_names)
    if matched:
        reasons.append("declared input changed: " + ", ".join(matched))
    selected_types = {str(item).upper() for item in policy.get("recordTypes", [])}
    overlap_types = sorted(selected_types & changed_types)
    if overlap_types:
        reasons.append("selected record type changed: " + ", ".join(overlap_types))
    globs = [str(item).casefold() for item in policy.get("assetGlobs", [])]
    matches = sorted({asset for asset in changed_assets
                      if any(fnmatch.fnmatch(asset.casefold(), pattern) for pattern in globs)})
    if matches:
        preview = matches[:5]
        reasons.append("selected asset path changed: " + ", ".join(preview)
                       + (f" (+{len(matches) - len(preview)} more)" if len(matches) > len(preview) else ""))
    return reasons, manual


def audit(operation: str, changed_roots: list[pathlib.Path], changed_names: list[str],
          instance: pathlib.Path = INSTANCE, profile: str = PROFILE,
          ledger_path: pathlib.Path = LEDGER) -> dict:
    instance = pathlib.Path(instance)
    ledger_path = pathlib.Path(ledger_path)
    roots: list[tuple[str, pathlib.Path]] = []
    for name in changed_names:
        root = instance / "mods" / name
        if not root.is_dir():
            raise FileNotFoundError(f"changed mod folder does not exist: {root}")
        roots.append((name, root))
    for root in changed_roots:
        path = pathlib.Path(root).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"changed root does not exist: {path}")
        roots.append((path.name, path))
    if not roots:
        raise ValueError("at least one changed mod/root is required")

    changed_plugin_paths = [path for _name, root in roots for path in plugin_inventory(root)]
    changed_assets = [asset for _name, root in roots for asset in relative_assets(root)]
    changed_name_keys = {key(name) for name, _root in roots}
    changed_name_keys |= {key(path.name) for path in changed_plugin_paths}
    changed_records: set[tuple[str, str, int]] = set()
    changed_types: set[str] = set()
    parse_errors: list[str] = []
    for path in changed_plugin_paths:
        try:
            records, types, _masters = record_keys(path)
            changed_records |= records
            changed_types |= types
        except Exception as exc:
            parse_errors.append(f"{path}: {type(exc).__name__}: {exc}")

    winners = effective_plugins(instance, profile)
    results = []
    policy_gaps = 0
    affected = 0
    for row in owned_rows(ledger_path):
        mod_name = str(row.get("modName"))
        record_path, source = source_record_for(row, REPO / "records" / "source-builds")
        policy = row.get("impactPolicy") or ((source or {}).get("impactPolicy"))
        reasons, manual = evaluate_policy(policy, changed_name_keys, changed_types, changed_assets)
        if not policy:
            policy_gaps += 1

        manifest_text = json.dumps(source or {}, sort_keys=True).casefold()
        mentioned = sorted(name for name in changed_name_keys if name and name in manifest_text)
        if mentioned:
            reasons.append("source-build record mentions changed input: " + ", ".join(mentioned))

        direct_count = 0
        hard_masters: set[str] = set()
        patch_parse_errors = []
        folder = instance / "mods" / mod_name
        for plugin_path in plugin_inventory(folder):
            effective = winners.get(key(plugin_path.name), plugin_path)
            try:
                patch_records, _types, masters = record_keys(effective)
                direct_count += len(patch_records & changed_records)
                hard_masters |= {m for m in masters if key(m) in changed_name_keys}
            except Exception as exc:
                patch_parse_errors.append(f"{effective}: {type(exc).__name__}: {exc}")
        if hard_masters:
            reasons.append("changed plugin is a hard master: " + ", ".join(sorted(hard_masters, key=str.casefold)))
        if direct_count:
            reasons.append(f"normalized record overlap: {direct_count} record(s)")

        observed = [r for r in reasons if r != "impactPolicy missing"]
        if observed:
            disposition = "candidate-impact"
            affected += 1
        elif manual or not policy:
            disposition = "manual-review-required"
        else:
            disposition = "no-observed-relation-review-required"
        if record_path:
            try:
                record_display = str(record_path.relative_to(REPO)).replace("\\", "/")
            except ValueError:
                record_display = str(record_path)
        else:
            record_display = None
        results.append({
            "artifact": mod_name,
            "sourceBuildRecord": record_display,
            "impactPolicy": policy,
            "disposition": disposition,
            "reasons": reasons,
            "patchParseErrors": patch_parse_errors,
            "requiredOutcome": "regenerated | amended | verified-current | not-affected | blocked-decision",
        })

    return {
        "schemaVersion": 1,
        "operation": operation,
        "changed": [{"name": name, "root": str(root)} for name, root in roots],
        "changedPlugins": [path.name for path in changed_plugin_paths],
        "changedRecordTypes": sorted(changed_types),
        "changedAssetCount": len(changed_assets),
        "changedPluginParseErrors": parse_errors,
        "summary": {
            "ownedArtifactsReviewed": len(results),
            "candidateImpacts": affected,
            "impactPolicyGaps": policy_gaps,
            "receiptComplete": False,
        },
        "artifacts": results,
        "receiptRule": "Every artifact needs one explicit requiredOutcome before activation (#228).",
    }


def render(result: dict) -> str:
    s = result["summary"]
    lines = [
        f"operation {result['operation']}; changed: " + ", ".join(row["name"] for row in result["changed"]),
        f"owned artifacts {s['ownedArtifactsReviewed']}; candidate impacts {s['candidateImpacts']}; "
        f"policy gaps {s['impactPolicyGaps']}",
    ]
    for row in result["artifacts"]:
        reason = "; ".join(row["reasons"]) or "no automatic relationship observed"
        lines.append(f"  {row['disposition']:<36} {row['artifact']}: {reason}")
    lines += ["", "INCOMPLETE: assign one evidenced outcome to every artifact before activation (#228)"]
    return "\n".join(lines)


def selftest() -> int:
    reasons, manual = evaluate_policy(
        {"mode": "record-types", "recordTypes": ["WEAP"]}, {"new weapons.esp"}, {"WEAP"}, []
    )
    assert not manual and any("WEAP" in reason for reason in reasons)
    reasons, manual = evaluate_policy(
        {"mode": "asset-paths", "assetGlobs": ["meshes/weapons/**"]}, set(), set(),
        ["meshes/weapons/test.nif", "textures/a.dds"],
    )
    assert not manual and any("test.nif" in reason for reason in reasons)
    reasons, manual = evaluate_policy({"mode": "full-profile"}, set(), set(), [])
    assert reasons == ["impactPolicy is full-profile"] and not manual
    reasons, manual = evaluate_policy(None, set(), set(), [])
    assert manual and reasons == ["impactPolicy missing"]
    reasons, manual = evaluate_policy({"mode": "typo"}, set(), set(), [])
    assert manual and any("invalid mode" in reason for reason in reasons)
    print("patch_impact selftest PASS (9 assertions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=False,
                        choices=("install", "update", "remove", "enable", "disable", "generate"))
    parser.add_argument("--changed-mod", action="append", default=[])
    parser.add_argument("--changed-root", action="append", type=pathlib.Path, default=[])
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--ledger", type=pathlib.Path, default=LEDGER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.operation:
        parser.error("--operation is required")
    result = audit(args.operation, args.changed_root, args.changed_mod,
                   args.instance, args.profile, args.ledger)
    text = json.dumps(result, indent=2) + "\n" if args.json or args.out else render(result) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    # A scan is intentionally incomplete until a reviewed receipt assigns the
    # final outcomes. Exit 2 distinguishes that from a tool failure.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
