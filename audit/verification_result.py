"""Safely append automated evidence to a fingerprint-bound verification plan.

The input is a repository evidence receipt, for example::

    {
      "schemaVersion": 1,
      "verificationPlan": "records/test-plans/SVT-....json",
      "testId": "SVT-...",
      "contractSignature": "...",
      "buildFingerprint": {"algorithm": "...", "sha256": "..."},
      "observedUtc": "2026-09-04T22:00:00Z",
      "resultType": "stage",
      "stage": "V1-boot",
      "status": "pass",
      "summary": "Main menu opened in 41.8 seconds.",
      "artifacts": ["records/launch-verify-20260904-220000.md"]
    }

Automated receipts cannot record V7, select a plan-level state, or
weaken/replace an existing result. The writer derives ``running``, ``failed``
and ``technical-pass`` itself. A separate, explicit ``--human-acceptance``
capability consumes a human-acceptance receipt only after technical pass.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import secrets
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import verification_plan
import verification_status


REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se")
PROFILE = "Default"
PLAN_ROOT = pathlib.Path("records/test-plans")
EVIDENCE_ROOT = pathlib.Path("records")
LEDGER_PATH = pathlib.Path("records/installed-mods.json")
HEX_256 = re.compile(r"[0-9A-Fa-f]{64}")
AUTOMATED_STATES = {"planned", "running", "technical-pass"}
TERMINAL_STATES = {"failed", "aborted", "playtest-accepted"}


class ResultError(ValueError):
    """An evidence receipt cannot safely mutate its requested plan."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _read_json(path: pathlib.Path, label: str):
    try:
        payload = path.read_bytes()
        document = json.loads(payload.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResultError(
            f"{label} is unreadable: {type(exc).__name__}: {exc}") from exc
    if not isinstance(document, dict):
        raise ResultError(f"{label} root must be a JSON object")
    return document, payload


def _relative(path: pathlib.Path, repo: pathlib.Path) -> str:
    return path.relative_to(repo).as_posix()


def _confined_file(repo: pathlib.Path, value, relative_root: pathlib.Path,
                   label: str) -> pathlib.Path:
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        raise ResultError(f"{label} path is required")
    repo = repo.resolve(strict=True)
    allowed = (repo / relative_root).resolve(strict=True)
    try:
        allowed.relative_to(repo)
    except ValueError as exc:
        raise ResultError(
            f"repository {relative_root.as_posix()} root escapes the repository") from exc
    raw = pathlib.Path(value)
    candidate = raw if raw.is_absolute() else repo / raw
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ResultError(f"{label} does not exist: {candidate}") from exc
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise ResultError(
            f"{label} must stay inside {relative_root.as_posix()}: {value}") from exc
    if not resolved.is_file():
        raise ResultError(f"{label} is not a file: {resolved}")
    return resolved


def _strict_utc(value, label: str) -> dt.datetime:
    text = str(value or "").strip()
    if not text or not (text.endswith("Z") or re.search(r"[+-]\d\d:\d\d$", text)):
        raise ResultError(f"{label} must be an ISO-8601 timestamp with a timezone")
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ResultError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ResultError(f"{label} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _fingerprint_identity(value, label: str):
    if not isinstance(value, dict):
        raise ResultError(f"{label} must be an object")
    algorithm = str(value.get("algorithm") or "").strip()
    digest = str(value.get("sha256") or "").strip().upper()
    if not algorithm or not HEX_256.fullmatch(digest):
        raise ResultError(f"{label} must contain an algorithm and SHA-256")
    return algorithm, digest


def _same_fingerprint(left, right) -> bool:
    try:
        return _fingerprint_identity(left, "buildFingerprint") == \
            _fingerprint_identity(right, "current build fingerprint")
    except ResultError:
        return False


def _expected_source(row: dict) -> dict:
    return {
        "operation": row.get("lifecycleOperation"),
        "game": "skyrimspecialedition",
        "modName": row.get("modName"),
        "modId": row.get("modId"),
        "fileId": row.get("fileId"),
        "archiveSha256": str(row.get("sha256") or "").upper(),
        "impactReceipt": row.get("impactReceipt"),
        "impactReceiptSha256": row.get("impactReceiptSha256"),
    }


def _ledger_binding(repo: pathlib.Path, plan_path: pathlib.Path):
    ledger_path = _confined_file(
        repo, LEDGER_PATH, pathlib.Path("records"), "installed-mod ledger")
    ledger, ledger_payload = _read_json(ledger_path, "installed-mod ledger")
    mods = ledger.get("mods")
    if not isinstance(mods, list):
        raise ResultError("installed-mod ledger must contain a mods array")
    plan_relative = _relative(plan_path, repo)
    matches = []
    for row in mods:
        if not isinstance(row, dict):
            continue
        reference = row.get("verificationPlan")
        if not isinstance(reference, str) or not reference.strip():
            continue
        raw = pathlib.Path(reference)
        if raw.is_absolute():
            continue
        try:
            target = (repo / raw).resolve(strict=False)
            target.relative_to((repo / PLAN_ROOT).resolve(strict=True))
        except (OSError, ValueError):
            continue
        if os.path.normcase(str(target)) == os.path.normcase(str(plan_path)):
            matches.append(row)
    if len(matches) != 1:
        raise ResultError(
            f"verification plan must have exactly one ledger binding; found {len(matches)}")
    row = matches[0]
    required = (
        "lifecyclePolicyVersion", "lifecycleOperation", "issue",
        "impactReceipt", "impactReceiptSha256", "verificationPlan",
        "verificationTestId", "verificationContractSignature",
    )
    missing = [field for field in required if not row.get(field)]
    if missing:
        raise ResultError(
            "ledger binding is incomplete: " + ", ".join(missing))
    normalized_reference = pathlib.PurePosixPath(
        str(row["verificationPlan"]).replace("\\", "/")).as_posix()
    if normalized_reference != plan_relative:
        raise ResultError("ledger verificationPlan is not the canonical repository path")
    return ledger_path, row, ledger_payload


def _validate_bound_plan(plan: dict, fingerprint: dict, row: dict):
    status = str(plan.get("status") or "").casefold()
    if status not in AUTOMATED_STATES | TERMINAL_STATES:
        raise ResultError(f"plan status is invalid: {status or '(blank)'}")
    if status == "playtest-accepted":
        raise ResultError("automation may not modify a playtest-accepted plan")
    if status in {"failed", "aborted"}:
        raise ResultError(f"plan is terminal and cannot be rewritten: {status}")
    results = plan.get("results")
    if not isinstance(results, dict):
        raise ResultError("plan results must be an object")
    stage_results = results.get("stages", {})
    cycles = results.get("cycles", [])
    if not isinstance(stage_results, dict):
        raise ResultError("plan results.stages must be an object")
    if not isinstance(cycles, list):
        raise ResultError("plan results.cycles must be an array")
    required_stages = plan.get("stagesRequired")
    if isinstance(required_stages, list):
        unexpected = sorted(set(stage_results) - set(required_stages))
        if unexpected:
            raise ResultError(
                "plan contains results for uncontracted stages: " +
                ", ".join(unexpected))
    required_cycles = plan.get("cyclesRequired")
    if isinstance(required_cycles, int) and not isinstance(required_cycles, bool) \
            and len(cycles) > required_cycles:
        raise ResultError("plan contains more cycles than its contract allows")
    automated_rows = [
        result for stage, result in stage_results.items()
        if stage != "V7-human-play" and isinstance(result, dict)
    ] + [result for result in cycles if isinstance(result, dict)]
    if status == "planned" and automated_rows:
        raise ResultError("planned status cannot contain prior automated results")
    if any(str(result.get("status") or "").casefold() == "fail"
           for result in automated_rows):
        raise ResultError("a failed automated result cannot return to a passing state")
    errors, pending = verification_status.validate_plan(
        plan,
        fingerprint,
        expected_signature=row.get("verificationContractSignature"),
        expected_test_id=row.get("verificationTestId"),
        expected_issue=row.get("issue"),
        expected_source=_expected_source(row),
    )
    if errors:
        raise ResultError("verification plan is not currently valid: " +
                          "; ".join(errors))
    return status, pending


def _artifact_record(repo: pathlib.Path, path: pathlib.Path, payload=None):
    if payload is None:
        digest = hashlib.sha256()
        size = 0
        try:
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
        except OSError as exc:
            raise ResultError(f"evidence artifact became unreadable: {path}") from exc
        sha256 = digest.hexdigest().upper()
    else:
        size = len(payload)
        sha256 = _sha256_bytes(payload)
    return {
        "path": _relative(path, repo),
        "bytes": size,
        "sha256": sha256,
    }


def _receipt_artifacts(repo: pathlib.Path, receipt_path: pathlib.Path,
                       receipt_payload: bytes, receipt: dict,
                       plan_path: pathlib.Path, ledger_path: pathlib.Path):
    records = [_artifact_record(repo, receipt_path, receipt_payload)]
    seen = {os.path.normcase(str(receipt_path))}
    forbidden = {os.path.normcase(str(plan_path)), os.path.normcase(str(ledger_path))}
    artifacts = receipt.get("artifacts", [])
    if artifacts is None:
        artifacts = []
    if not isinstance(artifacts, list):
        raise ResultError("evidence artifacts must be an array")
    for index, entry in enumerate(artifacts, 1):
        if isinstance(entry, str):
            reference, expected_hash = entry, None
        elif isinstance(entry, dict):
            reference = entry.get("path")
            expected_hash = str(entry.get("sha256") or "").strip().upper() or None
            if expected_hash is not None and not HEX_256.fullmatch(expected_hash):
                raise ResultError(f"artifact {index} sha256 is invalid")
        else:
            raise ResultError(f"artifact {index} must be a path or object")
        if pathlib.Path(str(reference or "")).is_absolute():
            raise ResultError(f"artifact {index} path must be repository-relative")
        path = _confined_file(repo, reference, EVIDENCE_ROOT,
                              f"evidence artifact {index}")
        identity = os.path.normcase(str(path))
        if identity in seen:
            raise ResultError(f"evidence artifact {index} is duplicated")
        if identity in forbidden:
            raise ResultError(f"evidence artifact {index} cannot be a plan or ledger")
        record = _artifact_record(repo, path)
        if expected_hash is not None and record["sha256"] != expected_hash:
            raise ResultError(f"evidence artifact {index} SHA-256 does not match")
        seen.add(identity)
        records.append(record)
    return records


def _validate_receipt(receipt: dict, plan: dict, plan_relative: str,
                      fingerprint: dict, allow_human_acceptance=False):
    if receipt.get("schemaVersion") != 1:
        raise ResultError("evidence schemaVersion must be 1")
    if receipt.get("verificationPlan") != plan_relative:
        raise ResultError("evidence verificationPlan does not match the target plan")
    if receipt.get("testId") != plan.get("testId"):
        raise ResultError("evidence testId does not match the target plan")
    if receipt.get("contractSignature") != plan.get("contractSignature"):
        raise ResultError("evidence contractSignature does not match the target plan")
    if not _same_fingerprint(receipt.get("buildFingerprint"), fingerprint):
        raise ResultError("evidence buildFingerprint is stale or belongs to another build")
    observed = _strict_utc(receipt.get("observedUtc"), "evidence observedUtc")
    created = _strict_utc(plan.get("createdUtc"), "plan createdUtc")
    if observed < created:
        raise ResultError("evidence predates the verification plan")
    if observed > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ResultError("evidence observedUtc is implausibly far in the future")
    summary = str(receipt.get("summary") or "").strip()
    if len(summary) < 6:
        raise ResultError("evidence summary must be substantive")
    result_type = str(receipt.get("resultType") or "").casefold()
    allowed_types = {"stage", "cycle"}
    if allow_human_acceptance:
        allowed_types.add("human-acceptance")
    if result_type not in allowed_types:
        allowed = "stage or cycle" + (
            " or human-acceptance" if allow_human_acceptance else "")
        raise ResultError(f"evidence resultType must be {allowed}")
    result_status = str(receipt.get("status") or "").casefold()
    if result_status not in {"pass", "fail"}:
        raise ResultError("automation result status must be pass or fail")
    if any(field in receipt for field in (
            "planStatus", "playtestAccepted", "humanAcceptance")):
        raise ResultError("evidence may not select a plan or human-acceptance state")
    artifacts = receipt.get("artifacts")
    if result_type == "human-acceptance":
        if result_status != "pass":
            raise ResultError("human acceptance must be a passing attestation")
        if receipt.get("stage") != "V7-human-play":
            raise ResultError("human acceptance must attest V7-human-play")
        if len(str(receipt.get("acceptedBy") or "").strip()) < 2:
            raise ResultError("human acceptance requires acceptedBy")
        if not isinstance(artifacts, list):
            raise ResultError("human acceptance artifacts must be an array")
    elif result_status == "pass" and (not isinstance(artifacts, list) or not artifacts):
        raise ResultError(
            "automated pass requires at least one external diagnostic artifact; "
            "the assertion receipt cannot attest itself")
    return result_type, result_status, observed, summary


def _verify_recorded_row(repo: pathlib.Path, row: dict, label: str):
    if not isinstance(row, dict):
        raise ResultError(f"{label} is not an object")
    status = str(row.get("status") or "").casefold()
    if status not in {"pass", "fail"}:
        raise ResultError(f"{label} has a non-monotonic status: {status or '(blank)'}")
    paths = row.get("evidence")
    if not isinstance(paths, list) or not paths:
        raise ResultError(f"{label} has no repository evidence paths")
    stored = row.get("evidenceArtifacts")
    if stored is not None and (not isinstance(stored, list) or len(stored) != len(paths)):
        raise ResultError(f"{label} evidence artifact metadata is inconsistent")
    for index, reference in enumerate(paths):
        path = _confined_file(repo, reference, EVIDENCE_ROOT,
                              f"{label} evidence {index + 1}")
        if stored is None:
            continue
        record = stored[index]
        if not isinstance(record, dict) or record.get("path") != reference:
            raise ResultError(f"{label} evidence artifact metadata is inconsistent")
        actual = _artifact_record(repo, path)
        if (record.get("bytes") != actual["bytes"] or
                str(record.get("sha256") or "").upper() != actual["sha256"]):
            raise ResultError(f"{label} evidence artifact changed after ingestion")


def _verify_recorded_evidence(repo: pathlib.Path, plan: dict):
    results = plan.get("results")
    if not isinstance(results, dict):
        return
    stages = results.get("stages")
    if isinstance(stages, dict):
        for stage, row in stages.items():
            if stage == "V7-human-play":
                continue
            _verify_recorded_row(repo, row, f"stage {stage}")
    cycles = results.get("cycles")
    if isinstance(cycles, list):
        for index, row in enumerate(cycles, 1):
            _verify_recorded_row(repo, row, f"cycle {index}")


def _result_row(receipt: dict, status: str, observed: dt.datetime,
                summary: str, artifact_records: list[dict]):
    row = {
        "status": status,
        "observedUtc": observed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "evidence": [record["path"] for record in artifact_records],
        "evidenceArtifacts": artifact_records,
    }
    producer = str(receipt.get("producer") or "").strip()
    if producer:
        row["producer"] = producer
    return row


def _apply_result(plan: dict, receipt: dict, result_type: str,
                  result_status: str, observed: dt.datetime, summary: str,
                  artifact_records: list[dict]):
    results = plan.setdefault("results", {})
    if not isinstance(results, dict):
        raise ResultError("plan results must be an object")
    desired = _result_row(
        receipt, result_status, observed, summary, artifact_records)
    if result_type == "human-acceptance":
        desired["acceptedBy"] = str(receipt.get("acceptedBy") or "").strip()
        stages = results.setdefault("stages", {})
        if not isinstance(stages, dict):
            raise ResultError("plan results.stages must be an object")
        existing = stages.get("V7-human-play")
        if existing is not None:
            if existing == desired:
                return False
            raise ResultError("V7 human acceptance is immutable once recorded")
        stages["V7-human-play"] = desired
        return True
    if result_type == "stage":
        stage = str(receipt.get("stage") or "")
        if stage == "V7-human-play":
            raise ResultError("automation may not record V7-human-play")
        if stage not in (plan.get("stagesRequired") or []):
            raise ResultError(f"stage is not required by this plan: {stage or '(blank)'}")
        character_id = str(receipt.get("testCharacterId") or "").strip()
        if stage == "V2-fresh-start" and result_status == "pass":
            if not character_id:
                raise ResultError("passing V2-fresh-start requires testCharacterId")
            cycles = results.get("cycles")
            if isinstance(cycles, list) and cycles:
                first_id = str(cycles[0].get("testCharacterId") or "").strip() \
                    if isinstance(cycles[0], dict) else ""
                if first_id and first_id != character_id:
                    raise ResultError(
                        "V2 testCharacterId must match the first verification cycle")
            fresh = plan.get("freshCharacter")
            if not isinstance(fresh, dict):
                raise ResultError("plan freshCharacter contract is invalid")
            prior = str(fresh.get("testCharacterId") or "").strip()
            if prior and prior != character_id:
                raise ResultError("V2 testCharacterId cannot replace an existing identity")
            desired["testCharacterId"] = character_id
        elif character_id:
            raise ResultError("testCharacterId belongs only on V2 or cycle evidence")
        stages = results.setdefault("stages", {})
        if not isinstance(stages, dict):
            raise ResultError("plan results.stages must be an object")
        existing = stages.get(stage)
        if existing is not None:
            if existing == desired:
                return False
            raise ResultError(f"stage result is immutable once recorded: {stage}")
        stages[stage] = desired
        if stage == "V2-fresh-start" and result_status == "pass":
            plan["freshCharacter"]["testCharacterId"] = character_id
        return True

    cycle = receipt.get("cycle")
    if not isinstance(cycle, int) or isinstance(cycle, bool) or cycle < 1:
        raise ResultError("cycle evidence requires a positive integer cycle")
    required = plan.get("cyclesRequired")
    if not isinstance(required, int) or isinstance(required, bool) or cycle > required:
        raise ResultError(f"cycle {cycle} exceeds this plan's required cycle count")
    character_id = str(receipt.get("testCharacterId") or "").strip()
    if not character_id:
        raise ResultError("cycle evidence requires testCharacterId")
    if cycle == 1:
        fresh = plan.get("freshCharacter")
        first_id = str(fresh.get("testCharacterId") or "").strip() \
            if isinstance(fresh, dict) else ""
        if first_id and first_id != character_id:
            raise ResultError(
                "first cycle testCharacterId must match V2-fresh-start")
    desired["cycle"] = cycle
    desired["testCharacterId"] = character_id
    cycles = results.setdefault("cycles", [])
    if not isinstance(cycles, list):
        raise ResultError("plan results.cycles must be an array")
    if cycle <= len(cycles):
        if cycles[cycle - 1] == desired:
            return False
        raise ResultError(f"cycle result is immutable once recorded: {cycle}")
    if cycle != len(cycles) + 1:
        raise ResultError("cycle evidence must be appended in numeric order")
    prior_ids = {
        str(row.get("testCharacterId") or "").strip()
        for row in cycles if isinstance(row, dict)
    }
    if character_id in prior_ids:
        raise ResultError("each verification cycle requires a unique testCharacterId")
    cycles.append(desired)
    return True


def _write_json_atomic(path: pathlib.Path, document: dict):
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        temporary.write_text(json.dumps(document, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class _PlanLock:
    def __init__(self, plan_path: pathlib.Path):
        self.path = plan_path.with_name(plan_path.name + ".result.lock")
        self.fd = None

    def __enter__(self):
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ResultError(
                f"another verification result writer holds {self.path.name}") from exc
        except OSError as exc:
            raise ResultError(f"cannot lock verification plan: {exc}") from exc
        try:
            os.write(self.fd, f"pid={os.getpid()}\n".encode("ascii"))
        except Exception:
            os.close(self.fd)
            self.fd = None
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _compute_fingerprint(repo: pathlib.Path, instance: pathlib.Path,
                         profile: str, ledger_path: pathlib.Path):
    return verification_plan.build_fingerprint(
        pathlib.Path(instance), profile, ledger_path, repo_root=repo)


def ingest(plan_reference, evidence_reference, repo=REPO, instance=INSTANCE,
           profile=PROFILE, current_fingerprint=None, human_acceptance=False):
    """Ingest one immutable result receipt and return the resulting state.

    ``current_fingerprint`` is an offline-test seam. The command-line path
    always computes the live fingerprint from the current ledger/profile/game
    authorities immediately before validation and again before its write.
    """
    try:
        repo = pathlib.Path(repo).resolve(strict=True)
    except OSError as exc:
        raise ResultError(f"repository does not exist: {repo}") from exc
    plan_path = _confined_file(repo, plan_reference, PLAN_ROOT,
                               "verification plan")
    evidence_path = _confined_file(repo, evidence_reference, EVIDENCE_ROOT,
                                   "verification evidence")
    if plan_path == evidence_path:
        raise ResultError("verification evidence cannot be the plan itself")

    with _PlanLock(plan_path):
        plan, original_payload = _read_json(plan_path, "verification plan")
        ledger_path, ledger_row, ledger_payload = _ledger_binding(repo, plan_path)
        if evidence_path == ledger_path:
            raise ResultError("verification evidence cannot be the installed-mod ledger")
        if current_fingerprint is None:
            try:
                fingerprint = _compute_fingerprint(
                    repo, pathlib.Path(instance), profile, ledger_path)
            except Exception as exc:
                raise ResultError(
                    f"cannot compute current build fingerprint: {exc}") from exc
        else:
            fingerprint = copy.deepcopy(current_fingerprint)
            _fingerprint_identity(fingerprint, "current build fingerprint")
        prior_status, _ = _validate_bound_plan(plan, fingerprint, ledger_row)
        _verify_recorded_evidence(repo, plan)

        receipt, receipt_payload = _read_json(
            evidence_path, "verification evidence")
        plan_relative = _relative(plan_path, repo)
        result_type, result_status, observed, summary = _validate_receipt(
            receipt, plan, plan_relative, fingerprint,
            allow_human_acceptance=human_acceptance)
        artifact_records = _receipt_artifacts(
            repo, evidence_path, receipt_payload, receipt, plan_path, ledger_path)

        candidate = copy.deepcopy(plan)
        changed = _apply_result(
            candidate, receipt, result_type, result_status, observed, summary,
            artifact_records)
        if not changed:
            return {
                "changed": False,
                "status": prior_status,
                "plan": plan_relative,
                "testId": plan.get("testId"),
            }
        if result_type == "human-acceptance" and prior_status != "technical-pass":
            raise ResultError("human acceptance requires an existing technical-pass")
        if prior_status == "technical-pass" and result_type != "human-acceptance":
            raise ResultError("technical-pass is monotonic and cannot accept new results")
        if result_type == "human-acceptance":
            candidate["status"] = "playtest-accepted"
        elif result_status == "fail":
            candidate["status"] = "failed"
        else:
            candidate["status"] = "running"
            errors, pending = verification_status.validate_plan(
                candidate,
                fingerprint,
                expected_signature=ledger_row.get("verificationContractSignature"),
                expected_test_id=ledger_row.get("verificationTestId"),
                expected_issue=ledger_row.get("issue"),
                expected_source=_expected_source(ledger_row),
            )
            technical_pending = [
                item for item in pending
                if not item.startswith("V7-human-play:")
                and item != "plan status is running"
            ]
            if errors:
                raise ResultError(
                    "new result would make the verification plan invalid: " +
                    "; ".join(errors))
            if not technical_pending:
                candidate["status"] = "technical-pass"
        if candidate["status"] == "technical-pass":
            errors, pending = verification_status.validate_plan(
                candidate,
                fingerprint,
                expected_signature=ledger_row.get("verificationContractSignature"),
                expected_test_id=ledger_row.get("verificationTestId"),
                expected_issue=ledger_row.get("issue"),
                expected_source=_expected_source(ledger_row),
            )
            if errors or any(not item.startswith("V7-human-play:") for item in pending):
                raise ResultError(
                    "verification_status did not validate every technical stage")
        if candidate["status"] == "playtest-accepted":
            errors, pending = verification_status.validate_plan(
                candidate,
                fingerprint,
                expected_signature=ledger_row.get("verificationContractSignature"),
                expected_test_id=ledger_row.get("verificationTestId"),
                expected_issue=ledger_row.get("issue"),
                expected_source=_expected_source(ledger_row),
            )
            if errors or pending:
                raise ResultError(
                    "human acceptance did not complete a valid verification plan: " +
                    "; ".join(errors + pending))
        original_stages = plan["results"].get("stages", {})
        candidate_stages = candidate["results"].get("stages", {})
        original_v7 = original_stages.get("V7-human-play")
        candidate_v7 = candidate_stages.get("V7-human-play")
        if (not human_acceptance and
                (candidate.get("status") == "playtest-accepted" or
                 candidate_v7 != original_v7)):
            raise ResultError("automation cannot write V7 or playtest-accepted")
        _verify_recorded_evidence(repo, candidate)
        deep_errors = verification_status.validate_result_evidence(
            candidate, repo, plan_path, ledger_path)
        if deep_errors:
            raise ResultError("result evidence failed durable validation: " +
                              "; ".join(deep_errors))

        try:
            unchanged = plan_path.read_bytes() == original_payload
        except OSError as exc:
            raise ResultError(
                "verification plan became unreadable during evidence ingestion") from exc
        if not unchanged:
            raise ResultError("verification plan changed during evidence ingestion")
        try:
            ledger_unchanged = ledger_path.read_bytes() == ledger_payload
        except OSError as exc:
            raise ResultError(
                "installed-mod ledger became unreadable during evidence ingestion") from exc
        if not ledger_unchanged:
            raise ResultError("installed-mod ledger changed during evidence ingestion")
        if current_fingerprint is None:
            try:
                final_fingerprint = _compute_fingerprint(
                    repo, pathlib.Path(instance), profile, ledger_path)
            except Exception as exc:
                raise ResultError(
                    f"cannot recheck current build fingerprint: {exc}") from exc
            if not _same_fingerprint(final_fingerprint, fingerprint):
                raise ResultError("build fingerprint changed during evidence ingestion")
        try:
            _write_json_atomic(plan_path, candidate)
        except OSError as exc:
            raise ResultError(f"could not update verification plan: {exc}") from exc
        return {
            "changed": True,
            "status": candidate["status"],
            "plan": plan_relative,
            "testId": candidate.get("testId"),
            "resultType": result_type,
            "result": (receipt.get("stage") if result_type in {
                       "stage", "human-acceptance"}
                       else f"cycle-{receipt.get('cycle')}")
        }


def selftest():
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    def rejected(call, text=None):
        nonlocal checks
        try:
            call()
        except ResultError as exc:
            checks += 1
            if text and text.casefold() not in str(exc).casefold():
                raise AssertionError(f"wrong rejection: {exc}")
            return
        raise AssertionError("unsafe evidence was accepted")

    with tempfile.TemporaryDirectory(prefix="verification-result-") as raw:
        root = pathlib.Path(raw)
        repo = root / "repo"
        plans = repo / PLAN_ROOT
        evidence = repo / "records" / "test-evidence"
        plans.mkdir(parents=True)
        evidence.mkdir(parents=True)
        fingerprint = {
            "algorithm": "fixture-v1", "sha256": "A" * 64, "inputs": []}

        def source(name, mod_id, file_id):
            return {
                "operation": "install", "game": "skyrimspecialedition",
                "modName": name, "modId": mod_id, "fileId": file_id,
                "archiveSha256": "B" * 64,
                "impactReceipt": f"records/impact-receipts/{name}.json",
                "impactReceiptSha256": "C" * 64,
            }

        plan = verification_plan.make_plan(
            ["plugin"], "result fixture", "#235", False, fingerprint,
            source("Fixture", 10, 20))
        plan_path = plans / "fixture.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        plan_rel = _relative(plan_path, repo)
        row = {
            "modName": "Fixture", "modId": 10, "fileId": 20,
            "sha256": "B" * 64, "issue": "#235",
            "lifecyclePolicyVersion": 1, "lifecycleOperation": "install",
            "impactReceipt": "records/impact-receipts/Fixture.json",
            "impactReceiptSha256": "C" * 64,
            "verificationPlan": plan_rel,
            "verificationTestId": plan["testId"],
            "verificationContractSignature": plan["contractSignature"],
        }
        ledger_path = repo / LEDGER_PATH
        ledger_path.write_text(json.dumps({"schemaVersion": 1, "mods": [row]}, indent=2),
                               encoding="utf-8")
        artifact = evidence / "launch.md"
        artifact.write_text("main menu and save-load evidence\n", encoding="utf-8")

        def receipt(name, result_type="stage", status="pass", stage="V0-static",
                    cycle=None, character=None, fingerprint_override=None,
                    artifacts=None, plan_override=None, accepted_by=None):
            document = {
                "schemaVersion": 1,
                "verificationPlan": plan_override or plan_rel,
                "testId": plan["testId"],
                "contractSignature": plan["contractSignature"],
                "buildFingerprint": fingerprint_override or fingerprint,
                "observedUtc": plan["createdUtc"],
                "resultType": result_type,
                "status": status,
                "summary": f"Automated fixture result for {name}",
                "artifacts": ([_relative(artifact, repo)]
                              if artifacts is None else artifacts),
            }
            if result_type == "stage":
                document["stage"] = stage
            elif result_type == "cycle":
                document["cycle"] = cycle
            elif result_type == "human-acceptance":
                document["stage"] = stage
            if character:
                document["testCharacterId"] = character
            if accepted_by:
                document["acceptedBy"] = accepted_by
            path = evidence / f"{name}.json"
            path.write_text(json.dumps(document, indent=2), encoding="utf-8")
            return path

        outside = root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        rejected(lambda: ingest(plan_path, outside, repo=repo,
                                current_fingerprint=fingerprint), "inside records")
        escaped_plan = root / "outside-plan.json"
        escaped_plan.write_text(plan_path.read_text(encoding="utf-8"), encoding="utf-8")
        rejected(lambda: ingest(escaped_plan, outside, repo=repo,
                                current_fingerprint=fingerprint), "inside records/test-plans")

        wrong_fp = receipt("wrong-fingerprint", fingerprint_override={
            "algorithm": "fixture-v1", "sha256": "D" * 64})
        original = plan_path.read_bytes()
        rejected(lambda: ingest(plan_rel, wrong_fp, repo=repo,
                                current_fingerprint=fingerprint), "fingerprint")
        check(plan_path.read_bytes() == original,
              "binding rejection changed the plan")
        wrong_contract = receipt("wrong-contract")
        wrong_contract_doc = json.loads(wrong_contract.read_text(encoding="utf-8"))
        wrong_contract_doc["contractSignature"] = "D" * 64
        wrong_contract.write_text(json.dumps(wrong_contract_doc), encoding="utf-8")
        rejected(lambda: ingest(plan_rel, wrong_contract, repo=repo,
                                current_fingerprint=fingerprint), "contractSignature")

        binding_receipt = receipt("binding")
        wrong_ledger = {"schemaVersion": 1, "mods": [
            {**row, "verificationContractSignature": "D" * 64}]}
        ledger_path.write_text(json.dumps(wrong_ledger), encoding="utf-8")
        rejected(lambda: ingest(plan_rel, binding_receipt, repo=repo,
                                current_fingerprint=fingerprint), "ledger transaction")
        ledger_path.write_text(json.dumps({"schemaVersion": 1, "mods": [row]}),
                               encoding="utf-8")

        tampered_plan = json.loads(original.decode("utf-8"))
        tampered_plan["summary"] = "edited after contract generation"
        plan_path.write_text(json.dumps(tampered_plan), encoding="utf-8")
        rejected(lambda: ingest(plan_rel, binding_receipt, repo=repo,
                                current_fingerprint=fingerprint), "contract")
        plan_path.write_bytes(original)
        escaped_artifact = receipt("escaped-artifact", artifacts=["../outside.json"])
        rejected(lambda: ingest(plan_rel, escaped_artifact, repo=repo,
                                current_fingerprint=fingerprint), "inside records")
        self_attested = receipt("self-attested", artifacts=[])
        rejected(lambda: ingest(plan_rel, self_attested, repo=repo,
                                current_fingerprint=fingerprint), "external diagnostic")

        v7 = receipt("v7", stage="V7-human-play")
        rejected(lambda: ingest(plan_rel, v7, repo=repo,
                                current_fingerprint=fingerprint), "may not record V7")
        forbidden = receipt("forbidden-status", status="playtest-accepted")
        rejected(lambda: ingest(plan_rel, forbidden, repo=repo,
                                current_fingerprint=fingerprint), "pass or fail")
        forbidden_control = receipt("forbidden-control")
        forbidden_doc = json.loads(forbidden_control.read_text(encoding="utf-8"))
        forbidden_doc["planStatus"] = "playtest-accepted"
        forbidden_control.write_text(json.dumps(forbidden_doc), encoding="utf-8")
        rejected(lambda: ingest(plan_rel, forbidden_control, repo=repo,
                                current_fingerprint=fingerprint), "may not select")

        v0 = receipt("v0", artifacts=[{
            "path": _relative(artifact, repo),
            "sha256": _sha256_bytes(artifact.read_bytes()),
        }])
        result = ingest(plan_rel, v0, repo=repo, current_fingerprint=fingerprint)
        check(result["changed"] and result["status"] == "running",
              "first technical result did not advance to running")
        after_v0 = plan_path.read_bytes()
        duplicate = ingest(plan_rel, v0, repo=repo,
                           current_fingerprint=fingerprint)
        check(not duplicate["changed"] and plan_path.read_bytes() == after_v0,
              "idempotent receipt rewrote the plan")
        original_artifact = artifact.read_bytes()
        artifact.write_text("evidence changed after ingestion\n", encoding="utf-8")
        after_tamper = receipt("after-evidence-tamper", stage="V1-boot")
        rejected(lambda: ingest(plan_rel, after_tamper, repo=repo,
                                current_fingerprint=fingerprint),
                 "changed after ingestion")
        artifact.write_bytes(original_artifact)
        overwrite = receipt("overwrite", status="fail", stage="V0-static")
        rejected(lambda: ingest(plan_rel, overwrite, repo=repo,
                                current_fingerprint=fingerprint), "immutable")

        for stage in [item for item in plan["stagesRequired"]
                      if item not in {"V0-static", "V7-human-play"}]:
            item = receipt(
                "stage-" + stage,
                stage=stage,
                character="FV-FIXTURE-1" if stage == "V2-fresh-start" else None)
            ingest(plan_rel, item, repo=repo, current_fingerprint=fingerprint)
        cycle = receipt("cycle-1", result_type="cycle", cycle=1,
                        character="FV-FIXTURE-1")
        result = ingest(plan_rel, cycle, repo=repo,
                        current_fingerprint=fingerprint)
        check(result["status"] == "technical-pass",
              "complete technical evidence did not derive technical-pass")
        finished = json.loads(plan_path.read_text(encoding="utf-8"))
        check("V7-human-play" not in finished["results"]["stages"],
              "automation wrote V7")
        errors, pending = verification_status.validate_plan(
            finished, fingerprint,
            expected_signature=row["verificationContractSignature"],
            expected_test_id=row["verificationTestId"],
            expected_issue=row["issue"], expected_source=source("Fixture", 10, 20))
        check(not errors and pending == ["V7-human-play: no result"],
              "technical-pass was not independently validated")
        changed_after_pass = receipt("after-pass", stage="V0-static", status="fail")
        rejected(lambda: ingest(plan_rel, changed_after_pass, repo=repo,
                                current_fingerprint=fingerprint), "immutable")

        human_receipt = receipt(
            "human-acceptance", result_type="human-acceptance",
            stage="V7-human-play", artifacts=[],
            accepted_by="Skyrim build owner")
        rejected(lambda: ingest(plan_rel, human_receipt, repo=repo,
                                current_fingerprint=fingerprint), "stage or cycle")
        result = ingest(
            plan_rel, human_receipt, repo=repo, current_fingerprint=fingerprint,
            human_acceptance=True)
        check(result["status"] == "playtest-accepted",
              "explicit human receipt did not derive playtest-accepted")
        status_result = verification_status.audit(
            repo=repo, instance=repo / "unused", profile="Default",
            ledger_path=ledger_path, current_fingerprint=fingerprint)
        check(len(status_result["complete"]) == 1 and not status_result["invalid"],
              "normal status gate did not validate the accepted evidence")
        accepted_plan = plan_path.read_bytes()
        artifact_bytes = artifact.read_bytes()
        artifact.write_text("post-final-ingest tamper\n", encoding="utf-8")
        tampered_artifact_status = verification_status.audit(
            repo=repo, instance=repo / "unused", profile="Default",
            ledger_path=ledger_path, current_fingerprint=fingerprint)
        check(bool(tampered_artifact_status["invalid"]),
              "normal status gate accepted a tampered diagnostic artifact")
        artifact.write_bytes(artifact_bytes)
        human_bytes = human_receipt.read_bytes()
        human_receipt.write_text("{}", encoding="utf-8")
        tampered_status = verification_status.audit(
            repo=repo, instance=repo / "unused", profile="Default",
            ledger_path=ledger_path, current_fingerprint=fingerprint)
        check(bool(tampered_status["invalid"]),
              "normal status gate accepted tampered final evidence")
        human_receipt.write_bytes(human_bytes)
        check(plan_path.read_bytes() == accepted_plan,
              "status audit changed the accepted plan")

        failed_plan = verification_plan.make_plan(
            ["asset"], "failure fixture", "#236", False, fingerprint,
            source("Failure", 11, 21))
        failed_path = plans / "failure.json"
        failed_path.write_text(json.dumps(failed_plan, indent=2) + "\n", encoding="utf-8")
        failed_rel = _relative(failed_path, repo)
        failed_row = {
            "modName": "Failure", "modId": 11, "fileId": 21,
            "sha256": "B" * 64, "issue": "#236",
            "lifecyclePolicyVersion": 1, "lifecycleOperation": "install",
            "impactReceipt": "records/impact-receipts/Failure.json",
            "impactReceiptSha256": "C" * 64,
            "verificationPlan": failed_rel,
            "verificationTestId": failed_plan["testId"],
            "verificationContractSignature": failed_plan["contractSignature"],
        }
        ledger_path.write_text(json.dumps(
            {"schemaVersion": 1, "mods": [row, failed_row]}, indent=2),
            encoding="utf-8")
        fail_receipt_doc = {
            "schemaVersion": 1, "verificationPlan": failed_rel,
            "testId": failed_plan["testId"],
            "contractSignature": failed_plan["contractSignature"],
            "buildFingerprint": fingerprint,
            "observedUtc": failed_plan["createdUtc"],
            "resultType": "stage", "stage": "V0-static", "status": "fail",
            "summary": "Static fixture deliberately failed", "artifacts": [],
        }
        fail_receipt = evidence / "failure.json"
        fail_receipt.write_text(json.dumps(fail_receipt_doc), encoding="utf-8")
        result = ingest(failed_rel, fail_receipt, repo=repo,
                        current_fingerprint=fingerprint)
        check(result["status"] == "failed", "failed evidence was not terminal")
        later = evidence / "failure-later.json"
        fail_receipt_doc["status"] = "pass"
        fail_receipt_doc["summary"] = "Attempted replacement after failure"
        later.write_text(json.dumps(fail_receipt_doc), encoding="utf-8")
        rejected(lambda: ingest(failed_rel, later, repo=repo,
                                current_fingerprint=fingerprint), "terminal")
        check(not list(plans.glob("*.result.lock")), "result lock leaked")

    print(f"verification_result selftest PASS ({checks} assertions)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=pathlib.Path)
    parser.add_argument("--evidence", type=pathlib.Path)
    parser.add_argument("--repo", type=pathlib.Path, default=REPO)
    parser.add_argument("--instance", type=pathlib.Path, default=INSTANCE)
    parser.add_argument("--profile", default=PROFILE)
    parser.add_argument(
        "--human-acceptance", action="store_true",
        help="explicit user capability: ingest a separate V7 human-acceptance receipt")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.plan is None or args.evidence is None:
        parser.error("--plan and --evidence are required")
    try:
        result = ingest(
            args.plan, args.evidence, repo=args.repo, instance=args.instance,
            profile=args.profile, human_acceptance=args.human_acceptance)
    except ResultError as exc:
        print(f"verification result rejected: {exc}", file=sys.stderr)
        return 1
    verb = "updated" if result["changed"] else "already recorded in"
    print(f"{verb} {result['plan']}: status={result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
