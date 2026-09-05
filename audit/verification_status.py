"""Validate durable test plans linked from the installed-mod ledger.

A plan is not a test result.  This gate binds every post-doctrine install to
the current build fingerprint and requires structured, evidenced stage results
before it can be called technically verified or playtest-accepted.

It is read-only.  The fresh-character/runtime harness owns result writes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import verification_plan


REPO = pathlib.Path(__file__).resolve().parent.parent
LEDGER = REPO / "records" / "installed-mods.json"
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
POLICY_EPOCH = dt.datetime(2026, 9, 4, tzinfo=dt.timezone.utc)
FINAL_STATES = {"technical-pass", "playtest-accepted"}
FAIL_STATES = {"failed", "aborted"}
STAGE_PASS = {"pass"}
HEX_256 = re.compile(r"[0-9A-F]{64}")


def _parse_utc(value):
    try:
        parsed = dt.datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def _evidence_valid(value):
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and len(item.strip()) >= 6 for item in value)


def _sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _confined_evidence_file(repo, value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} path is required")
    raw = pathlib.Path(value)
    if raw.is_absolute():
        raise ValueError(f"{label} must be repository-relative")
    repo = pathlib.Path(repo).resolve(strict=True)
    records = (repo / "records").resolve(strict=True)
    try:
        path = (repo / raw).resolve(strict=True)
        path.relative_to(records)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{label} must be an existing file beneath records/") from exc
    if not path.is_file():
        raise ValueError(f"{label} is not a file")
    canonical = path.relative_to(repo).as_posix()
    if canonical != value:
        raise ValueError(f"{label} path is not canonical: {value}")
    return path


def _receipt_artifact_references(receipt, repo, label):
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"{label} receipt artifacts must be an array")
    references = []
    for index, entry in enumerate(artifacts, 1):
        if isinstance(entry, str):
            reference = entry
            declared_hash = None
        elif isinstance(entry, dict):
            reference = entry.get("path")
            declared_hash = str(entry.get("sha256") or "").strip().upper() or None
            if declared_hash is not None and not HEX_256.fullmatch(declared_hash):
                raise ValueError(f"{label} receipt artifact {index} SHA-256 is invalid")
        else:
            raise ValueError(f"{label} receipt artifact {index} is invalid")
        path = _confined_evidence_file(
            repo, reference, f"{label} receipt artifact {index}")
        references.append((path.relative_to(pathlib.Path(repo).resolve()).as_posix(),
                           declared_hash))
    return references


def _validate_recorded_result(plan, row, repo, plan_path, ledger_path,
                              label, result_type, identity):
    """Revalidate one writer-shaped result and every immutable artifact byte."""
    errors = []
    if not isinstance(row, dict):
        return [f"{label}: result must be an object"]
    status = str(row.get("status") or "").casefold()
    if status not in {"pass", "fail"}:
        return [f"{label}: result status must be pass or fail"]
    observed = _parse_utc(row.get("observedUtc"))
    if observed is None:
        errors.append(f"{label}: observedUtc must be a timezone-aware timestamp")
    summary = str(row.get("summary") or "").strip()
    if len(summary) < 6:
        errors.append(f"{label}: result summary must be substantive")
    references = row.get("evidence")
    metadata = row.get("evidenceArtifacts")
    if not isinstance(references, list) or not references or not all(
            isinstance(item, str) and item for item in references):
        errors.append(f"{label}: writer-shaped evidence paths are required")
        return errors
    if not isinstance(metadata, list) or len(metadata) != len(references):
        errors.append(f"{label}: writer-shaped evidenceArtifacts are required")
        return errors

    repo = pathlib.Path(repo).resolve()
    forbidden = {
        os.path.normcase(str(pathlib.Path(plan_path).resolve())),
        os.path.normcase(str(pathlib.Path(ledger_path).resolve())),
    }
    paths = []
    seen = set()
    receipt_payload = None
    for index, (reference, record) in enumerate(zip(references, metadata), 1):
        item_label = f"{label} evidence {index}"
        if not isinstance(record, dict) or record.get("path") != reference:
            errors.append(f"{item_label}: artifact metadata/path mismatch")
            continue
        size = record.get("bytes")
        digest = str(record.get("sha256") or "").strip().upper()
        if (not isinstance(size, int) or isinstance(size, bool) or size < 0 or
                not HEX_256.fullmatch(digest)):
            errors.append(f"{item_label}: artifact bytes/SHA-256 metadata is invalid")
            continue
        try:
            path = _confined_evidence_file(repo, reference, item_label)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        key = os.path.normcase(str(path))
        if key in forbidden:
            errors.append(f"{item_label}: a plan or ledger cannot be evidence")
            continue
        if key in seen:
            errors.append(f"{item_label}: duplicate evidence path")
            continue
        seen.add(key)
        try:
            if index == 1:
                payload = path.read_bytes()
                actual_size = len(payload)
                actual_hash = hashlib.sha256(payload).hexdigest().upper()
            else:
                payload = None
                actual_size = path.stat().st_size
                actual_hash = _sha256_file(path)
        except OSError as exc:
            errors.append(f"{item_label}: artifact became unreadable: {exc}")
            continue
        if actual_size != size or actual_hash != digest:
            errors.append(f"{item_label}: artifact bytes changed after ingestion")
            continue
        if index == 1:
            receipt_payload = payload
        paths.append(path)

    if len(paths) != len(references):
        return errors
    if result_type != "human-acceptance" and status == "pass" and len(paths) < 2:
        errors.append(f"{label}: automated pass requires an external diagnostic artifact")

    try:
        receipt = json.loads(receipt_payload.decode("utf-8-sig"))
        if not isinstance(receipt, dict):
            raise ValueError("receipt root is not an object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{label}: evidence receipt is unreadable: {exc}")
        return errors
    plan_relative = pathlib.Path(plan_path).resolve().relative_to(repo).as_posix()
    common = {
        "schemaVersion": 1,
        "verificationPlan": plan_relative,
        "testId": plan.get("testId"),
        "contractSignature": plan.get("contractSignature"),
    }
    for field, expected in common.items():
        if receipt.get(field) != expected:
            errors.append(f"{label}: evidence receipt {field} does not match the result")
    if str(receipt.get("summary") or "").strip() != summary:
        errors.append(f"{label}: evidence receipt summary does not match the result")
    if str(receipt.get("status") or "").casefold() != status:
        errors.append(f"{label}: evidence receipt status does not match the result")
    receipt_fingerprint = receipt.get("buildFingerprint")
    plan_fingerprint = plan.get("buildFingerprint")
    if (not isinstance(receipt_fingerprint, dict) or
            not isinstance(plan_fingerprint, dict) or
            receipt_fingerprint.get("algorithm") != plan_fingerprint.get("algorithm") or
            str(receipt_fingerprint.get("sha256") or "").upper() !=
            str(plan_fingerprint.get("sha256") or "").upper()):
        errors.append(f"{label}: evidence receipt buildFingerprint does not match")
    receipt_observed = _parse_utc(receipt.get("observedUtc"))
    if observed is None or receipt_observed is None or receipt_observed != observed:
        errors.append(f"{label}: evidence receipt observedUtc does not match the result")

    if result_type == "stage":
        if (str(receipt.get("resultType") or "").casefold() != "stage" or
                receipt.get("stage") != identity):
            errors.append(f"{label}: evidence receipt does not attest this stage")
        if identity == "V2-fresh-start":
            fresh = plan.get("freshCharacter")
            expected_character = str(
                fresh.get("testCharacterId") or "").strip() \
                if isinstance(fresh, dict) else ""
            if (not expected_character or
                    str(row.get("testCharacterId") or "").strip() != expected_character or
                    str(receipt.get("testCharacterId") or "").strip() != expected_character):
                errors.append(
                    f"{label}: receipt/result/fresh-character identity does not match")
    elif result_type == "cycle":
        if (str(receipt.get("resultType") or "").casefold() != "cycle" or
                receipt.get("cycle") != identity):
            errors.append(f"{label}: evidence receipt does not attest this cycle")
        if row.get("cycle") != identity:
            errors.append(f"{label}: recorded cycle number is inconsistent")
        if receipt.get("testCharacterId") != row.get("testCharacterId"):
            errors.append(f"{label}: receipt testCharacterId does not match the cycle")
    else:
        accepted_by = str(receipt.get("acceptedBy") or "").strip()
        if (str(receipt.get("resultType") or "").casefold() != "human-acceptance" or
                receipt.get("stage") != "V7-human-play"):
            errors.append(f"{label}: a separate human-acceptance receipt is required")
        if len(accepted_by) < 2 or row.get("acceptedBy") != accepted_by:
            errors.append(f"{label}: acceptedBy is missing or does not match")

    try:
        receipt_artifacts = _receipt_artifact_references(receipt, repo, label)
        recorded_external = [path.relative_to(repo).as_posix() for path in paths[1:]]
        if [reference for reference, _digest in receipt_artifacts] != recorded_external:
            errors.append(f"{label}: receipt artifact list does not match recorded evidence")
        for index, (_reference, declared_hash) in enumerate(receipt_artifacts, 1):
            if index >= len(metadata) or not isinstance(metadata[index], dict):
                continue
            if (declared_hash is not None and declared_hash !=
                    str(metadata[index].get("sha256") or "").upper()):
                errors.append(
                    f"{label}: receipt artifact {index} SHA-256 does not match metadata")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def validate_result_evidence(plan, repo, plan_path, ledger_path):
    """Validate durable result receipts for normal preflight/status reads.

    The result writer is not the trust boundary by itself: artifacts can be
    changed after its final write, and result/status fields are intentionally
    outside the immutable test-contract signature. Every normal gate therefore
    re-opens and hashes the writer-shaped evidence.
    """
    if not isinstance(plan, dict):
        return ["plan root must be a JSON object"]
    results = plan.get("results")
    if not isinstance(results, dict):
        return []
    errors = []
    stages = results.get("stages")
    if isinstance(stages, dict):
        for stage, row in stages.items():
            kind = "human-acceptance" if stage == "V7-human-play" else "stage"
            errors.extend(_validate_recorded_result(
                plan, row, repo, plan_path, ledger_path,
                f"stage {stage}", kind, stage))
    cycles = results.get("cycles")
    if isinstance(cycles, list):
        for index, row in enumerate(cycles, 1):
            errors.extend(_validate_recorded_result(
                plan, row, repo, plan_path, ledger_path,
                f"cycle {index}", "cycle", index))
    return errors


def validate_plan(plan, current_fingerprint, expected_signature=None,
                  expected_test_id=None, expected_issue=None,
                  expected_source=None):
    errors = []
    pending = []
    if not isinstance(plan, dict):
        return ["plan root must be a JSON object"], pending
    if plan.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if not re.fullmatch(r"SVT-[A-Za-z0-9-]+", str(plan.get("testId") or "")):
        errors.append("testId is missing or invalid")
    if expected_test_id and plan.get("testId") != expected_test_id:
        errors.append("testId does not match the ledger transaction")
    signature = plan.get("contractSignature")
    if signature != verification_plan.contract_signature(plan):
        errors.append("immutable verification contract was edited after generation")
    if expected_signature and signature != expected_signature:
        errors.append("verification contract signature does not match the ledger transaction")
    if expected_issue and str(plan.get("issue") or "") != str(expected_issue):
        errors.append("verification issue does not match the ledger transaction")
    if expected_source:
        source = plan.get("source") if isinstance(plan.get("source"), dict) else {}
        for field, expected in expected_source.items():
            if source.get(field) != expected:
                errors.append(f"verification source.{field} does not match the ledger transaction")

    try:
        required_contract = verification_plan.requirements(
            plan.get("changeKinds"), plan.get("crashFix") is True)
        if plan.get("changeKinds") != required_contract["kinds"]:
            errors.append("changeKinds must be normalized and unique")
        if plan.get("riskClass") != required_contract["risk"]:
            errors.append("riskClass was weakened or is inconsistent with changeKinds")
        if plan.get("cyclesRequired") != required_contract["cycles"]:
            errors.append("cyclesRequired was weakened or is inconsistent with changeKinds/crashFix")
        if plan.get("stagesRequired") != required_contract["stages"]:
            errors.append("stagesRequired was weakened or is inconsistent with changeKinds/crashFix")
    except (TypeError, ValueError) as exc:
        errors.append(f"invalid change contract: {exc}")
    fingerprint = plan.get("buildFingerprint")
    if not isinstance(fingerprint, dict):
        errors.append("buildFingerprint is required")
    elif (fingerprint.get("algorithm") != current_fingerprint.get("algorithm") or
          fingerprint.get("sha256") != current_fingerprint.get("sha256")):
        errors.append("buildFingerprint is stale or belongs to another build")

    stages = plan.get("stagesRequired")
    if not isinstance(stages, list) or not stages or not all(
            isinstance(stage, str) and stage for stage in stages):
        errors.append("stagesRequired must be a non-empty array of names")
        stages = []
    results = plan.get("results")
    stage_results = results.get("stages") if isinstance(results, dict) else None
    if not isinstance(stage_results, dict):
        stage_results = {}
    for stage in stages:
        row = stage_results.get(stage)
        if not isinstance(row, dict):
            pending.append(f"{stage}: no result")
            continue
        status = str(row.get("status") or "").casefold()
        if status not in STAGE_PASS:
            pending.append(f"{stage}: {status or 'no status'}")
            continue
        if not _evidence_valid(row.get("evidence")):
            errors.append(f"{stage}: passing result requires substantive evidence")

    if "V2-fresh-start" in stages:
        fresh = plan.get("freshCharacter")
        if not isinstance(fresh, dict) or not str(fresh.get("testCharacterId") or "").strip():
            pending.append("V2-fresh-start: unique testCharacterId not recorded")

    cycles_required = plan.get("cyclesRequired")
    if not isinstance(cycles_required, int) or isinstance(cycles_required, bool) or cycles_required < 1:
        errors.append("cyclesRequired must be a positive integer")
        cycles_required = 1
    cycles = results.get("cycles") if isinstance(results, dict) else None
    if not isinstance(cycles, list):
        cycles = []
    passed_cycle_ids = set()
    for index, cycle in enumerate(cycles, 1):
        if not isinstance(cycle, dict):
            errors.append(f"cycle {index}: result must be an object")
            continue
        identity = str(cycle.get("testCharacterId") or "").strip()
        if not identity:
            errors.append(f"cycle {index}: testCharacterId is required")
        elif identity in passed_cycle_ids:
            errors.append(f"cycle {index}: testCharacterId is not unique")
        else:
            passed_cycle_ids.add(identity)
        if str(cycle.get("status") or "").casefold() != "pass":
            pending.append(f"cycle {index}: not passed")
        elif not _evidence_valid(cycle.get("evidence")):
            errors.append(f"cycle {index}: passing cycle requires substantive evidence")
    if len(cycles) < cycles_required:
        pending.append(f"cycles: {len(cycles)}/{cycles_required} recorded")

    status = str(plan.get("status") or "").casefold()
    if status in FAIL_STATES:
        errors.append(f"plan status is {status}")
    if status == "playtest-accepted":
        human = stage_results.get("V7-human-play", {})
        if human.get("status") != "pass" or not _evidence_valid(human.get("evidence")):
            errors.append("playtest-accepted requires evidenced V7-human-play pass")
        if pending:
            errors.append("playtest-accepted has incomplete required stages/cycles")
    elif status == "technical-pass":
        technical_pending = [item for item in pending
                             if not item.startswith("V7-human-play:")]
        if technical_pending:
            errors.append("technical-pass has incomplete technical stages")
    elif status in {"planned", "running"}:
        pending.append(f"plan status is {status}")
    elif status not in {*FAIL_STATES, *FINAL_STATES}:
        errors.append("plan status is invalid")
    return errors, pending


def _managed_plan_source(plan):
    """Return a lifecycle-owned source descriptor, or ``None``.

    Install/update plans are ledger transactions, not free-floating notes.  A
    ledger edit which deletes ``verificationPlan`` must therefore leave an
    orphan that normal status/preflight can still detect.
    """
    source = plan.get("source") if isinstance(plan, dict) else None
    if not isinstance(source, dict):
        return None
    if (str(source.get("operation") or "").casefold() not in {"install", "update"}
            or str(source.get("game") or "").casefold() != "skyrimspecialedition"):
        return None
    return source


def _source_matches_ledger(source, row):
    if not isinstance(row, dict):
        return False
    return (
        str(row.get("modName") or "").casefold() ==
        str(source.get("modName") or "").casefold()
        and str(row.get("modId") or "") == str(source.get("modId") or "")
        and str(row.get("fileId") or "") == str(source.get("fileId") or "")
        and str(row.get("sha256") or "").upper() ==
        str(source.get("archiveSha256") or "").upper()
        and source.get("fomodPlan") == row.get("fomodPlan")
        and str(source.get("fomodPlanSha256") or "").upper() ==
        str(row.get("fomodPlanSha256") or "").upper()
    )


def _validate_fomod_binding(repo, row):
    """Validate an optional FOMOD plan as exact, confined provenance."""
    reference = str(row.get("fomodPlan") or "").strip()
    declared = str(row.get("fomodPlanSha256") or "").strip().upper()
    if not reference and not declared:
        return []
    if not reference or not HEX_256.fullmatch(declared):
        return ["FOMOD plan reference and SHA-256 must both be present"]
    raw = pathlib.Path(reference)
    if raw.is_absolute():
        return ["FOMOD plan must be repository-relative"]
    root = (pathlib.Path(repo) / "records" / "fomod-plans").resolve()
    try:
        path = (pathlib.Path(repo) / raw).resolve(strict=True)
        path.relative_to(root)
    except (OSError, ValueError):
        return ["FOMOD plan must be an existing file beneath records/fomod-plans"]
    if not path.is_file():
        return ["FOMOD plan is not a regular file"]
    try:
        actual = _sha256_file(path)
    except OSError as exc:
        return [f"FOMOD plan is unreadable: {exc}"]
    return [] if actual == declared else ["FOMOD plan SHA-256 does not match the ledger"]


def audit(repo=REPO, instance=INSTANCE, profile=PROFILE, ledger_path=LEDGER,
          current_fingerprint=None):
    repo = pathlib.Path(repo)
    ledger_path = pathlib.Path(ledger_path)
    document = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict) or not isinstance(document.get("mods"), list):
        raise ValueError("installed-mod ledger must be an object with a mods array")
    has_referenced_plan = any(
        isinstance(mod, dict) and str(mod.get("verificationPlan") or "").strip()
        for mod in document["mods"]
    )
    fingerprint = current_fingerprint
    if has_referenced_plan and fingerprint is None:
        fingerprint = verification_plan.build_fingerprint(
            pathlib.Path(instance), profile, ledger_path)
    rows = []
    plan_root = (repo / "records" / "test-plans").resolve()
    references = {}
    for mod in document["mods"]:
        if not isinstance(mod, dict):
            continue
        reference = str(mod.get("verificationPlan") or "").strip()
        if not reference:
            continue
        try:
            resolved = (repo / reference).resolve()
            resolved.relative_to(plan_root)
        except ValueError:
            continue
        references.setdefault(os.path.normcase(str(resolved)), []).append(mod)
    for mod in document["mods"]:
        if not isinstance(mod, dict):
            continue
        pre_errors = []
        raw_installed = str(mod.get("installedUtc") or "").strip()
        installed = _parse_utc(raw_installed)
        if raw_installed and installed is None:
            pre_errors.append("installedUtc is malformed or lacks a timezone")
        managed = bool(mod.get("lifecyclePolicyVersion") or
                       mod.get("lifecycleOperation") or
                       mod.get("impactReceipt") or mod.get("verificationPlan") or
                       mod.get("verificationTestId") or
                       mod.get("verificationContractSignature"))
        required = managed or bool(installed and installed >= POLICY_EPOCH)
        if required:
            for field in ("lifecyclePolicyVersion", "lifecycleOperation", "issue",
                          "impactReceipt", "impactReceiptSha256",
                          "verificationPlan", "verificationTestId",
                          "verificationContractSignature"):
                if not mod.get(field):
                    pre_errors.append(f"post-policy ledger row is missing {field}")
        pre_errors += _validate_fomod_binding(repo, mod)
        reference = str(mod.get("verificationPlan") or "").strip()
        if not reference:
            if required or pre_errors:
                rows.append({"modName": mod.get("modName"), "state": "invalid",
                             "errors": pre_errors or
                                       ["post-policy install has no verificationPlan"],
                             "pending": []})
            continue
        path = (repo / reference).resolve()
        try:
            path.relative_to(plan_root)
        except ValueError:
            rows.append({"modName": mod.get("modName"), "state": "invalid",
                         "errors": ["verificationPlan escapes records/test-plans"],
                         "pending": [], "path": str(path)})
            continue
        try:
            plan = json.loads(path.read_text(encoding="utf-8-sig"))
            expected_source = {
                "operation": mod.get("lifecycleOperation"),
                "game": "skyrimspecialedition",
                "modName": mod.get("modName"),
                "modId": mod.get("modId"),
                "fileId": mod.get("fileId"),
                "archiveSha256": str(mod.get("sha256") or "").upper(),
                "impactReceipt": mod.get("impactReceipt"),
                "impactReceiptSha256": mod.get("impactReceiptSha256"),
                **({"fomodPlan": mod.get("fomodPlan"),
                    "fomodPlanSha256": mod.get("fomodPlanSha256")}
                   if mod.get("fomodPlan") or mod.get("fomodPlanSha256") else {}),
            }
            errors, pending = validate_plan(
                plan, fingerprint,
                expected_signature=mod.get("verificationContractSignature"),
                expected_test_id=mod.get("verificationTestId"),
                expected_issue=mod.get("issue"),
                expected_source=expected_source,
            )
            errors += validate_result_evidence(
                plan, repo, path, ledger_path)
            errors = pre_errors + errors
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors, pending = [f"plan unreadable: {type(exc).__name__}: {exc}"], []
            plan = {}
        state = "invalid" if errors else ("pending" if pending else "complete")
        rows.append({"modName": mod.get("modName"), "state": state,
                     "errors": errors, "pending": pending, "path": str(path),
                     "testId": plan.get("testId") if isinstance(plan, dict) else None,
                      "planStatus": (str(plan.get("status") or "").casefold()
                                     if isinstance(plan, dict) else None)})

    # Cross-check the other direction.  Looking only from ledger -> plan lets a
    # field deletion hide the whole lifecycle: the plan still exists and names
    # the exact archive/mod row, but no row asks us to validate it.  Managed
    # plans must have exactly one ledger reference; abandoned plans belong in a
    # separately archived evidence area, not the active test-plans directory.
    if plan_root.is_dir():
        for plan_path in sorted(plan_root.glob("*.json"), key=lambda p: p.name.casefold()):
            resolved = plan_path.resolve()
            key = os.path.normcase(str(resolved))
            try:
                resolved = plan_path.resolve(strict=True)
                resolved.relative_to(plan_root)
                plan = json.loads(resolved.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                # A referenced unreadable plan is already represented by its
                # ledger row. Every other JSON file in this active authority is
                # invalid rather than being silently mistaken for an archive.
                if key not in references:
                    rows.append({
                        "modName": plan_path.name, "state": "invalid",
                        "errors": [f"unreferenced active test-plan JSON is unreadable: "
                                   f"{type(exc).__name__}: {exc}"],
                        "pending": [], "path": str(resolved),
                        "testId": None, "planStatus": None,
                    })
                continue
            source = _managed_plan_source(plan)
            bound = references.get(key, [])
            if len(bound) == 1:
                continue
            matches = ([mod for mod in document["mods"]
                        if _source_matches_ledger(source, mod)]
                       if source is not None else [])
            if not bound and source is None:
                detail = ("active test-plan JSON is unreferenced; move notes/archived "
                          "evidence outside records/test-plans")
            elif not bound and matches:
                detail = ("managed plan is orphaned: its exact ledger row exists but "
                          "does not reference this verificationPlan")
            elif not bound:
                detail = "managed plan is orphaned: no exact ledger row references it"
            else:
                detail = (f"managed plan has {len(bound)} ledger bindings; exactly one "
                          "is required")
            rows.append({
                "modName": ((source or {}).get("modName") or plan_path.name),
                "state": "invalid", "errors": [detail], "pending": [],
                "path": str(resolved), "testId": plan.get("testId"),
                "planStatus": str(plan.get("status") or "").casefold(),
            })
    return {
        "schemaVersion": 1,
        "fingerprint": fingerprint,
        "plans": rows,
        "invalid": [row for row in rows if row["state"] == "invalid"],
        "pending": [row for row in rows if row["state"] == "pending"],
        "complete": [row for row in rows if row["state"] == "complete"],
    }


def run(fails, warns, mode="play"):
    if mode not in {"play", "test-harness"}:
        fails.append(f"unknown preflight mode: {mode}")
        return
    try:
        result = audit()
    except Exception as exc:
        fails.append(f"verification-plan state unreadable: {type(exc).__name__}: {exc}")
        return
    for row in result["invalid"]:
        fails.append(f"invalid verification plan for {row['modName']}: " +
                     "; ".join(row["errors"]))
    for row in result["pending"]:
        detail = "; ".join(row["pending"][:3])
        human_only = (row.get("planStatus") == "technical-pass" and
                      all(item.startswith("V7-human-play:")
                          for item in row["pending"]))
        if mode == "test-harness":
            warns.append(f"test harness may exercise pending plan for {row['modName']}: " +
                         detail)
        elif human_only:
            warns.append(f"technical verification passed for {row['modName']}; "
                         f"human play acceptance remains: {detail}")
        else:
            fails.append(f"ordinary play blocked by unverified build for "
                         f"{row['modName']}: {detail}")


def selftest():
    fingerprint = {"algorithm": "fixture-v1", "sha256": "A" * 64, "inputs": []}
    plan = verification_plan.make_plan(["plugin"], "fixture", "#102", False,
                                       fingerprint)
    errors, pending = validate_plan(plan, fingerprint)
    assert not errors and pending
    plan["freshCharacter"]["testCharacterId"] = "FV-FIXTURE"
    plan["results"] = {"stages": {
        stage: {"status": "pass", "evidence": [f"receipt/{stage}.json"]}
        for stage in plan["stagesRequired"]
    }, "cycles": [{
        "testCharacterId": "FV-FIXTURE",
        "status": "pass",
        "evidence": ["receipt/cycle-1.json"],
    }]}
    plan["status"] = "playtest-accepted"
    errors, pending = validate_plan(plan, fingerprint)
    assert not errors and not pending
    plan["buildFingerprint"]["sha256"] = "B" * 64
    assert any("fingerprint" in error.casefold()
               for error in validate_plan(plan, fingerprint)[0])
    plan["buildFingerprint"]["sha256"] = "A" * 64
    plan["results"]["stages"]["V3-feature-probes"]["evidence"] = []
    assert any("evidence" in error for error in validate_plan(plan, fingerprint)[0])
    plan["results"]["stages"]["V3-feature-probes"]["evidence"] = ["receipt/v3.json"]
    plan["status"] = "technical-pass"
    plan["results"]["stages"].pop("V7-human-play")
    errors, pending = validate_plan(plan, fingerprint)
    assert not errors and pending == ["V7-human-play: no result"]
    native = verification_plan.make_plan(["native"], "native", "#102", False,
                                         fingerprint)
    native["freshCharacter"]["testCharacterId"] = "FV-NATIVE-1"
    native["results"] = {"stages": {
        stage: {"status": "pass", "evidence": [f"receipt/{stage}.json"]}
        for stage in native["stagesRequired"]
    }, "cycles": [{
        "testCharacterId": "FV-NATIVE-1", "status": "pass",
        "evidence": ["receipt/native-1.json"],
    }]}
    native["status"] = "technical-pass"
    errors, pending = validate_plan(native, fingerprint)
    assert errors and any("cycles" in item for item in pending)
    native["results"]["stages"]["V4-save-load-round-trip"]["status"] = \
        "not-applicable"
    assert any("V4-save-load-round-trip" in item
               for item in validate_plan(native, fingerprint)[1])
    tampered = verification_plan.make_plan(
        ["native"], "tamper", "#102", True, fingerprint)
    original_signature = tampered["contractSignature"]
    tampered.update({
        "changeKinds": ["asset"], "riskClass": 1, "cyclesRequired": 1,
        "stagesRequired": ["V0-static"], "crashFix": False,
    })
    assert any("contract" in error for error in validate_plan(tampered, fingerprint)[0])
    tampered["contractSignature"] = verification_plan.contract_signature(tampered)
    assert any("ledger" in error for error in validate_plan(
        tampered, fingerprint, expected_signature=original_signature)[0])
    with tempfile.TemporaryDirectory(prefix="verification-status-") as raw:
        root = pathlib.Path(raw)
        (root / "records" / "test-plans").mkdir(parents=True)
        plan["status"] = "playtest-accepted"
        plan_path = root / "records" / "test-plans" / "fixture.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        ledger = root / "ledger.json"
        ledger.write_text(json.dumps({"mods": [{
            "modName": "Fixture", "installedUtc": "2026-09-04T01:00:00Z",
            "verificationPlan": "records/test-plans/fixture.json",
        }]}), encoding="utf-8")
        result = audit(root, root / "unused", "Default", ledger, fingerprint)
        assert result["invalid"]
        ledger.write_text(json.dumps({"mods": [{
            "modName": "Naive Fixture", "installedUtc": "2026-09-04T01:00:00",
        }]}), encoding="utf-8")
        result = audit(root, root / "unused", "Default", ledger, fingerprint)
        assert result["invalid"] and any(
            "timezone" in error for error in result["invalid"][0]["errors"])

        managed_source = {
            "operation": "install", "game": "skyrimspecialedition",
            "modName": "Stripped Binding", "modId": 77, "fileId": 88,
            "archiveSha256": "C" * 64,
            "impactReceipt": "records/impact-receipts/fixture.json",
            "impactReceiptSha256": "D" * 64,
        }
        stripped_plan = verification_plan.make_plan(
            ["asset"], "stripped", "#235", False, fingerprint, managed_source)
        (root / "records" / "test-plans" / "stripped.json").write_text(
            json.dumps(stripped_plan), encoding="utf-8")
        orphan_source = dict(managed_source, modName="No Ledger Row", modId=78)
        orphan_plan = verification_plan.make_plan(
            ["asset"], "orphan", "#235", False, fingerprint, orphan_source)
        (root / "records" / "test-plans" / "orphan.json").write_text(
            json.dumps(orphan_plan), encoding="utf-8")
        ledger.write_text(json.dumps({"mods": [{
            "modName": "Stripped Binding", "modId": 77, "fileId": 88,
            "sha256": "C" * 64, "installedUtc": "2026-09-03T01:00:00Z",
        }]}), encoding="utf-8")
        result = audit(root, root / "unused", "Default", ledger, fingerprint)
        orphan_errors = {
            row["modName"]: "; ".join(row["errors"])
            for row in result["invalid"]
        }
        assert "Stripped Binding" in orphan_errors and "exact ledger row" in \
            orphan_errors["Stripped Binding"]
        assert "No Ledger Row" in orphan_errors and "no exact ledger row" in \
            orphan_errors["No Ledger Row"]

        unreferenced = root / "records" / "test-plans" / "notes.json"
        unreferenced.write_text('{"note":"not an active test plan"}\n', encoding="utf-8")
        unreadable = root / "records" / "test-plans" / "broken.json"
        unreadable.write_text('{broken\n', encoding="utf-8")
        result = audit(root, root / "unused", "Default", ledger, fingerprint)
        active_errors = {row["modName"]: "; ".join(row["errors"])
                         for row in result["invalid"]}
        assert "notes.json" in active_errors and "unreferenced" in active_errors["notes.json"]
        assert "broken.json" in active_errors and "unreadable" in active_errors["broken.json"]

        fomod_root = root / "records" / "fomod-plans"
        fomod_root.mkdir()
        fomod = fomod_root / "fixture.json"
        fomod.write_text('{"schemaVersion":1,"mappings":[]}\n', encoding="utf-8")
        fomod_row = {
            "fomodPlan": "records/fomod-plans/fixture.json",
            "fomodPlanSha256": _sha256_file(fomod),
        }
        assert not _validate_fomod_binding(root, fomod_row)
        fomod.write_text('{"schemaVersion":1,"mappings":[1]}\n', encoding="utf-8")
        assert any("SHA-256" in error for error in _validate_fomod_binding(root, fomod_row))
    original_audit = globals()["audit"]
    try:
        globals()["audit"] = lambda: {
            "invalid": [], "complete": [], "fingerprint": fingerprint,
            "pending": [{"modName": "Pending", "planStatus": "planned",
                         "pending": ["V1-boot: no result"]}],
        }
        play_fails, play_warns = [], []
        run(play_fails, play_warns, mode="play")
        assert play_fails and not play_warns
        harness_fails, harness_warns = [], []
        run(harness_fails, harness_warns, mode="test-harness")
        assert not harness_fails and harness_warns
        globals()["audit"] = lambda: {
            "invalid": [], "complete": [], "fingerprint": fingerprint,
            "pending": [{"modName": "Human", "planStatus": "technical-pass",
                         "pending": ["V7-human-play: no result"]}],
        }
        human_fails, human_warns = [], []
        run(human_fails, human_warns, mode="play")
        assert not human_fails and human_warns
    finally:
        globals()["audit"] = original_audit
    print("verification_status selftest PASS (20 assertions)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--mode", choices=("play", "test-harness"), default="play")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["invalid"]:
            print(f"FAIL {row['modName']}: " + "; ".join(row["errors"]))
        for row in result["pending"]:
            print(f"PENDING {row['modName']}: " + "; ".join(row["pending"]))
        print(f"{len(result['complete'])} complete, {len(result['pending'])} pending, "
              f"{len(result['invalid'])} invalid verification plan(s)")
    return 1 if result["invalid"] or result["pending"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
