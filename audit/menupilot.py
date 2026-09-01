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
import argparse, json, os, sys, time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

PILOT = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                     'Skyrim Special Edition', 'SKSE', 'MenuPilot')
LOG = os.path.join(PILOT, 'menupilot.log')
COMMANDS = os.path.join(PILOT, 'commands.jsonl')


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
    os.makedirs(PILOT, exist_ok=True)
    for line in lines:
        parsed = json.loads(line)          # refuse to send malformed commands
        if not isinstance(parsed, dict) or 'op' not in parsed:
            raise SystemExit(f'not a command object: {line}')

    if os.path.exists(COMMANDS):
        print('a commands.jsonl is already pending (unclaimed); is the game running?')
        return 2

    before = read_log()
    if 'POLL_START' not in before:
        print('WARNING: log shows no POLL_START; plugin may not be listening yet')

    tmp = COMMANDS + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    os.replace(tmp, COMMANDS)
    print(f'sent {len(lines)} command(s); waiting up to {timeout}s')

    done_before = before.count('BATCH_DONE')
    deadline = time.time() + timeout
    offset = len(before)
    claimed = False
    while time.time() < deadline:
        time.sleep(0.25)
        text = read_log()
        if len(text) > offset:
            sys.stdout.write(text[offset:])
            offset = len(text)
        if not claimed and not os.path.exists(COMMANDS):
            claimed = True
        if text.count('BATCH_DONE') > done_before:
            return 0
    if not claimed:
        print('TIMEOUT: command file never claimed (plugin not polling)')
        return 2
    print('TIMEOUT: batch claimed but BATCH_DONE never arrived')
    return 1


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
