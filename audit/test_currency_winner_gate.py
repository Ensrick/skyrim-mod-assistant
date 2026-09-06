from dataclasses import replace
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import currency_winner_gate as gate
from currency_purse_gate import Plugin,Record


class WinnerTests(unittest.TestCase):
    def fixture(self):
        key='000800:coin.esp'
        plugin=Plugin('winner.esp',['Skyrim.esm'],0x200,{},0,0,0,'HASH')
        record=Record(key,'MISC',0,((b'FULL',b'Copper Coin\0'),(b'MODL',b'Meshes\\Coin.nif\0'),
            (b'DATA',struct.pack('<If',1,0.1)),(b'KSIZ',struct.pack('<I',1)),
            (b'KWDA',struct.pack('<I',0xFF9FB))))
        expected={key:dict(name='Copper Coin',model='Meshes\\Coin.nif',value=1)}
        return key,plugin,record,expected

    def test_correct_winner_and_windows_path_case(self):
        key,plugin,record,expected=self.fixture()
        expected[key]['model']='meshes/coin.NIF'
        rows,blockers=gate.check_winners(expected,{key:(plugin,record)})
        self.assertEqual([],blockers)
        self.assertEqual('winner.esp',rows[0]['winningPlugin'])
        self.assertEqual(gate.model_path('Clutter\\Coin01.nif'),gate.model_path('Meshes/Clutter/Coin01.nif'))

    def test_invalid_model_paths_are_not_normalized_away(self):
        for path in ('C:Coin.nif','\\Meshes\\Coin.nif','Meshes\\..\\Coin.nif','Meshes\\Meshes\\Coin.nif'):
            with self.assertRaises(ValueError): gate.model_path(path)

    def test_late_deleted_winner_does_not_resurrect_earlier_coin(self):
        key,plugin,record,expected=self.fixture()
        _,blockers=gate.check_winners(expected,{key:(plugin,replace(record,flags=0x20))})
        self.assertIn('deleted',blockers[0]['errors'][0])

    def test_actual_overlay_last_declaration_wins_and_retains_deletions(self):
        key,plugin,record,expected=self.fixture()
        first=replace(plugin,name='first.esp',records={key:record})
        last=replace(plugin,name='last.esp',records={key:replace(record,flags=0x20)})
        with patch.object(gate,'read_plugin',side_effect=[first,last]):
            result=gate.scan([Path('first.esp'),Path('last.esp')],expected)
        self.assertEqual('last.esp',result['forms'][0]['winningPlugin'])
        self.assertIn('deleted',result['blockers'][0]['errors'][0])

    def test_name_value_model_and_keyword_drift_rejected(self):
        for tag,value,error in ((b'FULL',b'Coin\0','name'),(b'DATA',struct.pack('<If',10,0.1),'value'),
                                (b'MODL',b'Wrong.nif\0','model'),(b'KWDA',struct.pack('<I',0x123),'VendorItemNoSale')):
            key,plugin,record,expected=self.fixture()
            record=replace(record,subs=tuple((t,value if t==tag else v) for t,v in record.subs))
            _,blockers=gate.check_winners(expected,{key:(plugin,record)})
            self.assertIn(error,' '.join(blockers[0]['errors']))

    def test_missing_form_and_malformed_keyword_counter_rejected(self):
        key,plugin,record,expected=self.fixture()
        self.assertTrue(gate.check_winners(expected,{})[1])
        record=replace(record,subs=tuple((t,bytes(4) if t==b'KSIZ' else v) for t,v in record.subs))
        self.assertIn('counter',gate.check_winners(expected,{key:(plugin,record)})[1][0]['errors'][0])

    def test_unresolved_localized_name_fails_closed(self):
        key,plugin,record,expected=self.fixture()
        plugin.flags |= 0x80
        self.assertIn('localized',gate.check_winners(expected,{key:(plugin,record)})[1][0]['errors'][0])

    def test_candidate_inserts_only_after_active_main_and_deduplicates_helper(self):
        paths=[Path('Skyrim.esm'),Path(gate.HELPER),Path(gate.MAIN),Path('later.esp')]
        main=Path('candidate')/gate.MAIN
        helper=Path('candidate')/gate.HELPER
        self.assertEqual([paths[0],main,helper,paths[-1]],gate.candidate_order(paths,main,helper))
        self.assertEqual(paths,gate.candidate_order(paths))

    def test_candidate_cannot_implicitly_enable_absent_main_or_misname(self):
        with self.assertRaisesRegex(ValueError,'already-active'):
            gate.candidate_order([Path('Skyrim.esm')],Path(gate.MAIN))
        with self.assertRaisesRegex(ValueError,'filename'):
            gate.candidate_order([Path(gate.MAIN)],Path('wrong.esp'))
        with self.assertRaisesRegex(ValueError,'paired'):
            gate.candidate_order([Path(gate.MAIN)],None,Path(gate.HELPER))


if __name__=='__main__':
    unittest.main()
