"""Compare selected fields after a known compatibility anchor plugin.

The broad FormKey inventory intentionally over-reports. This audit asks the
more useful question: for records touched by an anchor such as Lux Orbis CS,
which semantic header fields are different in the final active winner?

Run:
  py -3 audit/semantic_record_conflicts.py Cell "Lux Orbis CS.esp" [output-dir]
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import record_conflicts
import verify_order as order


RECORD_CLI = (
    r"C:\Users\danjo\source\repos\skyrim-tools-builds"
    r"\skyrim-record-cli-1f3c8d9\skyrim-record-cli.exe"
)
CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")),
    "SkyrimModAssistant",
    "semantic-fields",
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records"
)
FIELDS_BY_TYPE = {
    "Cell": (
        "AcousticSpace",
        "EncounterZone",
        "FactionRank",
        "Flags",
        "Grid",
        "ImageSpace",
        "LNAM",
        "Lighting",
        "LightingTemplate",
        "Location",
        "LockList",
        "MaxHeightData",
        "Music",
        "Name",
        "OcclusionData",
        "Owner",
        "Regions",
        "SkyAndWeatherFromRegion",
        "Water",
        "WaterEnvironmentMap",
        "WaterHeight",
        "WaterNoiseTexture",
        "WaterVelocity",
        "XWCN",
        "XWCS",
    ),
    "Worldspace": (
        "CanopyShadow",
        "Climate",
        "CloudModel",
        "DistantLodMultiplier",
        "EncounterZone",
        "FixedDimensionsCenterCell",
        "Flags",
        "HdLodDiffuseTexture",
        "HdLodNormalTexture",
        "InteriorLighting",
        "LandDefaults",
        "Location",
        "LodWater",
        "LodWaterHeight",
        "MapData",
        "MapImage",
        "MaxHeight",
        "Music",
        "Name",
        "ObjectBoundsMax",
        "ObjectBoundsMin",
        "Parent",
        "Water",
        "WaterEnvironmentMap",
        "WaterNoiseTexture",
        "WorldMapCellOffset",
        "WorldMapOffsetScale",
    ),
}
NOISE_KEYS = {
    "Absolute",
    "AssetTypeInstance",
    "Extension",
    "FormKeyNullable",
    "IsNull",
    "Length",
    "Magnitude",
    "Normalized",
    "NullableRawEqualityComparer",
    "SqrMagnitude",
    "StaticRegistration",
    "Type",
}


def sha256(path: str) -> str:
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value, field: str | None = None):
    if field == "Grid" and isinstance(value, dict):
        return value.get("Point")
    if isinstance(value, dict):
        if "FormKey" in value:
            return value["FormKey"]
        if "GivenPath" in value:
            return value["GivenPath"].replace("/", "\\").lower()
        return {
            key: canonical(item)
            for key, item in sorted(value.items())
            if key not in NOISE_KEYS
        }
    if isinstance(value, list):
        result = [canonical(item) for item in value]
        return sorted(result, key=lambda item: json.dumps(item, sort_keys=True)) if field == "Regions" else result
    if isinstance(value, str) and ("\\" in value or "/" in value):
        return value.replace("/", "\\").lower()
    return value


def selected_records(path: str, record_type: str, fields: tuple[str, ...]) -> list[dict]:
    executable_hash = sha256(RECORD_CLI)
    plugin_hash = sha256(path)
    signature = hashlib.sha256(
        (record_type + "\0" + ",".join(fields)).encode("utf-8")
    ).hexdigest()
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, f"{executable_hash}-{plugin_hash}-{signature}.json")
    if os.path.exists(cached):
        with open(cached, encoding="utf-8") as stream:
            return json.load(stream)
    process = subprocess.run(
        [
            RECORD_CLI,
            "record-selected-fields-by-type",
            path,
            record_type,
            ",".join(fields),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if process.returncode:
        raise RuntimeError((process.stderr or process.stdout)[-1000:])
    rows = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    temporary = cached + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(rows, stream, ensure_ascii=False)
    os.replace(temporary, cached)
    return rows


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    record_type = sys.argv[1]
    anchor = sys.argv[2]
    output_dir = os.path.abspath(sys.argv[3]) if len(sys.argv) == 4 else DEFAULT_OUTPUT
    fields = FIELDS_BY_TYPE.get(record_type)
    if not fields:
        print(f"Unsupported semantic record type: {record_type}", file=sys.stderr)
        return 2

    index = order.build_index()
    active = [
        line[1:]
        for line in open(
            os.path.join(order.PROFILE, "plugins.txt"), encoding="utf-8"
        ).read().splitlines()
        if line.startswith("*")
    ]
    load_position = {name.lower(): position for position, name in enumerate(active)}
    raw_chains: dict[str, list[dict]] = collections.defaultdict(list)
    failures: list[dict] = []
    for number, plugin in enumerate(active, 1):
        path = index.get(plugin.lower())
        if not path:
            continue
        try:
            rows = record_conflicts.inventory(path)
        except Exception as error:
            failures.append({"plugin": plugin, "stage": "inventory", "error": str(error)})
            continue
        for row in rows:
            if row.get("type") != record_type or not row.get("formKey"):
                continue
            raw_chains[row["formKey"]].append(
                {
                    "plugin": plugin,
                    "loadPosition": load_position[plugin.lower()],
                    "editorId": row.get("editorId"),
                }
            )

    targets = {}
    participants: set[str] = set()
    for form_key, entries in raw_chains.items():
        entries.sort(key=lambda item: item["loadPosition"])
        anchor_positions = [
            position
            for position, item in enumerate(entries)
            if item["plugin"].lower() == anchor.lower()
        ]
        if not anchor_positions or anchor_positions[-1] == len(entries) - 1:
            continue
        start = anchor_positions[-1]
        targets[form_key] = entries[start:]
        participants.update(item["plugin"] for item in entries[start:])

    rows_by_plugin: dict[str, dict[str, dict]] = {}
    for number, plugin in enumerate(sorted(participants, key=lambda name: load_position[name.lower()]), 1):
        path = index.get(plugin.lower())
        if not path:
            continue
        try:
            rows = selected_records(path, record_type, fields)
        except Exception as error:
            failures.append({"plugin": plugin, "stage": "fields", "error": str(error)})
            print(f"[{number}/{len(participants)}] FAIL {plugin}: {error}", flush=True)
            continue
        rows_by_plugin[plugin.lower()] = {row["formKey"]: row for row in rows}
        print(f"[{number}/{len(participants)}] {plugin}: {len(rows)} {record_type}", flush=True)

    records = []
    divergences = []
    for form_key, chain in targets.items():
        enriched = []
        for entry in chain:
            row = rows_by_plugin.get(entry["plugin"].lower(), {}).get(form_key)
            if not row:
                failures.append(
                    {
                        "plugin": entry["plugin"],
                        "stage": "join",
                        "error": f"missing {record_type} {form_key}",
                    }
                )
                continue
            source = row.get("fields", {})
            enriched.append(
                {
                    **entry,
                    "fields": {field: canonical(source.get(field), field) for field in fields},
                }
            )
        if len(enriched) < 2:
            continue
        anchor_entry = enriched[0]
        winner = enriched[-1]
        differences = []
        for field in fields:
            anchor_value = anchor_entry["fields"][field]
            final_value = winner["fields"][field]
            if anchor_value == final_value:
                continue
            difference = {
                "field": field,
                "anchorValue": anchor_value,
                "finalValue": final_value,
            }
            differences.append(difference)
            divergences.append(
                {
                    "formKey": form_key,
                    "editorId": winner.get("editorId") or anchor_entry.get("editorId"),
                    "field": field,
                    "anchor": anchor,
                    "winner": winner["plugin"],
                    **difference,
                }
            )
        records.append(
            {
                "formKey": form_key,
                "editorId": winner.get("editorId") or anchor_entry.get("editorId"),
                "chain": [item["plugin"] for item in enriched],
                "winner": winner["plugin"],
                "differences": differences,
            }
        )

    records.sort(key=lambda item: (item["editorId"] or "", item["formKey"]))
    divergences.sort(key=lambda item: (item["editorId"] or "", item["field"]))
    captured = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", anchor.lower()).strip("-")
    stem = f"{record_type.lower()}-after-{slug}"
    report = {
        "schemaVersion": 1,
        "capturedUtc": captured,
        "profile": "Default",
        "recordType": record_type,
        "anchor": anchor,
        "candidateChains": len(targets),
        "semanticDivergences": len(divergences),
        "divergences": divergences,
        "records": records,
        "failures": failures,
    }
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, stem + ".json")
    markdown_path = os.path.join(output_dir, stem + ".md")
    temporary = json_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    os.replace(temporary, json_path)

    lines = [
        f"# {record_type} fields after {anchor}",
        "",
        f"Captured: `{captured}`",
        "",
        f"- Candidate chains: {len(targets)}",
        f"- Final semantic field differences: {len(divergences)}",
        f"- Read/join failures: {len(failures)}",
        "",
    ]
    for item in divergences:
        lines.append(
            f'- `{item["editorId"] or item["formKey"]}` `{item["field"]}`: '
            f'{item["winner"]} differs from {anchor}'
        )
    lines.append("")
    temporary = markdown_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))
    os.replace(temporary, markdown_path)
    print(json.dumps({
        "ok": not failures,
        "json": json_path,
        "markdown": markdown_path,
        "chains": len(targets),
        "divergences": len(divergences),
        "failures": len(failures),
    }))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
