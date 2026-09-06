import copy
import importlib.util
from pathlib import Path
import unittest

import currency_bos_gate as gate
import currency_tier_contract as tiers
from test_currency_tier_contract import complete_fixture

script = Path(__file__).resolve().parents[1] / 'mods/currency-integration/generate_bos.py'
spec = importlib.util.spec_from_file_location('generate_bos', script)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class BosTests(unittest.TestCase):
    def setUp(self):
        _, self.config = complete_fixture()
        self.config['routing'] = {
            'precedence': ['questExceptions', 'regionalRoutes', 'septimFallback'],
            'rules': [{'id': identity, 'anyKeywords': keywords, 'familyIds': families}
                      for identity, keywords, families in copy.deepcopy(tiers.ROUTES)]}
        self.roots = {identity: [] for identity, _, _ in tiers.ROUTES}
        self.outputs = generator.build(self.config, self.roots)

    def test_all_design_metal_intervals_and_physical_value_conservation(self):
        self.assertEqual(24, len(self.outputs))
        gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_copper_to_gold_drop_exploit_rejected(self):
        name = 'zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini'
        self.outputs[name] = self.outputs[name].replace(
            '0x000B6D~exchangeCurrency_enhanced.esp|0x000B6D~exchangeCurrency_enhanced.esp|scale(1)',
            '0x000B6D~exchangeCurrency_enhanced.esp|0x000824~exchangeCurrency_enhanced.esp|NONE')
        with self.assertRaisesRegex(ValueError, 'changes value'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_missing_face_threshold_or_wrong_region_rejected(self):
        name = 'zz_Ensrick_Currency_90_nordic-ruin_SWAP.ini'
        lines = self.outputs[name].splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith('0x00000F'))
        lines.pop(index + 1)
        self.outputs[name] = '\n'.join(lines)
        with self.assertRaises(ValueError):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_wrong_probability_is_rejected(self):
        name = 'zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini'
        self.outputs[name] = self.outputs[name].replace('chanceS(25)', 'chanceS(30)')
        with self.assertRaisesRegex(ValueError, 'probability'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_invalid_identity_swap_is_rejected(self):
        name = 'zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini'
        self.outputs[name] = self.outputs[name].replace('scale(1)', 'NONE')
        with self.assertRaisesRegex(ValueError, 'identity swaps'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_wrong_purse_size_is_rejected(self):
        name = 'zz_Ensrick_Currency_86_mede-region_SWAP.ini'
        self.outputs[name] = self.outputs[name].replace(
            '0x000800~Ensrick Currency Regional Purses.esp',
            '0x000802~Ensrick Currency Regional Purses.esp')
        with self.assertRaisesRegex(ValueError, 'purse size'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_unreviewed_legacy_mask_rules_are_rejected(self):
        self.outputs['C.O.I.N_SWAP.ini'] = '[Forms|LocSetNordicRuin]\n0xF~Skyrim.esm|0xDE5012~Update.esm|NONE|chanceS(100)\n'
        with self.assertRaisesRegex(ValueError, 'unreviewed active'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_missing_legacy_mask_is_rejected(self):
        del self.outputs['C.O.I.N_SWAP.ini']
        with self.assertRaisesRegex(ValueError, 'eight legacy masks'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)

    def test_ancestor_location_scope_is_bound(self):
        self.roots['dwemer-ruin'] = ['018EE8:Skyrim.esm']
        self.outputs = generator.build(self.config, self.roots)
        gate.check(self.config, self.outputs, self.roots, generator.PURSES)
        self.roots['dwemer-ruin'] = []
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            gate.check(self.config, self.outputs, self.roots, generator.PURSES)


if __name__ == '__main__':
    unittest.main()
