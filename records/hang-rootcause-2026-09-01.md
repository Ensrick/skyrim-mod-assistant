# Data-load hang root cause - truncated ccvsvsse004-beafarmer.bsa (#142)

- when: 2026-09-01 ~07:40-08:00
- agent: phase-2 machine/VFS investigation
- verdict: **root cause found and mechanically proven; zero launches spent on
  diagnosis** (a live hang specimen, pid 60524, launched 07:35:51 by a prior
  session, was captured in place)

## The mechanism

`Data\ccvsvsse004-beafarmer.bsa` (vanilla-side Creation Club archive, real
Steam path, OUTSIDE the MO2 VFS) is **truncated on disk**: 4,194,256 bytes
(= 4MB - 48). The engine's archive tables expect more data than exists. During
background data load the BSResource IO thread seeks past EOF and calls
ReadFile in an unbounded retry loop; `kDataLoaded` never fires.

Proof chain, all from outside the process (audit/spindump.py, new):

1. Exactly 3 threads burn ~85-100%/core each (matches every hang record):
   - **tid 50788** (engine IO worker, entry `SkyrimSE.exe+0xCE4290`):
     40/40 RIP samples at `ntdll!ZwReadFile+0x14`, rsp spread 0 (tight loop).
     Stack: `KERNELBASE+0x22B1D (ReadFile)` <- `SkyrimSE.exe+0xEC05C5` <-
     `+0xED610A` <- `+0xEC0699` <- `+0xED61E9` <- `+0xECC031/0xECC66F/0xECC878`
     <- `+0xEC6D61` <- `+0x9CEDFC` (BSResource archive IO chain; EngineFixes.dll
     frames deeper on the stack at +0x360/+0x3B0 are likely stale).
   - **tid 49424** (engine worker): poll loop through `ZwDelayExecution`
     (Sleep) + `RtlQueryPerformanceCounter` + `SkyrimSE.exe+0x14EC696` -
     waiting for the load that never completes.
   - **tid 46676** (main thread, entry `SkyrimSE.exe+0x38EF310`): busy
     PeekMessage pump (`NtUserPeekMessage+0x14`, 39/40 samples), Steam overlay
     hook frames present but only as pass-through wrappers.
2. The wedged thread's file handle **0x85C** resolves (DuplicateHandle +
   GetFinalPathNameByHandle) to
   `C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\ccvsvsse004-beafarmer.bsa`.
3. The handle's shared file position is pinned at **4,739,072 - 544,816 bytes
   PAST the 4,194,256-byte EOF** - sampled 6x over 1.8s, never moves. ReadFile
   at/past EOF returns 0 bytes; the engine retries forever.
4. The file reads cleanly end-to-end from disk (no device error): the damage
   is logical truncation, not hardware.

Raw captures: `records/tool-runs/spindump-20260901-quiescent.txt`,
`records/tool-runs/spindump-20260901-handle.txt`, full minidump (all 66-70
threads, stacks+contexts)
`Documents\My Games\Skyrim Special Edition\SKSE\minidump-20260901-074040.dmp`.

## How the file got truncated - the timeline that explains everything

Steam `content_log.txt` + file mtimes:

| when (08-31) | event |
|---|---|
| 22:02:51-22:03:00 | run 1 - reset/default INI, **reached the main menu** (user saw the AE upsell; `bUpsellOwned=0` = first-run CC state) |
| 22:03:39 | run 2 starts |
| 22:04:30 | run 2 killed - Steam state `App Running,Terminating` |
| **22:04:31-53** | `ccbgssse069-contest.bsa/esl`, `ccbgssse068-bloodfall.bsa/esl` rewritten; `ccvsvsse004-beafarmer.bsa` rewritten LAST and left at exactly 4MB-48 (its .esl still dated 1/2025 - the update never finished) |
| 22:04:56 | Steam state back to `Fully Installed` - Steam considers nothing wrong |
| 22:07-22:08 | INI restore (the red herring: every later hang postdates it by coincidence) |
| 22:09:18+ | every subsequent launch hangs at the translations line, 3 threads spinning - 11+ consecutive failures across 91-231 plugins |

[inference] The first-run CC state (bUpsellOwned=0) triggered re-acquisition
of free CC content; the 22:04:30 kill (or the launcher script's Steam cycling)
interrupted the write mid-file. Whichever process held the pen, the artifact
is the same: a half-written official BSA that no mod park could ever touch -
which is exactly why the phase-1 bisect exonerated all 135 parked mods while
the hang stayed byte-identical (plateau 1810-1879MB regardless of content).

## Suspects cleared (phase A, zero launches)

- Windows: no OS KBs after 08-28 (good launch 08-29 17:23); only daily
  Defender signature updates (same cadence before/after the boundary).
- GPU: driver 32.0.16.1088 dated 7/21/2026, driver store untouched since
  8/10; NVIDIA DXCache continuous since 2024 (no invalidation).
- Steam client: updater built Aug 3 2026, no client update in the window.
- usvfs/MO2: not the blocker - the wedged file is on the real path, and the
  spin is engine retry logic, not VFS code.
- SkyrimPrefs restore: run 1 reached the menu on the reset INI *before* the
  CC rewrite, and the file was damaged before the first hang - the INI delta
  never needed a test launch.

## Fix + confirmation

Steam validate of app 489830 (`steam://validate/489830`) to restore the three
rewritten CC files, INI verification after (per docs/INI_AND_PROFILE_STATE.md
- validation is on the "assume INIs touched" list), then ONE confirmation
launch via `audit/launch_verify.py` expecting main menu <60s + save load.

Also check `ccbgssse068-bloodfall.*` / `ccbgssse069-contest.*` post-validate:
they were written in the same interrupted window and finished only by luck.
