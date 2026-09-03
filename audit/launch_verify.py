"""Prove a change did not break the game: launch it, reach the menu, load a save.

User criterion, 2026-08-31: *"With each change we must successfully launch the
game and load the save"* and *"It must reach the main menu in under 60 seconds
or it's a failure."* This is that test, as a pass/fail command.

  py -3 audit/launch_verify.py --dry-run     # everything except starting the game
  py -3 audit/launch_verify.py               # the real run
  py -3 audit/launch_verify.py --menu-budget 60 --save-budget 180
  py -3 audit/launch_verify.py --save Save7_17674846_0_...  # a specific save
  py -3 audit/launch_verify.py --leave-running   # never kill, inspect it yourself
  py -3 audit/launch_verify.py --attach-pid N    # self-test: watch a process, no launch
  py -3 audit/launch_verify.py --claim-owner NAME  # owner for the work claim ($SKYRIM_CLAIM_OWNER)
  py -3 audit/launch_verify.py --steam-chain     # legacy Steam launch; can never autoload
  py -3 audit/launch_verify.py --force-kill "reason"  # kill even if a human is detected (#164)
  py -3 audit/launch_verify.py --no-autoload --leave-running  # stop at the MAIN MENU (menu
                                                 # pilot work); verdict MENU-ONLY, never PASS

PASS requires BOTH:
  1. the real main menu open within --menu-budget seconds of process start, and
  2. a save actually loaded (kPostLoadGame, success).

Exit 0 PASS, 1 FAIL. Either way a record lands in records/launch-verify-*.md.

Unlike launch_watch.py this DOES launch the game and DOES kill it - the user
authorized assistant-driven launches for verification runs specifically. It is
still the only file here allowed to do either.

## Why it insists on LaunchProbe

The cheap main-menu signals lie. On both hung launches of 2026-08-31,
CommunityShaders' `InitializeMenuIcons` and SkyParkour's log fired at about
T+56s and the game never became playable. A signal that fires during the exact
failure it is meant to exclude cannot gate a PASS, so this refuses to certify
anything without LaunchProbe - a micro SKSE plugin that logs the game's own
`MenuOpenCloseEvent` for "Main Menu" and SKSE's kPostLoadGame, timestamped.
Staged at records/source-builds/launch-probe/. `--allow-unverified-signal`
downgrades the run to a timing observation that can only ever FAIL or be
INCONCLUSIVE; it can never PASS.

## The hardened chain (2026-09-01, #103 #141 #143)

- The run holds the instance work claim (audit/claim.py) from before the
  launch until the verdict; a claim held by another owner REFUSES the run. It
  also refuses while a SkyrimSE.exe or MO2Headless.exe already exists.
- launch_skyrim.ps1 scrubs every SKYRIM_LAUNCH_PROBE_* / SKYRIM_MENU_PILOT_*
  variable before it restarts Steam, so nothing this harness sets can leak
  into the user's later launches. The game is therefore spawned DIRECTLY
  (`-Direct`: MO2Headless run -> ModOrganizer.exe headless-run ->
  skse64_loader.exe) with the probe variables on that child only.
  `--steam-chain` uses steam://rungameid instead; on that chain the probe can
  never autoload, so the verdict can only be MENU-ONLY or FAIL.
- The profile's INIs are synced over the Documents pair first (see the ps1).

## Human at the controls (#164)

Before the kill at the end of a run (the only kill in this file; there is no
idle timeout under --leave-running), `human_presence.judge` reads the probe
logs: a gameplay menu opened after AUTOLOAD_SETTLED that no MenuPilot command
explains within 2 s means a person is playing in the harness's session. Then
the kill is REFUSED, `HUMAN_AT_CONTROLS` is logged
(records/human-at-controls.jsonl and the run record), the game stays up, and
the exit code is 88 regardless of the verdict. `--force-kill "<reason>"`
overrides; the reason is logged. Same check in install_mod.py before an
install or sort while SkyrimSE.exe is alive.
"""
import datetime, io, json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

import launch_watch as W
import threaddump as TD
import claim
import human_presence as HP

AUDIT = os.path.dirname(os.path.abspath(__file__))
REPO = W.REPO
INSTANCE = W.INSTANCE
PROFILE = os.path.join(INSTANCE, 'profiles', 'Default')
SAVES = os.path.join(W.DOCS, 'Saves')
LAUNCHER = os.path.join(AUDIT, 'launch_skyrim.ps1')
PROBE_DLL = 'LaunchProbe.dll'
PROBE_STAGED = os.path.join(REPO, 'records', 'source-builds', 'launch-probe')
EPOCH_DELTA = 11644473600            # FILETIME 1601 epoch -> unix 1970 epoch


# --------------------------------------------------------------- environment
def probe_installed():
    """Is LaunchProbe.dll reachable through the VFS this launch will build?

    Enabled mods only: a staged-but-disabled copy contributes nothing, and
    reporting it as present is how a PASS gets certified on a signal that was
    never loaded."""
    hits = []
    ml = os.path.join(PROFILE, 'modlist.txt')
    if os.path.exists(ml):
        for line in io.open(ml, encoding='utf-8', errors='replace'):
            line = line.rstrip('\n')
            if not line.startswith('+'):
                continue                      # '-' disabled, '*' separator
            p = os.path.join(INSTANCE, 'mods', line[1:], 'SKSE', 'Plugins', PROBE_DLL)
            if os.path.exists(p):
                hits.append(p)
    for extra in (os.path.join(INSTANCE, 'overwrite', 'SKSE', 'Plugins', PROBE_DLL),
                  os.path.join(r'C:\Program Files (x86)\Steam\steamapps\common'
                               r'\Skyrim Special Edition\Data\SKSE\Plugins', PROBE_DLL)):
        if os.path.exists(extra):
            hits.append(extra)
    return hits


def newest_save():
    """The save the run will load. LocalSaves=false, so these live in Documents."""
    local = False
    st = os.path.join(PROFILE, 'settings.txt')
    if os.path.exists(st):
        local = 'localsaves=true' in io.open(st, encoding='utf-8',
                                             errors='replace').read().lower()
    d = os.path.join(PROFILE, 'saves') if local else SAVES
    if not os.path.isdir(d):
        return None, d
    ess = [f for f in os.listdir(d) if f.lower().endswith('.ess')]
    if not ess:
        return None, d
    newest = max(ess, key=lambda f: os.path.getmtime(os.path.join(d, f)))
    return os.path.splitext(newest)[0], d


def start_epoch(pid):
    """Process creation as unix time, so probe wall-clock lines can be measured
    against it. This is T0: the 60-second budget is from the game process
    starting, not from the Steam cycle, which is not the build's fault."""
    h = W.k32.OpenProcess(W.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        import ctypes.wintypes as wt
        c, x, kt, ut = (wt.FILETIME() for _ in range(4))
        import ctypes
        if not W.k32.GetProcessTimes(h, *(ctypes.byref(v) for v in (c, x, kt, ut))):
            return None
        return W._ft(c) - EPOCH_DELTA
    finally:
        W.k32.CloseHandle(h)


def probe_wall(ev):
    """Probe timestamps are local wall clock: '2026-08-31 23:04:12.345'."""
    try:
        return datetime.datetime.strptime(ev['wall'],
                                          '%Y-%m-%d %H:%M:%S.%f').timestamp()
    except ValueError:
        return None


def first(events, name):
    return next((e for e in events if e['event'] == name), None)


def decide(st, cfg):
    """The pass/fail rules, as a pure function of one observation.

    Kept separate from the sampling loop so `--selftest` can replay whole
    timelines - including the two real shapes from 2026-08-31 - without a game.
    Order matters: the menu budget is checked BEFORE a successful load, because
    the user's criterion is a hard one and a save that loads at t+90s after a
    menu at t+75s is still a failed launch."""
    if st['save_ok'] is False:
        return True, 'FAIL', f'the game reported the save load FAILED: {st["detail"]}'
    if not st['alive']:
        return True, 'FAIL', f'the game process exited after {st["elapsed"]:.0f}s'
    if st['menu_at'] is not None and st['menu_at'] > cfg['menu_budget']:
        return True, 'FAIL', (f'main menu took {st["menu_at"]:.1f}s, over the '
                              f'{cfg["menu_budget"]:.0f}s budget')
    if st['menu_at'] is None and st['elapsed'] > cfg['menu_budget']:
        return True, 'FAIL', (f'no main menu within {cfg["menu_budget"]:.0f}s '
                              f'(last probe event: {st["detail"] or "none"})')
    if cfg.get('no_autoload') and st['menu_at'] is not None:
        return True, 'MENU-ONLY', (f'main menu at {st["menu_at"]:.1f}s; no save load was '
                                   f'requested (--no-autoload), so this is NOT a PASS')
    if st['save_at'] is not None:
        return True, 'PASS', (f'main menu at {st["menu_at"]:.1f}s, save loaded at '
                              f'{st["save_at"]:.1f}s')
    if st['menu_at'] is not None and st['elapsed'] > st['menu_at'] + cfg['save_budget']:
        return True, 'FAIL', (f'main menu reached at {st["menu_at"]:.1f}s but the save '
                              f'never finished loading within '
                              f'{cfg["save_budget"]:.0f}s')
    if st['state'] in W.HANG:
        return True, 'FAIL', f'watchdog verdict {st["state"]}'
    return False, None, None


# ------------------------------------------------------------------ the run
class Result:
    def __init__(self):
        self.verdict = 'FAIL'
        self.reason = 'not run'
        self.t0 = None
        self.pid = None
        self.phases = {}          # name -> seconds after t0
        self.samples = []
        self.threads = None
        self.evidence = []
        self.probe = []
        self.human_at_controls = False   # kill refused; exit 88 (#164)


def launch(env_extra, timeout=420, steam_chain=False):
    """Start the sanctioned launch sequence and return the child.

    launch_skyrim.ps1 owns the parts that are easy to get wrong: closing a
    stale chain, seeding the game-side Plugins.txt, and cycling Steam to clear
    a wedged launcher. Its `-AllowInteractiveDesktop` gate exists because
    autonomous launches were forbidden; the user has now authorized them for
    verification, which is the only reason this passes it.

    The environment matters more than it looks: the probe reads its settings
    from env vars, and the ONLY way they reach the game is by being set before
    this script restarts Steam, since the chain is Steam -> MO2 -> SKSE ->
    SkyrimSE and each link inherits from the last."""
    env = dict(os.environ, **env_extra)
    cmd = ['pwsh', '-NoProfile', '-NonInteractive', '-File', LAUNCHER,
           '-AllowInteractiveDesktop', '-WaitSeconds', '30']
    if not steam_chain:
        cmd.append('-Direct')
    # A pipe nobody drains fills at 64KB and blocks the child mid-Steam-cycle,
    # which would look exactly like a launch failure. Spool to a file instead.
    import tempfile
    fd, path = tempfile.mkstemp(prefix='launch-skyrim-', suffix='.log')
    fh = os.fdopen(fd, 'w', encoding='utf-8', errors='replace')
    return subprocess.Popen(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT), path


def _running(name):
    out = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}'],
                         capture_output=True, text=True).stdout or ''
    return name.lower() in out.lower()


def _tail(path, n):
    try:
        return io.open(path, encoding='utf-8', errors='replace').read()[-n:].strip()
    except OSError:
        return '(unavailable)'


def kill(pid, why, cfg=None, r=None, since=None):
    """End the game process - unless a human is at the controls (#164).

    2026-09-01 23:45: this kill ended a session the user had started playing
    in; nothing saved. Now the game's own menu events are consulted first, and
    a refusal is loud in three places: stdout, the run record, and
    records/human-at-controls.jsonl. Returns True when the process was killed."""
    cfg = cfg or {}
    verdict = HP.judge(since=since)
    if verdict['human'] and not cfg.get('force_kill'):
        line = (f'HUMAN_AT_CONTROLS - NOT killing pid {pid}: {HP.describe(verdict)}. '
                f'The game stays up; exit code {HP.HUMAN_AT_CONTROLS}. '
                f'--force-kill "<reason>" overrides.')
        print('   ' + line)
        HP.log_refusal(verdict, f'launch_verify pid {os.getpid()} ({why})')
        if r is not None:
            r.human_at_controls = True
            r.evidence.append(line)
        return False
    if verdict['human']:
        line = f'FORCE_KILL over a detected human: reason="{cfg["force_kill"]}" ({HP.describe(verdict)})'
        print('   ' + line)
        HP.log_refusal(verdict, f'launch_verify pid {os.getpid()} FORCE_KILL reason={cfg["force_kill"]!r}')
        if r is not None:
            r.evidence.append(line)
    print(f'   killing pid {pid}: {why}')
    subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True, text=True)
    return True


def verify(cfg):
    r = Result()
    launch_started = time.time()
    probe_paths = probe_installed()
    save, save_dir = (cfg['save'], None) if cfg['save'] else newest_save()

    print(f'probe:  {"installed: " + probe_paths[0] if probe_paths else "NOT INSTALLED"}')
    print(f'save:   {save}')
    print(f'budget: menu {cfg["menu_budget"]:.0f}s, save {cfg["save_budget"]:.0f}s')

    blockers = []
    if not probe_paths and not cfg['allow_unverified']:
        blockers.append('LaunchProbe is not installed in any enabled mod, so a real '
                        'main menu cannot be distinguished from a wedge and no PASS '
                        f'would mean anything. Install {PROBE_STAGED} (the team lead '
                        'schedules this), or re-run with --allow-unverified-signal '
                        'for a timing observation that can never PASS.')
    if not save and not cfg['no_autoload']:
        blockers.append(f'no .ess save found in {save_dir}')
    owner = cfg['claim_owner'] or claim.default_owner()
    other = claim.held_by_other(owner)
    if other:
        blockers.append(f'instance work claim is {claim.describe(other)} - not launching '
                        f'under someone else\'s work (#103)')
    if not cfg['attach_pid']:
        live = W.find_process()
        if live:
            blockers.append(f'SkyrimSE.exe is already running (pid {live}); a verification '
                            f'launch needs a clean start')
        for exe in ('MO2Headless.exe', 'ModOrganizer.exe'):
            if _running(exe):
                blockers.append(f'{exe} is running - a mutation or another launch chain '
                                f'is in progress (#103)')
    if cfg['steam_chain'] and not cfg['no_autoload']:
        blockers.append('--steam-chain cannot autoload: the launcher scrubs the probe '
                        'variables before Steam restarts (#141). Use the direct chain, '
                        'or --no-autoload for a menu-only observation.')

    # An empty SKYRIM_LAUNCH_PROBE_AUTOLOAD disables the probe's autoload
    # (LaunchProbe main.cpp: AutoLoadEnabled() == !autoLoadSave.empty()).
    env = {'SKYRIM_LAUNCH_PROBE_AUTOLOAD': '' if cfg['no_autoload'] else (save or ''),
           'SKYRIM_LAUNCH_PROBE_DELAY_MS': str(int(cfg['settle_ms'])),
           'SKSE_AUTOMATION_SILENT_UI': '1',
           'SKYRIM_CLAIM_OWNER': owner}
    plan = [f'would run: pwsh -NoProfile -NonInteractive -File {LAUNCHER} '
            f'-AllowInteractiveDesktop -WaitSeconds 30'
            + ('' if cfg['steam_chain'] else ' -Direct'),
            f'with env {json.dumps(env)} (scrubbed from Steam by the launcher; '
            f'applied to the direct child only)',
            f'claim: {claim.describe(claim.read())} -> would acquire as {owner}',
            f'probe: {probe_paths[0] if probe_paths else "NOT INSTALLED"}',
            f'save: {save} (from {save_dir})']
    # A dry run still reports the blockers - it is the rehearsal, so it has to
    # show what the real run would refuse on, not just what it would type.
    if cfg['dry_run']:
        r.verdict = 'DRY-RUN'
        r.reason = ('plan validated; the real run would REFUSE' if blockers
                    else 'plan validated, nothing blocking')
        r.evidence = plan + [f'BLOCKER: {b}' for b in blockers]
        return r
    if blockers:
        r.verdict, r.reason = 'REFUSED', blockers[0]
        r.evidence = blockers[1:]
        return r

    if not cfg['attach_pid']:
        try:
            claim.acquire(owner, f'launch_verify ({"menu-only" if cfg["no_autoload"] else "full"})',
                          ttl=45, pid_bound=False)
        except claim.ClaimHeld as e:
            r.verdict, r.reason = 'REFUSED', f'instance work claim is {e}'
            return r
        r.evidence.append(f'claim held as {owner}; chain: '
                          f'{"steam://rungameid" if cfg["steam_chain"] else "direct (MO2Headless run)"}')

    child = launcher_log = None
    if cfg['attach_pid']:
        # Harness self-test seam: exercise the sampling loop, the phase timing,
        # the record and the kill against a process that is not Skyrim, so none
        # of that code is first run for real on a launch that matters. This
        # branch MUST come before launch() - an earlier edit of this file failed
        # to apply silently and the "self-test" launched the game for real.
        pid = cfg['attach_pid']
        print(f'\nATTACH MODE: not launching; watching existing pid {pid}')
    else:
        print('\nlaunching (launch_skyrim.ps1 cycles Steam first; this takes a minute)')
        child, launcher_log = launch(env, steam_chain=cfg['steam_chain'])

        # ---- wait for the process, then start the clock at ITS creation time
        pid = None
        while time.time() - launch_started < cfg['spawn_budget']:
            pid = W.find_process()
            if pid and (start_epoch(pid) or 0) >= launch_started - 5:
                break
            pid = None
            time.sleep(1)
        if not pid:
            r.reason = (f'no SkyrimSE.exe appeared within {cfg["spawn_budget"]:.0f}s of '
                        f'starting the launch sequence')
            r.evidence.append('launcher output: ' + _tail(launcher_log, 1200))
            return r
    r.pid, r.t0 = pid, start_epoch(pid)
    print(f'{"watching" if cfg["attach_pid"] else "game started:"} pid {pid}\n')

    # ---- watch, with the probe log as the authoritative clock
    p = W.Proc(pid)
    prog = W.Progress()
    prev_cpu = p.cpu_seconds() or 0.0
    prev_ws = (p.memory()[0] or 0) / 1e6
    prev_prog = prog.sample()
    last_move = time.time()
    menu_at = save_at = None
    try:
        while True:
            time.sleep(cfg['interval'])
            now = time.time()
            elapsed = now - r.t0
            alive = p.alive()
            cpu = p.cpu_seconds() if alive else None
            ws = ((p.memory()[0] or 0) / 1e6) if alive else 0.0
            now_prog = prog.sample()
            moved = W.Progress.delta(prev_prog, now_prog)
            if moved:
                last_move = now
            cpu_pct = ((cpu - prev_cpu) / cfg['interval'] * 100) if (cpu and alive) else 0.0
            m = W.markers(since=launch_started)
            s = {'alive': alive, 'moved': moved, 'cpu_core_pct': cpu_pct, 'ws_mb': ws,
                 'ws_delta_mb': ws - prev_ws, 'responding': p.responding() if alive else None,
                 'stalled_for': now - last_move, 'markers': m}
            state, ev = W.classify(s, _cfg_obj(cfg))
            r.samples.append({'elapsed': elapsed, 'cpu_core_pct': cpu_pct, 'ws_mb': ws,
                              'responding': s['responding'], 'state': state,
                              'moved': moved})
            print(f'  t+{elapsed:>5.1f}s  {state:<20} cpu {cpu_pct:>5.1f}%core  '
                  f'ws {ws:>6.0f}MB  {", ".join(moved[:2]) or "-"}')
            prev_cpu, prev_ws, prev_prog = cpu or prev_cpu, ws, now_prog

            r.probe = W.probe_events(since=launch_started) or []
            if menu_at is None:
                e = first(r.probe, 'MAIN_MENU_OPEN')
                if e and probe_wall(e):
                    menu_at = probe_wall(e) - r.t0
                    r.phases['main menu'] = menu_at
                    print(f'   MAIN MENU at t+{menu_at:.1f}s '
                          f'({"within" if menu_at <= cfg["menu_budget"] else "OVER"} '
                          f'the {cfg["menu_budget"]:.0f}s budget)')
            for name, label in (('kDataLoaded', 'kDataLoaded'),
                                ('kInputLoaded', 'kInputLoaded'),
                                ('kPreLoadGame', 'save load started')):
                e = first(r.probe, name)
                if e and label not in r.phases and probe_wall(e):
                    r.phases[label] = probe_wall(e) - r.t0
            save_ok = None
            post = [e for e in r.probe if e['event'] == 'kPostLoadGame']
            if post and probe_wall(post[-1]):
                save_ok = 'success=1' in post[-1]['rest']
                if save_ok and save_at is None:
                    save_at = probe_wall(post[-1]) - r.t0
                    r.phases['save loaded'] = save_at

            done, verdict, reason = decide(
                {'alive': alive, 'elapsed': elapsed, 'menu_at': menu_at,
                 'save_at': save_at, 'save_ok': save_ok, 'state': state,
                 'detail': (post[-1]['rest'] if post else
                            (r.probe[-1]['event'] if r.probe else None))}, cfg)
            if done:
                r.reason = reason
                if verdict in ('PASS', 'MENU-ONLY'):
                    r.verdict = verdict
                elif state in W.HANG:
                    r.evidence += ev
                    r.threads = W.busiest_threads(pid)
                break
    except KeyboardInterrupt:
        r.reason = 'interrupted by Ctrl-C'
    finally:
        r.evidence.append(f'probe events seen: '
                          f'{", ".join(e["event"] for e in r.probe) or "none"}')
        if r.verdict != 'PASS' and r.threads is None and p.alive():
            r.threads = W.busiest_threads(pid)
        p.close()
        if not cfg['leave_running'] and (W.find_process() == pid or cfg['attach_pid']):
            kill(pid, 'verification run finished'
                 if r.verdict == 'PASS' else f'FAIL: {r.reason}',
                 cfg=cfg, r=r, since=None if cfg['attach_pid'] else launch_started)
        if child is not None:
            try:
                child.wait(timeout=60)
            except Exception:
                pass
            r.evidence.append('launcher output: ' + _tail(launcher_log, 800))
        if not cfg['attach_pid'] and not cfg['keep_claim']:
            claim.release(owner)
    if cfg['allow_unverified'] and not probe_paths and r.verdict == 'PASS':
        r.verdict, r.reason = 'INCONCLUSIVE', (
            'ran without LaunchProbe, so no signal here can certify a real main '
            'menu; timings below are observations, not a pass')
    return r


def _cfg_obj(cfg):
    c = W.Cfg()
    c.interval = cfg['interval']
    c.hang_seconds = cfg['hang_seconds']
    return c


# ------------------------------------------------------------------ record
def write_record(r, cfg):
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    path = os.path.join(REPO, 'records', f'launch-verify-{stamp}.md')
    L = [f'# Launch verification - {r.verdict}', '',
         f'- when: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}',
         f'- verdict: **{r.verdict}**'
         + ('  (HUMAN_AT_CONTROLS - kill refused, game left running, exit 88)'
            if r.human_at_controls else ''),
         f'- reason: {r.reason}',
         f'- criterion: main menu within {cfg["menu_budget"]:.0f}s of process start '
         f'AND a save loaded'
         + (' (--no-autoload: save load deliberately skipped, MENU-ONLY is not a PASS)'
            if cfg.get('no_autoload') else ''),
         f'- pid: {r.pid}', '']
    if r.phases:
        L += ['## Timing (seconds after SkyrimSE.exe started)', '',
              '| phase | t+s |', '|---|---:|']
        L += [f'| {k} | {v:.1f} |' for k, v in sorted(r.phases.items(), key=lambda kv: kv[1])]
        L.append('')
    if r.evidence:
        L += ['## Evidence', ''] + [f'- {e}' for e in r.evidence if e] + ['']
    if r.probe:
        L += ['## LaunchProbe timeline', '', '```']
        L += [f'{e["ms"]:>8}ms  {e["event"]} {e["rest"]}'.rstrip() for e in r.probe[:60]]
        L += ['```', '']
    if r.samples:
        L += ['## Samples', '', '| t+s | cpu %core | ws MB | responding | state | moved |',
              '|---|---|---|---|---|---|']
        for s in r.samples[-30:]:
            L.append(f'| {s["elapsed"]:.0f} | {s["cpu_core_pct"]:.0f} | {s["ws_mb"]:.0f} '
                     f'| {s["responding"]} | {s["state"]} | '
                     f'{", ".join(s["moved"][:3]) or "-"} |')
        L.append('')
    if r.threads:
        rows, total, _ = r.threads
        L += [f'## Threads ({total} in the process)', '',
              '| CPU s in 1.5s | tid | entry-point module |', '|---|---|---|']
        L += [f'| {c:.3f} | {t} | {m or "(unattributed)"} |' for c, t, m in rows]
        L.append('')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    return path


def selftest():
    """Replay whole timelines through decide() and the probe parser.

    The two that matter are real: a good launch, and the 2026-08-31 shape where
    every cheap signal said the menu was up at ~T+56s and the game was dead."""
    cfg = {'menu_budget': 60.0, 'save_budget': 180.0}
    cases = [
        ('PASS', 'menu 41.8s, save 65.1s', dict(alive=True, elapsed=70, menu_at=41.8,
                                                save_at=65.1, save_ok=True,
                                                state='at-menu', detail='')),
        ('FAIL', 'menu over budget', dict(alive=True, elapsed=80, menu_at=75.0,
                                          save_at=None, save_ok=None,
                                          state='loading', detail='')),
        # a save that loads AFTER a late menu is still a failed launch
        ('FAIL', 'late menu beats a good load', dict(alive=True, elapsed=95, menu_at=75.0,
                                                     save_at=90.0, save_ok=True,
                                                     state='at-menu', detail='')),
        ('FAIL', 'no menu in budget', dict(alive=True, elapsed=61, menu_at=None,
                                           save_at=None, save_ok=None,
                                           state='stalled', detail='kDataLoaded')),
        ('FAIL', 'died', dict(alive=False, elapsed=30, menu_at=None, save_at=None,
                              save_ok=None, state='died', detail='')),
        ('FAIL', 'hang before the budget runs out',
         dict(alive=True, elapsed=50, menu_at=None, save_at=None, save_ok=None,
              state='hung-spin', detail='')),
        ('FAIL', 'load reported failure', dict(alive=True, elapsed=90, menu_at=40.0,
                                               save_at=None, save_ok=False,
                                               state='at-menu', detail='success=0')),
        ('FAIL', 'menu fine, save never lands',
         dict(alive=True, elapsed=230, menu_at=40.0, save_at=None, save_ok=None,
              state='stalled', detail='')),
        (None, 'still loading, nothing decided yet',
         dict(alive=True, elapsed=20, menu_at=None, save_at=None, save_ok=None,
              state='loading', detail='')),
    ]
    bad = 0
    for want, label, st in cases:
        done, verdict, reason = decide(st, cfg)
        got = verdict if done else None
        bad += got != want
        print(f'  {"ok  " if got == want else "FAIL"} {str(want):<5} {label:<34} '
              f'{(reason or "keep watching")[:60]}')
    # the parser, against the format the plugin actually writes
    sample = ('[2026-08-31 23:40:41.905] +41817ms MAIN_MENU_OPEN constant="Main Menu" '
              'ui_is_menu_open=1 has_movie_view=1\n'
              '[2026-08-31 23:41:05.200] +65112ms SKSE_MESSAGE name="kPostLoadGame" '
              'sender="" success=1\n')
    import tempfile
    fd, path = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    io.open(path, 'w', encoding='utf-8').write(sample)
    old = W.PROBE_LOG
    W.PROBE_LOG = path
    try:
        ev = W.probe_events()
        m = W.markers()
        ok = ([e['event'] for e in ev] == ['MAIN_MENU_OPEN', 'kPostLoadGame']
              and m['menu_confirmed'] and m['save_loaded'])
        bad += not ok
        print(f'  {"ok  " if ok else "FAIL"} parser  menu_confirmed={m["menu_confirmed"]} '
              f'save_loaded={m["save_loaded"]} events={[e["event"] for e in ev]}')
    finally:
        W.PROBE_LOG = old
        os.remove(path)
    print(f'\n{len(cases) + 1 - bad}/{len(cases) + 1} verification cases pass')
    print(f'probe installed: {probe_installed() or "no"}')
    print(f'save that would load: {newest_save()[0]}')
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if '--selftest' in a:
        return selftest()

    def opt(name, cast, default):
        if name not in a:
            return default
        i = a.index(name) + 1
        return cast(a[i]) if i < len(a) and not a[i].startswith('--') else default

    cfg = {
        'menu_budget': opt('--menu-budget', float, 60.0),      # the user's criterion
        'save_budget': opt('--save-budget', float, 180.0),
        'spawn_budget': opt('--spawn-budget', float, 300.0),
        'settle_ms': opt('--settle-ms', float, 1500.0),
        'interval': opt('--interval', float, 3.0),
        'hang_seconds': opt('--hang-seconds', float, 45.0),
        'save': opt('--save', str, None),
        'dry_run': '--dry-run' in a,
        'leave_running': '--leave-running' in a,
        'no_autoload': '--no-autoload' in a,      # stop at the main menu (MenuPilot)
        'steam_chain': '--steam-chain' in a,      # legacy chain: no autoload possible
        'claim_owner': opt('--claim-owner', str, None),
        'keep_claim': '--keep-claim' in a,        # leave the claim held after the run
        'allow_unverified': '--allow-unverified-signal' in a,
        'attach_pid': opt('--attach-pid', int, None),   # self-test seam, see verify()
        'force_kill': opt('--force-kill', str, None),   # reason; overrides the human guard (#164)
    }
    if '--force-kill' in a and not (cfg['force_kill'] or '').strip():
        print('--force-kill needs the reason as its argument'); return 64

    print('=' * 72)
    print('[1] preflight')
    print('=' * 72)
    if '--skip-preflight' not in a:
        rc = subprocess.run([sys.executable, os.path.join(AUDIT, 'preflight.py')],
                            capture_output=True, text=True, timeout=1800)
        print((rc.stdout or '').rstrip())
        if rc.returncode != 0:
            print('\nSTOP: preflight failed, refusing to launch.')
            return 1

    print('\n' + '=' * 72)
    print('[2] launch and verify' + ('  (DRY RUN)' if cfg['dry_run'] else ''))
    print('=' * 72)
    r = verify(cfg)

    print('\n' + '=' * 72)
    print(f'VERDICT: {r.verdict} - {r.reason}')
    for k, v in sorted(r.phases.items(), key=lambda kv: kv[1]):
        print(f'   {k:<20} t+{v:.1f}s')
    for e in r.evidence:
        if e:
            print(f'   {e}')

    if r.verdict not in ('DRY-RUN', 'REFUSED'):
        print('\n' + '=' * 72)
        print('[3] triage')
        print('=' * 72)
        t = subprocess.run([sys.executable, os.path.join(AUDIT, 'launch_triage.py')],
                           capture_output=True, text=True, timeout=600)
        print((t.stdout or '').rstrip())
        dump = TD.newest_dump()
        if dump and r.t0 and os.path.getmtime(dump) >= r.t0:
            print('\nthread dump taken during this run:')
            TD.report(dump)
        print(f'\nrecord: {write_record(r, cfg)}')
    if r.human_at_controls:
        print(f'\nHUMAN_AT_CONTROLS: the game was left running (exit {HP.HUMAN_AT_CONTROLS}); '
              f'report this, do not retry with --force-kill unless the user says so')
        return HP.HUMAN_AT_CONTROLS
    return 0 if r.verdict in ('PASS', 'DRY-RUN', 'MENU-ONLY') else 1


if __name__ == '__main__':
    sys.exit(main())
