"""Inventory active plugin override chains without editing vendor files.

This is the decision-stage companion to xEdit.  It resolves every active
plugin through MO2's effective file tree, inventories records with the pinned
source-built Mutagen CLI, and reports FormKeys written by two or more managed
plugins in load-order sequence.  A shared FormKey is a review candidate, not
automatically an error: upstream compatibility patches intentionally create
many such chains.

Run: py -3 audit/record_conflicts.py [output-directory]
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import itertools
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_order as order


RECORD_CLI = (
    r"C:\Users\danjo\source\repos\skyrim-tools-builds"
    r"\skyrim-record-cli-1f3c8d9\skyrim-record-cli.exe"
)
CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")),
    "SkyrimModAssistant",
    "record-inventories",
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records"
)

# NAVI (Navigation Mesh Info Map) records are file-local indexes. xEdit's
# documentation explicitly warns that they are not ordinary override records,
# so a matching FormID in two plugins is not a winner/loser conflict.
FILE_LOCAL_RECORD_TYPES = {"NavigationMeshInfoMap"}


def owner_of(path: str) -> str:
    marker = os.path.normcase(os.path.join(order.INSTANCE, "mods") + os.sep)
    normal = os.path.normcase(os.path.abspath(path))
    if normal.startswith(marker):
        return os.path.relpath(path, os.path.join(order.INSTANCE, "mods")).split(os.sep)[0]
    return "Game Data"


def inventory(path: str) -> list[dict]:
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, sha + ".json")
    if os.path.exists(cached):
        return json.load(open(cached, encoding="utf-8"))
    process = subprocess.run(
        [RECORD_CLI, "records", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if process.returncode:
        raise RuntimeError((process.stderr or process.stdout)[-500:])
    rows = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    temporary = cached + ".tmp"
    json.dump(rows, open(temporary, "w", encoding="utf-8"), ensure_ascii=False)
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
    load_position = {name.lower(): position for position, name in enumerate(active)}
    providers = []
    failures = []
    file_local_records_skipped: collections.Counter[str] = collections.Counter()
    chains: dict[str, list[dict]] = collections.defaultdict(list)

    for number, plugin in enumerate(active, 1):
        path = index.get(plugin.lower())
        if not path or owner_of(path) == "Game Data":
            continue
        try:
            rows = inventory(path)
        except Exception as error:
            failures.append({"plugin": plugin, "error": str(error)})
            print(f"[{number}/{len(active)}] FAIL {plugin}: {error}", flush=True)
            continue
        owner = owner_of(path)
        providers.append(
            {
                "plugin": plugin,
                "owner": owner,
                "path": path,
                "loadPosition": load_position[plugin.lower()],
                "records": len(rows),
            }
        )
        for row in rows:
            record_type = row.get("type")
            if record_type in FILE_LOCAL_RECORD_TYPES:
                file_local_records_skipped[record_type] += 1
                continue
            form_key = row.get("formKey")
            if not form_key:
                continue
            chains[form_key].append(
                {
                    "plugin": plugin,
                    "owner": owner,
                    "loadPosition": load_position[plugin.lower()],
                    "type": row.get("type"),
                    "editorId": row.get("editorId"),
                }
            )
        print(f"[{number}/{len(active)}] {plugin}: {len(rows)} records", flush=True)

    conflicts = []
    pair_counts: dict[tuple[str, str], int] = collections.Counter()
    pair_types: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    for form_key, entries in chains.items():
        entries.sort(key=lambda item: item["loadPosition"])
        distinct = []
        seen = set()
        for entry in entries:
            if entry["plugin"].lower() in seen:
                continue
            seen.add(entry["plugin"].lower())
            distinct.append(entry)
        if len(distinct) < 2:
            continue
        conflicts.append(
            {
                "formKey": form_key,
                "type": next((entry["type"] for entry in reversed(distinct) if entry["type"]), None),
                "editorId": next(
                    (entry["editorId"] for entry in reversed(distinct) if entry["editorId"]), None
                ),
                "chain": distinct,
                "winner": distinct[-1]["plugin"],
            }
        )
        for left, right in itertools.combinations(distinct, 2):
            pair = (left["plugin"], right["plugin"])
            pair_counts[pair] += 1
            pair_types[pair][left.get("type") or right.get("type") or "Unknown"] += 1

    conflicts.sort(key=lambda item: (item["type"] or "", item["formKey"]))
    pairs = [
        {
            "earlier": pair[0],
            "later": pair[1],
            "records": count,
            "types": dict(pair_types[pair].most_common()),
        }
        for pair, count in pair_counts.most_common()
    ]
    captured = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "schemaVersion": 1,
        "capturedUtc": captured,
        "profile": "Default",
        "activePluginCount": len(active),
        "managedPluginCount": len(providers),
        "candidateOverrideChains": len(conflicts),
        "fileLocalRecordsSkipped": dict(file_local_records_skipped),
        "providers": providers,
        "pairs": pairs,
        "chains": conflicts,
        "failures": failures,
        "interpretation": (
            "Shared FormKeys are review candidates, not automatic errors. "
            "File-local NAVI indexes are excluded because they do not use ordinary "
            "override/winner semantics. "
            "Vendor plugins remain immutable; approved resolutions belong in a separate ESL patch."
        ),
    }

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "active-record-conflicts.json")
    markdown_path = os.path.join(output_dir, "active-record-conflicts.md")
    temporary = json_path + ".tmp"
    json.dump(report, open(temporary, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.replace(temporary, json_path)

    lines = [
        "# Active record-conflict inventory",
        "",
        f"Captured: `{captured}`",
        "",
        f"- Active plugins: {len(active)}",
        f"- Managed plugins inventoried: {len(providers)}",
        f"- Shared FormKey chains: {len(conflicts)}",
        "- File-local records excluded: "
        + (", ".join(f"{name} {count}" for name, count in file_local_records_skipped.items()) or "none"),
        f"- Inventory failures: {len(failures)}",
        "",
        "A shared record is a review candidate, not automatically a defect. File-local NAVI indexes are excluded because matching FormIDs in separate plugins do not represent an override chain. Vendor mods are immutable; approved resolutions belong in our own ESL-flagged patch.",
        "",
        "## Highest-overlap plugin pairs",
        "",
        "| Earlier plugin | Later plugin | Shared records | Leading record types |",
        "|---|---|---:|---|",
    ]
    for pair in pairs[:80]:
        types = ", ".join(f"{name} {count}" for name, count in list(pair["types"].items())[:6])
        lines.append(
            f'| {pair["earlier"]} | {pair["later"]} | {pair["records"]} | {types} |'
        )
    lines += ["", "## Sample winning chains", ""]
    for item in conflicts[:160]:
        chain = " → ".join(entry["plugin"] for entry in item["chain"])
        identity = item.get("editorId") or item["formKey"]
        lines.append(
            f'- `{item.get("type") or "Unknown"}` `{identity}`: {chain} '
            f'(**winner:** {item["winner"]})'
        )
    if failures:
        lines += ["", "## Inventory failures", ""]
        lines += [f'- `{item["plugin"]}`: {item["error"]}' for item in failures]
    lines.append("")
    temporary = markdown_path + ".tmp"
    open(temporary, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    os.replace(temporary, markdown_path)
    print(
        json.dumps(
            {
                "ok": not failures,
                "json": json_path,
                "markdown": markdown_path,
                "chains": len(conflicts),
                "failures": len(failures),
            }
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
