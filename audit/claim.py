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
- Re-acquiring your own claim renews it (new TTL, new purpose) - so a script
  that runs under an agent's outer claim does not fight it, and does not
  release it either (see `guard`).
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
import datetime, getpass, io, json, os, socket, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
CLAIM = os.path.join(INSTANCE, '.assistant-claim.json')
LOG = os.path.join(REPO, 'records', 'claim-log.jsonl')
DEFAULT_TTL = 30
ExTempFail = 75


class ClaimHeld(Exception):
    """Raised by acquire() when another owner holds a live claim."""
    def __init__(self, record):
        self.record = record
        super().__init__(describe(record))


def _now():
    return datetime.datetime.now().astimezone()


def _iso(t):
    return t.replace(microsecond=0).isoformat()


def _parse(s):
    try:
        return datetime.datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


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
    exp = _parse(rec.get('expiresAt'))
    if exp is None or exp < _now():
        return True
    if rec.get('pidBound') and not pid_alive(rec.get('pid')):
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
    return (f'held by {rec.get("owner")} (pid {rec.get("pid")}) for '
            f'"{rec.get("purpose")}" since {rec.get("acquiredAt")}{left}')


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
    return {'owner': owner, 'pid': os.getpid(), 'pidBound': bool(pid_bound),
            'purpose': purpose, 'acquiredAt': _iso(t), 'ttlMinutes': int(ttl),
            'expiresAt': _iso(t + datetime.timedelta(minutes=int(ttl))),
            'host': socket.gethostname(), 'user': getpass.getuser()}


def held_by_other(owner):
    """The live record blocking `owner`, or None if free / ours / stale."""
    rec = read()
    if rec is None or is_stale(rec):
        return None
    if rec.get('owner') == owner:
        return None
    return rec


def acquire(owner, purpose, ttl=DEFAULT_TTL, wait=0, pid_bound=False):
    """Take (or renew) the claim. Returns (record, renewed: bool).

    Raises ClaimHeld if another owner holds a live claim after `wait` seconds."""
    if not owner or not owner.strip():
        raise ValueError('a claim needs an owner name (--owner or $SKYRIM_CLAIM_OWNER)')
    deadline = time.time() + max(0, wait)
    while True:
        rec = read()
        if rec is not None and not is_stale(rec) and rec.get('owner') != owner:
            if time.time() < deadline:
                time.sleep(5)
                continue
            raise ClaimHeld(rec)
        new = _record(owner, purpose, ttl, pid_bound)
        if rec is None:
            try:
                _write_new(new)
            except FileExistsError:
                continue                 # lost the race: re-evaluate
            _log('acquire', new)
            return new, False
        if rec.get('owner') == owner and not is_stale(rec):
            new['acquiredAt'] = rec.get('acquiredAt') or new['acquiredAt']
            new['renewedAt'] = _iso(_now())
            _write_replace(new)
            _log('renew', new)
            return new, True
        # stale: take it over, loudly
        sys.stderr.write(f'WARNING claim takeover: {describe(rec)} was stale; '
                         f'now {owner} for "{purpose}"\n')
        _write_replace(new)
        _log('takeover', new, {'replaced': rec})
        return new, False


def release(owner, force=False):
    """Drop the claim. Refuses (returns False) if another owner holds it and
    force is not set."""
    rec = read()
    if rec is None:
        return True
    if rec.get('owner') != owner and not force and not is_stale(rec):
        sys.stderr.write(f'refusing to release: {describe(rec)} (not {owner})\n')
        return False
    try:
        os.remove(CLAIM)
    except FileNotFoundError:
        pass
    _log('release' if rec.get('owner') == owner else 'force-release', rec,
         {'by': owner})
    return True


class guard:
    """Context manager: hold the claim for the block.

    If the same owner already holds a live claim (an agent acquired it from
    the shell before running this script), the block runs under that claim
    and does NOT release it on exit - the outer owner decides when work ends."""
    def __init__(self, owner, purpose, ttl=DEFAULT_TTL, wait=0):
        self.owner = owner or default_owner()
        self.purpose, self.ttl, self.wait = purpose, ttl, wait
        self.nested = False

    def __enter__(self):
        rec = read()
        self.nested = (rec is not None and not is_stale(rec)
                       and rec.get('owner') == self.owner)
        self.record, _ = acquire(self.owner, self.purpose, self.ttl, self.wait,
                                 pid_bound=not self.nested)
        return self.record

    def __exit__(self, *exc):
        if not self.nested:
            release(self.owner)
        return False


def default_owner():
    """$SKYRIM_CLAIM_OWNER, else a per-process name that is at least honest
    about who it is."""
    return (os.environ.get('SKYRIM_CLAIM_OWNER') or
            f'{getpass.getuser()}@{socket.gethostname()}:pid{os.getpid()}')


def require_or_exit(owner, purpose, ttl=DEFAULT_TTL, wait=0, pid_bound=True):
    """For scripts: acquire or print the blocker and exit 75."""
    try:
        return acquire(owner, purpose, ttl, wait, pid_bound=pid_bound)[0]
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
    _, renewed = acquire('a', 'again', ttl=1)
    ok(renewed and read()['purpose'] == 'again', 'a renews in place')
    ok(release('b') is False and read() is not None, 'b cannot release a')
    # stale by TTL
    rec = read(); rec['expiresAt'] = _iso(_now() - datetime.timedelta(minutes=5))
    _write_replace(rec)
    ok(is_stale(read()), 'expired record is stale')
    b, _ = acquire('b', 'takeover', ttl=1)
    ok(b['owner'] == 'b', 'b takes over a stale claim')
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
    # malformed file is never "free"
    io.open(CLAIM, 'w').write('{not json')
    ok(read().get('malformed') and is_stale(read()), 'malformed file is stale, not free')
    os.remove(CLAIM)
    events = [json.loads(l)['event'] for l in io.open(LOG, encoding='utf-8')]
    ok('takeover' in events and 'release' in events, 'log has takeover + release')
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
    ttl = int(opt('--ttl', DEFAULT_TTL))

    if cmd == 'status':
        print(describe(read()) + (' [STALE]' if is_stale(read()) else ''))
        return 0
    if cmd == 'check':
        rec = read()
        if rec is None or is_stale(rec):
            print('free' + (' (stale record present)' if rec else '')); return 0
        if owner and rec.get('owner') == owner:
            print('mine: ' + describe(rec)); return 0
        print('HELD: ' + describe(rec)); return 1
    if not owner:
        print('an owner is required: --owner NAME or set SKYRIM_CLAIM_OWNER'); return 64
    if cmd == 'acquire' or cmd == 'renew':
        purpose = opt('--purpose') or (read() or {}).get('purpose') or '(no purpose given)'
        try:
            rec, renewed = acquire(owner, purpose, ttl, wait=int(opt('--wait', 0)))
        except ClaimHeld as e:
            print(f'HELD: {e}'); return ExTempFail
        print(f'{"renewed" if renewed else "acquired"}: {describe(rec)}'); return 0
    if cmd == 'release':
        return 0 if release(owner, force='--force' in a) else ExTempFail
    print(f'unknown command {cmd}\n{__doc__}'); return 64


if __name__ == '__main__':
    sys.exit(main())
