"""Independent, read-only binary and exact-probability audit of regional purses.

This gate does not import the C# generator or trust its self-audit. It interprets
the emitted FLOR/LVLI records and compares whole-purse outcome distributions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import importlib.util
import json
import mmap
from pathlib import Path
import struct
import zlib

from biped_slot_audit import subrecords, zstring


def need(condition, message):
    if not condition:
        raise ValueError(message)


def normalized(text):
    local, plugin = text.split(':', 1)
    return f'{int(local, 16):06X}:{plugin.lower()}'


@dataclass(frozen=True)
class Record:
    key: str
    kind: str
    flags: int
    subs: tuple[tuple[bytes, bytes], ...]

    def one(self, tag, length=None):
        values = [value for current, value in self.subs if current == tag]
        need(len(values) == 1, f'{self.key}: expected exactly one {tag!r}')
        need(length is None or len(values[0]) == length, f'{self.key}: invalid {tag!r} length')
        return values[0]

    @property
    def editor_id(self):
        return zstring(self.one(b'EDID'), 'EDID')


@dataclass
class Plugin:
    name: str
    masters: list[str]
    flags: int
    records: dict[str, Record]
    declared_count: int
    actual_count: int
    group_count: int
    sha256: str

    def link(self, payload):
        need(len(payload) == 4, 'FormID must be exactly four bytes')
        value, = struct.unpack('<I', payload)
        if value == 0:
            return None
        modules = self.masters + [self.name]
        need(value >> 24 < len(modules), f'{self.name}: invalid master index {value:08X}')
        return normalized(f'{value & 0xFFFFFF:06X}:{modules[value >> 24]}')


def read_plugin(path: Path, selected_types=None):
    """Check every record boundary; materialize only requested record types."""
    with path.open('rb') as stream:
        need(path.stat().st_size >= 24, f'{path.name}: missing TES4 header')
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            need(raw[:4] == b'TES4', f'{path.name}: invalid TES4 header')
            size, flags = struct.unpack_from('<II', raw, 4)
            need(size + 24 <= len(raw), 'TES4 exceeds file')
            header = Record('header', 'TES4', flags, tuple(subrecords(raw[24:24+size])))
            hedr = header.one(b'HEDR', 12)
            masters = [zstring(value, 'MAST') for tag, value in header.subs if tag == b'MAST']
            need(len({name.lower() for name in masters + [path.name]}) == len(masters)+1,
                 'duplicate or self-referencing master')
            need(all(name and not any(char in name for char in '/\\:') for name in masters),
                 'invalid master filename')
            plugin = Plugin(path.name, masters, flags, {}, struct.unpack_from('<I', hedr, 4)[0],
                            0, 0, hashlib.sha256(raw).hexdigest().upper())
            observed = set()

            def walk(start, end, depth=0, top_group=None):
                need(depth < 32, 'excessive GRUP nesting')
                while start < end:
                    need(start+24 <= end, 'truncated record header')
                    tag, length, record_flags, form = struct.unpack_from('<4sIII', raw, start)
                    if tag == b'GRUP':
                        need(length >= 24 and start+length <= end, 'invalid GRUP bounds')
                        plugin.group_count += 1
                        group_type, = struct.unpack_from('<I',raw,start+12)
                        label = raw[start+8:start+12] if group_type == 0 else top_group
                        walk(start+24, start+length, depth+1,label)
                        start += length
                        continue
                    need(start+24+length <= end, 'record exceeds GRUP bounds')
                    need(form != 0 and form not in observed, 'null or duplicate record FormID')
                    observed.add(form)
                    plugin.actual_count += 1
                    kind = tag.decode('ascii')
                    if selected_types is None or kind in selected_types:
                        need(top_group == tag, 'selected record is outside its matching top-level GRUP')
                        key = plugin.link(struct.pack('<I', form))
                        body = raw[start+24:start+24+length]
                        if record_flags & 0x40000:
                            need(len(body) >= 4, 'compressed record missing length')
                            inflated_size, = struct.unpack_from('<I', body)
                            need(inflated_size <= 64*1024*1024, 'unreasonable compressed record length')
                            decoder = zlib.decompressobj()
                            body = decoder.decompress(body[4:], inflated_size+1)
                            need(len(body) == inflated_size and decoder.eof and not decoder.unused_data
                                 and not decoder.unconsumed_tail, 'malformed compressed record')
                        plugin.records[key] = Record(key, kind, record_flags, tuple(subrecords(body)))
                    start += 24+length
            walk(24+size, len(raw))
    return plugin


def read_strings(raw):
    need(len(raw) >= 8, 'truncated STRINGS header')
    count, size = struct.unpack_from('<II', raw)
    start = 8 + count*8
    need(start+size == len(raw), 'STRINGS directory/data length mismatch')
    result = {}
    for index in range(count):
        identity, offset = struct.unpack_from('<II', raw, 8+index*8)
        need(identity not in result and offset < size, 'duplicate STRINGS ID or invalid offset')
        end = raw.find(b'\0', start+offset)
        need(end >= start+offset, 'unterminated STRINGS value')
        result[identity] = raw[start+offset:end]
    return result


def pinned_python_source(raw, expected):
    """Permit checkout newline conversion only; retain raw provenance too."""
    raw_hash = hashlib.sha256(raw).hexdigest().upper()
    canonical_hash = hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest().upper()
    need(canonical_hash == expected, 'pinned BSA reader source hash drift')
    return raw_hash, canonical_hash


def archive_strings(path):
    """Reuse the pinned credential-free archive reader; never extract to disk."""
    root = Path(__file__).resolve().parents[1]
    assets = root/'mods/currency-integration/assets'
    pins = json.loads((assets/'inputs.json').read_text(encoding='utf-8-sig'))
    reader_path = root/'audit/modasset.py'
    reader_bytes = reader_path.read_bytes()
    # Git's Windows checkout may convert LF to CRLF. Python source pinning is
    # canonical-LF; do not otherwise alter whitespace, text or executable code.
    reader_hash, canonical_reader_hash = pinned_python_source(reader_bytes,pins['bsaReaderSha256'])
    spec = importlib.util.spec_from_file_location('currency_purse_asset_recipe',assets/'recipe.py')
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    recipe.REPO = root
    archive = recipe.bsa_reader()(path)
    member = 'strings/skyrim_english.strings'
    matches = [index for index,name in enumerate(archive.names())
               if name.replace('\\','/').lower() == member]
    need(len(matches) == 1, 'archive must contain exactly one original Skyrim English STRINGS member')
    raw = archive.read(matches[0])
    result = read_strings(raw)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest().upper()
    return result, dict(archiveSha256=digest, member=member, bytes=len(raw),
                        memberSha256=hashlib.sha256(raw).hexdigest().upper(),
                        readerSha256=reader_hash, canonicalLfReaderSha256=canonical_reader_hash,
                        recipeSha256=hashlib.sha256((assets/'recipe.py').read_bytes()).hexdigest().upper())


def flora_content(plugin, record, strings):
    """Normalize only FormIDs and localized text; retain every other byte."""
    result = []
    for tag, value in record.subs:
        if tag in (b'EDID', b'PFIG'):
            continue
        if tag in (b'FULL', b'RNAM'):
            if plugin.flags & 0x80:
                need(len(value) == 4, 'localized FLOR text requires a StringID')
                identity, = struct.unpack('<I', value)
                need(identity in strings, f'unresolved FLOR text StringID {identity:X}')
                value = strings[identity]
            else:
                need(value.endswith(b'\0') and b'\0' not in value[:-1], 'malformed inline FLOR text')
                value = value[:-1]
        elif tag == b'SNAM':
            value = plugin.link(value)
        else:
            # Reviewed vanilla templates have no VMAD, destructible, alternate
            # textures or keywords. Reject new fields rather than pretending
            # opaque bytes can prove safety of unparsed embedded FormIDs.
            need(tag in (b'OBND', b'MODL', b'MODT', b'PNAM', b'FNAM', b'PFPC'),
                 f'unreviewed FLOR field {tag!r}')
        result.append((tag, value))
    return tuple(result)


def list_entries(plugin, record):
    need(record.kind == 'LVLI', 'payout graph traversed a non-LVLI record')
    allowed = {b'EDID', b'OBND', b'LVLD', b'LVLF', b'LLCT', b'LVLO'}
    need(all(tag in allowed for tag, _ in record.subs), 'unreviewed LVLI field/global/ownership')
    record.one(b'EDID')
    need(record.one(b'OBND', 12) == bytes(12), 'LVLI has unreviewed bounds')
    need(record.one(b'LVLD', 1) == b'\0', 'purse payout has nonzero chance-none')
    flags = record.one(b'LVLF', 1)[0]
    need(flags in (0, 4), 'purse graph uses per-item rerolls or unreviewed LVLI flags')
    values = [value for tag, value in record.subs if tag == b'LVLO']
    need(len(values) == record.one(b'LLCT', 1)[0] and 0 < len(values) <= 255,
         'LVLI entry counter or size is invalid')
    result = []
    for value in values:
        need(len(value) == 12, 'invalid LVLO size')
        level, unknown, _, count, unknown2 = struct.unpack('<hhIhh', value)
        need(level == 1 and unknown == unknown2 == 0 and count > 0,
             'LVLO level, count or reserved field changed')
        target = plugin.link(value[4:8])
        need(target is not None, 'null LVLO target')
        result.append((target, count))
    return flags, result


def add_vectors(left, right):
    return tuple(a+b for a, b in zip(left, right, strict=True))


def convolve(left, right):
    result = defaultdict(Fraction)
    for a, pa in left.items():
        for b, pb in right.items():
            result[add_vectors(a, b)] += pa*pb
    need(len(result) <= 4096, 'purse graph has excessive outcome complexity')
    return dict(result)


class Evaluator:
    def __init__(self, plugin, coins):
        self.plugin, self.coins = plugin, coins
        self.cache, self.visited, self.active = {}, set(), set()

    def evaluate(self, key):
        if key in self.coins:
            vector = [0, 0, 0]
            vector[self.coins[key]] = 1
            return {tuple(vector): Fraction(1)}
        need(key in self.plugin.records, f'unresolved or foreign-family payout link: {key}')
        need(key not in self.active, f'cyclic LVLI payout graph at {key}')
        if key in self.cache:
            return self.cache[key]
        need(len(self.active) < 32, 'payout graph depth exceeds reviewed bound')
        self.active.add(key)
        self.visited.add(key)
        flags, entries = list_entries(self.plugin, self.plugin.records[key])
        output = {(0, 0, 0): Fraction(1)} if flags == 4 else defaultdict(Fraction)
        for target, count in entries:
            child = self.evaluate(target)
            # CalculateForEachItemInCount is forbidden above, so the selected
            # complete child vector is multiplied, never independently rerolled.
            child = {tuple(value*count for value in vector): probability
                     for vector, probability in child.items()}
            if flags == 4:
                output = convolve(output, child)
            else:
                for vector, probability in child.items():
                    output[vector] += probability / len(entries)
        self.active.remove(key)
        need(sum(output.values()) == 1, 'purse probability is not exhausted')
        self.cache[key] = dict(output)
        return self.cache[key]


def vectors(amount):
    gold, remainder = divmod(amount, 100)
    silver, copper = divmod(remainder, 10)
    canonical = (copper, silver, gold)
    broken = (copper, silver+10, gold-1) if gold else (
        (copper+10, silver-1, 0) if silver else canonical)
    return canonical, broken


def expected_distribution(amounts):
    result = defaultdict(Fraction)
    for amount in amounts:
        canonical, broken = vectors(amount)
        result[canonical] += Fraction(4, 5*len(amounts))
        result[broken] += Fraction(1, 5*len(amounts))
    return dict(result)


FAMILY_LAYOUT = [('mede', 0x800, 0x810), ('oshka', 0x803, 0x813),
                 ('ohzer', 0x806, 0x816), ('varken', 0x809, 0x819),
                 ('bruma_ayleid_mala', 0x80C, 0x81C)]
PINNED_AMOUNTS = [
    [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 22, 28],
    [5, 8, 10, 12, 14, 16, 18, 19, 20, 21, 22, 24, 27, 30, 36, 42],
    [10, 14, 18, 22, 26, 29, 31, 33, 35, 36, 38, 41, 45, 50, 58, 70],
]
SOURCES = ['0D790C:Skyrim.esm', '0D8E7F:Skyrim.esm', '0D8E80:Skyrim.esm']
MASTER_NAMES = ['Skyrim.esm', 'Update.esm', 'BSAssets.esm',
                'exchangeCurrency_patch_COIN.esp', 'Ensrick Currency Integration Patch.esp']


def audit(companion, main, skyrim, strings, policy, config):
    expected_name = 'Ensrick Currency Regional Purses.esp'
    need(companion.name == expected_name, 'wrong regional purse plugin filename')
    need(companion.masters == MASTER_NAMES, 'regional purse exact master order differs')
    need(companion.flags == 0x200, 'regional purse must be only ESL flagged')
    need(companion.actual_count == 405 and len(companion.records) == 405 and
         Counter(row.kind for row in companion.records.values()) == {'FLOR': 15, 'LVLI': 390},
         'regional purse record/type count changed')
    need(companion.declared_count == companion.actual_count+companion.group_count,
         'regional purse TES4 record/group count mismatch')
    need(main.name == MASTER_NAMES[-1] and main.flags & 0x200, 'main currency master is not ESL flagged')
    layout = policy['overrides']['regionalPurseCompanion']
    need(layout['outputPlugin'] == expected_name and int(layout['terminalFormIdBase'],16) == 0x820 and
         [(item['familyId'],int(item['floraFormIdBase'],16),int(item['budgetFormIdBase'],16))
          for item in layout['families']] == FAMILY_LAYOUT, 'purse layout policy changed')
    purse_policy = policy['overrides']['coinPurses']
    need([item['counts'] for item in purse_policy] == PINNED_AMOUNTS and
         [normalized(item['floraFormKey']) for item in purse_policy] == list(map(normalized,SOURCES)),
         'pinned purse amount/source policy changed')
    own = lambda identity: normalized(f'{identity:06X}:{expected_name}')
    expected_ids = set(range(0x800,0x80F)) | set(range(0x810,0x81F)) | set(range(0x820,0x997))
    need(set(companion.records) == {own(identity) for identity in expected_ids},
         'purse plugin contains overrides, missing IDs or out-of-range owned IDs')
    need(all(row.flags == 0 for row in companion.records.values()), 'purse records carry unexpected flags')
    need(len({row.editor_id for row in companion.records.values()}) == 405,
         'purse plugin contains duplicate EditorIDs')
    visited, results = set(), []
    by_id = {family['id']: family for family in config['families']}
    for family, flora_base, budget_base in FAMILY_LAYOUT:
        coins = {normalized(coin['form']): ('copper','silver','gold').index(coin['tier'])
                 for coin in by_id[family]['denominations']}
        need(len(coins) == 3, 'regional purse family does not have three unique coin forms')
        for key, tier in coins.items():
            need(key in main.records and main.records[key].kind == 'MISC',
                 f'purse denomination lacks main winning MISC: {key}')
            value = struct.unpack_from('<I', main.records[key].one(b'DATA',8))[0]
            need(value == (1,10,100)[tier], f'purse denomination has wrong actual value: {key}')
        evaluator = Evaluator(companion, coins)
        for index, size in enumerate(('Small','Medium','Large')):
            source = skyrim.records[normalized(SOURCES[index])]
            flora = companion.records[own(flora_base+index)]
            need(flora.kind == 'FLOR' and flora.editor_id == f'Ensrick_{family}_CoinPurse{size}',
                 'wrong purse FLOR type/EditorID')
            need(source.editor_id == f'CoinPurse{size}', 'vanilla purse source identity changed')
            need(flora_content(companion, flora, strings) == flora_content(skyrim, source, strings),
                 f'{flora.key}: original FLOR fields changed beyond EDID/ingredient/header')
            sound = companion.link(flora.one(b'SNAM',4))
            need(sound in skyrim.records and skyrim.records[sound].kind == 'SNDR',
                 'purse harvest sound has an unresolved/wrong-type outgoing link')
            target = companion.link(flora.one(b'PFIG',4))
            need(target == own(budget_base+index), 'purse ingredient points to wrong size/family budget')
            budget = companion.records[target]
            flags, entries = list_entries(companion,budget)
            need(flags == 0 and len(entries) == 16 and
                 budget.editor_id == f'Ensrick_{family}_CoinPurse{size}Budget',
                 'purse budget is not the reviewed 16-entry selector')
            output = evaluator.evaluate(target)
            need(output == expected_distribution(PINNED_AMOUNTS[index]),
                 f'{family}/{size}: actual whole-purse 80/20 distribution differs')
            for vector in output:
                need(sum(a*b for a,b in zip(vector,(1,10,100))) in PINNED_AMOUNTS[index],
                     'purse creates an unapproved total value')
            results.append(dict(family=family,size=size,flora=flora.key,budget=target,
                                distinctVectors=len(output), totalProbability='1',
                                amounts=PINNED_AMOUNTS[index], canonicalFraction='4/5',singleBreakFraction='1/5'))
        visited |= evaluator.visited
    need(visited == {row.key for row in companion.records.values() if row.kind == 'LVLI'},
         'companion contains unreachable or unreviewed LVLI records')
    return dict(status='offline-binary-and-exact-probability-pass; not in-game verification',
                companionSha256=companion.sha256, mainSha256=main.sha256,
                skyrimSha256=skyrim.sha256, masters=companion.masters,
                ownedRecords=405, floraClones=15, reachableLists=len(visited), purses=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--companion',type=Path,required=True)
    parser.add_argument('--main',type=Path,required=True)
    parser.add_argument('--skyrim',type=Path,required=True)
    strings = parser.add_mutually_exclusive_group(required=True)
    strings.add_argument('--strings',type=Path,help='Exact original Skyrim English STRINGS file')
    strings.add_argument('--strings-archive',type=Path,help='Original Skyrim - Interface.bsa; read exact English STRINGS member in memory')
    parser.add_argument('--policy',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,help='Optional offline JSON evidence output')
    options = parser.parse_args()
    if options.output:
        input_paths = [getattr(options,name) for name in
                       ('companion','main','skyrim','strings','strings_archive','policy','config')]
        need(options.output.suffix.lower() == '.json' and
             options.output.resolve() not in {path.resolve() for path in input_paths if path},
             'evidence output must be a JSON file distinct from every input')
    if options.strings_archive:
        source_strings, string_proof = archive_strings(options.strings_archive)
    else:
        raw = options.strings.read_bytes()
        source_strings = read_strings(raw)
        string_proof = dict(memberSha256=hashlib.sha256(raw).hexdigest().upper(),bytes=len(raw))
    result = audit(read_plugin(options.companion),read_plugin(options.main,{'MISC'}),
                   read_plugin(options.skyrim,{'FLOR','SNDR'}),source_strings,
                   json.loads(options.policy.read_text(encoding='utf-8-sig')),
                   json.loads(options.config.read_text(encoding='utf-8-sig')))
    result['additionalInputHashes'] = {name: hashlib.sha256(getattr(options,name).read_bytes()).hexdigest().upper()
                                       for name in ('policy','config')}
    result['sourceStrings'] = string_proof
    result['verifierSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()
    result['parserHelpersCanonicalLfSha256'] = hashlib.sha256(
        Path(__file__).with_name('biped_slot_audit.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()
    rendered = json.dumps(result,indent=2)+'\n'
    if options.output:
        options.output.write_text(rendered,encoding='utf-8')
    print(rendered,end='')


if __name__ == '__main__':
    main()
