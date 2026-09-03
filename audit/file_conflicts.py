"""Audit MO2 file-provider conflicts without changing the profile.

The report keeps every order-sensitive code/config collision, while aggregating
large mesh/texture replacement sets by provider pair. The first enabled mod in
MO2's modlist.txt is the effective provider because that file is stored in
descending mod priority.

Run: py -3 audit/file_conflicts.py [output-directory]
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import os
import sys


INSTANCE = r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se"
PROFILE = os.path.join(INSTANCE, "profiles", "Default")
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "records"
)
CRITICAL = {"native", "papyrus", "behavior", "plugin", "config", "interface"}


def category(path: str) -> str:
    extension = os.path.splitext(path)[1].lower()
    if extension in {".dll", ".exe"}:
        return "native"
    if extension == ".pex":
        return "papyrus"
    if extension == ".hkx":
        return "behavior"
    if extension in {".esp", ".esm", ".esl"}:
        return "plugin"
    if extension in {".ini", ".toml", ".json", ".yaml", ".yml"}:
        return "config"
    if extension == ".swf":
        return "interface"
    if extension == ".nif":
        return "mesh"
    if extension in {".dds", ".tga", ".png"}:
        return "texture"
    if extension in {".xwm", ".wav", ".fuz", ".lip"}:
        return "audio"
    return "other"


def digest(path: str) -> str:
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def enabled_mods() -> list[str]:
    lines = open(
        os.path.join(PROFILE, "modlist.txt"), encoding="utf-8", errors="replace"
    ).read().splitlines()
    return [line[1:] for line in lines if line.startswith("+")]


def main() -> int:
    output_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    providers: dict[str, list[dict]] = collections.defaultdict(list)
    mods = enabled_mods()
    file_count = 0

    for priority, mod in enumerate(mods):
        root = os.path.join(INSTANCE, "mods", mod)
        if not os.path.isdir(root):
            continue
        for current, directories, files in os.walk(root):
            directories.sort(key=str.lower)
            for name in sorted(files, key=str.lower):
                absolute = os.path.join(current, name)
                relative = os.path.relpath(absolute, root).replace("\\", "/")
                # MO2 bookkeeping lives beside a mod's Data-root payload but is
                # not exposed through the game VFS.
                if "/" not in relative and relative.lower() in {
                    "meta.ini",
                    "_install_choices.txt",
                }:
                    continue
                key = relative.lower()
                providers[key].append(
                    {
                        "mod": mod,
                        "relativePath": relative,
                        "absolutePath": absolute,
                        "modOrder": priority,
                        "bytes": os.path.getsize(absolute),
                    }
                )
                file_count += 1

    collisions = {path: rows for path, rows in providers.items() if len(rows) > 1}
    category_counts: collections.Counter[str] = collections.Counter()
    pair_counts: dict[tuple[str, str, str], int] = collections.Counter()
    critical = []

    for rows in collisions.values():
        kind = category(rows[0]["relativePath"])
        category_counts[kind] += 1
        winner = rows[0]["mod"]
        for loser in rows[1:]:
            pair_counts[(kind, winner, loser["mod"])] += 1
        if kind not in CRITICAL:
            continue
        public_rows = []
        hashes = []
        for row in rows:
            sha256 = digest(row["absolutePath"])
            hashes.append(sha256)
            public_rows.append(
                {
                    "mod": row["mod"],
                    "relativePath": row["relativePath"],
                    "modOrder": row["modOrder"],
                    "bytes": row["bytes"],
                    "sha256": sha256,
                }
            )
        critical.append(
            {
                "path": rows[0]["relativePath"],
                "category": kind,
                "winner": winner,
                "providers": public_rows,
                "byteIdentical": len(set(hashes)) == 1,
            }
        )

    critical.sort(key=lambda item: (item["category"], item["path"].lower()))
    pairs = [
        {"category": key[0], "winner": key[1], "overridden": key[2], "files": count}
        for key, count in sorted(pair_counts.items(), key=lambda item: -item[1])
    ]
    captured = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "schemaVersion": 1,
        "capturedUtc": captured,
        "profile": "Default",
        "enabledManagedMods": len(mods),
        "filesScanned": file_count,
        "conflictingPaths": len(collisions),
        "categories": dict(category_counts.most_common()),
        "criticalConflicts": critical,
        "providerPairs": pairs,
        "interpretation": (
            "The first provider is the effective MO2 winner. A collision is not automatically "
            "a defect; update overlays and compatibility packages intentionally replace files."
        ),
    }

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "active-file-conflicts.json")
    markdown_path = os.path.join(output_dir, "active-file-conflicts.md")
    temporary = json_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    os.replace(temporary, json_path)

    lines = [
        "# Active file-conflict inventory",
        "",
        f"Captured: `{captured}`",
        "",
        f"- Enabled managed mods: {len(mods)}",
        f"- Files scanned: {file_count}",
        f"- Conflicting paths: {len(collisions)}",
        f"- Order-sensitive code/config paths: {len(critical)}",
        "",
        "The first provider is the effective MO2 winner. Collisions are review candidates, not automatic defects.",
        "",
        "## Collision categories",
        "",
    ]
    lines += [f"- {name}: {count}" for name, count in category_counts.most_common()]
    lines += ["", "## Order-sensitive collisions", ""]
    for item in critical:
        chain = " -> ".join(row["mod"] for row in item["providers"])
        identical = " (byte-identical)" if item["byteIdentical"] else ""
        lines.append(
            f'- `{item["category"]}` `{item["path"]}`: {chain} '
            f'(**winner:** {item["winner"]}){identical}'
        )
    lines += ["", "## Highest-volume provider pairs", ""]
    lines += [
        f'- `{item["category"]}` {item["winner"]} over {item["overridden"]}: {item["files"]} files'
        for item in pairs[:100]
    ]
    lines.append("")
    temporary = markdown_path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))
    os.replace(temporary, markdown_path)

    print(
        json.dumps(
            {
                "ok": True,
                "json": json_path,
                "markdown": markdown_path,
                "files": file_count,
                "collisions": len(collisions),
                "critical": len(critical),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
