"""Watch the 1.7.99-blocked plugin pages for new uploads.

Run: py -3 audit/plugin_watch.py    (any time; prints NEW when a page grew a file)
State in records/plugin-watch.json. Born 2026-08-23: runtime 1.7.99 is days old
and four core DLLs await updates.
"""
import os, sys, io, json, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modasset as M

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, 'records', 'plugin-watch.json')

WATCH = {
    17230: 'SSE Engine Fixes (needs address library format 5 support)',
    19080: 'RaceMenu (1.7.99 build done per author, gated on SKSE fix)',
    13048: 'PapyrusUtil (newest 4.6 predates 1.7.99)',
    16495: 'JContainers (4.2.13.1 whitelist stops before 1.7.99)',
    30379: 'SKSE64 page (RaceMenu waits on an SKSE Papyrus fix)',
    # rebuild blocked: 51 ext/ headers deleted upstream; author returned
    # 2026-08-29 and shipped SDS 1.5.9 with 1.7.x support, so an official
    # IED build is the realistic path (issue #94)
    62001: 'Immersive Equipment Displays (1.7.4 refused; needs 1.7.x build)',
    50049: 'Simple Dual Sheath (same author; a new upload here signals IED work)',
}

def main():
    prev = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    cur, news = {}, []
    for mid, label in WATCH.items():
        try:
            files = M.v1(f'/mods/{mid}/files.json')['files']
        except Exception as ex:
            print(f'{mid} {label}: ERR {ex}')
            continue
        latest = max((f['uploaded_timestamp'] for f in files), default=0)
        ids = sorted(f['file_id'] for f in files
                     if f['category_name'] in ('MAIN', 'OPTIONAL', 'UPDATE', 'MISCELLANEOUS'))
        cur[str(mid)] = {'latest': latest, 'fileIds': ids}
        old = prev.get(str(mid), {})
        fresh = [i for i in ids if i not in old.get('fileIds', ids)]
        stamp = datetime.datetime.fromtimestamp(latest).strftime('%Y-%m-%d') if latest else '?'
        if fresh:
            news.append(mid)
            print(f'NEW  {mid} {label}: {len(fresh)} new file(s) since last check! latest upload {stamp}')
        else:
            print(f'     {mid} {label}: no new files (latest {stamp})')
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(cur, open(STATE, 'w', encoding='utf-8'), indent=1)
    return 3 if news else 0

if __name__ == '__main__':
    sys.exit(main())
