"""One command for a whole launch: gate it, watch it, then read the wreckage.

The three pieces existed separately and so got run separately, which is how a
launch went out with a stale gate and nobody watching. This is the order they
are meant to run in, and it refuses to move on when a step says no.

This is the INTERACTIVE flow: the user launches, this watches. For the
automated pass/fail run that launches the game itself and requires a main menu
inside 60 seconds plus a loaded save, use `--verify`, which hands off to
`launch_verify.py` (same gate, same watchdog, plus a verdict).

  py -3 audit/launch_session.py
  py -3 audit/launch_session.py --verify [...]       # -> launch_verify.py
  py -3 audit/launch_session.py --wait 300 --hang-seconds 90
  py -3 audit/launch_session.py --skip-preflight     # only when it just ran clean

  1. preflight.py     - anything non-zero here and the user is NOT told to launch
  2. the user launches (this tool never launches the game itself)
  3. launch_watch.py  - live state until the game exits or the user stops it
  4. launch_triage.py - what the SKSE logs say afterwards
  5. threaddump.py    - automatically, if a dump was taken during the hang

Exit code is the first thing that failed: 1 preflight, 2 a hang was reported,
3 died before the menu, 4 never started, 5 triage found refused plugins.
"""
import io, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# reconfigure, not a fresh TextIOWrapper: two of these modules import each
# other's siblings, and re-wrapping an already-wrapped stdout closes the
# buffer the first wrapper owns
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

import launch_watch as W
import threaddump as TD

AUDIT = os.path.dirname(os.path.abspath(__file__))


def step(n, title):
    print(f'\n{"=" * 72}\n[{n}] {title}\n{"=" * 72}')


def run(script, *args):
    r = subprocess.run([sys.executable, os.path.join(AUDIT, script), *args],
                       capture_output=True, text=True, timeout=1800)
    print((r.stdout or '').rstrip())
    if r.stderr.strip():
        print(r.stderr.rstrip())
    return r.returncode


def main():
    a = sys.argv[1:]
    if '--verify' in a:
        rest = [x for x in a if x != '--verify']
        return subprocess.call([sys.executable, os.path.join(AUDIT, 'launch_verify.py'),
                                *rest])

    def opt(name, cast, default):
        return cast(a[a.index(name) + 1]) if name in a else default

    if '--skip-preflight' not in a:
        step(1, 'preflight - is this build safe to launch at all?')
        if run('preflight.py') != 0:
            print('\nSTOP. Do not tell the user to launch. Fix the FAIL lines above, '
                  'then run this again.')
            return 1

    step(2, 'launch')
    print('The game is NOT launched by this tool (standing rule: no autonomous '
          'launches).\nLaunch it now the usual way - Steam, or MO2 -> SKSE.\n')

    cfg = W.Cfg()
    cfg.interval = opt('--interval', float, W.Cfg.interval)
    cfg.hang_seconds = opt('--hang-seconds', float, W.Cfg.hang_seconds)
    wait = opt('--wait', float, 300.0)

    step(3, 'watch - is it progressing?')
    dumps_before = set(os.listdir(W.SKSE_DIR)) if os.path.isdir(W.SKSE_DIR) else set()
    deadline = time.time() + wait
    pid = None
    print(f'waiting up to {wait:.0f}s for {W.PROCESS_NAME}...')
    while time.time() < deadline:
        pid = W.find_process()
        if pid:
            break
        time.sleep(2)
    if not pid:
        print(f'no {W.PROCESS_NAME} appeared in {wait:.0f}s - the launch never reached '
              f'the game.')
        run('launch_triage.py', '--max-age-min', '5')
        return 4
    rc = W.watch(pid, cfg)

    step(4, 'triage - what do the logs say?')
    trc = run('launch_triage.py')

    new_dumps = [f for f in os.listdir(W.SKSE_DIR)
                 if f.startswith('threaddump-') and f not in dumps_before]
    if new_dumps:
        step(5, f'thread dump taken during this session: {sorted(new_dumps)[-1]}')
        TD.report(os.path.join(W.SKSE_DIR, sorted(new_dumps)[-1]))

    print(f'\n{"=" * 72}')
    said = {0: 'clean', 2: 'HANG REPORTED', 3: 'DIED BEFORE MENU'}.get(rc, str(rc))
    print(f'watch said: {said}   triage exit: {trc}')
    return rc or (5 if trc == 2 else 0)


if __name__ == '__main__':
    sys.exit(main())
