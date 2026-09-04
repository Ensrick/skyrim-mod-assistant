"""Drive the MenuPilot SKSE plugin: write commands, wait for results, tail log.

MenuPilot (source: skyrim-tools-source/MenuPilot, installed as MO2 mod
"MenuPilot") polls Documents\\My Games\\Skyrim Special Edition\\SKSE\\MenuPilot\\
for commands.jsonl, consumes it exactly once (claim-by-rename), runs each
command on the game's main thread and appends flushed result lines to
menupilot.log in the same folder. Command reference: docs/MENUPILOT.md.

  py -3 audit/menupilot.py send '{"op":"ping"}' '{"op":"menu.list"}'
  py -3 audit/menupilot.py send --file batch.jsonl --timeout 60
  py -3 audit/menupilot.py tail [-n 80]
  py -3 audit/menupilot.py panic
  py -3 audit/menupilot.py status

send exits 0 when the batch's BATCH_DONE line lands, 1 on timeout (partial
log still printed), 2 when the game/plugin is clearly not listening.
"""
import argparse, dataclasses, datetime, json, os, secrets, sys, time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

PILOT = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                     'Skyrim Special Edition', 'SKSE', 'MenuPilot')
LOG = os.path.join(PILOT, 'menupilot.log')
COMMANDS = os.path.join(PILOT, 'commands.jsonl')


@dataclasses.dataclass
class BatchResult:
    """One claimed MenuPilot batch, including only log text from this send."""
    code: int
    token: str
    text: str
    claimed: bool
    cleanup: str = ''


def _payload(commands, token):
    """Validate and tag commands so their echoes are unambiguous in the log."""
    lines = []
    for raw in commands:
        parsed = json.loads(raw) if isinstance(raw, str) else dict(raw)
        if not isinstance(parsed, dict) or 'op' not in parsed:
            raise ValueError(f'not a command object: {raw}')
        parsed['_driver_token'] = token       # ignored by the DLL, echoed in COMMAND raw
        lines.append(json.dumps(parsed, separators=(',', ':'), ensure_ascii=True))
    if not lines:
        raise ValueError('nothing to send')
    return ('\n'.join(lines) + '\n').encode('utf-8')


def quarantine_pending(label='stale', expected=None):
    """Atomically make commands.jsonl inert; never move somebody else's bytes.

    `expected` is the exact payload this process wrote.  When omitted, callers
    must already have proved no game/poller is alive and that they own the
    instance claim.  Renaming, rather than deleting, leaves a forensic copy and
    guarantees the next launch cannot consume it.
    """
    if not os.path.exists(COMMANDS):
        return None
    if expected is not None:
        try:
            with open(COMMANDS, 'rb') as fh:
                if fh.read() != expected:
                    return None
        except FileNotFoundError:              # the plugin claimed it meanwhile
            return None
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    safe = ''.join(c for c in label if c.isalnum() or c in '-_')[:40] or 'stale'
    dest = os.path.join(PILOT, f'commands-{stamp}-{safe}-{secrets.token_hex(3)}.jsonl')
    try:
        os.replace(COMMANDS, dest)
    except FileNotFoundError:                  # claim-by-rename won the race
        return None
    return dest


def send_batch(commands, timeout=45, require_ready=False):
    """Send dictionaries/JSON strings and always retire an unclaimed payload.

    The DLL already provides consume-exactly-once.  This adds the missing
    driver-side half: a timeout or Ctrl-C cannot strand *our* commands.jsonl for
    the next game launch.  A payload already claimed by the DLL is not pending;
    the caller receives the partial log and must stop issuing further batches.
    """
    os.makedirs(PILOT, exist_ok=True)
    token = 'mp-' + secrets.token_hex(12)
    payload = _payload(commands, token)
    if os.path.exists(COMMANDS):
        return BatchResult(2, token, '', False,
                           'refused: commands.jsonl already pending (not ours)')

    before = read_log()
    if require_ready and 'POLL_START' not in before:
        return BatchResult(2, token, '', False,
                           'refused: log shows no POLL_START')

    tmp = COMMANDS + f'.{token}.tmp'
    try:
        with open(tmp, 'wb') as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        try:
            # On Windows rename-to-existing fails: never overwrite a command
            # that won the race after the read-only existence check.
            os.rename(tmp, COMMANDS)
        except FileExistsError:
            return BatchResult(2, token, '', False,
                               'refused: another commands.jsonl won the publish race')

        done_before = before.count('BATCH_DONE')
        deadline = time.time() + timeout
        offset = len(before)
        claimed = False
        latest = before
        while time.time() < deadline:
            time.sleep(0.10)
            latest = read_log()
            if not claimed and not os.path.exists(COMMANDS):
                claimed = True
            segment = latest[offset:] if len(latest) >= offset else latest
            if (claimed and token in segment and
                    latest.count('BATCH_DONE') > done_before):
                return BatchResult(0, token, segment, True)
        cleanup = ''
        if not claimed:
            moved = quarantine_pending('timeout', expected=payload)
            cleanup = (f'unclaimed payload quarantined as {moved}' if moved else
                       'payload was replaced or claimed during timeout cleanup')
        return BatchResult(1 if claimed else 2, token,
                           latest[offset:] if len(latest) >= offset else latest,
                           claimed, cleanup)
    except BaseException:
        quarantine_pending('interrupted', expected=payload)
        raise
    finally:
        try:
            os.remove(tmp)
        except FileNotFoundError:
            pass


def read_log():
    if not os.path.exists(LOG):
        return ''
    # The plugin opens the log _SH_DENYWR: reading is allowed.
    with open(LOG, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def tail(n):
    text = read_log()
    if not text:
        print(f'no log at {LOG} (game not running, or plugin not loaded)')
        return 1
    for line in text.splitlines()[-n:]:
        print(line)
    return 0


def status():
    game_alive = os.path.exists(LOG) and time.time() - os.path.getmtime(LOG) < 3600
    print(f'pilot dir : {PILOT}')
    print(f'log       : {"present" if os.path.exists(LOG) else "MISSING"}'
          + (f' (mtime {time.ctime(os.path.getmtime(LOG))})' if os.path.exists(LOG) else ''))
    print(f'pending   : {"commands.jsonl WAITING (unclaimed)" if os.path.exists(COMMANDS) else "none"}')
    text = read_log()
    ready = 'POLL_START' in text
    print(f'poller    : {"started" if ready else "NOT started (needs kInputLoaded)"}')
    return 0 if ready else 1


def send(lines, timeout):
    before = read_log()
    if 'POLL_START' not in before:
        print('WARNING: log shows no POLL_START; plugin may not be listening yet')
    print(f'sent {len(lines)} command(s); waiting up to {timeout}s')
    try:
        result = send_batch(lines, timeout)
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        raise SystemExit(str(e))
    if result.text:
        sys.stdout.write(result.text)
    if result.code:
        print(('TIMEOUT: batch claimed but BATCH_DONE never arrived' if result.claimed
               else 'TIMEOUT/REFUSED: command file was not claimed'))
        if result.cleanup:
            print('cleanup: ' + result.cleanup)
    return result.code


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('send', help='write commands.jsonl and stream results')
    s.add_argument('commands', nargs='*', help='JSON command objects, one per arg')
    s.add_argument('--file', help='read commands (one JSON object per line) from a file')
    s.add_argument('--timeout', type=float, default=45)

    t = sub.add_parser('tail', help='print the last log lines')
    t.add_argument('-n', type=int, default=50)

    sub.add_parser('panic', help='send {"op":"panic"}')
    sub.add_parser('status', help='pilot health at a glance')

    a = p.parse_args()
    if a.cmd == 'tail':
        return tail(a.n)
    if a.cmd == 'status':
        return status()
    if a.cmd == 'panic':
        return send(['{"op":"panic"}'], 15)

    lines = list(a.commands)
    if a.file:
        with open(a.file, encoding='utf-8') as fh:
            lines += [l.strip() for l in fh if l.strip()]
    if not lines:
        raise SystemExit('nothing to send')
    return send(lines, a.timeout)


if __name__ == '__main__':
    raise SystemExit(main())
