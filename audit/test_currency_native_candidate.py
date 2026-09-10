"""Candidate admission cannot replace the release contract or use player saves."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import currency_save_gate as gate


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'mods/currency-integration/native'
        self.build = self.root / 'build'
        self.instance = self.root / 'instance'
        self.profile = 'Astra Load262 fixture'
        self.settings = self.instance / 'profiles' / self.profile / 'settings.ini'
        self.write(self.settings, b'[General]\nLocalSaves=true\n')
        self.dll = self.build / 'build/Release/EnsrickCurrencyDenominations.dll'
        self.write(self.dll, b'fixture, never executed')
        self.release = {'winningFiles': {gate.CONFIG: 'A' * 64}}
        inputs = []
        for name in ('src/Plugin.cpp', 'src/AdmissionIdentity.h', 'CMakeLists.txt', 'build-native.ps1'):
            self.write(self.source / name, b'fixture source')
            inputs.append(dict(relativePath=name, bytes=14, sha256=self.sha(b'fixture source')))
        self.receipt = dict(schemaVersion=1, sourceRoot=str(self.source), runtime='1.7.104.0', skse='2.3.1',
            commonLibCommit='90a64a4d65ce659a139137c968f42151bb6ecec9', commonLibTrackedStatus='clean',
            runtimeConfig={'sha256': 'A' * 64}, sourceInputs=inputs,
            dll=dict(relativePath=gate.DLL, bytes=self.dll.stat().st_size, sha256=self.sha(self.dll.read_bytes())))
        self.fake_module = self.root / 'audit/currency_save_gate.py'

    @staticmethod
    def sha(raw):
        return hashlib.sha256(raw).hexdigest().upper()

    @staticmethod
    def write(path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def check(self, profile=None):
        self.write(self.build / 'native-build-receipt.json', json.dumps(self.receipt).encode())
        with patch.object(gate, '__file__', str(self.fake_module)):
            return gate.reviewed_test_dll(self.build, self.instance, profile or self.profile, self.release)

    def test_matching_candidate_returns_only_dll_hash(self):
        before = dict(self.release['winningFiles'])
        self.assertEqual(self.receipt['dll']['sha256'], self.check())
        self.assertEqual(before, self.release['winningFiles'])

    def test_default_and_arbitrary_profiles_refused(self):
        for profile in ('Default', 'Other', 'Astra Unbound263 Source'):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.check(profile)

    def test_global_saves_or_duplicate_setting_refused(self):
        for raw in (b'LocalSaves=false', b'', b'LocalSaves=true\nLocalSaves=false', b'LocalSaves=true\nLocalSaves=true'):
            self.settings.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.check()

    def test_changed_source_refused(self):
        (self.source / 'src/Plugin.cpp').write_bytes(b'changed')
        with self.assertRaises(ValueError): self.check()

    def test_changed_binary_refused(self):
        self.dll.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.check()

    def test_config_runtime_dependency_mismatch_refused(self):
        for field in ('runtime', 'skse', 'commonLibCommit', 'commonLibTrackedStatus', 'sourceRoot'):
            old = self.receipt[field]
            self.receipt[field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
            self.receipt[field] = old
        self.receipt['runtimeConfig']['sha256'] = 'B' * 64
        with self.assertRaises(ValueError): self.check()

    def test_missing_critical_input_refused(self):
        self.receipt['sourceInputs'].pop()
        with self.assertRaises(ValueError): self.check()

    def test_duplicate_input_refused(self):
        self.receipt['sourceInputs'].append(self.receipt['sourceInputs'][0])
        with self.assertRaises(ValueError): self.check()

    def test_parent_traversal_refused(self):
        self.receipt['sourceInputs'][0]['relativePath'] = '../outside'
        self.write(self.source.parent / 'outside', b'fixture source')
        with self.assertRaises(ValueError): self.check()

    def test_non_dll_payload_refused(self):
        self.receipt['dll']['relativePath'] = gate.CONFIG
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main()
