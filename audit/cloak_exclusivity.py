"""Build an original, allowlisted full-cloak equipment exclusivity overlay.

Read-only against MO2. Writes only to the explicit staging output, never mods/.
The added slot is an equipment exclusion bit, NOT a mesh partition migration.
See cloak-exclusivity.md for evidence, limits, and the required in-game test.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
from biped_slot_audit import runtime_plugins, scan_profile


SLOT = 58
INDEX = SLOT - 30
MASK = 1 << INDEX
PELT_MASK = 1 << (57 - 30)
MOD_NAME = "Ensrick - Full Cloak Exclusivity"
RELATIVE_MANIFEST = Path("SKSE/Plugins/EnsrickFullCloakExclusivity.manifest.json")
RELATIVE_CONFIG = Path("SKSE/Plugins/SkyPatcher/armor/Ensrick Full Cloak Exclusivity/Full Cloaks.ini")
SOURCE_COMMIT = "876662e5c5b91326edf9797540c466399cb317db"
# These hashes pin the exact item inventories reviewed for this first version.
# A vendor update requires reclassification, not an automatically widened rule.
INPUTS = {
    "NW_Sons_of_Skyrim.esp": ("0610D825D420E84043BC2AF4CD6E5D8E68256C76C0A223A92021A52E838BC246", 12),
    "Cloaks - RMB SPCH.esp": ("43B409BD047B83A42B20A758E5BAB78307914F515666BBD775C837A8F1C8005C", 122),
    "Campfire.esm": ("AD5512460EFA4690EC68371C5952F7CE442CACB49A64DE96C4736251C9CE0742", 4),
    "moe-scarves.esl": ("2AC9C94068D7919932F3A85132C16096E3D9D8DF0F1F61561841B3C7A8336C19", 3),
    "Pelt Cloaks.esp": ("FF534D3D4AE65906EC1A2475D11DF9FAC1E92CA7CF2B1F9A32306F755A66B9AB", 99),
    "DIS_NordScale.esp": ("A4817E783E6653205838041E604D5C6460D7009D1D03AB8E624A7ACE6AD85C72", 0),
}
SYMBOLIC = {name: 1 << bit for bit, name in enumerate((
    "Head", "Hair", "Body", "Hands", "Forearms", "Amulet", "Ring", "Feet",
    "Calves", "Shield", "Tail", "LongHair", "Circlet", "Ears",
))}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def body_mask(value: str | int) -> int:
    if isinstance(value, int) or str(value).isdecimal():
        result = int(value)
        if not 0 <= result <= 0xFFFFFFFF:
            raise ValueError(f"Out-of-range biped mask: {value}")
        return result
    result = 0
    for part in str(value).split(","):
        try:
            result |= SYMBOLIC[part.strip()]
        except KeyError as error:
            raise ValueError(f"Unrecognized biped flag: {part!r}") from error
    return result


def full_cloak(plugin: str, editor_id: str) -> bool:
    if plugin == "NW_Sons_of_Skyrim.esp":
        return re.fullmatch(r"0_.+_Cloak(?:_.*)?", editor_id) is not None
    if plugin == "Cloaks - RMB SPCH.esp":
        return editor_id.startswith(("Cloak", "Cape"))
    if plugin == "Campfire.esm":
        return editor_id.startswith("_Camp_Cloak_Basic")
    if plugin == "moe-scarves.esl":
        return editor_id in {"_MOE_cape001AM", "_MOE_cape002gAM", "_MOE_cape002rAM"}
    if plugin == "Pelt Cloaks.esp":
        return "PeltCloak" in editor_id
    if plugin == "DIS_NordScale.esp":
        return False
    raise ValueError(f"Unaudited plugin: {plugin}")


def form_key(value: str) -> str:
    return value.split("<", 1)[0]


def directive(key: str) -> str:
    local_id, plugin = key.split(":", 1)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", local_id) or plugin not in INPUTS:
        raise ValueError(f"Invalid allowlist FormKey: {key}")
    return f"filterByArmors={plugin}|{local_id}:bipedSlotsToAdd={INDEX}"


def providers(instance: Path) -> list[Path]:
    modlist = instance / "profiles/Default/modlist.txt"
    return [instance / "overwrite"] + [
        instance / "mods" / line[1:]
        for line in modlist.read_text(encoding="utf-8-sig").splitlines()
        if line.startswith("+")
    ]


def resolve(roots: list[Path], relative: Path | str) -> Path:
    for root in roots:
        path = root / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"Not supplied by an enabled MO2 mod: {relative}")


def read_records(cli: Path, path: Path, kind: str, env: dict) -> list[dict]:
    fields = "EditorID,Name,BodyTemplate,Armature" if kind == "Armor" else "EditorID,BodyTemplate"
    proc = subprocess.run([str(cli), "record-selected-fields-by-type", str(path), kind, fields],
                          env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if proc.returncode:
        raise RuntimeError(f"Record inspection failed for {path.name}: {proc.stderr[-1000:]}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def analyze(plugin: str, armors: list[dict], addons: list[dict]) -> tuple[list[dict], list[dict]]:
    aa = {row["formKey"]: row for row in addons}
    full, excluded = [], []
    for armor in armors:
        fields = armor["fields"]
        selected = full_cloak(plugin, armor["editorId"] or "")
        row = {
            "formKey": armor["formKey"], "editorId": armor["editorId"],
            "name": fields.get("Name"), "sourceMask": body_mask(fields["BodyTemplate"]["FirstPersonFlags"]),
            "armatures": [form_key(value) for value in fields.get("Armature", [])],
            "classification": "full-cloak-or-cape" if selected else "excluded",
        }
        if not selected:
            excluded.append(row)
            continue
        if plugin == "Pelt Cloaks.esp":
            if row["sourceMask"] != PELT_MASK:
                raise ValueError(f"Pelts cloak is no longer slot57-only: {row['formKey']}")
        elif row["sourceMask"] & MASK:
            raise ValueError(f"Unexpected existing reserved slot in audited source: {row['formKey']}")
        if not row["armatures"]:
            raise ValueError(f"Full cloak has no ARMA: {row['formKey']}")
        row["expectedMaskBeforeOtherPatches"] = row["sourceMask"] | MASK
        row["addedSlot"] = None if row["sourceMask"] & MASK else SLOT
        row["addonMasks"] = {}
        for key in row["armatures"]:
            if key not in aa:
                raise ValueError(f"Unresolved or cross-plugin ARMA requires review: {key}")
            old = body_mask(aa[key]["fields"]["BodyTemplate"]["FirstPersonFlags"])
            row["addonMasks"][key] = {"source": old, "afterUnion": old | MASK}
        full.append(row)
    count = INPUTS[plugin][1]
    if len(full) != count:
        raise ValueError(f"{plugin}: classified {len(full)} full cloaks, expected {count}")
    changed_addons = {key for row in full if row["addedSlot"] for key in row["armatures"]}
    for row in excluded:
        if changed_addons.intersection(row["armatures"]):
            raise ValueError(f"Full cloak ARMA is shared by excluded item: {row['formKey']}")
    return full, excluded


def profile_fingerprint(instance: Path, game_data: Path) -> dict:
    roots = providers(instance) + [game_data]
    configs = {}
    archives = {}
    for root in roots:
        if root.is_dir():
            for path in root.glob("*.bsa"):
                stat = path.stat()
                archives.setdefault(path.name.lower(), {"bytes": stat.st_size, "mtimeNs": stat.st_mtime_ns})
        base = root / "SKSE/Plugins/SkyPatcher"
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.ini")):
            relative = path.relative_to(root).as_posix().lower()
            if relative != RELATIVE_CONFIG.as_posix().lower():
                configs.setdefault(relative, sha256(path))
    profile = instance / "profiles/Default"
    enabled = [line[1:] for line in (profile / "modlist.txt").read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("+") and line[1:] != MOD_NAME]
    return {
        "plugins": [{"name": path.name.lower(), "sha256": sha256(path)} for path in runtime_plugins(instance, game_data)],
        "enabledModOrderExcludingSelf": enabled,
        "winningLooseSkyPatcherConfigsExcludingSelf": configs,
        "skyPatcherDllSha256": sha256(resolve(roots, "SKSE/Plugins/SkyPatcher.dll")),
        "skyPatcherIniSha256": sha256(resolve(roots, "SKSE/Plugins/SkyPatcher.ini")),
        # Watch container additions/changes without hashing unrelated gigabytes
        # of textures. Participating BSA contents are separately SHA-256 bound.
        "visibleBsaMetadata": archives,
    }


def check_installed(instance: Path, game_data: Path) -> list[str]:
    """Preflight API: [] means fresh STATIC reservation, not a gameplay pass.

    If the overlay is not installed/enabled this gate is a no-op. A manifest
    missing from an installed overlay is a failure, not an implicit adoption.
    """
    roots = providers(instance) + [game_data]
    enabled = any(root.name == MOD_NAME for root in roots)
    try:
        config = resolve(roots, RELATIVE_CONFIG)
    except FileNotFoundError:
        try:
            resolve(roots, RELATIVE_MANIFEST)
            manifest_present = True
        except FileNotFoundError:
            manifest_present = False
        return ["Enabled full-cloak overlay is missing its equipment configuration"] if enabled or manifest_present else []
    try:
        manifest = json.loads(resolve(roots, RELATIVE_MANIFEST).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as error:
        return [f"Full-cloak slot reservation manifest missing or invalid: {error}"]
    if not isinstance(manifest, dict):
        return ["Full-cloak reservation manifest must be a JSON object"]
    problems = []
    if manifest.get("slot") != SLOT or manifest.get("configSha256") != sha256(config):
        problems.append("Full-cloak configuration or reserved slot differs from its audited manifest")
    try:
        actual = profile_fingerprint(instance, game_data)
        expected = manifest["fingerprint"]
        if not isinstance(expected, dict):
            raise ValueError("Manifest fingerprint must be a JSON object")
        for key in actual:
            if actual[key] != expected.get(key):
                problems.append(f"Full-cloak slot reservation is stale: {key} changed; rerun full reservation audit")
        models = manifest.get("participatingModelPaths", [])
        if not isinstance(models, list) or any(not isinstance(path, str) for path in models):
            raise ValueError("Manifest model paths must be a JSON array of strings")
        problems.extend(validate_layer_proof(manifest.get("allLayerReservationAudit"), roots, actual, set(models)))
    except (OSError, ValueError, KeyError) as error:
        problems.append(f"Full-cloak reservation freshness could not be verified: {error}")
    return problems


def safe_relative(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Proof input path must be a string")
    result = value.replace("\\", "/").lower()
    if result.startswith("/") or ":" in result or any(part in ("", ".", "..") for part in result.split("/")):
        raise ValueError(f"Unsafe proof input path: {value!r}")
    return result


def validate_layer_proof(proof: dict | None, roots: list[Path], fingerprint: dict,
                         expected_models: set[str]) -> list[str]:
    """Bind the independent inspection to current bytes without loading a DLL.

    Packed assets bind their whole source BSA, including its index. Missing
    assets have explicit absence sentinels. A new loose override invalidates
    either packed or absent proof. All visible BSA metadata is also bound by
    the profile fingerprint to detect newly added/changed potential providers.
    """
    errors = []
    if not isinstance(proof, dict) or proof.get("slot") != SLOT or proof.get("status") != "PASS":
        return ["Full-cloak all-layer reservation proof is missing or not PASS"]
    if not expected_models:
        return ["Full-cloak participating mesh allowlist is missing"]
    if proof.get("profileFingerprint") != fingerprint:
        errors.append("Full-cloak all-layer proof belongs to a different profile/input fingerprint")
    assets = proof.get("assets", [])
    if not isinstance(assets, list) or any(not isinstance(row, dict) for row in assets):
        return errors + ["Full-cloak asset proof must be an array of objects"]
    try:
        paths = [safe_relative(row["relativePath"]) for row in assets]
    except (KeyError, TypeError, ValueError) as error:
        return errors + [f"Malformed full-cloak asset bindings: {error}"]
    if len(paths) != len(set(paths)) or set(paths) != {path.lower() for path in expected_models}:
        errors.append("Full-cloak layer proof does not cover the exact explicit and weight-companion model set")
    checked_hashes = {}

    def file_hash(path: Path) -> str:
        key = str(path.resolve()).lower()
        if key not in checked_hashes:
            checked_hashes[key] = sha256(path)
        return checked_hashes[key]

    def current_hash(relative: str) -> str:
        relative = safe_relative(relative)
        return file_hash(resolve(roots, relative))

    bindings = proof.get("fileBindings", [])
    if not isinstance(bindings, list) or any(not isinstance(row, dict) for row in bindings):
        return errors + ["Full-cloak physical input bindings must be an array of objects"]
    binding_index = {}
    for binding in bindings:
        try:
            origin = binding.get("root")
            bases = {"instance": roots[0].parent, "gameData": roots[-1], "game-data": roots[-1]}
            if origin not in bases:
                raise ValueError(f"Unknown input root: {origin}")
            relative = safe_relative(binding["relativePath"])
            expected_hash = binding["sha256"]
            if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected_hash):
                raise ValueError("Malformed physical input digest")
            key = (origin, relative)
            if key in binding_index:
                raise ValueError(f"Duplicate physical input binding: {relative}")
            binding_index[key] = expected_hash.upper()
            path = bases[origin] / relative
            if file_hash(path) != expected_hash.upper():
                errors.append(f"Audited cloak layer physical input changed: {relative}")
        except (OSError, IndexError, KeyError, TypeError, ValueError) as error:
            errors.append(f"Could not verify full-cloak physical input: {error}")

    for row, relative in zip(assets, paths):
        try:
            try:
                loose = resolve(roots, relative)
            except FileNotFoundError:
                loose = None
            if row.get("state") == "absent":
                if loose is not None:
                    errors.append(f"Previously absent cloak model appeared: {relative}; inspect its partitions")
                continue
            if row.get("state") != "present":
                errors.append(f"Unrecognized cloak model proof state: {relative}")
                continue
            partitions = row.get("partitionSlots")
            if row.get("parseSucceeded") is not True or not isinstance(partitions, list) or any(type(value) is not int for value in partitions):
                errors.append(f"Cloak mesh proof lacks successful parse/partition evidence: {relative}")
            elif SLOT in partitions:
                errors.append(f"Cloak mesh already uses reserved partition {SLOT}: {relative}")
            kind = str(row.get("providerKind", "")).lower()
            if kind == "loose":
                expected_hash = row.get("sha256", row.get("hash", ""))
                if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected_hash) or loose is None or current_hash(relative) != expected_hash.upper():
                    errors.append(f"Audited cloak mesh changed or lost its loose provider: {relative}")
            elif kind == "bsa":
                if loose is not None:
                    errors.append(f"Packed cloak model acquired a new loose override: {relative}")
                archive = row.get("archiveName", row.get("providerName"))
                source = safe_relative(row["sourceRelativePath"]) if "sourceRelativePath" in row else None
                expected_hash = row.get("archiveSha256", row.get("archiveHash",
                                      binding_index.get((row.get("sourceRoot"), source), "")))
                if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected_hash) or not archive or current_hash(archive) != expected_hash.upper():
                    errors.append(f"Cloak mesh source BSA changed: {relative}")
            else:
                errors.append(f"Unrecognized cloak mesh provider kind: {relative}")
        except (OSError, TypeError, ValueError) as error:
            errors.append(f"Could not verify cloak model binding {relative}: {error}")
    return errors


def conservative_addon_scope(reservation: dict, target_keys: set[str]) -> set[str]:
    """Include override links, and reject all excluded users of changed ARMA.

    Every declaration is considered rather than guessing ESM staging order.
    A losing record can therefore block a safe update, but cannot conceal an
    unsafe one. Resolving such a block needs explicit winning-record review.
    """
    declarations = reservation["declarations"]
    observed = {row["formKey"].lower() for row in declarations if row["type"] == "ARMO"}
    if target_keys - observed:
        raise ValueError(f"Full-cloak targets absent from active plugins: {sorted(target_keys - observed)}")
    changed = {link for row in declarations if row["type"] == "ARMO"
               and row["formKey"].lower() in target_keys for link in row["armatures"]}
    changed_keys = {key.lower() for key in changed}
    if not changed:
        raise ValueError("No active armor addons resolved for the full-cloak allowlist")
    leaks = [{"formKey": row["formKey"], "editorId": row["editorId"], "provider": row["provider"]}
             for row in declarations if row["type"] == "ARMO" and row["formKey"].lower() not in target_keys
             and changed_keys.intersection(key.lower() for key in row["armatures"])]
    if leaks:
        raise ValueError(f"Full cloak ARMA shared by an excluded active declaration: {leaks}")
    addon_rows = [row for row in declarations if row["type"] == "ARMA" and row["formKey"].lower() in changed_keys]
    found = {row["formKey"].lower() for row in addon_rows}
    if changed_keys - found:
        raise ValueError(f"Active full-cloak ARMA unresolved: {sorted(changed_keys - found)}")
    explicit = {"meshes/" + model.removeprefix("meshes/") for row in addon_rows for model in row["models"]}
    return expand_weight_models(explicit)


def expand_weight_models(paths: set[str]) -> set[str]:
    """Weight-slider endpoints may load a _0 NIF not named in the ARMA."""
    return paths | {path[:-6] + "_0.nif" for path in paths if path.lower().endswith("_1.nif")}


def build(instance: Path, cli: Path, output: Path, dotnet_root: Path | None,
          game_data: Path, layer_audit: Path | None = None) -> dict:
    instance, output = instance.resolve(), output.resolve()
    if output == instance or instance in output.parents:
        raise ValueError("Output must be outside the MO2 instance; no live or vendor writes allowed")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory; do not silently replace an earlier receipt")
    roots = providers(instance) + [game_data]
    fingerprint = profile_fingerprint(instance, game_data)
    reservation = scan_profile(instance, game_data, SLOT)
    if reservation["collisions"]:
        raise ValueError(f"Slot {SLOT} is occupied by active ARMO/ARMA: {reservation['collisions']}")
    env = dict(os.environ)
    if dotnet_root:
        env["DOTNET_ROOT"] = str(dotnet_root.resolve())
    paths = {plugin: resolve(roots, plugin) for plugin in INPUTS}
    for plugin, path in paths.items():
        if sha256(path) != INPUTS[plugin][0]:
            raise ValueError(f"{plugin}: vendor input changed; re-audit its item classification")
    sky = resolve(roots, "SKSE/Plugins/SkyPatcher.dll")
    sky_config = configparser.ConfigParser(interpolation=None)
    sky_config.read(resolve(roots, "SKSE/Plugins/SkyPatcher.ini"), encoding="utf-8-sig")
    if sky_config.getint("Patcher", "iEnableArmorPatching", fallback=0) != 1:
        raise ValueError("SkyPatcher armor patching is disabled; exclusion config cannot execute")
    sky_bytes = sky.read_bytes()
    tokens = {key: key.encode("ascii") in sky_bytes for key in ("filterByArmors", "bipedSlotsToAdd")}
    if not all(tokens.values()):
        raise ValueError(f"Winning SkyPatcher binary lacks required parser tokens: {tokens}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {(plugin, kind): pool.submit(read_records, cli, path, kind, env)
                for plugin, path in paths.items() for kind in ("Armor", "ArmorAddon")}
        data = {key: job.result() for key, job in jobs.items()}
    full, excluded = [], []
    for plugin in INPUTS:
        selected, omitted = analyze(plugin, data[plugin, "Armor"], data[plugin, "ArmorAddon"])
        full.extend(selected)
        excluded.extend(omitted)
    full.sort(key=lambda row: row["formKey"].lower())
    mutations = [row for row in full if row["addedSlot"]]
    target_models = conservative_addon_scope(reservation, {row["formKey"].lower() for row in mutations})
    lines = [
        "; Ensrick - Full Cloak Exclusivity 0.1.0 (original configuration, MIT).",
        "; Explicit reviewed ARMO allowlist; retain all original rendering slots.",
        "; Index28 = reserved biped slot58. SkyPatcher adds this bit to ARMO and attached ARMA.",
        "; Existing slots are preserved. No mesh/texture/vendor plugin is redistributed.",
        "; No collar, fur mantle, scarf, gaiter, hood, or unrelated accessory is changed.",
        "; Source and fresh audit recipe: audit/cloak_exclusivity.py in skyrim-mod-assistant.",
        "; This is equipment exclusion, not NPC inventory cleanup or cloth physics.",
        "",
    ]
    for row in mutations:
        lines.extend([f"; {row['editorId']}", directive(row["formKey"])])
    config = ("\n".join(lines) + "\n").encode("utf-8")
    destination = output / "mod" / RELATIVE_CONFIG
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(config)
    # Pairwise mathematical exclusion is a static property, not an engine test.
    pairs = sum(1 for i, first in enumerate(full) for second in full[i + 1:]
                if first["expectedMaskBeforeOtherPatches"] & second["expectedMaskBeforeOtherPatches"] & MASK)
    if pairs != len(full) * (len(full) - 1) // 2:
        raise AssertionError("A full-cloak pair does not share the exclusivity bit")
    if fingerprint != profile_fingerprint(instance, game_data):
        raise ValueError("Profile inputs changed during the audit; discard staging and retry")
    manifest = {"component": MOD_NAME, "version": "0.1.0", "slot": SLOT,
                "configSha256": sha256(destination), "fingerprint": fingerprint,
                "participatingModelPaths": sorted(target_models),
                "recordReservation": {key: reservation[key] for key in ("plugins", "armorDeclarations", "armorAddonDeclarations")},
                "allLayerReservationAudit": None}
    # Until an independent NIF/runtime-config proof is supplied, stage only:
    # deliberately do not produce an installable ZIP or an approving manifest.
    package = output / "Ensrick-Full-Cloak-Exclusivity-0.1.0.zip"
    if layer_audit is not None:
        proof = json.loads(layer_audit.read_text(encoding="utf-8"))
        proof_errors = validate_layer_proof(proof, roots, fingerprint, target_models)
        if proof_errors:
            raise ValueError(f"Independent all-layer proof is invalid/stale: {proof_errors}")
        manifest["allLayerReservationAudit"] = proof
        manifest_path = output / "mod" / RELATIVE_MANIFEST
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        license_path = output / "mod" / "EnsrickFullCloakExclusivity.LICENSE.txt"
        license_path.write_text((Path(__file__).resolve().parents[1] / "LICENSE").read_text(encoding="utf-8"), encoding="utf-8")
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for file in sorted((output / "mod").rglob("*")):
                if file.is_file():
                    entry = zipfile.ZipInfo(file.relative_to(output / "mod").as_posix(), date_time=(2026, 9, 5, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(entry, file.read_bytes())
    receipt = {
        "component": "Ensrick - Full Cloak Exclusivity", "version": "0.1.0",
        "verification": "STATIC PASS; UNVERIFIED in game; not installed by this command" if layer_audit else "STAGED ONLY; awaiting independent NIF/runtime-config reservation audit; no ZIP emitted",
        "instance": str(instance), "inputs": {plugin: {"path": str(path), "sha256": sha256(path)} for plugin, path in paths.items()},
        "skyPatcher": {"path": str(sky), "sha256": sha256(sky), "parserTokensPresent": tokens,
                       "inspectedUpstreamCommit": SOURCE_COMMIT,
                       "sourceMatchesVendorBinary": "not proven; parser token presence is not execution"},
        "config": {"relativePath": RELATIVE_CONFIG.as_posix(), "sha256": sha256(destination), "directives": len(mutations)},
        "package": {"path": str(package), "sha256": sha256(package)} if package.is_file() else None,
        "reservation": reservation,
        "participatingModelPaths": sorted(target_models),
        "counts": {"fullCloaks": len(full), "patchedArmors": len(mutations),
                   "pairwiseExclusions": pairs, "excludedItems": len(excluded)},
        "fullCloaks": full, "excludedItems": excluded,
        "limits": ["Existing saved worn flags require re-equip testing, not inventory reset.",
                   "Does not remove spare inventory items or change distribution.",
                   "Does not add SMP physics.", "MrDragonfly slot57 accessories are unaffected by the new slot58 reservation.",
                   "SoS and Scale Nord collars retain their existing slot46 cloth-cloak conflict.",
                   "Pelts full cloaks and Pelts mantles retain their existing shared slot57 conflict.",
                   "Ten Pelts mantle-family objects are deliberately excluded, including Crude Cloak/FurPeltMantle.",
                   "No full-cloak coverage claim for unrelated new-land/NPC equipment beyond the six audited sources."],
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--record-cli", type=Path, required=True)
    parser.add_argument("--dotnet-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-data", type=Path, required=True)
    parser.add_argument("--layer-audit", type=Path)
    args = parser.parse_args()
    receipt = build(args.instance, args.record_cli, args.output, args.dotnet_root, args.game_data, args.layer_audit)
    print(json.dumps({key: receipt[key] for key in ("verification", "counts", "config", "package")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
