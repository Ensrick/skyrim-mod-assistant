"""Everything that must be true BEFORE the user is told to launch.

Born 2026-09-01 after three consecutive broken launches, each caused by state
the assistant owned and never checked: INIs reset to 1080p windowed, DLLs
unparked on a version-gate pass alone, and plugins silently unstarred. The user:
"You're going to need to monitor this shit."

Exit 0 = safe to launch. Non-zero = do not tell the user to launch.

  py -3 audit/preflight.py
"""
import io, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = os.path.join(INSTANCE, 'profiles', 'Default')
DOCS = os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games',
                    'Skyrim Special Edition')
GAME_SIDE = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Skyrim Special Edition', 'Plugins.txt')

# Keys the user decided deliberately. Each is a value the game or a launcher has
# been observed to reset. Rationale lives in docs/INI_AND_PROFILE_STATE.md.
DELIBERATE = {
    'skyrimprefs.ini': {
        'iSize W': '3840', 'iSize H': '2160',
        'bFull Screen': '0', 'bBorderless': '1',
        'bUpsellOwned': '1',          # 0 makes the game show the AE first-run prompt
    },
    'skyrim.ini': {
        'fDefaultWorldFOV': '120', 'fDefault1stPersonFOV': '120',
        'fMaxTime': '0.0083',         # 120 Hz desktop
        'bEnableLogging': '1',
    },
}

fails, warns = [], []


def ini_get(path, key):
    if not os.path.exists(path):
        return None
    t = io.open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'^' + re.escape(key) + r'\s*=\s*(.+?)\s*$', t, re.M | re.I)
    return m.group(1) if m else None


def check_profile_owns_inis():
    s = os.path.join(PROFILE, 'settings.txt')
    t = io.open(s, encoding='utf-8', errors='replace').read() if os.path.exists(s) else ''
    if not re.search(r'^LocalSettings\s*=\s*true', t, re.M | re.I):
        fails.append('profile settings.txt: LocalSettings is not true - the GAME '
                     'owns the INIs and will reset them (#98)')
    for name in ('skyrim.ini', 'skyrimprefs.ini'):
        p = os.path.join(PROFILE, name)
        if not os.path.exists(p) or os.path.getsize(p) < 200:
            fails.append(f'profile {name} missing or suspiciously small')


def _same_value(got, want):
    """0.0083 and .0083 are the same setting; 384 and 3840 are not.

    An earlier version stripped trailing zeros off both sides, which made
    iSize W=384 compare equal to 3840 - a resolution reset would have passed."""
    try:
        return abs(float(got) - float(want)) < 1e-9
    except (TypeError, ValueError):
        return got.strip().lower() == want.strip().lower()


def check_deliberate_keys():
    for name, keys in DELIBERATE.items():
        p = os.path.join(PROFILE, name)
        for key, want in keys.items():
            got = ini_get(p, key)
            if got is None:
                warns.append(f'{name}: {key} absent (want {want})')
            elif not _same_value(got, want):
                fails.append(f'{name}: {key}={got}, expected {want}')


def check_plugin_state():
    """Every ledger plugin on, every off-plugin explained. Reuses install_mod.

    Exit codes, not output matching: `'0 problem(s)' in stdout` is true for
    "10 problem(s)", so the old test passed silently on 10, 20, 30 faults."""
    if game_running():
        warns.append('SkyrimSE.exe is already running - skipped the MO2 plugin and '
                     'load-order checks rather than driving MO2Headless at the same '
                     'time as a live session (#103)')
        return
    r = subprocess.run([sys.executable, os.path.join(REPO, 'audit', 'install_mod.py'),
                        '--verify'], capture_output=True, text=True, timeout=600)
    tail = (r.stdout or '').strip().splitlines()[-3:]
    if r.returncode != 0:
        fails.append('install_mod --verify is not clean: ' + ' | '.join(tail))
    r = subprocess.run([sys.executable, os.path.join(REPO, 'audit', 'verify_order.py')],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        fails.append('verify_order is not clean: ' + (r.stdout or '')[-200:])


def check_last_launch_completed():
    """Did the previous launch finish loading plugins, or die partway?

    The gate tells you SKSE will ACCEPT a DLL; it does not tell you the DLL
    survives its own init on this runtime. OAR and CRD both passed the gate and
    then hung the game mid-load (#140). The signature is unmistakable in
    skse64.log: `loading plugin "X"` with no matching listener registration and
    nothing after it. Every plugin queued behind X never loads at all, which is
    why one bad DLL looks like "everything is broken"."""
    log = os.path.join(DOCS, 'SKSE', 'skse64.log')
    if not os.path.exists(log):
        warns.append('no skse64.log - the game has never launched through SKSE')
        return
    t = io.open(log, encoding='utf-8', errors='replace').read()
    checked = re.findall(r'checking plugin (\S+)', t)
    loads = re.findall(r'loading plugin "([^"]+)"', t)
    if not loads:
        warns.append('skse64.log records no plugin loads at all')
        return
    # a completed run gets past every plugin it checked and then goes on to
    # dispatch messages / read translations
    finished = 'dispatch message' in t or 'Reading translations' in t
    if not finished:
        fails.append(f'last launch DIED while loading "{loads[-1]}" - '
                     f'{len(checked) - len(loads)} plugin(s) behind it never loaded. '
                     f'Park it before launching again (#140)')
    elif len(loads) < len(checked) - 1:      # msdia140 is a PDB helper, not a plugin
        warns.append(f'{len(checked)} plugins checked but only {len(loads)} loaded '
                     f'- verify nothing was skipped silently')


def check_steam_overlay():
    """The overlay hooks the window message loop and has hung this build."""
    warns.append('Steam overlay: cannot be verified from disk (Steam stores it '
                 'encrypted). It was in the hung main thread on 2026-08-31. '
                 'Confirm it is OFF for app 489830 before blaming a mod.')


def running(name):
    """Case-insensitive process-name test, used by several checks below."""
    r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}'],
                       capture_output=True, text=True)
    return name.lower() in (r.stdout or '').lower()


def game_running():
    return running('SkyrimSE.exe')


def check_no_competing_writer():
    """A headless MO2 mid-transaction rewrites the five profile files (#103).

    The GUI is not a fault - it is how the game gets launched - but a headless
    writer running right now means the state this gate just read can change
    before the game reads it."""
    if running('MO2Headless.exe'):
        fails.append('MO2Headless.exe is running - an assistant-side writer may '
                     'rewrite profile files under the launch (#103). Let it finish.')
    if running('ModOrganizer.exe'):
        warns.append('ModOrganizer.exe is running. Expected if this is the launcher; '
                     'a problem only if a second session is also driving it (#103).')


def check_steam_not_wedged():
    """Steam flagging the app as running with no process makes the next launch a
    silent no-op. launch_skyrim.ps1 step 3 cycles Steam to clear it."""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r'Software\Valve\Steam\Apps\489830')
        flagged = winreg.QueryValueEx(k, 'Running')[0]
    except Exception:
        return
    if flagged and not game_running():
        fails.append('STEAM-WEDGE: Steam has app 489830 flagged as running but no '
                     'SkyrimSE.exe exists. The next launch will do nothing. Cycle '
                     'Steam (launch_skyrim.ps1 step 3) first.')


def check_last_session_crash():
    """A crash log newer than skse64.log means the last session died AFTER init -
    a different failure from the mid-plugin-load death above, and one that stays
    invisible if nobody looks in the folder."""
    log = os.path.join(DOCS, 'SKSE', 'skse64.log')
    if not os.path.exists(log):
        return
    d = os.path.join(DOCS, 'SKSE')
    newer = [f for f in os.listdir(d)
             if f.startswith('crash-') and f.endswith('.log')
             and os.path.getmtime(os.path.join(d, f)) > os.path.getmtime(log)]
    if not newer:
        return
    fn = sorted(newer)[-1]
    line = ''
    for l in io.open(os.path.join(d, fn), encoding='utf-8', errors='replace'):
        if 'Unhandled exception' in l:
            line = l.strip()[:150]
            break
    warns.append(f'last session CRASHED after init: {fn}{" - " + line if line else ""}')


def check_game_side_plugin_list():
    """The 1.7.99+ runtime can read %LOCALAPPDATA%\\Skyrim Special Edition\\
    Plugins.txt, which MO2 2.5.2 does not virtualize; launch_skyrim.ps1 step 2
    seeds it from the profile for exactly that reason.

    Reported as a warning, not a gate. At the last session MO2 did redirect the
    game's own write (the profile's plugins.txt is the file that got rewritten,
    not this one), so a stale copy here is a fallback-path risk rather than
    proof that plugins are inactive. It is still the first thing to re-seed if
    a launch comes up missing content."""
    prof = os.path.join(PROFILE, 'plugins.txt')
    if not (os.path.exists(prof) and os.path.exists(GAME_SIDE)):
        return
    act = lambda p: {l.strip().lower() for l in io.open(p, encoding='utf-8',
                                                        errors='replace')
                     if l.startswith('*')}
    want, got = act(prof), act(GAME_SIDE)
    if want == got:
        return
    import datetime
    stamp = datetime.datetime.fromtimestamp(os.path.getmtime(GAME_SIDE))
    warns.append(f'game-side Plugins.txt lists {len(got)} active plugins, the profile '
                 f'{len(want)} ({len(want - got)} missing there). Last seeded '
                 f'{stamp:%Y-%m-%d %H:%M}. Re-seed with launch_skyrim.ps1 step 2 if a '
                 f'launch comes up missing content.')


def main():
    check_profile_owns_inis()
    check_deliberate_keys()
    check_no_competing_writer()
    check_plugin_state()
    check_last_launch_completed()
    check_last_session_crash()
    check_game_side_plugin_list()
    check_steam_not_wedged()
    check_steam_overlay()

    for w in warns:
        print(f'  WARN  {w}')
    for f in fails:
        print(f'  FAIL  {f}')
    if fails:
        print(f'\n{len(fails)} blocking problem(s) - DO NOT tell the user to launch')
        return 1
    print(f'\npreflight clean ({len(warns)} warning(s)) - safe to launch')
    return 0


if __name__ == '__main__':
    sys.exit(main())
