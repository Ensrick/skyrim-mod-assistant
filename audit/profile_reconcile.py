"""Reconcile the four authorities that describe the live MO2 profile.

The physical mod tree, ``modlist.txt``, ``plugins.txt`` and
``records/installed-mods.json`` must describe the same build.  Looking only at
ledger rows is not verification: a mod which bypassed ``install_mod.py`` is
then invisible by construction (issue #102).

This module is deliberately read-only.  ``--adoption-plan`` emits the exact
stub facts an operator needs to adopt unledgered folders, but it never invents
provenance or edits the ledger.  A later, reviewed lifecycle transaction owns
that write.

    py -3 audit/profile_reconcile.py
    py -3 audit/profile_reconcile.py --json
    py -3 audit/profile_reconcile.py --adoption-plan
    py -3 audit/profile_reconcile.py --selftest

Exit 0 means all four authorities agree.  Exit 1 means the profile is not a
reproducible state and must not be launched or changed again until reconciled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import tempfile
from collections import defaultdict


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
LEDGER = REPO / "records" / "installed-mods.json"
GAME_DATA = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"
)
PLUGIN_SUFFIXES = {".esm", ".esp", ".esl"}


def _key(value: object) -> str:
    return str(value or "").strip().casefold()


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def _read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_modlist(path: pathlib.Path) -> tuple[dict[str, dict], list[dict]]:
    rows: dict[str, dict] = {}
    duplicates: list[dict] = []
    if not path.exists():
        return rows, duplicates
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
    ):
        if not raw or raw.startswith("#") or raw[0] not in "+-*":
            continue
        # '*' rows are MO2's unmanaged game/DLC entries, not directories in
        # the managed mods tree and therefore not ledger subjects.
        if raw[0] == "*":
            continue
        name = raw[1:].strip()
        if not name:
            continue
        key = _key(name)
        row = {"name": name, "enabled": raw[0] == "+", "line": line_number}
        if key in rows:
            duplicates.append({"name": name, "lines": [rows[key]["line"], line_number]})
        rows[key] = row
    return rows, duplicates


def parse_plugins(path: pathlib.Path) -> tuple[dict[str, dict], list[dict]]:
    rows: dict[str, dict] = {}
    duplicates: list[dict] = []
    if not path.exists():
        return rows, duplicates
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
    ):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        active = raw.startswith("*")
        name = raw[1:].strip() if active else raw
        if pathlib.Path(name).suffix.casefold() not in PLUGIN_SUFFIXES:
            continue
        key = _key(name)
        row = {"name": name, "active": active, "line": line_number}
        if key in rows:
            duplicates.append({"name": name, "lines": [rows[key]["line"], line_number]})
        rows[key] = row
    return rows, duplicates


def physical_mods(mods_dir: pathlib.Path) -> dict[str, dict]:
    rows = {}
    if not mods_dir.exists():
        return rows
    for path in sorted((p for p in mods_dir.iterdir() if p.is_dir()), key=lambda p: p.name.casefold()):
        if path.name.startswith(".") or path.name.endswith("_separator"):
            continue
        plugins = sorted(
            (p.name for p in path.iterdir() if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES),
            key=str.casefold,
        )
        rows[_key(path.name)] = {
            "name": path.name,
            "path": str(path),
            "plugins": plugins,
            "nexusId": metadata_nexus_id(path / "meta.ini"),
        }
    return rows


def metadata_nexus_id(path: pathlib.Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(r"^\s*modid\s*=\s*(\d+)\s*$", text, re.I | re.M)
    if match and int(match.group(1)) > 0:
        return int(match.group(1))
    match = re.search(r"^\s*installationFile\s*=\s*(.*?)\s*$", text, re.I | re.M)
    if match:
        filename = pathlib.PurePath(match.group(1).replace("\\", "/")).name
        inferred = re.match(r"^(\d+)-\d+(?:\.|$)", filename)
        if inferred and int(inferred.group(1)) > 0:
            return int(inferred.group(1))
    return None


def _ledger_rows(path: pathlib.Path) -> tuple[list[dict], dict[str, dict], list[dict]]:
    document = _read_json(path)
    source = document.get("mods", [])
    by_name: dict[str, dict] = {}
    duplicates = []
    for index, row in enumerate(source):
        name = str(row.get("modName") or "").strip()
        key = _key(name)
        if not key:
            duplicates.append({"name": "", "rows": [index], "reason": "blank modName"})
            continue
        if key in by_name:
            duplicates.append({"name": name, "reason": "duplicate modName"})
        by_name[key] = row
    return source, by_name, duplicates


def _problem(code: str, message: str, **details) -> dict:
    return {"code": code, "message": message, **details}


def reconcile(
    instance: pathlib.Path = INSTANCE,
    profile: str = PROFILE,
    ledger_path: pathlib.Path = LEDGER,
    game_data: pathlib.Path = GAME_DATA,
) -> dict:
    instance = pathlib.Path(instance)
    ledger_path = pathlib.Path(ledger_path)
    profile_dir = instance / "profiles" / profile
    physical = physical_mods(instance / "mods")
    modlist, modlist_dupes = parse_modlist(profile_dir / "modlist.txt")
    plugins, plugin_dupes = parse_plugins(profile_dir / "plugins.txt")
    ledger_rows, ledger, ledger_dupes = _ledger_rows(ledger_path)

    errors: list[dict] = []
    warnings: list[dict] = []
    adoption: list[dict] = []

    for row in modlist_dupes:
        errors.append(_problem("duplicate-modlist-row", f"duplicate modlist row: {row['name']}", **row))
    for row in plugin_dupes:
        errors.append(_problem("duplicate-plugin-row", f"duplicate plugins.txt row: {row['name']}", **row))
    for row in ledger_dupes:
        errors.append(_problem("duplicate-ledger-row", f"invalid/duplicate ledger row: {row['name']!r}", **row))

    for key, disk in physical.items():
        state = modlist.get(key)
        row = ledger.get(key)
        if state is None:
            errors.append(_problem(
                "physical-mod-not-in-modlist",
                f"physical mod folder has no modlist row: {disk['name']}",
                modName=disk["name"],
            ))
        if row is None:
            enabled = bool(state and state["enabled"])
            errors.append(_problem(
                "unledgered-physical-mod",
                f"physical mod has no ledger row: {disk['name']} ({'enabled' if enabled else 'disabled'})",
                modName=disk["name"], enabled=enabled, nexusId=disk["nexusId"],
            ))
            adoption.append({
                "modName": disk["name"],
                "modId": disk["nexusId"] or 0,
                "enabled": enabled,
                "plugins": disk["plugins"],
                "provenanceStatus": "REVIEW_REQUIRED",
                "note": "Generated by profile_reconcile --adoption-plan; verify source, version, file ID, archive hash, permissions and installation transaction before adoption.",
            })
            continue

        ledger_enabled = row.get("enabled")
        if not isinstance(ledger_enabled, bool):
            errors.append(_problem(
                "ledger-enabled-not-boolean",
                f"ledger enabled state is not boolean: {disk['name']}",
                modName=disk["name"], value=ledger_enabled,
            ))
        elif state is not None and ledger_enabled != state["enabled"]:
            errors.append(_problem(
                "ledger-enabled-mismatch",
                f"ledger/profile enabled mismatch: {disk['name']} ledger={ledger_enabled} profile={state['enabled']}",
                modName=disk["name"], ledgerEnabled=ledger_enabled,
                profileEnabled=state["enabled"],
            ))

        declared = { _key(p): p for p in row.get("plugins", []) }
        actual = { _key(p): p for p in disk["plugins"] }
        missing = sorted((declared[k] for k in declared.keys() - actual.keys()), key=str.casefold)
        unrecorded = sorted((actual[k] for k in actual.keys() - declared.keys()), key=str.casefold)
        if missing or unrecorded:
            errors.append(_problem(
                "ledger-plugin-inventory-mismatch",
                f"ledger/plugin inventory mismatch: {disk['name']}",
                modName=disk["name"], missingFromFolder=missing,
                missingFromLedger=unrecorded,
            ))

        ledger_id = row.get("modId")
        try:
            ledger_id = int(ledger_id or 0)
        except (TypeError, ValueError):
            ledger_id = 0
        if disk["nexusId"] and ledger_id and disk["nexusId"] != ledger_id:
            errors.append(_problem(
                "nexus-id-mismatch",
                f"Nexus ID mismatch: {disk['name']} ledger={ledger_id} meta={disk['nexusId']}",
                modName=disk["name"], ledgerModId=ledger_id,
                metadataModId=disk["nexusId"],
            ))

    for key, state in modlist.items():
        if key not in physical:
            errors.append(_problem(
                "modlist-folder-missing",
                f"modlist row points to no physical folder: {state['name']}",
                modName=state["name"], enabled=state["enabled"],
            ))

    for key, row in ledger.items():
        if key in physical:
            continue
        archived_to = row.get("archivedTo")
        archived_ok = bool(archived_to and pathlib.Path(archived_to).exists() and row.get("enabled") is False)
        if archived_ok:
            warnings.append(_problem(
                "archived-ledger-row",
                f"ledger row is explicitly archived outside the live tree: {row.get('modName')}",
                modName=row.get("modName"), archivedTo=archived_to,
            ))
        else:
            errors.append(_problem(
                "stale-ledger-row",
                f"ledger row points to no physical mod folder: {row.get('modName')}",
                modName=row.get("modName"), archivedTo=archived_to,
            ))

    # Preserve modlist order: this instance writes highest-priority provider
    # first, so only that winner's disabledPlugins intent governs a duplicated
    # plugin basename. A parked lower copy must not override a live overlay.
    enabled_providers: dict[str, list[str]] = defaultdict(list)
    for mod_key, state in modlist.items():
        disk = physical.get(mod_key)
        if not disk or not state.get("enabled"):
            continue
        for plugin in disk["plugins"]:
            enabled_providers[_key(plugin)].append(disk["name"])

    disabled_intent_by_mod: dict[str, set[str]] = defaultdict(set)
    for key, row in ledger.items():
        if key not in physical or not modlist.get(key, {}).get("enabled"):
            continue
        for plugin in row.get("disabledPlugins", []):
            disabled_intent_by_mod[key].add(_key(plugin))

    for plugin_key, providers in sorted(enabled_providers.items()):
        plugin = plugins.get(plugin_key)
        display = physical[_key(providers[0])]["plugins"]
        display_name = next((p for p in display if _key(p) == plugin_key), plugin_key)
        winner_key = _key(providers[0])
        winner_disabled = plugin_key in disabled_intent_by_mod.get(winner_key, set())
        if plugin is None:
            errors.append(_problem(
                "enabled-mod-plugin-undiscovered",
                f"enabled mod plugin is absent from plugins.txt: {display_name}",
                plugin=display_name, providers=providers,
            ))
        elif not plugin["active"] and not winner_disabled:
            errors.append(_problem(
                "unexplained-inactive-plugin",
                f"enabled mod plugin is inactive without disabledPlugins intent: {plugin['name']}",
                plugin=plugin["name"], providers=providers,
            ))
        elif plugin["active"] and winner_disabled:
            errors.append(_problem(
                "active-plugin-marked-disabled",
                f"active plugin is marked disabled in the ledger: {plugin['name']}",
                plugin=plugin["name"], ledgerMods=[providers[0]],
            ))

    data_plugins = set()
    if game_data.exists():
        data_plugins = {
            _key(p.name) for p in game_data.iterdir()
            if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES
        }
    overwrite = instance / "overwrite"
    overwrite_plugins = {
        _key(p.name) for p in overwrite.iterdir()
        if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES
    } if overwrite.exists() else set()
    for plugin_key, state in plugins.items():
        if not state["active"]:
            continue
        if plugin_key not in enabled_providers and plugin_key not in data_plugins and plugin_key not in overwrite_plugins:
            errors.append(_problem(
                "active-plugin-without-provider",
                f"active plugin has no enabled mod/Data/overwrite provider: {state['name']}",
                plugin=state["name"],
            ))

    result = {
        "schemaVersion": 1,
        "instance": str(instance),
        "profile": profile,
        "ledger": str(ledger_path),
        "counts": {
            "physicalMods": len(physical),
            "profileMods": len(modlist),
            "enabledProfileMods": sum(1 for row in modlist.values() if row["enabled"]),
            "ledgerRows": len(ledger_rows),
            "discoveredPlugins": len(plugins),
            "activePlugins": sum(1 for row in plugins.values() if row["active"]),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
        "adoptionPlan": sorted(adoption, key=lambda row: row["modName"].casefold()),
    }
    result["reconciled"] = not errors
    return result


def render(result: dict) -> str:
    c = result["counts"]
    lines = [
        f"physical {c['physicalMods']}, profile {c['profileMods']} "
        f"({c['enabledProfileMods']} enabled), ledger {c['ledgerRows']}, "
        f"plugins {c['discoveredPlugins']} ({c['activePlugins']} active)",
    ]
    for item in result["warnings"]:
        lines.append(f"  WARN  [{item['code']}] {item['message']}")
    for item in result["errors"]:
        lines.append(f"  FAIL  [{item['code']}] {item['message']}")
    lines.append("")
    if result["reconciled"]:
        lines.append("profile authorities reconciled")
    else:
        lines.append(
            f"{c['errors']} reconciliation failure(s); profile mutation and launch are blocked (#102)"
        )
    return "\n".join(lines)


def _fixture_ledger(path: pathlib.Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schemaVersion": 1, "mods": rows}), encoding="utf-8")


def selftest() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="profile-reconcile-") as raw:
        root = pathlib.Path(raw)
        instance = root / "instance"
        profile = instance / "profiles" / "Default"
        mods = instance / "mods"
        data = root / "Data"
        profile.mkdir(parents=True)
        mods.mkdir(parents=True)
        data.mkdir()

        (mods / "Good").mkdir()
        (mods / "Good" / "Good.esp").write_bytes(b"x")
        (mods / "Asset only").mkdir()
        (profile / "modlist.txt").write_text("+Good\n-Asset only\n", encoding="utf-8")
        (profile / "plugins.txt").write_text("*Good.esp\n", encoding="utf-8")
        ledger = root / "ledger.json"
        _fixture_ledger(ledger, [
            {"modId": 1, "modName": "Good", "plugins": ["Good.esp"], "enabled": True},
            {"modId": 2, "modName": "Asset only", "plugins": [], "enabled": False},
        ])
        clean = reconcile(instance, "Default", ledger, data)
        assert clean["reconciled"], clean
        checks += 1

        (mods / "Bypass").mkdir()
        (mods / "Bypass" / "Bypass.esl").write_bytes(b"x")
        with (profile / "modlist.txt").open("a", encoding="utf-8") as stream:
            stream.write("+Bypass\n")
        with (profile / "plugins.txt").open("a", encoding="utf-8") as stream:
            stream.write("Bypass.esl\n")
        broken = reconcile(instance, "Default", ledger, data)
        codes = {row["code"] for row in broken["errors"]}
        assert "unledgered-physical-mod" in codes
        assert "unexplained-inactive-plugin" in codes
        assert broken["adoptionPlan"][0]["modName"] == "Bypass"
        checks += 3

        _fixture_ledger(ledger, [
            {"modId": 1, "modName": "Good", "plugins": [], "enabled": False},
            {"modId": 2, "modName": "Asset only", "plugins": [], "enabled": False},
            {"modId": 3, "modName": "Bypass", "plugins": ["Bypass.esl"],
             "disabledPlugins": ["Bypass.esl"], "enabled": True},
            {"modId": 4, "modName": "Gone", "plugins": [], "enabled": False},
        ])
        broken = reconcile(instance, "Default", ledger, data)
        codes = {row["code"] for row in broken["errors"]}
        assert "ledger-enabled-mismatch" in codes
        assert "ledger-plugin-inventory-mismatch" in codes
        assert "stale-ledger-row" in codes
        checks += 3

    print(f"profile_reconcile selftest PASS ({checks} assertions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--ledger", type=pathlib.Path, default=LEDGER)
    parser.add_argument("--game-data", type=pathlib.Path, default=GAME_DATA)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--adoption-plan", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = reconcile(args.instance, args.profile, args.ledger, args.game_data)
    if args.adoption_plan:
        print(json.dumps({"schemaVersion": 1, "candidates": result["adoptionPlan"]}, indent=2))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0 if result["reconciled"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
