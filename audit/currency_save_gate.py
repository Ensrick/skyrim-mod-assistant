"""Read-only launch admission for the native currency ledger; never edits saves.

SKSE wrapper layout: pinned skse64 Serialization.cpp Header/PluginHeader/
ChunkHeader. Currency payload: SaveMarkerPolicy.h ECMK v2. Passing proves a
matching checkpoint, not gameplay correctness or complete save health.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

DLL = 'SKSE/Plugins/EnsrickCurrencyDenominations.dll'
CONFIG = 'SKSE/Plugins/EnsrickCurrencyDenominations.json'
PLUGIN = 'Ensrick Currency Integration Patch.esp'
PURSES = 'Ensrick Currency Regional Purses.esp'
RECEIPT = Path(__file__).resolve().parents[1] / 'records/source-builds/currency-integration-0.4.0-native-0.2.3.json'
MAX_COSAVE = 256 * 1024 * 1024
MAX_VALUE = 2**31 - 1
MASK64 = 2**64 - 1


def winning_file(instance, game_data, relative, profile='Default'):
    instance = Path(instance)
    rows = (instance / 'profiles' / profile / 'modlist.txt').read_text(encoding='utf-8-sig').splitlines()
    # MO2 modlist is descending priority: first active loose file wins.
    roots = [instance / 'overwrite'] + [instance / 'mods' / row[1:] for row in rows if row.startswith('+')]
    roots.append(Path(game_data))
    return next((root / relative for root in roots if (root / relative).is_file()), None)


def ledger_fingerprint(config):
    """Byte-identical to schema-2 ComputeLedgerFingerprint, including order."""
    if config.get('schemaVersion') != 2:
        raise ValueError('currency schema 2 is required; legacy exclusions are unsupported')
    data = bytearray()

    def integer(value):
        data.extend(struct.pack('<Q', value))

    def string(value, fold=False):
        raw = value.encode('utf-8')
        integer(len(raw))
        data.extend(raw.lower() if fold else raw)  # C locale byte folding.

    def form(value):
        local, plugin = value.split(':')
        if not plugin or not 1 <= len(local) <= 6:
            raise ValueError('invalid ledger FormKey')
        string(plugin, True)
        integer(int(local, 16))

    string('EnsrickCurrencyLedgerV2')
    string(config['accounting']['owner'])
    integer(int(config['accounting']['strictSingleOwner']))
    form(config['accounting']['backendForm'])
    integer(int(config['excludePhysicalFormsFromOrdinaryBarter']))
    integer(int(config['excludePhysicalFormsFromDrop']))
    integer(config['distribution']['canonicalPercent'])
    integer(config['distribution']['variantPercent'])
    integer(int(config['distribution']['seed'], 16))
    integer(len(config['routing']['precedence']))
    for phase in config['routing']['precedence']:
        string(phase)
    integer(len(config['families']))
    for family in config['families']:
        string(family['id'])
        string(family['displayLabel'])
        string(family['backendLabel'])
        integer(int(family['salt'], 16))
        integer(int(family['enabled']))
        integer(int(family['fallback']))
        integer(int(family.get('perk') is not None))
        if family.get('perk') is not None:
            form(family['perk'])
        integer(len(family['denominations']))
        for denomination in family['denominations']:
            string(denomination['tier'])
            integer(denomination['value'])
            form(denomination['form'])
        aliases = family.get('inputAliases', [])
        integer(len(aliases))
        for alias in aliases:
            string(alias['tier'])
            form(alias['form'])
    integer(len(config['routing']['rules']))
    for rule in config['routing']['rules']:
        string(rule['id'])
        integer(len(rule['anyKeywords']))
        for keyword in rule['anyKeywords']:
            form(keyword)
        integer(len(rule['familyIds']))
        for identity in rule['familyIds']:
            string(identity)
    result = 14695981039346656037
    for byte in data:
        result = ((result ^ byte) * 1099511628211) & MASK64
    return result


def read_checkpoint(raw, expected_fingerprint):
    """Strictly bound each wrapper/record; reject duplicate or unsupported data."""
    if len(raw) > MAX_COSAVE or len(raw) < 20:
        raise ValueError('co-save size invalid')
    signature, version, _skse, _runtime, plugins = struct.unpack_from('<4s4I', raw)
    if signature != b'SKSE' or version != 1:
        raise ValueError('unsupported SKSE co-save header')
    offset, checkpoint, currency_plugins = 20, None, 0
    for _ in range(plugins):
        if offset + 12 > len(raw):
            raise ValueError('truncated plugin header')
        identity, chunks, length = struct.unpack_from('<4sII', raw, offset)
        offset += 12
        end = offset + length
        if end > len(raw):
            raise ValueError('plugin length exceeds co-save')
        currency = identity == b'ECDN'
        if currency:
            currency_plugins += 1
            if currency_plugins != 1:
                raise ValueError('duplicate currency plugin data')
        for _ in range(chunks):
            if offset + 12 > end:
                raise ValueError('truncated chunk header')
            kind, chunk_version, size = struct.unpack_from('<4sII', raw, offset)
            offset += 12
            if offset + size > end:
                raise ValueError('chunk length exceeds plugin')
            if currency:
                if checkpoint is not None or kind != b'ECMK' or chunk_version != 2 or size != 40:
                    raise ValueError('missing, duplicate or unsupported currency checkpoint')
                magic, schema, fingerprint, value, backend, physical = struct.unpack_from('<4sI4Q', raw, offset)
                if magic != b'ECV2' or schema != 2:
                    raise ValueError('invalid currency checkpoint payload')
                if not expected_fingerprint or fingerprint != expected_fingerprint:
                    raise ValueError('currency configuration does not match this save')
                if any(number > MAX_VALUE for number in (value, backend, physical)):
                    raise ValueError('currency checkpoint exceeds supported balance')
                checkpoint = dict(value=value, backend=backend, physical=physical, fingerprint=fingerprint)
            offset += size
        if offset != end:
            raise ValueError('plugin length/chunk count mismatch')
    if offset != len(raw):
        raise ValueError('trailing co-save data')
    if checkpoint is None:
        raise ValueError('no native currency v2 checkpoint; this can mean an older save '
                         'or failed bridge initialization/serialization, not proof of save age')
    return checkpoint


def reviewed_test_dll(build, instance, profile, release):
    """Explicit source-bound private test exception for the DLL only.

    Never accepts arbitrary replacement receipts or alters the normal release
    contract. This authorizes testing, not installation or gameplay acceptance.
    """
    if not profile.startswith('Astra Load262 ') or any(char in profile for char in '/\\:'):
        raise ValueError('native candidate requires a dedicated Load262 test profile')
    settings = (Path(instance) / 'profiles' / profile / 'settings.ini').read_text()
    values = [row.strip().lower() for row in settings.splitlines()]
    if values.count('localsaves=true') != 1 or 'localsaves=false' in values:
        raise ValueError('native candidate requires isolated local saves')
    build = Path(build).resolve(strict=True)
    native = json.loads((build / 'native-build-receipt.json').read_text(encoding='utf-8-sig'))
    source = Path(__file__).resolve().parents[1] / 'mods/currency-integration/native'
    if (Path(native['sourceRoot']).resolve() != source.resolve()
            or native['schemaVersion'] != 1 or native['runtime'] != '1.7.104.0'
            or native['skse'] != '2.3.1'
            or native['commonLibCommit'] != '90a64a4d65ce659a139137c968f42151bb6ecec9'
            or native['commonLibTrackedStatus'] != 'clean'
            or native['runtimeConfig']['sha256'] != release['winningFiles'][CONFIG]):
        raise ValueError('native candidate build contract mismatch')
    inputs = native['sourceInputs']
    seen = set()
    for item in inputs:
        relative = Path(item['relativePath'])
        resolved = (source / relative).resolve(strict=True)
        if (relative.is_absolute() or '..' in relative.parts
                or not resolved.is_relative_to(source.resolve()) or resolved in seen):
            raise ValueError('invalid or duplicate native source input')
        seen.add(resolved)
        data = resolved.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest().upper() != item['sha256']:
            raise ValueError('native candidate source changed since build')
    required = {source / name for name in ('src/Plugin.cpp', 'src/AdmissionIdentity.h',
                                          'CMakeLists.txt', 'build-native.ps1')}
    if not required.issubset(seen):
        raise ValueError('native candidate missing critical source inputs')
    dll = native['dll']
    data = (build / 'build/Release/EnsrickCurrencyDenominations.dll').read_bytes()
    if (dll['relativePath'] != DLL or len(data) != dll['bytes']
            or hashlib.sha256(data).hexdigest().upper() != dll['sha256']):
        raise ValueError('native candidate binary does not match its source receipt')
    return dll['sha256']


def check_save(instance, game_data, save_path, profile='Default', *, receipt_path=RECEIPT,
               test_native_build=None):
    """Return launch blockers only when the native package is reachable."""
    try:
        dll = winning_file(instance, game_data, DLL, profile)
        config_path = winning_file(instance, game_data, CONFIG, profile)
        esp = winning_file(instance, game_data, PLUGIN, profile)
        purses = winning_file(instance, game_data, PURSES, profile)
        if test_native_build and not all((dll, config_path, esp, purses)):
            return ['native candidate test requires the complete existing currency package']
        if not dll and not config_path and not purses:
            # Legacy profiles are unaffected, but the new reviewed ESP alone
            # cannot be allowed to masquerade as a pre-native installation.
            if not esp or not Path(receipt_path).is_file():
                return []
            receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8-sig'))
            expected = receipt['winningFiles'][PLUGIN]
            if (not isinstance(expected, str) or len(expected) != 64
                    or any(c not in '0123456789abcdefABCDEF' for c in expected)):
                raise ValueError('invalid reviewed currency companion hash')
            if hashlib.sha256(esp.read_bytes()).hexdigest().lower() != expected.lower():
                return []
        if not dll or not config_path or not esp or not purses:
            return ['native currency package is incomplete; DLL, configuration, integration ESP and regional purse ESP must be paired']
        active = (Path(instance) / 'profiles' / profile / 'plugins.txt').read_text(encoding='utf-8-sig')
        active_plugins = [row.strip()[1:].casefold() for row in active.splitlines()
                          if row.strip().startswith('*')]
        if any(name.casefold() not in active_plugins for name in (PLUGIN, PURSES)):
            return ['native currency integration and regional purse ESPs must both be active']
        if active_plugins.index(PURSES.casefold()) < active_plugins.index(PLUGIN.casefold()):
            return ['regional purse ESP must load after its currency integration master']
        # This is the trusted repository release receipt, never a receipt
        # supplied by a mod folder. Fail closed if it is missing or malformed.
        receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8-sig'))
        if receipt['schemaVersion'] != 1 or receipt['version'] != '0.4.0':
            raise ValueError('unsupported reviewed currency release receipt')
        test_dll = reviewed_test_dll(test_native_build, instance, profile, receipt) if test_native_build else None
        for relative, winner in ((DLL, dll), (CONFIG, config_path), (PLUGIN, esp), (PURSES, purses)):
            expected = test_dll if relative == DLL and test_dll else receipt['winningFiles'][relative]
            if (not isinstance(expected, str) or len(expected) != 64
                    or any(c not in '0123456789abcdefABCDEF' for c in expected)):
                raise ValueError('invalid reviewed currency winner hash')
            if hashlib.sha256(winner.read_bytes()).hexdigest().lower() != expected.lower():
                raise ValueError('winning currency file differs from reviewed release: ' + relative)
        if save_path is None:
            return []  # Menu-only launch, not permission to load an old save.
        save = Path(save_path)
        if save.suffix.lower() != '.ess' or not save.is_file():
            return ['currency gate requires an existing, explicitly resolved .ess file']
        cosave = save.with_suffix('.skse')
        if cosave.stat().st_size > MAX_COSAVE:
            return ['currency co-save exceeds inspection limit']
        config = json.loads(config_path.read_text(encoding='utf-8-sig'))
        read_checkpoint(cosave.read_bytes(), ledger_fingerprint(config))
        return []
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        return [f'currency save admission refused: {error}. Verify bridge initialization and '
                'package/save compatibility before retrying; a fresh character must also produce '
                'a valid checkpoint. Do not clean or delete save data.']


def run(fails, warns, *, instance, game_data):
    fails.extend(check_save(instance, game_data, None))
    try:
        if winning_file(instance, game_data, DLL):
            warns.append('Native currency is fresh-character/exact-v2-save only. General preflight '
                         'does not approve loading an old save; launch_verify checks the selected co-save.')
    except OSError as error:
        fails.append('currency package presence could not be verified: ' + str(error))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', type=Path, required=True)
    parser.add_argument('--game-data', type=Path, required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--save', type=Path)
    parser.add_argument('--test-native-build', type=Path,
                        help='Source-bound candidate build; dedicated isolated Load262 profiles only')
    args = parser.parse_args(argv)
    # Profile is a single instance-relative name, never an arbitrary path.
    if (args.profile in ('.', '..') or not args.profile.strip()
            or any(char in args.profile for char in '/\\:')):
        parser.error('--profile must be a single profile name')
    blockers = check_save(args.instance, args.game_data, args.save, args.profile,
                          test_native_build=args.test_native_build)
    print(json.dumps({
        'verdict': 'REFUSED' if blockers else 'CURRENCY-ADMITTED',
        'save': str(args.save) if args.save else None,
        'blockers': blockers,
        'scope': ('Currency package/checkpoint only; not save health or gameplay '
                  'certification. Without --save, no saved game is admitted.'),
    }, indent=2))
    return 1 if blockers else 0


if __name__ == '__main__':
    raise SystemExit(main())
