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
import datetime as dt
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
LIFECYCLE_POLICY_EPOCH = dt.datetime(2026, 9, 4, tzinfo=dt.timezone.utc)


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


def _parse_utc(value: object) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def _within(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


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
    if not isinstance(document, dict):
        raise ValueError("ledger root must be a JSON object")
    source = document.get("mods", [])
    if not isinstance(source, list) or not all(isinstance(row, dict) for row in source):
        raise ValueError("ledger mods must be an array of objects")
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
    repo_root: pathlib.Path = REPO,
) -> dict:
    instance = pathlib.Path(instance)
    ledger_path = pathlib.Path(ledger_path)
    repo_root = pathlib.Path(repo_root)
    profile_dir = instance / "profiles" / profile
    errors: list[dict] = []
    warnings: list[dict] = []
    adoption: list[dict] = []

    mods_dir = instance / "mods"
    modlist_path = profile_dir / "modlist.txt"
    plugins_path = profile_dir / "plugins.txt"
    for code, path, label in (
        ("mods-directory-missing", mods_dir, "managed mods directory"),
        ("modlist-missing", modlist_path, "profile modlist.txt"),
        ("plugins-list-missing", plugins_path, "profile plugins.txt"),
        ("ledger-missing", ledger_path, "installed-mod ledger"),
    ):
        if not path.exists():
            errors.append(_problem(code, f"required authority is missing: {label}", path=str(path)))

    physical = physical_mods(mods_dir)
    modlist, modlist_dupes = parse_modlist(modlist_path)
    plugins, plugin_dupes = parse_plugins(plugins_path)
    if ledger_path.exists():
        try:
            ledger_document = _read_json(ledger_path)
            if not isinstance(ledger_document, dict):
                raise ValueError("ledger root must be a JSON object")
            if ledger_document.get("schemaVersion") != 1:
                errors.append(_problem(
                    "ledger-schema-version-invalid",
                    f"installed-mod ledger schemaVersion must be 1, got {ledger_document.get('schemaVersion')!r}",
                    path=str(ledger_path),
                ))
            declared_instance = pathlib.Path(
                str(ledger_document.get("instance") or ""))
            if not str(ledger_document.get("instance") or "").strip() or \
                    os.path.normcase(os.path.abspath(declared_instance)) != \
                    os.path.normcase(os.path.abspath(instance)):
                errors.append(_problem(
                    "ledger-instance-mismatch",
                    "installed-mod ledger instance does not match the audited instance",
                    declared=str(ledger_document.get("instance") or ""), actual=str(instance),
                ))
            if str(ledger_document.get("profile") or "") != str(profile):
                errors.append(_problem(
                    "ledger-profile-mismatch",
                    "installed-mod ledger profile does not match the audited profile",
                    declared=str(ledger_document.get("profile") or ""), actual=str(profile),
                ))
            ledger_rows, ledger, ledger_dupes = _ledger_rows(ledger_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(_problem(
                "ledger-unreadable",
                f"installed-mod ledger is unreadable: {type(exc).__name__}: {exc}",
                path=str(ledger_path),
            ))
            ledger_rows, ledger, ledger_dupes = [], {}, []
    else:
        ledger_rows, ledger, ledger_dupes = [], {}, []

    for row in modlist_dupes:
        errors.append(_problem("duplicate-modlist-row", f"duplicate modlist row: {row['name']}", **row))
    for row in plugin_dupes:
        errors.append(_problem("duplicate-plugin-row", f"duplicate plugins.txt row: {row['name']}", **row))
    for row in ledger_dupes:
        errors.append(_problem("duplicate-ledger-row", f"invalid/duplicate ledger row: {row['name']!r}", **row))

    receipt_root = (repo_root / "records" / "impact-receipts").resolve()
    for row in ledger_rows:
        raw_installed = str(row.get("installedUtc") or "").strip()
        installed = _parse_utc(raw_installed)
        if raw_installed and installed is None:
            errors.append(_problem(
                "installed-utc-invalid",
                f"installedUtc is malformed or lacks a timezone: {row.get('modName')}",
                modName=row.get("modName"), installedUtc=raw_installed,
            ))
        managed = bool(row.get("lifecyclePolicyVersion") or
                       row.get("lifecycleOperation") or row.get("impactReceipt") or
                       row.get("verificationPlan") or row.get("verificationTestId") or
                       row.get("verificationContractSignature"))
        required = managed or bool(installed and installed >= LIFECYCLE_POLICY_EPOCH)
        reference = str(row.get("impactReceipt") or "").strip()
        declared_hash = str(row.get("impactReceiptSha256") or "").strip().upper()
        name = str(row.get("modName") or "(unnamed)")
        if not reference:
            if required:
                errors.append(_problem(
                    "impact-receipt-missing",
                    f"post-policy ledger row has no impact receipt: {name}",
                    modName=name,
                ))
            continue
        if pathlib.Path(reference).is_absolute():
            errors.append(_problem(
                "impact-receipt-not-portable",
                f"impact receipt must be repository-relative: {name}",
                modName=name, impactReceipt=reference,
            ))
            continue
        receipt_path = (repo_root / reference).resolve()
        if not _within(receipt_path, receipt_root):
            errors.append(_problem(
                "impact-receipt-path-invalid",
                f"impact receipt escapes records/impact-receipts: {name}",
                modName=name, impactReceipt=reference,
            ))
            continue
        if not re.fullmatch(r"[0-9A-F]{64}", declared_hash):
            errors.append(_problem(
                "impact-receipt-hash-invalid",
                f"impact receipt hash is missing or invalid: {name}",
                modName=name, impactReceipt=reference,
            ))
            continue
        try:
            actual_hash = _sha256(receipt_path)
        except OSError as exc:
            errors.append(_problem(
                "impact-receipt-unreadable",
                f"impact receipt is missing/unreadable: {name}: {exc}",
                modName=name, impactReceipt=reference,
            ))
            continue
        if actual_hash != declared_hash:
            errors.append(_problem(
                "impact-receipt-hash-mismatch",
                f"impact receipt bytes changed after ledger commit: {name}",
                modName=name, impactReceipt=reference,
                expectedSha256=declared_hash, actualSha256=actual_hash,
            ))

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

        provenance_status = _key(row.get("provenanceStatus")).replace("_", "-").replace(" ", "-")
        if provenance_status == "review-required":
            errors.append(_problem(
                "ledger-provenance-review-required",
                f"ledger provenance is still REVIEW_REQUIRED: {disk['name']}",
                modName=disk["name"],
            ))

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
        if disk["nexusId"]:
            if not ledger_id:
                errors.append(_problem(
                    "ledger-nexus-id-missing",
                    f"physical mod identifies Nexus {disk['nexusId']} but ledger uses local/unknown provenance: {disk['name']}",
                    modName=disk["name"], ledgerModId=ledger_id,
                    metadataModId=disk["nexusId"],
                ))
            elif disk["nexusId"] != ledger_id:
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
    physical_providers: dict[str, list[str]] = defaultdict(list)
    enabled_providers: dict[str, list[str]] = defaultdict(list)
    for mod_key, state in modlist.items():
        disk = physical.get(mod_key)
        if not disk:
            continue
        for plugin in disk["plugins"]:
            physical_providers[_key(plugin)].append(disk["name"])
            if state.get("enabled"):
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

    data_plugin_paths: dict[str, pathlib.Path] = {}
    if game_data.exists():
        data_plugin_paths = {
            _key(p.name): p for p in game_data.iterdir()
            if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES
        }
    overwrite = instance / "overwrite"
    overwrite_plugin_paths = {
        _key(p.name): p for p in overwrite.iterdir()
        if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES
    } if overwrite.exists() else {}

    for plugin_key, overwrite_path in sorted(overwrite_plugin_paths.items()):
        data_path = data_plugin_paths.get(plugin_key)
        if data_path and _sha256(data_path) == _sha256(overwrite_path):
            warnings.append(_problem(
                "identical-data-plugin-in-overwrite",
                f"overwrite redundantly contains a byte-identical Data plugin: {overwrite_path.name}",
                plugin=overwrite_path.name,
                overwritePath=str(overwrite_path),
                dataPath=str(data_path),
            ))
        else:
            errors.append(_problem(
                "untracked-overwrite-plugin",
                f"overwrite contains an unmanaged plugin payload: {overwrite_path.name}",
                plugin=overwrite_path.name,
                overwritePath=str(overwrite_path),
                dataPath=str(data_path) if data_path else None,
            ))

    for plugin_key, state in plugins.items():
        managed_providers = enabled_providers if state["active"] else physical_providers
        has_provider = (
            plugin_key in managed_providers or
            plugin_key in data_plugin_paths or
            plugin_key in overwrite_plugin_paths
        )
        if not has_provider:
            errors.append(_problem(
                "active-plugin-without-provider" if state["active"] else "inactive-plugin-without-provider",
                f"{'active' if state['active'] else 'inactive'} plugin has no enabled mod/Data/overwrite provider: {state['name']}",
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


def _fixture_ledger(path: pathlib.Path, rows: list[dict], profile: str = "Default") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schemaVersion": 1,
        "instance": str(path.parent / "instance"),
        "profile": profile,
        "mods": rows,
    }), encoding="utf-8")


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

        receipt = root / "records" / "impact-receipts" / "good.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(b'{"reviewed":true}\n')
        rows = json.loads(ledger.read_text(encoding="utf-8"))["mods"]
        rows[0].update({
            "installedUtc": "2026-09-04T01:00:00Z",
            "impactReceipt": "records/impact-receipts/good.json",
            "impactReceiptSha256": _sha256(receipt),
        })
        _fixture_ledger(ledger, rows)
        assert reconcile(instance, "Default", ledger, data, root)["reconciled"]
        receipt.write_bytes(b'{"reviewed":false}\n')
        receipt_broken = reconcile(instance, "Default", ledger, data, root)
        assert "impact-receipt-hash-mismatch" in {
            row["code"] for row in receipt_broken["errors"]
        }
        checks += 2
        _fixture_ledger(ledger, [
            {"modId": 1, "modName": "Good", "plugins": ["Good.esp"], "enabled": True},
            {"modId": 2, "modName": "Asset only", "plugins": [], "enabled": False},
        ])

        invalid_header = json.loads(ledger.read_text(encoding="utf-8"))
        invalid_header.update({"schemaVersion": 999, "instance": "wrong", "profile": "wrong"})
        ledger.write_text(json.dumps(invalid_header), encoding="utf-8")
        broken_header = reconcile(instance, "Default", ledger, data)
        header_codes = {row["code"] for row in broken_header["errors"]}
        assert {"ledger-schema-version-invalid", "ledger-instance-mismatch",
                "ledger-profile-mismatch"} <= header_codes
        checks += 3
        _fixture_ledger(ledger, [
            {"modId": 1, "modName": "Good", "plugins": ["Good.esp"], "enabled": True},
            {"modId": 2, "modName": "Asset only", "plugins": [], "enabled": False},
        ])

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

        # Explicitly unresolved provenance is never a clean ledger adoption.
        rows = json.loads(ledger.read_text(encoding="utf-8"))["mods"]
        next(row for row in rows if row["modName"] == "Bypass")["provenanceStatus"] = "REVIEW_REQUIRED"
        _fixture_ledger(ledger, rows)
        broken = reconcile(instance, "Default", ledger, data)
        assert "ledger-provenance-review-required" in {row["code"] for row in broken["errors"]}
        checks += 1

        # plugins.txt is state, not a provider inventory: stale inactive rows
        # and unmanaged overwrite plugins must both fail closed.
        with (profile / "plugins.txt").open("a", encoding="utf-8") as stream:
            stream.write("Ghost.esp\n*Loose.esp\n")
        overwrite = instance / "overwrite"
        overwrite.mkdir()
        (overwrite / "Loose.esp").write_bytes(b"unmanaged")
        broken = reconcile(instance, "Default", ledger, data)
        codes = {row["code"] for row in broken["errors"]}
        assert "inactive-plugin-without-provider" in codes
        assert "untracked-overwrite-plugin" in codes
        checks += 2

        # A byte-identical official/Data duplicate is still visible debt, but
        # not a second payload whose content differs from its authority.
        (data / "Official.esl").write_bytes(b"same")
        (overwrite / "Official.esl").write_bytes(b"same")
        with (profile / "plugins.txt").open("a", encoding="utf-8") as stream:
            stream.write("*Official.esl\n")
        broken = reconcile(instance, "Default", ledger, data)
        warning_codes = {row["code"] for row in broken["warnings"]}
        assert "identical-data-plugin-in-overwrite" in warning_codes
        checks += 1

        # A folder which identifies a Nexus source cannot be laundered into an
        # apparently local artifact merely by omitting provenance in the row.
        (mods / "Asset only" / "meta.ini").write_text("modid=42\n", encoding="utf-8")
        rows = json.loads(ledger.read_text(encoding="utf-8"))["mods"]
        next(row for row in rows if row["modName"] == "Asset only")["modId"] = 0
        _fixture_ledger(ledger, rows)
        broken = reconcile(instance, "Default", ledger, data)
        assert "ledger-nexus-id-missing" in {row["code"] for row in broken["errors"]}
        checks += 1

        # Empty fixture directories cannot turn absent authority files into a
        # vacuous clean result.
        empty = root / "empty"
        (empty / "mods").mkdir(parents=True)
        missing = reconcile(empty, "Default", empty / "ledger.json", root / "missing-data")
        missing_codes = {row["code"] for row in missing["errors"]}
        assert {"modlist-missing", "plugins-list-missing", "ledger-missing"} <= missing_codes
        checks += 3

    print(f"profile_reconcile selftest PASS ({checks} assertions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--ledger", type=pathlib.Path, default=LEDGER)
    parser.add_argument("--game-data", type=pathlib.Path, default=GAME_DATA)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--adoption-plan", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = reconcile(args.instance, args.profile, args.ledger, args.game_data,
                       args.repo_root)
    if args.adoption_plan:
        print(json.dumps({"schemaVersion": 1, "candidates": result["adoptionPlan"]}, indent=2))
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0 if result["reconciled"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
