"""Install a Nexus mod through the headless MO2 controller and record it.

One path in and out: download from Nexus, install transactionally into the MO2
instance, enable it, then append to the ledger. Nothing is copied into the game
folder by hand, so every installed mod stays reversible through MO2's
transaction journal and visible in one file.

  py -3 audit/install_mod.py 12604 "SkyUI"
  py -3 audit/install_mod.py 12604 "SkyUI" --prefer "2K"     # pick a file variant
  py -3 audit/install_mod.py --list                          # show the ledger
  py -3 audit/install_mod.py --sort                          # LOOT sort, then re-enable
  py -3 audit/install_mod.py 27962 "Skyrim Unbound Reborn" --plan records/fomod-plans/x.json

Order matters after a LOOT sort: LootCLI rewrites plugins.txt and drops the
enable markers on managed plugins, so plugin-enable has to run afterwards.
`--verify` re-checks that every ledger plugin is still enabled.

Ledger conventions for things that are OFF ON PURPOSE. `--verify` is a gate
that must read `0 problem(s)`; a standing false positive trains everyone to
skim the one line where a real regression appears, so intent has to be
machine-readable, not just prose in `note`:

  "enabled": false          the whole mod is parked. Its plugins are expected
                            to be inactive; one that IS active fails instead.

  "disabledPlugins": [...]  the mod is enabled but these specific plugins are
                            deliberately unstarred - a patch whose target is
                            absent, a variant superseded by another mod, an
                            asset-only install whose ESP must not load. They
                            are reported as `deliberately-disabled`, are not
                            counted as problems, and `sort_order()` will not
                            re-enable them. One that IS active fails instead.

Always give the reason in `note` as well; the field says WHAT, the note says
WHY. A plugin that is off with neither marker is a fault by definition - that
is the whole point of the check, and it is how a disabled CBBE.esp was caught
on 2026-08-31 after a bookkeeping explanation had nearly buried it.
"""
import json, os, re, sys, hashlib, subprocess, datetime

SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SP)
sys.path.insert(0, SP)

INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = 'Default'
MO2 = os.path.join(INSTANCE, 'MO2Headless.exe')
LEDGER = os.path.join(REPO, 'records', 'installed-mods.json')


def mo2(*args, root=INSTANCE):
    cmd = [MO2, '--root', root] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    raw = (p.stdout or p.stderr or '').strip()
    try:
        return json.loads(raw.splitlines()[-1])
    except Exception:
        return {'ok': False, 'raw': raw[:400]}


def load():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding='utf-8'))
    return {'schemaVersion': 1, 'instance': INSTANCE, 'profile': PROFILE, 'mods': []}


def save(led):
    led['mods'].sort(key=lambda m: m['modName'].lower())
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    tmp = LEDGER + '.tmp'
    json.dump(led, open(tmp, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    os.replace(tmp, LEDGER)


def plugins_of(mod_name):
    d = os.path.join(INSTANCE, 'mods', mod_name)
    return sorted(f for f in os.listdir(d)
                  if f.lower().endswith(('.esp', '.esm', '.esl'))) if os.path.isdir(d) else []


def install(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None):
    import modasset as M
    if file_id:
        # an exact, dossier-verified file: never re-pick, because pick_file only
        # scans MAIN and would silently choose a different (or newer) variant
        files = M.v1(f'/mods/{mid}/files.json')['files']
        f = next((x for x in files if x['file_id'] == file_id), None)
        if not f:
            print(f'mod {mid}: no file {file_id}'); return 1
    else:
        f = M.pick_file(mid, prefer=prefer)
    archive = M.download(mid, f)
    sha = hashlib.sha256(open(archive, 'rb').read()).hexdigest()

    args = ['mod-install', archive, mod_name, '--enable']
    if replace:
        args += ['--replace']
    if plan:
        args += ['--install-plan', os.path.abspath(plan)]
    res = mo2(*args)
    if not res.get('ok'):
        print('install failed:', res); return 1
    print(f"installed {mod_name}  transaction {res.get('transaction')}")

    added = plugins_of(mod_name)
    for p in added:
        r = mo2('plugin-enable', p)
        print(f"   plugin {p}: {'enabled' if r.get('ok') else r}")

    led = load()
    # an update replaces the old ledger row for the same mod folder, not just
    # a re-download of the identical file
    led['mods'] = [m for m in led['mods']
                   if m.get('fileId') != f['file_id']
                   and not (replace and m.get('modName') == mod_name)]
    led['mods'].append({
        'modId': mid, 'modName': mod_name,
        'nexusName': f['name'], 'version': f.get('version'),
        'fileId': f['file_id'], 'fileName': f['file_name'],
        'sizeMb': round(f['size_kb'] / 1024, 2), 'sha256': sha,
        'plugins': added, 'enabled': True,
        'installedUtc': datetime.datetime.now(datetime.timezone.utc)
                                 .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'transaction': res.get('transaction'),
        **({'fomodPlan': plan} if plan else {}),
    })
    save(led)
    print(f'ledger now holds {len(led["mods"])} mods -> {LEDGER}')
    return 0


def verify():
    led = load()
    state = mo2('plugin-list')
    live = {p['name']: p['enabled'] for p in state.get('plugins', [])}
    print(f"{len(led['mods'])} mods in ledger; {state.get('discoveredCount')} plugins discovered\n")
    bad = 0
    off_on_purpose = []          # (mod, plugin, why) - expected off, never a fault
    faults = []                  # the rows that actually matter
    for m in led['mods']:
        for p in m['plugins']:
            ok = live.get(p)
            flag = 'enabled' if ok else ('DISABLED' if p in live else 'MISSING')
            if not m.get('enabled'):
                # parked mod: its plugins are expected to be undiscovered
                flag = 'parked' if not ok else 'ACTIVE-WHILE-PARKED'
                if ok:
                    bad += 1
                    faults.append((m['modName'], p, flag))
                else:
                    off_on_purpose.append((m['modName'], p, 'mod parked'))
            elif p in m.get('disabledPlugins', []):
                # deliberately unstarred (e.g. its master is not installed)
                flag = 'deliberately-disabled' if not ok else 'ACTIVE-BUT-MARKED-DISABLED'
                if ok:
                    bad += 1
                    faults.append((m['modName'], p, flag))
                else:
                    off_on_purpose.append((m['modName'], p, 'listed in disabledPlugins'))
            elif not ok:
                bad += 1
                faults.append((m['modName'], p, flag))
            print(f"   {m['modName']:<28}{p:<28}{flag}")
        if not m['plugins']:
            print(f"   {m['modName']:<28}{'(no plugin)':<28}-")
    # An off-on-purpose row is intent, not a fault, so it is summarised
    # separately and never reaches the problem total. Anything off WITHOUT one
    # of those two markers is a fault - see the ledger conventions at the top.
    print(f'\ndeliberately off ({len(off_on_purpose)}):'
          if off_on_purpose else '\ndeliberately off (0)')
    for mod, p, why in off_on_purpose:
        print(f'   {mod:<28}{p:<28}{why}')
    if faults:
        print(f'\nfaults ({len(faults)}):')
        for mod, p, flag in faults:
            print(f'   {mod:<28}{p:<28}{flag}')
    print(f'\n{bad} problem(s)')
    return 1 if bad else 0


def sort_order():
    """Sort with LootCLI through MO2's VFS, then restore enable markers.

    LootCLI rewrites plugins.txt and drops the '*' on managed plugins, so the
    re-enable is not optional housekeeping - skip it and the mods you just
    installed are silently inactive.

    The restore is driven by what was ACTIVE before the sort, not by the ledger.
    Driving it from the ledger silently disabled every plugin whose mod had no
    ledger row - it cost the Legacy of Ysgramor stack once and the 559-record
    Ensrick Lux Water CS patch a second time, both discovered only by accident.
    A hand-made patch or a locally built overlay legitimately has no ledger row,
    so the ledger is the wrong authority for "should this be on"."""
    plugins = os.path.join(INSTANCE, 'profiles', PROFILE, 'plugins.txt')
    out = os.path.join(INSTANCE, 'loot-report.json')
    game = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
    # `--` does not survive `pwsh -File`; PowerShell then tries to bind --game
    # as a parameter name. Pass the tool arguments as an explicit array instead.
    def q(s):
        return "'" + str(s).replace("'", "''") + "'"
    targs = ','.join(q(x) for x in ['--game', 'SkyrimSE', '--gamePath', game,
                                    '--pluginListPath', plugins, '--out', out])
    # snapshot the pre-sort active set: this, not the ledger, decides what gets
    # its marker back afterwards
    state = mo2('plugin-list')
    was_active = {p['name'] for p in state.get('plugins', []) if p.get('enabled')}
    if not was_active:
        print('refusing to sort: could not read the pre-sort active set, and '
              'sorting without it would drop every enable marker')
        return 1
    script = (f"& {q(os.path.join(REPO, 'run-through-mo2.ps1'))} -Tool loot "
              f"-Profile {q(PROFILE)} -Instance {q(INSTANCE)} -TimeoutSeconds 900 "
              f"-ToolArguments @({targs})")
    p = subprocess.run(['pwsh', '-NoProfile', '-Command', script],
                       capture_output=True, text=True, timeout=1200, cwd=REPO)
    print('loot exit', p.returncode)
    if p.returncode != 0:
        print((p.stdout or p.stderr)[-500:])
        return 1
    led = load()
    # everything that was active before the sort goes back on, full stop. A
    # plugin that was deliberately off is by definition not in the snapshot, so
    # no ledger row gets a say here - a stale parked row must never be able to
    # force a live plugin off (process audit 2026-08-30, F2)
    failed = []
    for pl in sorted(was_active):
        r = mo2('plugin-enable', pl)
        if not r.get('ok'):
            failed.append((pl, r))
    # anything newly installed this run is not in the snapshot; the ledger is
    # the right authority for those, since they have never been active before
    deliberate = {pl for m in led['mods']
                  for pl in (m.get('disabledPlugins', []) if m.get('enabled')
                             else m.get('plugins', []))}
    fresh = [pl for m in led['mods'] if m.get('enabled')
             for pl in m['plugins']
             if pl not in was_active and pl not in deliberate]
    for pl in fresh:
        r = mo2('plugin-enable', pl)
        if not r.get('ok'):
            failed.append((pl, r))
    # prove it: the post-sort active set must contain the pre-sort one
    after = {p['name'] for p in mo2('plugin-list').get('plugins', []) if p.get('enabled')}
    lost = sorted(was_active - after)
    print(f'sorted, then restored {len(was_active)} previously active plugins '
          f'and enabled {len(fresh)} newly installed one(s)')
    for pl, r in failed:
        print(f'   ENABLE FAILED {pl}: {r}')
    if lost:
        print(f'   LOST AFTER SORT ({len(lost)}): ' + ', '.join(lost))
    rc = verify()
    return 1 if (failed or lost) else rc


def show():
    led = load()
    print(f"{len(led['mods'])} installed, instance {led['instance']}\n")
    print(f"{'mod':<30}{'id':>8}  {'version':<10}{'plugins'}")
    for m in led['mods']:
        print(f"   {m['modName']:<27}{m['modId']:>8}  {str(m['version'] or '-'):<10}"
              f"{', '.join(m['plugins']) or '-'}")


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == '--list':
        show()
    elif a[0] == '--verify':
        sys.exit(verify())
    elif a[0] == '--sort':
        sys.exit(sort_order())
    else:
        prefer = None
        plan = None
        replace = False
        if '--prefer' in a:
            i = a.index('--prefer'); prefer = a[i + 1]; a = a[:i] + a[i + 2:]
        if '--plan' in a:
            i = a.index('--plan'); plan = a[i + 1]; a = a[:i] + a[i + 2:]
        if '--replace' in a:
            a.remove('--replace'); replace = True
        file_id = None
        if '--file' in a:
            i = a.index('--file'); file_id = int(a[i + 1]); a = a[:i] + a[i + 2:]
        sys.exit(install(int(a[0]), a[1], prefer, plan, replace, file_id))
