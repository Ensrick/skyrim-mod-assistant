from fractions import Fraction
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import currency_purse_gate as gate


def sub(tag,value):
    return tag+struct.pack('<H',len(value))+value


def major(tag,identity,body,flags=0):
    return struct.pack('<4sIIIIHH',tag,len(body),flags,identity,0,44,0)+body


def binary(*records):
    header = sub(b'HEDR',struct.pack('<fII',1.7,len(records)+1,0x900))
    group = struct.pack('<4sI4sI8s',b'GRUP',24+sum(map(len,records)),b'LVLI',0,bytes(8))
    return major(b'TES4',0,header,0x200)+group+b''.join(records)


def record(identity,entries,flags=0):
    body = [(b'EDID',f'Test{identity:X}'.encode()+b'\0'),(b'OBND',bytes(12)),
            (b'LVLD',b'\0'),(b'LVLF',bytes([flags])),(b'LLCT',bytes([len(entries)]))]
    body.extend((b'LVLO',struct.pack('<hhIhh',1,0,target,count,0)) for target,count in entries)
    key = gate.normalized(f'{identity:06X}:test.esp')
    return gate.Record(key,'LVLI',0,tuple(body))


def graph():
    records = [record(0x800,[(0x100,4),(0x101,2)],4),
               record(0x801,[(0x100,14),(0x101,1)],4),
               record(0x802,[(0x800,1)]*4+[(0x801,1)])]
    plugin = gate.Plugin('test.esp',[],0x200,{r.key:r for r in records},4,3,1,'TEST')
    coins = {gate.normalized(f'{identity:06X}:test.esp'):index for index,identity in enumerate((0x100,0x101,0x102))}
    return plugin,coins


class PurseTests(unittest.TestCase):
    def test_pinned_python_source_only_permits_crlf_checkout_conversion(self):
        source=b'def example():\n    return 1\n'
        expected=hashlib.sha256(source).hexdigest().upper()
        self.assertEqual((expected,expected),gate.pinned_python_source(source,expected))
        raw,canonical=gate.pinned_python_source(source.replace(b'\n',b'\r\n'),expected)
        self.assertNotEqual(raw,canonical)
        self.assertEqual(expected,canonical)
        for bad in (source.rstrip(),source.replace(b'1',b'2'),source.replace(b'    ',b'\t')):
            with self.assertRaisesRegex(ValueError,'hash drift'):
                gate.pinned_python_source(bad,expected)

    def test_whole_purse_exact_80_20(self):
        plugin,coins = graph()
        result = gate.Evaluator(plugin,coins).evaluate('000802:test.esp')
        self.assertEqual({(4,2,0):Fraction(4,5),(14,1,0):Fraction(1,5)},result)
        self.assertEqual(result,gate.expected_distribution([24]))

    def test_one_gold_break_does_not_break_resulting_silvers(self):
        self.assertEqual(((4,2,1),(4,12,0)),gate.vectors(124))
        self.assertEqual(((0,0,1),(0,10,0)),gate.vectors(100))
        self.assertEqual(((4,0,0),(4,0,0)),gate.vectors(4))

    def test_expected_uniform_budget_and_value_conservation(self):
        for amounts in gate.PINNED_AMOUNTS:
            result=gate.expected_distribution(amounts)
            totals={}
            for vector,probability in result.items():
                total=sum(a*b for a,b in zip(vector,(1,10,100)))
                totals[total]=totals.get(total,0)+probability
            self.assertEqual({amount:Fraction(1,16) for amount in amounts},totals)

    def test_incorrect_selector_weight_changes_distribution(self):
        plugin,coins=graph()
        wrong=record(0x802,[(0x800,1)]*3+[(0x801,1)]*2)
        plugin.records[wrong.key]=wrong
        self.assertNotEqual(gate.expected_distribution([24]),
                            gate.Evaluator(plugin,coins).evaluate(wrong.key))

    def test_per_coin_variation_is_not_whole_purse_variation(self):
        leaf={(0,1,0):Fraction(4,5),(10,0,0):Fraction(1,5)}
        wrong=gate.convolve(gate.convolve(leaf,leaf),{(4,0,0):Fraction(1)})
        self.assertEqual(Fraction(1,25),wrong[(24,0,0)])
        self.assertNotEqual(gate.expected_distribution([24]),wrong)

    def test_each_item_count_flag_is_rejected(self):
        plugin,coins=graph()
        wrong=record(0x802,[(0x800,1)]*4+[(0x801,1)],2)
        plugin.records[wrong.key]=wrong
        with self.assertRaisesRegex(ValueError,'per-item rerolls'):
            gate.Evaluator(plugin,coins).evaluate(wrong.key)

    def test_cycle_and_unresolved_targets_are_rejected(self):
        for target,message in ((0x802,'cyclic'),(0xFFF,'unresolved')):
            plugin,coins=graph()
            wrong=record(0x802,[(target,1)])
            plugin.records[wrong.key]=wrong
            with self.assertRaisesRegex(ValueError,message):
                gate.Evaluator(plugin,coins).evaluate(wrong.key)

    def test_foreign_family_coin_and_non_list_links_are_rejected(self):
        plugin,coins=graph()
        with self.assertRaisesRegex(ValueError,'foreign-family'):
            gate.Evaluator(plugin,coins).evaluate('000199:test.esp')
        wrong=gate.Record('000900:test.esp','MISC',0,())
        plugin.records[wrong.key]=wrong
        with self.assertRaisesRegex(ValueError,'non-LVLI'):
            gate.Evaluator(plugin,coins).evaluate(wrong.key)

    def test_chance_none_counter_unknown_subrecord_and_level_rejected(self):
        for tag,value,message in ((b'LVLD',b'\1','chance-none'),(b'LLCT',b'\1','counter'),
                                  (b'LVLG',bytes(4),'unreviewed')):
            plugin,coins=graph()
            original=plugin.records['000802:test.esp']
            subs=tuple((t,value if t==tag else v) for t,v in original.subs)
            if tag==b'LVLG': subs += ((tag,value),)
            plugin.records[original.key]=gate.Record(original.key,'LVLI',0,subs)
            with self.assertRaisesRegex(ValueError,message):
                gate.Evaluator(plugin,coins).evaluate(original.key)
        plugin,coins=graph()
        original=record(0x900,[(0x100,1)])
        subs=tuple((tag,b'\2\0'+value[2:] if tag==b'LVLO' else value) for tag,value in original.subs)
        with self.assertRaisesRegex(ValueError,'level'):
            gate.list_entries(plugin,gate.Record(original.key,'LVLI',0,subs))

    def test_localized_flora_strings_compare_semantically(self):
        source=gate.Plugin('Skyrim.esm',[],0x81,{},0,0,0,'')
        target=gate.Plugin('target.esp',['Skyrim.esm'],0x200,{},0,0,0,'')
        original=gate.Record('000100:skyrim.esm','FLOR',0,
            ((b'FULL',struct.pack('<I',17)),(b'RNAM',struct.pack('<I',18)),
             (b'SNAM',struct.pack('<I',0x899AD)),(b'PFPC',bytes([100]*4))))
        copied=gate.Record('000800:target.esp','FLOR',0,
            ((b'FULL',b'Coin Purse\0'),(b'RNAM',b'Take\0'),
             (b'SNAM',struct.pack('<I',0x899AD)),(b'PFPC',bytes([100]*4))))
        strings={17:b'Coin Purse',18:b'Take'}
        self.assertEqual(gate.flora_content(source,original,strings),
                         gate.flora_content(target,copied,strings))
        with self.assertRaisesRegex(ValueError,'unresolved FLOR text'):
            gate.flora_content(source,original,{})

    def test_strings_directory_bounds_and_duplicate_ids(self):
        raw=struct.pack('<IIII',1,5,42,0)+b'Test\0'
        self.assertEqual({42:b'Test'},gate.read_strings(raw))
        for bad in (raw[:-1],raw+b'\0',struct.pack('<IIIIII',2,5,42,0,42,0)+b'Test\0'):
            with self.assertRaises(ValueError): gate.read_strings(bad)

    def test_strict_binary_accepts_valid_and_compressed_record(self):
        body=sub(b'EDID',b'Test\0')
        compressed=struct.pack('<I',len(body))+zlib.compress(body)
        for payload,flags in ((body,0),(compressed,0x40000)):
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'test.esp'
                path.write_bytes(binary(major(b'LVLI',0x800,payload,flags)))
                plugin=gate.read_plugin(path)
                self.assertEqual(1,plugin.actual_count)
                self.assertEqual('Test',plugin.records['000800:test.esp'].editor_id)

    def test_strict_binary_rejects_boundaries_duplicates_and_invalid_indices(self):
        rec=major(b'LVLI',0x800,sub(b'EDID',b'Test\0'))
        malformed=[binary(rec)[:-1],binary(rec,rec),
                   binary(rec).replace(b'LVLI',b'FLOR',1),
                   binary(major(b'LVLI',0x01000800,sub(b'EDID',b'Test\0'))),
                   binary(major(b'LVLI',0x800,sub(b'EDID',b'Test\0')+b'X')),
                   binary(major(b'LVLI',0x800,struct.pack('<I',99)+zlib.compress(b'x'),0x40000))]
        for raw in malformed:
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'test.esp'
                path.write_bytes(raw)
                with self.assertRaises(ValueError): gate.read_plugin(path)


if __name__ == '__main__':
    unittest.main()
