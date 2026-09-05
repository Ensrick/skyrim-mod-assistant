r"""Identify owned patches/artifacts which must be reviewed for a mod change.

The scanner is conservative by design.  It proves candidate relationships from
hard masters, declared source-build inputs, normalized record overlap,
record-type selectors and asset globs.  A missing impact policy is a manual
review requirement, never evidence that an artifact is unaffected (#228).

It does not mutate a patch and it does not make a taste decision.

    py -3 audit/patch_impact.py --operation install --changed-mod "Some Mod"
    py -3 audit/patch_impact.py --operation update --changed-root C:\staged\mod
    py -3 audit/patch_impact.py --selftest
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import fnmatch
import json
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esp import Plugin
import keep_coverage


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
LEDGER = REPO / "records" / "installed-mods.json"
GAME_DATA = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"
)
PLUGIN_SUFFIXES = {".esm", ".esp", ".esl"}
OUTCOMES = {"regenerated", "amended", "verified-current", "not-affected", "blocked-decision"}


def key(value: object) -> str:
    return str(value or "").strip().casefold()


def _within(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _direct_child(root: pathlib.Path, name: str) -> pathlib.Path | None:
    """Resolve one literal child name without permitting path traversal."""
    text = str(name)
    if (not text or text != text.strip() or text in {".", ".."} or
            "/" in text or "\\" in text or
            pathlib.PureWindowsPath(text).drive):
        return None
    resolved_root = pathlib.Path(root).resolve()
    candidate = (resolved_root / text).resolve()
    return candidate if candidate.parent == resolved_root else None


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def changed_fingerprint(roots: list[tuple[str, pathlib.Path]]) -> dict:
    """Bind a review to exact installed content, excluding MO2-owned metadata."""
    files = []
    for name, root in roots:
        for path in sorted((p for p in root.rglob("*") if p.is_file()),
                           key=lambda p: str(p).casefold()):
            relative = path.relative_to(root).as_posix()
            if relative.casefold() == "meta.ini":
                continue
            files.append({
                "mod": name,
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    canonical = "\n".join(
        f"{row['mod'].casefold()}\t{row['path'].casefold()}\t{row['bytes']}\t{row['sha256']}"
        for row in files
    )
    return {
        "algorithm": "sha256(relative-path,size,content)-v1; excludes meta.ini",
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper(),
        "files": len(files),
        "bytes": sum(row["bytes"] for row in files),
    }


def audit_signature(result: dict) -> str:
    scope = {
        "operation": result.get("operation"),
        "source": result.get("source"),
        "changedFingerprint": result.get("changedFingerprint"),
        "changedPlugins": result.get("changedPlugins"),
        "changedRecordTypes": result.get("changedRecordTypes"),
        "changedPluginParseErrors": result.get("changedPluginParseErrors"),
        "artifacts": [{
            "artifact": row.get("artifact"),
            "artifactEnabled": row.get("artifactEnabled"),
            "artifactFingerprint": row.get("artifactFingerprint"),
            "sourceBuildRecord": row.get("sourceBuildRecord"),
            "sourceBuildRecordSha256": row.get("sourceBuildRecordSha256"),
            "impactPolicy": row.get("impactPolicy"),
            "disposition": row.get("disposition"),
            "reasons": row.get("reasons"),
            "patchParseErrors": row.get("patchParseErrors"),
        } for row in result.get("artifacts", [])],
    }
    payload = json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def enabled_mods(instance: pathlib.Path, profile: str) -> list[str]:
    path = instance / "profiles" / profile / "modlist.txt"
    if not path.exists():
        return []
    return [
        line[1:].strip() for line in path.read_text(
            encoding="utf-8-sig", errors="replace"
        ).splitlines()
        if line.startswith("+") and line[1:].strip()
    ]


def active_plugins(instance: pathlib.Path, profile: str) -> set[str]:
    """Normalized plugin identities starred in the selected MO2 profile."""
    path = instance / "profiles" / profile / "plugins.txt"
    if not path.is_file():
        return set()
    return {
        key(line[1:]) for line in path.read_text(
            encoding="utf-8-sig", errors="replace").splitlines()
        if line.startswith("*") and key(line[1:])
    }


def plugin_inventory(root: pathlib.Path) -> list[pathlib.Path]:
    if not root.is_dir():
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_file() and p.suffix.casefold() in PLUGIN_SUFFIXES),
        key=lambda p: p.name.casefold(),
    )


def relative_assets(root: pathlib.Path) -> list[str]:
    if not root.is_dir():
        return []
    assets = {p.relative_to(root).as_posix()
              for p in root.rglob("*") if p.is_file()}
    # Asset-path policies describe Data-relative assets, regardless of whether
    # a vendor ships them loose or packed. Reading the BSA index is sufficient;
    # no extraction or payload decoding is needed for relationship discovery.
    from modasset import BSA
    for archive in (p for p in root.rglob("*")
                    if p.is_file() and p.suffix.casefold() == ".bsa"):
        for name in BSA(str(archive)).names():
            assets.add(name.replace("\\", "/"))
    return sorted(assets, key=str.casefold)


def effective_plugins(instance: pathlib.Path, profile: str,
                      game_data: pathlib.Path = GAME_DATA) -> dict[str, pathlib.Path]:
    """MO2 modlist is highest-priority first in this instance."""
    winners: dict[str, pathlib.Path] = {}
    # Overwrite is always above every managed mod, regardless of modlist order.
    overwrite = instance / "overwrite"
    for path in plugin_inventory(overwrite):
        winners[key(path.name)] = path
    for mod_name in enabled_mods(instance, profile):
        for path in plugin_inventory(instance / "mods" / mod_name):
            winners.setdefault(key(path.name), path)
    if game_data.is_dir():
        for path in plugin_inventory(game_data):
            winners.setdefault(key(path.name), path)
    return winners


def record_keys(path: pathlib.Path) -> tuple[set[tuple[str, str, int]], set[str], list[str]]:
    plugin = Plugin(str(path))
    records: set[tuple[str, str, int]] = set()
    types: set[str] = set()
    for record_type, form_id, _size in plugin.formids:
        record_name = record_type.decode("ascii", "replace")
        types.add(record_name)
        index = form_id >> 24
        origin = plugin.masters[index] if index < len(plugin.masters) else plugin.name
        records.add((record_name, key(origin), form_id & 0x00FFFFFF))
    return records, types, plugin.masters


def source_record_for(row: dict, records_dir: pathlib.Path) -> tuple[pathlib.Path | None, dict | None]:
    candidates: list[tuple[str, bool]] = []
    recipe = row.get("recipe")
    if isinstance(recipe, dict) and recipe.get("record"):
        candidates.append((str(recipe["record"]), True))
    for field in (row.get("note"), row.get("distributionBasis")):
        if field:
            candidates += [
                (candidate, False) for candidate in
                re.findall(r"records/source-builds/[A-Za-z0-9_.-]+\.json", str(field))
            ]
    repo_root = records_dir.parent.parent
    for candidate, explicit in candidates:
        path = pathlib.Path(candidate)
        if not path.is_absolute():
            path = repo_root / path
        if path.exists():
            try:
                return path, json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                if explicit:
                    raise ValueError(
                        f"explicit source-build record is unreadable: {path}: {exc}") from exc
                continue
        if explicit:
            raise FileNotFoundError(f"explicit source-build record is missing: {path}")

    normalized_name = re.sub(r"[^a-z0-9]+", "", key(row.get("modName")))
    best = None
    for path in records_dir.glob("*.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        component = re.sub(r"[^a-z0-9]+", "", key(document.get("component")))
        if component and (component == normalized_name or component in normalized_name or normalized_name in component):
            if best is None or len(component) > best[0]:
                best = (len(component), path, document)
    return (best[1], best[2]) if best else (None, None)


def owned_rows(ledger_path: pathlib.Path) -> list[dict]:
    document = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    out = []
    for row in document.get("mods", []):
        name = str(row.get("modName") or "")
        try:
            mod_id = int(row.get("modId") or 0)
        except (TypeError, ValueError):
            mod_id = -1
        own = (mod_id == 0 and (
            name.startswith("Ensrick") or name.endswith("- Ensrick") or
            "Source Build" in name or name in {"LaunchProbe", "MenuPilot", "Period Underlayers - SPID"}
        )) or bool(row.get("distribution"))
        if own:
            out.append(row)
    return sorted(out, key=lambda row: key(row.get("modName")))


def evaluate_policy(policy: dict | None, changed_names: set[str],
                    changed_types: set[str], changed_assets: list[str]) -> tuple[list[str], bool]:
    if not policy:
        return ["impactPolicy missing"], True
    reasons: list[str] = []
    manual = False
    mode = key(policy.get("mode"))
    allowed_modes = {"declared-inputs", "record-types", "full-profile", "asset-paths", "manual"}
    if mode not in allowed_modes:
        reasons.append(f"impactPolicy has invalid mode: {mode or '(blank)'}")
        manual = True
    required_arrays = {
        "declared-inputs": "inputs",
        "record-types": "recordTypes",
        "asset-paths": "assetGlobs",
    }
    required = required_arrays.get(mode)
    if required and (not isinstance(policy.get(required), list) or
                     not policy.get(required)):
        reasons.append(f"impactPolicy mode {mode} requires a non-empty {required} array")
        manual = True
    if mode == "full-profile":
        reasons.append("impactPolicy is full-profile")
    if mode == "manual":
        reasons.append("impactPolicy requires manual review")
        manual = True
    declared = {key(item) for item in policy.get("inputs", [])}
    matched = sorted(declared & changed_names)
    if matched:
        reasons.append("declared input changed: " + ", ".join(matched))
    selected_types = {str(item).upper() for item in policy.get("recordTypes", [])}
    overlap_types = sorted(selected_types & changed_types)
    if overlap_types:
        reasons.append("selected record type changed: " + ", ".join(overlap_types))
    globs = [str(item).casefold() for item in policy.get("assetGlobs", [])]
    matches = sorted({asset for asset in changed_assets
                      if any(fnmatch.fnmatch(asset.casefold(), pattern) for pattern in globs)})
    if matches:
        preview = matches[:5]
        reasons.append("selected asset path changed: " + ", ".join(preview)
                       + (f" (+{len(matches) - len(preview)} more)" if len(matches) > len(preview) else ""))
    return reasons, manual


def audit(operation: str, changed_roots: list[pathlib.Path], changed_names: list[str],
          instance: pathlib.Path = INSTANCE, profile: str = PROFILE,
          ledger_path: pathlib.Path = LEDGER) -> dict:
    instance = pathlib.Path(instance)
    ledger_path = pathlib.Path(ledger_path)
    roots: list[tuple[str, pathlib.Path]] = []
    for name in changed_names:
        root = _direct_child(instance / "mods", name)
        if root is None:
            raise ValueError(
                f"changed mod must be one literal MO2 mod folder name: {name!r}")
        if not root.is_dir():
            raise FileNotFoundError(f"changed mod folder does not exist: {root}")
        roots.append((str(name), root))
    for root in changed_roots:
        path = pathlib.Path(root).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"changed root does not exist: {path}")
        roots.append((path.name, path))
    if not roots:
        raise ValueError("at least one changed mod/root is required")
    if operation == "remove" and not any(
            any(path.is_file() for path in root.rglob("*")) for _name, root in roots):
        raise ValueError(
            "remove audit requires a retained, non-empty before-image root; an "
            "empty post-removal directory cannot prove deleted records/assets")

    changed_plugin_paths = [path for _name, root in roots for path in plugin_inventory(root)]
    changed_assets = [asset for _name, root in roots for asset in relative_assets(root)]
    changed_name_keys = {key(name) for name, _root in roots}
    changed_name_keys |= {key(path.name) for path in changed_plugin_paths}
    changed_records: set[tuple[str, str, int]] = set()
    changed_types: set[str] = set()
    parse_errors: list[str] = []
    for path in changed_plugin_paths:
        try:
            records, types, _masters = record_keys(path)
            changed_records |= records
            changed_types |= types
        except Exception as exc:
            parse_errors.append(f"{path}: {type(exc).__name__}: {exc}")

    results = []
    policy_gaps = 0
    affected = 0
    for row in owned_rows(ledger_path):
        mod_name = str(row.get("modName"))
        record_path, source = source_record_for(row, REPO / "records" / "source-builds")
        policy = row.get("impactPolicy") or ((source or {}).get("impactPolicy"))
        reasons, manual = evaluate_policy(policy, changed_name_keys, changed_types, changed_assets)
        if not policy:
            policy_gaps += 1

        manifest_text = json.dumps(source or {}, sort_keys=True).casefold()
        mentioned = sorted(name for name in changed_name_keys if name and name in manifest_text)
        if mentioned:
            reasons.append("source-build record mentions changed input: " + ", ".join(mentioned))

        direct_count = 0
        hard_masters: set[str] = set()
        patch_parse_errors = []
        folder = _direct_child(instance / "mods", mod_name)
        artifact_fingerprint = (changed_fingerprint([(mod_name, folder)])
                                if folder is not None and folder.is_dir() else None)
        if folder is None:
            reasons.append("owned artifact name is not one literal MO2 mod folder")
            manual = True
        elif artifact_fingerprint is None:
            reasons.append("owned artifact folder is missing")
            manual = True
        for plugin_path in plugin_inventory(folder) if folder is not None else []:
            try:
                # Review the artifact's own bytes, including when the artifact
                # is disabled or its basename is currently shadowed. Parsing an
                # effective winner here can silently substitute an unrelated
                # provider and erase this owned patch's real relationships.
                patch_records, _types, masters = record_keys(plugin_path)
                direct_count += len(patch_records & changed_records)
                hard_masters |= {m for m in masters if key(m) in changed_name_keys}
            except Exception as exc:
                patch_parse_errors.append(f"{plugin_path}: {type(exc).__name__}: {exc}")
        if hard_masters:
            reasons.append("changed plugin is a hard master: " + ", ".join(sorted(hard_masters, key=str.casefold)))
        if direct_count:
            reasons.append(f"normalized record overlap: {direct_count} record(s)")

        observed = [r for r in reasons if r != "impactPolicy missing"]
        if observed:
            disposition = "candidate-impact"
            affected += 1
        elif manual or not policy:
            disposition = "manual-review-required"
        else:
            disposition = "no-observed-relation-review-required"
        if record_path:
            try:
                record_display = str(record_path.relative_to(REPO)).replace("\\", "/")
            except ValueError:
                record_display = str(record_path)
        else:
            record_display = None
        record_hash = sha256_file(record_path) if record_path else None
        results.append({
            "artifact": mod_name,
            "artifactEnabled": row.get("enabled") is True,
            "artifactFingerprint": artifact_fingerprint,
            "sourceBuildRecord": record_display,
            "sourceBuildRecordSha256": record_hash,
            "impactPolicy": policy,
            "disposition": disposition,
            "reasons": reasons,
            "patchParseErrors": patch_parse_errors,
            "requiredOutcome": "regenerated | amended | verified-current | not-affected | blocked-decision",
            "outcome": None,
            "evidence": "",
            "outputHashes": [],
        })

    result = {
        "schemaVersion": 1,
        "operation": operation,
        "changed": [{"name": name, "root": str(root)} for name, root in roots],
        "changedFingerprint": changed_fingerprint(roots),
        "changedPlugins": [path.name for path in changed_plugin_paths],
        "changedRecordTypes": sorted(changed_types),
        "changedAssetCount": len(changed_assets),
        "changedPluginParseErrors": parse_errors,
        "summary": {
            "ownedArtifactsReviewed": len(results),
            "candidateImpacts": affected,
            "impactPolicyGaps": policy_gaps,
            "receiptComplete": False,
        },
        "artifacts": results,
        "review": {"reviewedBy": "", "reviewedUtc": "", "issue": ""},
        "receiptRule": "Every artifact needs one explicit requiredOutcome before activation (#228).",
    }
    result["auditSignature"] = audit_signature(result)
    return result


def validate_receipt(current: dict, receipt: dict, repo_root: pathlib.Path = REPO,
                     instance: pathlib.Path = INSTANCE, profile: str = PROFILE,
                     ledger_path: pathlib.Path = LEDGER) -> list[str]:
    """Validate explicit decisions against a freshly recomputed impact audit.

    ``requiredPatches`` names existing, independently completed dependencies;
    it is not a batch-install request. Each name must be one literal MO2 mod
    folder already enabled and matched by one enabled ledger row. Nexus-backed
    rows additionally require an applied curator Keep (a queued Keep does not
    count). The caller must install/accept such patches in an earlier lifecycle.
    """
    errors = []
    if not isinstance(receipt, dict):
        return ["receipt root must be a JSON object"]
    if receipt.get("schemaVersion") != 1:
        errors.append("receipt schemaVersion must be 1")
    if receipt.get("operation") != current.get("operation"):
        errors.append("receipt operation does not match current operation")
    if receipt.get("changedFingerprint", {}).get("sha256") != \
            current.get("changedFingerprint", {}).get("sha256"):
        errors.append("receipt changed-content fingerprint does not match current payload")
    if receipt.get("auditSignature") != current.get("auditSignature"):
        errors.append("receipt audit signature is stale; artifact relationships or policy changed")
    if audit_signature(receipt) != current.get("auditSignature"):
        errors.append("receipt frozen audit fields were edited after generation")

    source = current.get("source") if isinstance(current.get("source"), dict) else {}
    try:
        nexus_mod_id = int(source.get("modId") or 0)
    except (TypeError, ValueError):
        nexus_mod_id = 0
    if nexus_mod_id > 0:
        intake = receipt.get("intakeReview")
        if not isinstance(intake, dict):
            errors.append("Nexus adoption requires an intakeReview object")
            intake = {}
        approval = intake.get("userApproval")
        if not isinstance(approval, dict) or approval.get("approved") is not True:
            errors.append("intakeReview.userApproval.approved must be true")
        elif len(str(approval.get("evidence") or "").strip()) < 12:
            errors.append("intakeReview.userApproval requires durable evidence")
        selection = intake.get("fileSelection")
        if not isinstance(selection, dict) or selection.get("reviewed") is not True:
            errors.append("intakeReview.fileSelection.reviewed must be true")
        elif len(str(selection.get("evidence") or "").strip()) < 12:
            errors.append("intakeReview.fileSelection requires exact-file rationale")
        permissions = intake.get("permissions")
        permission_classes = {
            "distributable", "vendor-only", "external-download", "local-only"
        }
        if (not isinstance(permissions, dict) or
                str(permissions.get("classification") or "") not in permission_classes):
            errors.append("intakeReview.permissions.classification is invalid/missing")
        elif len(str(permissions.get("evidence") or "").strip()) < 12:
            errors.append("intakeReview.permissions requires licence/permission evidence")
        requirements = intake.get("requirements")
        if not isinstance(requirements, dict) or requirements.get("reviewed") is not True:
            errors.append("intakeReview.requirements.reviewed must be true")
        else:
            required_patches = requirements.get("requiredPatches")
            if not isinstance(required_patches, list) or not all(
                    isinstance(name, str) and name.strip() for name in required_patches):
                errors.append("intakeReview.requirements.requiredPatches must be an array")
            else:
                required_plugins = requirements.get("requiredPlugins", {})
                if not isinstance(required_plugins, dict) or not all(
                        isinstance(name, str) and isinstance(plugins, list) and
                        all(isinstance(plugin, str) and plugin.strip()
                            for plugin in plugins)
                        for name, plugins in required_plugins.items()):
                    errors.append(
                        "intakeReview.requirements.requiredPlugins must map patch "
                        "folder names to plugin-name arrays")
                    required_plugins = {}
                patch_keys = {key(name) for name in required_patches}
                extra_plugin_scopes = sorted(
                    name for name in required_plugins if key(name) not in patch_keys)
                if extra_plugin_scopes:
                    errors.append(
                        "requiredPlugins names patches absent from requiredPatches: " +
                        ", ".join(extra_plugin_scopes))
                mods_root = pathlib.Path(instance) / "mods"
                enabled = {key(name) for name in enabled_mods(
                    pathlib.Path(instance), profile)}
                active = active_plugins(pathlib.Path(instance), profile)
                winners = effective_plugins(pathlib.Path(instance), profile)
                try:
                    ledger_document = json.loads(pathlib.Path(ledger_path).read_text(
                        encoding="utf-8-sig"))
                    ledger_rows = ledger_document.get("mods", [])
                    if not isinstance(ledger_document, dict) or not isinstance(
                            ledger_rows, list):
                        raise ValueError("ledger root must contain a mods array")
                except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                    errors.append(
                        "required compatibility patch ledger is unreadable: "
                        f"{type(exc).__name__}: {exc}")
                    ledger_rows = []
                decisions = None
                for name in required_patches:
                    candidate = _direct_child(mods_root, name)
                    if candidate is None:
                        errors.append(
                            "required compatibility patch must be one literal "
                            f"MO2 mod folder name: {name!r}")
                    elif not candidate.is_dir():
                        errors.append(
                            f"required compatibility patch is not installed: {name}")
                        continue
                    matches = [row for row in ledger_rows
                               if isinstance(row, dict) and
                               key(row.get("modName")) == key(name)]
                    if len(matches) != 1:
                        errors.append(
                            f"required compatibility patch must have exactly one "
                            f"ledger row: {name} (found {len(matches)})")
                        continue
                    row = matches[0]
                    if row.get("enabled") is not True or key(name) not in enabled:
                        errors.append(
                            f"required compatibility patch is not active/reconciled: {name}")
                    shipped_plugins = {
                        key(path.name): path for path in plugin_inventory(candidate)
                    }
                    declared_plugins = next(
                        (plugins for patch_name, plugins in required_plugins.items()
                         if key(patch_name) == key(name)), None)
                    if shipped_plugins and not declared_plugins:
                        errors.append(
                            f"required compatibility patch ships plugins but "
                            f"requiredPlugins does not declare them: {name}")
                    for plugin_name in declared_plugins or []:
                        plugin_key = key(plugin_name)
                        shipped = shipped_plugins.get(plugin_key)
                        if shipped is None:
                            errors.append(
                                f"required plugin is not shipped by {name}: {plugin_name}")
                            continue
                        if plugin_key not in active:
                            errors.append(
                                f"required plugin is not active in plugins.txt: {plugin_name}")
                        winner = winners.get(plugin_key)
                        try:
                            is_winner = bool(
                                winner and winner.resolve() == shipped.resolve())
                        except OSError:
                            is_winner = False
                        if not is_winner:
                            errors.append(
                                f"required plugin is shadowed or not the effective "
                                f"winner: {plugin_name} ({name})")
                        disabled = {key(value) for value in
                                    (row.get("disabledPlugins") or [])}
                        if plugin_key in disabled:
                            errors.append(
                                f"required plugin is ledgered as deliberately disabled: "
                                f"{plugin_name} ({name})")
                    try:
                        required_mod_id = int(row.get("modId") or 0)
                    except (TypeError, ValueError):
                        required_mod_id = -1
                    if required_mod_id > 0:
                        if decisions is None:
                            try:
                                decisions = keep_coverage.curator_decisions()
                            except Exception as exc:
                                errors.append(
                                    "required compatibility patch Keep state is unreadable: "
                                    f"{type(exc).__name__}: {exc}")
                                decisions = {}
                        decision = decisions.get(required_mod_id, {})
                        if key(decision.get("status")) != "keep":
                            errors.append(
                                f"required compatibility patch lacks an applied Keep: "
                                f"{name} (Nexus {required_mod_id})")
            if len(str(requirements.get("evidence") or "").strip()) < 12:
                errors.append("intakeReview.requirements requires source/patch evidence")
        compatibility = intake.get("compatibility")
        if not isinstance(compatibility, dict) or compatibility.get("reviewed") is not True:
            errors.append("intakeReview.compatibility.reviewed must be true")
        else:
            if len(str(compatibility.get("lootEvidence") or "").strip()) < 12:
                errors.append("intakeReview.compatibility requires LOOT evidence")
            if len(str(compatibility.get("conflictEvidence") or "").strip()) < 12:
                errors.append("intakeReview.compatibility requires conflict evidence")
            decisions = compatibility.get("openDecisions")
            if not isinstance(decisions, list):
                errors.append("intakeReview.compatibility.openDecisions must be an array")
            elif decisions:
                errors.append("intakeReview.compatibility has unresolved user decisions")

    review = receipt.get("review") or {}
    if not isinstance(review, dict):
        errors.append("receipt review must be an object")
        review = {}
    if not str(review.get("reviewedBy") or "").strip():
        errors.append("receipt review.reviewedBy is required")
    if not str(review.get("reviewedUtc") or "").strip():
        errors.append("receipt review.reviewedUtc is required")
    else:
        try:
            reviewed = dt.datetime.fromisoformat(
                str(review["reviewedUtc"]).replace("Z", "+00:00"))
            if reviewed.tzinfo is None:
                raise ValueError("timezone missing")
        except (TypeError, ValueError):
            errors.append("receipt review.reviewedUtc must be an ISO-8601 timestamp with timezone")
    if not str(review.get("issue") or "").strip():
        errors.append("receipt review.issue is required")
    elif key(review.get("issue")) != key((current.get("source") or {}).get("issue")):
        errors.append("receipt review.issue does not match the transaction issue")

    current_artifacts = current.get("artifacts", [])
    receipt_artifacts = receipt.get("artifacts", [])
    if not isinstance(receipt_artifacts, list) or not all(
            isinstance(row, dict) for row in receipt_artifacts):
        errors.append("receipt artifacts must be an array of objects")
        receipt_artifacts = []
    current_rows = {key(row.get("artifact")): row for row in current_artifacts}
    receipt_rows = {key(row.get("artifact")): row for row in receipt_artifacts}
    if len(receipt_rows) != len(receipt_artifacts):
        errors.append("receipt artifact names must be non-blank and unique")
    missing = sorted(set(current_rows) - set(receipt_rows))
    extra = sorted(set(receipt_rows) - set(current_rows))
    if missing:
        errors.append("receipt omits artifact(s): " + ", ".join(missing))
    if extra:
        errors.append("receipt contains unknown artifact(s): " + ", ".join(extra))

    sha_pattern = re.compile(r"^[0-9a-fA-F]{64}$")
    for artifact_key in sorted(set(current_rows) & set(receipt_rows)):
        row = receipt_rows[artifact_key]
        outcome = key(row.get("outcome"))
        if outcome not in OUTCOMES:
            errors.append(f"{row.get('artifact')}: invalid or missing outcome")
            continue
        if outcome == "blocked-decision":
            errors.append(f"{row.get('artifact')}: blocked-decision is not an acceptance outcome")
        evidence = str(row.get("evidence") or "").strip()
        if len(evidence) < 12:
            errors.append(f"{row.get('artifact')}: evidence is missing or too vague")
        output_hashes = row.get("outputHashes") or []
        if not isinstance(output_hashes, list) or not all(
                isinstance(output, dict) for output in output_hashes):
            errors.append(f"{row.get('artifact')}: outputHashes must be an array of objects")
            output_hashes = []
        if outcome in {"regenerated", "amended"} and not output_hashes:
            errors.append(f"{row.get('artifact')}: {outcome} requires exact outputHashes")
        artifact_root = (pathlib.Path(instance) / "mods" /
                         str(row.get("artifact") or "")).resolve()
        for output in output_hashes:
            if not str(output.get("path") or "").strip() or not sha_pattern.fullmatch(
                    str(output.get("sha256") or "")):
                errors.append(f"{row.get('artifact')}: invalid output hash receipt")
                continue
            path = pathlib.Path(str(output["path"]))
            if not path.is_absolute():
                path = artifact_root / path
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                errors.append(
                    f"{row.get('artifact')}: output is missing/unreadable: {path} ({exc})")
                continue
            if not _within(resolved, artifact_root):
                errors.append(
                    f"{row.get('artifact')}: output is not owned by that artifact: {resolved}")
                continue
            if not resolved.is_file() or sha256_file(resolved) != str(output["sha256"]).upper():
                errors.append(f"{row.get('artifact')}: output hash does not match: {resolved}")
        if current_rows[artifact_key].get("patchParseErrors"):
            errors.append(f"{row.get('artifact')}: patch parse errors prevent acceptance")

    if current.get("changedPluginParseErrors"):
        errors.append("changed plugin parse errors prevent receipt acceptance")
    return errors


def render(result: dict, validation_errors: list[str] | None = None) -> str:
    s = result["summary"]
    lines = [
        f"operation {result['operation']}; changed: " + ", ".join(row["name"] for row in result["changed"]),
        f"owned artifacts {s['ownedArtifactsReviewed']}; candidate impacts {s['candidateImpacts']}; "
        f"policy gaps {s['impactPolicyGaps']}",
    ]
    for row in result["artifacts"]:
        reason = "; ".join(row["reasons"]) or "no automatic relationship observed"
        lines.append(f"  {row['disposition']:<36} {row['artifact']}: {reason}")
    lines.append("")
    if validation_errors is None:
        lines.append("INCOMPLETE: assign one evidenced outcome to every artifact before activation (#228)")
    elif validation_errors:
        lines.append("RECEIPT REJECTED:")
        lines += [f"  - {error}" for error in validation_errors]
    else:
        lines.append("RECEIPT COMPLETE: every owned artifact has a current evidenced outcome")
    return "\n".join(lines)


def selftest() -> int:
    reasons, manual = evaluate_policy(
        {"mode": "record-types", "recordTypes": ["WEAP"]}, {"new weapons.esp"}, {"WEAP"}, []
    )
    assert not manual and any("WEAP" in reason for reason in reasons)
    reasons, manual = evaluate_policy(
        {"mode": "asset-paths", "assetGlobs": ["meshes/weapons/**"]}, set(), set(),
        ["meshes/weapons/test.nif", "textures/a.dds"],
    )
    assert not manual and any("test.nif" in reason for reason in reasons)
    reasons, manual = evaluate_policy({"mode": "full-profile"}, set(), set(), [])
    assert reasons == ["impactPolicy is full-profile"] and not manual
    reasons, manual = evaluate_policy(None, set(), set(), [])
    assert manual and reasons == ["impactPolicy missing"]
    reasons, manual = evaluate_policy({"mode": "typo"}, set(), set(), [])
    assert manual and any("invalid mode" in reason for reason in reasons)
    for mode, field in (("declared-inputs", "inputs"),
                        ("record-types", "recordTypes"),
                        ("asset-paths", "assetGlobs")):
        reasons, manual = evaluate_policy({"mode": mode}, set(), set(), [])
        assert manual and any(field in reason for reason in reasons)
    with tempfile.TemporaryDirectory(prefix="patch-impact-") as raw:
        root = pathlib.Path(raw)
        (root / "payload.bin").write_bytes(b"payload")
        (root / "meta.ini").write_text("installedAt=one\n", encoding="utf-8")
        first = changed_fingerprint([("Fixture", root)])
        (root / "meta.ini").write_text("installedAt=two\n", encoding="utf-8")
        second = changed_fingerprint([("Fixture", root)])
        assert first == second and first["files"] == 1
        instance = root / "instance"
        (instance / "profiles" / "Default").mkdir(parents=True)
        (instance / "mods" / "A").mkdir(parents=True)
        (instance / "overwrite").mkdir()
        (instance / "profiles" / "Default" / "modlist.txt").write_text(
            "+A\n", encoding="utf-8")
        (instance / "mods" / "A" / "Same.esp").write_bytes(b"managed")
        (instance / "overwrite" / "Same.esp").write_bytes(b"overwrite")
        assert effective_plugins(instance, "Default", root / "no-data")["same.esp"] == \
            instance / "overwrite" / "Same.esp"
        ledger = root / "ledger.json"
        ledger.write_text(json.dumps({"mods": [{
            "modId": 0, "modName": "Ensrick Disabled Patch", "enabled": False,
        }]}), encoding="utf-8")
        assert [row["modName"] for row in owned_rows(ledger)] == \
            ["Ensrick Disabled Patch"]

        changed = instance / "mods" / "Changed Fixture"
        owned = instance / "mods" / "Ensrick Disabled Patch"
        changed.mkdir()
        owned.mkdir()
        changed_plugin = changed / "Changed.esp"
        owned_plugin = owned / "Same.esp"
        changed_plugin.write_bytes(b"changed")
        owned_plugin.write_bytes(b"owned")
        ledger.write_text(json.dumps({"mods": [{
            "modId": 0,
            "modName": "Ensrick Disabled Patch",
            "enabled": False,
            "impactPolicy": {"mode": "declared-inputs", "inputs": ["unrelated"]},
        }]}), encoding="utf-8")
        original_record_keys = globals()["record_keys"]
        original_relative_assets = globals()["relative_assets"]
        original_repo = globals()["REPO"]
        parsed = []

        def fixture_record_keys(path):
            path = pathlib.Path(path)
            parsed.append(path)
            if path == changed_plugin:
                return {("WEAP", "base.esm", 1)}, {"WEAP"}, []
            if path == owned_plugin:
                return {("WEAP", "base.esm", 1)}, {"WEAP"}, ["Changed.esp"]
            return set(), set(), []

        try:
            globals()["record_keys"] = fixture_record_keys
            globals()["relative_assets"] = lambda _root: []
            globals()["REPO"] = root
            relationship = audit(
                "install", [], ["Changed Fixture"], instance, "Default", ledger)
        finally:
            globals()["record_keys"] = original_record_keys
            globals()["relative_assets"] = original_relative_assets
            globals()["REPO"] = original_repo
        assert parsed == [changed_plugin, owned_plugin], parsed
        assert any("hard master" in reason for reason in
                   relationship["artifacts"][0]["reasons"])
        assert any("record overlap" in reason for reason in
                   relationship["artifacts"][0]["reasons"])

    current = {
        "schemaVersion": 1,
        "operation": "install",
        "source": {"issue": "#228"},
        "changedFingerprint": {"sha256": "A" * 64},
        "changedPlugins": [],
        "changedRecordTypes": [],
        "changedPluginParseErrors": [],
        "artifacts": [{
            "artifact": "Owned Patch",
            "artifactFingerprint": {"sha256": "C" * 64, "files": 1, "bytes": 7},
            "sourceBuildRecord": None,
            "impactPolicy": {"mode": "manual"},
            "disposition": "manual-review-required",
            "reasons": ["impactPolicy requires manual review"],
            "patchParseErrors": [],
        }],
    }
    current["auditSignature"] = audit_signature(current)
    receipt = json.loads(json.dumps(current))
    receipt["review"] = {
        "reviewedBy": "fixture reviewer",
        "reviewedUtc": "2026-09-04T00:00:00Z",
        "issue": "#228",
    }
    receipt["artifacts"][0].update({
        "outcome": "not-affected",
        "evidence": "Fixture inputs are disjoint by exact record and asset scope.",
        "outputHashes": [],
    })
    assert validate_receipt(current, receipt) == []
    receipt["changedFingerprint"]["sha256"] = "B" * 64
    assert any("fingerprint" in error for error in validate_receipt(current, receipt))
    receipt["changedFingerprint"]["sha256"] = "A" * 64
    receipt["artifacts"][0]["outcome"] = "blocked-decision"
    assert any("blocked-decision" in error for error in validate_receipt(current, receipt))
    receipt["artifacts"][0]["outcome"] = "not-affected"
    changed_artifact = json.loads(json.dumps(current))
    changed_artifact["artifacts"][0]["artifactFingerprint"]["sha256"] = "D" * 64
    changed_artifact["auditSignature"] = audit_signature(changed_artifact)
    assert any("stale" in error for error in validate_receipt(changed_artifact, receipt))
    changed_manifest = json.loads(json.dumps(current))
    changed_manifest["artifacts"][0]["sourceBuildRecordSha256"] = "E" * 64
    assert audit_signature(changed_manifest) != current["auditSignature"]
    nexus_current = json.loads(json.dumps(current))
    nexus_current["source"] = {"modId": 42, "issue": "#228"}
    nexus_current["auditSignature"] = audit_signature(nexus_current)
    nexus_receipt = json.loads(json.dumps(receipt))
    nexus_receipt["source"] = nexus_current["source"]
    nexus_receipt["auditSignature"] = nexus_current["auditSignature"]
    assert any("userApproval" in error for error in
               validate_receipt(nexus_current, nexus_receipt))
    nexus_receipt["intakeReview"] = {
        "userApproval": {"approved": True,
                         "evidence": "user request linked on issue #228"},
        "fileSelection": {"reviewed": True,
                          "evidence": "exact main file 42 selected"},
        "permissions": {"classification": "external-download",
                        "evidence": "vendor archive remains external"},
        "requirements": {"reviewed": True, "requiredPatches": [],
                         "requiredPlugins": {},
                         "evidence": "requirements and files reviewed"},
        "compatibility": {"reviewed": True,
                          "lootEvidence": "fixture LOOT report is clean",
                          "conflictEvidence": "fixture conflict delta is empty",
                          "openDecisions": []},
    }
    assert validate_receipt(nexus_current, nexus_receipt) == []
    with tempfile.TemporaryDirectory(prefix="required-patch-owner-") as raw:
        instance = pathlib.Path(raw) / "instance"
        required = instance / "mods" / "Required Patch"
        required.mkdir(parents=True)
        (required / "Required Patch.esp").write_bytes(b"fixture plugin")
        profile_dir = instance / "profiles" / "Default"
        profile_dir.mkdir(parents=True)
        (profile_dir / "modlist.txt").write_text(
            "+Required Patch\n", encoding="utf-8")
        (profile_dir / "plugins.txt").write_text(
            "*Required Patch.esp\n", encoding="utf-8")
        ledger = pathlib.Path(raw) / "ledger.json"
        ledger.write_text(json.dumps({"mods": [{
            "modName": "Required Patch", "modId": 0, "enabled": True,
            "plugins": ["Required Patch.esp"],
        }]}), encoding="utf-8")
        nexus_receipt["intakeReview"]["requirements"]["requiredPatches"] = [
            "Required Patch"
        ]
        nexus_receipt["intakeReview"]["requirements"]["requiredPlugins"] = {
            "Required Patch": ["Required Patch.esp"]
        }
        assert validate_receipt(
            nexus_current, nexus_receipt, instance=instance,
            ledger_path=ledger) == []
        (profile_dir / "plugins.txt").write_text("", encoding="utf-8")
        assert any("required plugin is not active" in error for error in
                   validate_receipt(nexus_current, nexus_receipt,
                                    instance=instance, ledger_path=ledger))
        (profile_dir / "plugins.txt").write_text(
            "*Required Patch.esp\n", encoding="utf-8")
        nexus_receipt["intakeReview"]["requirements"]["requiredPatches"] = [
            "../.."
        ]
        assert any("literal MO2 mod folder name" in error for error in
                   validate_receipt(nexus_current, nexus_receipt,
                                    instance=instance, ledger_path=ledger))
    with tempfile.TemporaryDirectory(prefix="patch-output-owner-") as raw:
        root = pathlib.Path(raw)
        owned = root / "instance" / "mods" / "Owned Patch"
        owned.mkdir(parents=True)
        output = owned / "output.esl"
        output.write_bytes(b"owned")
        unrelated = root / "unrelated.esl"
        unrelated.write_bytes(b"foreign")
        receipt["artifacts"][0].update({
            "outcome": "amended",
            "outputHashes": [{"path": str(unrelated),
                              "sha256": sha256_file(unrelated)}],
        })
        assert any("not owned" in error for error in validate_receipt(
            current, receipt, instance=root / "instance"))
        receipt["artifacts"][0]["outputHashes"] = [
            {"path": "output.esl", "sha256": sha256_file(output)}
        ]
        assert validate_receipt(current, receipt, instance=root / "instance") == []
    with tempfile.TemporaryDirectory(prefix="patch-cli-instance-") as raw:
        root = pathlib.Path(raw)
        selected_instance = root / "selected-instance"
        receipt_path = root / "receipt.json"
        receipt_path.write_text("{}\n", encoding="utf-8")
        captured = {}
        original_audit = globals()["audit"]
        original_validate = globals()["validate_receipt"]

        def fixture_audit(*_args, **_kwargs):
            return {"summary": {"receiptComplete": False}}

        def fixture_validate(_current, _receipt, repo_root=REPO,
                             instance=INSTANCE):
            captured["instance"] = pathlib.Path(instance)
            return []

        try:
            globals()["audit"] = fixture_audit
            globals()["validate_receipt"] = fixture_validate
            assert main([
                "--operation", "install",
                "--instance", str(selected_instance),
                "--receipt", str(receipt_path),
                "--json",
            ]) == 0
        finally:
            globals()["audit"] = original_audit
            globals()["validate_receipt"] = original_validate
        assert captured["instance"] == selected_instance
    print("patch_impact selftest PASS (32 assertions)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=False,
                        choices=("install", "update", "remove", "enable", "disable",
                                 "generate", "config", "order", "fomod-reselect"))
    parser.add_argument("--changed-mod", action="append", default=[])
    parser.add_argument("--changed-root", action="append", type=pathlib.Path, default=[])
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument("--ledger", type=pathlib.Path, default=LEDGER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path,
                        help="reviewed receipt to validate against a fresh audit")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.operation:
        parser.error("--operation is required")
    result = audit(args.operation, args.changed_root, args.changed_mod,
                   args.instance, args.profile, args.ledger)
    validation_errors = None
    if args.receipt:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
        validation_errors = validate_receipt(
            result, receipt, instance=args.instance)
        result["summary"]["receiptComplete"] = not validation_errors
        result["receiptValidationErrors"] = validation_errors
    text = (json.dumps(result, indent=2) + "\n" if args.json or args.out else
            render(result, validation_errors) + "\n")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    # A scan is intentionally incomplete until a reviewed receipt assigns the
    # final outcomes. Exit 2 distinguishes that from a tool failure.
    return 0 if validation_errors == [] else 2


if __name__ == "__main__":
    raise SystemExit(main())
