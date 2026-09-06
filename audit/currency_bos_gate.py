"""Independent semantic checks for the generated currency BOS probability bins."""
from collections import defaultdict
from decimal import Decimal
import re

from currency_tier_contract import VALUES, all_families, complete_routes, form_key, need

MASKS = {
    'MorrowindUsesDrams_SWAP.ini', 'WindhelmUsesUlfrics_SWAP.ini',
    'DominionUsesSancar_SWAP.ini', 'C.O.I.N_SWAP.ini',
    'C.O.I.N. - Beyond Skyrim Patch_SWAP.ini', 'C.O.I.N. - The Cause Patch_SWAP.ini',
    'zz_Ensrick_Currency_80_Regional_SWAP.ini', 'zz_Ensrick_Currency_90_Ancient_SWAP.ini',
}


def key(text):
    match = re.fullmatch(r'0x([0-9A-Fa-f]{1,6})~([^|,]+)', text)
    need(match is not None, f'invalid exact BOS form: {text}')
    return form_key(match[1] + ':' + match[2])


def parse(text):
    scope, rules = None, defaultdict(list)
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(';'):
            continue
        if line.startswith('['):
            need(scope is None and line.startswith('[Forms|') and line.endswith(']'),
                 'exactly one conditional Forms section required')
            scope = line[7:-1].split(',')
            continue
        need(scope is not None, 'BOS rule outside reviewed section')
        parts = line.split('|')
        need(len(parts) == 4, 'BOS rule needs exact source/target/property/chance')
        source, target = key(parts[0]), key(parts[1])
        need(parts[2] == ('scale(1)' if source == target else 'NONE'),
             'identity swaps require scale(1); other transforms are not authorized')
        match = re.fullmatch(r'chanceS\(([0-9]+(?:\.[0-9]+)?)\)', parts[3])
        need(match is not None, 'only stable cumulative chanceS thresholds allowed')
        chance = Decimal(match[1])
        need(0 < chance <= 100, 'invalid cumulative chance threshold')
        rules[source].append((chance, target))
    return scope, dict(rules)


def distribution(rows):
    chances = [chance for chance, _ in rows]
    need(chances and chances[0] == 100 and
         all(left > right for left, right in zip(chances, chances[1:])),
         'rows must load in strictly descending cumulative threshold order')
    boundaries = sorted({Decimal(0), *chances})
    result = defaultdict(Decimal)
    for low, high in zip(boundaries, boundaries[1:]):
        midpoint = (low + high) / 2
        target = next(target for chance, target in reversed(rows) if midpoint <= chance)
        result[target] += high - low
    need(sum(result.values()) == 100, 'source probability is not exhausted')
    return dict(result)


def check_section(config, text, expected_families, conditions, purse_targets):
    scope, rules = parse(text)
    need(scope == conditions, 'BOS scope differs from reviewed cultural/location roots')
    canonical, recognized = {}, {}
    for family in config['families']:
        for coin in family['denominations']:
            item = (family['id'], coin['tier'], coin['value'])
            canonical[form_key(coin['form'])] = item
            recognized[form_key(coin['form'])] = item
        for alias in family.get('inputAliases', []):
            recognized[form_key(alias['form'])] = (family['id'], alias['tier'], VALUES[alias['tier']])
    gold = form_key('00000F:Skyrim.esm')
    purses = [form_key(item) for item in ('0D790C:Skyrim.esm', '0D8E7F:Skyrim.esm', '0D8E80:Skyrim.esm')]
    expected_sources = {gold, *recognized, *purses}
    pile_family = expected_families[0] if expected_families[0] in ('drakr_dragon', 'nchuark') else None
    pile_keys = [form_key(item) for item in ('018486:Dragonborn.esm', '018488:Dragonborn.esm')]
    if pile_family:
        expected_sources.update(pile_keys)
    need(set(rules) == expected_sources, 'BOS has a missing or unreviewed source form')
    gold_mix = distribution(rules[gold])
    need(len(gold_mix) == 3 * len(expected_families), 'some metal/face design cannot occur as loose Gold001')
    for target, probability in gold_mix.items():
        need(target in canonical, 'loose currency target is not a canonical denomination')
        identity, tier, _ = canonical[target]
        need(identity in expected_families, 'loose coin has the wrong regional design')
        need(probability == Decimal({'copper': 75, 'silver': 20, 'gold': 5}[tier]) / len(expected_families),
             'wrong 75/20/5 denomination or equal-face probability')
    for source, (source_family, tier, value) in recognized.items():
        outcomes = distribution(rules[source])
        allowed = [source_family] if source_family in expected_families else expected_families
        need(len(outcomes) == len(allowed), 'physical coin face route is incomplete')
        for target, probability in outcomes.items():
            need(target in canonical, 'physical output is not canonical')
            family, target_tier, target_value = canonical[target]
            need(target_tier == tier and target_value == value,
                 'physical coin reroll changes value; drop/pickup duplication risk')
            need(family in allowed and probability == Decimal(100) / len(allowed),
                 'physical coin cultural identity is incorrect')
    for source, target in zip(purses, purse_targets, strict=True):
        need(distribution(rules[source]) == {form_key(target): Decimal(100)},
             'purse size/regional target is wrong')
    if pile_family:
        target = form_key('0009C6:C.O.I.N.esp' if pile_family == 'drakr_dragon' else '000810:C.O.I.N.esp')
        for source in pile_keys:
            need(distribution(rules[source]) == {target: Decimal(100)}, 'authored cultural pile mapping lost')


def check(config, outputs, location_roots, purse_catalog):
    all_families(config)
    complete_routes(config)
    expected_names = set()
    for index, rule in enumerate(config['routing']['rules']):
        name = f'zz_Ensrick_Currency_{94-index:02d}_{rule["id"]}_SWAP.ini'
        expected_names.add(name)
        normalized = {form_key(item): item for item in rule['anyKeywords'] + location_roots[rule['id']]}
        conditions = [f'0x{int(normalized[item].split(":")[0],16):06X}~{normalized[item].split(":")[1]}'
                      for item in sorted(normalized)]
        check_section(config, outputs[name], rule['familyIds'], conditions,
                      purse_catalog[rule['familyIds'][0]])
    for name, condition in (
            ('zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini', '-DLC2GyldenhulBarrowLocation'),
            ('zz_Ensrick_Currency_95_Exceptions_SWAP.ini', 'DLC2GyldenhulBarrowLocation')):
        expected_names.add(name)
        check_section(config, outputs[name], ['septim'], [condition], purse_catalog['septim'])
    # Every other generated override must be an inert mask, not an unreviewed
    # second owner that can beat or intercept the checked routes.
    need(set(outputs) == expected_names | MASKS,
         'exact sixteen route/default/exception files and eight legacy masks required')
    for name, text in outputs.items():
        if name not in expected_names:
            need(parse(text) == (None, {}), f'unreviewed active BOS rules: {name}')
