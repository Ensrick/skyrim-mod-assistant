"""Every installed Nexus mod must carry a Keep; no Keep may be uninstalled.

Doctrine: docs/CURATION_POLICY.md, "Installed implies Keep" (user, 2026-09-02).
Adding the Keep is a required step of installing a mod, so this is a gate, not a
report. It runs inside preflight.py.

Three violations, all blocking once no matching durable Keep operation is
pending:

  1. installed Nexus id with no Keep      - the install never finished
  2. Keep with nothing installed          - stale, or an un-actioned adoption
  3. Skip that is installed               - a rejected mod left in the tree

Enabled/disabled is deliberately irrelevant. A parked, superseded or
overlap-held mod is still in the build and keeps its Keep. Our own artifacts
(Ensrick overlays, native rebuilds, source builds, harness mods) resolve to no
Nexus id and are exempt.

  py -3 audit/keep_coverage.py            # gate; queued Keeps print PENDING
  py -3 audit/keep_coverage.py --json     # machine-readable, always exit 0
  py -3 audit/keep_coverage.py --plan     # what a relay batch would change

Reading the live curator state needs nexus-local-curator/scripts/curator_state.py
(Firefox extension storage). If that authority is unavailable the gate fails
closed: it cannot prove that the build obeys the user's Keep/Skip decisions.
"""
import argparse, datetime as dt, json, os, pathlib, re, sys, tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
INSTANCE = pathlib.Path(r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se')
LEDGER = REPO / 'records' / 'installed-mods.json'
GAME = 'skyrimspecialedition'
PROFILE = 'Default'
PENDING_TTL = dt.timedelta(days=7)


def canonical_mod_id(value):
    """Return one canonical positive decimal Nexus ID, otherwise ``None``."""
    raw = str(value if value is not None else '')
    if not re.fullmatch(r'[1-9][0-9]*', raw):
        return None
    return int(raw)


def curator_scripts(candidates=None):
    """Locate the curator checkout from canonical and isolated worktrees.

    ``REPO.parent`` is the shared ``repos`` directory in the canonical checkout,
    but it is ``repos/_codex_worktrees`` for a review worktree.  Deriving a
    second candidate from the configured MO2 instance keeps the audit portable
    across both layouts.  An explicit environment override is useful for CI
    fixtures and other machines without encoding a second user-specific path.
    """
    if candidates is None:
        candidates = []
        override = os.environ.get('NEXUS_CURATOR_SCRIPTS')
        if override:
            candidates.append(pathlib.Path(override))
        candidates.append(REPO.parent / 'nexus-local-curator' / 'scripts')
        try:
            candidates.append(INSTANCE.parents[1] / 'nexus-local-curator' / 'scripts')
        except IndexError:
            pass
    candidates = [pathlib.Path(candidate) for candidate in candidates]
    for candidate in candidates:
        if (candidate / 'curator_state.py').is_file():
            return candidate
    checked = ', '.join(str(path) for path in candidates)
    raise FileNotFoundError(f'curator_state.py not found; checked: {checked}')


def selftest():
    with tempfile.TemporaryDirectory(prefix='keep-coverage-') as raw:
        root = pathlib.Path(raw)
        missing = root / 'missing'
        valid = root / 'curator' / 'scripts'
        valid.mkdir(parents=True)
        (valid / 'curator_state.py').write_text('# fixture\n', encoding='utf-8')
        assert curator_scripts([missing, valid]) == valid
        try:
            curator_scripts([missing])
        except FileNotFoundError as exc:
            assert str(missing) in str(exc)
        else:
            raise AssertionError('missing curator fixture did not fail closed')
        instance = root / 'instance'
        (instance / 'mods' / 'vendor').mkdir(parents=True)
        ledger = root / 'ledger.json'
        ledger.write_text(json.dumps({
            'mods': [{'modName': 'Vendor', 'modId': 42}],
        }), encoding='utf-8')
        assert installed_ids(instance, ledger)['vendor'] == {42}
        pending = root / 'pending.json'
        now = dt.datetime(2026, 9, 4, tzinfo=dt.timezone.utc)
        pending.write_text(json.dumps([
            {'status': 'keep', 'mod': {'game': GAME, 'modId': '43'},
             'queuedAt': '2026-09-03T00:00:00Z'},
            {'status': 'keep', 'mod': {'game': 'skyrim', 'modId': '44'},
             'queuedAt': '2026-09-03T00:00:00Z'},
            {'status': 'keep', 'mod': {'game': GAME, 'modId': '45'},
             'queuedAt': '2000-01-01T00:00:00Z'},
            {'status': 'skip', 'mod': {'game': GAME, 'modId': '46'},
             'queuedAt': '2026-09-03T00:00:00Z'},
        ]), encoding='utf-8')
        state = queued_keep_state(pending, now)
        assert state['ids'] == {43}
        assert any('expired' in message for message in state['errors'])
        refresh = queued_keep_state(pending, now, refresh_target=45)
        assert refresh['ids'] == {43} and refresh['errors'] == []
        assert refresh['refreshableExpired'] == {45}
        assert queued_keep_state(pending, now, refresh_target=43)['errors']
        pending.write_text(json.dumps([{
            'status': 'keep', 'mod': {'game': GAME, 'modId': '0045'},
            'queuedAt': '2026-09-03T00:00:00Z',
        }]), encoding='utf-8')
        noncanonical = queued_keep_state(pending, now, refresh_target=45)
        assert not noncanonical['ids'] and noncanonical['errors']
        assert pending_keep_id(json.loads(pending.read_text())[0], now) is None
        pending.write_text('{broken', encoding='utf-8')
        assert queued_keep_state(pending, now)['errors']
        try:
            queued_keeps(pending, now)
        except ValueError:
            pass
        else:
            raise AssertionError('corrupt pending spool failed open')
        pending.unlink()
        stranded = pending.with_name(pending.name + '.123.fixture.claimed')
        stranded.write_text('[]', encoding='utf-8')
        assert any('stranded writer claim' in error
                   for error in queued_keep_state(pending, now)['errors'])
    print('keep_coverage selftest PASS (13 assertions)')
    return 0


def installed_ids(instance=INSTANCE, ledger_path=LEDGER):
    """name -> {nexus ids}, for every directory under mods/, enabled or not."""
    by_name = {}
    if ledger_path.exists():
        for row in json.loads(ledger_path.read_text(encoding='utf-8-sig')).get('mods', []):
            try:
                mid = int(row.get('modId') or 0)
            except (TypeError, ValueError):
                continue
            name = str(row.get('modName') or '').strip().casefold()
            if name and mid > 0:
                by_name.setdefault(name, set()).add(mid)

    mods = instance / 'mods'
    out = {}
    for d in sorted(p for p in mods.iterdir() if p.is_dir()):
        if d.name.startswith('.') or d.name.endswith('_separator'):
            continue
        ids = set(by_name.get(d.name.strip().casefold(), ()))
        meta = d / 'meta.ini'
        if meta.exists():
            txt = meta.read_text(encoding='utf-8-sig', errors='replace')
            m = re.search(r'^modid\s*=\s*(\d+)', txt, re.M | re.I)
            if m and int(m.group(1)) > 0:
                ids.add(int(m.group(1)))
            m = re.search(r'^installationFile=(.*)$', txt, re.M)
            if m:
                lead = re.match(r'^(\d+)-\d+\.', pathlib.PurePath(m.group(1).strip()).name)
                if lead:
                    ids.add(int(lead.group(1)))
        out[d.name] = ids
    return out


def enabled_names(instance=INSTANCE, profile=PROFILE):
    ml = instance / 'profiles' / profile / 'modlist.txt'
    return {l[1:].strip() for l in ml.read_text(encoding='utf-8-sig').splitlines()
            if l.startswith('+') and l[1:].strip()}


def curator_decisions():
    """{id: row}. Raises if the extension state cannot be read."""
    sys.path.insert(0, str(curator_scripts()))
    import curator_state
    out = {}
    for row in curator_state.decisions():
        if row.get('game') != GAME or not row.get('modId'):
            continue
        try:
            out[int(row['modId'])] = row
        except (TypeError, ValueError):
            pass
    return out


def audit():
    name_ids = installed_ids()
    enabled = enabled_names()
    ids_to_names = {}
    for name, ids in name_ids.items():
        for i in ids:
            ids_to_names.setdefault(i, []).append(name)

    result = {'installedDirs': len(name_ids),
              'installedNexusIds': len(ids_to_names),
              'ownArtifacts': sorted(n for n, s in name_ids.items() if not s)}

    cur = curator_decisions()
    keeps = {i for i, r in cur.items() if r.get('status') == 'keep'}
    skips = {i for i, r in cur.items() if r.get('status') == 'skip'}

    result['liveKeeps'] = len(keeps)
    result['installedWithoutKeep'] = [
        {'modId': i, 'status': cur.get(i, {}).get('status') or 'unreviewed',
         'mods': sorted(ids_to_names[i]),
         'enabled': any(n in enabled for n in ids_to_names[i])}
        for i in sorted(ids_to_names) if i not in keeps and i not in skips]
    result['keepNotInstalled'] = [
        {'modId': i, 'title': cur[i].get('title') or str(i),
         'author': cur[i].get('author') or '', 'keptAt': cur[i].get('addedAt') or ''}
        for i in sorted(keeps) if i not in ids_to_names]
    result['skipInstalled'] = [
        {'modId': i, 'mods': sorted(ids_to_names[i]),
         'enabled': any(n in enabled for n in ids_to_names[i])}
        for i in sorted(skips & set(ids_to_names))]
    return result


def pending_keep_id(entry, now=None):
    """Return one valid SSE Keep ID, or None for stale/foreign/malformed rows."""
    now = now or dt.datetime.now(dt.timezone.utc)
    mod = entry.get('mod', {}) if isinstance(entry, dict) else {}
    mod_id = canonical_mod_id(mod.get('modId'))
    if (not isinstance(entry, dict) or entry.get('status') != 'keep' or
            mod.get('game') != GAME or mod_id is None):
        return None
    try:
        queued_at = dt.datetime.fromisoformat(
            str(entry.get('queuedAt') or '').replace('Z', '+00:00'))
        if queued_at.tzinfo is None:
            return None
    except (TypeError, ValueError):
        return None
    age = now - queued_at.astimezone(dt.timezone.utc)
    return mod_id if dt.timedelta(0) <= age <= PENDING_TTL else None


def queued_keep_state(pending=None, now=None, refresh_target=None):
    """Parse the durable relay spool without discarding integrity failures.

    ``refresh_target`` is a deliberately narrow install-time exception.  One
    otherwise valid, expired SSE Keep for that exact Nexus ID is reported as
    refreshable instead of corrupt so ``install_mod.queue_keep`` can replace it
    atomically after the install succeeds.  It does not excuse duplicates,
    malformed/future timestamps, another game, another ID, or a Skip.
    """
    pending = pathlib.Path(pending) if pending else (
        pathlib.Path(os.environ.get('TEMP', '.')) / 'nlc-relay' /
        'decisions-pending.json')
    if refresh_target is not None:
        try:
            refresh_target = int(refresh_target)
        except (TypeError, ValueError):
            raise ValueError('refresh_target must be one positive Nexus mod ID')
        if refresh_target <= 0:
            raise ValueError('refresh_target must be one positive Nexus mod ID')
    result = {'ids': set(), 'errors': [], 'warnings': [],
              'refreshableExpired': set(), 'path': str(pending)}
    stranded = sorted(pending.parent.glob(pending.name + '.*.claimed')) \
        if pending.parent.is_dir() else []
    if stranded:
        result['errors'].append(
            'pending curator spool has stranded writer claim(s): ' +
            ', '.join(path.name for path in stranded))
    if not pending.exists():
        return result
    try:
        batch = json.loads(pending.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result['errors'].append(
            f'pending curator spool is unreadable: {type(exc).__name__}: {exc}')
        return result
    if not isinstance(batch, list):
        result['errors'].append('pending curator spool root must be a JSON array')
        return result

    now = now or dt.datetime.now(dt.timezone.utc)
    seen = set()
    for index, entry in enumerate(batch):
        label = f'pending curator row {index + 1}'
        if not isinstance(entry, dict):
            result['errors'].append(f'{label} must be an object')
            continue
        status = entry.get('status')
        mod = entry.get('mod')
        if status not in {'keep', 'skip'}:
            result['errors'].append(
                f'{label} has invalid/case-sensitive status {status!r}')
        if not isinstance(mod, dict):
            result['errors'].append(f'{label}.mod must be an object')
            continue
        game = mod.get('game')
        raw_mid = str(mod.get('modId') if mod.get('modId') is not None else '')
        mod_id = canonical_mod_id(mod.get('modId'))
        if not isinstance(game, str) or not game.strip() or mod_id is None:
            result['errors'].append(f'{label} has invalid game/modId identity')
            continue
        identity = (game.casefold(), mod_id)
        if identity in seen:
            result['errors'].append(
                f'{label} duplicates pending identity {game}/{raw_mid}')
        seen.add(identity)
        try:
            queued_at = dt.datetime.fromisoformat(
                str(entry.get('queuedAt') or '').replace('Z', '+00:00'))
            if queued_at.tzinfo is None:
                raise ValueError('timezone missing')
            age = now - queued_at.astimezone(dt.timezone.utc)
        except (TypeError, ValueError):
            result['errors'].append(
                f'{label} queuedAt is missing/invalid or lacks a timezone')
            continue
        if age < dt.timedelta(0):
            result['errors'].append(f'{label} is future-dated')
            continue
        if age > PENDING_TTL:
            if (refresh_target is not None and status == 'keep' and
                    game == GAME and mod_id == refresh_target):
                result['refreshableExpired'].add(refresh_target)
                result['warnings'].append(
                    f'{label} is expired ({age.days} day(s) old; limit '
                    f'{PENDING_TTL.days}) and is eligible only for atomic '
                    'same-ID refresh by the current install')
                continue
            result['errors'].append(
                f'{label} is expired ({age.days} day(s) old; limit {PENDING_TTL.days})')
            continue
        if game == GAME and status == 'keep':
            result['ids'].add(mod_id)
    return result


def queued_keeps(pending=None, now=None, refresh_target=None):
    """Return current SSE Keep IDs, raising if spool integrity is unproven."""
    state = queued_keep_state(pending, now, refresh_target=refresh_target)
    if state['errors']:
        raise ValueError('; '.join(state['errors']))
    return state['ids']


def run(fails, warns):
    """preflight hook."""
    try:
        r = audit()
    except Exception as exc:                                  # unreadable state
        fails.append('keep coverage unverifiable: %s: %s' % (type(exc).__name__, exc))
        return
    queue_state = queued_keep_state()
    fails.extend(f"keep queue integrity: {message}" for message in queue_state['errors'])
    warns.extend(f"keep queue: {message}" for message in queue_state['warnings'])
    queued = queue_state['ids']
    for row in r['installedWithoutKeep']:
        if row['modId'] in queued:
            fails.append('Keep for %d (%s) is queued but not yet applied - '
                         'lifecycle remains open until the extension consumes it'
                         % (row['modId'], ', '.join(row['mods'])))
            continue
        fails.append('installed with no Keep: %d (%s) - the install is not '
                     'finished until the Keep exists or is queued'
                     % (row['modId'], ', '.join(row['mods'])))
    for row in r['keepNotInstalled']:
        # WARN, not FAIL, in the LAUNCH gate: a Keep whose mod is not installed
        # puts no files in the tree and cannot affect a launch, and there is a
        # legitimate window for it during an adoption in flight (2026-09-02: a
        # Keep applied ahead of its install deadlocked two agents against each
        # other). The standalone gate still exits 1 on it - it is a curation
        # violation, just not a launch blocker.
        warns.append('Keep with nothing installed: %d %s - adopt it or clear it '
                     'to unreviewed (not a launch blocker)'
                     % (row['modId'], row['title'] or ''))
    for row in r['skipInstalled']:
        fails.append('Skip is installed: %d (%s) - move it to '
                     'mo2-instances\\_archived-rejects'
                     % (row['modId'], ', '.join(row['mods'])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--plan', action='store_true',
                    help='print the keep additions a relay batch would make')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    r = audit()
    queue_state = queued_keep_state()
    r['pendingQueue'] = {
        'ids': sorted(queue_state['ids']),
        'errors': queue_state['errors'],
        'warnings': queue_state['warnings'],
        'path': queue_state['path'],
    }
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if args.plan:
        for row in r['installedWithoutKeep']:
            print('keep %-7d %s' % (row['modId'], ', '.join(row['mods'])))
        return 0

    print('installed dirs %d, nexus ids %d, own artifacts %d, live keeps %d'
          % (r['installedDirs'], r['installedNexusIds'],
             len(r['ownArtifacts']), r['liveKeeps']))
    bad = 0
    queued = queue_state['ids']
    for message in queue_state['errors']:
        print('  FAIL  keep queue integrity: ' + message)
        bad += 1
    for message in queue_state['warnings']:
        print('  WARN  keep queue: ' + message)
    for row in r['installedWithoutKeep']:
        if row['modId'] in queued:
            print('  PENDING Keep queued but not yet applied: %d (%s)'
                  % (row['modId'], ', '.join(row['mods'])))
            bad += 1
            continue
        print('  FAIL  installed with no Keep: %d (%s)%s'
              % (row['modId'], ', '.join(row['mods']),
                 '' if row['enabled'] else ' [disabled - still needs the Keep]'))
        bad += 1
    for row in r['keepNotInstalled']:
        print('  FAIL  Keep with nothing installed: %d %s %s'
              % (row['modId'], row['title'], row['keptAt']))
        bad += 1
    for row in r['skipInstalled']:
        print('  FAIL  Skip is installed: %d (%s)' % (row['modId'], ', '.join(row['mods'])))
        bad += 1
    if bad:
        print('\n%d keep-coverage violation(s) - docs/CURATION_POLICY.md '
              '"Installed implies Keep"' % bad)
        return 1
    print('\nkeep coverage clean')
    return 0


if __name__ == '__main__':
    sys.exit(main())
