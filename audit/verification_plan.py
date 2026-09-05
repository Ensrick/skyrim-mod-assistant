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
import copy
import datetime as dt
import glob
import hashlib
import json
import os
import pathlib
import re
import secrets
import tempfile


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
LEDGER = REPO / "records" / "installed-mods.json"
WATCHLIST = REPO / "audit" / "watched_configs.json"
DOCUMENTS = pathlib.Path(os.environ.get("USERPROFILE", "")) / "Documents" / "My Games" / "Skyrim Special Edition"
GAME_ROOT = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition"
)
CONTENT_CATALOG = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / \
    "Skyrim Special Edition" / "ContentCatalog.txt"


_VDF_TOKEN = re.compile(r'"((?:\\.|[^"\\])*)"|([{}])')


def _tokenize_vdf(text):
    tokens = []
    cursor = 0
    for match in _VDF_TOKEN.finditer(text):
        if text[cursor:match.start()].strip():
            raise ValueError("unexpected text in Steam app manifest")
        tokens.append(
            ("text", match.group(1)) if match.group(1) is not None
            else ("brace", match.group(2))
        )
        cursor = match.end()
    if text[cursor:].strip():
        raise ValueError("unexpected trailing text in Steam app manifest")
    return tokens


def _parse_vdf_object(tokens, index=0, nested=False):
    """Parse the quoted-string/braces subset used by Steam app manifests."""
    result = {}
    while index < len(tokens):
        kind, value = tokens[index]
        if kind == "brace" and value == "}":
            if not nested:
                raise ValueError("unexpected closing brace in Steam app manifest")
            return result, index + 1
        if kind != "text":
            raise ValueError("expected a quoted key in Steam app manifest")
        key = value
        index += 1
        if index >= len(tokens):
            raise ValueError(f"Steam app manifest key has no value: {key}")
        next_kind, next_value = tokens[index]
        if next_kind == "brace" and next_value == "{":
            child, index = _parse_vdf_object(tokens, index + 1, nested=True)
        elif next_kind == "text":
            child = next_value
            index += 1
        else:
            raise ValueError(f"Steam app manifest key has invalid value: {key}")
        result[key] = child
    if nested:
        raise ValueError("unterminated object in Steam app manifest")
    return result, index


def _vdf_field(mapping, name):
    if not isinstance(mapping, dict):
        return None
    wanted = name.casefold()
    return next((value for key, value in mapping.items()
                 if str(key).casefold() == wanted), None)


def _canonical_vdf(value):
    if not isinstance(value, dict):
        return str(value)
    return {
        str(key).casefold(): _canonical_vdf(child)
        for key, child in sorted(value.items(), key=lambda item: str(item[0]).casefold())
    }


def steam_app_manifest_build_payload(path: pathlib.Path) -> bytes:
    """Return stable, build-relevant Steam manifest state.

    Raw appmanifest bytes also contain session state such as ``LastPlayed`` and
    ``StateFlags``. Steam can change those while running the very verification
    launch whose fingerprint we are trying to preserve. The build ID and depot
    manifests identify installed content; language/beta selection identifies
    the content variant.
    """
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8-sig")
    tokens = _tokenize_vdf(text)
    parsed, consumed = _parse_vdf_object(tokens)
    if consumed != len(tokens):
        raise ValueError("unparsed tokens remain in Steam app manifest")
    app = _vdf_field(parsed, "AppState")
    if not isinstance(app, dict):
        raise ValueError("Steam app manifest has no AppState object")

    state = {}
    for field in ("appid", "installdir", "buildid"):
        value = _vdf_field(app, field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Steam app manifest is missing {field}")
        state[field] = value.strip()
    size = _vdf_field(app, "SizeOnDisk")
    if isinstance(size, str) and size.strip():
        state["sizeondisk"] = size.strip()
    beta = _vdf_field(app, "BetaKey")
    if isinstance(beta, str) and beta.strip():
        state["betakey"] = beta.strip()
    for section_name in ("UserConfig", "MountedConfig"):
        section = _vdf_field(app, section_name)
        selected = {}
        for field in ("language", "BetaKey"):
            value = _vdf_field(section, field)
            if isinstance(value, str) and value.strip():
                selected[field.casefold()] = value.strip().casefold()
        if selected:
            state[section_name.casefold()] = selected
    for field in ("InstalledDepots", "MountedDepots", "SharedDepots"):
        value = _vdf_field(app, field)
        if isinstance(value, dict):
            state[field.casefold()] = _canonical_vdf(value)

    return json.dumps(state, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

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
    repo_root: pathlib.Path = REPO,
    game_root: pathlib.Path | None = GAME_ROOT,
) -> dict:
    """Hash durable authorities and runtime-bearing files, not whole textures.

    Vendor archive hashes and owned-output hashes live in the ledger/source
    records.  Hashing those records plus live plugins/DLLs detects the changes
    that can affect initialization or save state without rereading the entire
    texture tree for every test.
    """
    instance = pathlib.Path(instance)
    repo_root = pathlib.Path(repo_root)
    game_root = pathlib.Path(game_root) if game_root is not None else None
    profile_dir = instance / "profiles" / profile
    inputs: list[dict] = []
    seen: set[str] = set()

    def stable_identity(path: pathlib.Path) -> str:
        resolved = path.resolve()
        bases = [("instance", instance), ("repo", repo_root),
                 ("documents", DOCUMENTS)]
        if game_root is not None:
            bases.append(("game", game_root))
        for label, base in bases:
            try:
                return f"{label}/{resolved.relative_to(base.resolve()).as_posix()}"
            except ValueError:
                continue
        return f"external/{resolved.name}"

    def add(path: pathlib.Path, role: str, required: bool = False,
            identity_override: str | None = None) -> None:
        identity = os.path.normcase(os.path.abspath(path))
        if required and not path.is_file():
            raise FileNotFoundError(f"required fingerprint input is missing: {path}")
        if path.is_file() and identity not in seen:
            seen.add(identity)
            inputs.append({
                "role": role,
                "path": str(path),
                "identity": identity_override or stable_identity(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    def add_normalized(path: pathlib.Path, role: str, payload: bytes,
                       normalization: str,
                       identity_override: str | None = None) -> None:
        identity = os.path.normcase(os.path.abspath(path))
        if identity in seen:
            return
        seen.add(identity)
        inputs.append({
            "role": role,
            "path": str(path),
            "identity": identity_override or stable_identity(path),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest().upper(),
            "normalization": normalization,
        })

    ledger = pathlib.Path(ledger)
    if not ledger.is_file():
        raise FileNotFoundError(f"required fingerprint input is missing: {ledger}")
    ledger_document = json.loads(ledger.read_text(encoding="utf-8-sig"))
    if not isinstance(ledger_document, dict) or not isinstance(
            ledger_document.get("mods"), list):
        raise ValueError("installed-mod ledger must be an object with a mods array")
    # The plan signature binds the build fingerprint, while the ledger stores
    # that signature. Exclude only this derived field from the ledger input to
    # avoid a cryptographic cycle; every source/test/receipt identity remains.
    fingerprint_ledger = copy.deepcopy(ledger_document)
    for row in fingerprint_ledger["mods"]:
        if isinstance(row, dict):
            row.pop("verificationContractSignature", None)
    ledger_payload = json.dumps(
        fingerprint_ledger, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode("utf-8")
    seen.add(os.path.normcase(os.path.abspath(ledger)))
    inputs.append({
        "role": "ledger",
        "path": str(ledger),
        "identity": stable_identity(ledger),
        "bytes": len(ledger_payload),
        "sha256": hashlib.sha256(ledger_payload).hexdigest().upper(),
        "normalization": "canonical-json excluding verificationContractSignature",
    })
    watchlist = repo_root / "audit" / "watched_configs.json"
    add(watchlist, "watch-spec", required=True)
    for path in sorted((repo_root / "records" / "source-builds").glob("*.json"),
                       key=lambda p: p.name.casefold()):
        add(path, "owned-source-build")
    receipt_root = (repo_root / "records" / "impact-receipts").resolve()
    for row in ledger_document["mods"]:
        if not isinstance(row, dict) or not str(row.get("impactReceipt") or "").strip():
            continue
        reference = pathlib.Path(str(row["impactReceipt"]))
        if reference.is_absolute():
            raise ValueError(f"impact receipt is not repository-relative: {reference}")
        receipt = (repo_root / reference).resolve()
        try:
            receipt.relative_to(receipt_root)
        except ValueError as exc:
            raise ValueError(
                f"impact receipt escapes records/impact-receipts: {reference}") from exc
        add(receipt, "impact-receipt", required=True)

    # Steam/Bethesda/Creations state is part of the tested build. Bind the
    # preflight-maintained inventory (normalized relative path and exact SHA-256
    # for every tracked official runtime/archive), plus exact executable,
    # catalog and master/light-plugin bytes.
    if game_root is not None:
        if not game_root.is_dir():
            raise FileNotFoundError(f"required game root is missing: {game_root}")
        manifest = repo_root / "records" / "game-folder-manifest.json"
        if not manifest.is_file():
            canonical = pathlib.Path(
                r"C:\Users\danjo\source\repos\skyrim-mod-assistant\records\game-folder-manifest.json"
            )
            if canonical.is_file():
                manifest = canonical
        add(manifest, "official-runtime-manifest", required=True,
            identity_override="repo/records/game-folder-manifest.json")
        add(game_root / "SkyrimSE.exe", "game-runtime", required=True)
        add(game_root / "skse64_loader.exe", "game-runtime", required=True)
        steam_manifest = game_root.parents[1] / "appmanifest_489830.acf"
        if not steam_manifest.is_file():
            raise FileNotFoundError(
                f"required fingerprint input is missing: {steam_manifest}")
        add_normalized(
            steam_manifest,
            "steam-app-manifest",
            steam_app_manifest_build_payload(steam_manifest),
            "canonical Steam build/depot fields; volatile session fields excluded",
        )
        add(CONTENT_CATALOG, "creations-content-catalog", required=True)
        data_root = game_root / "Data"
        for path in sorted(
            (p for p in data_root.iterdir()
             if p.is_file() and p.suffix.casefold() in {".esm", ".esl"}),
            key=lambda p: p.name.casefold(),
        ):
            add(path, "official-master-or-creation")
    for name in (
        "modlist.txt", "plugins.txt", "loadorder.txt", "lockedorder.txt",
        "settings.ini", "skyrim.ini", "skyrimprefs.ini", "skyrimcustom.ini",
    ):
        add(profile_dir / name, "profile",
            required=name in {"modlist.txt", "plugins.txt"})

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
    suffixes = {".esm", ".esp", ".esl", ".dll", ".bsa", ".ba2"}
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
    if watchlist.is_file():
        spec = json.loads(watchlist.read_text(encoding="utf-8-sig"))
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
        f"{row['role']}\t{row['identity'].casefold()}\t{row['bytes']}\t{row['sha256']}"
        for row in sorted(inputs, key=lambda row: (row["identity"].casefold(), row["role"]))
    )
    return {
        "algorithm": "sha256(stable-authority-runtime-archives-scripts-watched-config-v6)",
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
        "inputs": inputs,
    }


def contract_signature(plan: dict) -> str:
    """Hash immutable test requirements; results/status remain writable."""
    frozen = {
        "schemaVersion": plan.get("schemaVersion"),
        "testId": plan.get("testId"),
        "createdUtc": plan.get("createdUtc"),
        "summary": plan.get("summary"),
        "issue": plan.get("issue"),
        "source": plan.get("source"),
        "changeKinds": plan.get("changeKinds"),
        "riskClass": plan.get("riskClass"),
        "crashFix": plan.get("crashFix"),
        "freshCharacter": {
            key: (plan.get("freshCharacter") or {}).get(key)
            for key in ("required", "method", "reuseAcrossBuildFingerprints")
        },
        "cyclesRequired": plan.get("cyclesRequired"),
        "stagesRequired": plan.get("stagesRequired"),
        "campaignSave": plan.get("campaignSave"),
        "buildFingerprint": {
            key: (plan.get("buildFingerprint") or {}).get(key)
            for key in ("algorithm", "sha256")
        },
    }
    payload = json.dumps(frozen, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def requirements(kinds: list[str], crash_fix: bool) -> dict:
    if not kinds:
        raise ValueError("at least one change kind is required")
    unknown = sorted(set(kinds) - set(KINDS))
    if unknown:
        raise ValueError("unknown change kind(s): " + ", ".join(unknown))
    normalized = sorted(set(kinds))
    risk = max(KINDS[k]["risk"] for k in normalized)
    cycles = max(KINDS[k]["cycles"] for k in normalized)
    if crash_fix:
        cycles = max(cycles, 10)
    round_trip = any(KINDS[k]["roundTrip"] for k in normalized)
    soak = any(KINDS[k]["soak"] for k in normalized) or crash_fix
    required = ["V0-static", "V1-boot", "V2-fresh-start",
                "V3-feature-probes", "V5-log-diff"]
    if round_trip:
        required.insert(4, "V4-save-load-round-trip")
    if soak:
        required.append("V6-soak")
    required.append("V7-human-play")
    return {"kinds": normalized, "risk": risk, "cycles": cycles,
            "stages": required}


def make_plan(kinds: list[str], summary: str, issue: str | None,
              crash_fix: bool, fingerprint: dict | None = None,
              source: dict | None = None) -> dict:
    required_contract = requirements(kinds, crash_fix)
    stamp = dt.datetime.now(dt.timezone.utc)
    test_id = f"SVT-{stamp:%Y%m%dT%H%M%SZ}-{secrets.token_hex(3).upper()}"
    plan = {
        "schemaVersion": 1,
        "testId": test_id,
        "createdUtc": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "issue": issue,
        "source": copy.deepcopy(source),
        "changeKinds": required_contract["kinds"],
        "riskClass": required_contract["risk"],
        "crashFix": bool(crash_fix),
        "freshCharacter": {
            "required": True,
            "method": "main-menu New Game flow; never clone/autoload an older clean save",
            "reuseAcrossBuildFingerprints": False,
        },
        "cyclesRequired": required_contract["cycles"],
        "stagesRequired": required_contract["stages"],
        "campaignSave": {
            "required": False,
            "allowedAfterDisposablePassOnly": True,
            "purpose": "explicit migration test, never technical source of truth",
        },
        "buildFingerprint": copy.deepcopy(fingerprint),
        "status": "planned",
        "results": {},
    }
    plan["contractSignature"] = contract_signature(plan)
    return plan


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
    assert crash["crashFix"] and crash["contractSignature"] == contract_signature(crash)
    with tempfile.TemporaryDirectory(prefix="verification-fingerprint-") as raw:
        root = pathlib.Path(raw)
        instance = root / "instance"
        profile = instance / "profiles" / "Default"
        mod = instance / "mods" / "Archive Fixture"
        profile.mkdir(parents=True)
        mod.mkdir(parents=True)
        (profile / "modlist.txt").write_text("+Archive Fixture\n", encoding="utf-8")
        (profile / "plugins.txt").write_text("", encoding="utf-8")
        ledger = root / "ledger.json"
        ledger.write_text(json.dumps({"schemaVersion": 1, "mods": []}), encoding="utf-8")
        archive = mod / "Fixture.bsa"
        archive.write_bytes(b"ORIGINAL")
        first = build_fingerprint(instance, "Default", ledger, REPO, game_root=None)
        archive.write_bytes(b"CORRUPTED")
        second = build_fingerprint(instance, "Default", ledger, REPO, game_root=None)
        assert first["sha256"] != second["sha256"]
        assert any(row["identity"].endswith("mods/Archive Fixture/Fixture.bsa")
                   for row in second["inputs"])
        try:
            build_fingerprint(root / "missing-instance", "Default", ledger,
                              REPO, game_root=None)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("missing profile authorities produced a fingerprint")
        steam = root / "appmanifest_489830.acf"
        steam.write_text('''"AppState"
{
    "appid" "489830"
    "StateFlags" "4"
    "installdir" "Skyrim Special Edition"
    "LastPlayed" "1788541200"
    "buildid" "20260904"
    "SizeOnDisk" "17000000000"
    "UserConfig" { "language" "english" }
    "InstalledDepots"
    {
        "489831" { "manifest" "111" "size" "222" }
    }
}
''', encoding="utf-8")
        build_state = steam_app_manifest_build_payload(steam)
        steam.write_text('''"AppState"
{
    "appid" "489830"
    "StateFlags" "1026"
    "installdir" "Skyrim Special Edition"
    "LastPlayed" "1788549999"
    "buildid" "20260904"
    "SizeOnDisk" "17000000000"
    "UserConfig" { "language" "english" }
    "InstalledDepots" { "489831" { "manifest" "111" "size" "222" } }
}
''', encoding="utf-8")
        assert steam_app_manifest_build_payload(steam) == build_state
        steam.write_text('''"AppState"
{
    "appid" "489830"
    "installdir" "Skyrim Special Edition"
    "buildid" "20260905"
    "SizeOnDisk" "17000000000"
    "UserConfig" { "language" "english" }
    "InstalledDepots" { "489831" { "manifest" "333" "size" "222" } }
}
''', encoding="utf-8")
        assert steam_app_manifest_build_payload(steam) != build_state
    print("verification_plan selftest PASS (11 assertions)")
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
    if args.no_fingerprint:
        parser.error("--no-fingerprint is disabled: a successful verification plan must bind a build")
    fingerprint = build_fingerprint(args.instance, args.profile, args.ledger)
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
