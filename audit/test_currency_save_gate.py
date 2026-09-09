import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

import currency_save_gate as gate

CONFIG = {
    'schemaVersion': 2,
    'accounting': {'backendForm': '00000F:Skyrim.esm',
                   'owner': 'EnsrickCurrencyDenominations', 'strictSingleOwner': True},
    'excludePhysicalFormsFromOrdinaryBarter': True,
    'excludePhysicalFormsFromDrop': False,
    'distribution': {'canonicalPercent': 80, 'variantPercent': 20, 'seed': '0x454E535249434B31'},
    'routing': {'precedence': ['questExceptions', 'regionalRoutes', 'septimFallback'],
                'rules': [{'id': 'test-route', 'anyKeywords': ['000900:Test.esp'],
                           'familyIds': ['septim']}]},
    'families': [{
        'id': 'septim', 'displayLabel': 'Septims', 'backendLabel': 'Septim value',
        'salt': '0x53657074696D', 'enabled': True, 'fallback': True, 'perk': None,
        'denominations': [
            {'tier': 'copper', 'value': 1, 'form': '000800:Test.esp'},
            {'tier': 'silver', 'value': 10, 'form': '000801:Test.esp'},
            {'tier': 'gold', 'value': 100, 'form': '000802:Test.esp'}],
        'inputAliases': [{'tier': 'copper', 'form': '000803:Test.esp'}]}]}
FINGERPRINT = gate.ledger_fingerprint(CONFIG)


def record(value=100, backend=100, physical=100, fingerprint=FINGERPRINT, version=2):
    payload = struct.pack('<4sI4Q', b'ECV2', 2, fingerprint, value, backend, physical)
    return struct.pack('<4sII', b'ECMK', version, len(payload)) + payload


def plugin(chunks, identity=b'ECDN'):
    body = b''.join(chunks)
    return struct.pack('<4sII', identity, len(chunks), len(body)) + body


def cosave(*plugins):
    return struct.pack('<4s4I', b'SKSE', 1, 0, 0, len(plugins)) + b''.join(plugins)


class CheckpointTests(unittest.TestCase):
    def test_missing_checkpoint_does_not_diagnose_save_age(self):
        with self.assertRaisesRegex(ValueError, 'failed bridge initialization/serialization') as caught:
            gate.read_checkpoint(cosave(), FINGERPRINT)
        self.assertNotIn('predates', str(caught.exception))

    def test_pending_transactions_remain_valid(self):
        for values in ((105, 100, 105), (0, 0, 100), (0, 100, 0), (0, 0, 0)):
            with self.subTest(values=values):
                actual = gate.read_checkpoint(cosave(plugin([record(*values)])), FINGERPRINT)
                self.assertEqual(values, tuple(actual[k] for k in ('value', 'backend', 'physical')))

    def test_other_plugins_are_bounded_but_not_interpreted(self):
        other = struct.pack('<4sII', b'OTHR', 9, 3) + b'abc'
        self.assertEqual(100, gate.read_checkpoint(cosave(plugin([other], b'ABCD'),
                                                       plugin([record()])), FINGERPRINT)['value'])

    def test_rejects_legacy_future_duplicate_missing_and_changed_config(self):
        candidates = [cosave(), cosave(plugin([])), cosave(plugin([record(version=1)])),
                      cosave(plugin([record(version=3)])), cosave(plugin([record(), record()])),
                      cosave(plugin([record()]), plugin([record()])),
                      cosave(plugin([record(fingerprint=1)])),
                      cosave(plugin([record(value=2**31)]))]
        for raw in candidates:
            with self.subTest(raw=raw.hex()):
                with self.assertRaises(ValueError):
                    gate.read_checkpoint(raw, FINGERPRINT)

    def test_every_truncation_rejected(self):
        raw = cosave(plugin([record()]))
        for length in range(len(raw)):
            with self.subTest(length=length), self.assertRaises(ValueError):
                gate.read_checkpoint(raw[:length], FINGERPRINT)

    def test_tampered_wrapper_rejected(self):
        raw = cosave(plugin([record()]))
        candidates = [raw + b'junk', b'FAIL' + raw[4:], raw[:4] + struct.pack('<I', 2) + raw[8:]]
        for at in (16, 24, 28, 40):
            candidates.append(raw[:at] + struct.pack('<I', 0xFFFFFFFF) + raw[at + 4:])
        for candidate in candidates:
            with self.subTest(raw=candidate.hex()), self.assertRaises(ValueError):
                gate.read_checkpoint(candidate, FINGERPRINT)

    def test_fingerprint_case_fold_and_order(self):
        self.assertEqual(0x0D15619C721A4FAF, FINGERPRINT)
        changed = copy.deepcopy(CONFIG)
        changed['accounting']['backendForm'] = '00000f:SKYRIM.ESM'
        self.assertEqual(FINGERPRINT, gate.ledger_fingerprint(changed))
        changed['families'][0]['denominations'].reverse()
        self.assertNotEqual(FINGERPRINT, gate.ledger_fingerprint(changed))

    def test_fingerprint_binds_tiers_routes_and_source_aliases(self):
        for defect in ('tier', 'keyword', 'alias', 'salt', 'distribution'):
            changed = copy.deepcopy(CONFIG)
            if defect == 'tier':
                changed['families'][0]['denominations'][0]['tier'] = 'gold'
            elif defect == 'keyword':
                changed['routing']['rules'][0]['anyKeywords'][0] = '000901:Test.esp'
            elif defect == 'alias':
                changed['families'][0]['inputAliases'] = []
            elif defect == 'salt':
                changed['families'][0]['salt'] = '0x1'
            else:
                changed['distribution']['seed'] = '0x2'
            with self.subTest(defect=defect):
                self.assertNotEqual(FINGERPRINT, gate.ledger_fingerprint(changed))

    def test_schema1_fingerprint_is_not_an_admission_path(self):
        changed = copy.deepcopy(CONFIG)
        changed['schemaVersion'] = 1
        with self.assertRaisesRegex(ValueError, 'schema 2'):
            gate.ledger_fingerprint(changed)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.instance, self.data = self.root / 'instance', self.root / 'Data'
        self.write(self.instance / 'profiles/Default/modlist.txt', '+Currency\n')
        self.mod = self.instance / 'mods/Currency'
        self.save = self.root / 'Save.ess'
        self.receipt = self.root / 'reviewed-release.json'
        self.write(self.save, b'untouched')

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def adopt(self):
        self.write(self.mod / gate.DLL, b'dll')
        self.write(self.mod / gate.CONFIG, json.dumps(CONFIG))
        self.write(self.mod / gate.PLUGIN, b'esp')
        self.write(self.mod / gate.PURSES, b'purses')
        self.write(self.instance / 'profiles/Default/plugins.txt',
                   '*' + gate.PLUGIN + '\n*' + gate.PURSES + '\n')
        self.write(self.receipt, json.dumps({'schemaVersion': 1, 'version': '0.4.0', 'winningFiles': {
            relative: hashlib.sha256((self.mod / relative).read_bytes()).hexdigest()
            for relative in (gate.DLL, gate.CONFIG, gate.PLUGIN, gate.PURSES)}}))

    def check(self, path='default'):
        return gate.check_save(self.instance, self.data, self.save if path == 'default' else path,
                               receipt_path=self.receipt)

    def test_legacy_profile_unaffected(self):
        self.assertEqual([], self.check())

    def test_missing_cosave_is_blocker_and_no_writes(self):
        self.adopt()
        self.assertTrue(self.check())
        self.assertEqual(b'untouched', self.save.read_bytes())
        self.assertFalse(self.save.with_suffix('.skse').exists())

    def test_exact_save_admitted_then_overwrite_config_mismatch_refused(self):
        self.adopt()
        self.write(self.save.with_suffix('.skse'), cosave(plugin([record()])))
        self.assertEqual([], self.check())
        changed = copy.deepcopy(CONFIG)
        changed['families'][0]['denominations'][0]['value'] = 2
        self.write(self.instance / 'overwrite' / gate.CONFIG, json.dumps(changed))
        self.assertTrue(self.check())

    def test_menu_only_allowed_but_incomplete_pair_refused(self):
        self.adopt()
        self.assertEqual([], self.check(None))
        (self.mod / gate.DLL).unlink()
        self.assertTrue(self.check(None))

    def test_esp_only_malformed_receipt_returns_clean_blocker(self):
        self.adopt()
        (self.mod / gate.DLL).unlink()
        (self.mod / gate.CONFIG).unlink()
        (self.mod / gate.PURSES).unlink()
        self.write(self.receipt, json.dumps({'winningFiles': {gate.PLUGIN: 123}}))
        failures = self.check(None)
        self.assertTrue(failures)
        self.assertIn('invalid reviewed currency companion hash', failures[0])

    def test_missing_disabled_or_tampered_companion_refused(self):
        for defect in ('missing', 'disabled', 'overridden', 'stale'):
            with self.subTest(defect=defect):
                self.adopt()
                override = self.instance / 'overwrite' / gate.PLUGIN
                if override.exists():
                    override.unlink()
                if defect == 'missing':
                    (self.mod / gate.PLUGIN).unlink()
                elif defect == 'disabled':
                    self.write(self.instance / 'profiles/Default/plugins.txt', gate.PLUGIN + '\n')
                elif defect == 'overridden':
                    self.write(override, b'other esp')
                else:
                    self.write(self.mod / gate.PLUGIN, b'old esp')
                self.assertTrue(self.check(None))

    def test_replaced_dll_and_missing_or_malformed_receipt_refused(self):
        for defect in ('dll', 'missing receipt', 'invalid hash', 'version', 'mod receipt'):
            with self.subTest(defect=defect):
                self.adopt()
                if defect == 'dll':
                    self.write(self.mod / gate.DLL, b'other dll')
                elif defect in ('missing receipt', 'mod receipt'):
                    if defect == 'mod receipt':
                        self.write(self.mod / self.receipt.name, self.receipt.read_bytes())
                    self.receipt.unlink()
                else:
                    receipt = json.loads(self.receipt.read_text())
                    if defect == 'invalid hash':
                        receipt['winningFiles'][gate.DLL] = 'x' * 64
                    else:
                        receipt['version'] = '0.2.6'
                    self.write(self.receipt, json.dumps(receipt))
                self.assertTrue(self.check(None))

    def test_reviewed_esp_without_both_native_files_refused(self):
        self.adopt()
        (self.mod / gate.DLL).unlink()
        (self.mod / gate.CONFIG).unlink()
        self.assertTrue(self.check(None))

    def test_regional_purse_plugin_missing_inactive_stale_or_early_is_blocked(self):
        for defect in ('missing', 'inactive', 'stale', 'early'):
            with self.subTest(defect=defect):
                self.adopt()
                if defect == 'missing':
                    (self.mod / gate.PURSES).unlink()
                elif defect == 'stale':
                    self.write(self.mod / gate.PURSES, b'wrong purse generation')
                elif defect == 'early':
                    self.write(self.instance / 'profiles/Default/plugins.txt',
                               '*' + gate.PURSES + '\n*' + gate.PLUGIN + '\n')
                else:
                    self.write(self.instance / 'profiles/Default/plugins.txt',
                               '*' + gate.PLUGIN + '\n' + gate.PURSES + '\n')
                self.assertTrue(self.check(None))

    def test_orphan_purse_esp_cannot_be_mistaken_for_legacy_profile(self):
        self.write(self.mod / gate.PURSES, b'purses')
        self.write(self.mod / gate.PLUGIN, b'old ESP unrelated to new receipt')
        self.assertTrue(self.check(None))

    def test_purse_winner_override_and_malformed_purse_hash_are_blocked(self):
        self.adopt()
        self.write(self.instance / 'overwrite' / gate.PURSES, b'wrong override')
        self.assertTrue(self.check(None))
        (self.instance / 'overwrite' / gate.PURSES).unlink()
        receipt = json.loads(self.receipt.read_text())
        receipt['winningFiles'][gate.PURSES] = None
        self.write(self.receipt, json.dumps(receipt))
        self.assertTrue(self.check(None))


if __name__ == '__main__':
    unittest.main()
