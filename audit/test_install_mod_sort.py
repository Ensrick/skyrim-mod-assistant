import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import install_mod as subject


def state(*rows):
    return {'plugins': [
        {'name': name, 'enabled': enabled}
        for name, enabled in rows
    ]}


class PluginMembershipTests(unittest.TestCase):
    def test_identity_is_case_insensitive(self):
        before, duplicates = subject._plugin_snapshot(state(('Patch.ESP', True)))
        after, _ = subject._plugin_snapshot(state(('patch.esp', True)))

        self.assertEqual([], duplicates)
        self.assertEqual([], subject._membership_delta(before, after)['lost'])
        self.assertEqual([], subject._membership_delta(before, after)['unexpectedlyEnabled'])
        self.assertEqual(
            [{'before': 'Patch.ESP', 'after': 'patch.esp'}],
            subject._membership_delta(before, after)['caseChanges'])

    def test_duplicate_case_variants_are_rejected(self):
        _, duplicates = subject._plugin_snapshot(
            state(('Patch.esp', True), ('PATCH.ESP', True)))
        self.assertEqual([('Patch.esp', 'PATCH.ESP')], duplicates)

    def test_ledger_verification_is_case_insensitive(self):
        ledger = {'mods': [{
            'modName': 'Fixture',
            'plugins': ['Patch.ESP'],
            'enabled': True,
        }]}
        with mock.patch.object(subject, 'load', return_value=ledger), \
                mock.patch.object(subject, 'mo2', return_value={
                    'discoveredCount': 1,
                    'plugins': [{'name': 'patch.esp', 'enabled': True}],
                }), \
                mock.patch.object(subject.profile_reconcile, 'reconcile',
                                  return_value={
                                      'counts': {'errors': 0},
                                      'reconciled': True,
                                  }), \
                mock.patch.object(subject.profile_reconcile, 'render',
                                  return_value='fixture reconciled'):
            self.assertEqual(0, subject.verify())


class SortOrderTests(unittest.TestCase):
    def run_sort(self, before, after):
        with tempfile.TemporaryDirectory() as run_directory:
            process = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({
                    'runDirectory': run_directory,
                    'controllerStateDelta': {
                        'activeBefore': 1,
                        'activeAfter': 1,
                        'newlyActive': [],
                        'missing': [],
                    },
                }) + '\n',
                stderr='',
            )
            with mock.patch.object(subject, 'mo2', side_effect=[before, after]) as mo2, \
                    mock.patch.object(subject.subprocess, 'run', return_value=process), \
                    mock.patch.object(subject, 'verify', return_value=0):
                result = subject._sort_order()
            with open(os.path.join(run_directory, 'plugin-state-delta.json'),
                      encoding='utf-8') as report_file:
                report = json.load(report_file)
            return result, report, mo2

    def test_sort_preserves_exact_membership_without_enable_calls(self):
        result, report, mo2 = self.run_sort(
            state(('Keep.esp', True), ('StayOff.esp', False)),
            state(('keep.ESP', True), ('StayOff.esp', False)))

        self.assertEqual(0, result)
        self.assertTrue(report['activeSetPreserved'])
        self.assertEqual([], report['lost'])
        self.assertEqual([], report['unexpectedlyEnabled'])
        self.assertEqual([mock.call('plugin-list'), mock.call('plugin-list')],
                         mo2.call_args_list)

    def test_new_activation_fails_closed(self):
        result, report, _ = self.run_sort(
            state(('Keep.esp', True), ('StayOff.esp', False)),
            state(('Keep.esp', True), ('StayOff.esp', True)))

        self.assertEqual(1, result)
        self.assertFalse(report['activeSetPreserved'])
        self.assertEqual(['StayOff.esp'], report['unexpectedlyEnabled'])

    def test_lost_activation_fails_closed(self):
        result, report, _ = self.run_sort(
            state(('Keep.esp', True), ('StayOff.esp', False)),
            state(('Keep.esp', False), ('StayOff.esp', False)))

        self.assertEqual(1, result)
        self.assertFalse(report['activeSetPreserved'])
        self.assertEqual(['Keep.esp'], report['lost'])


if __name__ == '__main__':
    unittest.main()
