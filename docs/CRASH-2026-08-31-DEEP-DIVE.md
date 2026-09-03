# Crash deep dive - 2026-08-31 22:42:16 (and the hangs around it)

Status: investigation only, nothing changed. Evidence-first; anything not
directly backed by an artifact is tagged [inference] or [unverified].

## Summary

Every launch since the 2026-08-30/31 install wave stalls at the same phase:
after SKSE finishes reading translation files, during the background data load
behind the main menu, before `kDataLoaded` is ever dispatched. Three launches
hung there indefinitely; one crashed there at 85s uptime with
`EXCEPTION_ACCESS_VIOLATION` inside engine code, on a background job thread,
where two adjacent registers held the ASCII bytes `r\facege` - the middle of an
`actors\character\facegendata` path - where a pointer/index pair should have
been. That is heap corruption: string data from a facegen path was written over
memory that engine code later interpreted as an address. The hang and the crash
are best read as two outcomes of the same racy corruption at the same load
phase.

## Timeline - the night of 2026-08-31 (all times CDT, UTC-5)

usvfs log filenames are UTC; PIDs from `inithooks` lines. PID 61084 matches the
crash log exactly (crash 22:42:16 minus 85.769s uptime = start 22:40:50).

| # | Start | PID | Outcome |
|---|---|---|---|
| 0 | ~21:5x | - | OAR hang at SKSE plugin load (issue #140). OAR re-parked, transaction 20260901T030136569Z = 22:01:36 CDT. |
| 1 | 22:02:52 | 13824 | Short run. [inference] This or #2 is the "1920x1080 windowed + AE upsell" launch in `docs/INI_AND_PROFILE_STATE.md` - SkyrimPrefs.ini had been reset by the game. |
| 2 | 22:03:39 | 57292 | usvfs log ends mid-BSA-mapping - killed during early load. |
| - | 22:07-22:08 | - | INI recovery: `SkyrimPrefs.ini.bak.v20260901-firstrun-reset` written 22:07:07, `settings.txt` (LocalSettings=true) 22:07:44, restored profile+global SkyrimPrefs 22:08:30. |
| 3 | 22:09:18 | 56500 | HANG. Thread dump 22:13:15 taken in this process. Memory flat at 3,682MB. Killed. |
| 4 | 22:24:14 | 60492 | HANG at the same skse64.log line. Killed. |
| 5 | 22:40:50 | 61084 | CRASH 22:42:16, EXCEPTION_ACCESS_VIOLATION, crash-2026-08-31-22-42-16.log. Translations line reached ~22:41:13; ~3 cores busy before the AV. |
| 6 | 22:47:19 | 49232 | Failed again. Plugin logs run to 22:47:46.98 (CS shader enumeration + menu icons, SkyParkour "Menu Shown"), then nothing; process gone by 22:50:18. No crash log, no dump - [inference] hung and was killed. |

All of runs 3-6 end at the identical skse64.log line:
`Reading translations from Interface\Translations\nwsFollowerFramework_ENGLISH.txt...`
(nwsFF is simply the last plugin in load order with a translation file). No
`kDataLoaded` dispatch is ever logged. The INI reset is ruled out for runs 3-6:
the restore predates them.

## Crash analysis (crash-2026-08-31-22-42-16.log)

**Faulting instruction**: `movzx r8d, byte ptr [r14+rbp*1]` at
`SkyrimSE.exe+0E128B2` (AddressLib ID 68782+0xF2). The faulting code is the
**engine's own**, not any plugin DLL - base 0x7FF70EEA0000 + 0xE128B2 falls
inside SkyrimSE.exe.

**The read that failed**: r14 (0x61665C72) + rbp (0x244232F7468) =
0x2448495D0DA - a plausible-looking but unmapped heap address.

**Register decode** (little-endian bytes as they sat in memory):

| Reg | Value | Bytes | ASCII |
|---|---|---|---|
| R14 | 0x61665C72 | 72 5C 66 61 | `r\fa` |
| RSI | 0x65676563 | 63 65 67 65 | `cege` |

Concatenated: **`r\facege`** - eight consecutive characters of
`...characte[r\facege]ndata...`, i.e. an `actors\character\facegendata\...`
path (facegeom/facetint layout). Two registers holding adjacent 4-byte slices
of one path string means the code loaded two adjacent dwords from memory that a
facegen path had been written over. Classic overwrite/use-after-free signature;
the string's *owner* is not identifiable from the crash alone - heap reuse
means any subsystem building such paths (or an archive name table containing
them) could have supplied the bytes.

**Thread identity**: crash thread 54704 is NOT the main thread. Its stack roots
in a thread-start (KERNEL32/ntdll) into engine thread code (IDs 68445 ->
35423 -> 39039 -> 68617 -> 68782 [names unverified - no 1.7.104 name map]).
On its stack: `JobListManager::ServingThread*` (RSP+48) with
`State[0]=State[1]=kLoadScreen` - confirming the load-screen phase - and
`BSWin32KeyboardDevice*` at RSP+0/RBX, with rbp pointing *inside* that object
(RBX+0x268). So an engine job/worker thread was iterating byte-by-byte over
data addressed relative to a live keyboard-device object, using a
pointer/index pair that had been stomped with facegen-path text.
[inference] The keyboard device may be involved (input stack) or may merely be
the heap neighbor of the corrupted allocation - the crash log cannot
distinguish.

**Environment facts**: gameoverlayrenderer64.dll WAS loaded (the per-game
overlay disable did not take). 28 SKSE DLLs loaded; no OpenAnimationReplacer,
no CRD, no Light Placer (parks held). Memory: 3.9GB working set, 25GB free -
not OOM. usvfs_x64 active (MO2 VFS).

## Thread dump analysis (threaddump-2026-08-31-22-13-15.log, run 3)

Caveat: the dump captured **17 of 127 threads** - the data-loading thread is
almost certainly in the uncaptured 110, so its stack (the actual stall
signature) was never observed.

- **Main thread**: pumping window messages - win32u/USER32 with
  gameoverlayrenderer64 hook frames interleaved. This proves the main thread
  was *alive* and pumping (consistent with a visible menu, a modal dialog, or
  an ordinary pump with overlay hooks in the chain), not that the overlay was
  the blocker.
- **6 engine job threads**: idle waits (IDs 69617/69620 region).
- **10 CommunityShaders BS::thread_pool workers**: idle, parked in
  ShaderCache waits.
- Nothing in the captured subset was executing load work; memory flat at
  3,682MB says load progress had stopped.

## Change diff since last-good (2026-08-29 17:23, 21 SKSE DLLs)

Now 28 DLLs load. New or replaced native code since last-good
(records/installed-mods.json):

| DLL | Installed | Load-phase behavior / plausibility vs evidence |
|---|---|---|
| hdtsmp64 (FSMP 4.1.1) + Vanilla Hair Remake SMP + SMP NPCs plugin | 08-30 21:58-22:27 | **High.** Physics framework touching hair/head-part meshes; NPC head parts live under facegendata; heavy native init. |
| CommunityShaders AIO 1.8, 1.7.99 source build | 08-30 17:17 | **High.** Self-built for a different runtime line than 1.7.104; spawns its own thread pool; compiles shaders during exactly this phase (the ~3 busy cores in run 5). |
| SSEDisplayTweaks official 0.5.25 + LockCursor=true flip | 08-30 02:31 / flip 08-31 | **High.** Hooks window proc, DirectInput, present chain - the only new code squarely on the keyboard/window path the crash gestures at. |
| SkyParkourNG 3.6.3 | 08-30 23:24 | Medium. Input-adjacent (parkour keys), menu creation observed at load. |
| SimpleDualSheath 1.5.9 | 08-30 16:03 | Medium-low. Five engine patches at init (log clean); node attach work is later, in-game. |
| MCMHelper 1.6.3 | 08-30 15:43 | Low. Config scan at load; log clean (0 setting files anomaly noted). |
| SoundRecordDistributor 1.5.3 | 08-30 15:38 | Low. _SRD parsing at DataLoaded - which is never reached. |
| QuickLootIE Ensrick 1.7.99 rebuild | 08-30 17:17 | Low-medium. Input sink registration; rebuilt binary. |

Content wave (not native code, but supplies exactly the string seen in the
crash): 3DNPC/Interesting NPCs 4.54, Cutting Room Floor, Inigo, Varinia, VHR
SMP NPCs - thousands of new `facegendata` entries in BSA name tables and the
usvfs VFS tree (~35 mods, 63 regular + 248 light plugins now). Also tonight:
INI reset+restore (ruled out for runs 3-6), OAR/CRD/Light Placer parks (held -
absent from the crash module list).

## Hypotheses, ranked

1. **Racy heap corruption during background data load, facegen-path string
   written over live engine data** - hang when the stomp wedges the loader,
   AV when a worker dereferences it. Fits: same phase every time, 3 hangs +
   1 AV + 1 silent death; `r\facege` in registers; engine-code fault.
   Culprit unknown; FSMP+VHR, CS source build, and SSEDT are the new native
   code with the right footprints.
   *Test*: park the 8 new/replaced DLLs (table above) in one launch - see
   Recommendation.
2. **SSEDT (official build + LockCursor flip) x Steam overlay input-stack
   interaction** - both hook the window/input path; crash thread carries a
   BSWin32KeyboardDevice*; overlay disable did not take. Weakened by: overlay
   was present during the 08-29 good launches too [inference - overlay is
   default-on], so it can only be an interaction term, not a solo cause.
   *Test*: revert LockCursor + park SSEDT only (second-round bisect); verify
   overlay state in-process, not via Steam UI.
3. **CS 1.7.99-source-build on 1.7.104 runtime misbehaving during its
   load-phase shader work** - version-line mismatch for self-built native
   code; its workers own the busy cores at the stall.
   *Test*: park CS alone (second-round bisect; falls out of test 1's branch).
4. **Content-side (3DNPC-scale BSA/VFS growth) triggering a latent engine or
   usvfs bug** - the string source is definitely content-shaped; doubled VFS
   tree. Lower: content alone rarely AVs the loader this early, and plugins
   loaded fine to 311.
   *Test*: only if the DLL-park launch still fails - disable the 08-30/31
   content plugins as a block.

## Follow-up evidence round (same night, from the #141 watchdog work)

Three claims arrived after the first draft; each was checked against artifacts.

**1. "The 22:13 hang is a pure WAIT, not slow work" - CONFIRMED, with a
caveat.** `audit/threaddump.py` walked all 17 captured stacks: none executing.
Main thread in a win32u message wait (overlay frames are hook wrappers on the
pump), CS pool parked, engine pools parked. Folded in: the hang is a wait that
never completes, not slow loading. Caveat unchanged: 110 of 127 threads -
including the loader thread - were never captured, so blocked-on-lock vs
waiting-for-an-event cannot be distinguished. Note also the runs differ: the
22:09 dump run showed nothing computing, while the 22:40 crash run burned ~3
cores at the same phase. Both end states are compatible with the corruption
hypothesis (what got stomped differs per run).

**2. "A session at 22:44 reached the menu and exited normally" - NOT SUPPORTED
by any artifact; treat as misreport.** The full usvfs listing has exactly six
logs (22:02:52 through 22:47:19), nothing between 22:42:17 (crash-run log
close) and 22:47:19. Every game launch tonight went through MO2
(`moshortcut://:SKSE` per mo_interface.log), so a session without a usvfs log
would be a non-MO2 launch - and there is no trace of one: the game rewrites
SkyrimPrefs on clean exit, yet profile `skyrimprefs.ini` mtime stayed 22:08:30
all night; all SKSE plugin logs start 22:47:22 (run 6). Until someone produces
the 22:44 artifact, the failure is 4-for-4 post-INI-restore, not intermittent.
(Bonus timeline fix: MO2 saved its lists and exited at 22:49:18, so run 6
lived ~2 minutes - same shape as the other hangs.)

**3. "Stale 92-plugin `%LOCALAPPDATA%\Skyrim Special Edition\Plugins.txt`" -
REFUTED for the failing runs by the crash log itself.** The file is real: 92
active entries, mtime 2026-08-28 14:05:33, untouched since. But the crash
log's in-engine enumeration shows 311 plugins loaded = 80 official (5 base +
CC + _ResourcePack) + exactly 231 modded - the profile list to the plugin,
including 08-30/31 content (3DNPC, ACMOS, Freak's Floral, Landscape and Water
Fixes) that a list seeded 08-28 could not contain. MO2 2.5.2/usvfs 0.5.7.2 DID
virtualize plugins.txt for these launches, reads and writes both (profile
plugins.txt rewritten 22:49:18 at MO2 exit; the LOCALAPPDATA copy is a stale
husk). `launch_skyrim.ps1` seeding remains belt-and-suspenders for non-MO2
launch paths, but the engine was not running a 92-plugin list tonight.

**OAR/CRD addendum**: their removal did not move the stall line - identical
before and after the parks - so they are innocent of the hang (still real init
failures in their own right per #140).

## Ruled out by evidence

- **OAR / CRD / Light Placer**: parked before run 1; absent from crash module
  list.
- **INI reset as cause of runs 3-6**: restore completed 22:08:30, before all
  of them; run 6's SSEDT log requests 3840x2160 borderless correctly.
- **Plugin-load / SKSE-gate failure shape** (#140's shape): all 28 DLLs loaded
  and initialized cleanly in every run 3-6.
- **OOM**: 3.9GB WS, 25GB physical free.
- **A plugin DLL as the *faulting* code**: the AV is inside SkyrimSE.exe.
  (Does not rule plugins out as the *corrupter*.)
- **Stale LOCALAPPDATA Plugins.txt (92 entries)**: refuted by the crash log's
  own 311-plugin enumeration - see follow-up evidence item 3.
- **Intermittency**: no artifact supports the reported 22:44 clean session -
  see follow-up evidence item 2. 4-for-4 failures post-INI-restore.

## Recommendation - the single next test

**One launch with the eight new/replaced SKSE DLLs parked** (hdtsmp64+VHR SMP
configs, CommunityShaders AIO, SSEDisplayTweaks [restoring the pre-08-30
custom build and LockCursor state], SkyParkourNG, SimpleDualSheath, MCMHelper,
SoundRecordDistributor, QuickLootIE rebuild), content plugins untouched.

Why this split: it cleanly halves the space along the new-native-code axis.
Clean launch -> corruption lives in the DLL wave; binary-search it in 2-3 more
launches (park half). Still hangs/crashes -> every new DLL is exonerated at
once and attention narrows to content volume, usvfs, or overlay interaction -
each with its own cheap follow-up. No other single launch eliminates as much.

If a second thread dump gets taken during any future hang: capture ALL
threads, not the 17-thread subset - the loader thread's stack is the missing
stall signature.

## Artifacts

- `C:\Users\danjo\Documents\My Games\Skyrim Special Edition\SKSE\crash-2026-08-31-22-42-16.log`
- `...\SKSE\threaddump-2026-08-31-22-13-15.log`
- `...\SKSE\skse64.log` (run 6; runs 3-5 overwritten, identical last line per observation)
- `C:\Users\danjo\source\repos\mo2-instances\skyrim-se\logs\usvfs-2026-09-01_03-*.log` (UTC names; PID 61084 = crash run)
- `records/installed-mods.json` (installedUtc), `docs/INI_AND_PROFILE_STATE.md`, issues #140, #98, #103
