"""Native package names and notices follow receipt-bound source, not old labels."""
import importlib.util
from pathlib import Path
import unittest
import package_currency_native_hotfix as hotfix

spec = importlib.util.spec_from_file_location('currency_test_overlay', Path(__file__).resolve().parents[1] / 'mods/currency-integration/native/package-test-overlay.py')
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class Versions(unittest.TestCase):
    def test_current_and_prior(self):
        for version in ('0.2.2', '0.2.3'):
            source = f'project(\n EnsrickCurrencyDenominations\n VERSION {version}\n LANGUAGES CXX\n)'
            payload = {'Source/EnsrickCurrencyDenominations/CMakeLists.txt': source.encode()}
            self.assertEqual(overlay.native_version(source), version)
            self.assertEqual(hotfix.native_version(payload, {}), version)
            self.assertEqual(hotfix.native_version(payload, {'nativeVersion': version}), version)
            with self.assertRaises(ValueError):
                hotfix.native_version(payload, {'nativeVersion': 'wrong'})

    def test_ambiguous_missing_or_unsafe(self):
        good = 'project(EnsrickCurrencyDenominations VERSION 0.2.3 LANGUAGES CXX)'
        for source in ('', good + '\n' + good, good.replace('0.2.3', '../../payload'), good.replace('EnsrickCurrencyDenominations', 'Other')):
            payload = {'Source/EnsrickCurrencyDenominations/CMakeLists.txt': source.encode()}
            with self.assertRaises(ValueError):
                overlay.native_version(source)
            with self.assertRaises(ValueError):
                hotfix.native_version(payload, {})


if __name__ == '__main__':
    unittest.main()
