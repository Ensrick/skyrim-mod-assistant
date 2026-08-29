"""Audit the generated compatibility plugin against Decision A and its inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import zipfile

REPOSITORY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPOSITORY, "audit"))
import semantic_record_conflicts as semantic  # noqa: E402


WORLDSPACE_FIELDS = semantic.FIELDS_BY_TYPE["Worldspace"]
CELL_FIELDS = semantic.FIELDS_BY_TYPE["Cell"]
WATER_FIELDS = {"Water", "LodWater", "LodWaterHeight", "WaterEnvironmentMap"}
OUTPUT_NAME = "Ensrick General Compatibility Patch.esp"
ESL_FLAG = 0x00000200
INVENTORY_CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")),
    "SkyrimModAssistant",
    "record-inventories",
)


def run_json_lines(executable: str, *arguments: str) -> list[dict]:
    process = subprocess.run(
        [executable, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if process.returncode:
        raise RuntimeError((process.stderr or process.stdout)[-2000:])
    return [json.loads(line) for line in process.stdout.splitlines() if line.strip()]


def selected(executable: str, path: str, record_type: str, fields: tuple[str, ...]) -> dict[str, dict]:
    rows = run_json_lines(
        executable,
        "record-selected-fields-by-type",
        path,
        record_type,
        ",".join(fields),
    )
    return {row["formKey"]: row for row in rows}


def inventory(executable: str, path: str) -> list[dict]:
    plugin_hash = sha256(path).lower()
    os.makedirs(INVENTORY_CACHE, exist_ok=True)
    cached = os.path.join(INVENTORY_CACHE, plugin_hash + ".json")
    if os.path.exists(cached):
        with open(cached, encoding="utf-8") as stream:
            return json.load(stream)
    rows = run_json_lines(executable, "records", path)
    temporary = f"{cached}.{os.getpid()}.tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(rows, stream, ensure_ascii=False)
    os.replace(temporary, cached)
    return rows


def fingerprint(value, field: str | None = None) -> str:
    return json.dumps(semantic.canonical(value, field), sort_keys=True, separators=(",", ":"))


def plugin_flags(path: str) -> int:
    with open(path, "rb") as stream:
        header = stream.read(12)
    if len(header) != 12 or header[:4] != b"TES4":
        raise ValueError("output is not a TES4 plugin")
    return struct.unpack_from("<I", header, 8)[0]


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def build_index(instance_root: str, profile: str, data_folder: str) -> dict[str, str]:
    index: dict[str, str] = {}
    modlist = os.path.join(instance_root, "profiles", profile, "modlist.txt")
    with open(modlist, encoding="utf-8") as stream:
        for raw_line in stream:
            line = raw_line.rstrip("\r\n")
            if not line.startswith("+"):
                continue
            folder = os.path.join(instance_root, "mods", line[1:])
            if not os.path.isdir(folder):
                continue
            for name in os.listdir(folder):
                if name.lower().endswith((".esm", ".esp", ".esl")):
                    index.setdefault(name.lower(), os.path.join(folder, name))
    if os.path.isdir(data_folder):
        for name in os.listdir(data_folder):
            if name.lower().endswith((".esm", ".esp", ".esl")):
                index.setdefault(name.lower(), os.path.join(data_folder, name))
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--load-order", required=True)
    parser.add_argument("--record-cli", required=True)
    parser.add_argument("--decisions", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--instance-root", required=True)
    parser.add_argument("--provider-profile", required=True)
    parser.add_argument("--data-folder", required=True)
    arguments = parser.parse_args()

    with open(arguments.decisions, encoding="utf-8") as stream:
        decisions = json.load(stream)["recommendedPlugin"]

    worldspace_targets = {
        item["formKey"]: {
            "editorId": item["editorId"],
            "source": "Lux Orbis CS.esp",
            "owned": set(item["fields"]),
        }
        for item in decisions["worldspaceFieldsFromLuxOrbisCs"]
    }
    worldspace_targets.update({
        item["formKey"]: {
            "editorId": item["editorId"],
            "source": "BSHeartland.esm",
            "owned": set(item["fields"]),
        }
        for item in decisions["worldspaceFieldsFromBruma"]
    })
    cell_targets = {
        item["formKey"]: {
            "editorId": item["editorId"],
            "source": "Lux Orbis CS.esp",
            "owned": set(item["fields"]),
        }
        for item in decisions["cellFieldsFromLuxOrbisCs"]
    }
    expected_keys = set(worldspace_targets) | set(cell_targets)

    info = run_json_lines(arguments.record_cli, "plugin-info", arguments.plugin)[0]
    records = run_json_lines(arguments.record_cli, "records", arguments.plugin)
    actual_keys = {row["formKey"] for row in records}
    failures: list[str] = []
    if info["records"] != 14:
        failures.append(f"expected 14 records, found {info['records']}")
    if info["recordTypes"] != {"CellBinaryOverlay": 2, "WorldspaceBinaryOverlay": 12}:
        failures.append(f"unexpected record types: {info['recordTypes']}")
    if actual_keys != expected_keys:
        failures.append(
            f"record set differs; missing={sorted(expected_keys - actual_keys)}, "
            f"extra={sorted(actual_keys - expected_keys)}"
        )
    if any(row["formKey"].lower().endswith(f":{OUTPUT_NAME.lower()}") for row in records):
        failures.append("output contains a newly allocated form")
    if not plugin_flags(arguments.plugin) & ESL_FLAG:
        failures.append("TES4 Small/ESL flag is absent")

    with open(arguments.load_order, encoding="utf-8") as stream:
        ordered_plugins = [
            line.strip().lstrip("*")
            for line in stream
            if line.strip() and not line.lstrip().startswith("#")
        ]
    positions = {name.lower(): index for index, name in enumerate(ordered_plugins)}
    index = build_index(arguments.instance_root, arguments.provider_profile, arguments.data_folder)
    implicit_masters = {
        name.lower()
        for name in os.listdir(arguments.data_folder)
        if name.lower().endswith((".esm", ".esp", ".esl"))
    }

    for master in info["masters"]:
        if master.lower() not in positions and master.lower() not in implicit_masters:
            failures.append(f"missing output master: {master}")
        if master.lower() not in index:
            failures.append(f"master has no resolved provider: {master}")

    chain_entries: dict[str, list[tuple[int, str, str]]] = {
        form_key: [] for form_key in expected_keys
    }
    for position, plugin in enumerate(ordered_plugins):
        path = index.get(plugin.lower())
        if not path:
            continue
        try:
            plugin_records = inventory(arguments.record_cli, path)
        except Exception as exception:
            failures.append(f"could not inventory {plugin}: {exception}")
            continue
        for row in plugin_records:
            form_key = row.get("formKey")
            if form_key in chain_entries:
                chain_entries[form_key].append((position, plugin, path))

    output_by_type = {
        "Worldspace": selected(arguments.record_cli, arguments.plugin, "Worldspace", WORLDSPACE_FIELDS),
        "Cell": selected(arguments.record_cli, arguments.plugin, "Cell", CELL_FIELDS),
    }
    selected_cache: dict[tuple[str, str], dict[str, dict]] = {}

    def row_for(path: str, record_type: str, form_key: str) -> dict | None:
        cache_key = (path.lower(), record_type)
        if cache_key not in selected_cache:
            fields = WORLDSPACE_FIELDS if record_type == "Worldspace" else CELL_FIELDS
            selected_cache[cache_key] = selected(arguments.record_cli, path, record_type, fields)
        return selected_cache[cache_key].get(form_key)

    checked_fields = 0
    proven_water_fields = 0
    for record_type, targets in (("Worldspace", worldspace_targets), ("Cell", cell_targets)):
        all_fields = WORLDSPACE_FIELDS if record_type == "Worldspace" else CELL_FIELDS
        for form_key, target in targets.items():
            chain = chain_entries[form_key]
            if not chain:
                failures.append(f"no active input chain for {form_key}")
                continue
            winner = chain[-1]
            sources = [entry for entry in chain if entry[1].lower() == target["source"].lower()]
            if not sources:
                failures.append(f"{target['source']} does not provide {form_key}")
                continue
            source = sources[-1]
            output_row = output_by_type[record_type].get(form_key)
            winner_row = row_for(winner[2], record_type, form_key)
            source_row = row_for(source[2], record_type, form_key)
            if not output_row or not winner_row or not source_row:
                failures.append(f"could not load selected fields for {form_key}")
                continue
            if output_row.get("editorId") != target["editorId"]:
                failures.append(
                    f"EditorID mismatch for {form_key}: {output_row.get('editorId')} != {target['editorId']}"
                )
            for field in all_fields:
                expected_row = source_row if field in target["owned"] else winner_row
                expected = fingerprint(expected_row["fields"].get(field), field)
                actual = fingerprint(output_row["fields"].get(field), field)
                checked_fields += 1
                if record_type == "Worldspace" and field in WATER_FIELDS:
                    proven_water_fields += 1
                if actual != expected:
                    failures.append(
                        f"{form_key} {field}: output differs from "
                        f"{'owned source ' + source[1] if field in target['owned'] else 'final winner ' + winner[1]}"
                    )

    with zipfile.ZipFile(arguments.archive) as archive:
        entries = archive.infolist()
        if len(entries) != 1 or entries[0].filename != OUTPUT_NAME:
            failures.append(f"archive entries are not exactly [{OUTPUT_NAME}]")
        else:
            archived_hash = hashlib.sha256(archive.read(entries[0])).hexdigest().upper()
            if archived_hash != sha256(arguments.plugin):
                failures.append("archived plugin bytes differ from generated plugin")
            if entries[0].date_time != (2000, 1, 1, 0, 0, 0):
                failures.append(f"archive timestamp is not deterministic: {entries[0].date_time}")

    result = {
        "ok": not failures,
        "pluginSha256": sha256(arguments.plugin),
        "records": len(records),
        "recordTypes": info["recordTypes"],
        "masters": info["masters"],
        "selectedFieldsChecked": checked_fields,
        "worldspaceWaterFieldsComparedToFinalWinner": proven_water_fields,
        "newForms": sum(
            row["formKey"].lower().endswith(f":{OUTPUT_NAME.lower()}") for row in records
        ),
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
