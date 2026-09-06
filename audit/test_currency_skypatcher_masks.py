"""Regression checks for order-independent legacy currency configuration masks."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'mods/currency-integration/validate.py'
SPEC=importlib.util.spec_from_file_location('currency_release_validate_masks',SOURCE)
VALIDATE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)


class CurrencySkyPatcherMasks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sky=Path(self.temp.name)/'misc'
        shutil.copytree(VALIDATE.PACKAGE/'SKSE/Plugins/SkyPatcher/misc',self.sky)

    def check(self):
        VALIDATE.validate_skypatcher_legacy_masks(self.sky)

    def test_exact_reviewed_files_pass(self):
        self.check()

    def test_missing_regional_mask_rejected(self):
        (self.sky/'ECE_regionalCurrencies.ini').unlink()
        with self.assertRaises(AssertionError): self.check()

    def test_restored_silver_25_rejected(self):
        path=self.sky/'ECE_septims_100.ini'
        path.write_bytes(path.read_bytes()+b'filterByMiscs=exchangeCurrency_enhanced.esp|0x823:value=25\n')
        with self.assertRaises(AssertionError): self.check()

    def test_lost_backend_row_rejected(self):
        path=self.sky/'ECE_septims_100.ini'
        path.write_bytes(path.read_bytes().replace(b'filterByMiscs= skyrim.esm|0xf:value=1:weight=0:fullName=~Septim~\n',b''))
        with self.assertRaises(AssertionError): self.check()

    def test_changed_plural_name_rejected(self):
        path=self.sky/'ECE_septims_100.ini'
        path.write_bytes(path.read_bytes().replace(b'~Silver Septims~',b'~Silvers~'))
        with self.assertRaises(AssertionError): self.check()

    def test_extra_writer_rejected(self):
        (self.sky/'zzz_bad.ini').write_bytes(b'filterByMiscs=update.esm|0xde5021:value=0\n')
        with self.assertRaises(AssertionError): self.check()

    def test_reactivated_ancient_writer_rejected(self):
        (self.sky/'zz_Ensrick_Currency_AncientWeights.ini').write_bytes(b'filterByMiscs=update.esm|0xde5015:weight=0.01\n')
        with self.assertRaises(AssertionError): self.check()

    def test_exact_bytes_reject_line_ending_mutation(self):
        path=self.sky/'ECE_regionalCurrencies.ini'
        path.write_bytes(path.read_bytes().replace(b'\n',b'\r\n'))
        with self.assertRaises(AssertionError): self.check()


if __name__=='__main__': unittest.main()
