using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

// Diagnostic workers only. A private desktop prevents child dialogs appearing
// on the user's desktop; a kill-on-close job owns the entire descendant tree.
// No desktop switch, elevation request, global hook, or OS input injection.
public static class QuietWorker
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct Startup {
        public int cb;
        public string reserved, desktop, title;
        public uint x, y, width, height, xchars, ychars, fill, flags;
        public short show, reservedSize;
        public IntPtr reservedPointer, input, output, error;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct ProcessInfo { public IntPtr process, thread; public uint pid, tid; }
    [StructLayout(LayoutKind.Sequential)]
    struct BasicLimits {
        public long processTime, jobTime;
        public uint flags;
        public UIntPtr minWorkingSet, maxWorkingSet;
        public uint activeProcesses;
        public UIntPtr affinity;
        public uint priority, scheduling;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct IoCounters { public ulong readOps, writeOps, otherOps, readBytes, writeBytes, otherBytes; }
    [StructLayout(LayoutKind.Sequential)]
    struct ExtendedLimits {
        public BasicLimits basic;
        public IoCounters io;
        public UIntPtr processMemory, jobMemory, peakProcessMemory, peakJobMemory;
    }
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateDesktop(string name, IntPtr device, IntPtr mode, uint flags, uint access, IntPtr security);
    [DllImport("user32.dll")] static extern bool CloseDesktop(IntPtr desktop);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateJobObject(IntPtr security, string name);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedLimits limits, uint size);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool CreateProcess(string app, StringBuilder command, IntPtr processSecurity, IntPtr threadSecurity,
        bool inheritHandles, uint flags, IntPtr environment, string directory, ref Startup startup, out ProcessInfo process);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle, uint timeout);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process, out uint code);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(IntPtr process, uint code);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateJobObject(IntPtr job, uint code);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint threadId);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool GetUserObjectInformation(IntPtr handle, int index, StringBuilder value, uint length, out uint needed);

    public static bool IsPrivateWorkerDesktop()
    {
        var value = new StringBuilder(256);
        uint needed;
        return GetUserObjectInformation(GetThreadDesktop(GetCurrentThreadId()), 2, value, 512, out needed)
            && value.ToString().StartsWith("CodexQuietWorker-", StringComparison.Ordinal);
    }

    public static uint Run(string app, string arguments, string directory, uint timeoutMilliseconds)
    {
        string name = "CodexQuietWorker-" + Guid.NewGuid().ToString("N");
        IntPtr desktop = CreateDesktop(name, IntPtr.Zero, IntPtr.Zero, 0, 0xF01FF, IntPtr.Zero);
        if (desktop == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateDesktop");
        IntPtr job = IntPtr.Zero;
        IntPtr compatibilityJob = IntPtr.Zero;
        ProcessInfo process = new ProcessInfo();
        bool assigned = false;
        try {
            job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateJobObject");
            var limits = new ExtendedLimits();
            limits.basic.flags = 0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if (!SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf<ExtendedLimits>()))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "SetInformationJobObject");
            // MO2 requests CREATE_BREAKAWAY_FROM_JOB for its virtualized child.
            // Permit leaving this INNER job only. The OUTER kill-on-close job
            // prohibits breakaway and continues to own that child. Windows
            // nested-job semantics stop breakaway at the first prohibiting job.
            compatibilityJob = CreateJobObject(IntPtr.Zero, null);
            if (compatibilityJob == IntPtr.Zero)
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Create compatibility job");
            limits.basic.flags = 0x2800; // KILL_ON_JOB_CLOSE | BREAKAWAY_OK (inner only)
            if (!SetInformationJobObject(compatibilityJob, 9, ref limits, (uint)Marshal.SizeOf<ExtendedLimits>()))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Configure compatibility job");
            var startup = new Startup { cb=Marshal.SizeOf<Startup>(), desktop="WinSta0\\" + name, flags=1, show=0 };
            // Suspend until ownership is established. On failure no unowned
            // worker ever executes, and no child can escape before assignment.
            if (!CreateProcess(app, new StringBuilder("\"" + app + "\" " + arguments), IntPtr.Zero, IntPtr.Zero,
                    false, 0x08000004, IntPtr.Zero, directory, ref startup, out process))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateProcess");
            if (!AssignProcessToJobObject(job, process.process))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "AssignProcessToJobObject");
            assigned = true;
            if (!AssignProcessToJobObject(compatibilityJob, process.process))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Assign compatibility job");
            if (ResumeThread(process.thread) == uint.MaxValue)
                throw new Win32Exception(Marshal.GetLastWin32Error(), "ResumeThread");
            uint wait = WaitForSingleObject(process.process, timeoutMilliseconds);
            if (wait == 258) {
                if (!TerminateJobObject(job, 124)) throw new Win32Exception(Marshal.GetLastWin32Error(), "TerminateJobObject");
                WaitForSingleObject(process.process, 5000);
                return 124;
            }
            if (wait != 0) throw new Win32Exception(Marshal.GetLastWin32Error(), "WaitForSingleObject");
            uint code;
            if (!GetExitCodeProcess(process.process, out code))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "GetExitCodeProcess");
            return code;
        } finally {
            if (!assigned && process.process != IntPtr.Zero) TerminateProcess(process.process, 125);
            // Kill-on-close also covers any lingering descendants after the
            // main worker returned. Never enumerate or kill unrelated PIDs.
            if (job != IntPtr.Zero) CloseHandle(job);
            if (compatibilityJob != IntPtr.Zero) CloseHandle(compatibilityJob);
            if (process.thread != IntPtr.Zero) CloseHandle(process.thread);
            if (process.process != IntPtr.Zero) CloseHandle(process.process);
            CloseDesktop(desktop);
        }
    }
}
