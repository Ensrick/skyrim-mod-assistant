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
    # --max-age-min N: fail if skse64.log predates the launch attempt by more
    # than N minutes (catches failed-to-spawn, where a stale log looks green)
    max_age = None
    if '--max-age-min' in sys.argv:
        max_age = float(sys.argv[sys.argv.index('--max-age-min') + 1])
    log = os.path.join(SKSE_DIR, 'skse64.log')
    if not os.path.exists(log):
        print('NO skse64.log - the game has not launched through SKSE')
        return 1
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(log))
    print(f'skse64.log written {age.total_seconds()/60:.0f} min ago')
    if max_age is not None and age.total_seconds() > max_age * 60:
        print(f'STALE: skse64.log is older than {max_age:.0f} min - '
              f'this launch attempt never reached SKSE init (failed-to-spawn)')
        return 3
    # a crash log newer than skse64.log = the session died after init
    crashes = [fn for fn in os.listdir(SKSE_DIR)
               if fn.startswith('crash-') and fn.endswith('.log')
               and os.path.getmtime(os.path.join(SKSE_DIR, fn)) > os.path.getmtime(log)]
    if crashes:
        print(f'CRASHED after init: {sorted(crashes)[-1]} is newer than skse64.log')
        for fn in sorted(crashes):
            with open(os.path.join(SKSE_DIR, fn), encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    if 'Unhandled exception' in line:
                        print(f'   {fn}: {line.strip()[:160]}')
                        break
        return 4
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
    # steam-wedge check: chain dead but Steam still thinks the app runs
    # (recurring 1.7.99-era issue; heal = Steam cycle, launch_skyrim does it
    # pre-launch automatically)
    try:
        import subprocess, winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam\Apps\489830')
        running = winreg.QueryValueEx(k, 'Running')[0]
        tl = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq SkyrimSE.exe'],
                            capture_output=True, text=True).stdout
        if running and 'SkyrimSE.exe' not in tl:
            print('STEAM-WEDGE: Steam flags the app as running but no game process '
                  'exists - Steam missed the exit; next launch_skyrim run self-heals '
                  '(pre-launch Steam cycle), or cycle Steam to clear the badge now')
    except Exception:
        pass
    silent = [c for c in checked if not os.path.exists(os.path.join(SKSE_DIR, c.replace('.dll', '.log')))]
    print(f'({len(silent)} plugins keep no log here - popups like EngineFixes format errors '
          f'only surface on screen; treat any load-time popup as a triage item)')
    return 0 if not bad else 2

if __name__ == '__main__':
    sys.exit(main())
