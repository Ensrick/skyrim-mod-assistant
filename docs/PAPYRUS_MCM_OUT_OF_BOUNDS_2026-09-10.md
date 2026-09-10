# Exact-save Papyrus crash diagnosis — September 10

[#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) remains OPEN.
This establishes the failing memory access; it is not a campaign repair or
gameplay acceptance. No production fix was installed during this investigation.

## Evidence chain

The original Adventurer3 autosave was inspected read-only, then copied to a
fresh isolated profile for one muted QuietWorker reproduction. Original files:

- ESS SHA256 `ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
- Co-save SHA256 `E708EC7CE1B7CC384A4E676E2A52A41DCC668BA235D5FD0FD30571AF9E27A1CF`.

The new bounded SKSE inventory reports a nondynamic TrueHUD event handle
`0000FFFFFE051800` for `SKICP_configManagerReady`. The actual September9 crash
log maps saved plugin index `FE051` to missing (`255`), as it should. QuickLoot
is similarly mapped to missing. The SKSE restore implementation skips these
unresolvable registrations. A bad plugin-index remap is therefore not supported
by this evidence.

A source-built, headless FallrimTools consumer then parsed the original ESS:
7,787 script definitions, 76,568 instances, 91 active stacks, three suspended
stacks and 87 pending function messages; no reported truncation/parser failure.
Input hashes remained unchanged. Crucially:

- Saved TrueHUD_MCM instance `0000021f32e54640`, form `FE051800`, has25 variables.
- Saved `_configID` is integer18 at member index5, with matching descriptor.
- Active stack `0002c6a3` already contains `TrueHUD_MCM.OnConfigManagerReady`
  and `MCM_ConfigBase.OnConfigManagerReady`, both owned by that instance.
- A pending message for the same stack is `TrueHUD_MCM.LoadConfig`.

The saved call can resume independently of SKSE's restored event registrations.
Removing an event registration would not remove that already-saved call.

Parser source: [FallrimTools](https://github.com/mdfairch/FallrimTools), Apache-2.0,
pinned `61bb57d895f023617cb55045a4907849fd1ff566`; source-compiled with Java24.
Our consumer calls no save writer or cleaner. Its README documents dependencies
and an upstream array-label display defect that the consumer avoids. Parser
success alone does not certify compatibility with the live game.

## Actual memory capture

Game PID28776, thread4676; the same native stack reproduced after selecting
Continue, accepting the missing-content warning and explicitly choosing the
**current** load order. No removed plugin was restored. Fault occurred at
01:39:59 CDT; CrashLogger's header says01:41:22 after writing the large dump.
Engine1.7.104 MD5 `113faeb71fd8f62b26d0c8627299ab40`.

| Observed field | Value |
| --- | --- |
| Fault | SkyrimSE+09C00FC, array reference-count release |
| CodeTasklet / frame | `204B6A95AD0` / `204B6853C04` |
| Self object | `203B2CFF130` |
| Destination Variable (RDI) | `203B2CFF1B0` |
| Destination index | `(RDI - object - 0x30) / 16 = 5` |
| Self type info | `204B676D800`, name `TrueHUD_MCM` |
| Type parent / metadata pointer | Both null |
| Type state / variable count | Linked-invalid2 / zero |
| Invalid value being released | `20300000001` |

The pinned executable's variable-name lookup at1493090 independently confirms
the type layout: variable count is `(type+0x20 >>8)&0x3FF`, parent is+0x10,
and linked-valid is3. The captured type has count0 and no parent. The resumed
instruction nevertheless addresses member5 using unchecked native arithmetic
at14D59F1–14D5A03. Its failure/default path later treats unrelated memory at that
address as an array and attempts to decrement the invalid pointer.

**This proves a member access outside the receiver's runtime variable layout.**
It does not independently establish the engine heap allocation header/size or
the entire missing-type loader mechanism. The object's saved layout was25
variables; its runtime placeholder is empty. Earlier hypotheses of an index
remap, direct deterministic scalar/array restore mismatch, or a necessary
concurrent writer are no longer needed to explain this observed failure.

Fable5.1 independently traced the native resolver/caller. It corrected its own
earlier intermediate-addref and empty-variable-name interpretations. Parent
checked the actual memory and pinned executable; inference is not substituted
for the dump evidence.

## Preservation, cost and next work

The diagnostic-only CrashLogger setting and log destination were restored
byte-for-byte (SHA256 `0A38C67861A8BFAFD6640EB8D05398060ECF170621EB7FE2DF368AEB9A5C58DB`).
Cleanup was disabled for the private capture, so existing logs/dumps were not
deleted. Original ESS/co-save hashes remained unchanged. No DLL swap, mod
installation, profile load-order change, or save write was performed. The
owned controller exited0 at06:41:27UTC; that exit code means process cleanup,
**not test success**. Game is closed and the profile claim released.

One private dump is17,746,335,113 bytes (~16.5GiB), not uploaded or committed.
Keep this one root-cause artifact; do not create duplicate dumps casually.

- Dump SHA256 `33E759AC5E82217A7D51B28AF1B6049D25E03C7621F19CE6CA03A77B4D040923`.
- Crash log SHA256 `DFED9D19491A7206EC2D186D298A62061E79999CE6A1042E795C203A6784752D`.
- Read-only ESS inventory SHA256 `68CDB0775E8A37A2B64901D122B6D4C1DD4833C840C3355ADF2E0D35A74D2061`.
- Private artifacts: `records-work/mcm-dump-20260910` and
  `records-work/original-papyrus-inventory-20260910-v2.txt`.

Next: validate the resolver's existing failure contract, add a narrowly pinned
bounds check that never dereferences/defaults an invalid destination, and test
the exact copied save plus valid member accesses. No save cleaning, substitute
scripts or reinstated mods. Passing this fault is still not permission to call
the campaign healthy: missing content, currency checkpoint compatibility,
load/save/reload and sustained gameplay acceptance remain separate obligations.
