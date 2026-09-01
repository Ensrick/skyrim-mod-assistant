"""Capture what the spinning threads of a hung SkyrimSE are executing, from outside.

Born 2026-09-01 for #142: three SkyrimSE.exe-entry threads spin at 100%/core
during the data-load hang, and both prior capture paths missed them (the
CrashLogger dump saw 17 of 127 threads; none was a spinner). This tool needs
no code inside the game: it samples every thread's RIP via
SuspendThread/GetThreadContext/ResumeThread, profiles the hot threads with a
RIP histogram, scans their stacks for return addresses into known modules,
and writes a full minidump for offline symbolication.

  py -3 audit/spindump.py                 # newest SkyrimSE.exe
  py -3 audit/spindump.py --pid N
  py -3 audit/spindump.py --samples 60 --no-dump

Offsets are printed as module+0xOFF; SkyrimSE.exe offsets feed straight into
the Address Library map the deep-dive workflow already uses.
"""
import argparse, ctypes, ctypes.wintypes as wt, datetime, msvcrt, os, sys, time

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')
dbghelp = ctypes.WinDLL('dbghelp')
psapi = ctypes.WinDLL('psapi')

TH32CS_SNAPTHREAD = 0x4
TH32CS_SNAPMODULE = 0x8
THREAD_ALL = 0x0002 | 0x0008 | 0x0040          # suspend/resume, get context, query
PROC_ALL = 0x0400 | 0x0010                     # query information, vm read
CONTEXT_CONTROL_INTEGER = 0x100001 | 0x100002
CTX_SIZE = 0x4D0                               # AMD64 CONTEXT
OFF_FLAGS, OFF_RSP, OFF_RBP, OFF_RIP = 0x30, 0x98, 0xA0, 0xF8
GPR_OFFS = {'rax': 0x78, 'rcx': 0x80, 'rdx': 0x88, 'rbx': 0x90, 'rbp': 0xA0,
            'rsi': 0xA8, 'rdi': 0xB0, 'r8': 0xB8, 'r9': 0xC0, 'r10': 0xC8,
            'r11': 0xD0, 'r12': 0xD8, 'r13': 0xE0, 'r14': 0xE8, 'r15': 0xF0}


# 64-bit handles truncate under ctypes' default c_int restype
for fn in ('CreateToolhelp32Snapshot', 'OpenProcess', 'OpenThread'):
    getattr(k32, fn).restype = ctypes.c_void_p
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [ctypes.c_void_p]
k32.SuspendThread.argtypes = k32.ResumeThread.argtypes = [ctypes.c_void_p]
k32.SuspendThread.restype = k32.ResumeThread.restype = wt.DWORD
k32.GetThreadContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.GetThreadTimes.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 4
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
k32.Thread32First.argtypes = k32.Thread32Next.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.Module32FirstW.argtypes = k32.Module32NextW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
ntdll.NtQueryInformationThread.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                           ctypes.c_void_p, wt.ULONG, ctypes.c_void_p]
dbghelp.MiniDumpWriteDump.argtypes = [ctypes.c_void_p, wt.DWORD, ctypes.c_void_p,
                                      wt.DWORD, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_void_p]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                ('th32ThreadID', wt.DWORD), ('th32OwnerProcessID', wt.DWORD),
                ('tpBasePri', wt.LONG), ('tpDeltaPri', wt.LONG), ('dwFlags', wt.DWORD)]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('th32ModuleID', wt.DWORD),
                ('th32ProcessID', wt.DWORD), ('GlblcntUsage', wt.DWORD),
                ('ProccntUsage', wt.DWORD), ('modBaseAddr', ctypes.c_void_p),
                ('modBaseSize', wt.DWORD), ('hModule', ctypes.c_void_p),
                ('szModule', ctypes.c_wchar * 256), ('szExePath', ctypes.c_wchar * 260)]


def _ctx_buf():
    raw = ctypes.create_string_buffer(CTX_SIZE + 16)
    addr = (ctypes.addressof(raw) + 15) & ~15
    return raw, addr


def threads_of(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    te, out = THREADENTRY32(dwSize=ctypes.sizeof(THREADENTRY32)), []
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def modules_of(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
    me, out = MODULEENTRY32W(dwSize=ctypes.sizeof(MODULEENTRY32W)), []
    ok = k32.Module32FirstW(snap, ctypes.byref(me))
    while ok:
        out.append((me.modBaseAddr or 0, me.modBaseSize, me.szModule))
        ok = k32.Module32NextW(snap, ctypes.byref(me))
    k32.CloseHandle(snap)
    return sorted(out)


def locate(addr, mods):
    for base, size, name in mods:
        if base <= addr < base + size:
            return f'{name}+0x{addr - base:X}'
    return None


def cpu_seconds(h):
    c, e, kt, ut = (ctypes.c_ulonglong() for _ in range(4))
    if not k32.GetThreadTimes(h, ctypes.byref(c), ctypes.byref(e),
                              ctypes.byref(kt), ctypes.byref(ut)):
        return None
    return (kt.value + ut.value) / 1e7


def start_address(h):
    addr = ctypes.c_ulonglong()
    st = ntdll.NtQueryInformationThread(h, 9, ctypes.byref(addr),
                                        ctypes.sizeof(addr), None)
    return addr.value if st == 0 else 0


def get_context(h):
    raw, a = _ctx_buf()
    ctypes.c_uint32.from_address(a + OFF_FLAGS).value = CONTEXT_CONTROL_INTEGER
    if k32.SuspendThread(h) == 0xFFFFFFFF:
        return None
    try:
        if not k32.GetThreadContext(h, ctypes.c_void_p(a)):
            return None
        regs = {n: ctypes.c_ulonglong.from_address(a + o).value
                for n, o in GPR_OFFS.items()}
        regs['rip'] = ctypes.c_ulonglong.from_address(a + OFF_RIP).value
        regs['rsp'] = ctypes.c_ulonglong.from_address(a + OFF_RSP).value
        return regs
    finally:
        k32.ResumeThread(h)


def read_mem(hp, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(hp, ctypes.c_void_p(addr), buf, size,
                                 ctypes.byref(got)):
        return b''
    return buf.raw[:got.value]


def stack_scan(hp, rsp, mods, span=0x4000, limit=48):
    # page-by-page: one unreadable page (stack top is near) fails a single
    # ReadProcessMemory over the whole span
    data = b''
    a = rsp
    end = rsp + span
    while a < end:
        step = min(0x1000 - (a & 0xFFF), end - a)
        chunk = read_mem(hp, a, step)
        if not chunk:
            break
        data += chunk
        a += step
    hits, last = [], None
    for i in range(0, len(data) - 7, 8):
        q = int.from_bytes(data[i:i + 8], 'little')
        where = locate(q, mods)
        if where and where != last:
            hits.append((rsp + i, where))
            last = where
            if len(hits) >= limit:
                break
    return hits


def resolve_handle(pid, value):
    """Duplicate a handle out of the target and name what it points at."""
    hp = k32.OpenProcess(0x0040 | 0x0400, False, pid)      # DUP_HANDLE | QUERY
    if not hp:
        return f'OpenProcess for dup failed: {ctypes.get_last_error()}'
    dup = ctypes.c_void_p()
    try:
        if not k32.DuplicateHandle(hp, ctypes.c_void_p(value),
                                   ctypes.c_void_p(k32.GetCurrentProcess()),
                                   ctypes.byref(dup), 0, False, 0x2):  # SAME_ACCESS
            return f'DuplicateHandle failed: {ctypes.get_last_error()}'
        ftype = k32.GetFileType(dup)
        kinds = {1: 'disk file', 2: 'char device', 3: 'pipe'}
        buf = ctypes.create_unicode_buffer(1024)
        n = k32.GetFinalPathNameByHandleW(dup, buf, 1024, 0)
        name = buf.value if n else f'(unnamed, GetFinalPathName err {ctypes.get_last_error()})'
        return f'{kinds.get(ftype, f"type {ftype}")}: {name}'
    finally:
        if dup:
            k32.CloseHandle(dup)
        k32.CloseHandle(hp)


def write_minidump(hp, pid, path):
    # ThreadInfo + FullMemoryInfo + HandleData + UnloadedModules +
    # ProcessThreadData + IndirectlyReferencedMemory: stacks and context for
    # every thread without the multi-GB full-memory payload.
    flags = 0x1000 | 0x800 | 0x4 | 0x20 | 0x100 | 0x40
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC | os.O_BINARY)
    try:
        ok = dbghelp.MiniDumpWriteDump(hp, pid, msvcrt.get_osfhandle(fd),
                                       flags, None, None, None)
        return bool(ok), ctypes.get_last_error()
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pid', type=int)
    ap.add_argument('--samples', type=int, default=50)
    ap.add_argument('--hot-threshold', type=float, default=0.4,
                    help='cores of CPU over the probe window to count as a spinner')
    ap.add_argument('--no-dump', action='store_true')
    ap.add_argument('--handle', type=lambda s: int(s, 0),
                    help='resolve this handle value in the target to a name')
    ap.add_argument('--tids', type=lambda s: [int(x) for x in s.split(',')],
                    help='profile exactly these threads instead of hot detection')
    a = ap.parse_args()

    pid = a.pid
    if not pid:
        import subprocess
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq SkyrimSE.exe', '/FO', 'CSV'],
                             capture_output=True, text=True).stdout
        rows = [r.split('","') for r in out.splitlines() if r.startswith('"SkyrimSE')]
        if not rows:
            print('no SkyrimSE.exe process'); return 1
        pid = int(rows[-1][1])
    print(f'pid {pid}')
    if a.handle is not None:
        print(f'handle 0x{a.handle:X} -> {resolve_handle(pid, a.handle)}')

    hp = k32.OpenProcess(PROC_ALL, False, pid)
    if not hp:
        print(f'OpenProcess failed: {ctypes.get_last_error()}'); return 1
    mods = modules_of(pid)
    print(f'{len(mods)} modules')

    tids = threads_of(pid)
    handles = {t: k32.OpenThread(THREAD_ALL, False, t) for t in tids}
    handles = {t: h for t, h in handles.items() if h}

    # hot-thread identification: CPU delta over 1.5s
    t0 = {t: cpu_seconds(h) for t, h in handles.items()}
    time.sleep(1.5)
    hot = []
    print(f'\n== all {len(handles)} threads: one-shot RIP + CPU over 1.5s ==')
    rows = []
    for t, h in handles.items():
        d = (cpu_seconds(h) or 0) - (t0[t] or 0)
        ctx = get_context(h)
        rip = locate(ctx['rip'], mods) if ctx else '?'
        sa = locate(start_address(h), mods) or '?'
        rows.append((d, t, rip, sa))
        if a.tids is None and d / 1.5 >= a.hot_threshold:
            hot.append(t)
    if a.tids is not None:
        hot = [t for t in a.tids if t in handles]
    for d, t, rip, sa in sorted(rows, reverse=True):
        mark = ' <== HOT' if t in hot else ''
        print(f'  cpu {d:5.3f}s  tid {t:>6}  rip {rip or "?":<44} entry {sa}{mark}')

    print(f'\n== profiling {len(hot)} hot thread(s), {a.samples} samples each ==')
    for t in hot:
        h = handles[t]
        hist, rsps, ctx0 = {}, [], None
        for _ in range(a.samples):
            ctx = get_context(h)
            if not ctx:
                continue
            ctx0 = ctx0 or ctx
            where = locate(ctx['rip'], mods) or f'0x{ctx["rip"]:X}'
            hist[where] = hist.get(where, 0) + 1
            rsps.append(ctx['rsp'])
            time.sleep(0.02)
        print(f'\n-- tid {t} --')
        for where, n in sorted(hist.items(), key=lambda kv: -kv[1]):
            print(f'  {n:>3}/{a.samples}  {where}')
        if rsps:
            print(f'  rsp range: 0x{min(rsps):X}..0x{max(rsps):X} '
                  f'(spread 0x{max(rsps) - min(rsps):X})')
        if ctx0:
            regs = '  '.join(f'{n}=0x{ctx0[n]:X}' for n in
                             ('rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp',
                              'r8', 'r9', 'r12', 'r14'))
            print(f'  regs at first sample: {regs}')
            print('  stack scan (return-address candidates from rsp):')
            for addr, where in stack_scan(hp, ctx0['rsp'], mods):
                print(f'    [rsp+0x{addr - ctx0["rsp"]:X}] {where}')

    if not a.no_dump:
        skse = os.path.join(os.environ['USERPROFILE'], 'Documents', 'My Games',
                            'Skyrim Special Edition', 'SKSE')
        path = os.path.join(skse, 'minidump-%s.dmp'
                            % datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        ok, err = write_minidump(hp, pid, path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        print(f'\nminidump: {"OK" if ok else f"FAILED err={err}"} {path} '
              f'({size / 1e6:.0f}MB)')
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
