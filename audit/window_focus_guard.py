"""Read-only gate for the paired foreground cursor owner and DirectInput config."""
import configparser
import hashlib
import json
from pathlib import Path

MOD = 'Ensrick - Window Focus Guard'


def check(instance, repo, game_data, profile='Default'):
    instance, repo, game_data = Path(instance), Path(repo), Path(game_data)
    lines = (instance / 'profiles' / profile / 'modlist.txt').read_text(encoding='utf-8-sig').splitlines()
    active = [line[1:] for line in lines if line.startswith('+')]
    if not (instance / 'mods' / MOD).exists():
        return []  # Profile has not adopted this paired implementation.
    if MOD not in active:
        return ['WindowFocusGuard installed but disabled; review paired cursor ownership before launch']
    roots = [instance / 'overwrite'] + [instance / 'mods' / name for name in active] + [game_data]

    def winner(relative):
        return next((root / relative for root in roots if (root / relative).is_file()), None)

    problems = []
    dll = winner('SKSE/Plugins/WindowFocusGuard.dll')
    receipt = json.loads((repo / 'records/source-builds/window-focus-guard-0.1.0.json').read_text(encoding='utf-8'))
    if dll is None or hashlib.sha256(dll.read_bytes()).hexdigest().lower() != receipt['dllSha256'].lower():
        problems.append('WindowFocusGuard winning DLL missing or differs from reviewed receipt')

    def merged(paths):
        result = configparser.ConfigParser(strict=True, interpolation=None)
        for path in paths:
            file = winner('SKSE/Plugins/' + path)
            if file:
                result.read_string(file.read_text(encoding='utf-8-sig'))
        return result

    display = merged(['SSEDisplayTweaks.ini', 'SSEDisplayTweaks_Custom.ini'])
    if display.getboolean('Window', 'LockCursor', fallback=True):
        problems.append('Two cursor owners: Display Tweaks LockCursor must be false with WindowFocusGuard')
    media = merged(['MediaKeysFix.ini'])
    if winner('SKSE/Plugins/MediaKeysFix.dll') is None:
        problems.append('Media Keys Fix DLL missing; INI alone does not enable desktop input handoff')
    for key in ('DisableWindowsKey', 'BackgroundAccess'):
        if media.getboolean('General', key, fallback=True):
            problems.append('Media Keys Fix ' + key + ' must remain false for desktop input handoff')
    return problems


def run(fails, *, instance, repo, game_data):
    try:
        fails.extend('window focus: ' + item for item in check(instance, repo, game_data))
    except (OSError, ValueError, KeyError, configparser.Error) as error:
        fails.append('window focus pairing could not be verified: ' + str(error))
