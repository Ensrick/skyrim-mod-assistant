"""Offline CLI regression: an exact-file request must never silently fall back."""
import contextlib
import copy
import io
import sys
import types
import unittest
from unittest import mock

import install_mod


class InstallArgumentsTests(unittest.TestCase):
    def test_both_exact_file_spellings(self):
        for flag in ('--file', '--file-id'):
            args = install_mod.parse_install_arguments([
                '109254', 'BCS ESL Resource', flag, '467900',
                '--plan', 'plan.json', '--replace'])
            self.assertEqual(args.file_id, 467900)
            self.assertEqual(args.mod_id, 109254)
            self.assertEqual(args.plan, 'plan.json')
            self.assertTrue(args.replace)

    def test_unknown_argument_fails_closed(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                install_mod.parse_install_arguments(['901', 'Books', '--fileid', '40352'])
        self.assertEqual(error.exception.code, 2)

    def test_missing_file_number_fails_closed(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                install_mod.parse_install_arguments(['901', 'Books', '--file-id'])
        self.assertEqual(error.exception.code, 2)

    def test_automatic_selection_remains_explicit_default(self):
        args = install_mod.parse_install_arguments(['901', 'Books', '--prefer', 'Original'])
        self.assertIsNone(args.file_id)
        self.assertEqual(args.prefer, 'Original')

    def test_nonpositive_nexus_ids_fail_before_automatic_selection(self):
        cases = [
            ['0', 'Books'], ['-901', 'Books'],
            ['901', 'Books', '--file', '0'],
            ['901', 'Books', '--file-id', '0'],
            ['901', 'Books', '--file', '-40352'],
            ['901', 'Books', '--file-id', '-40352'],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        install_mod.parse_install_arguments(arguments)
                self.assertEqual(error.exception.code, 2)

    def test_abbreviated_options_are_not_silently_accepted(self):
        for flag, value in [('--file-i', '40352'), ('--pref', 'Original')]:
            with self.subTest(flag=flag):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        install_mod.parse_install_arguments(['901', 'Books', flag, value])
                self.assertEqual(error.exception.code, 2)


class InstallLedgerIdentityTests(unittest.TestCase):
    """Exercise real ledger selection with all external boundaries replaced."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.ledger = {'schemaVersion': 1, 'mods': []}
        self.file = {
            'file_id': 467900, 'name': 'Reviewed resource archive',
            'version': '1.0', 'file_name': 'reviewed.zip', 'size_kb': 24,
        }
        # Do not import real modasset: importing it reads a local API credential.
        self.vendor = types.SimpleNamespace(
            v1=mock.Mock(return_value={'files': [self.file]}),
            download=mock.Mock(return_value='in-memory-reviewed-archive.zip'),
            pick_file=mock.Mock(side_effect=AssertionError('unexpected automatic file selection')),
        )
        self.stack.enter_context(mock.patch.dict(sys.modules, {'modasset': self.vendor}))
        self.open_mock = self.stack.enter_context(
            mock.patch('builtins.open', mock.mock_open(read_data=b'reviewed vendor bytes')))
        self.controller = self.stack.enter_context(mock.patch.object(
            install_mod, 'mo2', return_value={'ok': True, 'transaction': 'mock-transaction'}))
        self.stack.enter_context(mock.patch.object(install_mod, 'plugins_of', return_value=[]))
        self.stack.enter_context(mock.patch.object(
            install_mod, 'load', side_effect=lambda: copy.deepcopy(self.ledger)))
        self.saved = self.stack.enter_context(mock.patch.object(
            install_mod, 'save', side_effect=self._capture_ledger))
        self.keeps = self.stack.enter_context(mock.patch.object(install_mod, 'queue_keep'))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def _capture_ledger(self, ledger):
        self.ledger = copy.deepcopy(ledger)

    def test_same_archive_in_two_distinct_mod_folders_keeps_both_rows(self):
        self.assertEqual(install_mod._install(
            109254, 'BCS Resource A', file_id=467900), 0)
        first = copy.deepcopy(self.ledger['mods'][0])

        self.assertEqual(install_mod._install(
            109254, 'BCS Resource B', file_id=467900), 0)

        rows = {row['modName']: row for row in self.ledger['mods']}
        self.assertEqual(set(rows), {'BCS Resource A', 'BCS Resource B'})
        self.assertEqual(rows['BCS Resource A'], first)
        self.assertEqual(rows['BCS Resource A']['fileId'], rows['BCS Resource B']['fileId'])
        self.assertEqual(self.saved.call_count, 2)
        self.vendor.pick_file.assert_not_called()
        self.controller.assert_has_calls([
            mock.call('mod-install', 'in-memory-reviewed-archive.zip', 'BCS Resource A', '--enable'),
            mock.call('mod-install', 'in-memory-reviewed-archive.zip', 'BCS Resource B', '--enable'),
        ])

    def test_replacing_same_folder_preserves_all_unrelated_rows(self):
        sibling = {'modId': 109254, 'modName': 'BCS Resource B', 'fileId': 467900,
                   'enabled': False, 'note': 'Preserve this independently installed component'}
        unrelated = {'modId': 901, 'modName': 'Book Assets', 'fileId': 40352,
                     'enabled': True, 'disabledPlugins': ['Book Covers Skyrim.esp']}
        self.ledger['mods'] = [
            {'modId': 109254, 'modName': 'bcs resource a', 'fileId': 461289,
             'enabled': False, 'transaction': 'old-transaction'},
            copy.deepcopy(sibling), copy.deepcopy(unrelated),
        ]

        self.assertEqual(install_mod._install(
            109254, 'BCS Resource A', replace=True, file_id=467900), 0)

        rows = {row['modName']: row for row in self.ledger['mods']}
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows['BCS Resource B'], sibling)
        self.assertEqual(rows['Book Assets'], unrelated)
        self.assertNotIn('bcs resource a', rows)
        self.assertEqual(rows['BCS Resource A']['fileId'], 467900)
        self.assertEqual(rows['BCS Resource A']['transaction'], 'mock-transaction')
        self.assertTrue(rows['BCS Resource A']['enabled'])
        self.controller.assert_called_once_with(
            'mod-install', 'in-memory-reviewed-archive.zip', 'BCS Resource A', '--enable', '--replace')
        self.keeps.assert_called_once_with(109254, 'BCS Resource A')
        self.vendor.pick_file.assert_not_called()


if __name__ == '__main__':
    unittest.main()
