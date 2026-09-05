"""Install a Nexus mod through the headless MO2 controller and record it.

One path in and out: download from Nexus, install it disabled, inspect every
owned-patch relationship, require a reviewed receipt, then activate and append
to the ledger. Nothing is copied into the game folder by hand, so every
installed mod stays reversible through MO2's transaction journal and visible
in one file.

  py -3 audit/install_mod.py 12604 "SkyUI" --issue 102
  # The first pass rolls back and writes the patch-impact draft. Review it,
  # assign every outcome/evidence field, then repeat with its exact path:
  py -3 audit/install_mod.py 12604 "SkyUI" --issue 102 --impact-receipt records/impact-receipts/skyui-....json
  py -3 audit/install_mod.py 12604 "SkyUI" --issue 102 --prefer "2K"
  py -3 audit/install_mod.py --list                          # show the ledger
  py -3 audit/install_mod.py --sort                          # deliberately refused
  py -3 audit/install_mod.py 27962 "Skyrim Unbound Reborn" --issue 102 --plan records/fomod-plans/x.json

`--sort` is intentionally fail-closed until load-order mutation is covered by
the same patch-impact and verification transaction. Use read-only LOOT
diagnostics in the meantime. `--verify` re-checks ledger/plugin agreement.
Replacement/update is likewise unsupported until retained before/after payload
receipts can prove removed records and assets; `--replace` always refuses.

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
import json, os, pathlib, re, sys, hashlib, subprocess, datetime

SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SP)
sys.path.insert(0, SP)
import claim
import human_presence as HP
import keep_coverage
import patch_impact
import profile_reconcile
import verification_plan
import verification_status

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
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    raw = (p.stdout or p.stderr or '').strip()
    try:
        result = json.loads(raw.splitlines()[-1])
        if not isinstance(result, dict):
            return {'ok': False, 'error': 'controller JSON root is not an object',
                    'raw': raw[:400]}
        return result
    except Exception:
        return {'ok': False, 'raw': raw[:400]}


def _best_effort_print(*args, **kwargs):
    """Diagnostics must never pre-empt or interrupt transaction cleanup."""
    try:
        print(*args, **kwargs)
        return True
    except BaseException:
        return False


def _journal_state(root=None):
    """Return controller journal manifests keyed by transaction ID.

    A command can commit and then lose/truncate its JSON response. The journal
    is the independent authority for whether that ambiguous call committed and
    gives us the rollback ID the response failed to deliver.
    """
    journal = pathlib.Path(root or INSTANCE) / 'headless-journal'
    out = {}
    if not journal.is_dir():
        return out
    for directory in journal.iterdir():
        if not directory.is_dir():
            continue
        manifest = directory / 'transaction.json'
        try:
            document = json.loads(manifest.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            out[directory.name] = {
                '_unreadable': f'{type(exc).__name__}: {exc}',
                '_path': str(manifest),
            }
            continue
        if isinstance(document, dict):
            document['_path'] = str(manifest)
            out[directory.name] = document
        else:
            out[directory.name] = {
                '_unreadable': 'manifest root is not an object',
                '_path': str(manifest),
            }
    return out


def mo2_mutation(*args, root=None):
    """Run one mutation and recover an exact committed result from its journal.

    This does not guess from filesystem side effects. Exactly one new,
    committed, non-rolled-back manifest for the requested operation is needed
    to recover a missing/broken controller response; every other outcome stays
    fail-closed for the caller's exact-state recovery path.
    """
    actual_root = root or INSTANCE
    before = _journal_state(actual_root)
    result = mo2(*args, root=actual_root)
    if not isinstance(result, dict):
        result = {
            'ok': False,
            'error': f'controller result is not an object: {type(result).__name__}',
        }
    after = _journal_state(actual_root)
    new_ids = sorted(set(after) - set(before))
    operation = str(args[0]) if args else ''
    committed = []
    unresolved = []
    for transaction_id in new_ids:
        row = after[transaction_id]
        if row.get('_unreadable'):
            unresolved.append(transaction_id)
            continue
        recorded_root = str(row.get('instanceRoot') or '')
        if recorded_root and os.path.normcase(os.path.realpath(recorded_root)) != \
                os.path.normcase(os.path.realpath(actual_root)):
            unresolved.append(transaction_id)
            continue
        if (row.get('operation') == operation and row.get('committed') is True
                and row.get('rolledBack') is not True):
            committed.append(transaction_id)

    returned = str(result.get('transaction') or '') if isinstance(result, dict) else ''
    if result.get('ok') and returned:
        # A real controller with a journal must bind success to the newly
        # written manifest. Offline fakes intentionally have no journal.
        journal_exists = (pathlib.Path(actual_root) / 'headless-journal').is_dir()
        if journal_exists and returned not in committed:
            return {'ok': False, 'error': 'controller success is not backed by a '
                    'new committed transaction manifest', 'controllerResult': result,
                    'newJournals': new_ids, 'unresolvedJournals': unresolved}
        return result
    if len(committed) == 1 and not unresolved:
        recovered = dict(result)
        recovered.update({
            'ok': True,
            'transaction': committed[0],
            'recoveredFromJournal': True,
            'controllerResult': result,
        })
        return recovered
    failed = dict(result)
    failed['newJournals'] = new_ids
    failed['committedJournals'] = committed
    failed['unresolvedJournals'] = unresolved
    return failed


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


def _replacement_identity_error(previous, requested_mid):
    if not previous:
        return None
    try:
        previous_mid = int(previous.get('modId') or 0)
    except (TypeError, ValueError):
        previous_mid = 0
    if previous_mid > 0 and previous_mid != int(requested_mid):
        return (f'--replace cannot migrate Nexus identity from {previous_mid} to '
                f'{requested_mid}. That requires an explicit curator migration '
                'transaction so the old Keep cannot be orphaned.')
    return None


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
    missing = sum(1 for transaction_id in transaction_ids if not transaction_id)
    if missing:
        okay = False
        _best_effort_print(
            f'   ROLLBACK INCOMPLETE: {missing} applied mutation(s) returned no transaction ID')
    for transaction_id in reversed([tx for tx in transaction_ids if tx]):
        try:
            result = mo2('rollback', transaction_id)
        except BaseException as exc:
            okay = False
            _best_effort_print(
                f'   ROLLBACK FAILED for MO2 transaction {transaction_id}: '
                f'{type(exc).__name__}: {exc}')
            continue
        if isinstance(result, dict) and result.get('ok'):
            _best_effort_print(f'   rolled back MO2 transaction {transaction_id}')
        else:
            okay = False
            _best_effort_print(
                f'   ROLLBACK FAILED for MO2 transaction {transaction_id}: {result}')
    if ledger_snapshot is not None:
        try:
            _restore_ledger_snapshot(ledger_snapshot)
            _best_effort_print('   restored exact pre-transaction ledger bytes')
        except BaseException as exc:
            okay = False
            _best_effort_print(
                f'   LEDGER ROLLBACK FAILED: {type(exc).__name__}: {exc}')
    return okay


class _LogicalInstall:
    """Fail-closed owner for every mutation after ``mod-install`` succeeds."""

    def __init__(self):
        self.applied = False
        self.closed = False
        self.transactions = []
        self.ledger_snapshot = None
        self.ledger_changed = False
        self.test_plan_path = None
        self.curator_change = None
        self.before_state = None

    def arm(self, ledger_snapshot, before_state=None):
        """Own recovery before entering the first fallible mutation call."""
        if self.applied:
            raise RuntimeError('logical install recovery was armed more than once')
        self.applied = True
        self.ledger_snapshot = ledger_snapshot
        self.before_state = before_state

    def begin(self, transaction_id, ledger_snapshot, before_state=None):
        self.arm(ledger_snapshot, before_state)
        self.transactions.append(transaction_id)

    def add(self, transaction_id):
        self.transactions.append(transaction_id)
        return bool(transaction_id)

    def abort(self, reason):
        if not self.applied or self.closed:
            return True
        self.closed = True
        try:
            curator_okay = self._rollback_curator()
        except BaseException as exc:
            curator_okay = False
            _best_effort_print(
                f'   CURATOR ROLLBACK FAILED: {type(exc).__name__}: {exc}')
        try:
            okay = _rollback_transactions(
                self.transactions,
                self.ledger_snapshot if self.ledger_changed else None)
        except BaseException as exc:
            okay = False
            _best_effort_print(
                f'   MO2/LEDGER ROLLBACK FAILED: {type(exc).__name__}: {exc}')
        if self.before_state is not None:
            try:
                after_state = _mutation_state_snapshot(self.before_state['modName'])
                if after_state != self.before_state:
                    _best_effort_print(
                        '   rollback journal did not restore the exact pre-transaction '
                        'state; applying the captured authority before-images')
                    if not _restore_mutation_snapshot(self.before_state):
                        okay = False
                    after_state = _mutation_state_snapshot(self.before_state['modName'])
                    if after_state != self.before_state:
                        okay = False
                        _best_effort_print(
                            '   ROLLBACK POSTCONDITION FAILED: profile/target bytes do '
                            'not match the exact pre-transaction snapshot')
            except BaseException as exc:
                okay = False
                _best_effort_print(
                    '   ROLLBACK POSTCONDITION FAILED: state recovery crashed: '
                    f'{type(exc).__name__}: {exc}')
            try:
                reconciled = profile_reconcile.reconcile()
                if not reconciled.get('reconciled'):
                    okay = False
                    _best_effort_print(
                        '   ROLLBACK POSTCONDITION FAILED: restored profile does '
                        'not reconcile')
            except BaseException as exc:
                okay = False
                _best_effort_print(
                    '   ROLLBACK POSTCONDITION FAILED: reconciliation crashed: '
                    f'{type(exc).__name__}: {exc}')
        if self.test_plan_path and pathlib.Path(self.test_plan_path).is_file():
            try:
                path = pathlib.Path(self.test_plan_path)
                aborted = json.loads(path.read_text(encoding='utf-8-sig'))
                aborted['status'] = 'aborted'
                aborted.setdefault('results', {})['abortReason'] = reason
                _write_json_atomic(path, aborted)
            except BaseException as exc:
                okay = False
                _best_effort_print(
                    f'   TEST-PLAN ABORT MARK FAILED: {type(exc).__name__}: {exc}')
        return okay and curator_okay

    def _rollback_curator(self):
        if not self.curator_change:
            return True
        change = self.curator_change
        path = pathlib.Path(change['path'])
        try:
            current = (path.exists(), path.read_bytes() if path.exists() else b'')
            if current == change['before']:
                _best_effort_print(
                    '   curator spool was already at its exact pre-transaction bytes')
                return True
            if current != change['after']:
                _best_effort_print(
                    '   CURATOR ROLLBACK REFUSED: relay spool changed/was consumed '
                    'after this transaction; manual reconciliation is required')
                return False
            _restore_file_snapshot(path, change['before'])
            _best_effort_print('   restored exact pre-transaction curator spool bytes')
            return True
        except BaseException as exc:
            _best_effort_print(
                f'   CURATOR ROLLBACK FAILED: {type(exc).__name__}: {exc}')
            return False

    def commit(self):
        self.closed = True


def _write_json_atomic(path, document):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n',
                         encoding='utf-8')
    os.replace(temporary, path)


def _fomod_plan_snapshot(plan):
    """Return immutable, repository-confined FOMOD-plan provenance."""
    if not plan:
        return None
    root = (pathlib.Path(REPO) / 'records' / 'fomod-plans').resolve()
    candidate = pathlib.Path(plan)
    if not candidate.is_absolute():
        candidate = pathlib.Path(REPO) / candidate
    try:
        path = candidate.resolve(strict=True)
        path.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ValueError(f'FOMOD plan must be one existing file beneath {root}') from exc
    if not path.is_file():
        raise ValueError(f'FOMOD plan is not a regular file: {path}')
    before = path.stat()
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError(f'FOMOD plan changed while being read: {path}')
    try:
        document = json.loads(payload.decode('utf-8-sig'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'FOMOD plan is not valid UTF-8 JSON: {path}') from exc
    if not isinstance(document, dict):
        raise ValueError(f'FOMOD plan root must be a JSON object: {path}')
    return {
        'path': path,
        'relative': path.relative_to(pathlib.Path(REPO).resolve()).as_posix(),
        'bytes': len(payload),
        'sha256': hashlib.sha256(payload).hexdigest().upper(),
    }


def _restore_file_snapshot(path, snapshot):
    path = pathlib.Path(path)
    existed, payload = snapshot
    if existed:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.rollback.tmp')
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    elif path.exists():
        path.unlink()


def _path_digest(path):
    path = pathlib.Path(path)
    payload = path.read_bytes() if path.is_file() else None
    return {
        'exists': path.is_file(),
        'bytes': len(payload) if payload is not None else None,
        'sha256': (hashlib.sha256(payload).hexdigest().upper()
                   if payload is not None else None),
        'payload': payload,
    }


def _tree_digest(root):
    root = pathlib.Path(root)
    if not root.is_dir():
        return {'exists': False, 'sha256': None, 'files': 0}
    rows = []
    for path in sorted((p for p in root.rglob('*') if p.is_file()),
                       key=lambda p: str(p).casefold()):
        rows.append((path.relative_to(root).as_posix().casefold(),
                     path.stat().st_size, patch_impact.sha256_file(path)))
    canonical = '\n'.join(f'{name}\t{size}\t{digest}'
                          for name, size, digest in rows)
    return {'exists': True, 'files': len(rows),
            'sha256': hashlib.sha256(canonical.encode('utf-8')).hexdigest().upper()}


def _mutation_state_snapshot(mod_name):
    profile = pathlib.Path(INSTANCE) / 'profiles' / PROFILE
    return {
        'modName': mod_name,
        'authorities': {
            name: _path_digest(profile / name)
            for name in ('modlist.txt', 'plugins.txt', 'loadorder.txt',
                         'lockedorder.txt', 'settings.ini')
        },
        'targetTree': _tree_digest(pathlib.Path(INSTANCE) / 'mods' / mod_name),
    }


def _restore_mutation_snapshot(snapshot):
    """Restore small profile authorities and quarantine an unexpected new mod.

    Updates are currently refused, so the only supported target before-image
    is an absent directory. If that invariant changes, update support must grow
    a retained before-tree rather than pretending a digest is restorable.
    """
    okay = True
    profile = pathlib.Path(INSTANCE) / 'profiles' / PROFILE
    try:
        for name, state in snapshot.get('authorities', {}).items():
            _restore_file_snapshot(
                profile / name,
                (bool(state.get('exists')), state.get('payload') or b''),
            )
    except BaseException as exc:
        okay = False
        _best_effort_print(
            '   authority before-image restore failed: '
            f'{type(exc).__name__}: {exc}')
    target = pathlib.Path(INSTANCE) / 'mods' / snapshot['modName']
    target_before = snapshot.get('targetTree') or {}
    if not target_before.get('exists') and target.exists():
        try:
            recovery = pathlib.Path(INSTANCE) / '.assistant-recovery'
            recovery.mkdir(parents=True, exist_ok=True)
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                '%Y%m%dT%H%M%S%fZ')
            slug = re.sub(r'[^A-Za-z0-9._-]+', '-', snapshot['modName']).strip('-')
            destination = recovery / f'{stamp}-{slug or "mod"}'
            os.replace(target, destination)
            _best_effort_print(f'   quarantined unjournaled target at {destination}')
        except BaseException as exc:
            okay = False
            _best_effort_print(
                '   unjournaled target quarantine failed: '
                f'{type(exc).__name__}: {exc}')
    elif target_before.get('exists') and _tree_digest(target) != target_before:
        okay = False
        _best_effort_print(
            '   existing target changed but no retained before-tree is available; '
            'manual recovery is required')
    return okay


def _log_ambiguous_recovery(mod_name, controller_result, before, restored, exact,
                            reconciled):
    """Append a durable, payload-free recovery receipt for an ambiguous write."""
    path = pathlib.Path(REPO) / 'records' / 'lifecycle-recovery.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    authorities = {
        name: {key: value for key, value in state.items() if key != 'payload'}
        for name, state in before.get('authorities', {}).items()
    }
    event = {
        'schemaVersion': 1,
        'at': datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'operation': 'ambiguous-mo2-mutation-recovery',
        'modName': mod_name,
        'controllerResult': controller_result,
        'before': {
            'modName': before.get('modName'),
            'authorities': authorities,
            'targetTree': before.get('targetTree'),
        },
        'restored': bool(restored),
        'exactPostcondition': bool(exact),
        'reconciledPostcondition': bool(reconciled),
    }
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def _change_kinds(mod_root):
    """Conservatively classify runtime risk from the installed payload."""
    root = pathlib.Path(mod_root)
    files = [path for path in root.rglob('*') if path.is_file()]
    suffixes = {path.suffix.casefold() for path in files}
    kinds = []
    if '.dll' in suffixes:
        kinds.append('native')
    # Configuration can alter native/plugin/script behavior without adding any
    # executable record of its own.  It therefore needs the risk-2 round-trip
    # contract, not the cheaper asset-only contract. XML is included because
    # SMP and other runtime frameworks commonly use it as executable config.
    if suffixes & {'.ini', '.json', '.toml', '.yaml', '.yml', '.xml',
                   '.cfg', '.conf'}:
        kinds.append('config')
    has_script = '.pex' in suffixes
    has_worldspace = False
    for plugin_path in (path for path in files
                        if path.suffix.casefold() in {'.esp', '.esm', '.esl'}):
        try:
            _records, record_types, _masters = patch_impact.record_keys(plugin_path)
            if record_types & {'WRLD', 'CELL', 'LAND', 'NAVM'}:
                has_worldspace = True
        except Exception:
            # A plan must never under-classify a plugin it could not inspect.
            has_worldspace = True
    for archive in (path for path in files if path.suffix.casefold() in {'.bsa', '.ba2'}):
        if archive.suffix.casefold() == '.ba2':
            # No BA2 indexer is available in this Skyrim-focused tool yet.
            has_script = True
            has_worldspace = True
            continue
        try:
            import modasset
            names = [name.replace('\\', '/').casefold()
                     for name in modasset.BSA(str(archive)).names()]
            has_script = has_script or any(
                name.startswith('scripts/') and name.endswith('.pex') for name in names)
            has_worldspace = has_worldspace or any(
                name.startswith(('lodsettings/', 'meshes/terrain/',
                                  'textures/terrain/', 'grass/'))
                for name in names)
        except Exception:
            has_script = True
            has_worldspace = True
    if has_script:
        kinds.append('script')
    if suffixes & {'.esp', '.esm', '.esl'}:
        kinds.append('plugin')
    if has_worldspace:
        kinds.append('worldspace')
    return kinds or ['asset']


def _impact_path(mod_name, fingerprint, signature):
    slug = re.sub(r'[^a-z0-9]+', '-', mod_name.casefold()).strip('-')[:60] or 'mod'
    return pathlib.Path(REPO) / 'records' / 'impact-receipts' / \
        f'{slug}-{fingerprint[:12].lower()}-{signature[:12].lower()}.json'


def _valid_issue_reference(value):
    text = str(value or '').strip()
    return bool(re.fullmatch(r'#?\d+', text) or re.fullmatch(
        r'https://github\.com/[^/]+/[^/]+/issues/\d+(?:#.*)?', text,
        flags=re.IGNORECASE))


def _mod_child(mod_name):
    """Return the target's one literal MO2 child path, or ``None``."""
    return patch_impact._direct_child(
        pathlib.Path(INSTANCE) / 'mods', str(mod_name))


def _open_lifecycle_errors(exclude_receipt=None):
    """Refuse overlapping changes until the prior build is user-accepted."""
    errors = []
    repo = pathlib.Path(REPO)
    ledger = load()
    referenced_receipts = {
        (repo / str(row.get('impactReceipt'))).resolve()
        for row in ledger.get('mods', [])
        if str(row.get('impactReceipt') or '').strip()
    }
    excluded = pathlib.Path(exclude_receipt).resolve() if exclude_receipt else None
    receipt_dir = repo / 'records' / 'impact-receipts'
    if receipt_dir.is_dir():
        for path in receipt_dir.glob('*.json'):
            resolved = path.resolve()
            if resolved not in referenced_receipts and resolved != excluded:
                errors.append(f'unresolved/unreferenced impact draft: {path.name}')
    try:
        status = verification_status.audit(
            repo=repo, instance=pathlib.Path(INSTANCE), profile=PROFILE,
            ledger_path=pathlib.Path(LEDGER))
    except BaseException as exc:
        errors.append(
            'verification lifecycle audit is unreadable: '
            f'{type(exc).__name__}: {exc}')
        return errors
    # A raw, writable ``plan.status`` is not authority. The shared deep audit
    # binds every row to its exact ledger contract/current fingerprint and
    # re-hashes writer-shaped evidence before it can be considered complete.
    for row in status.get('invalid', []):
        errors.append(
            f"invalid prior lifecycle for {row.get('modName')}: " +
            '; '.join(str(item) for item in row.get('errors', [])))
    for row in status.get('pending', []):
        errors.append(
            f"prior lifecycle for {row.get('modName')} is incomplete: " +
            '; '.join(str(item) for item in row.get('pending', [])))
    for row in status.get('complete', []):
        if str(row.get('planStatus') or '').casefold() != 'playtest-accepted':
            errors.append(
                f"prior lifecycle for {row.get('modName')} is "
                f"{row.get('planStatus') or 'statusless'}, not playtest-accepted")
    return errors


def _curation_precondition(mid, mod_name):
    """Require readable, non-contradictory Keep/Skip state before mutation."""
    try:
        coverage = keep_coverage.audit()
        decisions = keep_coverage.curator_decisions()
        # The only queue defect an install may heal is an otherwise valid,
        # expired SSE Keep for this exact target.  queue_keep() atomically
        # refreshes it only after the install's reviewed transaction succeeds;
        # all other queue errors remain fail-closed here.
        queued = keep_coverage.queued_keeps(refresh_target=int(mid))
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
                      if keep_coverage.canonical_mod_id(
                          e.get('mod', {}).get('modId')) == int(mid)
                      and str(e.get('mod', {}).get('game') or '').casefold() ==
                          'skyrimspecialedition']
    pending_states = {str(e.get('status') or '').casefold() for e in pending_target}
    if any(state != 'keep' for state in pending_states):
        print(f'REFUSING install: Nexus {mid} has contradictory pending curator '
              f'state: {", ".join(sorted(pending_states)) or "(blank)"}')
        return False

    failures = []
    for row in coverage['installedWithoutKeep']:
        state = 'Keep queued but not applied' if row['modId'] in queued else 'installed without Keep'
        failures.append('%s: %d (%s)' %
                        (state, row['modId'], ', '.join(row['mods'])))
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
    """#164: no profile mutation while any Skyrim process is alive.

    Human-presence evidence enriches the refusal and preserves exit 88 when a
    person is detected.  It is never permission to mutate an apparently idle
    game: the sanctioned launch chain owns the profile claim for its complete
    lifetime, and an unclaimed process is an unsafe unknown state.
    """
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq SkyrimSE.exe'],
                       capture_output=True, text=True)
    if 'skyrimse.exe' not in (r.stdout or '').lower():
        return
    v = HP.judge()
    print(f'REFUSING {what}: SkyrimSE.exe is running ({HP.describe(v)}); '
          'profile mutation is forbidden under every live game process')
    if v['human']:
        HP.log_refusal(v, f'install_mod {what}')
        sys.exit(HP.HUMAN_AT_CONTROLS)
    sys.exit(claim.ExTempFail)


def install(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None,
            impact_receipt=None, issue=None, crash_fix=False):
    if _mod_child(mod_name) is None:
        print('REFUSING install: mod_name must be one literal MO2 mod folder '
              f'name, not a path: {mod_name!r}')
        return 64
    if not _valid_issue_reference(issue):
        print('REFUSING install: --issue must be a GitHub issue number or URL so '
              'the change and every open decision have a durable tracker')
        return 1
    if replace:
        print('REFUSING update: before/after payload delta receipts for removed '
              'records/assets are not implemented yet (#235). Replacing a mod '
              'without them could falsely certify a stale owned patch.')
        return 78
    refuse_if_human_playing(f'install {mid} "{mod_name}"')
    with claim.guard(None, f'install_mod {mid} "{mod_name}"', ttl=45) as claim_record:
        # Reconcile only after acquiring the writer claim. A clean result read
        # before the claim would be stale if another controller changed the
        # profile while we waited.
        state = profile_reconcile.reconcile()
        if not state['reconciled']:
            print('REFUSING install: the existing profile is not reconciled (#102).')
            print(profile_reconcile.render(state))
            return 1
        return _install(mid, mod_name, prefer, plan, replace, file_id,
                        impact_receipt, issue, crash_fix,
                        claim_owner=claim_record.get('owner'),
                        claim_lease=(claim_record.get('holderLeaseId') or
                                     claim_record.get('leaseId')))


def _install(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None,
             impact_receipt=None, issue=None, crash_fix=False, claim_owner=None,
             claim_lease=None):
    logical = _LogicalInstall()
    try:
        result = _install_impl(mid, mod_name, prefer, plan, replace, file_id,
                               impact_receipt, issue, crash_fix, claim_owner,
                               claim_lease, logical)
    except BaseException as exc:
        okay = True
        if logical.applied and not logical.closed:
            okay = logical.abort(
                f'unexpected {type(exc).__name__}: {exc}')
        _best_effort_print(
            f'UNEXPECTED post-apply failure: {type(exc).__name__}: {exc}')
        if not okay:
            _best_effort_print(
                '   logical transaction remains BROKEN; manual recovery is required')
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return 1
    if result and logical.applied and not logical.closed:
        okay = logical.abort(f'install returned failure code {result}')
        if not okay:
            _best_effort_print(
                '   logical transaction remains BROKEN; manual recovery is required')
    return result


def _install_impl(mid, mod_name, prefer=None, plan=None, replace=False, file_id=None,
                  impact_receipt=None, issue=None, crash_fix=False,
                  claim_owner=None, claim_lease=None, logical=None):
    logical = logical or _LogicalInstall()
    # `_install` is also an intentionally testable/internal entry point. Keep
    # the path boundary here as well so no bypass can snapshot, quarantine, or
    # pass traversal syntax to the controller.
    if _mod_child(mod_name) is None:
        _best_effort_print(
            'REFUSING install: mod_name must be one literal MO2 mod folder '
            f'name, not a path: {mod_name!r}')
        return 64
    # The public wrapper already refuses updates. Keep the same fail-closed
    # boundary here: tests/importers must not reach the incomplete replacement
    # branch, whose digest-only before-image cannot restore an existing target
    # after an ambiguous first controller mutation.
    if replace:
        _best_effort_print(
            'REFUSING update: the retained before/after payload transaction is '
            'not implemented yet (#235); --replace is unavailable')
        return 78
    try:
        fomod_plan = _fomod_plan_snapshot(plan)
    except (OSError, ValueError) as exc:
        _best_effort_print(f'REFUSING install: {exc}')
        return 1
    impact_receipt_path = None
    impact_receipt_bytes = None
    if impact_receipt:
        impact_receipt_path = pathlib.Path(impact_receipt).resolve()
        allowed = (pathlib.Path(REPO) / 'records' / 'impact-receipts').resolve()
        try:
            impact_receipt_path.relative_to(allowed)
        except ValueError:
            print(f'REFUSING install: impact receipt must live beneath {allowed}')
            return 1
        try:
            # One immutable snapshot feeds both semantic validation and the
            # ledger hash. Re-reading here later would create a receipt TOCTOU.
            impact_receipt_bytes = impact_receipt_path.read_bytes()
        except OSError as exc:
            print(f'REFUSING install: impact receipt is unreadable: '
                  f'{type(exc).__name__}: {exc}')
            return 1
    open_lifecycle = _open_lifecycle_errors(impact_receipt_path)
    if open_lifecycle:
        print('REFUSING install: another lifecycle is still open (#228/#235):')
        for error in open_lifecycle:
            print('   ' + error)
        print('   finish/accept it, or explicitly archive an abandoned draft; '
              'batch semantics are not implemented yet')
        return 1
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
    sha = patch_impact.sha256_file(pathlib.Path(archive))

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
    identity_error = _replacement_identity_error(previous, mid) if replace else None
    if identity_error:
        print('REFUSING update: ' + identity_error)
        return 1
    try:
        before_plugins = _plugin_states()
    except RuntimeError as exc:
        print(f'REFUSING install: {exc}')
        return 1
    desired_mod_enabled = bool(previous.get('enabled')) if replace else True

    if not _curation_precondition(mid, mod_name):
        return 1
    # Stage every payload disabled.  Patch impact is reviewed before either its
    # assets or plugins become live, so a rejected/missing receipt never has a
    # transient activation window even though the game is guaranteed closed.
    refuse_if_human_playing(f'install {mid} "{mod_name}" at mutation boundary')
    if claim_owner:
        live_claim = claim.read()
        if (live_claim is None or claim.is_stale(live_claim) or
                not claim.same_holder(live_claim, claim_owner, claim_lease)):
            print('REFUSING install at mutation boundary: the profile claim was '
                  'lost or expired during download/audit preparation')
            return 1
    args = ['mod-install', archive, mod_name, '--disable']
    if replace:
        args += ['--replace']
    if fomod_plan:
        try:
            if _fomod_plan_snapshot(fomod_plan['path']) != fomod_plan:
                raise OSError('FOMOD plan bytes changed before controller invocation')
        except (OSError, ValueError) as exc:
            print(f'REFUSING install: {exc}')
            return 1
        args += ['--install-plan', str(fomod_plan['path'])]
    before_mutation = _mutation_state_snapshot(mod_name)
    # Recovery ownership begins before the controller call.  The call can
    # mutate successfully and then fail while decoding output or scanning its
    # journal; arming after it returns leaves that entire ambiguity window
    # outside the logical transaction.
    logical.arm(ledger_snapshot, before_mutation)

    def abort_applied(message):
        rolled_back = logical.abort(message)
        _best_effort_print(message)
        if not rolled_back:
            _best_effort_print(
                '   logical transaction remains BROKEN; manual recovery is required')
        return 1

    try:
        res = mo2_mutation(*args)
    except BaseException:
        # `_install` owns the common exception path so SystemExit,
        # KeyboardInterrupt, parser/type errors and post-call journal failures
        # all run the same exact-state cleanup before they propagate/return.
        raise
    if not res.get('ok'):
        try:
            changed = _mutation_state_snapshot(mod_name) != before_mutation
        except BaseException:
            changed = True
        restored = logical.abort('mod-install failed or returned an ambiguous result')
        exact = False
        reconciled = False
        if changed:
            try:
                exact = _mutation_state_snapshot(mod_name) == before_mutation
            except BaseException:
                exact = False
            try:
                reconciled = profile_reconcile.reconcile().get('reconciled') is True
            except BaseException as exc:
                _best_effort_print(
                    '   recovery reconciliation crashed: '
                    f'{type(exc).__name__}: {exc}')
            try:
                _log_ambiguous_recovery(mod_name, res, before_mutation,
                                        restored, exact, reconciled)
            except BaseException as exc:
                _best_effort_print(
                    '   RECOVERY RECEIPT WRITE FAILED: '
                    f'{type(exc).__name__}: {exc}')
                restored = False
            if not (restored and exact and reconciled):
                _best_effort_print(
                    '   AMBIGUOUS MUTATION RECOVERY FAILED; profile is blocked '
                    'pending manual recovery')
            else:
                _best_effort_print(
                    '   ambiguous mutation recovered to the exact pre-call state')
        _best_effort_print('install failed:', res)
        return 1
    if not logical.add(res.get('transaction')):
        return abort_applied('install applied without a rollback transaction ID')
    if res.get('recoveredFromJournal'):
        _best_effort_print(
            f"   controller response was ambiguous; recovered committed "
            f"transaction {res.get('transaction')} from its journal")
    _best_effort_print(
        f"installed {mod_name}  transaction {res.get('transaction')}")

    try:
        added = plugins_of(mod_name)
    except Exception as exc:
        return abort_applied(
            f'installed payload inventory failed: {type(exc).__name__}: {exc}')
    # New installs will activate their selected plugins only after review.
    # Updates preserve exact pre-update active membership; a newly introduced
    # plugin stays inactive until explicitly reviewed.
    desired_active = _desired_active_plugins(
        added, desired_mod_enabled, replace, before_plugins)

    operation = 'update' if replace else 'install'
    try:
        impact = patch_impact.audit(
            operation, [], [mod_name], pathlib.Path(INSTANCE), PROFILE,
            pathlib.Path(LEDGER))
        impact['source'] = {
            'game': 'skyrimspecialedition',
            'modId': int(mid),
            'fileId': int(f['file_id']),
            'archiveSha256': sha.upper(),
            'issue': str(issue),
            **({'fomodPlan': fomod_plan['relative'],
                'fomodPlanSha256': fomod_plan['sha256']}
               if fomod_plan else {}),
        }
        impact['intakeReview'] = {
            'userApproval': {'approved': False, 'evidence': ''},
            'fileSelection': {'reviewed': False, 'evidence': ''},
            'permissions': {'classification': '', 'evidence': ''},
            'requirements': {
                'reviewed': False, 'requiredPatches': [],
                'requiredPlugins': {}, 'evidence': ''},
            'compatibility': {
                'reviewed': False, 'lootEvidence': '', 'conflictEvidence': '',
                'openDecisions': [],
            },
        }
        impact['auditSignature'] = patch_impact.audit_signature(impact)
    except Exception as exc:
        return abort_applied(
            f'patch-impact audit failed: {type(exc).__name__}: {exc}')

    default_impact_path = _impact_path(
        mod_name, impact['changedFingerprint']['sha256'], impact['auditSignature'])
    if impact_receipt_path is None:
        if default_impact_path.exists():
            return abort_applied(
                'owned-patch review is required before activation; preserving '
                f'existing draft/receipt {default_impact_path} (pass it explicitly '
                'with --impact-receipt after review)')
        _write_json_atomic(default_impact_path, impact)
        return abort_applied(
            'owned-patch review is required before activation; wrote draft receipt '
            f'{default_impact_path}')
    try:
        reviewed_impact = json.loads(impact_receipt_bytes.decode('utf-8-sig'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return abort_applied(
            f'impact receipt is unreadable: {type(exc).__name__}: {exc}')
    impact_errors = patch_impact.validate_receipt(
        impact, reviewed_impact, instance=pathlib.Path(INSTANCE),
        profile=PROFILE, ledger_path=pathlib.Path(LEDGER))
    if impact_errors:
        print(patch_impact.render(impact, impact_errors))
        if impact_receipt_path != default_impact_path:
            if default_impact_path.exists():
                print(f'preserved existing current draft {default_impact_path}')
            else:
                _write_json_atomic(default_impact_path, impact)
                print(f'wrote current draft receipt {default_impact_path}')
        return abort_applied('owned-patch impact receipt was rejected')

    # The receipt is valid for this exact payload and current owned-patch
    # topology. Only now may the mod enter the active profile.
    if desired_mod_enabled:
        r = mo2_mutation('mod-enable', mod_name)
        if not r.get('ok'):
            return abort_applied(f'mod activation failed after impact review: {r}')
        if not logical.add(r.get('transaction')):
            return abort_applied(
                'mod activation returned no rollback transaction ID')
        print(f'   mod {mod_name}: enabled after patch-impact acceptance')
    try:
        current_plugins = _plugin_states()
    except RuntimeError as exc:
        return abort_applied(f'install applied but plugin-state verification failed: {exc}')
    for p in added:
        plugin_key = p.casefold()
        desired = plugin_key in desired_active
        actual = current_plugins.get(plugin_key, False)
        if actual == desired:
            continue
        r = mo2_mutation('plugin-enable' if desired else 'plugin-disable', p)
        if not r.get('ok'):
            return abort_applied(f"   plugin {p}: state update FAILED: {r}")
        if not logical.add(r.get('transaction')):
            return abort_applied(
                f'plugin {p}: state update returned no rollback transaction ID')
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

    try:
        if fomod_plan and _fomod_plan_snapshot(fomod_plan['path']) != fomod_plan:
            return abort_applied('FOMOD plan changed during installation; provenance '
                                 'cannot identify the mapping the controller applied')
        impact_relative = impact_receipt_path.relative_to(
            pathlib.Path(REPO)).as_posix()
        impact_hash = hashlib.sha256(impact_receipt_bytes).hexdigest().upper()
        change_kinds = _change_kinds(pathlib.Path(INSTANCE) / 'mods' / mod_name)
        test_plan = verification_plan.make_plan(
            change_kinds,
            f'{operation} Nexus {mid} {mod_name}',
            str(issue),
            crash_fix,
            fingerprint=None,
            source={
                'operation': operation,
                'game': 'skyrimspecialedition',
                'modName': mod_name,
                'modId': int(mid),
                'fileId': int(f['file_id']),
                'archiveSha256': sha.upper(),
                'impactReceipt': impact_relative,
                'impactReceiptSha256': impact_hash,
                **({'fomodPlan': fomod_plan['relative'],
                    'fomodPlanSha256': fomod_plan['sha256']}
                   if fomod_plan else {}),
            },
        )
        logical.test_plan_path = (pathlib.Path(REPO) / 'records' / 'test-plans' /
                                  f"{test_plan['testId']}.json")
        test_plan_relative = logical.test_plan_path.relative_to(
            pathlib.Path(REPO)).as_posix()
    except Exception as exc:
        return abort_applied(
            f'change-receipt preparation failed: {type(exc).__name__}: {exc}')

    # One source archive can legitimately be installed as multiple component
    # folders (core, official patch, optional assets). File ID is provenance,
    # not row identity. Replace only the row for this exact physical folder;
    # global file-ID deduplication silently erased sibling components.
    led['mods'] = [m for m in led['mods']
                   if str(m.get('modName') or '').casefold() != mod_name.casefold()]
    try:
        disabled_plugins = sorted(
            (p for p in added
             if desired_mod_enabled and p.casefold() not in desired_active),
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
            'issue': str(issue),
            'lifecycleOperation': operation,
            'lifecyclePolicyVersion': 1,
            'impactReceipt': impact_relative,
            'impactReceiptSha256': impact_hash,
            'verificationPlan': test_plan_relative,
            'verificationTestId': test_plan['testId'],
            'verificationContractSignature': test_plan['contractSignature'],
            **({'fomodPlan': fomod_plan['relative'],
                'fomodPlanSha256': fomod_plan['sha256']}
               if fomod_plan else {}),
        }
        row = _ledger_row(previous, **current)
        if not fomod_plan:
            row.pop('fomodPlan', None)
            row.pop('fomodPlanSha256', None)
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
        logical.ledger_changed = True
        save(led)
    except Exception as exc:
        return abort_applied(
            f'install applied but ledger commit failed: {type(exc).__name__}: {exc}')
    print(f'ledger now holds {len(led["mods"])} mods -> {LEDGER}')
    try:
        state = profile_reconcile.reconcile()
    except Exception as exc:
        return abort_applied(
            f'post-install reconciliation crashed: {type(exc).__name__}: {exc}')
    if not state['reconciled']:
        print(profile_reconcile.render(state))
        return abort_applied(
            'post-install profile does not reconcile; reverting the logical transaction (#102)')
    try:
        test_plan['buildFingerprint'] = verification_plan.build_fingerprint(
            pathlib.Path(INSTANCE), PROFILE, pathlib.Path(LEDGER))
        test_plan['contractSignature'] = verification_plan.contract_signature(test_plan)
        row['verificationContractSignature'] = test_plan['contractSignature']
        save(led)
        stable_fingerprint = verification_plan.build_fingerprint(
            pathlib.Path(INSTANCE), PROFILE, pathlib.Path(LEDGER))
        if stable_fingerprint['sha256'] != test_plan['buildFingerprint']['sha256']:
            return abort_applied(
                'verification fingerprint changed while anchoring its contract signature')
        _write_json_atomic(logical.test_plan_path, test_plan)
        print(f"verification plan {test_plan['testId']} -> {logical.test_plan_path}")
    except Exception as exc:
        return abort_applied(
            f'verification-plan creation failed: {type(exc).__name__}: {exc}')
    keep_okay, curator_change = queue_keep(
        mid, mod_name, with_receipt=True, logical=logical)
    if not keep_okay:
        return abort_applied(
            'required Keep could not be queued; reverting the logical transaction')
    logical.curator_change = curator_change
    logical.commit()
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


def queue_keep(mid, mod_name, with_receipt=False, logical=None):
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
    before = None
    after = None
    claimed = None
    published = False
    try:
        os.makedirs(spool, exist_ok=True)
        if os.path.exists(pending):
            claim_name = (pending + f'.{os.getpid()}.' +
                          datetime.datetime.now(datetime.timezone.utc)
                          .strftime('%Y%m%dT%H%M%S%fZ') + '.claimed')
            # Atomically take the producer side of the spool. The browser relay
            # either consumed the old path first (then this raises and we retry
            # on a later install), or we own these exact bytes until publish.
            os.rename(pending, claim_name)
            claimed = pathlib.Path(claim_name)
            original = claimed.read_bytes()
            before = (True, original)
            batch = json.loads(original.decode('utf-8-sig'))
            if not isinstance(batch, list):
                raise ValueError('curator pending batch is not a JSON array')
        else:
            before = (False, b'')
            batch = []
        noncanonical = [e for e in batch if isinstance(e, dict) and
                        isinstance(e.get('mod'), dict) and
                        keep_coverage.canonical_mod_id(
                            e['mod'].get('modId')) is None]
        if noncanonical:
            print(f'   KEEP QUEUE REFUSED for {mid}: existing batch contains '
                  'a noncanonical/non-positive Nexus modId')
            if claimed:
                os.rename(claimed, pending)
                claimed = None
            return (False, None) if with_receipt else False
        same_id = [e for e in batch
                   if keep_coverage.canonical_mod_id(
                       e.get('mod', {}).get('modId')) == int(mid)
                   and str(e.get('mod', {}).get('game') or '').casefold() ==
                       'skyrimspecialedition']
        if any(str(e.get('status') or '').casefold() != 'keep' for e in same_id):
            states = ', '.join(sorted({str(e.get('status') or '(blank)') for e in same_id}))
            print(f'   KEEP QUEUE REFUSED for {mid}: existing Skyrim SE pending '
                  f'decision is {states}, not Keep')
            print('   resolve the contradictory curator decision explicitly; '
                  'an install must never reinterpret Skip as Keep')
            if claimed:
                os.rename(claimed, pending)
                claimed = None
            return (False, None) if with_receipt else False
        valid = [e for e in same_id
                 if keep_coverage.pending_keep_id(e) == int(mid)]
        if len(same_id) == 1 and len(valid) == 1:
            # Republish the bytes atomically; we temporarily claimed the path
            # so a relay consumer cannot race a later producer overwrite.
            desired = before[1]
            tmp = (pending + f'.{os.getpid()}.' +
                   datetime.datetime.now(datetime.timezone.utc)
                   .strftime('%Y%m%dT%H%M%S%fZ') + '.tmp')
            with open(tmp, 'xb') as fh:
                fh.write(desired)
            os.rename(tmp, pending)  # Windows: fail rather than replace a peer
            published = True
            if claimed:
                claimed.unlink()
            print(f'keep {mid} already queued')
            return (True, None) if with_receipt else True
        if same_id:
            batch = [entry for entry in batch if entry not in same_id]
            print(f'   refreshing {len(same_id)} stale/duplicate Keep queue row(s) for {mid}')
        batch.append({'status': 'keep', 'mod': {
            'game': 'skyrimspecialedition', 'modId': str(mid),
            'title': mod_name,
            'sourceUrl': f'https://www.nexusmods.com/skyrimspecialedition/mods/{mid}'},
            'queuedAt': datetime.datetime.now(datetime.timezone.utc)
                                .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'source': 'audit/install_mod.py'})
        desired = json.dumps(batch, ensure_ascii=False, indent=1).encode('utf-8')
        tmp = (pending + f'.{os.getpid()}.' +
               datetime.datetime.now(datetime.timezone.utc)
               .strftime('%Y%m%dT%H%M%S%fZ') + '.tmp')
        with open(tmp, 'xb') as fh:
            fh.write(desired)
        after = (True, desired)
        receipt = {'path': pending, 'before': before, 'after': after}
        if logical is not None:
            # Register the rollback receipt before the atomic commit: even an
            # interrupt/fault immediately after os.replace remains recoverable.
            logical.curator_change = receipt
        os.rename(tmp, pending)  # publish only if no uncoordinated writer appeared
        published = True
        if claimed:
            claimed.unlink()
        print(f'keep {mid} queued for the curator ({len(batch)} in batch) -> {pending}')
        print('   it applies on the next Nexus page load; '
              'py -3 audit/keep_coverage.py is the gate')
        return (True, receipt) if with_receipt else True
    except BaseException as exc:
        # If publication never happened, put the atomically claimed old batch
        # back. If it did happen and this logical operation is failing, restore
        # only our byte-exact publication; never overwrite a consumed/changed
        # spool. A stranded .claimed file remains a preflight blocker.
        try:
            current = (os.path.exists(pending),
                       pathlib.Path(pending).read_bytes()
                       if os.path.exists(pending) else b'')
            if not published and claimed and claimed.exists() and not current[0]:
                os.rename(claimed, pending)
            elif published and before is not None and after is not None and current == after:
                _restore_file_snapshot(pending, before)
                if claimed and claimed.exists():
                    claimed.unlink()
        except Exception as spool_exc:
            print('   KEEP QUEUE SPOOL RECOVERY FAILED: '
                  f'{type(spool_exc).__name__}: {spool_exc}')
        # Standalone callers have no outer logical transaction. Restore only
        # when the file is either unchanged or byte-exactly our write; never
        # clobber a concurrently consumed/changed spool.
        if (logical is None and before is not None and after is not None
                and published):
            try:
                current = (os.path.exists(pending),
                           pathlib.Path(pending).read_bytes()
                           if os.path.exists(pending) else b'')
                if current == after:
                    _restore_file_snapshot(pending, before)
                elif current != before:
                    print('   KEEP QUEUE ROLLBACK REFUSED: relay spool changed '
                          'concurrently; manual reconciliation is required')
            except Exception as rollback_exc:
                print('   KEEP QUEUE ROLLBACK FAILED: '
                      f'{type(rollback_exc).__name__}: {rollback_exc}')
        print(f'   KEEP QUEUE FAILED for {mid}: {type(exc).__name__}: {exc}')
        print('   the lifecycle transaction is incomplete until this is repaired')
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return (False, None) if with_receipt else False


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
    print('REFUSING sort: load-order mutation is not yet routed through the '
          'patch-impact and verification transaction required by #235. Use '
          'read-only LOOT diagnostics until that controller lands.')
    return 78


def _legacy_sort_order_disabled():
    """Prior implementation retained as migration reference; never dispatched."""
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
        impact_receipt = None
        issue = None
        crash_fix = False
        if '--prefer' in a:
            i = a.index('--prefer'); prefer = a[i + 1]; a = a[:i] + a[i + 2:]
        if '--plan' in a:
            i = a.index('--plan'); plan = a[i + 1]; a = a[:i] + a[i + 2:]
        if '--replace' in a:
            a.remove('--replace'); replace = True
        if '--impact-receipt' in a:
            i = a.index('--impact-receipt')
            impact_receipt = a[i + 1]
            a = a[:i] + a[i + 2:]
        if '--issue' in a:
            i = a.index('--issue')
            issue = a[i + 1]
            a = a[:i] + a[i + 2:]
        if '--crash-fix' in a:
            a.remove('--crash-fix'); crash_fix = True
        file_id = None
        if '--file' in a:
            i = a.index('--file'); file_id = int(a[i + 1]); a = a[:i] + a[i + 2:]
        try:
            sys.exit(install(int(a[0]), a[1], prefer, plan, replace, file_id,
                             impact_receipt, issue, crash_fix))
        except claim.ClaimHeld as e:
            print(f'CLAIM HELD - not installing: {e}'); sys.exit(claim.ExTempFail)
