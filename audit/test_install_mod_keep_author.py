"""Offline Keep metadata/queue regressions; never import the credential reader."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

import install_mod


class KeepAuthorTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(mock.patch.dict(os.environ, {'TEMP': self.temp}))
        self.pending = Path(self.temp) / 'nlc-relay' / 'decisions-pending.json'
        self.secret = 'SYNTHETIC-KEY-MUST-NOT-BE-LOGGED'
        self.metadata = {
            'mod_id': 109254, 'uploaded_by': 'CurrentUploader',
            'author': 'Original artist and collaborators',
            'uploaded_users_profile_url': 'https://www.nexusmods.com/users/12345',
            'description': self.secret, 'apikey': self.secret,
        }
        self.vendor = types.SimpleNamespace(v1=mock.Mock(return_value=self.metadata))
        self.stack.enter_context(mock.patch.dict(sys.modules, {'modasset': self.vendor}))
        self.stdout = self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stderr = self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))

    def write(self, batch):
        self.pending.parent.mkdir(exist_ok=True)
        self.pending.write_text(json.dumps(batch), encoding='utf-8')

    def read(self):
        return json.loads(self.pending.read_text(encoding='utf-8'))

    def assert_no_secret(self):
        self.assertNotIn(self.secret, self.stdout.getvalue() + self.stderr.getvalue())
        if self.pending.exists():
            self.assertNotIn(self.secret, self.pending.read_text(encoding='utf-8'))

    def test_public_uploader_identity_is_queued_without_api_response(self):
        install_mod.queue_keep(109254, 'Book Covers Resource')
        self.vendor.v1.assert_called_once_with('/mods/109254.json')
        entry, = self.read()
        self.assertEqual(entry['status'], 'keep')
        self.assertEqual(entry['mod']['author'], 'CurrentUploader')
        self.assertEqual(entry['mod']['authorUserId'], '12345')
        self.assertEqual(entry['mod']['authorProfileUrl'],
                         'https://www.nexusmods.com/users/12345')
        self.assertEqual(entry['mod']['game'], 'skyrimspecialedition')
        self.assertEqual(entry['mod']['modId'], '109254')
        self.assertIn('queuedAt', entry)
        self.assert_no_secret()

    def test_profile_url_is_canonicalized_without_query_or_fragment(self):
        self.metadata['uploaded_users_profile_url'] += '?token=' + self.secret + '#private'
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.read()[0]['mod']['authorProfileUrl'],
                         'https://www.nexusmods.com/users/12345')
        self.assert_no_secret()

    def test_unrelated_pending_decisions_and_same_id_other_game_survive(self):
        original = [
            {'status': 'skip', 'mod': {'game': 'skyrim', 'modId': '109254',
                                     'title': 'Oldrim choice'}, 'note': 'Owner choice'},
            {'status': 'unreviewed', 'mod': {'game': 'skyrimspecialedition',
                                           'modId': '901'}, 'queuedAt': 'original'},
        ]
        self.write(original)
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.read()[:2], original)
        self.assertEqual(len(self.read()), 3)

    def test_existing_keep_is_enriched_not_duplicated_or_reset(self):
        original = {'status': 'keep', 'queuedAt': 'original', 'note': 'Preserve',
                    'mod': {'game': 'skyrimspecialedition', 'modId': 109254,
                            'title': 'Existing title', 'custom': 'Retain'}}
        self.write([original])
        install_mod.queue_keep(109254, 'New folder name')
        install_mod.queue_keep(109254, 'New folder name')
        entry, = self.read()
        expected = copy.deepcopy(original)
        expected['mod'].update(author='CurrentUploader', authorUserId='12345',
                               authorProfileUrl='https://www.nexusmods.com/users/12345')
        self.assertEqual(entry, expected)

    def test_pending_skip_is_not_silently_overridden(self):
        self.write([{'status': 'skip', 'mod': {
            'game': 'skyrimspecialedition', 'modId': '109254'}}])
        original = self.pending.read_bytes()
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.pending.read_bytes(), original)
        self.vendor.v1.assert_not_called()
        self.assertIn('KEEP QUEUE FAILED', self.stdout.getvalue())

    def test_api_failure_preserves_queue_and_redacts_exception_text(self):
        self.write([{'status': 'keep', 'mod': {
            'game': 'skyrimspecialedition', 'modId': '901'}}])
        original = self.pending.read_bytes()
        self.vendor.v1.side_effect = RuntimeError('apikey=' + self.secret)
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.pending.read_bytes(), original)
        self.assertIn('KEEP QUEUE FAILED for 109254: RuntimeError', self.stdout.getvalue())
        self.assert_no_secret()

    def test_missing_identity_does_not_claim_an_attributed_keep(self):
        self.vendor.v1.return_value = {'mod_id': 109254, 'name': 'Books'}
        install_mod.queue_keep(109254, 'Books')
        self.assertFalse(self.pending.exists())
        self.assertIn('KEEP QUEUE FAILED', self.stdout.getvalue())

    def test_batch_is_reread_after_metadata_lookup(self):
        earlier = {'status': 'keep', 'mod': {'game': 'skyrimspecialedition', 'modId': '901'}}
        later = {'status': 'skip', 'mod': {'game': 'skyrimspecialedition', 'modId': '1772'}}
        self.write([earlier])

        def lookup(_path):
            self.write([earlier, later])
            return self.metadata

        self.vendor.v1.side_effect = lookup
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.read()[:2], [earlier, later])
        self.assertEqual(len(self.read()), 3)

    def test_new_owner_decision_during_api_lookup_is_preserved(self):
        conflict = [{'status': 'skip', 'mod': {
            'game': 'skyrimspecialedition', 'modId': '109254'}}]

        def lookup(_path):
            self.write(conflict)
            return self.metadata

        self.vendor.v1.side_effect = lookup
        install_mod.queue_keep(109254, 'Books')
        self.assertEqual(self.read(), conflict)
        self.assertIn('KEEP QUEUE FAILED', self.stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
