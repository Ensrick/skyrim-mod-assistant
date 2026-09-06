"""Read-only final MO2 MISC winners for all 54 coin tiers and their input alias.

This checks plugin record winners, not subsequent SKSE/SkyPatcher mutations or
the on-disk texture/mesh assets. Candidate substitution is explicitly simulated;
the profile, plugins and game are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import struct

from biped_slot_audit import runtime_plugins, zstring
from currency_purse_gate import need, normalized, read_plugin
from currency_tier_contract import complete_designs

MAIN = 'Ensrick Currency Integration Patch.esp'
HELPER = 'Ensrick Currency Regional Purses.esp'
NO_SALE = normalized('0FF9FB:Skyrim.esm')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest().upper()


def expected_forms(policy, config):
    complete_designs(policy,config)
    definitions = {family['id']:family for family in policy['denominations']['tieredFamilies']}
    result = {}
    for family in config['families']:
        for coin in family['denominations'] + family.get('inputAliases',[]):
            tier = coin['tier']
            planned = definitions[family['id']]['tiers'][tier]
            key = normalized(coin['form'])
            need(key not in result, 'duplicate expected physical FormKey')
            result[key] = dict(family=family['id'],tier=tier,value=planned['value'],
                               name=planned['name'],model=planned['model'],
                               alias=coin in family.get('inputAliases',[]))
    need(len(result) == 55, 'final-winner gate requires all 55 physical forms')
    return result


def candidate_order(paths, main=None, helper=None):
    """Substitute active main only; optionally insert its companion afterwards."""
    result = list(paths)
    if helper:
        need(main is not None, 'candidate helper requires an explicit paired candidate main')
    if main:
        need(main.name == MAIN, 'candidate main filename differs from owned plugin')
        indices = [index for index,path in enumerate(result) if path.name.lower() == MAIN.lower()]
        need(len(indices) == 1, 'candidate main must replace exactly one already-active main plugin')
        result[indices[0]] = main
    if helper:
        need(helper.name == HELPER, 'candidate helper filename differs from owned companion')
        result = [path for path in result if path.name.lower() != HELPER.lower()]
        index = next(i for i,path in enumerate(result) if path.name.lower() == MAIN.lower())
        result.insert(index+1,helper)
    return result


def record_fields(plugin, record):
    need(record.kind == 'MISC' and not record.flags & 0x20, 'winning physical coin is missing/deleted/non-MISC')
    # Owned winners and the reviewed ECE Septim source are non-localized.
    # Do not misinterpret a future localized StringID as an inline name.
    need(not plugin.flags & 0x80, 'localized winning MISC requires a separately resolved name; cannot certify inline text')
    name = zstring(record.one(b'FULL'),'MISC FULL')
    model = zstring(record.one(b'MODL'),'MISC MODL')
    value, = struct.unpack_from('<I',record.one(b'DATA',8))
    count, = struct.unpack('<I',record.one(b'KSIZ',4))
    keyword_bytes = record.one(b'KWDA')
    need(len(keyword_bytes) == 4*count, 'MISC keyword counter/data mismatch')
    keywords = [plugin.link(keyword_bytes[index:index+4]) for index in range(0,len(keyword_bytes),4)]
    need(None not in keywords, 'null physical coin keyword')
    return dict(name=name,model=model,value=value,vendorNoSale=NO_SALE in keywords)


def model_path(text):
    """MODL may be meshes-relative; Mutagen policy AssetLinks include Meshes."""
    path=PureWindowsPath(text)
    need(not path.drive and not path.root and '..' not in path.parts and path.suffix.lower()=='.nif',
         'invalid model path')
    parts=[part.casefold() for part in path.parts]
    if parts and parts[0]=='meshes': parts=parts[1:]
    need(parts and parts[0]!='meshes', 'duplicate model root prefix')
    return 'meshes/'+'/'.join(parts)


def check_winners(expected, winners):
    reports, blockers = [], []
    for key, wanted in expected.items():
        report = dict(formKey=key,expected=wanted)
        if key not in winners:
            report['errors'] = ['no active winning MISC declaration']
        else:
            plugin, record = winners[key]
            report.update(winningPlugin=plugin.name,winningPluginSha256=plugin.sha256)
            try:
                actual = record_fields(plugin,record)
                report['actual'] = actual
                errors = []
                for field in ('name','value'):
                    if actual[field] != wanted[field]:
                        errors.append(f'{field} differs from approved tier')
                if model_path(actual['model']) != model_path(wanted['model']):
                    errors.append('model differs from approved tier')
                if not actual['vendorNoSale']:
                    errors.append('VendorItemNoSale keyword missing')
                report['errors'] = errors
            except ValueError as error:
                report['errors'] = [str(error)]
        if report['errors']:
            blockers.append(dict(formKey=key,winningPlugin=report.get('winningPlugin'),errors=report['errors']))
        reports.append(report)
    return reports,blockers


def scan(paths, expected):
    winners,inputs = {},[]
    for order,path in enumerate(paths):
        plugin = read_plugin(path,{'MISC'})
        inputs.append(dict(order=order,plugin=plugin.name,sha256=plugin.sha256))
        for key,record in plugin.records.items():
            if key in expected:
                # Retain deleted winners too; deletion must not resurrect an
                # earlier valid declaration by accidentally filtering it out.
                winners[key] = (plugin,record)
    reports,blockers = check_winners(expected,winners)
    return dict(physicalForms=len(expected),forms=reports,blockers=blockers,
                inputPlugins=inputs,pluginCount=len(paths))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance',type=Path,required=True)
    parser.add_argument('--game-data',type=Path,required=True)
    parser.add_argument('--policy',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--candidate-main',type=Path)
    parser.add_argument('--candidate-helper',type=Path)
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if options.output:
        need(options.output.suffix.lower()=='.json' and options.output.resolve() not in
             {path.resolve() for path in (options.policy,options.config,options.candidate_main,options.candidate_helper) if path},
             'diagnostic output must be distinct JSON evidence, not an input')
        need(options.instance.resolve() not in options.output.resolve().parents and
             options.game_data.resolve() not in options.output.resolve().parents,
             'diagnostic evidence must stay outside the live profile and game Data')
    expected=expected_forms(json.loads(options.policy.read_text(encoding='utf-8-sig')),
                            json.loads(options.config.read_text(encoding='utf-8-sig')))
    profile_paths={str(path.relative_to(options.instance)):path for path in (
        options.instance/'profiles/Default/modlist.txt',options.instance/'profiles/Default/plugins.txt')}
    ccc=options.game_data.parent/'Skyrim.ccc'
    if ccc.is_file(): profile_paths['Skyrim.ccc']=ccc
    profile_before={name:sha(path) for name,path in profile_paths.items()}
    active_paths=runtime_plugins(options.instance,options.game_data)
    paths=candidate_order(active_paths,
                          options.candidate_main,options.candidate_helper)
    result=scan(paths,expected)
    need(profile_before == {name:sha(path) for name,path in profile_paths.items()} and
         active_paths == runtime_plugins(options.instance,options.game_data),
         'active profile or resolved plugin providers changed during the scan')
    need(all(sha(path)==entry['sha256'] for path,entry in zip(paths,result['inputPlugins'],strict=True)),
         'plugin bytes changed during the scan')
    result['mode']='candidate-substitution-simulation' if options.candidate_main else 'actual-active-plugin-winners'
    result['status']='PASS' if not result['blockers'] else 'FAIL'
    result['scope']='Plugin MISC winners only; later engine/SKSE data mutation and asset winners require separate gates.'
    result['inputHashes']={'policy':sha(options.policy),'config':sha(options.config)}
    result['profileInputs']=profile_before
    result['stableSnapshotVerified']=True
    result['verifierSha256']=sha(Path(__file__))
    result['parserSourcesCanonicalLfSha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()
        for name in ('biped_slot_audit.py','currency_purse_gate.py','currency_tier_contract.py')}
    rendered=json.dumps(result,indent=2)+'\n'
    if options.output: options.output.write_text(rendered,encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('status','mode','physicalForms','pluginCount','blockers')},indent=2))
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    raise SystemExit(main())
