#!/usr/bin/env python3
"""Offline verifier for the private Lost LongSwords curation payload.

The test deliberately resolves the enabled profile rather than accepting file
names as evidence.  It overlays current LVLI winners, applies the declarative
SkyPatcher operations in memory, and audits acquisition reachability.  It does
not install files or launch Skyrim.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import mmap
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


RECORD_CLI_EXE_SHA256 = "AF77A44CB037348ECBF63C01B206A0B41F514017B59DB6825AFA8B573534FD85"
RECORD_CLI_DLL_SHA256 = "4A21F63F30C7DBE901EFBCCEA2AD721CD094E0B8C82B50EA0F4A2E3EB4B1F3FA"
CACHE_SCHEMA = "bb9aafb-typed-distribution-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_tree(root: Path) -> str:
    if not root.is_dir():
        raise AssertionError(f"Required tree is absent: {root}")
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest().upper()


def canonical(value: str) -> str:
    return value.casefold()


def run_jsonl(tool: Path, command: str, plugin: Path) -> list[dict[str, Any]]:
    creation_flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    process = subprocess.run(
        [str(tool), command, str(plugin)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=300,
        creationflags=creation_flags,
    )
    if process.returncode:
        raise RuntimeError(
            f"{command} failed for {plugin} ({process.returncode}):\n{process.stderr}\n{process.stdout}"
        )
    return [json.loads(line) for line in process.stdout.splitlines() if line.strip()]


def cached_jsonl(
    tool: Path, command: str, plugin: Path, cache_root: Path
) -> list[dict[str, Any]]:
    plugin_hash = sha256(plugin)
    path_key = hashlib.sha256(str(plugin).casefold().encode("utf-8")).hexdigest()[:12]
    cache = cache_root / f"{CACHE_SCHEMA}.{RECORD_CLI_DLL_SHA256}.{plugin_hash}.{path_key}.{command}.json"
    if cache.is_file():
        return json.loads(cache.read_text(encoding="utf-8"))
    rows = run_jsonl(tool, command, plugin)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")
    return rows


def source_weapon_text_without_owned_fields(path: Path) -> str:
    section = ""
    output: list[str] = []
    owned = {("BasicStats", "Damage"), ("Data", "Speed"), ("Data", "Reach"), ("Data", "Stagger")}
    seen: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        section_match = re.match(r"^([A-Za-z][A-Za-z0-9]*):(?:\s.*)?$", line)
        if section_match:
            section = section_match.group(1)
        field_match = re.match(r"^  ([A-Za-z][A-Za-z0-9]*):\s", line)
        key = (section, field_match.group(1)) if field_match else None
        if key in owned:
            seen.add(key)
            output.append(f"  {key[1]}: <OWNED>")
        else:
            output.append(line)
    if seen != owned:
        raise AssertionError(f"{path} did not contain exactly the four owned weapon fields: {sorted(seen)}")
    return "\n".join(output) + "\n"


def find_spriggit_record(root: Path, form_key: str) -> Path:
    form, plugin = form_key.split(":", 1)
    candidates = list(root.rglob(f"*{form}_{plugin}.yaml"))
    candidates.extend(path / "RecordData.yaml" for path in root.rglob(f"*{form}_{plugin}") if path.is_dir())
    matches = [
        path
        for path in candidates
        if path.is_file()
        and path.read_text(encoding="utf-8-sig").splitlines()[0] == f"FormKey: {form_key}"
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one Spriggit source for {form_key} below {root}; found {matches}")
    return matches[0]


def projected_cell_text(path: Path) -> str:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if re.match(r"^(NavigationMeshes|Persistent|Temporary|VisibleWhenDistant|MajorFlags):", line):
            break
        lines.append(line)
    return "\n".join(lines) + "\n"


def form_id(form_key: str) -> int:
    return int(form_key.split(":", 1)[0], 16)


def plugin_header_flags(path: Path) -> int:
    with path.open("rb") as stream:
        header = stream.read(12)
    if len(header) != 12 or header[:4] != b"TES4":
        raise AssertionError(f"Not a Bethesda TES4 plugin: {path}")
    return int.from_bytes(header[8:12], "little")


def is_master_stage_plugin(path: Path) -> bool:
    """Classify native masters plus master-flagged ESPs before regular ESPs."""

    return path.suffix.casefold() in {".esm", ".esl"} or bool(
        plugin_header_flags(path) & 0x1
    )


def leveled_entry_counter(record: dict[str, Any] | None) -> Counter[tuple[int, int, str]]:
    return Counter(
        (
            int(item["level"]),
            int(item["count"]),
            canonical(item["referenceFormKey"]),
        )
        for item in ((record or {}).get("entries") or [])
    )


def leveled_non_entry_semantics(record: dict[str, Any] | None) -> tuple[Any, ...] | None:
    if record is None:
        return None
    return (
        record.get("type"),
        record.get("editorId"),
        float(record.get("chanceNone", 0)),
        canonical(record["chanceNoneGlobalFormKey"])
        if record.get("chanceNoneGlobalFormKey")
        else None,
        record.get("flags"),
    )


def leveled_export_semantics(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {key: value for key, value in record.items() if key != "plugin"}


def resolve_profile(
    profile: Path, mods_root: Path, game_data: Path
) -> tuple[list[tuple[str, Path]], dict[str, str]]:
    plugins_file = profile / "plugins.txt"
    modlist_file = profile / "modlist.txt"
    active_names = [
        line[1:].strip()
        for line in plugins_file.read_text(encoding="utf-8-sig").splitlines()
        if line.startswith("*")
    ]

    # MO2 lists highest-priority mods first.  setdefault therefore captures the
    # actual left-pane file winner without walking ignored/optional subtrees.
    mod_winners: dict[str, Path] = {}
    overwrite = mods_root.parent / "overwrite"
    if overwrite.is_dir():
        for child in overwrite.iterdir():
            if child.is_file() and child.suffix.casefold() in {".esm", ".esp", ".esl"}:
                mod_winners.setdefault(child.name.casefold(), child)
    for line in modlist_file.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("+"):
            continue
        mod_dir = mods_root / line[1:].strip()
        if not mod_dir.is_dir():
            continue
        for child in mod_dir.iterdir():
            if child.is_file() and child.suffix.casefold() in {".esm", ".esp", ".esl"}:
                mod_winners.setdefault(child.name.casefold(), child)

    data_winners = {
        child.name.casefold(): child
        for child in game_data.iterdir()
        if child.is_file() and child.suffix.casefold() in {".esm", ".esp", ".esl"}
    }
    game_root = game_data.parent
    ccc = game_root / "Skyrim.ccc"
    official_names = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
    resource_pack = game_data / "_ResourcePack.esl"
    if resource_pack.is_file():
        official_names.append(resource_pack.name)
    if ccc.is_file():
        official_names.extend(
            line.strip()
            for line in ccc.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    ordered: list[tuple[str, Path]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for name in official_names + active_names:
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        path = mod_winners.get(key) or data_winners.get(key)
        if path is None:
            missing.append(name)
        else:
            ordered.append((name, path.resolve()))
    if missing:
        raise AssertionError(f"Runtime plugins could not be resolved to MO2/Data winners: {missing}")

    fingerprint = {
        "pluginsTxtSha256": sha256(plugins_file),
        "modlistTxtSha256": sha256(modlist_file),
    }
    return ordered, fingerprint


def resolve_mo2_asset(
    profile: Path, mods_root: Path, game_data: Path, relative_path: Path
) -> Path:
    """Resolve one VFS file using the same enabled left-pane precedence as MO2."""

    overwrite_candidate = mods_root.parent / "overwrite" / relative_path
    if overwrite_candidate.is_file():
        return overwrite_candidate.resolve()
    modlist_file = profile / "modlist.txt"
    for line in modlist_file.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("+"):
            continue
        candidate = mods_root / line[1:].strip() / relative_path
        if candidate.is_file():
            return candidate.resolve()
    data_candidate = game_data / relative_path
    if data_candidate.is_file():
        return data_candidate.resolve()
    raise AssertionError(f"MO2 VFS file is unresolved: {relative_path}")


def scan_load_order_leveled_items(
    tool: Path,
    ordered_plugins: list[tuple[str, Path]],
    cache_root: Path,
    workers: int,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    dict[str, list[tuple[int, str]]],
    dict[str, list[tuple[int, str, dict[str, Any]]]],
]:
    before = [(name, path, sha256(path)) for name, path in ordered_plugins]

    def scan(
        item: tuple[int, str, Path, str]
    ) -> tuple[int, str, Path, str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        index, name, path, digest = item
        return (
            index,
            name,
            path,
            digest,
            cached_jsonl(tool, "leveled-items", path, cache_root),
            cached_jsonl(tool, "npc-inventories", path, cache_root),
            cached_jsonl(tool, "outfits", path, cache_root),
        )

    indexed = [(index, name, path, digest) for index, (name, path, digest) in enumerate(before)]
    scanned: list[
        tuple[int, str, Path, str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]
    ] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(scan, indexed):
            scanned.append(result)
    scanned.sort(key=lambda row: row[0])

    after = [sha256(path) for _, path in ordered_plugins]
    changed = [
        str(ordered_plugins[index][1])
        for index, digest in enumerate(after)
        if digest != before[index][2]
    ]
    if changed:
        raise AssertionError(f"Plugin bytes changed during the load-order scan: {changed}")

    winners: dict[str, dict[str, Any]] = {}
    npc_winners: dict[str, dict[str, Any]] = {}
    outfit_winners: dict[str, dict[str, Any]] = {}
    providers: dict[str, list[tuple[int, str]]] = defaultdict(list)
    versions: dict[str, list[tuple[int, str, dict[str, Any]]]] = defaultdict(list)
    manifest: list[dict[str, Any]] = []
    for index, name, path, digest, rows, npcs, outfits in scanned:
        manifest.append(
            {
                "loadIndex": index,
                "plugin": name,
                "path": str(path),
                "sha256": digest,
                "leveledItems": len(rows),
                "npcs": len(npcs),
                "outfits": len(outfits),
            }
        )
        for row in rows:
            key = canonical(row["formKey"])
            winner = dict(row)
            winner["winningProvider"] = name
            winner["winningLoadIndex"] = index
            winners[key] = winner
            providers[key].append((index, name))
            versions[key].append((index, name, row))
        for row in npcs:
            winner = dict(row)
            winner["winningProvider"] = name
            winner["winningLoadIndex"] = index
            npc_winners[canonical(row["formKey"])] = winner
        for row in outfits:
            winner = dict(row)
            winner["winningProvider"] = name
            winner["winningLoadIndex"] = index
            outfit_winners[canonical(row["formKey"])] = winner
    return winners, npc_winners, outfit_winners, manifest, providers, versions


def scan_exact_record_versions(
    tool: Path,
    ordered_plugins: list[tuple[str, Path]],
    cache_root: Path,
    targets: dict[str, str],
    workers: int,
) -> dict[str, list[tuple[int, str, dict[str, Any]]]]:
    """Resolve provider chains for a handful of exact records.

    A cheap record-header prefilter avoids exporting the enormous complete
    Skyrim.esm inventory. Every positive candidate other than Skyrim.esm is
    then verified by Mutagen's typed `records` exporter before it is accepted.
    """

    signatures = {"Cell": b"CELL", "LeveledItem": b"LVLI"}
    target_headers = [
        (signatures[record_type], form_id(form_key), canonical(form_key))
        for form_key, record_type in targets.items()
    ]

    def possible(path: Path) -> bool:
        with path.open("rb") as stream:
            if stream.seek(0, os.SEEK_END) == 0:
                return False
            stream.seek(0)
            with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
                for signature, local_id, _ in target_headers:
                    position = data.find(signature)
                    while position >= 0:
                        # Bethesda record headers store the raw FormID twelve
                        # bytes after the four-byte signature. The low 24 bits
                        # are enough only as a prefilter; Mutagen verifies the
                        # full origin plugin below.
                        if position + 16 <= len(data):
                            raw_id = int.from_bytes(data[position + 12 : position + 16], "little")
                            if raw_id & 0xFFFFFF == local_id:
                                return True
                        position = data.find(signature, position + 1)
        return False

    candidates = [
        (index, name, path)
        for index, (name, path) in enumerate(ordered_plugins)
        if name.casefold() != "skyrim.esm" and possible(path)
    ]

    def inspect(item: tuple[int, str, Path]) -> tuple[int, str, list[dict[str, Any]]]:
        index, name, path = item
        rows = [
            row
            for row in cached_jsonl(tool, "records", path, cache_root)
            if canonical(row["formKey"]) in targets
        ]
        return index, name, rows

    versions: dict[str, list[tuple[int, str, dict[str, Any]]]] = defaultdict(list)
    skyrim_index = next(
        (index for index, (name, _) in enumerate(ordered_plugins) if name.casefold() == "skyrim.esm"),
        None,
    )
    if skyrim_index is None:
        raise AssertionError("Resolved load order has no Skyrim.esm")
    for form_key, record_type in targets.items():
        versions[form_key].append(
            (skyrim_index, "Skyrim.esm", {"formKey": form_key, "type": record_type})
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for index, name, rows in pool.map(inspect, candidates):
            for row in rows:
                key = canonical(row["formKey"])
                expected_type = targets[key]
                if row["type"] != expected_type:
                    raise AssertionError(
                        f"{row['formKey']} is {row['type']} in {name}, expected {expected_type}"
                    )
                versions[key].append((index, name, row))
    for chain in versions.values():
        chain.sort(key=lambda item: item[0])
    return versions


def apply_leveled_policy(
    winners: dict[str, dict[str, Any]], policy: dict[str, Any], built_lists: Iterable[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    graph = {
        key: dict(
            value,
            entries=[dict(entry) for entry in (value.get("entries") or [])],
        )
        for key, value in winners.items()
    }
    for row in built_lists:
        graph[canonical(row["formKey"])] = dict(
            row, entries=[dict(entry) for entry in (row.get("entries") or [])]
        )

    for edge in policy["vendorLeveledEdges"] + policy["excludedInternalEdges"]:
        target = canonical(edge["target"])
        if target not in graph:
            raise AssertionError(f"SkyPatcher removal target is absent from current graph: {edge['target']}")
        remove = canonical(edge["remove"])
        graph[target]["entries"] = [
            entry for entry in graph[target]["entries"] if canonical(entry["referenceFormKey"]) != remove
        ]

    for edge in policy["safeLeveledAdditions"]:
        target = canonical(edge["target"])
        if target not in graph:
            raise AssertionError(f"SkyPatcher addition target is absent from current graph: {edge['target']}")
        candidate = {
            "level": int(edge["level"]),
            "count": int(edge["count"]),
            "referenceFormKey": edge["add"],
        }
        already_present = any(
            canonical(entry["referenceFormKey"]) == canonical(candidate["referenceFormKey"])
            for entry in graph[target]["entries"]
        )
        if not already_present:
            graph[target]["entries"].append(candidate)
    return graph


def reachable_external_ancestors(graph: dict[str, dict[str, Any]], start: str, private_plugins: set[str]) -> set[str]:
    parents: dict[str, set[str]] = defaultdict(set)
    for key, record in graph.items():
        for entry in record["entries"]:
            parents[canonical(entry["referenceFormKey"])].add(key)

    custom_component: set[str] = set()
    stack = [canonical(start)]
    boundaries: set[str] = set()
    while stack:
        child = stack.pop()
        for parent in parents.get(child, set()):
            plugin = parent.split(":", 1)[1]
            if plugin in private_plugins:
                if parent not in custom_component:
                    custom_component.add(parent)
                    stack.append(parent)
            else:
                boundaries.add(parent)

    external: set[str] = set(boundaries)
    stack = list(boundaries)
    while stack:
        child = stack.pop()
        for parent in parents.get(child, set()):
            if parent not in external:
                external.add(parent)
                stack.append(parent)
    return external


def apply_npc_policy(npcs: dict[str, dict[str, Any]], policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {
        key: dict(value, items=[dict(item) for item in (value.get("items") or [])])
        for key, value in npcs.items()
    }
    for operation in policy["npcOperations"]:
        key = canonical(operation["target"])
        if key not in result:
            raise AssertionError(f"SkyPatcher NPC target is absent from current winners: {operation['target']}")
        if "remove" in operation:
            remove = canonical(operation["remove"])
            result[key]["items"] = [
                item for item in result[key]["items"] if canonical(item["itemFormKey"]) != remove
            ]
        else:
            old = canonical(operation["replace"])
            new = canonical(operation["with"])
            allow_inherited_noop = bool(operation.get("allowInheritedNoOp", False))
            if allow_inherited_noop and (
                "Inventory" not in (result[key].get("templateFlags") or "")
                or not result[key].get("templateFormKey")
            ):
                raise AssertionError(
                    "allowInheritedNoOp is valid only for a reviewed Inventory-template "
                    f"child: {operation['target']}"
                )
            replacements = 0
            for item in result[key]["items"]:
                if canonical(item["itemFormKey"]) == old:
                    item["itemFormKey"] = operation["with"]
                    replacements += 1
            if replacements == 0 and allow_inherited_noop:
                effective_key = key
                seen: set[str] = set()
                while True:
                    if effective_key in seen:
                        raise AssertionError(
                            f"Inventory-template cycle while checking {operation['target']}"
                        )
                    seen.add(effective_key)
                    effective = result.get(effective_key)
                    if effective is None:
                        raise AssertionError(
                            "Inventory-template target is absent while checking "
                            f"{operation['target']}: {effective_key}"
                        )
                    if "Inventory" not in (effective.get("templateFlags") or ""):
                        effective_items = effective.get("items") or []
                        break
                    template = effective.get("templateFormKey")
                    if not template:
                        raise AssertionError(
                            f"Inventory-inheriting NPC has no template: {effective_key}"
                        )
                    effective_key = canonical(template)
                effective_old = sum(
                    canonical(item["itemFormKey"]) == old for item in effective_items
                )
                effective_new = sum(
                    canonical(item["itemFormKey"]) == new for item in effective_items
                )
                if effective_old != 0 or effective_new != 1:
                    raise AssertionError(
                        "Reviewed inherited no-op does not resolve to exactly one new item "
                        f"and no old item on {operation['target']}: "
                        f"old={effective_old}, new={effective_new}"
                    )
            elif replacements != 1:
                raise AssertionError(
                    f"Expected one current inventory object {operation['replace']} on {operation['target']}; found {replacements}"
                )
    return result


def acquisition_ancestors(
    leveled: dict[str, dict[str, Any]],
    npcs: dict[str, dict[str, Any]],
    outfits: dict[str, dict[str, Any]],
    start: str,
    private_plugins: set[str],
) -> dict[str, tuple[str, str]]:
    parents: dict[str, set[str]] = defaultdict(set)
    metadata: dict[str, tuple[str, str]] = {}
    for key, record in leveled.items():
        metadata[key] = ("LeveledItem", record.get("editorId") or record["formKey"])
        for entry in record["entries"]:
            parents[canonical(entry["referenceFormKey"])].add(key)
    for key, record in outfits.items():
        metadata[key] = ("Outfit", record.get("editorId") or record["formKey"])
        for item in record.get("items") or []:
            if item:
                parents[canonical(item)].add(key)
    for key, record in npcs.items():
        metadata[key] = ("Npc", record.get("editorId") or record["formKey"])
        inherits_inventory = "Inventory" in (record.get("templateFlags") or "")
        template = record.get("templateFormKey")
        if inherits_inventory and template:
            parents[canonical(template)].add(key)
        else:
            for item in record.get("items") or []:
                parents[canonical(item["itemFormKey"])].add(key)
        outfit = record.get("defaultOutfitFormKey")
        if outfit:
            parents[canonical(outfit)].add(key)

    found: dict[str, tuple[str, str]] = {}
    seen: set[str] = {canonical(start)}
    stack = [canonical(start)]
    while stack:
        child = stack.pop()
        for parent in parents.get(child, set()):
            if parent in seen:
                continue
            seen.add(parent)
            stack.append(parent)
            kind, editor_id = metadata.get(parent, ("Unknown", parent))
            origin_plugin = parent.split(":", 1)[1]
            if kind != "LeveledItem" or origin_plugin not in private_plugins:
                found[parent] = (kind, editor_id)
    return found


def expected_config_lines(policy: dict[str, Any]) -> dict[str, list[str]]:
    def sp(form_key: str) -> str:
        form, plugin = form_key.split(":", 1)
        return f"{plugin}|{form.upper()}"

    leveled = [
        f"filterByLLs={sp(edge['target'])}:removeFromLLs={sp(edge['remove'])}"
        for edge in policy["vendorLeveledEdges"] + policy["excludedInternalEdges"]
    ] + [
        f"filterByLLs={sp(edge['target'])}:addOnceToLLs={sp(edge['add'])}~{edge['level']}~{edge['count']}"
        for edge in policy["safeLeveledAdditions"]
    ]
    npc: list[str] = []
    for op in policy["npcOperations"]:
        if "remove" in op:
            npc.append(f"filterByNpcs={sp(op['target'])}:objectsToRemove={sp(op['remove'])}")
        else:
            npc.append(
                f"filterByNpcs={sp(op['target'])}:objectsToReplace={sp(op['replace'])}~{sp(op['with'])}"
            )
    return {
        "leveledList": leveled,
        "npc": npc,
        "container": [
            f"filterByContainers={sp(op['target'])}:removeFromContainers={sp(op['remove'])}"
            for op in policy["containerOperations"]
        ],
        "constructibleObject": [
            f"filterByCobjs={sp(op['formKey'])}:workbenchKeyword=null"
            for op in policy["disabledConstructibleObjects"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the private Lost LongSwords payload. If the candidate is not "
            "active, the current profile is audited in memory with LostLongSwords "
            "and the candidate inserted at the start of the regular ESP stage. If "
            "it is active, its actual hash and exact placement are required."
        )
    )
    script_dir = Path(__file__).resolve().parent
    repo = script_dir.parent.parent
    parser.add_argument("--policy", type=Path, default=script_dir / "private-curation-policy.json")
    parser.add_argument("--proposal", type=Path, default=script_dir / "curation-proposal.json")
    parser.add_argument("--output", type=Path, default=repo / "work/lost-longswords/private-curation")
    parser.add_argument(
        "--record-tool",
        type=Path,
        default=repo.parent / "skyrim-tools-builds/skyrim-record-cli-bb9aafb/skyrim-record-cli.exe",
    )
    parser.add_argument(
        "--game-data",
        type=Path,
        default=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"),
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=repo.parent / "mo2-instances/skyrim-se/profiles/Default",
    )
    parser.add_argument(
        "--mods-root", type=Path, default=repo.parent / "mo2-instances/skyrim-se/mods"
    )
    parser.add_argument(
        "--ussep-plugin",
        type=Path,
        default=repo.parent
        / "mo2-instances/skyrim-se/mods/USSEP/unofficial skyrim special edition patch.esp",
    )
    parser.add_argument(
        "--skypatcher-dll",
        type=Path,
        default=None,
        help=(
            "optional explicit parser binary; it must still be the resolved current MO2 "
            "winner for SKSE/Plugins/SkyPatcher.dll"
        ),
    )
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    parser.add_argument("--skip-current-load-order", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    checks: dict[str, Any] = {}

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'failed'}")

    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    output = args.output.resolve()
    tool = args.record_tool.resolve()
    source_plugin = (repo / "work/lost-longswords/private-port/mod" / policy["source"]["plugin"]).resolve()
    skyrim_plugin = (args.game_data / "Skyrim.esm").resolve()
    ussep_plugin = args.ussep_plugin.resolve()
    resolved_skypatcher_dll = resolve_mo2_asset(
        args.profile,
        args.mods_root,
        args.game_data,
        Path("SKSE/Plugins/SkyPatcher.dll"),
    )
    skypatcher_dll = (
        args.skypatcher_dll.resolve()
        if args.skypatcher_dll is not None
        else resolved_skypatcher_dll
    )
    if skypatcher_dll != resolved_skypatcher_dll:
        raise AssertionError(
            "Explicit SkyPatcher binary is not the current MO2 VFS winner: "
            f"explicit={skypatcher_dll}; winner={resolved_skypatcher_dll}"
        )
    source_yaml = (repo / policy["source"]["validationTree"]).resolve()
    built_plugin = output / "mod" / policy["output"]["plugin"]
    storm_built_plugin = output / "mod" / policy["stormcloakOutput"]["plugin"]
    roundtrip = output / "roundtrip-a"
    storm_source_tree = output / "stormcloak-patch-source"
    skypatcher_tree = output / "mod/SKSE/Plugins/SkyPatcher"
    cache_root = output / "graph-cache"

    forward_providers = policy["masterForwarding"].get("providers", [])
    provider_policies = {
        row["plugin"].casefold(): row for row in forward_providers
    }
    if len(provider_policies) != len(forward_providers):
        raise AssertionError("Forwarding provider names must be unique")
    forward_provider_paths = {
        "skyrim.esm": skyrim_plugin,
        ussep_plugin.name.casefold(): ussep_plugin,
    }
    if set(provider_policies) != set(forward_provider_paths):
        raise AssertionError(
            "Exact verifier supports only the reviewed Skyrim/USSEP providers: "
            f"policy={sorted(provider_policies)}, paths={sorted(forward_provider_paths)}"
        )
    ussep_provider_policy = provider_policies[ussep_plugin.name.casefold()]

    compatibility_inputs = {
        policy["compatibility"]["sonsOfSkyrimPlugin"].casefold(): (
            repo.parent / policy["compatibility"]["sonsOfSkyrimPathAtReview"]
        ).resolve(),
        policy["compatibility"]["sonsLuxOrbisPatchPlugin"].casefold(): (
            repo.parent / policy["compatibility"]["sonsLuxOrbisPatchPathAtReview"]
        ).resolve(),
    }

    required_files = {
        "record tool": tool,
        "record tool assembly": tool.with_name("skyrim-record-cli.dll"),
        "vendor source": source_plugin,
        "Skyrim master": skyrim_plugin,
        "USSEP provider": ussep_plugin,
        "SkyPatcher parser": skypatcher_dll,
        "early curation plugin": built_plugin,
        "Stormcloak distribution plugin": storm_built_plugin,
        "Sons of Skyrim provider": compatibility_inputs[
            policy["compatibility"]["sonsOfSkyrimPlugin"].casefold()
        ],
        "Sons of Skyrim Lux Orbis provider": compatibility_inputs[
            policy["compatibility"]["sonsLuxOrbisPatchPlugin"].casefold()
        ],
    }
    for label, path in required_files.items():
        check(f"{label} exists", path.is_file(), str(path))
    if errors:
        raise AssertionError("\n".join(errors))

    initial_hashes = {
        "policy": sha256(args.policy),
        "proposal": sha256(args.proposal),
        "vendorSource": sha256(source_plugin),
        "skyrimSource": sha256(skyrim_plugin),
        "ussepSource": sha256(ussep_plugin),
        "sonsOfSkyrimSource": sha256(
            compatibility_inputs[policy["compatibility"]["sonsOfSkyrimPlugin"].casefold()]
        ),
        "sonsLuxOrbisSource": sha256(
            compatibility_inputs[
                policy["compatibility"]["sonsLuxOrbisPatchPlugin"].casefold()
            ]
        ),
        "sourceValidationTree": sha256_tree(source_yaml),
        "roundtripTree": sha256_tree(roundtrip),
        "stormSourceTree": sha256_tree(storm_source_tree),
        "skyPatcherTree": sha256_tree(skypatcher_tree),
        "skyPatcherDll": sha256(skypatcher_dll),
        "recordToolExe": sha256(tool),
        "recordToolDll": sha256(tool.with_name("skyrim-record-cli.dll")),
        "builtPlugin": sha256(built_plugin),
        "stormBuiltPlugin": sha256(storm_built_plugin),
    }

    check(
        "pinned record CLI executable",
        initial_hashes["recordToolExe"] == RECORD_CLI_EXE_SHA256,
        initial_hashes["recordToolExe"],
    )
    check(
        "pinned record CLI assembly",
        initial_hashes["recordToolDll"] == RECORD_CLI_DLL_SHA256,
        initial_hashes["recordToolDll"],
    )
    check(
        "proposal hash",
        initial_hashes["proposal"] == policy["proposalSha256"],
        initial_hashes["proposal"],
    )
    check(
        "immutable vendor hash",
        initial_hashes["vendorSource"] == policy["source"]["pluginSha256"],
        initial_hashes["vendorSource"],
    )
    for provider_name, provider_policy in provider_policies.items():
        provider_path = forward_provider_paths[provider_name]
        check(
            f"pinned forward provider {provider_policy['plugin']}",
            sha256(provider_path) == provider_policy["pluginSha256AtReview"],
            f"{provider_path} = {sha256(provider_path)}",
        )
    check(
        "pinned Sons of Skyrim source hash",
        initial_hashes["sonsOfSkyrimSource"]
        == policy["compatibility"]["sonsOfSkyrimSha256AtReview"],
        initial_hashes["sonsOfSkyrimSource"],
    )
    check(
        "pinned Sons of Skyrim Lux Orbis source hash",
        initial_hashes["sonsLuxOrbisSource"]
        == policy["compatibility"]["sonsLuxOrbisPatchSha256AtReview"],
        initial_hashes["sonsLuxOrbisSource"],
    )
    if errors:
        raise AssertionError("\n".join(errors))

    source_lists = run_jsonl(tool, "leveled-items", source_plugin)
    source_links = run_jsonl(tool, "record-links", source_plugin)
    source_records = run_jsonl(tool, "records", source_plugin)
    built_info = run_jsonl(tool, "plugin-info", built_plugin)[0]
    built_records = run_jsonl(tool, "records", built_plugin)
    built_weapons = run_jsonl(tool, "weapons", built_plugin)
    built_lists = run_jsonl(tool, "leveled-items", built_plugin)
    built_links = run_jsonl(tool, "record-links", built_plugin)
    storm_built_info = run_jsonl(tool, "plugin-info", storm_built_plugin)[0]
    storm_built_records = run_jsonl(tool, "records", storm_built_plugin)
    storm_built_lists = run_jsonl(tool, "leveled-items", storm_built_plugin)
    storm_built_links = run_jsonl(tool, "record-links", storm_built_plugin)

    expected_type_counts = {
        f"{record_type}BinaryOverlay": int(count)
        for record_type, count in policy["output"]["expectedRecordTypes"].items()
    }
    check(
        "output record count",
        built_info["records"] == sum(expected_type_counts.values()),
        str(built_info),
    )
    check("output masters", built_info["masters"] == policy["output"]["masters"], str(built_info["masters"]))
    check(
        "output type counts",
        built_info["recordTypes"] == expected_type_counts,
        str(built_info["recordTypes"]),
    )
    expected_storm_type_counts = {
        f"{record_type}BinaryOverlay": int(count)
        for record_type, count in policy["stormcloakOutput"]["expectedRecordTypes"].items()
    }
    check(
        "Stormcloak output record count",
        storm_built_info["records"] == sum(expected_storm_type_counts.values()),
        str(storm_built_info),
    )
    check(
        "Stormcloak output masters",
        storm_built_info["masters"] == policy["stormcloakOutput"]["masters"],
        str(storm_built_info["masters"]),
    )
    check(
        "Stormcloak output type counts",
        storm_built_info["recordTypes"] == expected_storm_type_counts,
        str(storm_built_info["recordTypes"]),
    )
    expected_record_types = {
        **{canonical(row["formKey"]): "Weapon" for row in policy["weapons"]},
        **{canonical(row["formKey"]): "LeveledItem" for row in policy["ownedLeveledItems"]},
        **{
            canonical(row["formKey"]): row["type"]
            for row in policy["masterForwarding"]["records"]
        },
    }
    observed_record_types = {
        canonical(row["formKey"]): row["type"] for row in built_records
    }
    check(
        "exact output FormKeys and types",
        observed_record_types == expected_record_types,
        str(
            {
                "missingOrDifferent": {
                    key: value
                    for key, value in expected_record_types.items()
                    if observed_record_types.get(key) != value
                },
                "extra": sorted(set(observed_record_types) - set(expected_record_types)),
            }
        ),
    )
    expected_storm_record_types = {
        canonical(row["formKey"]): "LeveledItem"
        for row in policy["stormcloakOwnedLeveledItems"]
    }
    observed_storm_record_types = {
        canonical(row["formKey"]): row["type"] for row in storm_built_records
    }
    check(
        "exact Stormcloak output FormKeys and types",
        observed_storm_record_types == expected_storm_record_types,
        str(
            {
                "missingOrDifferent": {
                    key: value
                    for key, value in expected_storm_record_types.items()
                    if observed_storm_record_types.get(key) != value
                },
                "extra": sorted(
                    set(observed_storm_record_types) - set(expected_storm_record_types)
                ),
            }
        ),
    )
    check(
        "ESL FormID range",
        all(
            0x800 <= form_id(row["formKey"]) <= 0xFFF
            for row in built_records
            if row["formKey"].split(":", 1)[1].casefold()
            == policy["output"]["plugin"].casefold()
        )
        and all(
            row["formKey"].split(":", 1)[1].casefold()
            != policy["output"]["plugin"].casefold()
            or row["type"] == "LeveledItem"
            for row in built_records
        ),
        "owned new records must be the approved LVLI forms within 0x800..0xFFF",
    )
    check(
        "Stormcloak ESL FormID range",
        all(
            row["formKey"].split(":", 1)[1].casefold()
            == policy["stormcloakOutput"]["plugin"].casefold()
            and 0x800 <= form_id(row["formKey"]) <= 0xFFF
            and row["type"] == "LeveledItem"
            for row in storm_built_records
        ),
        "all Stormcloak output records must be approved owned LVLI forms in 0x800..0xFFF",
    )
    header = (roundtrip / "RecordData.yaml").read_text(encoding="utf-8-sig")
    check("Small flag", bool(re.search(r"(?m)^  Flags:\r?\n  - Small$", header)), header)
    check("SE header 1.7", bool(re.search(r"(?m)^    Version: 1\.7$", header)), header)
    check(
        "both output binaries carry the Small/ESL flag",
        bool(plugin_header_flags(built_plugin) & 0x200)
        and bool(plugin_header_flags(storm_built_plugin) & 0x200),
        f"early=0x{plugin_header_flags(built_plugin):X}, storm=0x{plugin_header_flags(storm_built_plugin):X}",
    )

    policy_weapons = {canonical(row["formKey"]): row for row in policy["weapons"]}
    observed_weapons = {canonical(row["formKey"]): row for row in built_weapons}
    check("exact nine WEAP FormKeys", set(observed_weapons) == set(policy_weapons), str(sorted(observed_weapons)))
    for key, rule in policy_weapons.items():
        row = observed_weapons[key]
        check(f"{rule['editorId']} EditorID", row["editorId"] == rule["editorId"], row["editorId"])
        for field in ("damage", "speed", "reach", "stagger"):
            check(f"{rule['editorId']} {field}", float(row[field]) == float(rule[field]), str(row[field]))
        check(f"{rule['editorId']} two-handed animation", row["animationType"] == "TwoHandSword", row["animationType"])
        check(f"{rule['editorId']} two-handed skill", row["skill"] == "TwoHanded", row["skill"])

        source_file = next(
            path
            for path in (source_yaml / "Weapons").glob("*.yaml")
            if path.read_text(encoding="utf-8-sig").splitlines()[0] == f"FormKey: {rule['formKey']}"
        )
        generated_file = next(
            path
            for path in (roundtrip / "Weapons").glob("*.yaml")
            if path.read_text(encoding="utf-8-sig").splitlines()[0] == f"FormKey: {rule['formKey']}"
        )
        check(
            f"{rule['editorId']} non-owned field preservation",
            source_weapon_text_without_owned_fields(source_file)
            == source_weapon_text_without_owned_fields(generated_file),
            "a field outside Damage/Speed/Reach/Stagger changed",
        )

    # Compatibility records must be an exact typed semantic copy of their
    # hash-pinned provider. The exporter intentionally ignores binary
    # bookkeeping and the owning plugin name, but retains the complete LVLI
    # payload (flags, chance, global, and ordered entries).
    forward_source_lists_by_provider: dict[str, dict[str, dict[str, Any]]] = {}
    built_lists_by_key = {canonical(row["formKey"]): row for row in built_lists}
    for record in policy["masterForwarding"]["records"]:
        provider_name = record["provider"]
        provider_policy = provider_policies.get(provider_name.casefold())
        if provider_policy is None:
            raise AssertionError(
                f"Forward {record['formKey']} names undeclared provider {provider_name}"
            )
        provider_key = provider_name.casefold()
        if provider_key not in forward_source_lists_by_provider:
            forward_source_lists_by_provider[provider_key] = {
                canonical(row["formKey"]): row
                for row in cached_jsonl(
                    tool,
                    "leveled-items",
                    forward_provider_paths[provider_key],
                    cache_root,
                )
            }
        source_record = forward_source_lists_by_provider[provider_key].get(
            canonical(record["formKey"])
        )
        built_record = built_lists_by_key.get(canonical(record["formKey"]))

        check(
            f"exact pinned {provider_name} forward {record['formKey']}",
            record["type"] == "LeveledItem"
            and leveled_export_semantics(source_record)
            == leveled_export_semantics(built_record),
            "typed output differs from the hash-pinned provider",
        )

    # The Stormcloak plugin owns three new records copied from two exact,
    # hash-pinned current providers. Every typed LVLI property is preserved
    # except ownership/identity and the single declared entry transform.
    storm_source_lists_by_provider: dict[str, dict[str, dict[str, Any]]] = {}
    storm_built_lists_by_key = {
        canonical(row["formKey"]): row for row in storm_built_lists
    }
    for rule in policy["stormcloakOwnedLeveledItems"]:
        provider_key = rule["sourceProvider"].casefold()
        provider_path = compatibility_inputs.get(provider_key)
        if provider_path is None:
            raise AssertionError(
                f"Stormcloak clone names unpinned provider {rule['sourceProvider']}"
            )
        if provider_key not in storm_source_lists_by_provider:
            storm_source_lists_by_provider[provider_key] = {
                canonical(row["formKey"]): row
                for row in cached_jsonl(tool, "leveled-items", provider_path, cache_root)
            }
        source_record = storm_source_lists_by_provider[provider_key].get(
            canonical(rule["sourceFormKey"])
        )
        built_record = storm_built_lists_by_key.get(canonical(rule["formKey"]))
        expected_record = (
            dict(source_record, entries=[dict(row) for row in (source_record.get("entries") or [])])
            if source_record is not None
            else None
        )
        transform_ok = expected_record is not None
        if expected_record is not None:
            transform = rule["transform"]
            if transform["kind"] == "append":
                expected_record["entries"].append(dict(transform["entry"]))
            elif transform["kind"] == "replaceExactlyOnce":
                old = canonical(transform["from"])
                replacements = 0
                for entry in expected_record["entries"]:
                    if canonical(entry["referenceFormKey"]) == old:
                        entry["referenceFormKey"] = transform["to"]
                        replacements += 1
                transform_ok = replacements == 1
            else:
                raise AssertionError(
                    f"Unsupported Stormcloak transform {transform['kind']}"
                )
            expected_record["plugin"] = policy["stormcloakOutput"]["plugin"]
            expected_record["formKey"] = rule["formKey"]
            expected_record["editorId"] = rule["editorId"]
        check(
            f"exact pinned Stormcloak clone {rule['editorId']}",
            transform_ok
            and leveled_export_semantics(expected_record)
            == leveled_export_semantics(built_record),
            str(
                {
                    "provider": rule["sourceProvider"],
                    "source": rule["sourceFormKey"],
                    "expected": expected_record,
                    "actual": built_record,
                }
            ),
        )

    owned_lists = {
        canonical(row["formKey"]): row
        for row in built_lists
        if row["formKey"].split(":", 1)[1].casefold()
        == policy["output"]["plugin"].casefold()
    }
    for rule in policy["ownedLeveledItems"]:
        key = canonical(rule["formKey"])
        row = owned_lists.get(key)
        expected_entries = Counter(
            (
                int(entry["level"]),
                int(entry["count"]),
                canonical(entry["referenceFormKey"]),
            )
            for entry in rule["entries"]
        )
        observed_entries = Counter(
            (
                int(entry["level"]),
                int(entry["count"]),
                canonical(entry["referenceFormKey"]),
            )
            for entry in ((row or {}).get("entries") or [])
        )
        observed_flags = {
            value.strip()
            for value in str((row or {}).get("flags") or "").split(",")
            if value.strip()
        }
        check(
            f"exact owned LVLI {rule['editorId']}",
            row is not None
            and row.get("editorId") == rule["editorId"]
            and observed_flags == set(rule["flags"])
            and float(row.get("chanceNone", -1)) == 0
            and row.get("chanceNoneGlobalFormKey") is None
            and observed_entries == expected_entries,
            str(
                {
                    "observedFlags": sorted(observed_flags),
                    "expectedFlags": sorted(rule["flags"]),
                    "observedEntries": observed_entries,
                    "expectedEntries": expected_entries,
                }
            ),
        )

    actual_external = {
        (canonical(row["formKey"]), canonical(entry["referenceFormKey"]), int(entry["level"]), int(entry["count"]))
        for row in source_lists
        if row["formKey"].endswith(":Skyrim.esm")
        for entry in (row.get("entries") or [])
        if entry["referenceFormKey"].endswith(":LostLongSwords.esp")
    }
    expected_external = {
        (canonical(edge["target"]), canonical(edge["remove"]), int(edge["level"]), 1)
        for edge in policy["vendorLeveledEdges"]
    }
    check("exact 44 vendor leveled-list edges", actual_external == expected_external, f"actual={len(actual_external)}, expected={len(expected_external)}, delta={actual_external ^ expected_external}")

    excluded = {
        canonical(row["formKey"])
        for row in policy["excludedWeapons"]
        if not row.get("alreadyAbsent", False)
    }
    actual_internal = {
        (canonical(row["formKey"]), canonical(entry["referenceFormKey"]))
        for row in source_lists
        if row["formKey"].endswith(":LostLongSwords.esp")
        for entry in (row.get("entries") or [])
        if canonical(entry["referenceFormKey"]) in excluded
    }
    expected_internal = {
        (canonical(edge["target"]), canonical(edge["remove"]))
        for edge in policy["excludedInternalEdges"]
    }
    check("exact 25 excluded internal edge pairs", actual_internal == expected_internal, f"delta={actual_internal ^ expected_internal}")

    # Every excluded weapon's source recipe is explicitly disabled.  This is
    # derived from typed record links, not filename or EditorID heuristics.
    excluded_recipe_forms = {
        canonical(row["formKey"])
        for row in source_links
        if row["type"] == "ConstructibleObject"
        and any(canonical(link["formKey"]) in excluded for link in row["links"])
    }
    disabled_recipes = {canonical(row["formKey"]) for row in policy["disabledConstructibleObjects"]}
    check(
        "excluded crafting and tempering coverage",
        excluded_recipe_forms <= disabled_recipes,
        str(sorted(excluded_recipe_forms - disabled_recipes)),
    )

    source_npc_weapon_links = {
        (canonical(row["formKey"]), canonical(link["formKey"]))
        for row in source_links
        if row["type"] == "Npc"
        for link in row["links"]
        if canonical(link["formKey"]) in policy_weapons
    }
    expected_npc_removals = {
        (canonical(op["target"]), canonical(op["remove"]))
        for op in policy["npcOperations"]
        if "remove" in op
    }
    check("exact source named-NPC cleanup", source_npc_weapon_links == expected_npc_removals, str(source_npc_weapon_links ^ expected_npc_removals))

    placed_weapon_links = {
        (canonical(row["formKey"]), canonical(link["formKey"]))
        for row in source_links
        if row["type"] == "PlacedObject"
        for link in row["links"]
        if canonical(link["formKey"]) in policy_weapons or canonical(link["formKey"]) in excluded
    }
    retained_placements = {
        (canonical(row["formKey"]), canonical(row["base"]))
        for row in policy["retainedPlacedReferences"]
    }
    check("exact four valid source placements retained", placed_weapon_links == retained_placements, str(placed_weapon_links ^ retained_placements))
    check("no reference mutation config", not (output / "mod/SKSE/Plugins/SkyPatcher/reference").exists(), "reference patch directory exists")

    # The generated text configs are an exact projection of policy: comments
    # are ignored, but no extra mutation directive is permitted. Selector and
    # action spelling is also checked against strings embedded by the exact
    # installed parser binary; an unknown selector can otherwise become a
    # dangerous unfiltered catch-all rule.
    parser_bytes = skypatcher_dll.read_bytes()
    parser_contract = {
        "leveledList": ("filterByLLs", {"removeFromLLs", "addOnceToLLs"}),
        "npc": ("filterByNpcs", {"objectsToRemove", "objectsToReplace"}),
        "container": ("filterByContainers", {"removeFromContainers"}),
        "constructibleObject": ("filterByCobjs", {"workbenchKeyword"}),
    }
    required_parser_tokens = {
        token
        for selector, actions in parser_contract.values()
        for token in {selector, *actions}
    }
    check(
        "installed SkyPatcher parser contains every emitted token",
        all(token.encode("ascii") in parser_bytes for token in required_parser_tokens)
        and b"filterByConstructibleObjects" not in parser_bytes,
        str(
            {
                token: token.encode("ascii") in parser_bytes
                for token in sorted(
                    required_parser_tokens | {"filterByConstructibleObjects"}
                )
            }
        ),
    )
    expected_configs = expected_config_lines(policy)
    covered_config_files: set[Path] = set()
    for patcher, expected in expected_configs.items():
        files = sorted(
            (output / "mod/SKSE/Plugins/SkyPatcher" / patcher).rglob("*.ini")
        )
        covered_config_files.update(path.resolve() for path in files)
        observed = [
            line.strip()
            for file in files
            for line in file.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith(";")
        ]
        check(f"exact {patcher} config", observed == expected, f"observed={observed}, expected={expected}")
        selector, allowed_actions = parser_contract[patcher]
        invalid_lines: list[dict[str, Any]] = []
        for line in observed:
            clauses = line.split(":")
            parsed = [clause.split("=", 1) for clause in clauses]
            if (
                len(parsed) != 2
                or any(len(parts) != 2 or not parts[1].strip() for parts in parsed)
                or parsed[0][0] != selector
                or parsed[1][0] not in allowed_actions
            ):
                invalid_lines.append(
                    {
                        "line": line,
                        "requiredSelector": selector,
                        "allowedActions": sorted(allowed_actions),
                    }
                )
        check(
            f"{patcher} rules have recognized nonempty selectors",
            not invalid_lines,
            str(invalid_lines),
        )
    all_config_files = {
        path.resolve() for path in skypatcher_tree.rglob("*.ini") if path.is_file()
    }
    check(
        "no unreviewed SkyPatcher config files",
        all_config_files == covered_config_files,
        str(
            {
                "unreviewed": sorted(str(path) for path in all_config_files - covered_config_files),
                "outsideTree": sorted(
                    str(path) for path in covered_config_files - all_config_files
                ),
            }
        ),
    )

    # Full output link closure against every declared master. Complete record
    # identity sets prove each target exists without a reflection/truncation
    # shortcut.
    skyrim_records = cached_jsonl(tool, "records", skyrim_plugin, cache_root)
    ussep_records = cached_jsonl(tool, "records", ussep_plugin, cache_root)
    sos_records = cached_jsonl(
        tool,
        "records",
        compatibility_inputs[policy["compatibility"]["sonsOfSkyrimPlugin"].casefold()],
        cache_root,
    )
    identity_rows_by_plugin = {
        "skyrim.esm": skyrim_records,
        ussep_plugin.name.casefold(): ussep_records,
        source_plugin.name.casefold(): source_records,
        built_plugin.name.casefold(): built_records,
        policy["compatibility"]["sonsOfSkyrimPlugin"].casefold(): sos_records,
        storm_built_plugin.name.casefold(): storm_built_records,
    }

    def check_output_closure(
        label: str,
        output_policy: dict[str, Any],
        output_records: list[dict[str, Any]],
        output_links: list[dict[str, Any]],
    ) -> None:
        allowed_plugins = {
            canonical(name) for name in output_policy["masters"] + [output_policy["plugin"]]
        }
        identity_plugins = {
            name: rows
            for name, rows in identity_rows_by_plugin.items()
            if name in allowed_plugins
        }
        check(
            f"{label} closure inputs exactly match declared masters plus output",
            set(identity_plugins) == allowed_plugins,
            str(
                {
                    "actual": sorted(identity_plugins),
                    "expected": sorted(allowed_plugins),
                }
            ),
        )
        identities = {
            canonical(row["formKey"])
            for rows in identity_plugins.values()
            for row in rows
        }
        unresolved = sorted(
            {
                link["formKey"]
                for row in output_links
                for link in row["links"]
                if canonical(link["formKey"]) not in identities
                or canonical(link["formKey"].split(":", 1)[1]) not in allowed_plugins
            }
        )
        check(
            f"{label} complete FormKey closure",
            len(output_links) == len(output_records) and not unresolved,
            str(
                {
                    "recordLinks": len(output_links),
                    "records": len(output_records),
                    "unresolvedOrUndeclared": unresolved,
                }
            ),
        )

    check_output_closure(
        "early curation", policy["output"], built_records, built_links
    )
    check_output_closure(
        "Stormcloak distribution",
        policy["stormcloakOutput"],
        storm_built_records,
        storm_built_links,
    )

    load_order_report: dict[str, Any] = {"skipped": args.skip_current_load_order}
    if not args.skip_current_load_order:
        actual_ordered, profile_fingerprint = resolve_profile(
            args.profile, args.mods_root, args.game_data
        )
        initial_input_snapshot = [
            (name.casefold(), str(path).casefold(), sha256(path))
            for name, path in actual_ordered
        ]

        vendor_name = policy["source"]["plugin"]
        curation_name = policy["output"]["plugin"]
        storm_curation_name = policy["stormcloakOutput"]["plugin"]
        sos_name = policy["compatibility"]["sonsOfSkyrimPlugin"]
        actual_vendor_rows = [
            (name, path)
            for name, path in actual_ordered
            if name.casefold() == vendor_name.casefold()
        ]
        actual_curation_rows = [
            (name, path)
            for name, path in actual_ordered
            if name.casefold() == curation_name.casefold()
        ]
        actual_storm_curation_rows = [
            (name, path)
            for name, path in actual_ordered
            if name.casefold() == storm_curation_name.casefold()
        ]
        check(
            "vendor enabled exactly once in actual profile",
            len(actual_vendor_rows) == 1,
            str(actual_vendor_rows),
        )
        check(
            "curation enabled at most once in actual profile",
            len(actual_curation_rows) <= 1,
            str(actual_curation_rows),
        )
        check(
            "Stormcloak curation enabled at most once in actual profile",
            len(actual_storm_curation_rows) <= 1,
            str(actual_storm_curation_rows),
        )
        check(
            "private candidates are either both absent or both enabled",
            bool(actual_curation_rows) == bool(actual_storm_curation_rows),
            str(
                {
                    "early": actual_curation_rows,
                    "stormcloak": actual_storm_curation_rows,
                }
            ),
        )
        if (
            len(actual_vendor_rows) != 1
            or len(actual_curation_rows) > 1
            or len(actual_storm_curation_rows) > 1
            or bool(actual_curation_rows) != bool(actual_storm_curation_rows)
        ):
            raise AssertionError("Cannot construct an unambiguous planned load order")

        actual_vendor_index = next(
            index
            for index, (name, _) in enumerate(actual_ordered)
            if name.casefold() == vendor_name.casefold()
        )
        actual_curation_index = next(
            (
                index
                for index, (name, _) in enumerate(actual_ordered)
                if name.casefold() == curation_name.casefold()
            ),
            None,
        )
        actual_storm_curation_index = next(
            (
                index
                for index, (name, _) in enumerate(actual_ordered)
                if name.casefold() == storm_curation_name.casefold()
            ),
            None,
        )
        vendor_path = actual_vendor_rows[0][1]
        without_private = [
            (name, path)
            for name, path in actual_ordered
            if name.casefold()
            not in {
                vendor_name.casefold(),
                curation_name.casefold(),
                storm_curation_name.casefold(),
            }
        ]
        first_regular_index = next(
            (
                index
                for index, (_, path) in enumerate(without_private)
                if not is_master_stage_plugin(path)
            ),
            len(without_private),
        )
        planned_early = [
            *without_private[:first_regular_index],
            (vendor_name, vendor_path),
            (curation_name, built_plugin.resolve()),
            *without_private[first_regular_index:],
        ]
        planned_sos_indices = [
            index
            for index, (name, _) in enumerate(planned_early)
            if name.casefold() == sos_name.casefold()
        ]
        check(
            "Sons of Skyrim exists exactly once in planned inputs",
            len(planned_sos_indices) == 1,
            str(planned_sos_indices),
        )
        if len(planned_sos_indices) != 1:
            raise AssertionError("Cannot place the Stormcloak candidate unambiguously")
        planned_storm_index = planned_sos_indices[0] + 1
        planned_ordered = [
            *planned_early[:planned_storm_index],
            (storm_curation_name, storm_built_plugin.resolve()),
            *planned_early[planned_storm_index:],
        ]
        installed_mode = len(actual_curation_rows) == 1
        audit_ordered = actual_ordered if installed_mode else planned_ordered

        if installed_mode:
            actual_names = [name.casefold() for name, _ in actual_ordered]
            planned_names = [name.casefold() for name, _ in planned_ordered]
            check(
                "installed private plugins occupy the required early slots",
                actual_names == planned_names,
                str(
                    {
                        "actualVendorIndex": actual_names.index(vendor_name.casefold()),
                        "actualCurationIndex": actual_names.index(curation_name.casefold()),
                        "actualStormcloakCurationIndex": actual_names.index(
                            storm_curation_name.casefold()
                        ),
                        "plannedVendorIndex": planned_names.index(vendor_name.casefold()),
                        "plannedCurationIndex": planned_names.index(curation_name.casefold()),
                        "plannedStormcloakCurationIndex": planned_names.index(
                            storm_curation_name.casefold()
                        ),
                    }
                ),
            )

        (
            winners,
            npc_winners,
            outfit_winners,
            manifest,
            providers,
            versions,
        ) = scan_load_order_leveled_items(
            tool, audit_ordered, cache_root, max(1, args.workers)
        )

        manifest_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in manifest:
            manifest_by_name[row["plugin"].casefold()].append(row)

        def check_pinned_runtime_plugin(label: str, name: str, expected_hash: str) -> int:
            rows = manifest_by_name.get(name.casefold(), [])
            check(f"{label} enabled exactly once", len(rows) == 1, str(rows))
            if len(rows) != 1:
                return -1
            check(
                f"{label} current winner hash",
                rows[0]["sha256"] == expected_hash,
                f"{rows[0]['path']} = {rows[0]['sha256']}",
            )
            return int(rows[0]["loadIndex"])

        vendor_index = check_pinned_runtime_plugin(
            "vendor", vendor_name, policy["source"]["pluginSha256"]
        )
        ussep_name = ussep_provider_policy["plugin"]
        ussep_index = check_pinned_runtime_plugin(
            "USSEP", ussep_name, ussep_provider_policy["pluginSha256AtReview"]
        )
        sos_index = check_pinned_runtime_plugin(
            "Sons of Skyrim", sos_name, policy["compatibility"]["sonsOfSkyrimSha256AtReview"]
        )
        lux_name = policy["compatibility"]["sonsLuxOrbisPatchPlugin"]
        lux_index = check_pinned_runtime_plugin(
            "Sons of Skyrim Lux Orbis patch",
            lux_name,
            policy["compatibility"]["sonsLuxOrbisPatchSha256AtReview"],
        )
        check(
            "required masters precede vendor",
            ussep_index >= 0 and vendor_index >= 0 and ussep_index < vendor_index,
            f"USSEP={ussep_index}, vendor={vendor_index}",
        )

        curation_rows = manifest_by_name.get(curation_name.casefold(), [])
        check("curation present exactly once in audited order", len(curation_rows) == 1, str(curation_rows))
        curation_index = int(curation_rows[0]["loadIndex"]) if len(curation_rows) == 1 else None
        if curation_rows:
            check(
                "audited curation matches tested build",
                curation_rows[0]["sha256"] == sha256(built_plugin),
                f"audited={curation_rows[0]['sha256']}, tested={sha256(built_plugin)}",
            )
            check(
                "curation loads immediately after vendor",
                vendor_index >= 0
                and curation_index is not None
                and curation_index == vendor_index + 1,
                f"vendor={vendor_index}, curation={curation_index}",
            )
            check(
                "vendor begins the audited regular-plugin stage",
                vendor_index >= 0
                and all(
                    is_master_stage_plugin(path)
                    for _, path in audit_ordered[:vendor_index]
                )
                and not is_master_stage_plugin(audit_ordered[vendor_index][1])
                and curation_index is not None
                and not is_master_stage_plugin(audit_ordered[curation_index][1]),
                f"vendor={vendor_index}, curation={curation_index}",
            )

        storm_curation_rows = manifest_by_name.get(storm_curation_name.casefold(), [])
        check(
            "Stormcloak curation present exactly once in audited order",
            len(storm_curation_rows) == 1,
            str(storm_curation_rows),
        )
        storm_curation_index = (
            int(storm_curation_rows[0]["loadIndex"])
            if len(storm_curation_rows) == 1
            else None
        )
        if storm_curation_rows:
            check(
                "audited Stormcloak curation matches tested build",
                storm_curation_rows[0]["sha256"] == initial_hashes["stormBuiltPlugin"],
                f"audited={storm_curation_rows[0]['sha256']}, tested={initial_hashes['stormBuiltPlugin']}",
            )
            check(
                "Stormcloak curation loads immediately after Sons of Skyrim",
                sos_index >= 0
                and storm_curation_index is not None
                and storm_curation_index == sos_index + 1,
                f"SoS={sos_index}, Stormcloak curation={storm_curation_index}",
            )
            check(
                "Lux Orbis SoS patch remains later than owned Stormcloak branch",
                lux_index > (storm_curation_index if storm_curation_index is not None else 10**9),
                f"Stormcloak curation={storm_curation_index}, Lux patch={lux_index}",
            )

        # Both tested candidates are present in the audited order (physically
        # when installed, or as an in-memory plan). Winner resolution therefore
        # models later regular plugins before runtime SkyPatcher operations.
        expected_owned_winners = {
            **{
                canonical(row["formKey"]): curation_name.casefold()
                for row in policy["ownedLeveledItems"]
            },
            **{
                canonical(row["formKey"]): storm_curation_name.casefold()
                for row in policy["stormcloakOwnedLeveledItems"]
            },
        }
        bad_owned_winners = {
            key: (winners.get(key) or {}).get("winningProvider")
            for key, provider in expected_owned_winners.items()
            if (winners.get(key) or {}).get("winningProvider", "").casefold()
            != provider
        }
        check(
            "all owned LVLI forms resolve to their tested private plugin",
            not bad_owned_winners,
            str(bad_owned_winners),
        )
        graph = apply_leveled_policy(winners, policy, [])
        patched_npcs = apply_npc_policy(npc_winners, policy)

        for excluded_key in excluded:
            remaining = [
                row["formKey"]
                for row in graph.values()
                if any(canonical(entry["referenceFormKey"]) == excluded_key for entry in row["entries"])
            ]
            check(f"excluded {excluded_key} absent from every current LVLI", not remaining, str(remaining))

        choice_key = canonical("000800:Ensrick Lost LongSwords Curation.esp")
        choice = graph[choice_key]
        native = [entry for entry in choice["entries"] if canonical(entry["referenceFormKey"]) == canonical("0135B8:Skyrim.esm")]
        imperial = [entry for entry in choice["entries"] if canonical(entry["referenceFormKey"]) == canonical("008F16:LostLongSwords.esp")]
        check(
            "Imperial owned list 11 native entries",
            len(native) == 11
            and all(int(row["level"]) == 1 and int(row["count"]) == 1 for row in native),
            str(native),
        )
        check(
            "Imperial owned list one level-5 longsword",
            len(imperial) == 1
            and int(imperial[0]["level"]) == 5
            and int(imperial[0]["count"]) == 1,
            str(imperial),
        )
        check("Imperial chance global absent", choice.get("chanceNoneGlobalFormKey") is None and float(choice["chanceNone"]) == 0, str(choice))

        storm_two_hand = graph[
            canonical("000800:Ensrick Lost LongSwords Stormcloak Distribution.esp")
        ]
        storm_parent = graph[
            canonical("000801:Ensrick Lost LongSwords Stormcloak Distribution.esp")
        ]
        storm_gear = graph[
            canonical("000802:Ensrick Lost LongSwords Stormcloak Distribution.esp")
        ]
        storm_entries = [
            entry
            for entry in storm_two_hand["entries"]
            if canonical(entry["referenceFormKey"])
            == canonical("0099DF:LostLongSwords.esp")
        ]
        parent_two_hand_entries = [
            entry
            for entry in storm_parent["entries"]
            if canonical(entry["referenceFormKey"])
            == canonical(
                "000800:Ensrick Lost LongSwords Stormcloak Distribution.esp"
            )
        ]
        gear_parent_entries = [
            entry
            for entry in storm_gear["entries"]
            if canonical(entry["referenceFormKey"])
            == canonical(
                "000801:Ensrick Lost LongSwords Stormcloak Distribution.esp"
            )
        ]
        check(
            "owned Stormcloak 2H pool exact four equal-eligibility choices",
            len(storm_two_hand["entries"]) == 4
            and len(storm_entries) == 1
            and all(
                int(entry["level"]) == 1 and int(entry["count"]) == 1
                for entry in storm_two_hand["entries"]
            ),
            str(storm_two_hand),
        )
        check(
            "owned Stormcloak mixed-style parent exact three equal-eligibility choices",
            len(storm_parent["entries"]) == 3
            and len(parent_two_hand_entries) == 1
            and all(
                int(entry["level"]) == 1 and int(entry["count"]) == 1
                for entry in storm_parent["entries"]
            ),
            str(storm_parent),
        )
        check(
            "owned Stormcloak UseAll gear reaches its isolated parent exactly once",
            len(gear_parent_entries) == 1
            and storm_gear.get("flags") == "UseAll",
            str(storm_gear),
        )
        check(
            "Stormcloak probability globals absent",
            storm_two_hand.get("chanceNoneGlobalFormKey") is None
            and storm_parent.get("chanceNoneGlobalFormKey") is None
            and storm_gear.get("chanceNoneGlobalFormKey") is None
            and float(storm_two_hand["chanceNone"]) == 0
            and float(storm_parent["chanceNone"]) == 0
            and float(storm_gear["chanceNone"]) == 0,
            f"2H={storm_two_hand}, parent={storm_parent}, gear={storm_gear}",
        )
        selection_flags = {
            "CalculateFromAllLevelsLessThanOrEqualPlayer",
            "CalculateForEachItemInCount",
        }
        check(
            "Stormcloak branches use random-choice flags",
            {
                value.strip()
                for value in str(storm_two_hand.get("flags") or "").split(",")
                if value.strip()
            }
            == selection_flags
            and {
                value.strip()
                for value in str(storm_parent.get("flags") or "").split(",")
                if value.strip()
            }
            == selection_flags,
            f"2H={storm_two_hand.get('flags')}, parent={storm_parent.get('flags')}",
        )
        shared_sos_two_hand = graph[canonical("00C3B7:NW_Sons_of_Skyrim.esp")]
        check(
            "shared Sons of Skyrim branch has no longsword injection",
            not any(
                canonical(entry["referenceFormKey"])
                == canonical("0099DF:LostLongSwords.esp")
                for entry in shared_sos_two_hand["entries"]
            ),
            str(shared_sos_two_hand),
        )

        private_plugins = {
            "lostlongswords.esp",
            "ensrick lost longswords curation.esp",
            "ensrick lost longswords stormcloak distribution.esp",
        }
        prohibited_all = re.compile(
            r"(?<!red)guard|commander|officer|general|captain|legate|jarl|housecarl|thane|"
            r"draugr|vampire|falmer|forsworn|giant|werewolf|warlock|creature|monster",
            re.I,
        )
        military = re.compile(
            r"stormcloak|sons|soldier|civilwar|legion|(^|_)cw|(?<!red)guard|"
            r"commander|officer|general|legate",
            re.I,
        )
        wrong_imperial = re.compile(r"stormcloak|sons", re.I)
        wrong_stormcloak = re.compile(
            r"legion|^(?=.*imperial)(?=.*(?:soldier|(?<!red)guard|commander|"
            r"officer|general|legate|civilwar|cw))",
            re.I,
        )
        acquisition_report: dict[str, Any] = {}
        for weapon in policy["weapons"]:
            ancestors = acquisition_ancestors(
                graph, patched_npcs, outfit_winners, weapon["formKey"], private_plugins
            )
            bad = sorted(
                f"{kind}:{editor_id}"
                for kind, editor_id in ancestors.values()
                if prohibited_all.search(editor_id)
            )
            check(
                f"{weapon['editorId']} no typed guard/commander/monster path",
                not bad,
                str(bad),
            )
            if weapon["editorId"] == "ImperialLongSword":
                wrong = sorted(
                    f"{kind}:{editor_id}"
                    for kind, editor_id in ancestors.values()
                    if wrong_imperial.search(editor_id)
                )
                check("Imperial longsword no typed wrong-faction path", not wrong, str(wrong))
            elif weapon["editorId"] == "StormcloakLongSword":
                wrong = sorted(
                    f"{kind}:{editor_id}"
                    for kind, editor_id in ancestors.values()
                    if wrong_stormcloak.search(editor_id)
                )
                check("Stormcloak longsword no typed wrong-faction path", not wrong, str(wrong))
            else:
                military_paths = sorted(
                    f"{kind}:{editor_id}"
                    for kind, editor_id in ancestors.values()
                    if military.search(editor_id)
                )
                check(
                    f"{weapon['editorId']} has no typed military consumer",
                    not military_paths,
                    str(military_paths),
                )
            acquisition_report[weapon["editorId"]] = [
                {"formKey": key, "type": value[0], "editorId": value[1]}
                for key, value in sorted(ancestors.items())
            ]

        # Both faction branches are deliberately narrow: one non-unique base
        # template plus its exact reviewed Inventory-inheriting descendants.
        # Non-Inventory children (including guards/commanders) remain outside.
        def audit_template_branch(
            label: str,
            template_policy: dict[str, Any],
            old_gear_form: str,
            new_gear_form: str,
        ) -> dict[str, tuple[str, str]]:
            direct_key = canonical(template_policy["directTemplate"])
            direct_before = npc_winners.get(direct_key)
            direct = patched_npcs.get(direct_key)
            check(f"{label} direct template exists", direct is not None, direct_key)
            if direct is not None and direct_before is not None:
                direct_items_before = [
                    canonical(item["itemFormKey"])
                    for item in (direct_before.get("items") or [])
                ]
                direct_items = [
                    canonical(item["itemFormKey"])
                    for item in (direct.get("items") or [])
                ]
                check(
                    f"{label} direct template identity/nonunique",
                    direct.get("editorId") == template_policy["directTemplateEditorId"]
                    and bool(direct.get("unique"))
                    == bool(template_policy["directTemplateIsUnique"])
                    and (
                        not template_policy.get("winningProvider")
                        or direct.get("winningProvider", "").casefold()
                        == template_policy["winningProvider"].casefold()
                    ),
                    str(direct),
                )
                check(
                    f"{label} direct template has one reviewed old gear object",
                    direct_items_before.count(canonical(old_gear_form)) == 1,
                    str(direct_items_before),
                )
                check(
                    f"{label} template exact runtime gear replacement",
                    direct_items.count(canonical(old_gear_form)) == 0
                    and direct_items.count(canonical(new_gear_form)) == 1,
                    str(direct_items),
                )

            inventory_children: dict[str, set[str]] = defaultdict(set)
            direct_noninventory_children: set[str] = set()
            for key, npc in patched_npcs.items():
                template = npc.get("templateFormKey")
                if not template:
                    continue
                parent = canonical(template)
                if "Inventory" in (npc.get("templateFlags") or ""):
                    inventory_children[parent].add(key)
                elif parent == direct_key:
                    direct_noninventory_children.add(key)
            inventory_descendants: set[str] = set()
            pending = list(inventory_children.get(direct_key, set()))
            while pending:
                child = pending.pop()
                if child in inventory_descendants:
                    continue
                inventory_descendants.add(child)
                pending.extend(inventory_children.get(child, set()))
            expected_descendant_rows = {
                canonical(row["formKey"]): row
                for row in template_policy["inventoryInheritors"]
            }
            expected_inventory_descendants = set(expected_descendant_rows)
            expected_noninventory = {
                canonical(value) for value in template_policy["nonInventoryInheritors"]
            }
            check(
                f"exact {label} Inventory-template descendants",
                inventory_descendants == expected_inventory_descendants,
                str(
                    {
                        "actual": sorted(inventory_descendants),
                        "expected": sorted(expected_inventory_descendants),
                    }
                ),
            )
            check(
                f"exact {label} direct non-Inventory descendants",
                direct_noninventory_children == expected_noninventory,
                str(
                    {
                        "actual": sorted(direct_noninventory_children),
                        "expected": sorted(expected_noninventory),
                    }
                ),
            )
            bad_descendant_identity = {
                key: patched_npcs.get(key)
                for key, row in expected_descendant_rows.items()
                if key not in patched_npcs
                or patched_npcs[key].get("editorId") != row["editorId"]
                or bool(patched_npcs[key].get("unique"))
            }
            check(
                f"{label} reviewed descendants are exact nonunique NPCs",
                not bad_descendant_identity,
                str(bad_descendant_identity),
            )
            inherited_forbidden = sorted(
                patched_npcs[key].get("editorId") or key
                for key in inventory_descendants
                if prohibited_all.search(patched_npcs[key].get("editorId") or "")
            )
            check(
                f"no guard/commander inherits {label} gear",
                not inherited_forbidden
                and not template_policy["guardOrCommanderInventoryInheritors"],
                str(inherited_forbidden),
            )
            gear_consumers = acquisition_ancestors(
                graph,
                patched_npcs,
                outfit_winners,
                new_gear_form,
                private_plugins,
            )
            actual_gear_npcs = {
                key for key, (kind, _) in gear_consumers.items() if kind == "Npc"
            }
            expected_gear_npcs = {direct_key} | expected_inventory_descendants
            check(
                f"owned {label} gear reaches exactly reviewed ordinary NPC templates",
                actual_gear_npcs == expected_gear_npcs,
                str(
                    {
                        "actual": sorted(actual_gear_npcs),
                        "expected": sorted(expected_gear_npcs),
                    }
                ),
            )
            return gear_consumers

        imperial_gear_consumers = audit_template_branch(
            "Imperial",
            policy["imperialTemplateAudit"],
            "10FAFC:Skyrim.esm",
            "000801:Ensrick Lost LongSwords Curation.esp",
        )
        storm_gear_consumers = audit_template_branch(
            "Stormcloak",
            policy["stormcloakTemplateAudit"],
            "00C3BA:NW_Sons_of_Skyrim.esp",
            "000802:Ensrick Lost LongSwords Stormcloak Distribution.esp",
        )

        expected_replace_targets = {
            canonical(policy["imperialTemplateAudit"]["directTemplate"]),
            canonical(policy["stormcloakTemplateAudit"]["directTemplate"]),
            *(
                canonical(row["formKey"])
                for audit_name in ("imperialTemplateAudit", "stormcloakTemplateAudit")
                for row in policy[audit_name]["inventoryInheritors"]
            ),
        }
        actual_replace_targets = {
            canonical(operation["target"])
            for operation in policy["npcOperations"]
            if "replace" in operation
        }
        check(
            "NPC replacement scope is exactly the five reviewed ordinary templates",
            actual_replace_targets == expected_replace_targets,
            str(
                {
                    "actual": sorted(actual_replace_targets),
                    "expected": sorted(expected_replace_targets),
                }
            ),
        )

        # The new UseAll gear list is an exact projection of the latest current
        # non-vendor 10FAFC winner, with its single native weapon slot swapped
        # for the owned 1/12 choice list.
        baseline_chain = [
            item
            for item in versions.get(canonical("10FAFC:Skyrim.esm"), [])
            if item[1].casefold() not in {vendor_name.casefold(), curation_name.casefold()}
        ]
        check("current non-vendor 10FAFC baseline exists", bool(baseline_chain), str(baseline_chain))
        if baseline_chain:
            _, baseline_provider, baseline_gear = baseline_chain[-1]
            built_gear = graph[canonical("000801:Ensrick Lost LongSwords Curation.esp")]

            native_slot = canonical("0135B8:Skyrim.esm")
            choice_slot = canonical("000800:Ensrick Lost LongSwords Curation.esp")
            expected_entries = leveled_entry_counter(baseline_gear)
            native_keys = [key for key in expected_entries if key[2] == native_slot]
            check(
                "10FAFC has one native weapon-slot entry",
                len(native_keys) == 1 and expected_entries[native_keys[0]] == 1,
                str(expected_entries),
            )
            if len(native_keys) == 1 and expected_entries[native_keys[0]] == 1:
                old_key = native_keys[0]
                del expected_entries[old_key]
                expected_entries[(old_key[0], old_key[1], choice_slot)] += 1
            check(
                "owned Imperial gear exact current 10FAFC projection",
                leveled_entry_counter(built_gear) == expected_entries
                and baseline_gear.get("flags") == "UseAll"
                and built_gear.get("flags") == "UseAll"
                and float(baseline_gear.get("chanceNone", -1)) == 0
                and baseline_gear.get("chanceNoneGlobalFormKey") is None
                and float(built_gear.get("chanceNone", -1)) == 0
                and built_gear.get("chanceNoneGlobalFormKey") is None,
                f"provider={baseline_provider}; expected={expected_entries}; actual={leveled_entry_counter(built_gear)}",
            )

        custom_weapon_keys = set(policy_weapons)
        direct_assignments = sorted(
            (npc.get("editorId") or npc["formKey"], item["itemFormKey"])
            for npc in patched_npcs.values()
            for item in (npc.get("items") or [])
            if canonical(item["itemFormKey"]) in custom_weapon_keys
        )
        check("no direct named-NPC longsword assignments remain", not direct_assignments, str(direct_assignments))

        # Prove the Stormcloak soldier branch has typed, non-unique consumers
        # and no guard/command path. The exact current set is retained in the
        # report, while every input binary is hash-pinned below.
        storm_branch = storm_gear_consumers
        storm_npcs = {
            key: patched_npcs[key]
            for key, (kind, _) in storm_branch.items()
            if kind == "Npc"
        }
        storm_forbidden = sorted(
            npc.get("editorId") or key
            for key, npc in storm_npcs.items()
            if bool(npc.get("unique"))
            or prohibited_all.search(npc.get("editorId") or "")
            or wrong_stormcloak.search(npc.get("editorId") or "")
            or not military.search(npc.get("editorId") or "")
        )
        check(
            "Stormcloak branch has ordinary nonunique non-guard consumers only",
            bool(storm_npcs) and not storm_forbidden,
            str(storm_forbidden),
        )

        approved_substitution_keys: set[str] = set()
        substitution_report: dict[str, Any] = {}
        for substitution in policy.get("approvedSemanticSubstitutions", []):
            key = canonical(substitution["target"])
            approved_substitution_keys.add(key)
            chain = versions.get(key, [])
            baselines = [
                row
                for row in chain
                if row[0] < vendor_index
                and row[1].casefold()
                not in {
                    vendor_name.casefold(),
                    curation_name.casefold(),
                    storm_curation_name.casefold(),
                }
            ]
            baseline = baselines[-1] if baselines else None
            current = chain[-1] if chain else None
            final = graph.get(key)
            baseline_expected = leveled_entry_counter(
                {"entries": substitution["baseline"]}
            )
            final_expected = leveled_entry_counter(
                {"entries": substitution["intendedFinal"]}
            )
            policy_delta_ok = (
                sum(baseline_expected.values()) == 6
                and sum(final_expected.values()) == 6
                and baseline_expected - final_expected
                == Counter({(1, 1, canonical("10AA19:Skyrim.esm")): 1})
                and final_expected - baseline_expected
                == Counter(
                    {(1, 1, canonical("007423:LostLongSwords.esp")): 1}
                )
            )
            substitution_ok = (
                policy_delta_ok
                and baseline is not None
                and current is not None
                and final is not None
                and baseline[2].get("editorId") == substitution["editorId"]
                and leveled_entry_counter(baseline[2]) == baseline_expected
                and leveled_non_entry_semantics(current[2])
                == leveled_non_entry_semantics(baseline[2])
                and leveled_non_entry_semantics(final)
                == leveled_non_entry_semantics(baseline[2])
                and leveled_entry_counter(final) == final_expected
                and len(final.get("entries") or []) == 6
            )
            check(
                f"exact approved semantic substitution {substitution['target']}",
                substitution_ok,
                str(
                    {
                        "baselineProvider": baseline[1] if baseline else None,
                        "currentProvider": current[1] if current else None,
                        "baselineExpected": baseline_expected,
                        "baselineActual": leveled_entry_counter(
                            baseline[2] if baseline else None
                        ),
                        "finalExpected": final_expected,
                        "finalActual": leveled_entry_counter(final),
                    }
                ),
            )
            substitution_report[substitution["target"]] = {
                "baselineProvider": baseline[1] if baseline else None,
                "currentProvider": current[1] if current else None,
                "exactOneOfThreeNativeSlotsReplaced": substitution_ok,
            }

        leveled_gate_violations: list[dict[str, Any]] = []
        for edge in policy["vendorLeveledEdges"]:
            key = canonical(edge["target"])
            chain = versions.get(key, [])
            current = chain[-1] if chain else None
            if current is None:
                leveled_gate_violations.append({"formKey": edge["target"], "reason": "absent"})
                continue
            if (
                current[1].casefold() == vendor_name.casefold()
                and key
                not in {
                    canonical(row["formKey"])
                    for row in policy["masterForwarding"]["records"]
                }
                and key not in approved_substitution_keys
            ):
                previous = [row for row in chain if row[0] < vendor_index and row[1].casefold() != vendor_name.casefold()]
                if not previous:
                    leveled_gate_violations.append(
                        {"formKey": edge["target"], "reason": "no pre-vendor baseline"}
                    )
                    continue
                vendor_clean = dict(
                    current[2],
                    entries=[dict(item) for item in (current[2].get("entries") or [])],
                )
                removals = {
                    canonical(item["remove"])
                    for item in policy["vendorLeveledEdges"]
                    if canonical(item["target"]) == key
                }
                vendor_clean["entries"] = [
                    item
                    for item in vendor_clean["entries"]
                    if canonical(item["referenceFormKey"]) not in removals
                ]

                def lvli_semantics(record: dict[str, Any]) -> tuple[Any, ...]:
                    return (
                        record.get("editorId"),
                        float(record.get("chanceNone", 0)),
                        canonical(record["chanceNoneGlobalFormKey"])
                        if record.get("chanceNoneGlobalFormKey")
                        else None,
                        record.get("flags"),
                        tuple(
                            (
                                int(item["level"]),
                                int(item["count"]),
                                canonical(item["referenceFormKey"]),
                            )
                            for item in (record.get("entries") or [])
                        ),
                    )

                if lvli_semantics(vendor_clean) != lvli_semantics(previous[-1][2]):
                    leveled_gate_violations.append(
                        {
                            "formKey": edge["target"],
                            "reason": "vendor has non-injection semantic drift and no later winner",
                            "baselineProvider": previous[-1][1],
                        }
                    )
        check(
            "vendor LVLI load-order preservation gate",
            not leveled_gate_violations,
            json.dumps(leveled_gate_violations, separators=(",", ":")),
        )

        forwarded_targets = {
            canonical(row["formKey"]): row["type"]
            for row in policy["masterForwarding"]["records"]
        }
        forwarded_versions = scan_exact_record_versions(
            tool, audit_ordered, cache_root, forwarded_targets, max(1, args.workers)
        )
        forward_order_violations: list[dict[str, Any]] = []
        forward_chains: dict[str, list[dict[str, Any]]] = {}
        forward_policy_by_key = {
            canonical(row["formKey"]): row
            for row in policy["masterForwarding"]["records"]
        }
        for key, expected_type in forwarded_targets.items():
            chain = forwarded_versions.get(key, [])
            forward_chains[key] = [
                {"loadIndex": index, "plugin": name, "type": row["type"]}
                for index, name, row in chain
            ]
            names = [name.casefold() for _, name, _ in chain]
            declared_provider = forward_policy_by_key[key]["provider"].casefold()
            required_names = {
                declared_provider,
                vendor_name.casefold(),
                curation_name.casefold(),
            }
            missing_names = sorted(
                name for name in required_names if names.count(name) != 1
            )
            if missing_names:
                forward_order_violations.append(
                    {
                        "formKey": key,
                        "reason": "declared provider/vendor/curation chain is not exact",
                        "missingOrDuplicate": missing_names,
                        "providers": names,
                    }
                )
                continue
            provider_chain_index = next(
                index
                for index, name, _ in chain
                if name.casefold() == declared_provider
            )
            vendor_chain_index = next(
                index
                for index, name, _ in chain
                if name.casefold() == vendor_name.casefold()
            )
            curation_chain_index = next(
                index
                for index, name, _ in chain
                if name.casefold() == curation_name.casefold()
            )
            if not (
                provider_chain_index < vendor_chain_index < curation_chain_index
                and curation_chain_index == vendor_chain_index + 1
                and all(row[2]["type"] == expected_type for row in chain)
            ):
                forward_order_violations.append(
                    {
                        "formKey": key,
                        "reason": "forward chain order/type contract failed",
                        "declaredProviderIndex": provider_chain_index,
                        "vendorIndex": vendor_chain_index,
                        "curationIndex": curation_chain_index,
                        "providers": names,
                    }
                )
        check(
            "all approved forwards preserve later regular winners",
            not forward_order_violations,
            json.dumps(forward_order_violations, separators=(",", ":")),
        )

        ordered_after, profile_fingerprint_after = resolve_profile(
            args.profile, args.mods_root, args.game_data
        )
        final_input_snapshot = [
            (name.casefold(), str(path).casefold(), sha256(path))
            for name, path in ordered_after
        ]
        check(
            "profile and input binaries stable during current-stack audit",
            profile_fingerprint_after == profile_fingerprint
            and final_input_snapshot == initial_input_snapshot,
            "plugins.txt/modlist.txt/provider paths or bytes changed during audit",
        )

        load_order_report = {
            "skipped": False,
            **profile_fingerprint,
            "auditMode": "actual-installed" if installed_mode else "planned-in-memory",
            "enabledAndOfficialPlugins": len(manifest),
            "actualVendorLoadIndex": actual_vendor_index,
            "actualCurationLoadIndex": actual_curation_index,
            "actualStormcloakCurationLoadIndex": actual_storm_curation_index,
            "vendorLoadIndex": vendor_index,
            "ussepLoadIndex": ussep_index,
            "sonsOfSkyrimLoadIndex": sos_index,
            "sonsLuxOrbisPatchLoadIndex": lux_index,
            "curationLoadIndex": curation_index,
            "stormcloakCurationLoadIndex": storm_curation_index,
            "requiredCurationInsertion": (
                "actual profile: vendor/early curation start regular stage; Stormcloak curation follows SoS immediately"
                if installed_mode
                else "in-memory plan: vendor/early candidate start regular stage; Stormcloak candidate follows SoS immediately"
            ),
            "leveledGateViolations": leveled_gate_violations,
            "approvedSemanticSubstitutions": substitution_report,
            "forwardOrderViolations": forward_order_violations,
            "forwardProviderChains": forward_chains,
            "acquisition": acquisition_report,
            "imperialGearConsumers": [
                {"formKey": key, "type": value[0], "editorId": value[1]}
                for key, value in sorted(imperial_gear_consumers.items())
            ],
            "stormcloakBranchConsumers": [
                {"formKey": key, "type": value[0], "editorId": value[1]}
                for key, value in sorted(storm_branch.items())
            ],
            "inputs": manifest,
        }

    final_hashes = {
        "policy": sha256(args.policy),
        "proposal": sha256(args.proposal),
        "vendorSource": sha256(source_plugin),
        "skyrimSource": sha256(skyrim_plugin),
        "ussepSource": sha256(ussep_plugin),
        "sonsOfSkyrimSource": sha256(
            compatibility_inputs[policy["compatibility"]["sonsOfSkyrimPlugin"].casefold()]
        ),
        "sonsLuxOrbisSource": sha256(
            compatibility_inputs[
                policy["compatibility"]["sonsLuxOrbisPatchPlugin"].casefold()
            ]
        ),
        "sourceValidationTree": sha256_tree(source_yaml),
        "roundtripTree": sha256_tree(roundtrip),
        "stormSourceTree": sha256_tree(storm_source_tree),
        "skyPatcherTree": sha256_tree(skypatcher_tree),
        "skyPatcherDll": sha256(skypatcher_dll),
        "recordToolExe": sha256(tool),
        "recordToolDll": sha256(tool.with_name("skyrim-record-cli.dll")),
        "builtPlugin": sha256(built_plugin),
        "stormBuiltPlugin": sha256(storm_built_plugin),
    }
    check(
        "tested source/tool/artifact bytes stable",
        final_hashes == initial_hashes,
        str(
            {
                key: {"initial": initial_hashes.get(key), "final": value}
                for key in sorted(set(initial_hashes) | set(final_hashes))
                if initial_hashes.get(key) != final_hashes.get(key)
                for value in [final_hashes.get(key)]
            }
        ),
    )

    report = {
        "schemaVersion": 1,
        "status": "PASS" if not errors else "FAIL",
        "policySha256": initial_hashes["policy"],
        "proposalSha256": initial_hashes["proposal"],
        "outputPluginSha256": initial_hashes["builtPlugin"],
        "stormcloakOutputPluginSha256": initial_hashes["stormBuiltPlugin"],
        "checks": checks,
        "errors": errors,
        "currentLoadOrder": load_order_report,
        "runtimeValidationStillRequired": True,
        "liveInstallOrLaunchPerformed": False,
    }
    report_path = output / "test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "policySha256",
                    "outputPluginSha256",
                    "stormcloakOutputPluginSha256",
                    "errors",
                )
            },
            indent=2,
            allow_nan=False,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        raise
