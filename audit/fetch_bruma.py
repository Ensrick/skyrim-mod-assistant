"""One-shot: download Bruma main + DLC patch, dump FOMOD configs for planning."""
import sys, subprocess, os
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import modasset as M

SEVENZ = r'C:\Program Files\7-Zip\7z.exe'

def toplevel(arc, timeout=1200):
    r = subprocess.run([SEVENZ, 'l', '-slt', arc], capture_output=True, text=True, timeout=timeout)
    tops = {}
    cfg = None
    for line in r.stdout.splitlines():
        if line.startswith('Path = '):
            p = line[7:].strip()
            if p.lower().endswith('moduleconfig.xml'):
                cfg = p
            top = p.replace('/', '\\').split('\\')[0]
            tops[top] = tops.get(top, 0) + 1
    return tops, cfg

f = M.pick_file(10917, prefer=r'^Beyond Skyrim Bruma$')
print('downloading', f['name'], round(f['size_kb']/1024), 'MB ...', flush=True)
arc = M.download(10917, f)
print('cached at', arc, round(os.path.getsize(arc)/1e6), 'MB', flush=True)
tops, cfg = toplevel(arc)
print('top-level:', sorted(tops.items(), key=lambda x: -x[1])[:14], flush=True)
if cfg:
    out = os.path.join(os.environ['TEMP'], 'brumafomod')
    subprocess.run([SEVENZ, 'e', '-y', '-o' + out, arc, cfg], capture_output=True, timeout=1200)
    path = os.path.join(out, os.path.basename(cfg))
    if os.path.exists(path):
        print('===== Bruma ModuleConfig.xml =====', flush=True)
        print(open(path, encoding='utf-8', errors='replace').read(), flush=True)

f2 = M.pick_file(10917, prefer='DLC Integration')
arc2 = M.download(10917, f2)
print('DLC patch cached:', arc2, round(os.path.getsize(arc2)/1e6), 'MB', flush=True)
tops2, cfg2 = toplevel(arc2, timeout=300)
print('DLC patch top-level:', sorted(tops2.items(), key=lambda x: -x[1])[:14], flush=True)
if cfg2:
    out = os.path.join(os.environ['TEMP'], 'brumafomod2')
    subprocess.run([SEVENZ, 'e', '-y', '-o' + out, arc2, cfg2], capture_output=True, timeout=300)
    path = os.path.join(out, os.path.basename(cfg2))
    if os.path.exists(path):
        print('===== DLC Patch ModuleConfig.xml =====', flush=True)
        print(open(path, encoding='utf-8', errors='replace').read(), flush=True)
