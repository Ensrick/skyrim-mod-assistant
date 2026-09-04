"""Offline lifecycle regressions for install_mod.py.

This suite never invokes MO2, Nexus, the curator, or the live profile.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile

import install_mod as subject


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

    old_temp = os.environ.get("TEMP")
    old_audit = subject.keep_coverage.audit
    old_decisions = subject.keep_coverage.curator_decisions
    old_queued = subject.keep_coverage.queued_keeps
    old_installed_ids = subject.keep_coverage.installed_ids
    old_mo2 = subject.mo2
    old_ledger = subject.LEDGER
    try:
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
            subject.keep_coverage.queued_keeps = lambda: set()
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
    finally:
        subject.keep_coverage.audit = old_audit
        subject.keep_coverage.curator_decisions = old_decisions
        subject.keep_coverage.queued_keeps = old_queued
        subject.keep_coverage.installed_ids = old_installed_ids
        subject.mo2 = old_mo2
        subject.LEDGER = old_ledger
        if old_temp is None:
            os.environ.pop("TEMP", None)
        else:
            os.environ["TEMP"] = old_temp

    print(f"install_mod lifecycle tests PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
