"""Work claim on the live MO2 instance: one owner mutates the profile at a time.

Born 2026-09-01 from #103: two assistant sessions and their agents installed
the same mod twice (FSMP), nearly did it again (VHR), and unstarred plugins
under each other's sorts, because nothing told either side the other was in
the middle of something. The controller's `.mo2-headless.lock` serialises one
MO2Headless call; it says nothing about the ten calls that make up an install,
a sort, or a launch.

The claim is a small JSON file in the instance root that names WHO is working
on the profile, WHY, and until WHEN:

  mo2-instances/skyrim-se/.assistant-claim.json
  {"owner": "sol/farming-store", "pid": 1234, "purpose": "...",
   "acquiredAt": "2026-09-01T18:20:00-05:00", "ttlMinutes": 30,
   "expiresAt": "...", "host": "..."}

  # A multi-command shell session supplies one unguessable lease to every call:
  set SKYRIM_CLAIM_LEASE=<random-guid>
  py -3 audit/claim.py acquire --owner NAME --purpose "why" [--ttl 30] [--wait 600]
  py -3 audit/claim.py renew   --owner NAME [--ttl 30]
  py -3 audit/claim.py release --owner NAME
  py -3 audit/claim.py check   [--owner NAME]      # exit 0 free-or-mine, 1 held by another
  py -3 audit/claim.py status                      # print the record, exit 0

Rules the code enforces:

- `acquire` is atomic (O_EXCL create). A claim held by ANOTHER owner refuses
  (exit 75) unless it is stale; `--wait N` polls for up to N seconds first.
- Stale = past `expiresAt`, or `pidBound` is set and that pid is gone. A stale
  takeover is logged as a WARNING to stderr and to records/claim-log.jsonl with
  the record it replaced; it is never silent.
- Re-entry requires the same lease ID or exact creating process, not merely the
  same friendly owner string. Thus a child in one workflow can renew its outer
  claim, while two sibling agents named alike still serialize.
- `release` by a different owner is refused; `--force` overrides and is logged.
- The owner name defaults to $SKYRIM_CLAIM_OWNER so one export covers a
  whole session's calls. There is no anonymous claim.

Python API, for the scripts that mutate the profile:

    import claim
    with claim.guard('install_mod', 'install SkyUI', ttl=30):
        ...   # released on exit unless an outer claim by the same owner exists

    rec = claim.held_by_other(owner)   # None, or the blocking record

Who must hold it: every profile-mutating step - install_mod.py install/sort,
launch_verify.py, launch_skyrim.ps1, any hand-driven MO2Headless mutation or
INI/config edit. Read-only checks (verify, plugin-list, preflight) do not.
"""
import contextlib, datetime, getpass, hashlib, io, json, os, pathlib, secrets, socket, subprocess, sys, threading, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
CLAIM = os.path.join(INSTANCE, '.assistant-claim.json')
LOG = os.path.join(REPO, 'records', 'claim-log.jsonl')
DEFAULT_TTL = 30
ExTempFail = 75
_PROCESS_GUARD = threading.RLock()


class ClaimHeld(Exception):
    """Raised by acquire() when another owner holds a live claim."""
    def __init__(self, record):
        self.record = record
        super().__init__(describe(record))


@contextlib.contextmanager
def _claim_mutex(timeout=30):
    """Serialize claim-file compare/write sequences across processes.

    O_EXCL protects creation when the claim is absent, but it cannot make a
    stale-record read followed by ``os.replace`` a compare-and-swap. A tiny
    directory lock closes that takeover race. Its owner record makes a lock
    left by a killed process recoverable without stealing from a live one.
    """
    lock_dir = CLAIM + '.mutex'
    owner_path = os.path.join(lock_dir, 'owner.json')
    deadline = time.monotonic() + max(1, timeout)
    while True:
        try:
            os.mkdir(lock_dir)
            with io.open(owner_path, 'w', encoding='utf-8') as stream:
                json.dump({
                    'pid': os.getpid(),
                    'pidStarted': pid_start_identity(os.getpid()),
                    'createdAt': _iso(_now()),
                }, stream)
            break
        except FileExistsError:
            stale = False
            try:
                with io.open(owner_path, encoding='utf-8') as stream:
                    owner = json.load(stream)
                stale = not pid_alive(owner.get('pid'))
                expected = owner.get('pidStarted')
                actual = pid_start_identity(owner.get('pid'))
                if expected and actual and str(expected) != str(actual):
                    stale = True
            except Exception:
                try:
                    stale = time.time() - os.path.getmtime(lock_dir) > 30
                except OSError:
                    continue
            if stale:
                try:
                    if os.path.exists(owner_path):
                        os.unlink(owner_path)
                    os.rmdir(lock_dir)
                except (FileNotFoundError, OSError):
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError('timed out waiting for the claim-file mutex')
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            os.unlink(owner_path)
        except FileNotFoundError:
            pass
        try:
            os.rmdir(lock_dir)
        except FileNotFoundError:
            pass


def _now():
    return datetime.datetime.now().astimezone()


def _iso(t):
    return t.replace(microsecond=0).isoformat()


def _parse(s):
    try:
        parsed = datetime.datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None
    # Claims are compared with an aware local timestamp.  Treat a legacy or
    # malformed timezone-less value as untrusted/stale instead of letting the
    # comparison raise TypeError and bypass normal claim diagnostics.
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def pid_alive(pid):
    """True if a process with this pid exists. Win32 OpenProcess through ctypes;
    a pid that cannot be opened for query does not exist (or is not ours to see,
    which for a claim written by this user means the same thing)."""
    if not pid:
        return False
    try:
        import ctypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        h = k32.OpenProcess(0x1000, False, int(pid))    # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            code = ctypes.c_ulong()
            if k32.GetExitCodeProcess(h, ctypes.byref(code)):
                return code.value == 259                # STILL_ACTIVE
            return True
        finally:
            k32.CloseHandle(h)
    except Exception:
        return True                                     # cannot tell: assume alive


def pid_start_identity(pid):
    """Windows process creation FILETIME, guarding against PID reuse."""
    if not pid:
        return None
    try:
        import ctypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        h = k32.OpenProcess(0x1000, False, int(pid))
        if not h:
            return None
        try:
            created = ctypes.c_ulonglong()
            exited = ctypes.c_ulonglong()
            kernel = ctypes.c_ulonglong()
            user = ctypes.c_ulonglong()
            if not k32.GetProcessTimes(
                    h, ctypes.byref(created), ctypes.byref(exited),
                    ctypes.byref(kernel), ctypes.byref(user)):
                return None
            return str(created.value)
        finally:
            k32.CloseHandle(h)
    except Exception:
        return None


def _same_process(holder, pid=None, pid_started=None):
    if not isinstance(holder, dict):
        return False
    pid = os.getpid() if pid is None else pid
    if str(holder.get('pid')) != str(pid):
        return False
    expected = holder.get('pidStarted')
    actual = pid_start_identity(pid) if pid_started is None else pid_started
    return not expected or not actual or str(expected) == str(actual)


def _holder_live(holder):
    if not isinstance(holder, dict) or not pid_alive(holder.get('pid')):
        return False
    expected = holder.get('pidStarted')
    actual = pid_start_identity(holder.get('pid'))
    return not (expected and actual and str(expected) != str(actual))


def _active_holder(rec):
    active = rec.get('activeHolder') if isinstance(rec, dict) else None
    return active if isinstance(active, dict) else None


def _session_holder(rec, owner, lease=None, pid=None, pid_started=None):
    """Authorize the durable session, not an in-flight mutating process."""
    if not rec or rec.get('owner') != owner:
        return False
    lease = lease or os.environ.get('SKYRIM_CLAIM_LEASE')
    if lease and rec.get('leaseId'):
        return secrets.compare_digest(str(lease), str(rec['leaseId']))
    return _same_process(rec, pid, pid_started)


def read():
    """The current record, or None. A malformed file is reported as a record
    with owner '?' so it is never mistaken for 'free'."""
    if not os.path.exists(CLAIM):
        return None
    try:
        return json.load(io.open(CLAIM, encoding='utf-8'))
    except Exception as e:
        return {'owner': '?', 'purpose': f'unreadable claim file: {e}',
                'acquiredAt': None, 'expiresAt': None, 'pid': None, 'malformed': True}


def is_stale(rec):
    if rec is None:
        return False
    if rec.get('malformed'):
        return True
    # An unbound shell/session claim may lend one process-scoped child holder
    # at a time.  That live child is stronger than the session TTL: expiring
    # the parent record while it mutates would re-open the original race.
    active = _active_holder(rec)
    if active and _holder_live(active):
        return False
    # A claim owned by a live, pid-bound controller cannot become stealable in
    # the middle of a slow download/hash/FOMOD merely because its advisory TTL
    # elapsed. The process lifetime is the stronger lease. Unbound/manual
    # claims still expire normally so an abandoned shell claim is recoverable.
    if rec.get('pidBound'):
        if not pid_alive(rec.get('pid')):
            return True
        expected_start = rec.get('pidStarted')
        actual_start = pid_start_identity(rec.get('pid'))
        if expected_start and actual_start:
            return str(expected_start) != str(actual_start)
        # Legacy bound records lack a creation-time identity and cannot safely
        # defeat TTL forever because the PID may have been reused.
        if expected_start:
            return False
    exp = _parse(rec.get('expiresAt'))
    if exp is None or exp < _now():
        return True
    return False


def describe(rec):
    if rec is None:
        return 'free'
    left = ''
    exp = _parse(rec.get('expiresAt'))
    if exp:
        secs = (exp - _now()).total_seconds()
        left = f', {"expired " + str(int(-secs // 60)) + " min ago" if secs < 0 else str(int(secs // 60)) + " min left"}'
    active = _active_holder(rec)
    active_text = (f', active pid {active.get("pid")} for '
                   f'"{active.get("purpose")}"') if active and _holder_live(active) else ''
    return (f'held by {rec.get("owner")} (pid {rec.get("pid")}) for '
            f'"{rec.get("purpose")}" since {rec.get("acquiredAt")}{left}'
            f'{active_text}')


def _log(event, rec, extra=None):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    row = {'at': _iso(_now()), 'event': event, 'record': rec}
    if extra:
        row.update(extra)
    with io.open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')


def _write_new(rec):
    """Atomic create: fails if the file appeared between our read and now."""
    fd = os.open(CLAIM, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        json.dump(rec, fh, indent=2)


def _write_replace(rec):
    tmp = CLAIM + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(rec, fh, indent=2)
    os.replace(tmp, CLAIM)


def _record(owner, purpose, ttl, pid_bound):
    t = _now()
    pid = os.getpid()
    return {'owner': owner, 'leaseId': secrets.token_hex(16),
            'pid': pid, 'pidBound': bool(pid_bound),
            'pidStarted': pid_start_identity(pid) if pid_bound else None,
            'purpose': purpose, 'acquiredAt': _iso(t), 'ttlMinutes': int(ttl),
            'expiresAt': _iso(t + datetime.timedelta(minutes=int(ttl))),
            'host': socket.gethostname(), 'user': getpass.getuser()}


def same_holder(rec, owner, lease=None, pid=None, pid_started=None):
    """Prove that this caller, not merely its display name, owns ``rec``.

    ``owner`` is human-readable coordination metadata and is deliberately not
    an authentication token. Two sibling agents can inherit the same owner
    string; treating that string as re-entrant let both mutate concurrently.
    Re-entry therefore needs either the exact lease ID explicitly inherited by
    a child, or the exact process identity that created the claim.
    """
    if not rec or rec.get('owner') != owner:
        return False
    lease = lease or os.environ.get('SKYRIM_CLAIM_LEASE')
    active = _active_holder(rec)
    if active and _holder_live(active):
        if not _same_process(active, pid, pid_started):
            return False
        active_lease = active.get('leaseId')
        return (not lease or not active_lease or
                secrets.compare_digest(str(lease), str(active_lease)))
    if not _same_process(rec, pid, pid_started):
        return False
    record_lease = rec.get('leaseId')
    return (not lease or not record_lease or
            secrets.compare_digest(str(lease), str(record_lease)))


def issue_launch_check(owner, lease=None, ttl_seconds=120):
    """Issue one short-lived nonce to one designated launcher descendant.

    A holder lease alone is mutation authority inside its exact process and may
    be shared by shell siblings. It is therefore insufficient evidence that an
    arbitrary sibling is the launcher selected by ``launch_verify``. Only its
    SHA-256 is recorded atomically against the exact current holder; the nonce
    itself exists solely in the designated child's environment and is consumed
    once by the launcher's read-only ``check`` command.
    """
    with _claim_mutex():
        rec = read()
        if rec is None or is_stale(rec) or not same_holder(rec, owner, lease):
            raise ClaimHeld(rec or {
                'owner': '?', 'pid': None,
                'purpose': 'no exact holder can designate a launcher',
            })
        holder = _active_holder(rec)
        if not (holder and _holder_live(holder)):
            holder = rec
        nonce = secrets.token_hex(32)
        check = {
            'nonceSha256': hashlib.sha256(nonce.encode('ascii')).hexdigest().upper(),
            'holderLeaseId': str(holder.get('leaseId') or ''),
            'issuerPid': os.getpid(),
            'issuerPidStarted': pid_start_identity(os.getpid()),
            'issuedAt': _iso(_now()),
            'expiresAt': _iso(
                _now() + datetime.timedelta(seconds=max(1, int(ttl_seconds)))),
        }
        new = dict(rec)
        new['launchCheck'] = check
        _write_replace(new)
        _log('launch-check-issue', new)
        return nonce


def consume_launch_check(owner, nonce, lease=None):
    """Consume exactly one designated launcher nonce; grant no other authority."""
    if not nonce or not lease:
        return False
    with _claim_mutex():
        rec = read()
        if rec is None or is_stale(rec) or rec.get('owner') != owner:
            return False
        check = rec.get('launchCheck') if isinstance(rec.get('launchCheck'), dict) else None
        if not check:
            return False
        expires = _parse(check.get('expiresAt'))
        holder = _active_holder(rec)
        if not (holder and _holder_live(holder)):
            holder = rec
        valid = bool(
            expires and expires >= _now()
            and secrets.compare_digest(
                hashlib.sha256(str(nonce).encode('utf-8')).hexdigest().upper(),
                str(check.get('nonceSha256') or ''))
            and secrets.compare_digest(str(lease), str(check.get('holderLeaseId') or ''))
            and secrets.compare_digest(str(lease), str(holder.get('leaseId') or ''))
            and str(check.get('issuerPid')) == str(holder.get('pid'))
            and (not check.get('issuerPidStarted') or not holder.get('pidStarted') or
                 str(check.get('issuerPidStarted')) == str(holder.get('pidStarted')))
            and _holder_live(holder)
        )
        if not valid:
            return False
        new = dict(rec)
        new.pop('launchCheck', None)
        new['renewedAt'] = _iso(_now())
        _write_replace(new)
        _log('launch-check-consume', new, {'byPid': os.getpid()})
        return True


def held_by_other(owner, lease=None):
    """The live record blocking this holder, or None if free / ours / stale."""
    rec = read()
    if rec is None or is_stale(rec):
        return None
    if same_holder(rec, owner, lease):
        return None
    # A session token may enter an idle unbound/manual claim, but it does not
    # make a second process equivalent to a live pid-bound or child holder.
    if (not rec.get('pidBound') and not
            (_active_holder(rec) and _holder_live(_active_holder(rec))) and
            _session_holder(rec, owner, lease)):
        return None
    return rec


def acquire(owner, purpose, ttl=DEFAULT_TTL, wait=0, pid_bound=False,
            lease=None, process_scoped=True):
    """Take (or renew) the claim. Returns (record, renewed: bool).

    Raises ClaimHeld if another owner holds a live claim after `wait` seconds."""
    if not owner or not owner.strip():
        raise ValueError('a claim needs an owner name (--owner or $SKYRIM_CLAIM_OWNER)')
    deadline = time.time() + max(0, wait)
    while True:
        blocker = None
        with _claim_mutex():
            rec = read()
            live = rec is not None and not is_stale(rec)
            active = _active_holder(rec)
            active_live = bool(active and _holder_live(active))
            active_here = bool(active_live and _same_process(active))
            exact_here = bool(live and same_holder(rec, owner, lease))
            session_here = bool(live and _session_holder(rec, owner, lease))

            if live and process_scoped and not exact_here:
                # A pid-bound claim is itself the active process.  A shared
                # session token authorizes sequential work; it never lets a
                # second process enter alongside that live holder.
                if active_here and session_here:
                    exact_here = True
                elif rec.get('pidBound') or active_live or not session_here:
                    blocker = rec
                else:
                    # An idle unbound/manual session lends one unguessable
                    # process child token.  Sibling processes sharing the
                    # session lease serialize on this slot.
                    child = {
                        'leaseId': secrets.token_hex(16),
                        'pid': os.getpid(),
                        'pidStarted': pid_start_identity(os.getpid()),
                        'purpose': purpose,
                        'acquiredAt': _iso(_now()),
                    }
                    new = dict(rec)
                    new['activeHolder'] = child
                    new['renewedAt'] = _iso(_now())
                    new['expiresAt'] = _iso(
                        _now() + datetime.timedelta(minutes=int(ttl)))
                    _write_replace(new)
                    _log('child-acquire', new)
                    returned = dict(new)
                    returned['holderLeaseId'] = child['leaseId']
                    returned['holderRole'] = 'child'
                    return returned, True

            if live and not process_scoped and not session_here:
                blocker = rec

            if blocker is None:
                new = _record(owner, purpose, ttl, pid_bound)
                if lease:
                    new['leaseId'] = str(lease)
                if rec is None:
                    _write_new(new)
                    _log('acquire', new)
                    returned = dict(new)
                    returned['holderLeaseId'] = new['leaseId']
                    returned['holderRole'] = 'main'
                    return returned, False
                if live:
                    # A nested controller must not downgrade a live outer
                    # pid-bound lease to a fixed-TTL inner PID.
                    new['pid'] = rec.get('pid')
                    new['pidBound'] = bool(rec.get('pidBound'))
                    new['pidStarted'] = rec.get('pidStarted')
                    new['leaseId'] = rec.get('leaseId') or new['leaseId']
                    new['host'] = rec.get('host') or new['host']
                    new['user'] = rec.get('user') or new['user']
                    new['acquiredAt'] = rec.get('acquiredAt') or new['acquiredAt']
                    new['renewedAt'] = _iso(_now())
                    if active_live:
                        active = dict(active)
                        if active_here:
                            active['purpose'] = purpose
                            active['renewedAt'] = _iso(_now())
                        new['activeHolder'] = active
                    _write_replace(new)
                    _log('renew', new)
                    returned = dict(new)
                    if active_here:
                        returned['holderLeaseId'] = active['leaseId']
                        returned['holderRole'] = 'nested'
                    else:
                        returned['holderLeaseId'] = new['leaseId']
                        returned['holderRole'] = ('nested' if process_scoped else 'session')
                    return returned, True
                # stale: the mutex makes this a real compare-and-swap rather
                # than two simultaneous readers both believing they won.
                sys.stderr.write(f'WARNING claim takeover: {describe(rec)} was stale; '
                                 f'now {owner} for "{purpose}"\n')
                _write_replace(new)
                _log('takeover', new, {'replaced': rec})
                returned = dict(new)
                returned['holderLeaseId'] = new['leaseId']
                returned['holderRole'] = 'main'
                return returned, False
        if time.time() < deadline:
            time.sleep(min(0.1, max(0.01, deadline - time.time())))
            continue
        raise ClaimHeld(blocker)


def release(owner, force=False, lease=None):
    """Drop the claim. Refuses (returns False) if another owner holds it and
    force is not set."""
    with _claim_mutex():
        rec = read()
        if rec is None:
            return True
        active = _active_holder(rec)
        active_live = bool(active and _holder_live(active))
        if active_live and same_holder(rec, owner, lease):
            new = dict(rec)
            new.pop('activeHolder', None)
            new['renewedAt'] = _iso(_now())
            _write_replace(new)
            _log('child-release', new, {'released': active})
            return True
        if active_live and not force:
            sys.stderr.write(f'refusing to release: {describe(rec)} '
                             '(a process-scoped child is still active)\n')
            return False
        authorized = (same_holder(rec, owner, lease) or
                      _session_holder(rec, owner, lease))
        if not authorized and not force and not is_stale(rec):
            sys.stderr.write(f'refusing to release: {describe(rec)} '
                             f'(not this {owner} lease/process)\n')
            return False
        try:
            os.remove(CLAIM)
        except FileNotFoundError:
            pass
        _log('release' if authorized else 'force-release', rec,
             {'by': owner})
        return True


class guard:
    """Context manager: hold the claim for the block.

    An idle shell/session claim lends one process-scoped child slot. Nested
    blocks in that exact process are re-entrant; sibling processes which merely
    inherited the same friendly owner and session lease still serialize."""
    def __init__(self, owner, purpose, ttl=DEFAULT_TTL, wait=0):
        self.owner = owner or default_owner()
        self.purpose, self.ttl, self.wait = purpose, ttl, wait
        self.nested = False
        self.lease = None
        self.role = None
        self.process_lock = False

    def __enter__(self):
        if self.wait:
            self.process_lock = _PROCESS_GUARD.acquire(timeout=max(0, self.wait))
        else:
            self.process_lock = _PROCESS_GUARD.acquire(blocking=False)
        if not self.process_lock:
            raise ClaimHeld(read() or {
                'owner': self.owner, 'pid': os.getpid(),
                'purpose': 'another thread in this process is using the claim',
            })
        try:
            inherited = os.environ.get('SKYRIM_CLAIM_LEASE')
            self.record, _ = acquire(
                self.owner, self.purpose, self.ttl, self.wait,
                pid_bound=True, lease=inherited, process_scoped=True)
            self.role = self.record.get('holderRole')
            self.nested = self.role == 'nested'
            self.lease = (self.record.get('holderLeaseId') or
                          self.record.get('leaseId'))
            return self.record
        except BaseException:
            _PROCESS_GUARD.release()
            self.process_lock = False
            raise

    def __exit__(self, *exc):
        try:
            if not self.nested:
                release(self.owner, lease=self.lease)
            return False
        finally:
            if self.process_lock:
                _PROCESS_GUARD.release()
                self.process_lock = False


def default_owner():
    """$SKYRIM_CLAIM_OWNER, else a per-process name that is at least honest
    about who it is."""
    return (os.environ.get('SKYRIM_CLAIM_OWNER') or
            f'{getpass.getuser()}@{socket.gethostname()}:pid{os.getpid()}')


def require_or_exit(owner, purpose, ttl=DEFAULT_TTL, wait=0, pid_bound=True,
                    lease=None):
    """For scripts: acquire or print the blocker and exit 75."""
    try:
        return acquire(owner, purpose, ttl, wait, pid_bound=pid_bound,
                       lease=lease)[0]
    except ClaimHeld as e:
        print(f'CLAIM HELD - refusing to touch the profile: {e}\n'
              f'   wait for it, ask the owner, or (only if you know it is dead) '
              f'`py -3 audit/claim.py release --owner {e.record.get("owner")} --force`')
        sys.exit(ExTempFail)


# ------------------------------------------------------------------------ CLI
def selftest():
    """Exercise the state machine against a scratch claim path."""
    global CLAIM, LOG
    import tempfile
    d = tempfile.mkdtemp(prefix='claim-selftest-')
    CLAIM, LOG = os.path.join(d, 'claim.json'), os.path.join(d, 'log.jsonl')
    bad = 0

    def ok(cond, label):
        nonlocal bad
        bad += not cond
        print(f'  {"ok  " if cond else "FAIL"} {label}')

    ok(read() is None, 'starts free')
    a, renewed = acquire('a', 'first', ttl=1)
    ok(a['owner'] == 'a' and not renewed, 'a acquires')
    ok(held_by_other('b') is not None, 'b sees it held')
    ok(held_by_other('a') is None, 'a does not block itself')
    try:
        acquire('b', 'second', ttl=1)
        ok(False, 'b refused')
    except ClaimHeld:
        ok(True, 'b refused')
    _, renewed = acquire('a', 'again', ttl=1, lease=a['leaseId'])
    ok(renewed and read()['purpose'] == 'again', 'a renews in place')
    ok(release('b') is False and read() is not None, 'b cannot release a')
    # stale by TTL
    rec = read(); rec['expiresAt'] = _iso(_now() - datetime.timedelta(minutes=5))
    _write_replace(rec)
    ok(is_stale(read()), 'expired record is stale')
    b, _ = acquire('b', 'takeover', ttl=1)
    ok(b['owner'] == 'b', 'b takes over a stale claim')
    rec = read(); rec['pidBound'] = True; rec['pid'] = os.getpid()
    rec['pidStarted'] = pid_start_identity(os.getpid())
    rec['expiresAt'] = _iso(_now() - datetime.timedelta(minutes=5))
    _write_replace(rec)
    ok(not is_stale(read()), 'live pid-bound record survives advisory TTL expiry')
    original_pid = read()['pid']
    acquire('b', 'nested-renewal', ttl=1, pid_bound=False,
            lease=b['leaseId'])
    ok(read()['pidBound'] and read()['pid'] == original_pid,
       'same-owner nested renewal preserves outer pid binding')
    ok(not same_holder(read(), 'b', pid=os.getpid() + 100000,
                       pid_started='different'),
       'same owner string from a sibling process is not the same holder')
    try:
        acquire('b', 'sibling', ttl=1, lease='different-lease')
        ok(False, 'same-name sibling refused')
    except ClaimHeld:
        ok(True, 'same-name sibling refused')
    # stale by dead pid
    rec = read(); rec['pidBound'] = True; rec['pid'] = 999999999
    _write_replace(rec)
    ok(is_stale(read()), 'dead pid-bound record is stale')
    ok(release('b', force=True) and read() is None, 'force release clears')
    # guard nesting
    acquire('c', 'outer', ttl=1)
    with guard('c', 'inner', ttl=1):
        ok(read()['purpose'] == 'inner', 'nested guard renews')
    ok(read() is not None and read()['owner'] == 'c', 'nested guard does not release outer')
    release('c')
    with guard('d', 'solo', ttl=1):
        ok(read()['owner'] == 'd', 'solo guard acquires')
    ok(read() is None, 'solo guard releases')
    naive = _record('legacy', 'timezone-less expiry', 1, False)
    naive['expiresAt'] = '2026-09-04T12:00:00'
    _write_new(naive)
    ok(is_stale(read()), 'timezone-less expiry fails closed as stale')
    os.remove(CLAIM)
    # malformed file is never "free"
    io.open(CLAIM, 'w').write('{not json')
    ok(read().get('malformed') and is_stale(read()), 'malformed file is stale, not free')
    os.remove(CLAIM)
    events = [json.loads(l)['event'] for l in io.open(LOG, encoding='utf-8')]
    ok('takeover' in events and 'release' in events, 'log has takeover + release')

    # Real-process regression for a durable shell/session lease.  Merely
    # sharing the session token must authorize sequential children, never two
    # simultaneous profile mutators and never a sibling release of an active
    # child.  Each child redirects this module to the scratch paths above, so
    # the fixture cannot inspect or mutate the live MO2 claim.
    child_one = child_two = None
    gate_one = pathlib.Path(d) / 'release-one'
    gate_two = pathlib.Path(d) / 'release-two'
    ready_one = pathlib.Path(d) / 'ready-one'
    ready_two = pathlib.Path(d) / 'ready-two'
    attempt_two = pathlib.Path(d) / 'attempt-two'
    child_env = dict(os.environ)
    child_env.update({
        'CLAIM_SELFTEST_PATH': CLAIM,
        'CLAIM_SELFTEST_LOG': LOG,
        'CLAIM_SELFTEST_READY_ONE': str(ready_one),
        'CLAIM_SELFTEST_READY_TWO': str(ready_two),
        'CLAIM_SELFTEST_ATTEMPT_TWO': str(attempt_two),
        'CLAIM_SELFTEST_GATE_ONE': str(gate_one),
        'CLAIM_SELFTEST_GATE_TWO': str(gate_two),
    })
    module_dir = os.path.dirname(os.path.abspath(__file__))
    prefix = (
        'import os, pathlib, sys, time\n'
        f'sys.path.insert(0, {module_dir!r})\n'
        'import claim as c\n'
        "c.CLAIM = os.environ['CLAIM_SELFTEST_PATH']\n"
        "c.LOG = os.environ['CLAIM_SELFTEST_LOG']\n"
    )

    def wait_file(path, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.is_file():
                return True
            time.sleep(0.02)
        return path.is_file()

    def child_result(process, timeout=5):
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout.strip(), stderr.strip()

    try:
        # launch_skyrim.ps1 invokes a fresh claim.py process. Possession of the
        # holder lease alone must not let a sibling impersonate that launcher;
        # only the one-use nonce explicitly issued to its environment may pass.
        root_lease = 'launcher-root-secret'
        root, renewed = acquire(
            'launcher-root', 'launch parent', ttl=2, pid_bound=True,
            lease=root_lease, process_scoped=True)
        root_env = dict(child_env)
        root_env.update({
            'SKYRIM_CLAIM_OWNER': 'launcher-root',
            'SKYRIM_CLAIM_LEASE': root_lease,
        })
        sibling_check = subprocess.run(
            [sys.executable, '-c', prefix +
             'raise SystemExit(c.main())\n', 'check'],
            env=root_env, capture_output=True, text=True, timeout=5)
        ok(not renewed and sibling_check.returncode == 1 and
           'HELD:' in sibling_check.stdout,
           'sibling with the exact root lease cannot pass launcher check')
        launch_nonce = issue_launch_check(
            'launcher-root', root_lease, ttl_seconds=30)
        designated_env = dict(root_env)
        designated_env['SKYRIM_CLAIM_LAUNCH_CHECK'] = launch_nonce
        designated_check = subprocess.run(
            [sys.executable, '-c', prefix +
             'raise SystemExit(c.main())\n', 'check'],
            env=designated_env, capture_output=True, text=True, timeout=5)
        ok(designated_check.returncode == 0 and
           'designated launcher' in designated_check.stdout and
           'launchCheck' not in read(),
           'designated descendant consumes its exact one-use launcher nonce')
        replay_check = subprocess.run(
            [sys.executable, '-c', prefix +
             'raise SystemExit(c.main())\n', 'check'],
            env=designated_env, capture_output=True, text=True, timeout=5)
        ok(replay_check.returncode == 1 and 'HELD:' in replay_check.stdout,
           'consumed launcher nonce cannot be replayed')
        mutator = subprocess.run(
            [sys.executable, '-c', prefix +
             "try:\n"
             "    c.acquire('launcher-root', 'sibling mutation', ttl=2, "
             "lease='launcher-root-secret', process_scoped=True)\n"
             "except c.ClaimHeld:\n"
             "    raise SystemExit(0)\n"
             "raise SystemExit(2)\n"],
            env=root_env, capture_output=True, text=True, timeout=5)
        ok(mutator.returncode == 0 and read().get('pid') == os.getpid() and
           read().get('leaseId') == root_lease,
           'read-only lease recognition does not authorize a sibling mutator')
        ok(release('launcher-root', lease=root.get('holderLeaseId')) and
           read() is None,
           'launcher root fixture releases in its creating process')

        session, renewed = acquire(
            'shared', 'durable session', ttl=2, pid_bound=False,
            lease='session-secret', process_scoped=False)
        idle_identity = {key: session.get(key) for key in
                         ('owner', 'leaseId', 'pid', 'pidBound', 'purpose')}
        ok(not renewed and _active_holder(read()) is None,
           'subprocess fixture starts with one idle session lease')

        child_one_code = prefix + (
            "record, _ = c.acquire('shared', 'child one', ttl=2, "
            "lease='session-secret', process_scoped=True)\n"
            "pathlib.Path(os.environ['CLAIM_SELFTEST_READY_ONE']).write_text("
            "record['holderLeaseId'], encoding='utf-8')\n"
            "deadline = time.monotonic() + 12\n"
            "while not pathlib.Path(os.environ['CLAIM_SELFTEST_GATE_ONE']).exists():\n"
            "    if time.monotonic() >= deadline: raise TimeoutError('gate one')\n"
            "    time.sleep(0.02)\n"
            "if not c.release('shared', lease=record['holderLeaseId']): "
            "raise RuntimeError('child one release refused')\n"
        )
        child_one = subprocess.Popen(
            [sys.executable, '-c', child_one_code], env=child_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        first_ready = wait_file(ready_one)
        ok(first_ready and child_one.poll() is None and
           (_active_holder(read()) or {}).get('pid') == child_one.pid,
           'first child holds the active session slot')
        if not first_ready:
            raise RuntimeError('first claim child never became ready')

        child_two_code = prefix + (
            "pathlib.Path(os.environ['CLAIM_SELFTEST_ATTEMPT_TWO']).write_text("
            "'attempt', encoding='utf-8')\n"
            "record, _ = c.acquire('shared', 'child two', ttl=2, wait=20, "
            "lease='session-secret', process_scoped=True)\n"
            "pathlib.Path(os.environ['CLAIM_SELFTEST_READY_TWO']).write_text("
            "record['holderLeaseId'], encoding='utf-8')\n"
            "deadline = time.monotonic() + 12\n"
            "while not pathlib.Path(os.environ['CLAIM_SELFTEST_GATE_TWO']).exists():\n"
            "    if time.monotonic() >= deadline: raise TimeoutError('gate two')\n"
            "    time.sleep(0.02)\n"
            "if not c.release('shared', lease=record['holderLeaseId']): "
            "raise RuntimeError('child two release refused')\n"
        )
        child_two = subprocess.Popen(
            [sys.executable, '-c', child_two_code], env=child_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second_attempted = wait_file(attempt_two)
        time.sleep(0.25)
        ok(second_attempted and child_two.poll() is None and not ready_two.exists() and
           (_active_holder(read()) or {}).get('pid') == child_one.pid,
           'second same-session child waits behind the active child')

        sibling_release = subprocess.run(
            [sys.executable, '-c', prefix +
             "raise SystemExit(0 if not c.release('shared', "
             "lease='session-secret') else 2)\n"],
            env=child_env, capture_output=True, text=True, timeout=5)
        ok(sibling_release.returncode == 0 and
           (_active_holder(read()) or {}).get('pid') == child_one.pid,
           'session lease cannot release a live sibling child')

        intruder = subprocess.run(
            [sys.executable, '-c', prefix +
             "try:\n"
             "    c.acquire('intruder', 'third owner', ttl=2, wait=0, "
             "lease='intruder-secret', process_scoped=True)\n"
             "except c.ClaimHeld:\n"
             "    raise SystemExit(0)\n"
             "raise SystemExit(2)\n"],
            env=child_env, capture_output=True, text=True, timeout=5)
        ok(intruder.returncode == 0 and
           (_active_holder(read()) or {}).get('pid') == child_one.pid,
           'third owner cannot enter the held session')

        gate_one.write_text('release', encoding='utf-8')
        result_one = child_result(child_one)
        ok(result_one[0] == 0,
           'first child releases cleanly before the waiter enters')
        second_ready = wait_file(ready_two)
        ok(second_ready and child_two.poll() is None and
           (_active_holder(read()) or {}).get('pid') == child_two.pid,
           'waiting same-session child acquires only after release')
        if not second_ready:
            raise RuntimeError('second claim child never acquired after release')
        gate_two.write_text('release', encoding='utf-8')
        result_two = child_result(child_two)
        ok(result_two[0] == 0, 'second child releases cleanly')

        idle = read()
        ok(idle is not None and _active_holder(idle) is None and
           {key: idle.get(key) for key in idle_identity} == idle_identity,
           'child cleanup restores the exact idle session authority')
        ok(release('shared', lease='session-secret') and read() is None,
           'session owner performs exact final cleanup')
    except BaseException as exc:
        ok(False, f'subprocess claim fixture completed: {type(exc).__name__}: {exc}')
    finally:
        for gate in (gate_one, gate_two):
            try:
                gate.write_text('cleanup', encoding='utf-8')
            except OSError:
                pass
        for process in (child_one, child_two):
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                    process.communicate(timeout=2)
                except BaseException:
                    try:
                        process.kill()
                    except BaseException:
                        pass
        if read() is not None:
            release('selftest-cleanup', force=True)
    print(f'\n{"all" if not bad else bad} claim selftest {"cases pass" if not bad else "FAILURES"}')
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    if a[0] == '--selftest':
        return selftest()
    cmd = a[0]

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a else default
    owner = opt('--owner') or os.environ.get('SKYRIM_CLAIM_OWNER')
    lease = opt('--lease') or os.environ.get('SKYRIM_CLAIM_LEASE')
    ttl = int(opt('--ttl', DEFAULT_TTL))

    if cmd == 'status':
        print(describe(read()) + (' [STALE]' if is_stale(read()) else ''))
        return 0
    if cmd == 'check':
        rec = read()
        if rec is None or is_stale(rec):
            print('free' + (' (stale record present)' if rec else '')); return 0
        launch_check = (opt('--launch-check') or
                        os.environ.get('SKYRIM_CLAIM_LAUNCH_CHECK'))
        if owner and same_holder(rec, owner, lease):
            print('mine: ' + describe(rec)); return 0
        if owner and launch_check and consume_launch_check(
                owner, launch_check, lease):
            print('mine (designated launcher): ' + describe(read())); return 0
        print('HELD: ' + describe(rec)); return 1
    if not owner:
        print('an owner is required: --owner NAME or set SKYRIM_CLAIM_OWNER'); return 64
    if cmd == 'acquire' or cmd == 'renew':
        if not lease:
            print('a CLI session claim requires --lease ID or '
                  '$SKYRIM_CLAIM_LEASE; an owner name alone is not exclusive')
            return 64
        purpose = opt('--purpose') or (read() or {}).get('purpose') or '(no purpose given)'
        try:
            rec, renewed = acquire(owner, purpose, ttl, wait=int(opt('--wait', 0)),
                                    lease=lease, process_scoped=False)
        except ClaimHeld as e:
            print(f'HELD: {e}'); return ExTempFail
        print(f'{"renewed" if renewed else "acquired"}: {describe(rec)}'); return 0
    if cmd == 'release':
        return 0 if release(owner, force='--force' in a, lease=lease) else ExTempFail
    print(f'unknown command {cmd}\n{__doc__}'); return 64


if __name__ == '__main__':
    sys.exit(main())
