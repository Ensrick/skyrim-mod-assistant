"""Read a CrashLogger thread dump and say what the process was actually doing.

A dump is 127 threads of raw call stacks. The question is always the same and
takes several minutes to answer by hand: is anything RUNNING, and if not, what
is everything waiting on? This groups the threads by stack signature, names the
first non-system module in each group, and prints a verdict.

  py -3 audit/threaddump.py                       # newest dump in the SKSE dir
  py -3 audit/threaddump.py <path-to-dump.log>
  py -3 audit/threaddump.py --json

Born 2026-08-31: the 22:13 hang dump showed the main thread parked in a window
message wait routed through gameoverlayrenderer64.dll (the Steam overlay hooks
the message loop) with every Community Shaders pool thread idle in a condition
variable. Reaching that conclusion by eye took several manual passes; it is one
command now. See launch_watch.py, which tells you when to take a dump at all.
"""
import io, json, os, re, sys

# reconfigure, not a fresh TextIOWrapper: two of these modules import each
# other's siblings, and re-wrapping an already-wrapped stdout closes the
# buffer the first wrapper owns
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

SKSE_DIR = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                        'Skyrim Special Edition', 'SKSE')

# Frames in these modules say nothing about WHOSE code is running - they are the
# floor every thread stands on. The first frame outside this set is the answer.
SYSTEM = {
    'ntdll.dll', 'kernelbase.dll', 'kernel32.dll', 'ucrtbase.dll', 'user32.dll',
    'win32u.dll', 'msvcp140.dll', 'msvcp140_atomic_wait.dll', 'vcruntime140.dll',
    'vcruntime140_1.dll', 'msvcrt.dll', 'combase.dll', 'rpcrt4.dll', 'sechost.dll',
    'ole32.dll', 'oleaut32.dll', 'advapi32.dll', 'gdi32.dll', 'gdi32full.dll',
    'shcore.dll', 'shell32.dll', 'bcryptprimitives.dll', 'bcrypt.dll', 'crypt32.dll',
    'ws2_32.dll', 'winmm.dll', 'imm32.dll', 'powrprof.dll', 'umpdc.dll',
    'msvcp_win.dll', 'ntmarta.dll', 'cfgmgr32.dll', 'dxgi.dll', 'd3d11.dll',
}
# Not system, but not the answer either: naming the vendor is more useful than
# naming the export.
DRIVER = re.compile(r'^(nvwgf2umx|nvoglv64|nvapi64|nvldumd|amdxc64|amdvlk64|atidxx64|'
                    r'igd(10i)?umd\w*|d3d12core|d3dcompiler_\d+)\.dll$', re.I)

FRAME = re.compile(r'^\s*\[\s*(\d+)\]\s+0x([0-9A-Fa-f]+)\s+(\S+?)\+([0-9A-Fa-f]+)(.*)$')
THREAD = re.compile(r'^=+\s*THREAD\s+(\d+)\s+\(ID:\s*(\d+)\)\s*=+\s*$')


def newest_dump(directory=SKSE_DIR):
    if not os.path.isdir(directory):
        return None
    cand = [os.path.join(directory, f) for f in os.listdir(directory)
            if f.startswith('threaddump-') and f.endswith('.log')]
    return max(cand, key=os.path.getmtime) if cand else None


def _symbol(rest):
    """The human-readable half of a frame line, if the dump resolved one."""
    if '|' not in rest:
        return ''
    sym = rest.split('|', 1)[1].strip()
    sym = re.sub(r'\s*\[\?[^\]]*\]', '', sym)          # drop mangled duplicates
    sym = re.sub(r'^[A-Za-z]:\\[^\s]*?[\\/]([\w.+-]+:\d+)\s+', r'\1 ', sym)
    sym = sym.split('| params:')[0].strip()      # the signature, not the arg values
    return re.sub(r'\s+', ' ', sym)[:150]


def parse(path):
    head, threads, cur, in_stack = [], [], None, False
    for line in io.open(path, encoding='utf-8', errors='replace'):
        m = THREAD.match(line)
        if m:
            cur = {'index': int(m.group(1)), 'tid': int(m.group(2)), 'frames': []}
            threads.append(cur)
            in_stack = False
            continue
        if cur is None:
            if line.strip() and not line.startswith('='):
                head.append(line.strip())
            continue
        if 'CALLSTACK' in line:
            in_stack = True
            continue
        f = FRAME.match(line)
        if f and in_stack:
            cur['frames'].append({
                'n': int(f.group(1)), 'addr': f.group(2),
                'module': f.group(3), 'offset': f.group(4),
                'symbol': _symbol(f.group(5)),
            })
    return head, threads


def best_symbol(frames):
    """The most informative resolved name belonging to the thread's own module.

    Two traps: CrashLogger resolves the nearest preceding symbol, so a
    data-heavy module reports a static variable (`ShaderCache::instance`) where
    a function was meant; and every stack bottoms out in the process entry
    point, so an unrestricted search reports SKSE's WinMain hook for threads
    that have nothing to do with it. Stay inside the module that owns the
    thread, and prefer a symbol with an argument list."""
    o = owner(frames)
    if o is None:
        return ''
    ranked = []
    for depth, fr in enumerate(frames):
        sym = fr['symbol']
        if not sym or fr['module'].lower() != o['module'].lower():
            continue
        # a source file:line prefix means the dump resolved real debug info for
        # code, not the nearest static object; that beats a bare decorated name
        rank = 0 if re.match(r'^[\w.+-]+:\d+\s', sym) else (1 if '(' in sym else 2)
        ranked.append((rank, depth, sym))
    return min(ranked)[2] if ranked else ''


def owner(frames, skip_driver=False):
    """First frame that belongs to somebody's code rather than the OS floor."""
    for fr in frames:
        low = fr['module'].lower()
        if low in SYSTEM:
            continue
        if skip_driver and DRIVER.match(fr['module']):
            continue
        return fr
    return None


def kind(frames):
    """What the thread is doing, from the top of its stack.

    A stack top inside win32u/USER32 is a message wait; inside ntdll or
    KERNELBASE it is a kernel wait (mutex, condition variable, I/O). A top frame
    in anybody else's module means the thread was executing when sampled - the
    only case where the dump caught real work in flight."""
    if not frames:
        return 'empty'
    top = frames[0]['module'].lower()
    if top in ('win32u.dll',) or (top == 'user32.dll' and len(frames) > 1):
        return 'message-wait'
    if top in ('ntdll.dll', 'kernelbase.dll'):
        return 'kernel-wait'
    if top in SYSTEM:
        return 'system'
    return 'running'


def signature(t):
    """Group key: kind plus the first two non-system modules, which is enough to
    put every worker of one pool in one bucket without merging unrelated pools."""
    mods, seen = [], set()
    for fr in t['frames']:
        low = fr['module'].lower()
        if low in SYSTEM or low in seen:
            continue
        seen.add(low)
        mods.append(fr['module'])
        if len(mods) == 2:
            break
    return (kind(t['frames']), tuple(mods))


def analyse(path):
    head, threads = parse(path)
    groups = {}
    for t in threads:
        groups.setdefault(signature(t), []).append(t)
    running = [t for t in threads if kind(t['frames']) == 'running']
    main = next((t for t in threads if t['index'] == 1), None)
    overlay = [t for t in threads
               if any('gameoverlayrenderer' in f['module'].lower() for f in t['frames'])]
    modules = {}
    for t in threads:
        o = owner(t['frames'])
        if o:
            modules[o['module']] = modules.get(o['module'], 0) + 1
    return {
        'path': path, 'header': head, 'threads': threads, 'groups': groups,
        'running': running, 'main': main, 'overlay': overlay, 'modules': modules,
    }


def verdict(a):
    """One paragraph a human can act on, with the evidence named inline."""
    out, total = [], len(a['threads'])
    claimed = next((h.split(':', 1)[1].strip() for h in a['header']
                    if h.lower().startswith('total threads')), None)
    if claimed and claimed.isdigit() and int(claimed) > total:
        out.append(f'CrashLogger walked {total} of the {claimed} live threads; the rest '
                   f'had no walkable stack. Everything below describes those {total}.')
    if a['running']:
        mods = sorted({(owner(t['frames']) or t['frames'][0])['module']
                       for t in a['running']})
        out.append(f'{len(a["running"])} of {total} dumped thread(s) were EXECUTING, '
                   f'in {", ".join(mods)} - the process was doing work at dump time, '
                   f'so this is a slow operation or a spin, not a lock deadlock.')
    else:
        out.append(f'NO thread was executing: all {total} dumped stacks sit in a '
                   f'kernel or message wait. Nothing was computing, so a long '
                   f'stall here is not shader compilation or any other CPU work.')
    m = a['main']
    if m:
        k = kind(m['frames'])
        o = owner(m['frames'])
        sym = best_symbol(m['frames'])
        where = f'{o["module"] if o else "?"}' + (f' ({sym})' if sym else '')
        if k == 'message-wait':
            out.append(f'Main thread (TID {m["tid"]}) is blocked in a window message '
                       f'wait; first non-system frame is {where}.')
        else:
            out.append(f'Main thread (TID {m["tid"]}) is in a {k}; first non-system '
                       f'frame is {where}.')
    cs = [t for t in a['threads']
          if (owner(t['frames']) or {}).get('module', '').lower() == 'communityshaders.dll']
    if cs and all(kind(t['frames']) != 'running' for t in cs):
        out.append(f'All {len(cs)} Community Shaders pool thread(s) are parked in their '
                   f'worker wait, so NO shader was being compiled - rule shader '
                   f'compilation out as the reason for this stall.')
    if a['overlay']:
        ids = ', '.join(f'#{t["index"]}' for t in a['overlay'])
        out.append(f'gameoverlayrenderer64.dll (Steam overlay) is ON the stack of '
                   f'thread(s) {ids} - the overlay hooks the window procedure, so it '
                   f'sits between the OS and the game in the message loop. It has '
                   f'hung this build before; turn it off for app 489830 before '
                   f'blaming a mod.')
    return out


def report(path, as_json=False):
    """Print the grouped analysis for one dump. Importable so launch_session
    can fold it into a session summary without shelling out."""
    if not path or not os.path.exists(path):
        print('no thread dump found - press Ctrl+Shift+F12 in-game to take one '
              f'(CrashLogger writes it to {SKSE_DIR})')
        return 1
    a = analyse(path)
    if as_json:
        print(json.dumps({
            'path': path, 'header': a['header'],
            'threads': [{'index': t['index'], 'tid': t['tid'], 'kind': kind(t['frames']),
                         'owner': (owner(t['frames']) or {}).get('module'),
                         'symbol': best_symbol(t['frames'])}
                        for t in a['threads']],
            'modules': a['modules'],
        }, indent=1))
        return 0

    print(f'{os.path.basename(path)}')
    for line in a['header']:
        print(f'   {line}')
    print(f'   stacks walked in this dump: {len(a["threads"])}\n')

    print('thread groups (by state and first two non-system modules):')
    for sig, ts in sorted(a['groups'].items(), key=lambda kv: -len(kv[1])):
        state, mods = sig
        rep = ts[0]
        sym = best_symbol(rep['frames'])
        ids = ', '.join(f'#{t["index"]}' for t in ts[:6]) + (' ...' if len(ts) > 6 else '')
        print(f'   {len(ts):>3}x  {state:<13} {" <- ".join(mods) or "(system only)"}')
        print(f'         threads {ids}')
        if sym:
            print(f'         named frame: {sym}')
    print('\nfirst non-system module by thread count:')
    for mod, n in sorted(a['modules'].items(), key=lambda kv: -kv[1]):
        print(f'   {n:>3}  {mod}')
    print('\nVERDICT')
    for line in verdict(a):
        for chunk in _wrap(line, 88):
            print(f'   {chunk}')
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    return report(args[0] if args else newest_dump(), as_json='--json' in sys.argv)


def _wrap(text, width):
    words, line, out = text.split(), '', []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f'{line} {w}'.strip()
    if line:
        out.append(line)
    return out


if __name__ == '__main__':
    sys.exit(main())
