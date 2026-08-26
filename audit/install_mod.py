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
"""
import json, os, re, sys, hashlib, subprocess, datetime

SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SP)
sys.path.insert(0, SP)

MO2 = r'C:\Users\danjo\source\repos\mo2-builds\MO2-2.5.2-headless-23de14e2-full\MO2Headless.exe'
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = 'Default'
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
    for m in led['mods']:
        for p in m['plugins']:
            ok = live.get(p)
            flag = 'enabled' if ok else ('DISABLED' if p in live else 'MISSING')
            if not m.get('enabled'):
                # parked mod: its plugins are expected to be undiscovered
                flag = 'parked' if not ok else 'ACTIVE-WHILE-PARKED'
                if ok:
                    bad += 1
            elif p in m.get('disabledPlugins', []):
                # deliberately unstarred (e.g. its master is not installed)
                flag = 'deliberately-disabled' if not ok else 'ACTIVE-BUT-MARKED-DISABLED'
                if ok:
                    bad += 1
            elif not ok:
                bad += 1
            print(f"   {m['modName']:<28}{p:<28}{flag}")
        if not m['plugins']:
            print(f"   {m['modName']:<28}{'(no plugin)':<28}-")
    print(f'\n{bad} problem(s)')
    return 1 if bad else 0


def sort_order():
    """Sort with LootCLI through MO2's VFS, then restore enable markers.

    LootCLI rewrites plugins.txt and drops the '*' on managed plugins, so the
    re-enable is not optional housekeeping - skip it and the mods you just
    installed are silently inactive."""
    plugins = os.path.join(INSTANCE, 'profiles', PROFILE, 'plugins.txt')
    out = os.path.join(INSTANCE, 'loot-report.json')
    game = r'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition'
    # `--` does not survive `pwsh -File`; PowerShell then tries to bind --game
    # as a parameter name. Pass the tool arguments as an explicit array instead.
    def q(s):
        return "'" + str(s).replace("'", "''") + "'"
    targs = ','.join(q(x) for x in ['--game', 'SkyrimSE', '--gamePath', game,
                                    '--pluginListPath', plugins, '--out', out])
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
    n = 0
    for m in led['mods']:
        if not m.get('enabled'):
            continue                      # parked mods stay parked
        for pl in m['plugins']:
            if pl in m.get('disabledPlugins', []):
                continue                  # deliberately unstarred (absent master)
            mo2('plugin-enable', pl)
            n += 1
    print(f'sorted, then re-enabled {n} plugins '
          f'(parked mods and recorded disabledPlugins left alone)')
    return verify()


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
