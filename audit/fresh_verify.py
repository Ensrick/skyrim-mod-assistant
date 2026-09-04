"""V2 disposable fresh-start verification through the game's real Main Menu.

This is deliberately a Python orchestrator around launch_verify, MenuPilot and
LaunchProbe.  It does not focus a window, send OS input, invoke the console, or
reuse a save.  Each run clones Default into a uniquely named profile with local
INIs/saves, launches that clone on a hidden Windows desktop, reads the selected
Main Menu entry before every Accept, and requires both LaunchProbe kNewGame and
the Skyrim Unbound -> RaceMenu ``RaceSex Menu`` open event.

  py -3 audit/fresh_verify.py --dry-run
  py -3 audit/fresh_verify.py --selftest
  py -3 audit/fresh_verify.py

V2 ends at RaceMenu readiness.  It does not claim V3 feature probes or the V4
named-save/reload round trip; MenuPilot currently has no audited save/name
primitive.  See docs/MENUPILOT.md and issue #227.
"""
import argparse
import dataclasses
import datetime
import io
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

import claim
import human_presence as HP
import launch_verify as LV
import launch_watch as W
import menupilot as MP

AUDIT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AUDIT)
PROFILES = os.path.join(LV.INSTANCE, 'profiles')
DEFAULT_PROFILE = os.path.join(PROFILES, LV.DEFAULT_PROFILE_NAME)

MAIN_MENU = 'Main Menu'
SELECTED = '_root.MenuHolder.Menu_mc.MainList.selectedEntry.text'
STATE = '_root.MenuHolder.Menu_mc.strCurrentState'
CONFIRM_TEXT = '_root.MenuHolder.Menu_mc.ConfirmPanel_mc.textField.text'
NEW_GAME = '$NEW'
NEW_GAME_CONFIRM = 'start a new game?'
RACE_MENU = 'RaceSex Menu'
INPUTS = {'Down': (208, 'Down'), 'Accept': (28, 'Accept')}
MESSAGE_BOXES = {'messagebox menu', 'messageboxmenu'}


class FreshError(RuntimeError):
    pass


class HumanAtControls(FreshError):
    pass


@dataclasses.dataclass
class FreshResult:
    identity: str
    profile_name: str
    verdict: str = 'FAIL'
    reason: str = 'not run'
    pid: int | None = None
    started: float | None = None
    profile_path: str | None = None
    launch_record: str | None = None
    confirmation: str | None = None
    selections: list = dataclasses.field(default_factory=list)
    actions: list = dataclasses.field(default_factory=list)
    evidence: list = dataclasses.field(default_factory=list)
    probe: list = dataclasses.field(default_factory=list)
    human: bool = False


def _git_short():
    try:
        return subprocess.run(['git', 'rev-parse', '--short=8', 'HEAD'], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 'nogit'


def new_identity():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f'FV-{stamp}-{_git_short()}-{secrets.token_hex(3)}'


def _replace_flag(text, key, value):
    pattern = rf'(?im)^{re.escape(key)}[ \t]*=[ \t]*(?:true|false)[ \t]*$'
    changed, n = re.subn(pattern, f'{key}={str(value).lower()}', text)
    if n != 1:
        raise FreshError(f'profile settings.ini needs exactly one {key}= flag (found {n})')
    return changed


def clone_profile(identity):
    """Copy, never edit, Default.  Saves are excluded before the copy starts."""
    profile_name = 'Codex Fresh ' + identity
    dest = os.path.join(PROFILES, profile_name)
    if os.path.exists(dest):
        raise FreshError(f'unique profile unexpectedly exists: {dest}')
    if not os.path.isfile(os.path.join(DEFAULT_PROFILE, 'settings.ini')):
        raise FreshError(f'Default profile is unavailable: {DEFAULT_PROFILE}')

    def ignore(_directory, names):
        return {name for name in names if name.lower() == 'saves'}

    shutil.copytree(DEFAULT_PROFILE, dest, ignore=ignore)
    try:
        settings_path = os.path.join(dest, 'settings.ini')
        settings = io.open(settings_path, encoding='utf-8-sig').read()
        settings = _replace_flag(settings, 'LocalSettings', True)
        settings = _replace_flag(settings, 'LocalSaves', True)
        io.open(settings_path, 'w', encoding='utf-8', newline='\n').write(settings)

        plugins_path = os.path.join(dest, 'plugins.txt')
        plugins = io.open(plugins_path, encoding='utf-8-sig', errors='replace').read()
        if not re.search(r'(?im)^\*Skyrim Unbound\.esp\s*$', plugins):
            raise FreshError('disposable profile does not have Skyrim Unbound.esp active')

        prefs_path = next((os.path.join(dest, n) for n in os.listdir(dest)
                           if n.lower() == 'skyrimprefs.ini'), None)
        if not prefs_path:
            raise FreshError('profile clone has no SkyrimPrefs.ini to mute')
        prefs = io.open(prefs_path, encoding='utf-8-sig').read()
        prefs, n = re.subn(r'(?im)^fAudioMasterVolume\s*=\s*[^\r\n]+$',
                           'fAudioMasterVolume=0.0000', prefs)
        if n != 1:
            raise FreshError(f'SkyrimPrefs.ini needs one fAudioMasterVolume key (found {n})')
        io.open(prefs_path, 'w', encoding='utf-8', newline='\n').write(prefs)
        os.makedirs(os.path.join(dest, 'saves'), exist_ok=False)
        marker = {'identity': identity, 'createdAt': datetime.datetime.now(
                  datetime.timezone.utc).isoformat(timespec='seconds'),
                  'sourceProfile': LV.DEFAULT_PROFILE_NAME, 'reusable': False}
        io.open(os.path.join(dest, '.fresh-verification.json'), 'w',
                encoding='utf-8', newline='\n').write(json.dumps(marker, indent=2) + '\n')
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return profile_name, dest


def remove_profile(path, identity):
    """Delete only the exact disposable profile this run marked as its own."""
    target = pathlib.Path(path).resolve()
    parent = pathlib.Path(PROFILES).resolve()
    marker = target / '.fresh-verification.json'
    if target.parent != parent or not target.name.startswith('Codex Fresh FV-'):
        raise FreshError(f'refusing unsafe profile cleanup target: {target}')
    try:
        stamped = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise FreshError(f'refusing unmarked profile cleanup: {e}')
    if stamped.get('identity') != identity or stamped.get('reusable') is not False:
        raise FreshError('refusing profile cleanup: identity marker does not match')
    shutil.rmtree(target)


def normalize_confirmation(text):
    return ' '.join((text or '').strip().lower().split())


def confirmation_action(state, text):
    """Pure fail-closed decision for the only observed New Game confirmation."""
    if state == 'Main':
        return 'wait'
    if state != 'MainConfirm':
        raise FreshError(f'unrecognized Main Menu state after New Game: {state!r}')
    if normalize_confirmation(text) != NEW_GAME_CONFIRM:
        raise FreshError(f'refusing unknown confirmation: {text!r}')
    return 'accept'


def _menu_name(event):
    m = re.search(r'name="([^"]*)"', event.get('rest', ''))
    return m.group(1) if m else ''


def probe_status(events, elapsed, budget):
    """Pure V2 lifecycle decision used by the real loop and offline tests."""
    events = events or []
    new = next((e for e in events if e.get('event') == 'kNewGame'), None)
    for event in events:
        if event.get('event') == 'MENU_OPEN' and _menu_name(event).lower() in MESSAGE_BOXES:
            return 'FAIL', 'an unrecognized MessageBox opened during fresh start'
    if new:
        ready = next((e for e in events if e.get('event') == 'MENU_OPEN'
                      and _menu_name(e) == RACE_MENU
                      and e.get('ms', -1) >= new.get('ms', 0)), None)
        if ready:
            return 'PASS', 'LaunchProbe kNewGame followed by RaceSex Menu'
    if elapsed > budget:
        return 'FAIL', ('no RaceSex Menu after LaunchProbe kNewGame' if new else
                        'LaunchProbe kNewGame never arrived')
    return None, 'waiting'


def _result_line(text, op):
    lines = [line for line in text.splitlines()
             if ' RESULT ' in (' ' + line + ' ') and f'op="{op}"' in line]
    if not lines:
        raise FreshError(f'MenuPilot returned no RESULT for {op}: {text[-400:]}')
    line = lines[-1]
    if ' ok=1 ' not in (' ' + line + ' '):
        raise FreshError(f'MenuPilot {op} failed: {line}')
    return line


class Pilot:
    def __init__(self, result, timeout=10.0):
        self.run = result
        self.timeout = timeout

    def one(self, command):
        batch = MP.send_batch([command], self.timeout, require_ready=True)
        self.run.actions.append({'command': command, 'token': batch.token,
                                 'code': batch.code, 'claimed': batch.claimed,
                                 'cleanup': batch.cleanup})
        if batch.code:
            raise FreshError(f'MenuPilot batch failed ({batch.code}): '
                             f'{batch.cleanup or batch.text[-400:]}')
        return batch.text

    def get(self, path):
        line = _result_line(self.one({'op': 'gfx.get', 'menu': MAIN_MENU,
                                      'path': path}), 'gfx.get')
        m = re.search(r' value="([^"]*)"\s*$', line)
        if not m:
            raise FreshError(f'could not parse MenuPilot value: {line}')
        return m.group(1)

    def tap(self, name):
        code, event = INPUTS[name]
        _result_line(self.one({'op': 'input.tap', 'event': event, 'code': code,
                               'device': 'keyboard', 'hold_ms': 80}), 'input.tap')


def guard_no_human(result):
    verdict = HP.judge(since=result.started)
    if verdict['human']:
        result.human = True
        result.evidence.append(HP.describe(verdict))
        HP.log_refusal(verdict, f'fresh_verify {result.identity}')
        raise HumanAtControls(HP.describe(verdict))


def navigate_new_game(pilot, result, limit=12):
    """Move one step at a time, observing the selection after every step."""
    seen = []
    for _ in range(limit):
        selected = pilot.get(SELECTED)
        result.selections.append(selected)
        if selected == NEW_GAME:
            return
        if not selected or not selected.startswith('$'):
            raise FreshError(f'unrecognized Main Menu selection: {selected!r}')
        if selected in seen:
            raise FreshError(f'Main Menu cycled without finding {NEW_GAME}: {seen + [selected]}')
        seen.append(selected)
        guard_no_human(result)
        pilot.tap('Down')
    raise FreshError(f'{NEW_GAME} not found within {limit} observed selections')


def accept_new_game(pilot, result, confirm_budget=15.0):
    # The read is intentionally adjacent to Accept; a previous navigation read
    # is not authority because the selection can change after a sub-screen.
    selected = pilot.get(SELECTED)
    result.selections.append(selected)
    if selected != NEW_GAME:
        raise FreshError(f'refusing Accept: current selection is {selected!r}, not {NEW_GAME}')
    guard_no_human(result)
    pilot.tap('Accept')

    deadline = time.time() + confirm_budget
    accepted_confirm = False
    while time.time() < deadline:
        events = W.probe_events(since=result.started) or []
        early, reason = probe_status(events, 0, confirm_budget + 1)
        if early == 'FAIL':
            raise FreshError(reason)
        if any(e['event'] == 'kNewGame' for e in events):
            return
        if not _pid_alive(result.pid):
            raise FreshError('game exited before LaunchProbe kNewGame')
        try:
            state = pilot.get(STATE)
        except FreshError:
            time.sleep(0.25)  # main menu may be closing; probe remains authoritative
            continue
        text = pilot.get(CONFIRM_TEXT) if state == 'MainConfirm' else ''
        action = confirmation_action(state, text)
        if action == 'accept':
            if accepted_confirm:
                raise FreshError('New Game confirmation remained open after Accept')
            # Re-read the exact text immediately before the second Accept.
            text2 = pilot.get(CONFIRM_TEXT)
            if normalize_confirmation(text2) != NEW_GAME_CONFIRM:
                raise FreshError(f'confirmation changed before Accept: {text2!r}')
            result.confirmation = text2
            guard_no_human(result)
            pilot.tap('Accept')
            accepted_confirm = True
        time.sleep(0.25)
    raise FreshError('LaunchProbe kNewGame did not arrive after New Game acceptance')


def wait_ready(result, budget):
    deadline = time.time() + budget
    while time.time() < deadline:
        result.probe = W.probe_events(since=result.started) or []
        verdict, reason = probe_status(result.probe, time.time() - result.started, budget)
        if verdict:
            if verdict == 'PASS':
                return reason
            raise FreshError(reason)
        if not _pid_alive(result.pid):
            raise FreshError('game exited before fresh-start readiness')
        time.sleep(0.5)
    result.probe = W.probe_events(since=result.started) or []
    _verdict, reason = probe_status(result.probe, budget + 0.1, budget)
    raise FreshError(reason)


def _pid_alive(pid):
    if not pid:
        return False
    p = W.Proc(pid)
    try:
        return p.alive()
    finally:
        p.close()


def _wait_pid_exit(pid, timeout=10.0):
    deadline = time.time() + timeout
    while _pid_alive(pid) and time.time() < deadline:
        time.sleep(0.1)
    return not _pid_alive(pid)


def _running(name):
    return LV._running(name)


def ensure_idle_and_retire_stale(result):
    blockers = []
    if W.find_process():
        blockers.append('SkyrimSE.exe is already running')
    for exe in ('MO2Headless.exe', 'ModOrganizer.exe'):
        if _running(exe):
            blockers.append(f'{exe} is already running')
    if blockers:
        raise FreshError('; '.join(blockers) + ' - refusing to touch commands or launch')
    if os.path.exists(MP.COMMANDS):
        try:
            pending = pathlib.Path(MP.COMMANDS).read_bytes()
        except FileNotFoundError:
            return
        moved = MP.quarantine_pending(f'pre-{result.identity}', expected=pending)
        if not moved:
            raise FreshError('could not quarantine stale commands.jsonl')
        result.evidence.append(f'stale pending commands quarantined: {moved}')


def launch_cfg(profile_name, owner, args):
    return {
        'menu_budget': args.menu_budget,
        'save_budget': 180.0,
        'spawn_budget': args.spawn_budget,
        'settle_ms': 1500.0,
        'interval': 1.0,
        'hang_seconds': 45.0,
        'save': None,
        'dry_run': False,
        'leave_running': True,
        'no_autoload': True,
        'steam_chain': False,
        'claim_owner': owner,
        'keep_claim': True,
        'allow_unverified': False,
        'attach_pid': None,
        'force_kill': None,
        'profile_name': profile_name,
        'no_ini_sync': True,
        'hidden_desktop': True,
        'refuse_existing': True,
        'no_steam_cycle': True,
    }


def write_record(result):
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    path = os.path.join(REPO, 'records', f'fresh-verify-{stamp}-{result.identity}.md')
    lines = [f'# Fresh-character verification - {result.verdict}', '',
             f'- issue: #227', f'- identity: `{result.identity}`',
             f'- disposable profile: `{result.profile_name}`',
             f'- verdict: **{result.verdict}**', f'- reason: {result.reason}',
             f'- pid: {result.pid}', f'- hidden desktop: yes',
             f'- reused save: no (LocalSaves=true; source saves excluded)',
             f'- launch record: {result.launch_record or "(none)"}', '']
    if result.confirmation is not None:
        lines += [f'- accepted confirmation: `{result.confirmation}`', '']
    if result.selections:
        lines += ['## Observed selection path', '',
                  ' -> '.join(f'`{x}`' for x in result.selections), '']
    if result.actions:
        lines += ['## MenuPilot batches', '',
                  '| # | op | observed target | claimed | code | token |',
                  '|---:|---|---|---|---:|---|']
        for number, action in enumerate(result.actions, 1):
            command = action['command']
            target = command.get('path') or command.get('event') or ''
            lines.append(f'| {number} | `{command.get("op", "")}` | `{target}` | '
                         f'{action["claimed"]} | {action["code"]} | '
                         f'`{action["token"]}` |')
        lines.append('')
    if result.evidence:
        lines += ['## Evidence', ''] + [f'- {x}' for x in result.evidence] + ['']
    if result.probe:
        lines += ['## LaunchProbe timeline', '', '```']
        lines += [f'{e["ms"]:>8}ms  {e["event"]} {e["rest"]}'.rstrip()
                  for e in result.probe[:100]]
        lines += ['```', '']
    lines += ['## Scope', '',
              'This is V2 only. V3 feature probes and V4 named save/reload are '
              'not certified by this record.', '']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    return path


def selftest():
    bad = 0

    def ok(condition, label):
        nonlocal bad
        bad += not condition
        print(f'  {"ok  " if condition else "FAIL"} {label}')

    # Read-driven navigation: one Down, then exact $NEW; no blind fixed count.
    class FakePilot:
        def __init__(self):
            self.values = iter(['$QUIT', '$NEW'])
            self.taps = []
        def get(self, _path):
            return next(self.values)
        def tap(self, name):
            self.taps.append(name)

    fake_result = FreshResult('test', 'test', started=4e9)
    old_judge = HP.judge
    HP.judge = lambda **_kw: {'human': False}
    try:
        fake = FakePilot()
        navigate_new_game(fake, fake_result)
        ok(fake_result.selections == ['$QUIT', '$NEW'] and fake.taps == ['Down'],
           'menu navigation observes every selection before moving')
    finally:
        HP.judge = old_judge

    try:
        confirmation_action('MainConfirm', 'Delete every save?')
        ok(False, 'unknown confirmation refused')
    except FreshError:
        ok(True, 'unknown confirmation refused')
    ok(confirmation_action('MainConfirm', ' Start a New Game?  ') == 'accept',
       'documented New Game confirmation accepted')
    ok(probe_status([], 31, 30)[0] == 'FAIL', 'timeout without kNewGame fails')
    only_new = [{'event': 'kNewGame', 'ms': 100, 'rest': ''}]
    ok(probe_status(only_new, 31, 30)[0] == 'FAIL', 'kNewGame without RaceMenu fails')
    success = only_new + [{'event': 'MENU_OPEN', 'ms': 120,
                           'rest': 'name="RaceSex Menu"'}]
    ok(probe_status(success, 1, 30)[0] == 'PASS',
       'kNewGame followed by RaceSex Menu passes')
    popup = only_new + [{'event': 'MENU_OPEN', 'ms': 110,
                         'rest': 'name="MessageBox Menu"'}]
    ok(probe_status(popup, 1, 30)[0] == 'FAIL', 'unexpected MessageBox fails')

    fx = os.path.join(AUDIT, 'fixtures')
    old_hp_paths = HP.PROBE_LOG, HP.PILOT_LOG
    old_hp_log = HP.log_refusal
    HP.PROBE_LOG = os.path.join(fx, 'launchprobe-20260901-234109-human.log')
    HP.PILOT_LOG = os.path.join(fx, 'menupilot-20260901-234109.log')
    HP.log_refusal = lambda *_args, **_kwargs: None
    guarded = FreshResult('human-test', 'human-test', started=None)
    try:
        guard_no_human(guarded)
        ok(False, 'human-presence fixture refuses destructive cleanup')
    except HumanAtControls:
        ok(guarded.human, 'human-presence fixture refuses destructive cleanup')
    finally:
        HP.PROBE_LOG, HP.PILOT_LOG = old_hp_paths
        HP.log_refusal = old_hp_log

    # Profile isolation and exact-target cleanup, entirely under a temp root.
    global PROFILES, DEFAULT_PROFILE
    old_profiles = PROFILES, DEFAULT_PROFILE
    with tempfile.TemporaryDirectory(prefix='fresh-profile-selftest-') as temp:
        PROFILES = temp
        DEFAULT_PROFILE = os.path.join(temp, LV.DEFAULT_PROFILE_NAME)
        os.makedirs(os.path.join(DEFAULT_PROFILE, 'saves'))
        io.open(os.path.join(DEFAULT_PROFILE, 'settings.ini'), 'w').write(
            'LocalSettings=false\nLocalSaves=false\n')
        io.open(os.path.join(DEFAULT_PROFILE, 'plugins.txt'), 'w').write(
            '*Skyrim.esm\n*Skyrim Unbound.esp\n')
        io.open(os.path.join(DEFAULT_PROFILE, 'SkyrimPrefs.ini'), 'w').write(
            'fAudioMasterVolume=1.0000\n')
        io.open(os.path.join(DEFAULT_PROFILE, 'saves', 'old.ess'), 'w').write('old')
        name, path = clone_profile('FV-selftest')
        cloned_settings = io.open(os.path.join(path, 'settings.ini')).read().lower()
        ok(name.startswith('Codex Fresh FV-')
           and re.search(r'(?m)^localsettings=true$', cloned_settings)
           and re.search(r'(?m)^localsaves=true$', cloned_settings)
           and not os.path.exists(os.path.join(path, 'saves', 'old.ess')),
           'unique profile owns INIs/saves and excludes every source save')
        remove_profile(path, 'FV-selftest')
        ok(not os.path.exists(path) and os.path.exists(DEFAULT_PROFILE),
           'cleanup removes only its marked disposable profile')
    PROFILES, DEFAULT_PROFILE = old_profiles

    # Exercise the real driver timeout cleanup against isolated paths.
    old = MP.PILOT, MP.LOG, MP.COMMANDS
    with tempfile.TemporaryDirectory(prefix='fresh-verify-selftest-') as temp:
        MP.PILOT = temp
        MP.LOG = os.path.join(temp, 'menupilot.log')
        MP.COMMANDS = os.path.join(temp, 'commands.jsonl')
        timed = MP.send_batch([{'op': 'ping'}], timeout=0.01)
        archived = [n for n in os.listdir(temp) if 'timeout' in n]
        ok(timed.code == 2 and not os.path.exists(MP.COMMANDS) and archived,
           'unclaimed timeout leaves no pending commands.jsonl')
        # A pre-existing stale command is quarantined, never executed/deleted.
        io.open(MP.COMMANDS, 'w', encoding='utf-8').write('{"op":"wait"}\n')
        moved = MP.quarantine_pending('selftest-stale')
        ok(moved and os.path.exists(moved) and not os.path.exists(MP.COMMANDS),
           'stale command is quarantined for forensic review')
        io.open(MP.COMMANDS, 'w', encoding='utf-8').write('foreign\n')
        refused = MP.send_batch([{'op': 'ping'}], timeout=0.01)
        ok(refused.code == 2 and pathlib.Path(MP.COMMANDS).read_text() == 'foreign\n',
           'generic driver never overwrites a pre-existing command')
    MP.PILOT, MP.LOG, MP.COMMANDS = old

    print(f'\n{"all" if not bad else bad} fresh-verification selftest '
          f'{"cases pass" if not bad else "FAILURES"}')
    return 1 if bad else 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--keep-profile', action='store_true',
                        help='retain the disposable profile after the game exits')
    parser.add_argument('--menu-budget', type=float, default=60.0)
    parser.add_argument('--spawn-budget', type=float, default=300.0)
    parser.add_argument('--fresh-budget', type=float, default=180.0)
    parser.add_argument('--pilot-timeout', type=float, default=10.0)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.selftest:
        return selftest()
    identity = new_identity()
    profile_name = 'Codex Fresh ' + identity
    result = FreshResult(identity, profile_name)
    owner = 'fresh-verify/' + identity
    if args.dry_run:
        print(json.dumps({
            'issue': 227, 'stage': 'V2', 'identity': identity,
            'sourceProfile': LV.DEFAULT_PROFILE_NAME,
            'disposableProfile': profile_name,
            'localSettings': True, 'localSaves': True, 'copiesExistingSaves': False,
            'requiresActivePlugin': 'Skyrim Unbound.esp',
            'hiddenDesktop': True, 'osInput': False, 'autoload': False,
            'steamCycle': False,
            'menuSelectionRequiredBeforeAccept': NEW_GAME,
            'allowedConfirmation': 'Start a New Game?',
            'requiredProbeEvents': ['kNewGame', 'MENU_OPEN RaceSex Menu'],
            'pendingCommands': os.path.exists(MP.COMMANDS),
            'launchesGame': False,
        }, indent=2))
        return 0

    profile_path = None
    record = None
    claim_held = False
    try:
        # The Default-only preflight is still the source build gate.  Profile
        # cloning happens only after it succeeds and under the instance claim.
        pre = subprocess.run([sys.executable, os.path.join(AUDIT, 'preflight.py')],
                             capture_output=True, text=True, timeout=1800)
        print((pre.stdout or '').rstrip())
        if pre.returncode:
            raise FreshError('preflight failed; no profile cloned and no launch attempted')

        claim.acquire(owner, f'#227 V2 disposable fresh start {identity}', ttl=30,
                      pid_bound=True)
        claim_held = True
        ensure_idle_and_retire_stale(result)
        result.profile_name, profile_path = clone_profile(identity)
        result.profile_path = profile_path
        result.evidence.append('Default copied read-only; saves directory excluded; '
                               'Skyrim Unbound.esp active in cloned plugins.txt')
        cfg = launch_cfg(result.profile_name, owner, args)
        print(f'launching {identity} on hidden desktop with profile {result.profile_name}')
        boot = LV.verify(cfg)
        result.pid, result.started = boot.pid, boot.t0
        result.launch_record = LV.write_record(boot, cfg)
        if boot.verdict != 'MENU-ONLY':
            raise FreshError(f'V1 launch gate did not reach a real main menu: '
                             f'{boot.verdict} - {boot.reason}')
        guard_no_human(result)
        pilot = Pilot(result, args.pilot_timeout)
        navigate_new_game(pilot, result)
        accept_new_game(pilot, result)
        result.reason = wait_ready(result, args.fresh_budget)
        result.verdict = 'PASS'
    except HumanAtControls as e:
        result.verdict, result.reason, result.human = 'REFUSED', str(e), True
    except (FreshError, claim.ClaimHeld, OSError, subprocess.SubprocessError) as e:
        result.verdict, result.reason = 'FAIL', str(e)
    except Exception as e:
        result.verdict = 'ERROR'
        result.reason = f'{type(e).__name__}: {e}'
    finally:
        # send_batch retires its own unclaimed bytes.  A leftover here is
        # quarantined only when no game can race us for it.
        alive = _pid_alive(result.pid)
        if alive:
            if result.human:
                result.evidence.append('game left running: human-at-controls guard')
            else:
                killed = LV.kill(result.pid, f'#227 V2 run finished: {result.verdict}',
                                 cfg={}, r=None, since=result.started)
                alive = not _wait_pid_exit(result.pid) if killed else True
                if not killed or alive:
                    result.human = True
                    result.verdict = 'REFUSED'
                    result.reason = 'safe cleanup refused; game left running'
        if os.path.exists(MP.COMMANDS):
            if not alive:
                try:
                    pending = pathlib.Path(MP.COMMANDS).read_bytes()
                except FileNotFoundError:
                    pending = None
                if pending is not None:
                    moved = MP.quarantine_pending(f'post-{identity}', expected=pending)
                    if moved:
                        result.evidence.append(f'post-run pending command quarantined: {moved}')
                    else:
                        result.verdict = 'REFUSED'
                        result.reason = 'pending command changed during cleanup; not touched'
            else:
                result.evidence.append('pending command not touched while game is live')
                result.verdict = 'REFUSED'
        if profile_path and os.path.exists(profile_path) and not args.keep_profile and not alive:
            try:
                remove_profile(profile_path, identity)
                result.evidence.append('disposable profile removed after process exit')
            except FreshError as e:
                result.evidence.append(str(e))
                result.verdict, result.reason = 'FAIL', str(e)
        if claim_held:
            claim.release(owner)
        record = write_record(result)

    print(f'VERDICT: {result.verdict} - {result.reason}')
    print(f'identity: {result.identity}')
    print(f'record: {record}')
    if result.human:
        return HP.HUMAN_AT_CONTROLS
    return 0 if result.verdict == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
