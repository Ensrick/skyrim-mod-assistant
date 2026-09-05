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
import preflight_extra   # 2026-09-01 hardening: DLL depth, ledger gap, watched configs,
                         # saves mirror, the REAL profile settings.ini, work claim
import keep_coverage     # 2026-09-02: installed implies Keep (docs/CURATION_POLICY.md)
import weapon_balance_gate  # #239: no stale or unaudited generated weapon output

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
        'fMoveLimitMass': '0',        # clutter triage 2026-09-01, player push off
        'bEnableLogging': '1',
        'fPoissonRadiusScale': '8.0',  # #151 shadow edge softness (engine default 4.0)
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
    """MO2 reads the profile's settings.ini (modorganizer/src/profile.cpp:94).

    Until 2026-09-01 this gate read `settings.txt`, a stray file nothing loads,
    and passed for a day while the real flag said false and the game kept
    reading and rewriting the Documents INIs (#98, #143). The stray is kept
    only as a marker; preflight_extra warns whenever it still exists."""
    s = os.path.join(PROFILE, 'settings.ini')
    t = io.open(s, encoding='utf-8', errors='replace').read() if os.path.exists(s) else ''
    if not re.search(r'^LocalSettings\s*=\s*true\s*$', t, re.M | re.I):
        (fails if preflight_extra.SETTINGS_INI_GATE == 'fail' else warns).append(
            'profile settings.ini: LocalSettings is not true - this is the file MO2 '
            'actually reads (profile.cpp:94); the GAME owns the INIs and will reset '
            'them (#98, #143)')
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


def _enabled_dlls_named(plugin_name):
    """DLLs in the effective tree whose SKSE version data names `plugin_name`.

    Enabled mods (modlist '+'), overwrite, and the game's own Data/SKSE/Plugins;
    the name comes from SKSEPluginVersionData via skse_version_data.parse, the
    same field skse64.log prints in `loading plugin "<name>"`."""
    import skse_version_data as V
    roots = [os.path.join(INSTANCE, 'mods', n) for n in preflight_extra.enabled_mods()]
    roots.append(os.path.join(INSTANCE, 'overwrite'))
    roots.append(os.path.join(GAME, 'Data'))
    hits = []
    for root in roots:
        d = os.path.join(root, 'SKSE', 'Plugins')
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.lower().endswith('.dll'):
                continue
            try:
                v = V.parse(os.path.join(d, f))
                name = ((v or {}).get('vd') or {}).get('name') or ''
            except Exception:
                name = ''
            if name.lower() == plugin_name.lower():
                hits.append(os.path.relpath(os.path.join(d, f), INSTANCE))
    return hits


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
        culprit = loads[-1]
        msg = (f'last launch DIED while loading "{culprit}" - '
               f'{len(checked) - len(loads)} plugin(s) behind it never loaded.')
        # Fail-closed only while the culprit is still in the effective tree: once
        # its mod is parked the same log line must not block the validation
        # launch that proves the park (2026-09-01, Light Placer re-park).
        still = _enabled_dlls_named(culprit)
        if still:
            fails.append(msg + f' It is still enabled ({still[0]}). Park it before '
                               f'launching again (#140)')
        else:
            warns.append(msg + f' No enabled mod ships a DLL named "{culprit}" now, '
                               f'so it is parked; this launch is its confirmation (#140)')
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
        if game_running():
            # the hardened launch chain spawns the game through `MO2Headless run`,
            # which stays alive (holding the instance lock, on purpose) for the
            # whole session - that is the launcher, not a competing writer
            warns.append('MO2Headless.exe is running alongside SkyrimSE.exe - the '
                         'direct launch chain holds the instance lock for the session; '
                         'no profile mutation is possible until the game exits')
        else:
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


def snapshot_inis():
    """INIs are the one non-modular piece of the build (user, 2026-09-01), so
    give them the same revertibility as mods: every time a profile INI's
    content changes, a dated copy lands in records/ini-history/ before anything
    else runs. Reverting = copying a snapshot back; the history is the diff
    trail LOOT/MO2 already provide for plugins."""
    import hashlib, shutil
    hist = os.path.join(REPO, 'records', 'ini-history')
    os.makedirs(hist, exist_ok=True)
    stamp = __import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S')
    for name in ('skyrim.ini', 'skyrimprefs.ini', 'settings.txt'):
        p = os.path.join(PROFILE, name)
        if not os.path.exists(p):
            continue
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
        marker = os.path.join(hist, f'{name}.latest')
        prev = open(marker).read().strip() if os.path.exists(marker) else ''
        if h != prev:
            shutil.copy2(p, os.path.join(hist, f'{name}.{stamp}.{h}'))
            open(marker, 'w').write(h)
            warns.append(f'{name} changed since last snapshot - archived as '
                         f'{name}.{stamp}.{h} (diff it if the change is unexplained)')


GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'


def check_game_folder_manifest():
    """The game install is build state too, and it was the blind spot: on
    2026-08-31 a mid-download kill truncated ccvsvsse004-beafarmer (bsa+esl),
    and neither the truncation nor its later .bak rename was tracked anywhere -
    the resulting hang burned 10+ launches to isolate. So: inventory every
    plugin/archive/exe in the game root and Data (name, size, mtime), diff
    against the last-known manifest, and surface every change. Steam updates,
    foreign writes, renames and truncations all show up as diffs."""
    import hashlib
    man_path = os.path.join(REPO, 'records', 'game-folder-manifest.json')
    cur = {}
    for base, exts in ((GAME, ('.exe', '.dll', '.ccc', '.ini')),
                       (os.path.join(GAME, 'Data'), ('.esm', '.esl', '.esp', '.bsa', '.bak'))):
        if not os.path.isdir(base):
            fails.append(f'game folder missing: {base}')
            return
        for f in os.listdir(base):
            p = os.path.join(base, f)
            if os.path.isfile(p) and (f.lower().endswith(exts) or '.bak' in f.lower()):
                st = os.stat(p)
                cur[f] = [st.st_size, int(st.st_mtime)]
    if os.path.exists(man_path):
        old = json.load(open(man_path, encoding='utf-8'))
        added = sorted(set(cur) - set(old))
        gone = sorted(set(old) - set(cur))
        changed = sorted(k for k in set(cur) & set(old) if cur[k] != old[k])
        for k in added:
            warns.append(f'game folder NEW file: {k} ({cur[k][0]:,} B)')
        for k in gone:
            warns.append(f'game folder file GONE: {k} (was {old[k][0]:,} B)')
        for k in changed:
            warns.append(f'game folder file CHANGED: {k} {old[k][0]:,} -> {cur[k][0]:,} B')
        if added or gone or changed:
            hist = os.path.join(REPO, 'records', 'game-folder-manifest.history.jsonl')
            with open(hist, 'a', encoding='utf-8') as fh:
                fh.write(json.dumps({'at': __import__('datetime').datetime.now().isoformat(),
                                     'added': added, 'gone': gone,
                                     'changed': {k: [old[k], cur[k]] for k in changed}}) + '\n')
    tmp = man_path + '.tmp'
    json.dump(cur, open(tmp, 'w', encoding='utf-8'), indent=0)
    os.replace(tmp, man_path)


def main():
    snapshot_inis()
    check_game_folder_manifest()
    check_profile_owns_inis()
    check_deliberate_keys()
    check_no_competing_writer()
    check_plugin_state()
    check_last_launch_completed()
    check_last_session_crash()
    check_game_side_plugin_list()
    check_steam_not_wedged()
    check_steam_overlay()
    preflight_extra.run_all(fails, warns)
    keep_coverage.run(fails, warns)
    weapon_balance_gate.run(fails, warns, repo=REPO, instance=INSTANCE,
                            profile='Default')

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
