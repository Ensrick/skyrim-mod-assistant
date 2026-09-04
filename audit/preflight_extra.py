"""Preflight checks added by the 2026-09-01 hardening pass.

Kept in their own module so preflight.py stays a thin list of gates; each
function appends to the `fails` / `warns` lists it is handed and never raises.

  DLL depth sweep        an enabled mod shipping a .dll under `Plugins/` that is
                         NOT `SKSE/Plugins/` is a FAIL: SKSE never loads it and
                         the mod looks installed while being inert (the SKSE
                         strip class from the 2026-08-30 audit, F0/F7).
  profile reconciliation physical mods, modlist, plugins and ledger must agree
                         (#102). Any gap is a FAIL: an unledgered mod is
                         invisible to every ledger-only check.
  watched configs        the runtime configs that decide how the game looks and
                         feels (CS SettingsUser.json, FSMP configs.json, SSE
                         Display Tweaks INIs, Underwear.ini, ...) get the same
                         snapshot+diff trail the profile INIs already have
                         (#143 shape: a config was changed and nobody could say
                         when). List in audit/watched_configs.json.
  saves backup           before a launch the saves folder is mirrored to
                         records/save-backups/<stamp>/, newest 5 kept, skipped
                         when nothing changed since the last mirror. A harness
                         autoload once loaded a broken save twice in a row
                         (#141 comment 2026-09-01); the mirror makes "revert the
                         save" a copy instead of a loss.
  profile settings.ini   MO2 reads `settings.ini` (profile.cpp:94), NOT the
                         `settings.txt` the earlier gate checked. LocalSettings
                         must be true THERE or the game reads Documents (#143).
  claim                  the current work claim is printed so a launch never
                         starts under someone else's install.
"""
import datetime, fnmatch, glob, hashlib, io, json, os, re, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.dirname(os.path.abspath(__file__))
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = os.path.join(INSTANCE, 'profiles', 'Default')
MODS = os.path.join(INSTANCE, 'mods')
LEDGER = os.path.join(REPO, 'records', 'installed-mods.json')
WATCHLIST = os.path.join(AUDIT, 'watched_configs.json')
DOCS = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                    'Skyrim Special Edition')
SAVE_BACKUPS = os.path.join(REPO, 'records', 'save-backups')
KEEP_BACKUPS = 5
# 'warn' until the live profile's settings.ini is flipped under the claim, then
# 'fail' in the same commit - a gate that fails on state nobody has changed yet
# would only block the launches other agents are running right now.
SETTINGS_INI_GATE = 'fail'


def _stamp():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def enabled_mods():
    """Mod names with a '+' in the profile's modlist.txt (top of file = highest
    priority). '*' rows are unmanaged DLC and are skipped."""
    ml = os.path.join(PROFILE, 'modlist.txt')
    out = []
    if not os.path.exists(ml):
        return out
    for line in io.open(ml, encoding='utf-8', errors='replace'):
        line = line.rstrip('\r\n')
        if line.startswith('+'):
            out.append(line[1:])
    return out


# ------------------------------------------------------------ (i) DLL depth
def check_dll_depth(fails, warns):
    bad = []
    for name in enabled_mods():
        root = os.path.join(MODS, name)
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() not in ('fomod',)]
            for f in files:
                if not f.lower().endswith('.dll'):
                    continue
                rel = os.path.relpath(os.path.join(base, f), root)
                parts = [p.lower() for p in rel.split(os.sep)]
                # `Plugins/x.dll` at the mod root, or any `.../Plugins/x.dll`
                # whose parent is not `SKSE`, is one directory too high
                if len(parts) >= 2 and parts[-2] == 'plugins' and \
                        (len(parts) < 3 or parts[-3] != 'skse'):
                    bad.append(f'{name}\\{rel}')
    for b in bad:
        fails.append(f'DLL staged outside SKSE\\Plugins in an ENABLED mod: {b} - '
                     f'SKSE will never load it; restage the mod (audit F0/F7, #105)')


# ------------------------------------------------------------ (ii) ledger gap
def check_ledger_gap(fails, warns):
    import profile_reconcile
    result = profile_reconcile.reconcile()
    for item in result['warnings']:
        warns.append(f"profile reconcile [{item['code']}]: {item['message']}")
    for item in result['errors']:
        fails.append(f"profile reconcile [{item['code']}]: {item['message']}")


# ------------------------------------------------------ (iii) watched configs
def _expand(pattern):
    """Instance-relative glob, or absolute path / glob. `~docs~` expands to the
    Documents\\My Games\\Skyrim Special Edition folder."""
    pattern = pattern.replace('~docs~', DOCS)
    if not os.path.isabs(pattern):
        pattern = os.path.join(INSTANCE, pattern)
    return sorted(glob.glob(pattern))


def _key(path):
    """A stable, filesystem-safe name for a watched file's history entries."""
    rel = os.path.relpath(path, INSTANCE) if path.lower().startswith(INSTANCE.lower()) \
        else os.path.relpath(path, DOCS) if path.lower().startswith(DOCS.lower()) \
        else os.path.basename(path)
    return re.sub(r'[^A-Za-z0-9._-]+', '_', rel)[-120:]


def snapshot_watched_configs(fails, warns):
    if not os.path.exists(WATCHLIST):
        warns.append(f'no {os.path.relpath(WATCHLIST, REPO)} - watched-config diff skipped')
        return
    spec = json.load(io.open(WATCHLIST, encoding='utf-8'))
    hist = os.path.join(REPO, 'records', 'config-history')
    os.makedirs(hist, exist_ok=True)
    enabled = {n.lower() for n in enabled_mods()}
    stamp = _stamp()
    seen = 0
    for entry in spec.get('watch', []):
        pattern = entry['path'] if isinstance(entry, dict) else entry
        only_enabled = isinstance(entry, dict) and entry.get('enabledModsOnly', True)
        for path in _expand(pattern):
            if not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, INSTANCE)
            if only_enabled and rel.lower().startswith('mods' + os.sep):
                mod = rel.split(os.sep)[1]
                if mod.lower() not in enabled:
                    continue                  # a parked mod's config is not live
            seen += 1
            h = hashlib.sha256(io.open(path, 'rb').read()).hexdigest()[:16]
            key = _key(path)
            marker = os.path.join(hist, key + '.latest')
            prev = io.open(marker).read().strip() if os.path.exists(marker) else ''
            if h != prev:
                shutil.copy2(path, os.path.join(hist, f'{key}.{stamp}.{h}'))
                io.open(marker, 'w').write(h)
                warns.append(f'watched config changed: {rel} - archived as '
                             f'records/config-history/{key}.{stamp}.{h}'
                             + ('' if prev else ' (first snapshot)'))
    if not seen:
        warns.append('watched-config list matched no live files - check '
                     'audit/watched_configs.json')


# ------------------------------------------------------- (iv) saves backup
def saves_dir():
    st = os.path.join(PROFILE, 'settings.ini')
    local = False
    if os.path.exists(st):
        local = re.search(r'^LocalSaves\s*=\s*true', io.open(st, encoding='utf-8',
                                                             errors='replace').read(),
                          re.M | re.I) is not None
    return os.path.join(PROFILE, 'saves') if local else os.path.join(DOCS, 'Saves')


def _saves_manifest(d):
    rows = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            st = os.stat(p)
            rows.append(f'{f}|{st.st_size}|{int(st.st_mtime)}')
    return rows


def backup_saves(fails, warns):
    d = saves_dir()
    if not os.path.isdir(d):
        warns.append(f'saves folder missing: {d}')
        return
    rows = _saves_manifest(d)
    if not rows:
        warns.append(f'saves folder is empty: {d}')
        return
    digest = hashlib.sha256('\n'.join(rows).encode()).hexdigest()[:16]
    os.makedirs(SAVE_BACKUPS, exist_ok=True)
    existing = sorted(x for x in os.listdir(SAVE_BACKUPS)
                      if os.path.isdir(os.path.join(SAVE_BACKUPS, x)))
    if existing:
        m = os.path.join(SAVE_BACKUPS, existing[-1], 'manifest.json')
        if os.path.exists(m):
            try:
                if json.load(io.open(m, encoding='utf-8')).get('digest') == digest:
                    return            # nothing changed since the newest mirror
            except Exception:
                pass
    dest = os.path.join(SAVE_BACKUPS, _stamp())
    os.makedirs(dest, exist_ok=True)
    n = 0
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(dest, f))
            n += 1
    json.dump({'digest': digest, 'source': d, 'files': n,
               'at': datetime.datetime.now().isoformat()},
              io.open(os.path.join(dest, 'manifest.json'), 'w', encoding='utf-8'),
              indent=1)
    warns.append(f'saves mirrored: {n} file(s) -> records/save-backups/'
                 f'{os.path.basename(dest)}')
    # rotation: keep the newest KEEP_BACKUPS by renaming the rest aside is not
    # needed - these are our own mirrors, so the oldest are removed file by file
    existing = sorted(x for x in os.listdir(SAVE_BACKUPS)
                      if os.path.isdir(os.path.join(SAVE_BACKUPS, x)))
    for old in existing[:-KEEP_BACKUPS]:
        op = os.path.join(SAVE_BACKUPS, old)
        for f in os.listdir(op):
            try:
                os.remove(os.path.join(op, f))
            except OSError:
                pass
        try:
            os.rmdir(op)
        except OSError:
            pass


# ---------------------------------------------------- (v) profile settings.ini
def check_profile_settings_ini(fails, warns):
    """MO2 2.5.2 reads the profile's `settings.ini` for LocalSettings/LocalSaves
    (modorganizer/src/profile.cpp:94). A `settings.txt` beside it is a stray
    that nothing reads. With LocalSettings=false in settings.ini the game reads
    and rewrites the Documents INIs, which is exactly the 2026-08-31 reset (#98,
    #143). When it is true, MO2's game plugin maps the Documents INI paths onto
    the profile copies through usvfs for every launch it performs, GUI or
    headless-run."""
    # the LocalSettings value itself is gated in preflight.check_profile_owns_inis
    # (same file, same key); this covers the stray and the companion INIs
    txt = os.path.join(PROFILE, 'settings.txt')
    if os.path.exists(txt):
        warns.append('profile settings.txt exists but MO2 never reads it; the live '
                     'flag is in settings.ini (kept only so older tooling does not fail)')
    for name in ('skyrim.ini', 'skyrimprefs.ini', 'skyrimcustom.ini'):
        if not os.path.exists(os.path.join(PROFILE, name)):
            warns.append(f'profile {name} missing - MO2 GUI would pop a "missing '
                         f'profile-specific INI" dialog with LocalSettings=true')


# ------------------------------------------------------------------ (vi) claim
def report_claim(fails, warns):
    try:
        import claim
    except ImportError:
        return
    rec = claim.read()
    if rec is None:
        return
    if claim.is_stale(rec):
        warns.append(f'stale work claim on the instance: {claim.describe(rec)}')
    else:
        warns.append(f'work claim: {claim.describe(rec)} - do not launch or mutate '
                     f'under someone else\'s claim (#103)')


def run_all(fails, warns):
    for fn in (check_profile_settings_ini, check_dll_depth, check_ledger_gap,
               snapshot_watched_configs, backup_saves, report_claim):
        try:
            fn(fails, warns)
        except Exception as e:           # a broken check must not hide the others
            warns.append(f'{fn.__name__} crashed: {e!r}')


if __name__ == '__main__':
    f, w = [], []
    run_all(f, w)
    for x in w:
        print('  WARN ', x)
    for x in f:
        print('  FAIL ', x)
    print(f'\n{len(f)} fail(s), {len(w)} warning(s)')
    raise SystemExit(1 if f else 0)
