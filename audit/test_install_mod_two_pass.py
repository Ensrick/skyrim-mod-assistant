"""Offline integration tests for install_mod's real two-pass controller.

The fixture replaces only external authorities (Nexus download, MO2 process,
human-presence probe) and redirects every durable path beneath a temporary
directory.  ``install_mod._install`` and ``_install_impl`` remain real.
"""

from __future__ import annotations

import builtins
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types


AUDIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AUDIT))

import install_mod as subject


MOD_ID = 424242
FILE_ID = 515151
MOD_NAME = "Two Pass Fixture"
ISSUE = "#228"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def is_enabled(modlist: pathlib.Path, name: str) -> bool | None:
    wanted = name.casefold()
    for line in modlist.read_text(encoding="utf-8-sig").splitlines():
        if line[:1] in "+-" and line[1:].strip().casefold() == wanted:
            return line.startswith("+")
    return None


class FakeMO2:
    """Stateful MO2 journal with byte-exact rollback for one target mod."""

    def __init__(self, instance: pathlib.Path, events: list[str]):
        self.instance = instance
        self.profile = instance / "profiles" / "Default"
        self.modlist = self.profile / "modlist.txt"
        self.plugins = self.profile / "plugins.txt"
        self.events = events
        self.transactions: dict[str, dict] = {}
        self.sequence = 0

    def _tree(self, root: pathlib.Path) -> tuple[bool, dict[str, bytes]]:
        if not root.is_dir():
            return False, {}
        return True, {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()
        }

    def _snapshot(self, mod_name: str) -> dict:
        target = self.instance / "mods" / mod_name
        return {
            "modName": mod_name,
            "target": self._tree(target),
            "modlist": self.modlist.read_bytes(),
            "plugins": self.plugins.read_bytes(),
        }

    def _restore(self, snapshot: dict) -> None:
        target = self.instance / "mods" / snapshot["modName"]
        if target.exists():
            shutil.rmtree(target)
        existed, files = snapshot["target"]
        if existed:
            target.mkdir(parents=True)
            for relative, payload in files.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
        self.modlist.write_bytes(snapshot["modlist"])
        self.plugins.write_bytes(snapshot["plugins"])

    def _transaction(self, mod_name: str) -> str:
        self.sequence += 1
        transaction = f"fixture-tx-{self.sequence}"
        self.transactions[transaction] = self._snapshot(mod_name)
        return transaction

    def _set_mod(self, mod_name: str, enabled: bool) -> None:
        rows = [
            line for line in self.modlist.read_text(
                encoding="utf-8-sig").splitlines()
            if not (line[:1] in "+-" and
                    line[1:].strip().casefold() == mod_name.casefold())
        ]
        rows.append(("+" if enabled else "-") + mod_name)
        self.modlist.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def __call__(self, *args, root=None):
        command = args[0]
        if command == "plugin-list":
            return {"ok": True, "plugins": []}
        if command == "mod-install":
            archive = pathlib.Path(args[1])
            mod_name = str(args[2])
            transaction = self._transaction(mod_name)
            target = self.instance / "mods" / mod_name
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True)
            (target / "payload.bin").write_bytes(archive.read_bytes())
            self._set_mod(mod_name, enabled="--disable" not in args)
            self.events.append("mod-install")
            return {"ok": True, "transaction": transaction}
        if command in {"mod-enable", "mod-disable"}:
            mod_name = str(args[1])
            transaction = self._transaction(mod_name)
            self._set_mod(mod_name, command == "mod-enable")
            self.events.append(command)
            return {"ok": True, "transaction": transaction}
        if command == "rollback":
            transaction = str(args[1])
            snapshot = self.transactions.get(transaction)
            if snapshot is None:
                return {"ok": False, "error": "unknown fixture transaction"}
            self._restore(snapshot)
            self.events.append("rollback:" + transaction)
            return {"ok": True}
        return {"ok": False, "error": f"unsupported fixture command: {command}"}


class Sandbox:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="two-pass-install-")
        self.root = pathlib.Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.instance = self.root / "instance"
        self.profile = self.instance / "profiles" / "Default"
        self.mods = self.instance / "mods"
        self.ledger = self.repo / "records" / "installed-mods.json"
        self.archive = self.root / "vendor-archive.bin"
        self.pending = self.root / "nlc-relay" / "decisions-pending.json"
        self.events: list[str] = []
        self.fail_post_ledger = False
        self.originals: list[tuple[object, str, object]] = []
        self.old_temp = os.environ.get("TEMP")
        self.old_modasset = sys.modules.get("modasset")

    def patch(self, owner: object, name: str, value: object) -> None:
        self.originals.append((owner, name, getattr(owner, name)))
        setattr(owner, name, value)

    def __enter__(self):
        self.profile.mkdir(parents=True)
        self.mods.mkdir(parents=True)
        (self.instance / "overwrite").mkdir()
        (self.repo / "audit").mkdir(parents=True)
        (self.repo / "records" / "source-builds").mkdir(parents=True)
        (self.repo / "records" / "impact-receipts").mkdir(parents=True)
        (self.repo / "records" / "fomod-plans").mkdir(parents=True)
        (self.repo / "audit" / "watched_configs.json").write_text(
            '{"watch": []}\n', encoding="utf-8")
        self.profile.joinpath("modlist.txt").write_bytes(b"")
        self.profile.joinpath("plugins.txt").write_bytes(b"")
        self.ledger.write_text(json.dumps({
            "schemaVersion": 1,
            "instance": str(self.instance),
            "profile": "Default",
            "mods": [],
        }, indent=2) + "\n", encoding="utf-8")
        self.before_ledger = self.ledger.read_bytes()
        self.before_modlist = self.profile.joinpath("modlist.txt").read_bytes()
        self.before_plugins = self.profile.joinpath("plugins.txt").read_bytes()
        self.archive.write_bytes(b"ARCHIVE-V1")
        os.environ["TEMP"] = str(self.root)

        fake_modasset = types.ModuleType("modasset")
        file_row = {
            "file_id": FILE_ID,
            "name": "Fixture main file",
            "version": "1.0",
            "file_name": self.archive.name,
            "size_kb": 1,
        }
        fake_modasset.v1 = lambda _route: {"files": [dict(file_row)]}
        fake_modasset.pick_file = lambda _mid, prefer=None: dict(file_row)
        fake_modasset.download = lambda _mid, _row: str(self.archive)
        fake_modasset.BSA = type(
            "EmptyBSA", (), {
                "__init__": lambda _self, _path: None,
                "names": lambda _self: [],
            })
        sys.modules["modasset"] = fake_modasset

        self.fake_mo2 = FakeMO2(self.instance, self.events)
        self.patch(subject, "REPO", str(self.repo))
        self.patch(subject, "INSTANCE", str(self.instance))
        self.patch(subject, "LEDGER", str(self.ledger))
        self.patch(subject, "mo2", self.fake_mo2)
        self.patch(subject, "refuse_if_human_playing", lambda _what: None)
        self.patch(subject, "_curation_precondition", lambda _mid, _name: True)
        self.patch(subject.patch_impact, "REPO", self.repo)

        real_audit = subject.patch_impact.audit

        def audited(*args, **kwargs):
            state = is_enabled(self.profile / "modlist.txt", MOD_NAME)
            check(state is False,
                  "patch-impact audit did not observe the staged mod disabled")
            self.events.append("impact-audit-disabled")
            return real_audit(*args, **kwargs)

        self.patch(subject.patch_impact, "audit", audited)
        real_validate = subject.patch_impact.validate_receipt

        def validated(*args, **kwargs):
            result = real_validate(*args, **kwargs)
            self.events.append("receipt-valid" if not result else "receipt-rejected")
            return result

        self.patch(subject.patch_impact, "validate_receipt", validated)

        real_build = subject.verification_plan.build_fingerprint

        def isolated_fingerprint(instance, profile, ledger):
            return real_build(pathlib.Path(instance), profile, pathlib.Path(ledger),
                              repo_root=self.repo, game_root=None)

        self.patch(subject.verification_plan, "build_fingerprint", isolated_fingerprint)

        real_reconcile = subject.profile_reconcile.reconcile

        def reconciled():
            self.events.append("reconcile")
            if self.fail_post_ledger:
                self.fail_post_ledger = False
                raise RuntimeError("fixture failure after ledger commit")
            return real_reconcile(
                self.instance, "Default", self.ledger, self.root / "Data",
                self.repo)

        self.patch(subject.profile_reconcile, "reconcile", reconciled)

        real_save = subject.save

        def saved(document):
            real_save(document)
            self.events.append("ledger")

        self.patch(subject, "save", saved)
        real_write_json = subject._write_json_atomic

        def wrote_json(path, document):
            real_write_json(path, document)
            if pathlib.Path(path).parent.name == "test-plans":
                self.events.append("plan")

        self.patch(subject, "_write_json_atomic", wrote_json)
        real_queue_keep = subject.queue_keep

        def queued_keep(*args, **kwargs):
            result = real_queue_keep(*args, **kwargs)
            okay = result[0] if isinstance(result, tuple) else result
            if okay:
                self.events.append("keep")
            return result

        self.patch(subject, "queue_keep", queued_keep)
        return self

    def __exit__(self, *_exc):
        for owner, name, value in reversed(self.originals):
            setattr(owner, name, value)
        if self.old_modasset is None:
            sys.modules.pop("modasset", None)
        else:
            sys.modules["modasset"] = self.old_modasset
        if self.old_temp is None:
            os.environ.pop("TEMP", None)
        else:
            os.environ["TEMP"] = self.old_temp
        self.temporary.cleanup()

    def install(self, receipt: pathlib.Path | None = None,
                plan: pathlib.Path | None = None) -> int:
        return subject._install(
            MOD_ID, MOD_NAME, plan=str(plan) if plan else None, file_id=FILE_ID,
            impact_receipt=str(receipt) if receipt else None,
            issue=ISSUE,
        )

    def draft(self) -> pathlib.Path:
        drafts = list((self.repo / "records" / "impact-receipts").glob("*.json"))
        check(len(drafts) == 1, f"expected one impact draft, got {len(drafts)}")
        return drafts[0]

    def review(self, path: pathlib.Path) -> None:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["intakeReview"] = {
            "userApproval": {
                "approved": True,
                "evidence": "User-approved fixture recorded on issue #228.",
            },
            "fileSelection": {
                "reviewed": True,
                "evidence": f"Pinned exact fixture main file ID {FILE_ID}.",
            },
            "permissions": {
                "classification": "external-download",
                "evidence": "Fixture models an immutable vendor download.",
            },
            "requirements": {
                "reviewed": True,
                "requiredPatches": [],
                "evidence": "Fixture inventory has no external requirements.",
            },
            "compatibility": {
                "reviewed": True,
                "lootEvidence": "Fixture has no plugins for LOOT to evaluate.",
                "conflictEvidence": "Fixture contains one unique payload path.",
                "openDecisions": [],
            },
        }
        receipt["review"] = {
            "reviewedBy": "offline integration fixture",
            "reviewedUtc": "2026-09-04T12:00:00Z",
            "issue": ISSUE,
        }
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    def assert_exact_baseline(self) -> None:
        check(self.ledger.read_bytes() == self.before_ledger,
              "rollback did not restore exact ledger bytes")
        check(self.profile.joinpath("modlist.txt").read_bytes() == self.before_modlist,
              "rollback did not restore exact modlist bytes")
        check(self.profile.joinpath("plugins.txt").read_bytes() == self.before_plugins,
              "rollback did not restore exact plugins.txt bytes")
        check(not (self.mods / MOD_NAME).exists(),
              "rollback left the staged mod folder behind")


def pass_one_and_review(box: Sandbox, plan: pathlib.Path | None = None) -> pathlib.Path:
    check(box.install(plan=plan) == 1, "first pass unexpectedly committed")
    check("impact-audit-disabled" in box.events,
          "first pass did not inspect a disabled staging image")
    check(any(event.startswith("rollback:") for event in box.events),
          "first pass did not roll its MO2 transaction back")
    box.assert_exact_baseline()
    draft = box.draft()
    box.review(draft)
    return draft


def test_success() -> int:
    with Sandbox() as box:
        fomod = box.repo / "records" / "fomod-plans" / "fixture.json"
        fomod.write_text(
            '{"schemaVersion":1,"mappings":[{"source":".","destination":"."}]}\n',
            encoding="utf-8")
        fomod_hash = subject.patch_impact.sha256_file(fomod)
        receipt = pass_one_and_review(box, fomod)
        box.events.clear()
        check(box.install(receipt, fomod) == 0, "reviewed second pass did not commit")
        expected = [
            "mod-install", "impact-audit-disabled", "receipt-valid",
            "mod-enable", "ledger", "reconcile", "ledger", "plan", "keep",
        ]
        observed = [event for event in box.events if event in expected]
        check(observed == expected,
              f"second-pass postconditions were out of order: {observed}")
        check(is_enabled(box.profile / "modlist.txt", MOD_NAME) is True,
              "accepted second pass did not activate the mod")
        ledger = json.loads(box.ledger.read_text(encoding="utf-8"))
        row = ledger["mods"][0]
        check(row["impactReceipt"] == receipt.relative_to(box.repo).as_posix(),
              "ledger did not bind the reviewed receipt")
        check(row["fomodPlan"] == "records/fomod-plans/fixture.json" and
              row["fomodPlanSha256"] == fomod_hash,
              "ledger did not bind the confined FOMOD plan bytes")
        plan = box.repo / row["verificationPlan"]
        check(plan.is_file(), "accepted second pass did not write its test plan")
        plan_document = json.loads(plan.read_text(encoding="utf-8"))
        check(plan_document["source"]["fomodPlan"] == row["fomodPlan"] and
              plan_document["source"]["fomodPlanSha256"] == fomod_hash,
              "verification provenance did not bind the FOMOD plan hash")
        pending = json.loads(box.pending.read_text(encoding="utf-8"))
        check(pending[0]["status"] == "keep" and
              pending[0]["mod"]["modId"] == str(MOD_ID),
              "accepted second pass did not queue its exact Keep")
    return 12


def test_stale_payload() -> int:
    with Sandbox() as box:
        receipt = pass_one_and_review(box)
        box.archive.write_bytes(b"ARCHIVE-V2-DIFFERENT")
        box.events.clear()
        check(box.install(receipt) == 1, "stale payload/receipt was accepted")
        check("receipt-rejected" in box.events,
              "stale payload did not reach exact receipt rejection")
        check("mod-enable" not in box.events,
              "stale payload was transiently activated before rejection")
        box.assert_exact_baseline()
    return 4


def test_post_ledger_failure() -> int:
    with Sandbox() as box:
        receipt = pass_one_and_review(box)
        box.fail_post_ledger = True
        box.events.clear()
        check(box.install(receipt) == 1,
              "post-ledger fault unexpectedly reported success")
        check(box.events.index("ledger") < box.events.index("reconcile"),
              "fixture fault did not occur after the ledger commit")
        rollback_events = [event for event in box.events if event.startswith("rollback:")]
        check(len(rollback_events) == 2,
              f"post-ledger fault did not reverse both MO2 mutations: {rollback_events}")
        box.assert_exact_baseline()
        check(not box.pending.exists(), "failed transaction left a Keep queued")
        plans = list((box.repo / "records" / "test-plans").glob("*.json")) \
            if (box.repo / "records" / "test-plans").is_dir() else []
        check(not plans, "failed transaction left a live verification plan")
    return 7


def test_ambiguous_controller_failure() -> int:
    with Sandbox() as box:
        normal = box.fake_mo2

        def mutate_then_lose_response(*args, root=None):
            if args[0] != "mod-install":
                return normal(*args, root=root)
            mod_name = str(args[2])
            target = box.mods / mod_name
            target.mkdir(parents=True)
            (target / "orphaned.bin").write_bytes(b"MUTATED")
            normal._set_mod(mod_name, enabled=False)
            return {"ok": False, "raw": "truncated controller response",
                    "unresolvedJournals": ["fixture-uncommitted"]}

        subject.mo2 = mutate_then_lose_response
        check(box.install() == 1,
              "ambiguous controller failure unexpectedly reported success")
        box.assert_exact_baseline()
        recovery = box.repo / "records" / "lifecycle-recovery.jsonl"
        check(recovery.is_file(), "ambiguous recovery left no durable receipt")
        event = json.loads(recovery.read_text(encoding="utf-8").splitlines()[-1])
        check(event["exactPostcondition"] and event["reconciledPostcondition"],
              "recovery receipt did not prove exact/reconciled postconditions")
        quarantined = list((box.instance / ".assistant-recovery").glob("*"))
        check(len(quarantined) == 1,
              "unjournaled target was not retained in one recovery quarantine")
    return 5


def test_first_mutation_journal_exception() -> int:
    """A fault discovering the first transaction must restore before-images.

    This is the narrow ambiguity window which originally existed between the
    controller committing ``mod-install`` and the caller learning its journal
    ID.  The real ``mo2_mutation`` path runs; only its second journal scan is
    fault-injected.
    """
    with Sandbox() as box:
        scans = 0

        def journal_scan(_root=None):
            nonlocal scans
            scans += 1
            if scans == 2:
                raise PermissionError("fixture cannot read post-mutation journal")
            return {}

        box.patch(subject, "_journal_state", journal_scan)
        check(box.install() == 1,
              "post-mutation journal exception unexpectedly reported success")
        check(scans == 2 and "mod-install" in box.events,
              "fault did not occur after the first controller mutation")
        check(not any(event.startswith("rollback:") for event in box.events),
              "fixture unexpectedly relied on a transaction ID it never learned")
        box.assert_exact_baseline()
        check("reconcile" in box.events,
              "first-mutation exception recovery was not reconciled")
    return 5


def test_broken_pipe_after_first_mutation() -> int:
    """A closed diagnostic stream cannot interrupt transactional cleanup."""
    with Sandbox() as box:
        original_print = builtins.print
        injected = False
        injected_after_mutation = False

        def break_once(*args, **kwargs):
            nonlocal injected, injected_after_mutation
            if not injected:
                injected = True
                injected_after_mutation = "mod-install" in box.events
                raise BrokenPipeError("fixture output consumer closed")
            return original_print(*args, **kwargs)

        box.patch(builtins, "print", break_once)
        check(box.install() == 1,
              "first-pass install with a closed output pipe did not stop for review")
        check(injected and injected_after_mutation,
              "BrokenPipe fault was not injected after the first mutation")
        check("impact-audit-disabled" in box.events,
              "diagnostic BrokenPipe interrupted impact auditing")
        check(any(event.startswith("rollback:") for event in box.events),
              "diagnostic BrokenPipe interrupted first-pass rollback")
        box.assert_exact_baseline()
    return 5


def main() -> int:
    checks = (test_success() + test_stale_payload() + test_post_ledger_failure()
              + test_ambiguous_controller_failure()
              + test_first_mutation_journal_exception()
              + test_broken_pipe_after_first_mutation())
    print(f"install_mod two-pass integration PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
