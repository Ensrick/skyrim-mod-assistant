"""Compare semantic WRLD fields across the active MO2 override chains.

This supplements the broad record inventory with field-level evidence. It does
not edit plugins. Consecutive bookkeeping-only differences are ignored, while
late A -> B -> A field reversions are called out for compatibility review.

Run: py -3 audit/worldspace_conflicts.py [output-directory]
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import os
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
    "worldspace-fields",
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records"
)

# These fields affect world behavior or presentation. Mutagen's record wrapper
# also exposes file-version and subgroup bookkeeping that does not represent a
# gameplay conflict and is intentionally omitted here.
SEMANTIC_FIELDS = (
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
    "OffsetData",
    "Parent",
    "Water",
    "WaterEnvironmentMap",
    "WaterNoiseTexture",
    "WorldMapCellOffset",
    "WorldMapOffsetScale",
)
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
CORE_MASTER_ORDER = {
    "skyrim.esm": -10000,
    "update.esm": -9999,
    "dawnguard.esm": -9998,
    "hearthfires.esm": -9997,
    "dragonborn.esm": -9996,
}


def sha256(path: str) -> str:
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value):
    """Reduce Mutagen reflection output to stable, human-relevant values."""
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
        return [canonical(item) for item in value]
    if isinstance(value, str) and ("\\" in value or "/" in value):
        return value.replace("/", "\\").lower()
    return value


def worldspaces(path: str) -> list[dict]:
    executable_hash = sha256(RECORD_CLI)
    plugin_hash = sha256(path)
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, f"{executable_hash}-{plugin_hash}.json")
    if os.path.exists(cached):
        with open(cached, encoding="utf-8") as stream:
            return json.load(stream)
    process = subprocess.run(
        [RECORD_CLI, "record-fields-by-type", path, "Worldspace"],
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
    output_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    index = order.build_index()
    active = [
        line[1:]
        for line in open(
            os.path.join(order.PROFILE, "plugins.txt"), encoding="utf-8"
        ).read().splitlines()
        if line.startswith("*")
    ]
    active_position = {name.lower(): position for position, name in enumerate(active)}

    # The inexpensive record inventory is cached. Use it to avoid opening the
    # many active plugins that contain no WRLD records with the richer reader.
    candidates: list[str] = []
    source_plugins: set[str] = set()
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
        world_rows = [row for row in rows if row.get("type") == "Worldspace"]
        if not world_rows:
            continue
        candidates.append(plugin)
        source_plugins.update(
            row["formKey"].split(":", 1)[1]
            for row in world_rows
            if ":" in row.get("formKey", "")
        )
        print(f"[{number}/{len(active)}] candidate {plugin}: {len(world_rows)} WRLD", flush=True)

    # Include the source master when it is implicit (for example Skyrim.esm),
    # so A -> B -> A checks have the actual baseline rather than the first mod.
    names = list(candidates)
    for master in CORE_MASTER_ORDER:
        if master not in {name.lower() for name in names} and master in index:
            names.insert(0, os.path.basename(index[master]))
    for source in sorted(source_plugins, key=str.lower):
        if source.lower() not in {name.lower() for name in names} and source.lower() in index:
            names.insert(0, source)

    chains: dict[str, list[dict]] = collections.defaultdict(list)
    for number, plugin in enumerate(names, 1):
        path = index.get(plugin.lower())
        if not path:
            continue
        try:
            rows = worldspaces(path)
        except Exception as error:
            failures.append({"plugin": plugin, "stage": "fields", "error": str(error)})
            print(f"[{number}/{len(names)}] FAIL {plugin}: {error}", flush=True)
            continue
        position = active_position.get(
            plugin.lower(), CORE_MASTER_ORDER.get(plugin.lower(), -9000 + number)
        )
        for row in rows:
            fields = row.get("fields", {})
            chains[row["formKey"]].append(
                {
                    "plugin": plugin,
                    "loadPosition": position,
                    "editorId": row.get("editorId"),
                    "fields": {
                        field: canonical(fields.get(field)) for field in SEMANTIC_FIELDS
                    },
                }
            )
        print(f"[{number}/{len(names)}] {plugin}: {len(rows)} WRLD", flush=True)

    reports = []
    reversions = []
    for form_key, entries in chains.items():
        entries.sort(key=lambda item: item["loadPosition"])
        if len(entries) < 2:
            continue
        changes = []
        for position in range(1, len(entries)):
            previous = entries[position - 1]
            current = entries[position]
            for field in SEMANTIC_FIELDS:
                before = previous["fields"][field]
                after = current["fields"][field]
                if before == after:
                    continue
                changes.append(
                    {
                        "field": field,
                        "plugin": current["plugin"],
                        "previousPlugin": previous["plugin"],
                        "before": before,
                        "after": after,
                    }
                )

        final = entries[-1]
        for field in SEMANTIC_FIELDS:
            values = []
            for entry in entries:
                value = entry["fields"][field]
                if not values or values[-1]["value"] != value:
                    values.append({"plugin": entry["plugin"], "value": value})
            if len(values) < 3 or values[-1]["value"] not in [item["value"] for item in values[:-2]]:
                continue
            restored = next(
                item for item in reversed(values[:-2]) if item["value"] == values[-1]["value"]
            )
            reversions.append(
                {
                    "formKey": form_key,
                    "editorId": final["editorId"],
                    "field": field,
                    "winner": final["plugin"],
                    "restoresValueFrom": restored["plugin"],
                    "discardsValueFrom": values[-2]["plugin"],
                    "restoredValue": values[-1]["value"],
                    "discardedValue": values[-2]["value"],
                }
            )
        reports.append(
            {
                "formKey": form_key,
                "editorId": final["editorId"],
                "winner": final["plugin"],
                "chain": [entry["plugin"] for entry in entries],
                "changes": changes,
            }
        )

    reports.sort(key=lambda item: (item["editorId"] or "", item["formKey"]))
    reversions.sort(key=lambda item: (item["editorId"] or "", item["field"]))
    captured = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "schemaVersion": 1,
        "capturedUtc": captured,
        "profile": "Default",
        "worldspaceChains": len(reports),
        "finalReversionCandidates": len(reversions),
        "reversions": reversions,
        "chains": reports,
        "failures": failures,
        "interpretation": (
            "A final A -> B -> A field pattern is a focused compatibility candidate, not "
            "automatic proof of a defect. File-version and subgroup bookkeeping are excluded."
        ),
    }

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "active-worldspace-conflicts.json")
    markdown_path = os.path.join(output_dir, "active-worldspace-conflicts.md")
    temporary = json_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    os.replace(temporary, json_path)

    lines = [
        "# Active worldspace semantic audit",
        "",
        f"Captured: `{captured}`",
        "",
        f"- Shared WRLD chains: {len(reports)}",
        f"- Final A -> B -> A field candidates: {len(reversions)}",
        f"- Read failures: {len(failures)}",
        "",
        "A reversion is a focused review candidate, not automatic proof of a defect. File-version and subgroup bookkeeping are excluded.",
        "",
        "## Final reversion candidates",
        "",
    ]
    for item in reversions:
        lines.append(
            f'- `{item["editorId"] or item["formKey"]}` `{item["field"]}`: '
            f'{item["winner"]} restores {item["restoresValueFrom"]} and discards '
            f'{item["discardsValueFrom"]}'
        )
    if failures:
        lines += ["", "## Read failures", ""]
        lines += [
            f'- `{item["plugin"]}` ({item["stage"]}): {item["error"]}'
            for item in failures
        ]
    lines.append("")
    temporary = markdown_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))
    os.replace(temporary, markdown_path)

    print(json.dumps({
        "ok": not failures,
        "json": json_path,
        "markdown": markdown_path,
        "chains": len(reports),
        "reversions": len(reversions),
        "failures": len(failures),
    }))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
