"""Is a human at the controls of the running game? Decide from the probe logs.

Born 2026-09-01 23:45 (#164): a harness kill ended a session the user had
started playing in, unsaved. Every rule held - the process was the harness's
own - and the user still lost the session. So before ANY kill, and before any
profile mutation under a live game, this asks the game's own menu events
whether a person has been driving.

The rule (issue #164): after the harness's AUTOLOAD_SETTLED event, any
MENU_OPEN of a gameplay menu (TweenMenu, InventoryMenu, MagicMenu, MapMenu,
Journal Menu, Sleep/Wait Menu, Dialogue Menu, Console, plus the container,
barter, favorites, stats, crafting, lockpicking, book and training menus) that
no MenuPilot COMMAND explains within 2 s means a human is present.

  py -3 audit/human_presence.py                  # judge the live logs
  py -3 audit/human_presence.py --selftest       # the two 2026-09-01 fixtures
  py -3 audit/human_presence.py --probe X --pilot Y [--since EPOCH]

Exit 0 = no human detected, HUMAN_AT_CONTROLS (88) = detected. Callers:
launch_verify.kill (refuses, leaves the game running, exits 88 unless
--force-kill <reason>), install_mod install/sort under a live SkyrimSE.exe.

Both logs are written by SKSE plugins with wall-clock stamps
`[YYYY-MM-DD HH:MM:SS.mmm] +<ms> EVENT key="value"`; LaunchProbe truncates
its log on every launch, so `since` (the launch epoch) only guards against a
stale file from an earlier session.
"""
import datetime, io, json, os, re, sys

HUMAN_AT_CONTROLS = 88
DOCS = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                    'Skyrim Special Edition')
PROBE_LOG = os.environ.get('LAUNCH_PROBE_LOG', os.path.join(DOCS, 'SKSE', 'LaunchProbe.log'))
PILOT_LOG = os.environ.get('MENU_PILOT_LOG',
                           os.path.join(DOCS, 'SKSE', 'MenuPilot', 'menupilot.log'))
MATCH_WINDOW_S = 2.0

# The menus a person opens. Names are the game's own (RE::*Menu::MENU_NAME),
# as LaunchProbe logs them in MENU_OPEN name="...".
GAMEPLAY_MENUS = {
    'tweenmenu', 'inventorymenu', 'magicmenu', 'mapmenu', 'journal menu',
    'sleep/wait menu', 'dialogue menu', 'console',
    'containermenu', 'bartermenu', 'favoritesmenu', 'statsmenu', 'crafting menu',
    'lockpicking menu', 'book menu', 'training menu', 'giftmenu',
}
# Pilot ops that can open a menu without naming it (a key tap, a Scaleform call)
INDIRECT_OPS = {'input.tap', 'gfx.invoke', 'gfx.set', 'menu.msg'}

LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \+(\d+)ms (\S+)(.*)$')


def _wall(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f').timestamp()


def parse(path):
    """[{'t': epoch, 'ms': int, 'event': str, 'rest': str}] for a probe-style log."""
    out = []
    if not path or not os.path.exists(path):
        return out
    for line in io.open(path, encoding='utf-8', errors='replace'):
        m = LINE.match(line.rstrip('\r\n'))
        if not m:
            continue
        try:
            t = _wall(m.group(1))
        except ValueError:
            continue
        out.append({'t': t, 'ms': int(m.group(2)), 'event': m.group(3),
                    'rest': m.group(4).strip()})
    return out


def _name(rest):
    m = re.search(r'name="([^"]*)"', rest)
    return m.group(1) if m else ''


def pilot_commands(path):
    """MenuPilot COMMAND lines: [{'t', 'op', 'raw'}]."""
    cmds = []
    for ev in parse(path):
        if ev['event'] != 'COMMAND':
            continue
        op = re.search(r'op="([^"]*)"', ev['rest'])
        cmds.append({'t': ev['t'], 'op': op.group(1) if op else '',
                     'raw': ev['rest'].lower()})
    return cmds


def _piloted(menu, t, cmds):
    """A MenuPilot command that explains a MENU_OPEN of `menu` at time t:
    issued within MATCH_WINDOW_S before it, naming the menu or of an op that
    can open one indirectly."""
    key = menu.lower()
    for c in cmds:
        if t - MATCH_WINDOW_S <= c['t'] <= t + 0.25:
            if key in c['raw'] or c['op'] in INDIRECT_OPS:
                return c
    return None


def judge(probe_log=None, pilot_log=None, since=None):
    """Decide. Returns a dict; ['human'] is the verdict. Paths default to the
    module globals AT CALL TIME so a test (or a caller) can point them at a
    fixture after import."""
    probe_log = probe_log or PROBE_LOG
    pilot_log = pilot_log or PILOT_LOG
    events = parse(probe_log)
    result = {'human': False, 'probe_log': probe_log, 'pilot_log': pilot_log,
              'boundary': None, 'boundary_event': None, 'events_after': 0,
              'unmatched': [], 'piloted': [], 'note': ''}
    if not events:
        result['note'] = 'no probe events - cannot judge, assume nobody'
        return result
    if since is not None and events[-1]['t'] < since - 5:
        result['note'] = 'probe log predates this session - stale, assume nobody'
        return result
    # The boundary: the harness's own AUTOLOAD_SETTLED; without autoload (a
    # menu-only run) the real main menu is the earliest point a person could
    # start driving, so it is the boundary instead.
    boundary = None
    for ev in events:
        if ev['event'] == 'AUTOLOAD_SETTLED':
            boundary = ev
    if boundary is None:
        for ev in events:
            if ev['event'] == 'MAIN_MENU_OPEN':
                boundary = ev
                break
    if boundary is None:
        result['note'] = 'no AUTOLOAD_SETTLED or MAIN_MENU_OPEN yet - still loading, nobody'
        return result
    result['boundary'] = datetime.datetime.fromtimestamp(boundary['t']).strftime('%H:%M:%S.%f')[:-3]
    result['boundary_event'] = boundary['event']
    cmds = pilot_commands(pilot_log)
    for ev in events:
        if ev['t'] <= boundary['t'] or ev['event'] != 'MENU_OPEN':
            continue
        result['events_after'] += 1
        menu = _name(ev['rest'])
        if menu.lower() not in GAMEPLAY_MENUS:
            continue
        stamp = datetime.datetime.fromtimestamp(ev['t']).strftime('%H:%M:%S.%f')[:-3]
        c = _piloted(menu, ev['t'], cmds)
        if c:
            result['piloted'].append({'menu': menu, 'at': stamp, 'op': c['op']})
        else:
            result['unmatched'].append({'menu': menu, 'at': stamp})
    result['human'] = bool(result['unmatched'])
    return result


def describe(r):
    if r['human']:
        u = r['unmatched']
        return (f'HUMAN_AT_CONTROLS: {len(u)} gameplay menu(s) opened after '
                f'{r["boundary_event"]} {r["boundary"]} with no MenuPilot command within '
                f'{MATCH_WINDOW_S:.0f}s - first {u[0]["menu"]} at {u[0]["at"]}'
                + (f'; {len(r["piloted"])} piloted' if r['piloted'] else ''))
    if r['note']:
        return 'nobody detected (' + r['note'] + ')'
    return (f'nobody detected: {r["events_after"]} menu event(s) after '
            f'{r["boundary_event"]} {r["boundary"]}, {len(r["piloted"])} piloted, 0 unmatched')


def log_refusal(r, who, path=None):
    """Append a HUMAN_AT_CONTROLS line to records/human-at-controls.jsonl."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = (path or os.environ.get('HUMAN_AT_CONTROLS_LOG')
            or os.path.join(repo, 'records', 'human-at-controls.jsonl'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps({'at': datetime.datetime.now().isoformat(timespec='seconds'),
                             'by': who, 'verdict': 'HUMAN_AT_CONTROLS',
                             'summary': describe(r), 'unmatched': r['unmatched'],
                             'piloted': r['piloted']}) + '\n')


def selftest():
    fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
    bad = 0

    def ok(cond, label):
        nonlocal bad
        bad += not cond
        print(f'  {"ok  " if cond else "FAIL"} {label}')

    # 23:41 session (#164): the user played; a Journal Menu opened at 23:42:01
    # with no pilot command, and the Console at 23:42:07 WAS piloted
    r = judge(os.path.join(fx, 'launchprobe-20260901-234109-human.log'),
              os.path.join(fx, 'menupilot-20260901-234109.log'))
    print('  ' + describe(r))
    ok(r['human'], '23:41 session: human detected')
    ok(r['unmatched'] and r['unmatched'][0]['menu'] == 'Journal Menu'
       and r['unmatched'][0]['at'].startswith('23:42:01'), 'first unmatched = Journal Menu 23:42:01')
    ok(any(p['menu'] == 'Console' for p in r['piloted']), 'piloted Console open not counted')
    ok(r['boundary_event'] == 'AUTOLOAD_SETTLED', 'boundary is AUTOLOAD_SETTLED')
    # 23:11 session (the hardening smoke): killed 2 s after the save loaded,
    # nobody touched it (reconstructed from records/launch-verify-20260901-231117.md)
    r = judge(os.path.join(fx, 'launchprobe-20260901-231031-clean.log'),
              os.path.join(fx, 'menupilot-empty.log'))
    print('  ' + describe(r))
    ok(not r['human'], '23:11 session: nobody detected')
    ok(r['boundary_event'] == 'AUTOLOAD_SETTLED' and r['events_after'] > 0, 'boundary found, events examined')
    # same 23:41 log without the pilot log: the Console open becomes unmatched too
    r = judge(os.path.join(fx, 'launchprobe-20260901-234109-human.log'),
              os.path.join(fx, 'menupilot-empty.log'))
    ok(r['human'] and any(u['menu'] == 'Console' for u in r['unmatched']),
       'without a pilot log every gameplay open counts')
    # a still-loading log (nothing past the main menu) never claims a human
    r = judge(os.path.join(fx, 'launchprobe-20260901-231031-clean.log'),
              os.path.join(fx, 'menupilot-empty.log'), since=4e9)
    ok(not r['human'] and 'stale' in r['note'], 'stale log (since in the future) -> nobody')
    print(f'\n{"all" if not bad else bad} human-presence selftest {"cases pass" if not bad else "FAILURES"}')
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if '--selftest' in a:
        return selftest()

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    since = opt('--since')
    r = judge(opt('--probe', PROBE_LOG), opt('--pilot', PILOT_LOG),
              float(since) if since else None)
    print(describe(r))
    if '--json' in a:
        print(json.dumps(r, indent=1))
    return HUMAN_AT_CONTROLS if r['human'] else 0


if __name__ == '__main__':
    sys.exit(main())
