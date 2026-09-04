"""Create a machine-readable verification contract for one build change.

This does not launch Skyrim.  It freezes the build identity and says which
stages the runtime harness must satisfy, including whether a fresh character
and repeated save/load cycles are mandatory.  See docs/TESTING_POLICY.md.

Examples:

    py -3 audit/verification_plan.py --kind plugin --issue 102 --summary "ledger repair"
    py -3 audit/verification_plan.py --kind native --crash-fix --out records/test-plans/cdf.json
    py -3 audit/verification_plan.py --selftest
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import pathlib
import secrets


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
LEDGER = REPO / "records" / "installed-mods.json"
WATCHLIST = REPO / "audit" / "watched_configs.json"
DOCUMENTS = pathlib.Path(os.environ.get("USERPROFILE", "")) / "Documents" / "My Games" / "Skyrim Special Edition"

KINDS = {
    "asset": {"risk": 1, "roundTrip": False, "cycles": 1, "soak": False},
    "config": {"risk": 2, "roundTrip": True, "cycles": 1, "soak": False},
    "plugin": {"risk": 3, "roundTrip": True, "cycles": 1, "soak": False},
    "generated": {"risk": 3, "roundTrip": True, "cycles": 1, "soak": False},
    "worldspace": {"risk": 4, "roundTrip": True, "cycles": 2, "soak": True},
    "script": {"risk": 4, "roundTrip": True, "cycles": 3, "soak": True},
    "native": {"risk": 5, "roundTrip": True, "cycles": 3, "soak": True},
    "removal": {"risk": 5, "roundTrip": True, "cycles": 3, "soak": True},
}


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def build_fingerprint(
    instance: pathlib.Path = INSTANCE,
    profile: str = PROFILE,
    ledger: pathlib.Path = LEDGER,
) -> dict:
    """Hash durable authorities and runtime-bearing files, not whole textures.

    Vendor archive hashes and owned-output hashes live in the ledger/source
    records.  Hashing those records plus live plugins/DLLs detects the changes
    that can affect initialization or save state without rereading the entire
    texture tree for every test.
    """
    instance = pathlib.Path(instance)
    profile_dir = instance / "profiles" / profile
    inputs: list[dict] = []
    seen: set[str] = set()

    def add(path: pathlib.Path, role: str) -> None:
        identity = os.path.normcase(os.path.abspath(path))
        if path.is_file() and identity not in seen:
            seen.add(identity)
            inputs.append({
                "role": role,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    add(pathlib.Path(ledger), "ledger")
    add(WATCHLIST, "watch-spec")
    for path in sorted((REPO / "records" / "source-builds").glob("*.json"),
                       key=lambda p: p.name.casefold()):
        add(path, "owned-source-build")
    for name in (
        "modlist.txt", "plugins.txt", "loadorder.txt", "lockedorder.txt",
        "settings.ini", "skyrim.ini", "skyrimprefs.ini", "skyrimcustom.ini",
    ):
        add(profile_dir / name, "profile")

    enabled: list[str] = []
    modlist = profile_dir / "modlist.txt"
    if modlist.exists():
        enabled = [
            line[1:].strip() for line in modlist.read_text(
                encoding="utf-8-sig", errors="replace"
            ).splitlines()
            if line.startswith("+") and line[1:].strip()
        ]

    # A mod priority is represented by order in modlist. Hash every live copy,
    # not only the winner: the order file is already an input, and this makes a
    # shadowed DLL/plugin/script change visible before it unexpectedly becomes
    # live. Vendor archives and owned output receipts cover bulky asset trees.
    suffixes = {".esm", ".esp", ".esl", ".dll"}
    for mod_name in enabled:
        root = instance / "mods" / mod_name
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
            if path.is_file() and path.suffix.casefold() in suffixes:
                add(path, f"runtime:{mod_name}")
        dll_dir = root / "SKSE" / "Plugins"
        if dll_dir.is_dir():
            for path in sorted(dll_dir.glob("*.dll"), key=lambda p: p.name.casefold()):
                add(path, f"runtime:{mod_name}")
        scripts_dir = root / "scripts"
        if scripts_dir.is_dir():
            for path in sorted(scripts_dir.rglob("*.pex"), key=lambda p: str(p).casefold()):
                add(path, f"runtime-script:{mod_name}")

    # Runtime configs can change behavior without changing a plugin or ledger
    # row. Expand the same declarative watch list used by preflight_extra.py,
    # excluding configs under parked mods.
    enabled_keys = {name.casefold() for name in enabled}
    if WATCHLIST.is_file():
        spec = json.loads(WATCHLIST.read_text(encoding="utf-8-sig"))
        for entry in spec.get("watch", []):
            pattern = entry.get("path") if isinstance(entry, dict) else entry
            if not pattern:
                continue
            enabled_only = entry.get("enabledModsOnly", True) if isinstance(entry, dict) else True
            expanded = str(pattern).replace("~docs~", str(DOCUMENTS))
            if not os.path.isabs(expanded):
                expanded = str(instance / expanded)
            for raw in sorted(glob.glob(expanded, recursive=True), key=str.casefold):
                path = pathlib.Path(raw)
                if not path.is_file():
                    continue
                try:
                    rel = path.resolve().relative_to(instance.resolve())
                except ValueError:
                    rel = None
                if enabled_only and rel and len(rel.parts) > 2 and rel.parts[0].casefold() == "mods":
                    if rel.parts[1].casefold() not in enabled_keys:
                        continue
                add(path, "watched-config")

    canonical = "\n".join(
        f"{row['role']}\t{row['path'].casefold()}\t{row['bytes']}\t{row['sha256']}"
        for row in sorted(inputs, key=lambda row: (row["path"].casefold(), row["role"]))
    )
    return {
        "algorithm": "sha256(authority-runtime-scripts-watched-config-v2)",
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
        "inputs": inputs,
    }


def make_plan(kinds: list[str], summary: str, issue: str | None,
              crash_fix: bool, fingerprint: dict | None = None) -> dict:
    if not kinds:
        raise ValueError("at least one change kind is required")
    unknown = sorted(set(kinds) - set(KINDS))
    if unknown:
        raise ValueError("unknown change kind(s): " + ", ".join(unknown))
    risk = max(KINDS[k]["risk"] for k in kinds)
    cycles = max(KINDS[k]["cycles"] for k in kinds)
    if crash_fix:
        cycles = max(cycles, 10)
    round_trip = any(KINDS[k]["roundTrip"] for k in kinds)
    soak = any(KINDS[k]["soak"] for k in kinds) or crash_fix
    stamp = dt.datetime.now(dt.timezone.utc)
    test_id = f"SVT-{stamp:%Y%m%dT%H%M%SZ}-{secrets.token_hex(3).upper()}"
    required = ["V0-static", "V1-boot", "V2-fresh-start", "V3-feature-probes", "V5-log-diff"]
    if round_trip:
        required.insert(4, "V4-save-load-round-trip")
    if soak:
        required.append("V6-soak")
    required.append("V7-human-play")
    return {
        "schemaVersion": 1,
        "testId": test_id,
        "createdUtc": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "issue": issue,
        "changeKinds": sorted(set(kinds)),
        "riskClass": risk,
        "freshCharacter": {
            "required": True,
            "method": "main-menu New Game flow; never clone/autoload an older clean save",
            "reuseAcrossBuildFingerprints": False,
        },
        "cyclesRequired": cycles,
        "stagesRequired": required,
        "campaignSave": {
            "required": False,
            "allowedAfterDisposablePassOnly": True,
            "purpose": "explicit migration test, never technical source of truth",
        },
        "buildFingerprint": fingerprint,
        "status": "planned",
        "results": {},
    }


def render(plan: dict) -> str:
    lines = [
        f"# Verification plan {plan['testId']}", "",
        f"- change: {plan['summary'] or '(not supplied)'}",
        f"- kinds: {', '.join(plan['changeKinds'])}",
        f"- risk class: {plan['riskClass']}",
        f"- fresh character: required (new main-menu flow; never reused)",
        f"- complete cycles: {plan['cyclesRequired']}",
        f"- build fingerprint: {(plan.get('buildFingerprint') or {}).get('sha256', 'not captured')}",
        "", "## Required stages", "",
    ]
    lines += [f"- [ ] {stage}" for stage in plan["stagesRequired"]]
    return "\n".join(lines) + "\n"


def selftest() -> int:
    asset = make_plan(["asset"], "asset", None, False, None)
    assert asset["freshCharacter"]["required"]
    assert "V4-save-load-round-trip" not in asset["stagesRequired"]
    native = make_plan(["native"], "native", "1", False, None)
    assert native["cyclesRequired"] == 3
    assert "V4-save-load-round-trip" in native["stagesRequired"]
    crash = make_plan(["native", "script"], "crash", "2", True, None)
    assert crash["cyclesRequired"] == 10 and "V6-soak" in crash["stagesRequired"]
    print("verification_plan selftest PASS (5 assertions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", action="append", choices=sorted(KINDS))
    parser.add_argument("--summary", default="")
    parser.add_argument("--issue")
    parser.add_argument("--crash-fix", action="store_true")
    parser.add_argument("--no-fingerprint", action="store_true")
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--ledger", type=pathlib.Path, default=LEDGER)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.kind:
        parser.error("at least one --kind is required")
    fingerprint = None if args.no_fingerprint else build_fingerprint(
        args.instance, args.profile, args.ledger
    )
    plan = make_plan(args.kind, args.summary, args.issue, args.crash_fix, fingerprint)
    output = json.dumps(plan, indent=2) + "\n" if args.json or args.out else render(plan)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
