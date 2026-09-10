"""CLI wiring tests; binary checkpoint tests live in test_currency_save_gate."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import currency_save_gate as gate


class CurrencyCliTests(unittest.TestCase):
    def invoke(self, extra, blockers):
        output = io.StringIO()
        with patch.object(gate, 'check_save', return_value=blockers) as check:
            with contextlib.redirect_stdout(output):
                status = gate.main(['--instance', 'instance', '--game-data', 'Data',
                                    '--profile', 'Test Profile', *extra])
        return status, json.loads(output.getvalue()), check.call_args

    def test_refuses_exact_save_and_passes_profile(self):
        status, result, args = self.invoke(['--save', 'test.ess'], ['missing checkpoint'])
        self.assertEqual(1, status)
        self.assertEqual('REFUSED', result['verdict'])
        self.assertEqual(['missing checkpoint'], result['blockers'])
        self.assertEqual((Path('instance'), Path('Data'), Path('test.ess'), 'Test Profile'), args.args)

    def test_admitted_save_has_limited_scope(self):
        status, result, _ = self.invoke(['--save', 'test.ess'], [])
        self.assertEqual(0, status)
        self.assertEqual('CURRENCY-ADMITTED', result['verdict'])
        self.assertIn('not save health', result['scope'])

    def test_menu_only_still_checks_package_without_admitting_save(self):
        status, result, args = self.invoke([], [])
        self.assertEqual(0, status)
        self.assertIsNone(args.args[2])
        self.assertIsNone(result['save'])
        self.assertIn('no saved game is admitted', result['scope'])
        self.assertEqual(1, self.invoke([], ['incomplete package'])[0])

    def test_path_profiles_never_reach_checker(self):
        for profile in ('..', '.', '../Default', r'..\Default', 'C:Default', ' '):
            with self.subTest(profile=profile), patch.object(gate, 'check_save') as check:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    gate.main(['--instance', 'instance', '--game-data', 'Data', '--profile', profile])
                check.assert_not_called()


if __name__ == '__main__':
    unittest.main()
