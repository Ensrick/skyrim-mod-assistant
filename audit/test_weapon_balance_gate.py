"""Synthetic tests; no live MO2 profile or game is touched."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

if __package__:
    from . import weapon_balance_gate as gate
else:
    import weapon_balance_gate as gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="weapon-gate-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.repo, self.instance = self.root / "repo", self.root / "instance"
        self.profile = self.instance / "profiles" / "Default"
        self.profile.mkdir(parents=True)
        self.plugins = self.profile / "plugins.txt"
        self.plugins.write_text("*WeaponBalancePatch.esp\n", encoding="utf-8")
        self.script = self.repo / "mods" / "weapon-balance" / "audit.ps1"
        self.script.parent.mkdir(parents=True)
        self.script.write_text("# synthetic verifier placeholder", encoding="utf-8")
        (self.instance / "mods" / gate.MOD_FOLDER).mkdir(parents=True)
        self.fails, self.warns = [], []

    def check(self, runner):
        gate.run(self.fails, self.warns, repo=self.repo, instance=self.instance, runner=runner)

    def test_success_is_readonly_command(self):
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="PASS", stderr=""))
        self.check(runner)
        self.assertEqual([], self.fails)
        args, kwargs = runner.call_args
        self.assertIn("-FreshnessOnly", args[0])
        self.assertIn("-ArtifactRoot", args[0])
        self.assertNotIn("run", args[0])
        self.assertEqual(180, kwargs["timeout"])

    def test_disabled_does_not_run(self):
        self.plugins.write_text("WeaponBalancePatch.esp\n", encoding="utf-8")
        runner = Mock()
        self.check(runner)
        runner.assert_not_called()
        self.assertEqual([], self.fails)

    def test_nonzero_even_with_pass_text_fails(self):
        runner = Mock(return_value=SimpleNamespace(returncode=2, stdout="PASS old audit", stderr="input hash changed"))
        self.check(runner)
        self.assertIn("input hash changed", self.fails[0])

    def test_missing_verifier_fails(self):
        self.script.unlink()
        runner = Mock()
        self.check(runner)
        runner.assert_not_called()
        self.assertIn("lacks", self.fails[0])

    def test_timeout_fails_closed(self):
        self.check(Mock(side_effect=subprocess.TimeoutExpired("pwsh", 180)))
        self.assertIn("TimeoutExpired", self.fails[0])

    def test_missing_profile_fails(self):
        self.plugins.unlink()
        runner = Mock()
        self.check(runner)
        runner.assert_not_called()
        self.assertIn("missing", self.fails[0])

    def test_bom_whitespace_case(self):
        self.plugins.write_text("  *WEAPONBALANCEPATCH.ESP \n", encoding="utf-8-sig")
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="", stderr=""))
        self.check(runner)
        runner.assert_called_once()


if __name__ == "__main__":
    unittest.main()
