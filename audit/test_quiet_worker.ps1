#requires -Version 7.0
param([switch]$Child, [string]$Evidence)
$ErrorActionPreference = 'Stop'
if ($Child) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class BreakawayProbe {
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    struct SI { public int cb; public string r,d,t; public uint x,y,w,h,cx,cy,f,flags; public short show,n; public IntPtr p,i,o,e; }
    [StructLayout(LayoutKind.Sequential)]
    struct PI { public IntPtr p,t; public uint pid,tid; }
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
    static extern bool CreateProcess(string app,StringBuilder args,IntPtr ps,IntPtr ts,bool inherit,uint flags,IntPtr env,string cwd,ref SI si,out PI pi);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    public static uint Start(string app, bool breakaway) {
        var si = new SI { cb=Marshal.SizeOf<SI>() }; PI pi;
        if (!CreateProcess(app, new StringBuilder("\""+app+"\" -NoProfile -NonInteractive -Command \"Start-Sleep -Seconds 120\""),IntPtr.Zero,IntPtr.Zero,false,
            0x08000000u | (breakaway ? 0x01000000u : 0u),IntPtr.Zero,null,ref si,out pi))
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        CloseHandle(pi.p); CloseHandle(pi.t); return pi.pid;
    }
}
'@
    Add-Type -Path (Join-Path $PSScriptRoot 'QuietWorker.cs')
    if (-not [QuietWorker]::IsPrivateWorkerDesktop()) { throw 'Child was not placed on a private desktop.' }
    $app = (Get-Process -Id $PID).Path
    $ordinary = [BreakawayProbe]::Start($app, $false)
    $detached = [BreakawayProbe]::Start($app, $true)
    # Diagnostic evidence, never a path supplied to a destructive operation.
    @($ordinary, $detached) | ConvertTo-Json | Set-Content -LiteralPath $Evidence
    exit 7
}
Add-Type -Path (Join-Path $PSScriptRoot 'QuietWorker.cs')
if ([QuietWorker]::IsPrivateWorkerDesktop()) { throw 'Test must start outside the worker desktop.' }
$app = (Get-Process -Id $PID).Path
$evidence = Join-Path ([IO.Path]::GetTempPath()) ('quiet-worker-' + [guid]::NewGuid().ToString('N') + '.json')
$argsText = '-NoProfile -NonInteractive -File "' + $PSCommandPath + '" -Child -Evidence "' + $evidence + '"'
$result = [QuietWorker]::Run($app, $argsText, $PSScriptRoot, 30000)
if ($result -ne 7) { throw "Worker exit propagation failed: $result" }
$children = Get-Content -LiteralPath $evidence | ConvertFrom-Json
Start-Sleep -Milliseconds 500
foreach ($childPid in $children) {
    if (Get-Process -Id $childPid -ErrorAction SilentlyContinue) {
        throw "Child still alive after outer job close: $childPid (evidence $evidence)"
    }
}
$result = [QuietWorker]::Run($app, '-NoProfile -NonInteractive -Command "Start-Sleep -Seconds 120"', $PSScriptRoot, 1000)
if ($result -ne 124) { throw "Timeout failed: $result" }
Write-Output "PASS: exit propagation, ordinary child cleanup, breakaway child cleanup, bounded timeout; evidence $evidence"
