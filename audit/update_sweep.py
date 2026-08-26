"""Sweep every ledger mod's Nexus page for newer files (1.7.99 unpark radar).

Run: py -3 audit/update_sweep.py          (all ledger mods + watch pages)
     py -3 audit/update_sweep.py --parked (parked mods only)

Prints NEW for any mod whose newest applicable file is newer than the
installed fileId, with upload date and file description. Exit 3 when news
exists. Complements plugin_watch.py (which tracks a fixed page set with
state); this sweeps the whole ledger statelessly from installed-mods.json.

Born 2026-08-26 from HANDOFF open problem 2; first run of the pattern found
PapyrusUtil 4.7 minutes after upload.
"""
import os, sys, io, json, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modasset as M

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, 'records', 'installed-mods.json')
CATS = ('MAIN', 'UPDATE', 'OPTIONAL')


def main():
    parked_only = '--parked' in sys.argv
    led = json.load(open(LEDGER, encoding='utf-8'))
    news = 0
    seen = set()
    for m in sorted(led['mods'], key=lambda x: (x['enabled'], x['modName'].lower())):
        mid, fid = m['modId'], m['fileId']
        if not isinstance(mid, int) or mid <= 0 or mid in seen:
            continue
        seen.add(mid)
        if parked_only and m['enabled']:
            continue
        state = 'parked' if not m['enabled'] else 'active'
        try:
            files = [f for f in M.v1(f'/mods/{mid}/files.json')['files']
                     if f['category_name'] in CATS]
        except Exception as ex:
            print(f'ERR  {m["modName"]} ({mid}): {ex}')
            continue
        if not files:
            continue
        installed_ts = next((f['uploaded_timestamp'] for f in files
                             if f['file_id'] == fid), 0)
        fresh = [f for f in files if f['uploaded_timestamp'] > installed_ts
                 and f['file_id'] != fid]
        if fresh:
            news += 1
            for f in sorted(fresh, key=lambda x: -x['uploaded_timestamp'])[:3]:
                stamp = datetime.datetime.fromtimestamp(
                    f['uploaded_timestamp']).strftime('%Y-%m-%d')
                desc = (f.get('description') or '').replace('\n', ' ')[:90]
                print(f'NEW  [{state}] {m["modName"]} ({mid}): '
                      f'{f["category_name"]} {f["file_name"][:60]} '
                      f'file_id={f["file_id"]} v{f.get("version")} {stamp}  {desc}')
        else:
            print(f'     [{state}] {m["modName"]} ({mid}): current')
    print(f'\n{news} mod(s) with newer files')
    return 3 if news else 0


if __name__ == '__main__':
    sys.exit(main())
