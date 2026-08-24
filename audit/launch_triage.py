"""Post-launch triage: read SKSE logs and report every plugin that failed to load.

Run after EVERY launch attempt: py -3 audit/launch_triage.py
The MO2/SKSE stack DOES log failures (skse64.log) - this makes them impossible
to miss. Born 2026-08-23 when 4 DLLs failed silently behind one popup.
"""
import os, re, sys, io, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
SKSE_DIR = os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games',
                        'Skyrim Special Edition', 'SKSE')

def main():
    log = os.path.join(SKSE_DIR, 'skse64.log')
    if not os.path.exists(log):
        print('NO skse64.log - the game has not launched through SKSE')
        return 1
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(log))
    print(f'skse64.log written {age.total_seconds()/60:.0f} min ago')
    txt = open(log, encoding='utf-8', errors='replace').read()
    checked = re.findall(r'checking plugin (\S+)', txt)
    bad = []
    for m in re.finditer(r'plugin (\S+?) \(([^)]*)\) (.+?) \d* ?\(handle', txt):
        name, ver, why = m.group(1), m.group(2), m.group(3).strip()
        if 'loaded correctly' not in why and name.lower() not in ('msdia140.dll',):
            bad.append((name, why, ver))  # msdia140 = CrashLogger's PDB helper, not an SKSE plugin
    print(f'{len(checked)} plugins checked, {len(bad)} refused by the SKSE loader:')
    for name, why, ver in bad:
        print(f'   FAIL {name:<34} {why}')
    # runtime self-disables (EngineFixes-style) leave no skse64.log trace:
    # cross-check each plugin's own log written this session
    fresh = []
    for fn in os.listdir(SKSE_DIR):
        p = os.path.join(SKSE_DIR, fn)
        if fn.lower().endswith('.log') and os.path.getmtime(p) >= os.path.getmtime(log) - 120:
            body = open(p, encoding='utf-8', errors='replace').read()
            hits = re.findall(r'.*(?:error|fail|unsupported|incompatib).*', body, re.I)[:3]
            if hits and fn not in ('skse64.log', 'skse64_loader.log'):
                fresh.append((fn, hits))
    if fresh:
        print('per-plugin logs with error lines this session:')
        for fn, hits in fresh:
            print(f'   {fn}:')
            for h in hits:
                print(f'      {h.strip()[:120]}')
    silent = [c for c in checked if not os.path.exists(os.path.join(SKSE_DIR, c.replace('.dll', '.log')))]
    print(f'({len(silent)} plugins keep no log here - popups like EngineFixes format errors '
          f'only surface on screen; treat any load-time popup as a triage item)')
    return 0 if not bad else 2

if __name__ == '__main__':
    sys.exit(main())
