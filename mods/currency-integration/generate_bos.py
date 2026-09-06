"""Deterministic complete-tier BOS configuration; no live-profile writes.

Semantics are pinned to the inspected BOS source c0b9c093aa6260fd9b68beddea411db97f585ea2:
conditional keys sort by path|conditions, descending; rows are tried in reverse;
chanceS reuses the same reference hash. Therefore probabilities are cumulative
intervals, not independent rolls. Explicit face intervals avoid correlation
between a chance roll and BOS's re-seeded random comma-target selection.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'audit'))
from currency_tier_contract import all_families, complete_routes, form_key

GOLD = '00000F:Skyrim.esm'
PURSE_PLUGIN = 'Ensrick Currency Regional Purses.esp'
VANILLA_PURSES = ['0D790C:Skyrim.esm', '0D8E7F:Skyrim.esm', '0D8E80:Skyrim.esm']
PURSES = {
    'septim': VANILLA_PURSES,
    'drakr_dragon': ['000805:C.O.I.N.esp', '000804:C.O.I.N.esp', '000803:C.O.I.N.esp'],
    'nchuark': ['00080F:C.O.I.N.esp', '00080E:C.O.I.N.esp', '00080D:C.O.I.N.esp'],
    'mallari': ['000934:C.O.I.N.esp', '000935:C.O.I.N.esp', '000936:C.O.I.N.esp'],
    'mala': ['00093D:C.O.I.N.esp', '00093E:C.O.I.N.esp', '00093F:C.O.I.N.esp'],
    'gibber_dementia': ['000C5D:C.O.I.N.esp', '000C5E:C.O.I.N.esp', '000C5F:C.O.I.N.esp'],
    'dram': ['000F1C:M.I.N.T.esp', '000F1D:M.I.N.T.esp', '000F1E:M.I.N.T.esp'],
    'sancar': ['000F1F:M.I.N.T.esp', '000F20:M.I.N.T.esp', '000F21:M.I.N.T.esp'],
    'ulfric': ['000F22:M.I.N.T.esp', '000F23:M.I.N.T.esp', '000F24:M.I.N.T.esp'],
    **{identity: [f'{0x800+3*i+size:06X}:{PURSE_PLUGIN}' for size in range(3)]
       for i, identity in enumerate(('mede', 'oshka', 'ohzer', 'varken', 'bruma_ayleid_mala'))},
}
MASKS = [
    'MorrowindUsesDrams_SWAP.ini', 'WindhelmUsesUlfrics_SWAP.ini',
    'DominionUsesSancar_SWAP.ini', 'C.O.I.N_SWAP.ini',
    'C.O.I.N. - Beyond Skyrim Patch_SWAP.ini', 'C.O.I.N. - The Cause Patch_SWAP.ini',
    'zz_Ensrick_Currency_80_Regional_SWAP.ini', 'zz_Ensrick_Currency_90_Ancient_SWAP.ini',
]


def bos_form(key):
    form_key(key)  # Validate before emitting a source-derived identifier.
    local, plugin = key.split(':')
    return f'0x{int(local, 16):06X}~{plugin}'


def thresholds(families, metals):
    """Ascending disjoint bins; each design receives the same tier share."""
    result, total = [], Decimal(0)
    for tier, percent in metals:
        step = Decimal(percent) / len(families)
        for family in families:
            total += step
            coin = next(item['form'] for item in family['denominations'] if item['tier'] == tier)
            result.append((total, coin))
    if total != 100:
        raise ValueError('BOS intervals must exhaust the full source probability')
    return result


def rows(source, bins):
    result = []
    for threshold, target in reversed(bins):
        # BOS rejects identity swaps without a property. scale(1) is an exact
        # multiplicative no-op, preserving authored refScale while reserving
        # this winning result against lower-priority legacy rules.
        properties = 'scale(1)' if form_key(source) == form_key(target) else 'NONE'
        percent = format(threshold, 'f').rstrip('0').rstrip('.') if '.' in format(threshold, 'f') else str(threshold)
        result.append(f'{bos_form(source)}|{bos_form(target)}|{properties}|chanceS({percent})')
    return result


def section(config, family_ids, conditions):
    by_id = {family['id']: family for family in config['families']}
    selected = [by_id[identity] for identity in family_ids]
    lines = [f'[Forms|{",".join(conditions)}]']
    lines += rows(GOLD, thresholds(selected, [('gold', 5), ('silver', 20), ('copper', 75)]))
    for family in config['families']:
        for coin in family['denominations'] + family.get('inputAliases', []):
            # Existing physical denominations NEVER receive the loose Gold001
            # reroll. In particular, dropping copper cannot create silver/gold.
            choices = [family] if family['id'] in family_ids else selected
            lines += rows(coin['form'], thresholds(choices, [(coin['tier'], 100)]))
    for source, target in zip(VANILLA_PURSES, PURSES[family_ids[0]], strict=True):
        lines += rows(source, [(Decimal(100), target)])
    if family_ids[0] in ('drakr_dragon', 'nchuark'):
        target = '0009C6:C.O.I.N.esp' if family_ids[0] == 'drakr_dragon' else '000810:C.O.I.N.esp'
        for source in ('018486:Dragonborn.esm', '018488:Dragonborn.esm'):
            lines += rows(source, [(Decimal(100), target)])
    return '\n'.join(lines) + '\n'


def build(config, location_roots):
    all_families(config)
    complete_routes(config)
    rule_ids = {rule['id'] for rule in config['routing']['rules']}
    if set(location_roots) != rule_ids:
        raise ValueError('exact fourteen reviewed location-root sets required')
    result = {name: '; Superseded by the complete, ordered Ensrick currency route files.\n'
              '; Deliberate filename mask: no competing single-copper owner.\n' for name in MASKS}
    header = ('; GENERATED by generate_bos.py. Do not edit individual probability rows.\n'
              '; Only loose Gold001 rolls 75/20/5. Physical coins preserve value.\n'
              '; Chance thresholds share one stable reference hash; last rows run first.\n')
    result['zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini'] = header + section(
        config, ['septim'], ['-DLC2GyldenhulBarrowLocation'])
    for index, rule in enumerate(config['routing']['rules']):
        keys = rule['anyKeywords'] + location_roots[rule['id']]
        unique = {form_key(key): key for key in keys}
        conditions = [bos_form(unique[key]) for key in sorted(unique)]
        name = f'zz_Ensrick_Currency_{94-index:02d}_{rule["id"]}_SWAP.ini'
        result[name] = header + '; Explicit location roots also match descendants, unlike BOS keyword filters.\n' + section(
            config, rule['familyIds'], conditions)
    result['zz_Ensrick_Currency_95_Exceptions_SWAP.ini'] = header + (
        '; Preserve the reviewed Gyldenhul treasure exception above all cultural routes.\n') + section(
            config, ['septim'], ['DLC2GyldenhulBarrowLocation'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--locations', type=Path, default=ROOT / 'bos-location-roots.json')
    options = parser.parse_args()
    config = json.loads((ROOT / 'package/SKSE/Plugins/EnsrickCurrencyDenominations.json').read_text())
    roots = json.loads(options.locations.read_text())['routeLocations']
    outputs = build(config, roots)
    for name, text in outputs.items():
        target = ROOT / 'package' / name
        raw = text.encode('utf-8')
        if options.check:
            if not target.is_file() or target.read_bytes() != raw:
                raise ValueError(f'BOS output differs from checked source: {name}')
        else:
            target.write_bytes(raw)
    print(f'{len(outputs)} deterministic BOS files: {"verified" if options.check else "generated privately"}')


if __name__ == '__main__':
    main()
