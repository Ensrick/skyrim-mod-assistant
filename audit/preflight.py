"""Everything that must be true BEFORE the user is told to launch.

Born 2026-09-01 after three consecutive broken launches, each caused by state
the assistant owned and never checked: INIs reset to 1080p windowed, DLLs
unparked on a version-gate pass alone, and plugins silently unstarred. The user:
"You're going to need to monitor this shit."

Exit 0 = safe to launch. Non-zero = do not tell the user to launch.

  py -3 audit/preflight.py
"""
import argparse, contextlib, datetime, hashlib, io, json, os, re, secrets, subprocess, sys, tempfile, threading, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preflight_extra   # 2026-09-01 hardening: DLL depth, ledger gap, watched configs,
                         # saves mirror, the REAL profile settings.ini, work claim
import keep_coverage     # 2026-09-02: installed implies Keep (docs/CURATION_POLICY.md)
import claim

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


def _game_folder_inventory():
    """Return an exact, path-stable inventory of runtime-bearing game files.

    Basenames are not identities: ``Data/foo.dll`` and ``foo.dll`` are distinct
    files.  Size and mtime are useful diagnostics, but only a content digest can
    detect an in-place same-size rewrite or local corruption whose timestamp was
    preserved.  The game root is restricted to runtime/config extensions, while
    physical ``Data`` is recursive and intentionally includes every file: loose
    SKSE DLLs/configs, scripts and other nested payloads are just as capable of
    changing the build as top-level plugins and archives.
    """
    cur = {}
    game_root = os.path.realpath(GAME)
    data_root = os.path.join(GAME, 'Data')
    for required in (GAME, data_root):
        if not os.path.isdir(required):
            raise FileNotFoundError(f'game folder missing: {required}')

    candidates = []
    root_exts = ('.exe', '.dll', '.ccc', '.ini')
    for name in sorted(os.listdir(GAME), key=str.casefold):
        path = os.path.join(GAME, name)
        if (os.path.isfile(path) and
                (name.casefold().endswith(root_exts) or '.bak' in name.casefold())):
            candidates.append(path)

    is_junction = getattr(os.path, 'isjunction', lambda _path: False)
    for base, dirs, files in os.walk(data_root, topdown=True, followlinks=False):
        dirs.sort(key=str.casefold)
        files.sort(key=str.casefold)
        for name in dirs:
            path = os.path.join(base, name)
            if os.path.islink(path) or is_junction(path):
                raise ValueError(
                    f'game Data contains a linked directory that cannot be '
                    f'inventoried canonically: {path}')
        candidates.extend(os.path.join(base, name) for name in files)

    for path in candidates:
        if os.path.islink(path) or is_junction(path):
            raise ValueError(
                f'game runtime path is linked and not a canonical physical file: {path}')
        resolved = os.path.realpath(path)
        try:
            contained = (os.path.normcase(os.path.commonpath(
                [game_root, resolved])) == os.path.normcase(game_root))
        except ValueError:
            contained = False
        if not contained:
            raise ValueError(f'game runtime path escapes the game folder: {path}')
        before = os.stat(path)
        if not os.path.isfile(path):
            raise OSError(f'game runtime entry is not a regular file: {path}')
        digest = hashlib.sha256()
        with open(path, 'rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        after = os.stat(path)
        if (before.st_size, before.st_mtime_ns) != \
                (after.st_size, after.st_mtime_ns):
            raise OSError(f'game runtime file changed while hashing: {path}')
        relative = os.path.relpath(path, GAME).replace('\\', '/').casefold()
        if relative in cur:
            raise ValueError(f'duplicate normalized game runtime path: {relative}')
        cur[relative] = {
            'bytes': after.st_size,
            'mtimeNs': after.st_mtime_ns,
            'sha256': digest.hexdigest().upper(),
        }
    return cur


def _game_folder_delta(old, cur):
    return (
        sorted(set(cur) - set(old)),
        sorted(set(old) - set(cur)),
        sorted(key for key in set(cur) & set(old)
               if (cur[key].get('bytes'), cur[key].get('sha256')) !=
                  (old[key].get('bytes'), old[key].get('sha256'))),
    )


def _valid_game_folder_manifest(document):
    if not isinstance(document, dict):
        raise ValueError('manifest root is not an object')
    if document.get('schemaVersion') != 2:
        raise ValueError('manifest schemaVersion must be 2 (exact relative paths + SHA-256)')
    if document.get('algorithm') != 'sha256':
        raise ValueError('manifest algorithm must be sha256')
    files = document.get('files')
    if not isinstance(files, dict):
        raise ValueError('manifest files must be an object')
    for relative, value in files.items():
        if (not isinstance(relative, str) or not relative or
                relative != relative.casefold() or '\\' in relative or
                os.path.isabs(relative) or '..' in relative.split('/')):
            raise ValueError(f'manifest contains a non-canonical relative path: {relative!r}')
        if not isinstance(value, dict):
            raise ValueError(f'manifest entry is not an object: {relative}')
        size = value.get('bytes')
        mtime_ns = value.get('mtimeNs')
        digest = value.get('sha256')
        if (not isinstance(size, int) or isinstance(size, bool) or size < 0 or
                not isinstance(mtime_ns, int) or isinstance(mtime_ns, bool) or
                mtime_ns < 0 or not isinstance(digest, str) or
                not re.fullmatch(r'[0-9A-F]{64}', digest)):
            raise ValueError(
                f'manifest entry must contain non-negative bytes/mtimeNs and SHA-256: {relative}')
    return files


def _atomic_write_bytes(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = (path + f'.{os.getpid()}.{secrets.token_hex(8)}.tmp')
    try:
        with open(tmp, 'xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def _game_manifest_acceptance_mutex(timeout=30):
    """Serialize complete baseline+history transactions across processes.

    The directory create is the atomic lock operation. Its PID creation
    identity makes a lock left by a dead acceptor recoverable; a unique token
    prevents an old owner from deleting a successor's lock during cleanup.
    """
    lock_dir = os.path.join(
        REPO, 'records', 'game-folder-manifest.acceptance.lock')
    owner_path = os.path.join(lock_dir, 'owner.json')
    token = secrets.token_hex(16)
    deadline = time.monotonic() + max(0.1, float(timeout))
    while True:
        try:
            os.makedirs(os.path.dirname(lock_dir), exist_ok=True)
            os.mkdir(lock_dir)
            with open(owner_path, 'x', encoding='utf-8') as stream:
                json.dump({
                    'schemaVersion': 1, 'token': token, 'pid': os.getpid(),
                    'pidStarted': claim.pid_start_identity(os.getpid()),
                    'createdUtc': datetime.datetime.now(datetime.timezone.utc)
                        .strftime('%Y-%m-%dT%H:%M:%SZ'),
                }, stream)
                stream.flush()
                os.fsync(stream.fileno())
            break
        except FileExistsError:
            stale = False
            try:
                with open(owner_path, encoding='utf-8') as stream:
                    owner = json.load(stream)
                stale = not claim.pid_alive(owner.get('pid'))
                expected = owner.get('pidStarted')
                actual = claim.pid_start_identity(owner.get('pid'))
                if expected and actual and str(expected) != str(actual):
                    stale = True
            except (OSError, ValueError, json.JSONDecodeError):
                try:
                    stale = time.time() - os.path.getmtime(lock_dir) > 5
                except OSError:
                    continue
            if stale:
                retired = lock_dir + f'.stale.{os.getpid()}.{secrets.token_hex(8)}'
                try:
                    os.rename(lock_dir, retired)
                    retired_owner = os.path.join(retired, 'owner.json')
                    if os.path.exists(retired_owner):
                        os.unlink(retired_owner)
                    os.rmdir(retired)
                except (FileNotFoundError, OSError):
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError('timed out waiting for game-manifest acceptance lock')
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            with open(owner_path, encoding='utf-8') as stream:
                owner = json.load(stream)
            if secrets.compare_digest(str(owner.get('token') or ''), token):
                os.unlink(owner_path)
                os.rmdir(lock_dir)
        except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
            pass


def _manifest_bytes(document):
    return (json.dumps(document, indent=0, sort_keys=True) + '\n').encode('utf-8')


def _write_game_folder_manifest(path, document):
    _atomic_write_bytes(path, _manifest_bytes(document))


def _file_snapshot(path):
    return (True, open(path, 'rb').read()) if os.path.exists(path) else (False, b'')


def _write_game_folder_history(path, before, event):
    """Atomically append an event, provided history still has exact before-bytes."""
    if _file_snapshot(path) != before:
        raise OSError('game folder acceptance history changed concurrently')
    prior = before[1]
    if prior:
        try:
            text = prior.decode('utf-8')
            if not text.endswith('\n'):
                raise ValueError('last line is incomplete')
            for line in text.splitlines():
                if line.strip() and not isinstance(json.loads(line), dict):
                    raise ValueError('history row is not an object')
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise OSError(f'game folder acceptance history is unreadable: {exc}')
    desired = prior + (json.dumps(event, sort_keys=True) + '\n').encode('utf-8')
    _atomic_write_bytes(path, desired)
    return True, desired


def _restore_snapshot_if_current(path, before, expected):
    """Restore exact before-bytes without overwriting a concurrent writer."""
    current = _file_snapshot(path)
    if current == before:
        return
    if current != expected:
        raise OSError(f'refusing rollback because {path} changed concurrently')
    if before[0]:
        _atomic_write_bytes(path, before[1])
    else:
        os.unlink(path)


def _valid_issue_reference(value):
    value = str(value or '').strip()
    return bool(
        re.fullmatch(r'#?\d+', value)
        or re.fullmatch(r'https://github\.com/[^/]+/[^/]+/issues/\d+', value,
                        re.IGNORECASE)
    )


def check_game_folder_manifest(acceptance=None, _acceptance_locked=False):
    """The game install is build state too, and it was the blind spot: on
    2026-08-31 a mid-download kill truncated ccvsvsse004-beafarmer (bsa+esl),
    and neither the truncation nor its later .bak rename was tracked anywhere -
    the resulting hang burned 10+ launches to isolate. So: inventory every
    plugin/archive/exe in the game root and Data (relative path, exact SHA-256;
    size and nanosecond mtime are retained as diagnostics), diff
    against the last-known manifest, and surface every change. Steam updates,
    foreign writes, renames and truncations all show up as diffs.

    Ordinary preflight is read-only: any missing or changed baseline fails
    closed. A reviewed change advances the baseline only through the explicit
    ``--accept-game-folder-baseline ISSUE`` maintenance command."""
    if acceptance is not None and not _valid_issue_reference(acceptance):
        fails.append('refusing to update the game folder baseline without an '
                     'issue number or GitHub issue URL')
        return False
    if acceptance is not None and not _acceptance_locked:
        try:
            with _game_manifest_acceptance_mutex():
                return check_game_folder_manifest(
                    acceptance=acceptance, _acceptance_locked=True)
        except (OSError, TimeoutError, ValueError) as exc:
            fails.append(f'could not lock game folder baseline acceptance: {exc}')
            return False
    man_path = os.path.join(REPO, 'records', 'game-folder-manifest.json')
    transaction_path = os.path.join(
        REPO, 'records', 'game-folder-manifest.acceptance-pending.json')
    if os.path.exists(transaction_path):
        fails.append('game folder baseline has an incomplete acceptance transaction: '
                     f'{transaction_path}; baseline/history are not trusted until the '
                     'recorded transaction is recovered')
        return False
    try:
        cur = _game_folder_inventory()
    except (OSError, ValueError) as exc:
        fails.append(str(exc))
        return False

    old = None
    legacy = False
    if os.path.exists(man_path):
        try:
            with open(man_path, encoding='utf-8') as stream:
                document = json.load(stream)
            try:
                old = _valid_game_folder_manifest(document)
            except ValueError:
                # The former basename->[size,mtime] format cannot prove exact
                # bytes and may contain collisions. It is never silently trusted
                # or replaced; an issue-bound acceptance is the migration gate.
                if (isinstance(document, dict) and document and all(
                        isinstance(value, list) and len(value) == 2
                        for value in document.values())):
                    legacy = True
                    old = None
                else:
                    raise
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            fails.append(f'game folder baseline is unreadable: {man_path}: {exc}; '
                         'refusing to replace it')
            return False

    if legacy and acceptance is None:
        fails.append('game folder baseline uses the legacy basename/size/mtime '
                     'format, which cannot prove exact runtime bytes; inspect the '
                     'current install and migrate it explicitly with '
                     '`py -3 audit/preflight.py --accept-game-folder-baseline ISSUE`')
        return False

    if old is None:
        if acceptance is None:
            fails.append('game folder baseline is missing; inspect the current install, '
                         'then create it explicitly with '
                         '`py -3 audit/preflight.py '
                         '--accept-game-folder-baseline ISSUE`')
            return False
        added, gone, changed = sorted(cur), [], []
    else:
        added, gone, changed = _game_folder_delta(old, cur)

    if acceptance is None:
        for key in added:
            fails.append(f'game folder NEW file: {key} ({cur[key]["bytes"]:,} B)')
        for key in gone:
            fails.append(f'game folder file GONE: {key} (was {old[key]["bytes"]:,} B)')
        for key in changed:
            fails.append(f'game folder file CHANGED: {key} '
                         f'{old[key]["bytes"]:,} -> {cur[key]["bytes"]:,} B; '
                         f'SHA-256 {old[key]["sha256"][:12]} -> '
                         f'{cur[key]["sha256"][:12]}')
        if added or gone or changed:
            fails.append('game folder baseline differs; investigate the change and '
                         'leave the baseline unchanged until explicitly accepted with '
                         '`py -3 audit/preflight.py '
                         '--accept-game-folder-baseline ISSUE`')
            return False
        return True

    if not (added or gone or changed):
        warns.append('game folder baseline already matches; nothing was updated')
        return True

    history_path = os.path.join(
        REPO, 'records', 'game-folder-manifest.history.jsonl')
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    event = {
        'at': datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'acceptedByIssue': str(acceptance).strip(),
        'baselineMissing': old is None and not legacy,
        'legacyBaselineMigrated': legacy,
        'added': added,
        'gone': gone,
        'changed': {
            key: [old[key], cur[key]] for key in changed
        },
    }
    baseline = {
        'schemaVersion': 2,
        'algorithm': 'sha256',
        'files': cur,
    }
    baseline_before = _file_snapshot(man_path)
    history_before = _file_snapshot(history_path)
    baseline_after = (True, _manifest_bytes(baseline))
    history_after = (True, history_before[1] +
                     (json.dumps(event, sort_keys=True) + '\n').encode('utf-8'))
    marker = {
        'schemaVersion': 1,
        'acceptedByIssue': str(acceptance).strip(),
        'baselineBeforeSha256': hashlib.sha256(baseline_before[1]).hexdigest().upper()
            if baseline_before[0] else None,
        'baselineAfterSha256': hashlib.sha256(baseline_after[1]).hexdigest().upper(),
        'historyBeforeSha256': hashlib.sha256(history_before[1]).hexdigest().upper()
            if history_before[0] else None,
        'historyAfterSha256': hashlib.sha256(history_after[1]).hexdigest().upper(),
    }
    try:
        _atomic_write_bytes(transaction_path, _manifest_bytes(marker))
        # History can never claim an acceptance whose baseline write failed:
        # baseline publishes first, then an atomic whole-history replacement.
        _write_game_folder_manifest(man_path, baseline)
        actual_history_after = _write_game_folder_history(
            history_path, history_before, event)
        if actual_history_after != history_after:
            raise OSError('history writer produced unexpected acceptance bytes')
        os.unlink(transaction_path)
    except BaseException as exc:
        rollback_errors = []
        for path, before, expected in (
                (history_path, history_before, history_after),
                (man_path, baseline_before, baseline_after)):
            try:
                _restore_snapshot_if_current(path, before, expected)
            except OSError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        if not rollback_errors:
            try:
                if os.path.exists(transaction_path):
                    os.unlink(transaction_path)
            except OSError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        message = f'could not accept game folder baseline: {exc}'
        if rollback_errors:
            message += ('; rollback incomplete and transaction marker retained: ' +
                        '; '.join(rollback_errors))
        fails.append(message)
        return False
    warns.append('accepted game folder baseline under '
                 f'{str(acceptance).strip()}: {len(added)} added, '
                 f'{len(gone)} gone, {len(changed)} changed')
    return True


def selftest():
    """Exercise exact inventory and fail-closed baseline migration in scratch."""
    global GAME, REPO
    original_game, original_repo = GAME, REPO
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    try:
        with tempfile.TemporaryDirectory(prefix='preflight-game-manifest-') as raw:
            root = os.path.join(raw, 'game')
            data = os.path.join(root, 'Data')
            repo = os.path.join(raw, 'repo')
            os.makedirs(data)
            os.makedirs(os.path.join(repo, 'records'))
            GAME, REPO = root, repo
            root_dll = os.path.join(root, 'same.bak')
            data_dll = os.path.join(data, 'same.bak')
            with open(root_dll, 'wb') as stream:
                stream.write(b'ROOT')
            with open(data_dll, 'wb') as stream:
                stream.write(b'DATA')
            stamp = 1_700_000_000_000_000_000
            os.utime(root_dll, ns=(stamp, stamp))
            os.utime(data_dll, ns=(stamp, stamp))
            first = _game_folder_inventory()
            check(set(first) == {'same.bak', 'data/same.bak'},
                  'root/Data basename collision was not preserved')
            with open(data_dll, 'wb') as stream:
                stream.write(b'EVIL')
            os.utime(data_dll, ns=(stamp, stamp))
            second = _game_folder_inventory()
            check(first != second and
                  first['data/same.bak']['sha256'] != second['data/same.bak']['sha256'],
                  'same-size/same-mtime content rewrite was not detected')

            nested = os.path.join(data, 'SKSE', 'Plugins')
            os.makedirs(nested)
            rogue = os.path.join(nested, 'rogue.dll')
            with open(rogue, 'wb') as stream:
                stream.write(b'GOOD')
            os.utime(rogue, ns=(stamp, stamp))
            third = _game_folder_inventory()
            rogue_key = 'data/skse/plugins/rogue.dll'
            check(rogue_key in third and
                  _game_folder_delta(second, third)[0] == [rogue_key],
                  'nested physical Data DLL was absent from the manifest delta')
            with open(rogue, 'wb') as stream:
                stream.write(b'EVIL')
            os.utime(rogue, ns=(stamp, stamp))
            fourth = _game_folder_inventory()
            check(third[rogue_key]['bytes'] == fourth[rogue_key]['bytes'] and
                  third[rogue_key]['mtimeNs'] == fourth[rogue_key]['mtimeNs'] and
                  third[rogue_key]['sha256'] != fourth[rogue_key]['sha256'],
                  'same-size/same-mtime nested DLL rewrite was not detected')

            manifest = os.path.join(repo, 'records', 'game-folder-manifest.json')
            with open(manifest, 'w', encoding='utf-8') as stream:
                json.dump({'same.bak': [4, 1700000000]}, stream)
            legacy_bytes = open(manifest, 'rb').read()
            fails.clear(); warns.clear()
            check(not check_game_folder_manifest(), 'legacy manifest passed ordinary preflight')
            check(open(manifest, 'rb').read() == legacy_bytes,
                  'ordinary preflight rewrote the legacy baseline')
            fails.clear(); warns.clear()
            check(check_game_folder_manifest(acceptance='#235'),
                  'issue-bound legacy migration failed')
            migrated = json.load(open(manifest, encoding='utf-8'))
            check(migrated.get('schemaVersion') == 2 and
                  set(migrated.get('files', {})) == {
                      'same.bak', 'data/same.bak', rogue_key},
                  'migration did not write the exact schema')
            fails.clear(); warns.clear()
            check(check_game_folder_manifest(), 'exact baseline did not pass unchanged')
            baseline_bytes = open(manifest, 'rb').read()
            os.utime(data_dll, ns=(stamp + 1_000_000_000,
                                   stamp + 1_000_000_000))
            fails.clear(); warns.clear()
            check(check_game_folder_manifest(),
                  'diagnostic-only mtime drift changed runtime identity')
            check(open(manifest, 'rb').read() == baseline_bytes,
                  'mtime-only check rewrote the accepted baseline')
            with open(data_dll, 'wb') as stream:
                stream.write(b'DATA')
            os.utime(data_dll, ns=(stamp, stamp))
            fails.clear(); warns.clear()
            check(not check_game_folder_manifest(),
                  'same-size/same-mtime post-baseline change passed')
            check(open(manifest, 'rb').read() == baseline_bytes,
                  'drift check rewrote the accepted baseline')

            history = os.path.join(
                repo, 'records', 'game-folder-manifest.history.jsonl')
            transaction = os.path.join(
                repo, 'records', 'game-folder-manifest.acceptance-pending.json')
            history_bytes = open(history, 'rb').read()
            real_manifest_writer = globals()['_write_game_folder_manifest']
            real_history_writer = globals()['_write_game_folder_history']
            try:
                def fail_baseline(*_args, **_kwargs):
                    raise OSError('injected baseline publication failure')

                globals()['_write_game_folder_manifest'] = fail_baseline
                fails.clear(); warns.clear()
                check(not check_game_folder_manifest(acceptance='#235'),
                      'failed baseline publication reported acceptance')
                check(open(manifest, 'rb').read() == baseline_bytes and
                      open(history, 'rb').read() == history_bytes and
                      not os.path.exists(transaction),
                      'baseline failure published history or changed authority bytes')

                globals()['_write_game_folder_manifest'] = real_manifest_writer

                def fail_history(*_args, **_kwargs):
                    raise OSError('injected history publication failure')

                globals()['_write_game_folder_history'] = fail_history
                fails.clear(); warns.clear()
                check(not check_game_folder_manifest(acceptance='#235'),
                      'failed history publication reported acceptance')
                check(open(manifest, 'rb').read() == baseline_bytes and
                      open(history, 'rb').read() == history_bytes and
                      not os.path.exists(transaction),
                      'history failure did not roll the baseline back exactly')
            finally:
                globals()['_write_game_folder_manifest'] = real_manifest_writer
                globals()['_write_game_folder_history'] = real_history_writer

            with open(transaction, 'w', encoding='utf-8') as stream:
                stream.write('{}\n')
            fails.clear(); warns.clear()
            check(not check_game_folder_manifest(),
                  'incomplete acceptance transaction did not fail closed')
            check(open(manifest, 'rb').read() == baseline_bytes,
                  'incomplete transaction check mutated the baseline')
            os.unlink(transaction)

            entered = threading.Event()
            thread_errors = []

            def competing_acceptor():
                try:
                    with _game_manifest_acceptance_mutex(timeout=3):
                        entered.set()
                except BaseException as exc:
                    thread_errors.append(exc)

            with _game_manifest_acceptance_mutex(timeout=3):
                waiter = threading.Thread(target=competing_acceptor)
                waiter.start()
                time.sleep(0.15)
                check(not entered.is_set(),
                      'two game-manifest acceptance transactions entered concurrently')
            waiter.join(timeout=3)
            check(entered.is_set() and not waiter.is_alive() and not thread_errors,
                  'waiting game-manifest acceptor did not enter after serialization')

            lock_dir = os.path.join(
                repo, 'records', 'game-folder-manifest.acceptance.lock')
            os.mkdir(lock_dir)
            with open(os.path.join(lock_dir, 'owner.json'), 'w', encoding='utf-8') as stream:
                json.dump({'schemaVersion': 1, 'token': 'dead', 'pid': 999999999,
                           'pidStarted': 'dead'}, stream)
            recovered = False
            with _game_manifest_acceptance_mutex(timeout=3):
                recovered = True
            check(recovered and not os.path.exists(lock_dir),
                  'dead acceptance mutex was not recovered and cleaned')
    finally:
        GAME, REPO = original_game, original_repo
        fails.clear(); warns.clear()
    print(f'preflight game-manifest selftest PASS ({checks} assertions)')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('play', 'test-harness'), default='play',
                        help='ordinary play requires technical-pass; the isolated '
                             'test harness may launch a pending plan')
    parser.add_argument('--accept-game-folder-baseline',
                        '--update-game-folder-baseline', dest='baseline_issue',
                        metavar='ISSUE',
                        help='explicitly accept the inspected game-folder inventory; '
                             'requires an issue number or GitHub issue URL')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args(argv)
    fails.clear()
    warns.clear()
    if args.selftest:
        return selftest()
    if args.baseline_issue is not None:
        if not _valid_issue_reference(args.baseline_issue):
            parser.error('--accept-game-folder-baseline requires an issue number '
                         '(for example 235 or #235) or a GitHub issue URL')
        active = []
        if game_running():
            active.append('SkyrimSE.exe')
        if running('MO2Headless.exe'):
            active.append('MO2Headless.exe')
        if active:
            fails.append('refusing to update the game folder baseline while running: '
                         + ', '.join(active))
        else:
            check_game_folder_manifest(acceptance=args.baseline_issue)
        for warning in warns:
            print(f'  WARN  {warning}')
        for failure in fails:
            print(f'  FAIL  {failure}')
        if fails:
            print(f'\n{len(fails)} blocking problem(s) - baseline unchanged')
            return 1
        print('\ngame folder baseline accepted; run ordinary preflight before launch')
        return 0
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
    try:
        import verification_status
        verification_status.run(fails, warns, mode=args.mode)
    except Exception as exc:
        fails.append(f'verification status gate failed to load: {type(exc).__name__}: {exc}')

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
