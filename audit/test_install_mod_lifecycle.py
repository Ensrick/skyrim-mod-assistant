"""Offline lifecycle regressions for install_mod.py.

This suite never invokes MO2, Nexus, the curator, or the live profile.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile

import install_mod as subject
import test_install_mod_two_pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    checks = 0

    previous = {
        "modId": 1,
        "modName": "Example",
        "note": "reviewed intent",
        "disabledPlugins": ["Optional Patch.esp"],
        "impactPolicy": {"mode": "declared-inputs", "inputs": ["Example"]},
        "archivedTo": "old-path",
    }
    merged = subject._ledger_row(
        previous,
        modId=1,
        modName="Example",
        version="2.0",
        plugins=["Example.esp", "Optional Patch.esp"],
        enabled=True,
    )
    check(merged["note"] == "reviewed intent", "update erased the reviewed note")
    check(merged["disabledPlugins"] == ["Optional Patch.esp"],
          "update erased deliberate disabled-plugin intent")
    check(merged["impactPolicy"]["mode"] == "declared-inputs",
          "update erased patch-impact policy")
    check("archivedTo" not in merged, "reinstalled live row retained archivedTo")
    checks += 4

    plugins = ["Core.esp", "Optional.esp", "New Patch.esp"]
    before = {"core.esp": True, "optional.esp": False}
    check(subject._desired_active_plugins(plugins, True, True, before) == {"core.esp"},
          "update did not preserve exact prior active membership")
    check(subject._desired_active_plugins(plugins, True, False, before) ==
          {"core.esp", "optional.esp", "new patch.esp"},
          "new install did not select all installed plugins")
    check(not subject._desired_active_plugins(plugins, False, True, before),
          "parked update attempted to activate a plugin")
    checks += 3

    check(subject._replacement_identity_error({"modId": 1}, 2) is not None,
          "cross-Nexus-ID replacement did not require a curator migration")
    check(subject._replacement_identity_error({"modId": 1}, 1) is None,
          "same-Nexus-ID update was incorrectly rejected")
    check(subject._valid_issue_reference("#102") and
          subject._valid_issue_reference("102") and
          subject._valid_issue_reference(
              "https://github.com/Ensrick/skyrim-mod-assistant/issues/102"),
          "valid durable issue references were rejected")
    check(not subject._valid_issue_reference("remember this later"),
          "free-form prose was accepted as a durable issue reference")
    check(subject.sort_order() == 78,
          "unaudited LOOT order mutation was not refused")
    checks += 5

    with tempfile.TemporaryDirectory(prefix="change-kinds-") as raw:
        root = pathlib.Path(raw)
        (root / "SKSE" / "Plugins").mkdir(parents=True)
        (root / "scripts").mkdir()
        (root / "SKSE" / "Plugins" / "Example.dll").write_bytes(b"dll")
        (root / "scripts" / "Example.pex").write_bytes(b"pex")
        (root / "Example.esl").write_bytes(b"plugin")
        check(subject._change_kinds(root) ==
              ["native", "script", "plugin", "worldspace"],
              "payload risk classification did not fail conservatively on an "
              "unparseable runtime-bearing plugin")
        checks += 1
        config_root = root / "config-only"
        config_root.mkdir()
        (config_root / "runtime.toml").write_text("enabled=true\n", encoding="utf-8")
        check(subject._change_kinds(config_root) == ["config"],
              "configuration-only payload was weakened to asset-only testing")
        checks += 1

    old_repo_for_plan = subject.REPO
    try:
        with tempfile.TemporaryDirectory(prefix="fomod-plan-") as raw:
            fixture_repo = pathlib.Path(raw) / "repo"
            allowed = fixture_repo / "records" / "fomod-plans"
            allowed.mkdir(parents=True)
            good = allowed / "good.json"
            good.write_text('{"schemaVersion":1,"mappings":[]}\n', encoding="utf-8")
            outside = pathlib.Path(raw) / "outside.json"
            outside.write_text('{"schemaVersion":1,"mappings":[]}\n', encoding="utf-8")
            subject.REPO = str(fixture_repo)
            snapshot = subject._fomod_plan_snapshot(good)
            check(snapshot["relative"] == "records/fomod-plans/good.json" and
                  len(snapshot["sha256"]) == 64,
                  "confined FOMOD plan did not produce stable provenance")
            try:
                subject._fomod_plan_snapshot(outside)
                escaped = True
            except ValueError:
                escaped = False
            check(not escaped, "FOMOD plan outside records/fomod-plans was accepted")
            checks += 2
    finally:
        subject.REPO = old_repo_for_plan

    check(subject._install_impl(
        1, "Internal Replace Fixture", replace=True, issue="102") == 78,
        "internal _install_impl bypassed the fail-closed replacement gate")
    checks += 1

    old_tasklist = subject.subprocess.run
    old_judge = subject.HP.judge
    old_describe = subject.HP.describe
    old_log_refusal = subject.HP.log_refusal
    logged = []
    try:
        subject.subprocess.run = lambda *_args, **_kwargs: type(
            "TaskListResult", (), {"stdout": "SkyrimSE.exe 1234"})()
        subject.HP.judge = lambda: {"human": False}
        subject.HP.describe = lambda _verdict: "nobody detected by probe"
        subject.HP.log_refusal = lambda *_args, **_kwargs: logged.append(True)
        try:
            subject.refuse_if_human_playing("fixture install")
            blocked = False
        except SystemExit as exc:
            blocked = exc.code == subject.claim.ExTempFail
        check(blocked and not logged,
              "apparently idle live Skyrim did not block profile mutation")
        checks += 1
    finally:
        subject.subprocess.run = old_tasklist
        subject.HP.judge = old_judge
        subject.HP.describe = old_describe
        subject.HP.log_refusal = old_log_refusal

    old_temp = os.environ.get("TEMP")
    old_audit = subject.keep_coverage.audit
    old_decisions = subject.keep_coverage.curator_decisions
    old_queued = subject.keep_coverage.queued_keeps
    old_installed_ids = subject.keep_coverage.installed_ids
    old_mo2 = subject.mo2
    old_ledger = subject.LEDGER
    try:
        with tempfile.TemporaryDirectory(prefix="journal-recovery-") as raw:
            journal_root = pathlib.Path(raw)
            (journal_root / "headless-journal").mkdir()

            def committed_but_truncated(*args, root=None):
                tx = pathlib.Path(root) / "headless-journal" / "tx-recovered"
                tx.mkdir()
                (tx / "transaction.json").write_text(json.dumps({
                    "schemaVersion": 1,
                    "id": "tx-recovered",
                    "operation": args[0],
                    "instanceRoot": str(pathlib.Path(root)),
                    "committed": True,
                    "rolledBack": False,
                    "files": [],
                    "moves": [],
                }), encoding="utf-8")
                return {"ok": False, "raw": "truncated response"}

            subject.mo2 = committed_but_truncated
            recovered = subject.mo2_mutation(
                "mod-enable", "Fixture", root=journal_root)
            check(recovered.get("ok") and
                  recovered.get("transaction") == "tx-recovered" and
                  recovered.get("recoveredFromJournal"),
                  "ambiguous response was not recovered from its exact journal")

            subject.mo2 = lambda *_args, **_kwargs: {
                "ok": True, "transaction": "unbacked-tx"}
            unbacked = subject.mo2_mutation(
                "plugin-enable", "Fixture.esp", root=journal_root)
            check(not unbacked.get("ok"),
                  "unbacked controller success was accepted despite a live journal")
            checks += 2
            subject.mo2 = old_mo2

        with tempfile.TemporaryDirectory(prefix="install-lifecycle-") as raw:
            os.environ["TEMP"] = raw
            pending = pathlib.Path(raw) / "nlc-relay" / "decisions-pending.json"
            pending.parent.mkdir(parents=True)

            skip = [{
                "status": "skip",
                "mod": {"game": "skyrimspecialedition", "modId": "42"},
            }]
            pending.write_text(json.dumps(skip), encoding="utf-8")
            check(not subject.queue_keep(42, "Must Not Override Skip"),
                  "queued Skip was misreported or rewritten as Keep")
            check(json.loads(pending.read_text(encoding="utf-8")) == skip,
                  "refused Skip changed the pending batch")
            checks += 2

            stale = [{
                "status": "keep",
                "mod": {"game": "skyrimspecialedition", "modId": "47"},
                "queuedAt": "2000-01-01T00:00:00Z",
            }]
            pending.write_text(json.dumps(stale), encoding="utf-8")
            queued, change = subject.queue_keep(47, "Refresh Fixture", with_receipt=True)
            refreshed = json.loads(pending.read_text(encoding="utf-8"))
            check(queued and change and len(refreshed) == 1 and
                  refreshed[0]["queuedAt"] != stale[0]["queuedAt"],
                  "expired same-ID Keep was misreported as current instead of refreshed")
            check(subject.keep_coverage.pending_keep_id(refreshed[0]) == 47,
                  "refreshed Keep was not immediately valid to the coverage gate")
            checks += 2

            leading_zero = [{
                "status": "keep",
                "mod": {"game": "skyrimspecialedition", "modId": "0047"},
                "queuedAt": "2026-09-04T00:00:00Z",
            }]
            pending.write_text(json.dumps(leading_zero), encoding="utf-8")
            before_noncanonical = pending.read_bytes()
            check(not subject.queue_keep(47, "Canonical Identity Fixture"),
                  "noncanonical same-ID Keep was silently duplicated")
            check(pending.read_bytes() == before_noncanonical,
                  "refused noncanonical Keep batch was modified")
            checks += 2

            other_game = [{
                "status": "keep",
                "mod": {"game": "skyrim", "modId": "43"},
            }]
            pending.write_text(json.dumps(other_game), encoding="utf-8")
            check(subject.queue_keep(43, "SSE Target"),
                  "same numeric ID in another game blocked the SSE Keep")
            batch = json.loads(pending.read_text(encoding="utf-8"))
            check(len(batch) == 2 and batch[-1]["mod"]["game"] == "skyrimspecialedition",
                  "SSE Keep was not appended with game-scoped identity")
            checks += 2

            check(subject.queue_keep(43, "SSE Target"),
                  "an exact queued Keep was not idempotent")
            check(len(json.loads(pending.read_text(encoding="utf-8"))) == 2,
                  "idempotent Keep created a duplicate")
            checks += 2

            clean = {
                "installedWithoutKeep": [],
                "keepNotInstalled": [],
                "skipInstalled": [],
            }
            subject.keep_coverage.audit = lambda: clean
            subject.keep_coverage.queued_keeps = lambda **_kwargs: set()
            subject.keep_coverage.installed_ids = lambda: {"Existing": {43}}
            subject.keep_coverage.curator_decisions = lambda: {
                44: {"status": "skip"},
            }
            check(not subject._curation_precondition(44, "Live Skip"),
                  "live curator Skip did not block installation")
            checks += 1

            subject.keep_coverage.curator_decisions = lambda: {}
            check(subject._curation_precondition(45, "Approved Target"),
                  "clean unreviewed target did not pass curation preflight")
            staged = json.loads(pending.read_text(encoding="utf-8"))
            check(not any(e.get("mod", {}).get("modId") == "45" for e in staged),
                  "precondition queued Keep before the install committed")
            checks += 2

            # The global queue gate still rejects an expired row, but an
            # install of that exact ID may proceed to queue_keep's atomic
            # refresh. Expiry anywhere else, malformed evidence and duplicate
            # identities remain blockers.
            real_queued_keeps = old_queued
            subject.keep_coverage.queued_keeps = real_queued_keeps
            expired_target = [{
                "status": "keep",
                "mod": {"game": "skyrimspecialedition", "modId": "49"},
                "queuedAt": "2000-01-01T00:00:00Z",
            }]
            pending.write_text(json.dumps(expired_target), encoding="utf-8")
            check(subject._curation_precondition(49, "Refresh Exact Target"),
                  "exact expired target could not reach the atomic refresh path")
            check(not subject._curation_precondition(50, "Different Target"),
                  "expired Keep for another ID was weakened to an install exception")
            malformed_target = [{**expired_target[0], "queuedAt": "2026-09-04T12:00:00"}]
            pending.write_text(json.dumps(malformed_target), encoding="utf-8")
            check(not subject._curation_precondition(49, "Malformed Target"),
                  "timezone-less approval evidence was treated as refreshable")
            pending.write_text(json.dumps(expired_target * 2), encoding="utf-8")
            check(not subject._curation_precondition(49, "Duplicate Target"),
                  "duplicate expired target rows were treated as refreshable")
            subject.keep_coverage.queued_keeps = lambda **_kwargs: set()
            checks += 4

            subject.keep_coverage.audit = lambda: {
                **clean,
                "installedWithoutKeep": [{"modId": 99, "mods": ["Drift"]}],
            }
            check(not subject._curation_precondition(46, "Blocked By Drift"),
                  "unreconciled installed/Keep state did not block another install")
            checks += 1

            ledger = pathlib.Path(raw) / "ledger.json"
            before_bytes = b'{"before":true}\n'
            ledger.write_bytes(before_bytes)
            subject.LEDGER = str(ledger)
            ledger.write_bytes(b'{"after":true}\n')
            calls = []
            subject.mo2 = lambda *args, **_kwargs: (
                calls.append(args) or {"ok": True})
            check(subject._rollback_transactions(
                ["install-tx", "plugin-tx"], (True, before_bytes)),
                "logical rollback reported failure")
            check(calls == [("rollback", "plugin-tx"), ("rollback", "install-tx")],
                  "logical rollback was not last-applied-first")
            check(ledger.read_bytes() == before_bytes,
                  "logical rollback did not restore exact ledger bytes")
            checks += 3

            check(not subject._rollback_transactions([None]),
                  "missing transaction ID was reported as safely rolled back")
            checks += 1

            before_spool = pending.read_bytes()
            queued, change = subject.queue_keep(48, "Rollback Fixture", with_receipt=True)
            check(queued and pending.read_bytes() != before_spool,
                  "curator rollback fixture did not mutate its spool")
            logical = subject._LogicalInstall()
            logical.begin("curator-tx", (False, b""))
            logical.curator_change = change
            check(logical.abort("fixture abort") and pending.read_bytes() == before_spool,
                  "logical rollback did not restore exact curator spool bytes")
            checks += 2

            old_impl = subject._install_impl
            old_rollback = subject._rollback_transactions
            rollback_calls = []

            def crash_after_apply(*args, **kwargs):
                logical = args[-1]
                logical.begin("fault-tx", (False, b""))
                raise RuntimeError("fault injection after apply")

            subject._install_impl = crash_after_apply
            subject._rollback_transactions = lambda transactions, ledger_snapshot=None: (
                rollback_calls.append((list(transactions), ledger_snapshot)) or True)
            check(subject._install(1, "Fault Fixture", issue="102") == 1,
                  "unexpected post-apply exception did not become a controlled failure")
            check(rollback_calls == [(["fault-tx"], None)],
                  "unexpected post-apply exception did not roll back exactly once")
            checks += 2
            subject._install_impl = old_impl
            subject._rollback_transactions = old_rollback
    finally:
        subject.keep_coverage.audit = old_audit
        subject.keep_coverage.curator_decisions = old_decisions
        subject.keep_coverage.queued_keeps = old_queued
        subject.keep_coverage.installed_ids = old_installed_ids
        subject.mo2 = old_mo2
        subject.LEDGER = old_ledger
        if 'old_impl' in locals():
            subject._install_impl = old_impl
        if 'old_rollback' in locals():
            subject._rollback_transactions = old_rollback
        if old_temp is None:
            os.environ.pop("TEMP", None)
        else:
            os.environ["TEMP"] = old_temp

    check(test_install_mod_two_pass.main() == 0,
          "real two-pass integration suite failed")
    checks += 1
    print(f"install_mod lifecycle tests PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
