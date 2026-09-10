#requires -Version 7.0
param([Parameter(Mandatory)][int]$GamePid)
$ErrorActionPreference='Stop'
# Reuse the executable-hash guard and read-only Win32 reader; discard its
# unrelated ControlMap observation. No target allocation, write or suspension.
. (Join-Path $PSScriptRoot 'read_controlmap_snapshot.ps1') -GamePid $GamePid | Out-Null
$proc=Get-Process -Id $GamePid
$base=$proc.MainModule.BaseAddress.ToInt64()
$library=[IO.File]::ReadAllBytes('C:\Users\danjo\source\repos\mo2-instances\skyrim-se\mods\Address Library\SKSE\Plugins\versionlib-1-7-104-0.bin')
$vmSlot=[BitConverter]::ToUInt32($library,96+400475*4)
function Read-U64([long]$at) { [BitConverter]::ToInt64([ReadOnlyControlMap]::Read($GamePid,$at,8),0) }
$skyrimVM=Read-U64 ($base+$vmSlot)
$vm=Read-U64 ($skyrimVM+0x210)
$table=[ReadOnlyControlMap]::Read($GamePid,$vm+0x9320,0x30)
$capacity=[BitConverter]::ToUInt32($table,0xC)
$entries=[BitConverter]::ToInt64($table,0x28)
if($capacity -gt 65536 -or $entries -eq 0) { throw 'Invalid VM map bounds.' }
$rows=@(for($i=0;$i -lt $capacity;$i++) {
    $entry=[ReadOnlyControlMap]::Read($GamePid,$entries+24*$i,24)
    if([BitConverter]::ToInt64($entry,16) -eq 0) { continue }
    $id=[BitConverter]::ToUInt32($entry,0)
    $stack=[BitConverter]::ToInt64($entry,8)
    if($stack -eq 0) { continue }
    $bytes=[ReadOnlyControlMap]::Read($GamePid,$stack,0x88)
    [ordered]@{mapStackId=$id;stackAddress=('0x{0:X}' -f $stack);
        embeddedStackId=[BitConverter]::ToUInt32($bytes,0x80);
        legacyFirstDereference=('0x{0:X}' -f [BitConverter]::ToUInt64($bytes,0x18))}
})
[ordered]@{observedUtc=[DateTime]::UtcNow.ToString('o');processId=$GamePid;
    vmAddress=('0x{0:X}' -f $vm);capacity=$capacity;rows=$rows;
    scope='Read-only asynchronous map observations; not atomic and not a save validity test.'} | ConvertTo-Json -Depth 5
