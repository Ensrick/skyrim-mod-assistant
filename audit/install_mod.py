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

Two guards wrap every mutating path (install, --sort), both from the 2026-08-30
process audit:

  worktree guard   this file refuses to mutate the live profile unless it IS the
                   canonical checkout (CANONICAL below). Three agent worktrees
                   kept running a pre-fix copy against the same profile (#105);
                   `--i-know-what-im-doing` overrides, and is logged.
  work claim       install and sort run under audit/claim.py, so two sessions
                   queue instead of racing (#103). Set SKYRIM_CLAIM_OWNER for the
                   session, or acquire the claim from the shell first; a claim
                   held by someone else stops this script before it downloads.
"""
import json, os, re, sys, hashlib, subprocess, datetime

SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SP)
sys.path.insert(0, SP)
import claim
import human_presence as HP
import keep_coverage
import profile_reconcile

CANONICAL = r'C:\Users\danjo\source\repos\skyrim-mod-assistant'
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
PROFILE = 'Default'
MO2 = os.path.join(INSTANCE, 'MO2Headless.exe')
LEDGER = os.path.join(REPO, 'records', 'installed-mods.json')


def guard_canonical(override):
    """Refuse to mutate the live profile from any checkout but the canonical one.

    Every git worktree and agent clone carries its own copy of this file and
    its own idea of where the controller is; the 2026-08-30 recurrence (four
    plugins unstarred twice in a day) came from exactly that (#105, audit F0)."""
    here = os.path.normcase(os.path.realpath(REPO))
    want = os.path.normcase(os.path.realpath(CANONICAL))
    if here == want:
        return
    msg = (f'this install_mod.py lives in {REPO}, not the canonical checkout '
           f'{CANONICAL}. Worktree copies have installed stale code against the '
           f'live profile before (#105).')
    if not override:
        print('REFUSING: ' + msg + '\n   run the canonical copy, or pass '
              '--i-know-what-im-doing if you have rebased this checkout onto it.')
        sys.exit(78)
    print('WARNING: ' + msg + ' (override given)')


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


def _plugin_states():
    state = mo2('plugin-list')
    if not state.get('ok'):
        raise RuntimeError(f"cannot read plugin state: {state}")
    return {str(row.get('name') or '').casefold(): bool(row.get('enabled'))
            for row in state.get('plugins', []) if row.get('name')}


def _ledger_row(previous, **current):
    """Refresh provenance without erasing reviewed intent on an update."""
    row = dict(previous or {})
    row.pop('archivedTo', None)
    row.update(current)
    return row


def _desired_active_plugins(plugins, mod_enabled, replacing, before_states):
    return {
        str(plugin).casefold() for plugin in plugins
        if mod_enabled and (not replacing or before_states.get(str(plugin).casefold(), False))
    }


def _restore_ledger_snapshot(snapshot):
    existed, payload = snapshot
    if existed:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        tmp = LEDGER + '.rollback.tmp'
        with open(tmp, 'wb') as stream:
            stream.write(payload)
        os.replace(tmp, LEDGER)
    elif os.path.exists(LEDGER):
        os.remove(LEDGER)


def _rollback_transactions(transaction_ids, ledger_snapshot=None):
    """Reverse a logical install group in strict last-applied-first order."""
    okay = True
    for transaction_id in reversed([tx for tx in transaction_ids if tx]):
        result = mo2('rollback', transaction_id)
        if result.get('ok'):
            print(f'   rolled back MO2 transaction {transaction_id}')
        else:
            okay = False
            print(f'   ROLLBACK FAILED for MO2 transaction {transaction_id}: {result}')
    if ledger_snapshot is not None:
        try:
            _restore_ledger_snapshot(ledger_snapshot)
            print('   restored exact pre-transaction ledger bytes')
        except Exception as exc:
            okay = False
            print(f'   LEDGER ROLLBACK FAILED: {type(exc).__name__}: {exc}')
    return okay


def _curation_precondition(mid, mod_name):
    """Require readable, non-contradictory Keep/Skip state before mutation."""
    try:
        coverage = keep_coverage.audit()
        decisions = keep_coverage.curator_decisions()
        queued = keep_coverage.queued_keeps()
        pending = _pending_decisions()
    except Exception as exc:
        print('REFUSING install: curator state is unreadable; a mutation may not '
              f'guess Keep/Skip intent ({type(exc).__name__}: {exc})')
        return False

    target = decisions.get(int(mid), {})
    if str(target.get('status') or '').casefold() == 'skip':
        print(f'REFUSING install: Nexus {mid} is a live Skip. Record the user\'s '
              'explicit reversal in the curator before installing it.')
        return False

    pending_target = [e for e in pending
                      if str(e.get('mod', {}).get('modId')) == str(mid)
                      and str(e.get('mod', {}).get('game') or '').casefold() ==
                          'skyrimspecialedition']
    pending_states = {str(e.get('status') or '').casefold() for e in pending_target}
    if any(state != 'keep' for state in pending_states):
        print(f'REFUSING install: Nexus {mid} has contradictory pending curator '
              f'state: {", ".join(sorted(pending_states)) or "(blank)"}')
        return False

    failures = []
    for row in coverage['installedWithoutKeep']:
        if row['modId'] not in queued:
            failures.append('installed without Keep: %d (%s)' %
                            (row['modId'], ', '.join(row['mods'])))
    for row in coverage['skipInstalled']:
        failures.append('installed Skip: %d (%s)' %
                        (row['modId'], ', '.join(row['mods'])))
    for row in coverage['keepNotInstalled']:
        if int(row['modId']) != int(mid):
            failures.append('Keep with nothing installed: %d (%s)' %
                            (row['modId'], row['title']))
    installed_ids = {
        nexus_id
        for ids in keep_coverage.installed_ids().values()
        for nexus_id in ids
    }
    for entry in pending:
        if (str(entry.get('status') or '').casefold() != 'keep' or
                str(entry.get('mod', {}).get('game') or '').casefold() !=
                'skyrimspecialedition'):
            continue
        try:
            pending_id = int(entry.get('mod', {}).get('modId'))
        except (TypeError, ValueError):
            failures.append('pending Keep has invalid mod ID')
            continue
        if pending_id not in installed_ids and pending_id != int(mid):
            failures.append(f'pending Keep with nothing installed: {pending_id}')
    if failures:
        print('REFUSING install: existing curation state is not reconciled:')
        for failure in failures:
            print('   ' + failure)
        return False

    return True


def refuse_if_human_playing(what):
    """#164: no profile mutation under a session a person is playing in.

    A live SkyrimSE.exe alone is a warning (the launch chain holds the
    instance lock anyway); a live game whose probe log shows a human driving
    gameplay menus is a refusal with exit 88."""
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq SkyrimSE.exe'],
                       capture_output=True, text=True)
    if 'skyrimse.exe' not in (r.stdout or '').lower():
        return
    v = HP.judge()
    if v['human']:
        print(f'REFUSING {what}: SkyrimSE.exe is running and {HP.describe(v)}')
        HP.log_refusal(v, f'install_mod {what}')
        sys.exit(HP.HUMAN_AT_CONTROLS)
    print(f'WARNING: SkyrimSE.exe is running ({HP.describe(v)}); {what} continues '
          f'but the instance lock may be held by the launch chain')


def install(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None):
    refuse_if_human_playing(f'install {mid} "{mod_name}"')
    with claim.guard(None, f'install_mod {mid} "{mod_name}"', ttl=45):
        # Reconcile only after acquiring the writer claim. A clean result read
        # before the claim would be stale if another controller changed the
        # profile while we waited.
        state = profile_reconcile.reconcile()
        if not state['reconciled']:
            print('REFUSING install: the existing profile is not reconciled (#102).')
            print(profile_reconcile.render(state))
            return 1
        return _install(mid, mod_name, prefer, plan, replace, file_id)


def _install(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None):
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

    ledger_snapshot = (
        os.path.exists(LEDGER),
        open(LEDGER, 'rb').read() if os.path.exists(LEDGER) else b'',
    )
    led = load()
    previous = next((m for m in led['mods']
                     if str(m.get('modName') or '').casefold() == mod_name.casefold()), None)
    if replace and previous is None:
        print('REFUSING update: --replace requires an existing reconciled ledger row '
              f'for {mod_name}')
        return 1
    try:
        before_plugins = _plugin_states()
    except RuntimeError as exc:
        print(f'REFUSING install: {exc}')
        return 1
    desired_mod_enabled = bool(previous.get('enabled')) if replace else True

    if not _curation_precondition(mid, mod_name):
        return 1

    args = ['mod-install', archive, mod_name,
            '--enable' if desired_mod_enabled else '--disable']
    if replace:
        args += ['--replace']
    if plan:
        args += ['--install-plan', os.path.abspath(plan)]
    res = mo2(*args)
    if not res.get('ok'):
        print('install failed:', res); return 1
    print(f"installed {mod_name}  transaction {res.get('transaction')}")
    transactions = [res.get('transaction')]
    ledger_changed = False

    def abort_applied(message):
        print(message)
        rolled_back = _rollback_transactions(
            transactions, ledger_snapshot if ledger_changed else None)
        if not rolled_back:
            print('   logical transaction remains BROKEN; manual recovery is required')
        return 1

    added = plugins_of(mod_name)
    # New installs activate their selected plugins. Updates preserve the exact
    # pre-update active membership; a newly introduced plugin stays inactive
    # until it is explicitly reviewed instead of being silently activated.
    desired_active = _desired_active_plugins(
        added, desired_mod_enabled, replace, before_plugins)
    try:
        current_plugins = _plugin_states()
    except RuntimeError as exc:
        return abort_applied(f'install applied but plugin-state verification failed: {exc}')
    for p in added:
        key = p.casefold()
        desired = key in desired_active
        actual = current_plugins.get(key, False)
        if actual == desired:
            continue
        r = mo2('plugin-enable' if desired else 'plugin-disable', p)
        if not r.get('ok'):
            return abort_applied(f"   plugin {p}: state update FAILED: {r}")
        transactions.append(r.get('transaction'))
        print(f"   plugin {p}: {'enabled' if desired else 'deliberately disabled'}")

    try:
        after_plugins = _plugin_states()
    except RuntimeError as exc:
        return abort_applied(f'install applied but plugin-state verification failed: {exc}')
    wrong = [p for p in added
             if after_plugins.get(p.casefold(), False) != (p.casefold() in desired_active)]
    if wrong:
        return abort_applied(
            'install applied but exact plugin-state postcondition failed: ' + ', '.join(wrong))

    # One source archive can legitimately be installed as multiple component
    # folders (core, official patch, optional assets). File ID is provenance,
    # not row identity. Replace only the row for this exact physical folder;
    # global file-ID deduplication silently erased sibling components.
    led['mods'] = [m for m in led['mods']
                   if str(m.get('modName') or '').casefold() != mod_name.casefold()]
    disabled_plugins = sorted(
        (p for p in added if desired_mod_enabled and p.casefold() not in desired_active),
        key=str.casefold)
    current = {
        'modId': mid, 'modName': mod_name,
        'nexusName': f['name'], 'version': f.get('version'),
        'fileId': f['file_id'], 'fileName': f['file_name'],
        'sizeMb': round(f['size_kb'] / 1024, 2), 'sha256': sha,
        'plugins': added, 'enabled': desired_mod_enabled,
        'installedUtc': datetime.datetime.now(datetime.timezone.utc)
                                 .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'transaction': res.get('transaction'),
        **({'fomodPlan': plan} if plan else {}),
    }
    row = _ledger_row(previous, **current)
    if not plan:
        row.pop('fomodPlan', None)
    if disabled_plugins:
        row['disabledPlugins'] = disabled_plugins
    else:
        row.pop('disabledPlugins', None)
    if replace:
        introduced = sorted(
            set(added) - {str(p) for p in (previous.get('plugins') or [])},
            key=str.casefold)
        introduced_inactive = [p for p in introduced if p in disabled_plugins]
        if introduced_inactive:
            marker = ('Update introduced plugin(s) left inactive pending review: ' +
                      ', '.join(introduced_inactive) + '.')
            old_note = str(row.get('note') or '').strip()
            if marker not in old_note:
                row['note'] = (old_note + (' ' if old_note else '') + marker)
    led['mods'].append(row)
    try:
        save(led)
        ledger_changed = True
    except Exception as exc:
        return abort_applied(
            f'install applied but ledger commit failed: {type(exc).__name__}: {exc}')
    print(f'ledger now holds {len(led["mods"])} mods -> {LEDGER}')
    state = profile_reconcile.reconcile()
    if not state['reconciled']:
        print(profile_reconcile.render(state))
        return abort_applied(
            'post-install profile does not reconcile; reverting the logical transaction (#102)')
    if not queue_keep(mid, mod_name):
        return abort_applied(
            'required Keep could not be queued; reverting the logical transaction')
    return 0


def _pending_keep_path():
    return os.path.join(os.environ.get('TEMP', '.'), 'nlc-relay',
                        'decisions-pending.json')


def _pending_decisions():
    pending = _pending_keep_path()
    if not os.path.exists(pending):
        return []
    batch = json.load(open(pending, encoding='utf-8'))
    if not isinstance(batch, list):
        raise ValueError('curator pending batch is not a JSON array')
    return batch


def queue_keep(mid, mod_name):
    """Installing a mod includes adding its Keep - docs/CURATION_POLICY.md.

    Written 2026-09-02 on the user's instruction that "our processes and
    procedures doctrine makes adding to keeps necessary for installed mods".
    The Keep itself is applied by the Firefox extension on its next Nexus page
    load, so the guaranteed part is the QUEUE: this appends to the relay spool
    (merging with any batch not yet picked up, deduplicated by id) so the step
    can never be forgotten. audit/keep_coverage.py is the matching gate.
    """
    pending = _pending_keep_path()
    spool = os.path.dirname(pending)
    try:
        os.makedirs(spool, exist_ok=True)
        batch = _pending_decisions()
        same_id = [e for e in batch
                   if str(e.get('mod', {}).get('modId')) == str(mid)
                   and str(e.get('mod', {}).get('game') or '').casefold() ==
                       'skyrimspecialedition']
        if any(str(e.get('status') or '').casefold() == 'keep' for e in same_id):
            print(f'keep {mid} already queued')
            return True
        if same_id:
            states = ', '.join(sorted({str(e.get('status') or '(blank)') for e in same_id}))
            print(f'   KEEP QUEUE REFUSED for {mid}: existing Skyrim SE pending '
                  f'decision is {states}, not Keep')
            print('   resolve the contradictory curator decision explicitly; '
                  'an install must never reinterpret Skip as Keep')
            return False
        batch.append({'status': 'keep', 'mod': {
            'game': 'skyrimspecialedition', 'modId': str(mid),
            'title': mod_name,
            'sourceUrl': f'https://www.nexusmods.com/skyrimspecialedition/mods/{mid}'},
            'queuedAt': datetime.datetime.now(datetime.timezone.utc)
                                .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'source': 'audit/install_mod.py'})
        tmp = pending + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(batch, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, pending)
        print(f'keep {mid} queued for the curator ({len(batch)} in batch) -> {pending}')
        print('   it applies on the next Nexus page load; '
              'py -3 audit/keep_coverage.py is the gate')
        return True
    except Exception as exc:
        print(f'   KEEP QUEUE FAILED for {mid}: {type(exc).__name__}: {exc}')
        print('   the lifecycle transaction is incomplete until this is repaired')
        return False


def verify():
    reconciled = profile_reconcile.reconcile()
    print(profile_reconcile.render(reconciled) + '\n')
    led = load()
    state = mo2('plugin-list')
    live = {p['name']: p['enabled'] for p in state.get('plugins', [])}
    print(f"{len(led['mods'])} mods in ledger; {state.get('discoveredCount')} plugins discovered\n")
    bad = reconciled['counts']['errors']
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
    refuse_if_human_playing('--sort')
    with claim.guard(None, 'install_mod --sort (LOOT)', ttl=45):
        state = profile_reconcile.reconcile()
        if not state['reconciled']:
            print('REFUSING sort: the existing profile is not reconciled (#102).')
            print(profile_reconcile.render(state))
            return 1
        return _sort_order()


def _sort_order():
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
    override = '--i-know-what-im-doing' in a
    if override:
        a.remove('--i-know-what-im-doing')
    if not a or a[0] == '--list':
        show()
    elif a[0] == '--verify':
        sys.exit(verify())
    elif a[0] == '--reconcile':
        state = profile_reconcile.reconcile()
        print(profile_reconcile.render(state))
        sys.exit(0 if state['reconciled'] else 1)
    elif a[0] == '--sort':
        guard_canonical(override)
        try:
            sys.exit(sort_order())
        except claim.ClaimHeld as e:
            print(f'CLAIM HELD - not sorting: {e}'); sys.exit(claim.ExTempFail)
    else:
        guard_canonical(override)
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
        try:
            sys.exit(install(int(a[0]), a[1], prefer, plan, replace, file_id))
        except claim.ClaimHeld as e:
            print(f'CLAIM HELD - not installing: {e}'); sys.exit(claim.ExTempFail)
