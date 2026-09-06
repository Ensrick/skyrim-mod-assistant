"""Read-only launch admission for the native currency ledger; never edits saves.

SKSE wrapper layout: pinned skse64 Serialization.cpp Header/PluginHeader/
ChunkHeader. Currency payload: SaveMarkerPolicy.h ECMK v2. Passing proves a
matching checkpoint, not gameplay correctness or complete save health.
"""
import hashlib
import json
import struct
from pathlib import Path

DLL = 'SKSE/Plugins/EnsrickCurrencyDenominations.dll'
CONFIG = 'SKSE/Plugins/EnsrickCurrencyDenominations.json'
PLUGIN = 'Ensrick Currency Integration Patch.esp'
RECEIPT = Path(__file__).resolve().parents[1] / 'records/source-builds/currency-integration-0.3.0.json'
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
    """Byte-identical to Bridge::ComputeLedgerFingerprint, including JSON order."""
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

    string('EnsrickCurrencyLedgerV1')
    form(config['accounting']['backendForm'])
    integer(len(config['families']))
    for family in config['families']:
        string(family['id'])
        integer(int(family['enabled']))
        integer(int(family['fallback']))
        integer(len(family['denominations']))
        for denomination in family['denominations']:
            integer(denomination['value'])
            form(denomination['form'])
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
        raise ValueError('save predates the native currency ledger (no v2 checkpoint)')
    return checkpoint


def check_save(instance, game_data, save_path, profile='Default', *, receipt_path=RECEIPT):
    """Return launch blockers only when the native package is reachable."""
    try:
        dll = winning_file(instance, game_data, DLL, profile)
        config_path = winning_file(instance, game_data, CONFIG, profile)
        esp = winning_file(instance, game_data, PLUGIN, profile)
        if not dll and not config_path:
            # Legacy profiles are unaffected, but the new reviewed ESP alone
            # cannot be allowed to masquerade as a pre-native installation.
            if not esp or not Path(receipt_path).is_file():
                return []
            receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8-sig'))
            expected = receipt['winningFiles'][PLUGIN]
            if hashlib.sha256(esp.read_bytes()).hexdigest().lower() != expected.lower():
                return []
        if not dll or not config_path or not esp:
            return ['native currency package is incomplete; DLL, configuration and companion ESP must be paired']
        active = (Path(instance) / 'profiles' / profile / 'plugins.txt').read_text(encoding='utf-8-sig')
        if PLUGIN.casefold() not in {row.strip()[1:].casefold() for row in active.splitlines()
                                    if row.strip().startswith('*')}:
            return ['native currency companion ESP is not active']
        # This is the trusted repository release receipt, never a receipt
        # supplied by a mod folder. Fail closed if it is missing or malformed.
        receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8-sig'))
        if receipt['schemaVersion'] != 1 or receipt['version'] != '0.3.0':
            raise ValueError('unsupported reviewed currency release receipt')
        for relative, winner in ((DLL, dll), (CONFIG, config_path), (PLUGIN, esp)):
            expected = receipt['winningFiles'][relative]
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
        return [f'currency save admission refused: {error}. Start a fresh character with this package, '
                'or restore the old matching package to use an old save; do not clean or delete save data.']


def run(fails, warns, *, instance, game_data):
    fails.extend(check_save(instance, game_data, None))
    try:
        if winning_file(instance, game_data, DLL):
            warns.append('Native currency is fresh-character/exact-v2-save only. General preflight '
                         'does not approve loading an old save; launch_verify checks the selected co-save.')
    except OSError as error:
        fails.append('currency package presence could not be verified: ' + str(error))
