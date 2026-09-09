#requires -Version 7.0
param([Parameter(Mandatory)][int]$GamePid)
$ErrorActionPreference = 'Stop'
$gameProcess = Get-Process -Id $GamePid
$module = $gameProcess.MainModule
$expectedExe = 'C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\SkyrimSE.exe'
if ($module.FileName -ne $expectedExe) { throw 'Not the reviewed Skyrim executable.' }
if ((Get-FileHash -LiteralPath $expectedExe -Algorithm MD5).Hash -ne '113FAEB71FD8F62B26D0C8627299AB40') {
    throw 'Executable changed; rederive the offsets before reading.'
}
Add-Type @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class ReadOnlyControlMap {
    [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] bytes,UIntPtr length,out UIntPtr read);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    public static byte[] Read(int pid, long address, int size) {
        if (size < 1 || size > 1024) throw new ArgumentOutOfRangeException(nameof(size));
        IntPtr p=OpenProcess(0x1010,false,pid); // QUERY_LIMITED_INFORMATION | VM_READ, never VM_WRITE/VM_OPERATION
        if(p==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        try { var data=new byte[size]; UIntPtr read;
            if(!ReadProcessMemory(p,new IntPtr(address),data,(UIntPtr)size,out read) || read.ToUInt64()!=(ulong)size)
                throw new Win32Exception(Marshal.GetLastWin32Error());
            return data;
        } finally { CloseHandle(p); }
    }
}
'@
$slot = $module.BaseAddress.ToInt64() + 0x31A5690
$address = [BitConverter]::ToInt64([ReadOnlyControlMap]::Read($GamePid,$slot,8),0)
if ($address -eq 0) { throw 'ControlMap not initialized.' }
$bytes = [ReadOnlyControlMap]::Read($GamePid,$address,0x130)
$data = [BitConverter]::ToInt64($bytes,0x108)
$capacity = [BitConverter]::ToUInt32($bytes,0x110)
$count = [BitConverter]::ToUInt32($bytes,0x118)
$flags = [BitConverter]::ToUInt32($bytes,0x120)
$contexts = @()
$bounded = $count -le $capacity -and $count -le 128 -and ($count -eq 0 -or $data -ne 0)
if ($bounded -and $count) {
    $items = [ReadOnlyControlMap]::Read($GamePid,$data,4*$count)
    $contexts = @(for($i=0;$i -lt $count;$i++) { [BitConverter]::ToInt32($items,4*$i) })
}
$after = [ReadOnlyControlMap]::Read($GamePid,$address+0x108,0x20)
$consistent = [Convert]::ToHexString($bytes[0x108..0x127]) -eq [Convert]::ToHexString($after)
[ordered]@{
    observedUtc=[DateTime]::UtcNow.ToString('o'); processId=$GamePid;
    processStartedUtc=$gameProcess.StartTime.ToUniversalTime().ToString('o');
    controlMapAddress=('0x{0:X}' -f $address); contextDataAddress=('0x{0:X}' -f $data);
    contextCount=$count; contextCapacity=$capacity; bounded=$bounded;
    contexts=$contexts; enabledControls=('0x{0:X}' -f $flags);
    wheelZoomEnabled=([bool]($flags -band 512)); headerStableAcrossRead=$consistent;
    scope='Read-only asynchronous snapshot, not an atomic engine-state or writer-attribution proof.'
} | ConvertTo-Json -Depth 4
