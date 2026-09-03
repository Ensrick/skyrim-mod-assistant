"""Watch the game WHILE it runs and say continuously whether it is progressing.

preflight.py gates the launch and launch_triage.py reads the wreckage
afterwards. Between them was nothing, so on 2026-08-31 the user sat through a
two and a half minute stall with no way to tell loading from dead, and had to
ask. This closes that gap: it samples the process and the things a loading
Skyrim writes to disk, and names the state every few seconds.

  py -3 audit/launch_watch.py                  # wait for the game, then watch
  py -3 audit/launch_watch.py --pid 12345
  py -3 audit/launch_watch.py --hang-seconds 90 --interval 4
  py -3 audit/launch_watch.py --selftest       # exercise the state machine, no game
  py -3 audit/launch_watch.py --report-dir <dir>   # where a hang report is written

Exit: 0 watched to a normal end, 2 a hang was reported, 3 the process died
before reaching the menu, 4 no process ever appeared.

It NEVER kills the game. A hang gets a verdict, a thread snapshot and a written
report; ending the process stays the user's call.

The states it separates, because confusing them is what wasted the evening:

  loading      memory climbing or an SKSE-side log still being written
  shaders      Community Shaders is compiling - CPU pegged and memory flat look
               exactly like a hang, and reporting one here would be wrong
  at-menu      LaunchProbe saw the real main menu open
  stalled      nothing advancing but not yet long enough to call
  stalled-     nothing advancing, window still pumping, and NO authoritative
  unconfirmed  menu signal - a real menu and a wedge look identical from here
  hung-spin    burning CPU, nothing advancing, window dead
  hung-idle    no CPU and nothing advancing - a lock, not slow work
  died         the process is gone

Sampling is native Win32 through ctypes (GetProcessTimes,
GetProcessMemoryInfo, SendMessageTimeout) rather than a `pwsh` child per tick:
same numbers, no process spawn every few seconds while the machine is already
loading a heavy modlist.
"""
import ctypes
import ctypes.wintypes as wt
import datetime, io, os, re, sys, time

# reconfigure, not a fresh TextIOWrapper: two of these modules import each
# other's siblings, and re-wrapping an already-wrapped stdout closes the
# buffer the first wrapper owns
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except (AttributeError, ValueError):
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE = r'C:\Users\danjo\source\repos\mo2-instances\skyrim-se'
DOCS = os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'My Games',
                    'Skyrim Special Edition')
SKSE_DIR = os.path.join(DOCS, 'SKSE')
PAPYRUS_DIR = os.path.join(DOCS, 'Logs', 'Script')
SHADER_DIR = os.path.join(INSTANCE, 'overwrite', 'ShaderCache')
PROCESS_NAME = 'SkyrimSE.exe'

# ----------------------------------------------------------------- Win32 glue
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
u32 = ctypes.WinDLL('user32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')

TH32CS_SNAPPROCESS, TH32CS_SNAPTHREAD = 0x2, 0x4
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_QUERY_INFORMATION, PROCESS_VM_READ = 0x0400, 0x0010
THREAD_QUERY_LIMITED_INFORMATION, THREAD_QUERY_INFORMATION = 0x0800, 0x0040
LIST_MODULES_ALL = 0x03
SMTO_ABORTIFHUNG = 0x0002
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                ('th32ProcessID', wt.DWORD), ('th32DefaultHeapID', ctypes.c_void_p),
                ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD),
                ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', ctypes.c_long),
                ('dwFlags', wt.DWORD), ('szExeFile', ctypes.c_wchar * 260)]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                ('th32ThreadID', wt.DWORD), ('th32OwnerProcessID', wt.DWORD),
                ('tpBasePri', ctypes.c_long), ('tpDeltaPri', ctypes.c_long),
                ('dwFlags', wt.DWORD)]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [('cb', wt.DWORD), ('PageFaultCount', wt.DWORD),
                ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
                ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t),
                ('PrivateUsage', ctypes.c_size_t)]


class MODULEINFO(ctypes.Structure):
    _fields_ = [('lpBaseOfDll', ctypes.c_void_p), ('SizeOfImage', wt.DWORD),
                ('EntryPoint', ctypes.c_void_p)]


k32.OpenProcess.restype = wt.HANDLE
k32.OpenThread.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
u32.SendMessageTimeoutW.argtypes = [wt.HWND, ctypes.c_uint, ctypes.c_void_p,
                                    ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
                                    ctypes.POINTER(ctypes.c_size_t)]
# Module bases are 64-bit pointers. Without explicit argtypes ctypes marshals
# them as c_int and a normally-based DLL raises OverflowError.
k32.K32EnumProcessModulesEx.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_void_p),
                                        wt.DWORD, ctypes.POINTER(wt.DWORD), wt.DWORD]
k32.K32GetModuleInformation.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                        ctypes.POINTER(MODULEINFO), wt.DWORD]
k32.K32GetModuleBaseNameW.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                      ctypes.c_wchar_p, wt.DWORD]
ntdll.NtQueryInformationThread.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                           ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]


def _ft(ft):
    return (ft.dwHighDateTime << 32 | ft.dwLowDateTime) / 1e7      # 100ns -> seconds


def find_process(name=PROCESS_NAME):
    """Newest process with this image name, so a stale one never wins."""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in (0, -1, None):
        return None
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        found = []
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            if e.szExeFile.lower() == name.lower():
                found.append(e.th32ProcessID)
            ok = k32.Process32NextW(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    if not found:
        return None
    return max(found, key=lambda p: start_time(p) or 0)


def start_time(pid):
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        c, x, kt, ut = (wt.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(h, *(ctypes.byref(v) for v in (c, x, kt, ut))):
            return None
        return _ft(c)
    finally:
        k32.CloseHandle(h)


class Proc:
    """One open handle, sampled repeatedly. Read-only: no call here can change
    the process's state, and nothing in this file terminates anything."""

    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        self.hwnd = None
        self.cores = os.cpu_count() or 8

    def alive(self):
        code = wt.DWORD()
        if not self.h or not k32.GetExitCodeProcess(self.h, ctypes.byref(code)):
            return False
        return code.value == 259                                   # STILL_ACTIVE

    def cpu_seconds(self):
        c, x, kt, ut = (wt.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(self.h, *(ctypes.byref(v) for v in (c, x, kt, ut))):
            return None
        return _ft(kt) + _ft(ut)

    def memory(self):
        m = PROCESS_MEMORY_COUNTERS_EX()
        m.cb = ctypes.sizeof(m)
        if not k32.K32GetProcessMemoryInfo(self.h, ctypes.byref(m), m.cb):
            return None, None
        return m.WorkingSetSize, m.PrivateUsage

    def window(self):
        """Largest visible top-level window owned by the process."""
        if self.hwnd and u32.IsWindow(self.hwnd):
            return self.hwnd
        best = []

        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def cb(hwnd, _):
            owner = wt.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == self.pid and u32.IsWindowVisible(hwnd):
                r = wt.RECT()
                u32.GetWindowRect(hwnd, ctypes.byref(r))
                best.append(((r.right - r.left) * (r.bottom - r.top), hwnd))
            return True

        u32.EnumWindows(cb, 0)
        self.hwnd = max(best)[1] if best else None
        return self.hwnd

    def responding(self, timeout_ms=400):
        """Does the window pump messages? WM_NULL is a no-op the app never sees
        as input, so this cannot disturb a game that IS healthy.

        Not a health verdict on its own: a loading Skyrim is legitimately
        unresponsive for long stretches, and a main thread parked in
        GetMessage answers promptly while rendering nothing."""
        hwnd = self.window()
        if not hwnd:
            return None
        res = ctypes.c_size_t()
        ok = u32.SendMessageTimeoutW(hwnd, 0, None, None, SMTO_ABORTIFHUNG,
                                     timeout_ms, ctypes.byref(res))
        return bool(ok)

    def close(self):
        if self.h:
            k32.CloseHandle(self.h)
            self.h = None


# ------------------------------------------------------- per-thread snapshot
def thread_ids(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap in (0, -1, None):
        return []
    out = []
    try:
        e = THREADENTRY32()
        e.dwSize = ctypes.sizeof(e)
        ok = k32.Thread32First(snap, ctypes.byref(e))
        while ok:
            if e.th32OwnerProcessID == pid:
                out.append(e.th32ThreadID)
            ok = k32.Thread32Next(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    return out


def thread_cpu(tid):
    h = k32.OpenThread(THREAD_QUERY_LIMITED_INFORMATION, False, tid)
    if not h:
        return None
    try:
        c, x, kt, ut = (wt.FILETIME() for _ in range(4))
        if not k32.GetThreadTimes(h, *(ctypes.byref(v) for v in (c, x, kt, ut))):
            return None
        return _ft(kt) + _ft(ut)
    finally:
        k32.CloseHandle(h)


def thread_start_module(tid, modules):
    """Which DLL owns this thread's entry point - the closest thing to 'whose
    thread is this' without a debugger. Best effort; some threads refuse the
    query and are reported without a module rather than guessed at."""
    h = k32.OpenThread(THREAD_QUERY_INFORMATION, False, tid)
    if not h:
        return None
    try:
        addr = ctypes.c_void_p()
        # ThreadQuerySetWin32StartAddress = 9
        if ntdll.NtQueryInformationThread(h, 9, ctypes.byref(addr),
                                          ctypes.sizeof(addr), None) != 0:
            return None
        a = addr.value or 0
        for base, size, name in modules:
            if base <= a < base + size:
                return name
        return None
    finally:
        k32.CloseHandle(h)


def module_map(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        return []
    try:
        arr = (ctypes.c_void_p * 2048)()
        need = wt.DWORD()
        if not k32.K32EnumProcessModulesEx(h, arr, ctypes.sizeof(arr),
                                           ctypes.byref(need), LIST_MODULES_ALL):
            return []
        out = []
        for i in range(min(need.value // ctypes.sizeof(ctypes.c_void_p), 2048)):
            mi, buf = MODULEINFO(), ctypes.create_unicode_buffer(260)
            if k32.K32GetModuleInformation(h, arr[i], ctypes.byref(mi), ctypes.sizeof(mi)):
                k32.K32GetModuleBaseNameW(h, arr[i], buf, 260)
                out.append((mi.lpBaseOfDll or 0, mi.SizeOfImage, buf.value))
        return out
    finally:
        k32.CloseHandle(h)


def busiest_threads(pid, window=1.5, top=6):
    """CPU burned per thread over a short window, attributed to a module.

    This is the evidence that separates 'one thread spinning in a mod' from
    'the whole process is asleep on a lock'."""
    mods = module_map(pid)
    first = {t: thread_cpu(t) for t in thread_ids(pid)}
    time.sleep(window)
    rows = []
    for tid, was in first.items():
        if was is None:
            continue                                  # handle refused, not a datum
        now = thread_cpu(tid)
        if now is None:
            # the thread ended inside the sample window; that is itself worth
            # seeing, and dropping it silently once left the table empty
            rows.append((0.0, tid, '(thread exited during sample)'))
            continue
        rows.append((now - was, tid, thread_start_module(tid, mods)))
    rows.sort(reverse=True)
    return rows[:top], len(first), bool(mods)


# --------------------------------------------------------- progress on disk
def _tree(path):
    files = size = 0
    newest = 0.0
    for root, _dirs, names in os.walk(path):
        for n in names:
            try:
                st = os.stat(os.path.join(root, n))
            except OSError:
                continue
            files += 1
            size += st.st_size
            newest = max(newest, st.st_mtime)
    return files, size, newest


def _logs(path, skip=('crash-', 'threaddump-')):
    out = {}
    if not os.path.isdir(path):
        return out
    for n in os.listdir(path):
        if not n.lower().endswith('.log') or n.startswith(skip):
            continue
        try:
            st = os.stat(os.path.join(path, n))
        except OSError:
            continue
        out[n] = (st.st_size, st.st_mtime)
    return out


class Progress:
    """Everything a loading Skyrim leaves on disk, sampled cheaply.

    Shader cache lives on its own signal on purpose. A first launch after a
    shader-affecting change pegs a core with memory flat for minutes; that is
    the single most hang-shaped thing this build does that is not a hang, and
    the cache is the proof it is working."""

    def __init__(self):
        self.stride = 1                 # shader walk every Nth sample, adapted
        self._n = 0
        self._shader = (0, 0, 0.0)

    def sample(self):
        self._n += 1
        logs = _logs(SKSE_DIR)
        pap = _logs(PAPYRUS_DIR)
        if os.path.isdir(SHADER_DIR) and self._n % self.stride == 0:
            t0 = time.time()
            self._shader = _tree(SHADER_DIR)
            cost = time.time() - t0
            # a growing cache must never make the watcher itself the slow part
            self.stride = 1 if cost < 0.25 else (2 if cost < 0.75 else 4)
        return {'logs': logs, 'papyrus': pap, 'shader': self._shader}

    @staticmethod
    def delta(old, new):
        """Which signals moved SINCE THE LAST SAMPLE, named for the report.

        Progress is movement, never recency. Judging it by "written in the last
        minute" reports `progressing` forty seconds into a hang, because a
        stale burst keeps satisfying the window; that bug is why this compares
        sample to sample and nothing else.

        Size is compared with `!=`, not `>`: SKSE truncates skse64.log at
        startup, so a fresh launch begins by SHRINKING the file it will then
        fill, and a `>` test would score real progress as a stall for as long
        as it took to grow back past the previous session's size."""
        moved = []
        for group in ('logs', 'papyrus'):
            for name, (size, mt) in new[group].items():
                was = old[group].get(name)
                if was is None:
                    moved.append(f'new log {name}')
                elif size != was[0]:
                    moved.append(f'{name} {size - was[0]:+d}B')
                elif mt > was[1]:
                    moved.append(f'{name} rewritten')
        if new['shader'][1] != old['shader'][1] or new['shader'][2] > old['shader'][2]:
            moved.append(f'ShaderCache {new["shader"][0] - old["shader"][0]:+d} files, '
                         f'{(new["shader"][1] - old["shader"][1]) // 1024:+d}KB')
        return moved


def shader_moved(moved):
    return any(m.startswith('ShaderCache') or m.startswith('CommunityShaders.log')
               for m in moved)


# LAUNCH_PROBE_LOG overrides the path so the harness can be tested against a
# synthetic timeline without writing into the live SKSE log directory.
PROBE_LOG = os.environ.get('LAUNCH_PROBE_LOG',
                           os.path.join(SKSE_DIR, 'LaunchProbe.log'))
MENU_EVENTS = {'MAIN_MENU_OPEN', 'MAIN_MENU_ALREADY_OPEN'}


def probe_events(since=None):
    """LaunchProbe's timeline, or None when the probe is not installed.

    LaunchProbe is a micro SKSE plugin built for this harness; it logs the
    game's own UI and SKSE messaging events with wall-clock timestamps. It is
    the only main-menu signal in this build that is worth anything - see
    menu_confirmed() for why."""
    if not os.path.exists(PROBE_LOG):
        return None
    if since is not None and os.path.getmtime(PROBE_LOG) < since - 5:
        return None                                    # left over from a past run
    out = []
    try:
        lines = io.open(PROBE_LOG, encoding='utf-8', errors='replace').readlines()
    except OSError:
        # A sharing violation mid-run (the probe's pre-2026-09-01 build held the
        # log deny-all) must degrade to "no events yet", never abort the watch:
        # the first such abort killed a healthy bisect launch as 'FAIL: not run'.
        return []
    for line in lines:
        # [2026-08-31 23:04:12.345] +1234ms TOKEN key="value" ...
        m = re.match(r'\[([\d\-: .]+)\]\s+\+(\d+)ms\s+(\S+)(.*)', line.strip())
        if not m:
            continue
        token, rest = m.group(3), m.group(4).strip()
        # SKSE messages all arrive under one token with the real name inside;
        # lift it so callers can ask for 'kDataLoaded' directly
        name = re.match(r'name="([^"]+)"', rest)
        event = name.group(1) if (token == 'SKSE_MESSAGE' and name) else token
        out.append({'wall': m.group(1), 'ms': int(m.group(2)),
                    'event': event, 'token': token, 'rest': rest})
    return out


def markers(since=None):
    """What this session has actually reached.

    `menu_confirmed` is deliberately three-valued. True and False come only
    from LaunchProbe; None means nobody can tell. Community Shaders'
    `InitializeMenuIcons` line USED to fill this role and it is a liar: on both
    hung launches of 2026-08-31 it fired at about T+56s and the game never
    became playable. A signal that fires during the failure it is supposed to
    rule out is worse than no signal, so it is recorded as `weak_menu_hint` and
    never decides anything."""
    out = {'skse_init_done': False, 'last_plugin': None, 'menu_confirmed': None,
           'menu_source': 'no authoritative signal (LaunchProbe not installed)',
           'save_loaded': None, 'weak_menu_hint': False}
    log = os.path.join(SKSE_DIR, 'skse64.log')
    if os.path.exists(log):
        t = io.open(log, encoding='utf-8', errors='replace').read()
        out['skse_init_done'] = ('dispatch message' in t) or ('Reading translations' in t)
        loads = [l.split('"')[1] for l in t.splitlines()
                 if l.startswith('loading plugin "') and '"' in l]
        out['last_plugin'] = loads[-1] if loads else None
    cs = os.path.join(SKSE_DIR, 'CommunityShaders.log')
    if os.path.exists(cs):
        tail = io.open(cs, encoding='utf-8', errors='replace').read()[-40000:]
        out['weak_menu_hint'] = 'InitializeMenuIcons' in tail
    ev = probe_events(since)
    if ev is not None:
        names = [e['event'] for e in ev]
        # ALREADY_OPEN is the same proof: the sink registered after the menu was
        # up, so the probe polled IsMenuOpen instead of catching the event
        out['menu_confirmed'] = bool(MENU_EVENTS & set(names))
        out['menu_source'] = 'LaunchProbe ' + '/'.join(sorted(MENU_EVENTS))
        post = [e for e in ev if e['event'] == 'kPostLoadGame']
        out['save_loaded'] = bool(post) and 'success=1' in post[-1]['rest']
    return out


# ------------------------------------------------------------ state machine
class Cfg:
    interval = 4.0
    hang_seconds = 75.0        # the user's 2.5-minute wait must never repeat
    spin_cpu = 20.0            # % of one core, above which a stall is a spin
    mem_step_mb = 24.0         # working-set growth that counts as progress
    stable_mb = 1800.0


def classify(s, cfg=Cfg):
    """s: dict with alive, moved, cpu_core_pct, ws_mb, ws_delta_mb, responding,
    stalled_for, markers. Returns (state, evidence list).

    Pure function of one sample so --selftest can prove the branches without a
    game; every launch-state bug so far has been a wrong branch, not bad data."""
    ev = []
    if not s['alive']:
        return 'died', ['process is gone']
    if s['moved']:
        ev.append('advancing: ' + ', '.join(s['moved'][:4]))
        if shader_moved(s['moved']) and s['ws_delta_mb'] < cfg.mem_step_mb:
            ev.append('shader cache is growing - CPU-bound with flat memory is '
                      'CORRECT here, this is compilation, not a hang')
            return 'shaders', ev
        return 'loading', ev
    if s['ws_delta_mb'] >= cfg.mem_step_mb:
        return 'loading', [f'working set +{s["ws_delta_mb"]:.0f}MB with no log write']
    ev.append(f'nothing on disk moved for {s["stalled_for"]:.0f}s')
    m = s['markers']
    if m.get('menu_confirmed') and s['ws_mb'] >= cfg.stable_mb:
        return 'at-menu', [f'{m.get("menu_source")} fired and {s["ws_mb"]:.0f}MB is '
                           f'resident - idle here is the game waiting for you']
    if s['stalled_for'] < cfg.hang_seconds:
        return 'stalled', ev
    if not m.get('skse_init_done'):
        ev.append(f'SKSE never finished init; last plugin logged was '
                  f'{m.get("last_plugin")}')
    if s['responding'] is False:
        ev.append('window is not pumping messages')
    elif s['responding']:
        ev.append('window answers WM_NULL, so the message loop turns - but the main '
                  'thread of the 2026-08-31 hang was parked in GetMessage and looked '
                  'exactly like this, so this is not reassurance')
    if s['cpu_core_pct'] >= cfg.spin_cpu:
        ev.append(f'burning {s["cpu_core_pct"]:.0f}% of a core with nothing to show '
                  f'for it')
        return 'hung-spin', ev
    ev.append(f'CPU is idle ({s["cpu_core_pct"]:.0f}% of a core) - waiting on a lock '
              f'or an event, not doing slow work')
    # No authoritative menu signal means the two readings that matter - "sitting
    # at a real main menu" and "wedged with a message loop still turning" - are
    # indistinguishable from outside the process. Say so instead of picking one.
    if (m.get('menu_confirmed') is None and s['responding']
            and s['ws_mb'] >= cfg.stable_mb and m.get('skse_init_done')):
        ev.append('CANNOT TELL a real main menu from a wedge: ' + str(m.get('menu_source'))
                  + '. If a menu is on screen and responds to input this is normal; if '
                    'the screen is black or frozen it is the hang. Install LaunchProbe '
                    '(records/source-builds/launch-probe) to make this decidable.')
        return 'stalled-unconfirmed', ev
    return 'hung-idle', ev


HANG = ('hung-spin', 'hung-idle', 'stalled-unconfirmed')


# ----------------------------------------------------------------- reporting
def crash_after(log_mtime):
    if not os.path.isdir(SKSE_DIR):
        return None
    newer = [f for f in os.listdir(SKSE_DIR)
             if f.startswith('crash-') and f.endswith('.log')
             and os.path.getmtime(os.path.join(SKSE_DIR, f)) > log_mtime]
    return sorted(newer)[-1] if newer else None


DUMP_ADVICE = """How to get a thread dump of this hang

  1. Give the game window focus and press Ctrl+Shift+F12 (CrashLogger's manual
     trigger; already enabled - see CrashLogger.log "Thread dump hotkey
     monitoring started").
  2. Run: py -3 audit/threaddump.py

This watcher does NOT press it for you. CrashLogger polls GetAsyncKeyState on
its own thread (its import table has GetAsyncKeyState and no RegisterHotKey and
no window hook), so a synthetic trigger would mean injecting global keystrokes
with SendInput and hoping the poll catches them: delivery depends on which
window has focus, the keys land in whatever app is foreground, and an elevated
game blocks injection from an unelevated watcher entirely. Unreliable and
invisible when it fails, so it is not done. There is no event, pipe or file
trigger in the DLL to use instead."""


def write_report(path, state, ev, hist, pid, threads, markers_now):
    now = datetime.datetime.now()
    L = [f'# Launch watch - {state.upper()}', '',
         f'- when: {now:%Y-%m-%d %H:%M:%S}',
         f'- pid: {pid}',
         f'- watched for: {hist[-1]["elapsed"]:.0f}s',
         f'- verdict: **{state}**', '', '## Evidence', '']
    L += [f'- {e}' for e in ev]
    L += ['', '## Markers', '',
          f'- SKSE init finished: {markers_now.get("skse_init_done")}',
          f'- last plugin logged: {markers_now.get("last_plugin")}',
          f'- menu reached: {markers_now.get("menu")}', '',
          '## Samples (last 20)', '',
          '| t+s | cpu %core | ws MB | responding | state | moved |',
          '|---|---|---|---|---|---|']
    for h in hist[-20:]:
        L.append(f'| {h["elapsed"]:.0f} | {h["cpu_core_pct"]:.0f} | {h["ws_mb"]:.0f} '
                 f'| {h["responding"]} | {h["state"]} | '
                 f'{", ".join(h["moved"][:3]) or "-"} |')
    if threads:
        rows, total, have_mods = threads
        L += ['', f'## Threads ({total} in the process)', '',
              '| CPU s in 1.5s | tid | entry-point module |', '|---|---|---|']
        for cpu, tid, mod in rows:
            L.append(f'| {cpu:.3f} | {tid} | {mod or "(unattributed)"} |')
        if not have_mods:
            L.append('')
            L.append('Module list unavailable (handle refused) - entry points could '
                     'not be attributed.')
    L += ['', '## Next', '', DUMP_ADVICE, '',
          'The game was NOT killed by this tool.']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    return path


# ---------------------------------------------------------------------- main
def watch(pid, cfg, quiet=False, report_dir=None):
    p = Proc(pid)
    prog = Progress()
    t0 = time.time()
    prev_cpu, prev_ws = p.cpu_seconds() or 0.0, (p.memory()[0] or 0) / 1e6
    prev_prog = prog.sample()
    last_move = time.time()
    hist, reported, rc = [], False, 0
    print(f'watching pid {pid} ({PROCESS_NAME}), interval {cfg.interval:.0f}s, '
          f'hang threshold {cfg.hang_seconds:.0f}s - Ctrl-C to stop\n')
    try:
        while True:
            time.sleep(cfg.interval)
            alive = p.alive()
            cpu = p.cpu_seconds() if alive else None
            ws_b, _priv = p.memory() if alive else (None, None)
            ws = (ws_b or 0) / 1e6
            now_prog = prog.sample()
            moved = Progress.delta(prev_prog, now_prog)
            if moved:
                last_move = time.time()
            cpu_pct = ((cpu - prev_cpu) / cfg.interval * 100) if (cpu and alive) else 0.0
            s = {
                'alive': alive, 'moved': moved, 'cpu_core_pct': cpu_pct,
                'ws_mb': ws, 'ws_delta_mb': ws - prev_ws,
                'responding': p.responding() if alive else None,
                'stalled_for': time.time() - last_move, 'markers': markers(),
            }
            state, ev = classify(s, cfg)
            row = {'elapsed': time.time() - t0, 'cpu_core_pct': cpu_pct, 'ws_mb': ws,
                   'responding': s['responding'], 'state': state, 'moved': moved}
            hist.append(row)
            if not quiet:
                resp = {True: 'responding', False: 'NOT-responding',
                        None: 'no-window'}[s['responding']]
                print(f'  t+{row["elapsed"]:>4.0f}s  {state:<10} cpu {cpu_pct:>5.1f}%core  '
                      f'ws {ws:>6.0f}MB ({s["ws_delta_mb"]:+.0f})  {resp:<15} '
                      f'{", ".join(moved[:2]) or "-"}')
            prev_cpu, prev_ws, prev_prog = cpu or prev_cpu, ws, now_prog

            if state == 'died':
                print('\nPROCESS GONE after '
                      f'{row["elapsed"]:.0f}s of watching.')
                log = os.path.join(SKSE_DIR, 'skse64.log')
                if os.path.exists(log):
                    c = crash_after(os.path.getmtime(log))
                    print(f'   crash log newer than skse64.log: {c}' if c else
                          '   no crash log newer than skse64.log - it exited or was '
                          'killed rather than crashing')
                m = markers()
                rc = 0 if m.get('menu') else 3
                print('   run: py -3 audit/launch_triage.py')
                break
            if state in HANG and not reported:
                reported, rc = True, 2
                print(f'\n=== {state.upper()} ===')
                for e in ev:
                    print(f'   {e}')
                print('   capturing per-thread CPU (1.5s)...')
                threads = busiest_threads(pid)
                rows, total, have_mods = threads
                print(f'   {total} threads; busiest over 1.5s:')
                for cpus, tid, mod in rows:
                    print(f'      {cpus:6.3f}s  tid {tid:<7} {mod or "(unattributed)"}')
                stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                path = os.path.join(report_dir or os.path.join(REPO, 'records'),
                                    f'launch-watch-{stamp}.md')
                write_report(path, state, ev, hist, pid, threads, markers())
                print(f'\n{DUMP_ADVICE}\n')
                print(f'   report: {path}')
                print('   the game is still running - this tool does not kill it\n')
            elif state not in HANG and reported:
                reported = False       # it came back; re-arm for a later stall
                print('   ...progress resumed, hang report re-armed')
    except KeyboardInterrupt:
        print('\nstopped (Ctrl-C). The game was not touched.')
    finally:
        p.close()
    return rc


def selftest():
    """Prove each branch. The hard cases are the two that look identical from
    the process alone: shader compilation and a spin."""
    M = {'skse_init_done': True, 'menu_confirmed': None, 'last_plugin': 'x',
         'menu_source': 'no authoritative signal (LaunchProbe not installed)'}
    base = {'alive': True, 'moved': [], 'cpu_core_pct': 0.0, 'ws_mb': 2500.0,
            'ws_delta_mb': 0.0, 'responding': True, 'stalled_for': 0.0, 'markers': M}
    cases = [
        ('died', {'alive': False}),
        ('loading', {'moved': ['skse64.log +900B'], 'ws_delta_mb': 5.0}),
        ('loading', {'ws_delta_mb': 120.0}),
        ('shaders', {'moved': ['ShaderCache +14 files, +900KB'], 'cpu_core_pct': 99.0,
                     'ws_delta_mb': 0.0}),
        # a shader write WITH memory climbing is ordinary loading, not a compile stall
        ('loading', {'moved': ['ShaderCache +2 files, +40KB'], 'ws_delta_mb': 200.0}),
        ('stalled', {'stalled_for': 30.0}),
        ('hung-spin', {'stalled_for': 120.0, 'cpu_core_pct': 88.0, 'responding': False}),
        ('hung-idle', {'stalled_for': 120.0, 'cpu_core_pct': 0.4, 'responding': False}),
        # tonight's shape: stalled and idle, but the window still answers and no
        # probe is installed - the one case nobody outside the process can call
        ('stalled-unconfirmed', {'stalled_for': 150.0, 'cpu_core_pct': 1.0,
                                 'responding': True}),
        # same shape, but SKSE never finished init: that IS decidable
        ('hung-idle', {'stalled_for': 150.0, 'cpu_core_pct': 1.0, 'responding': True,
                       'markers': dict(M, skse_init_done=False)}),
        ('at-menu', {'stalled_for': 300.0, 'responding': True, 'ws_mb': 4000.0,
                     'markers': dict(M, menu_confirmed=True,
                                     menu_source='LaunchProbe MAIN_MENU_OPEN')}),
        # the liar: CS menu icons must never produce at-menu on its own
        ('stalled-unconfirmed', {'stalled_for': 300.0, 'responding': True,
                                 'ws_mb': 4000.0,
                                 'markers': dict(M, weak_menu_hint=True)}),
    ]
    bad = 0
    for want, patch in cases:
        s = dict(base, **patch)
        got, ev = classify(s)
        flag = 'ok  ' if got == want else 'FAIL'
        bad += got != want
        print(f'  {flag} want {want:<10} got {got:<10} {ev[0][:70] if ev else ""}')
    print(f'\n{len(cases) - bad}/{len(cases)} state-machine cases pass')
    # the disk scanners must survive a machine with no game running
    prog = Progress()
    a = prog.sample()
    b = prog.sample()
    print(f'  ok   scanners read {len(a["logs"])} SKSE log(s), '
          f'{a["shader"][0]} shader cache file(s); delta {Progress.delta(a, b) or "none"}')
    m = markers()
    print(f'  ok   markers: {m}')
    print(f'  ok   find_process({PROCESS_NAME}) -> {find_process()}')
    return 1 if bad else 0


def main():
    a = sys.argv[1:]

    def opt(name, cast, default):
        return cast(a[a.index(name) + 1]) if name in a else default

    cfg = Cfg()
    cfg.interval = opt('--interval', float, Cfg.interval)
    cfg.hang_seconds = opt('--hang-seconds', float, Cfg.hang_seconds)
    cfg.spin_cpu = opt('--spin-cpu', float, Cfg.spin_cpu)
    if '--selftest' in a:
        return selftest()
    k32.SetPriorityClass(k32.GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS)

    pid = opt('--pid', int, None)
    wait = opt('--wait', float, 240.0)
    if pid is None:
        deadline = time.time() + wait
        print(f'waiting up to {wait:.0f}s for {PROCESS_NAME} to appear '
              f'(launch the game now)...')
        while time.time() < deadline:
            pid = find_process()
            if pid:
                break
            time.sleep(2)
        if not pid:
            print(f'no {PROCESS_NAME} process appeared within {wait:.0f}s - the launch '
                  f'never got as far as starting the game.\n'
                  f'   run: py -3 audit/launch_triage.py --max-age-min 5')
            return 4
    return watch(pid, cfg, quiet='--quiet' in a,
                 report_dir=opt('--report-dir', str, None))


if __name__ == '__main__':
    sys.exit(main())
