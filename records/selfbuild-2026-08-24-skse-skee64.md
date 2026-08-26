# Self-build: SKSE master + RaceMenu skee64 for 1.7.99 (2026-08-24)

**Why:** runtime 1.7.99 broke the SKSE stack; Expired committed skee64's 1.7.99
port (SKSE64Plugins@9ebcb73, Aug 23) and his PC-offset fixes into ianpatt/skse64
master (6498c52), but no releases exist yet. User directive: prefer open source,
research first, share fixes upstream after verified success.

**Built** (VS2022 v143, x64):
- skse64_loader.exe + skse64_1_7_99.dll from ianpatt/skse64@14db212
  (CURRENT_RELEASE_RUNTIME = 1_7_99, SKSE 2.3.0 + post-release fixes)
- skee64.dll "Release Steam" from expired6978/SKSE64Plugins@9ebcb73
  + deps: ianpatt/common, vendored jsoncpp/spdlog, microsoft/DirectXTex
  (CMake, /MT) staged into the layout the vcxproj expects

**Local shims (no upstream source semantics changed):** skee_build.sln config
bridge; build_shim.props (include roots, skse64 objs linked into skee64, winmm,
loader crypt32/wintrust); DirectXTex via CMake because its vcxproj shader step
needs SDK env vars vcvars didn't provide (fxc via LegacyShaderCompiler).

**Source patches (upstream candidates, records/upstream-patches/):**
1. skee64/ILogger.h: SanitizeArg degrades typed pointers to const void* before
   fmt::sprintf (fmt v9 static-asserts on non-void pointers; triggered via
   skse64's ScaleformState.h logging wchar_t*/IMenu* through skee's template
   _MESSAGE). -> for Expired.
2. skse64/ScaleformExtendedData.cpp: static round() (global collided with UCRT
   at plugin link). skse64_loader.vcxproj: add SigCheck.cpp (in repo, missing
   from project) + needs crypt32/wintrust. -> for ianpatt.

**Staged with backups:** game root skse64_loader.exe + skse64_1_7_99.dll
(.bak.v2.3.0-nexus beside them); mods/RaceMenu skee64.dll
(.bak.v0.4.20-for-1.6.1170). Revert = restore backups, disable RaceMenu.

**Known caveats to test in-game:** Bethesda NIF regression (NiTriShape without
NiTriShapeData crashes engine; affects overlay nifs - Expired's kAlwaysDraw
change may or may not be the workaround). Cosave load: 173617 exists if needed.
JContainers + PapyrusUtil still dead (Proteus/NFF storage) - watcher armed.
Official releases supersede these builds on arrival (plugin_watch).

**Upstream sharing:** after user's in-game verification - PR/report to Expired
(ILogger patch + "9ebcb73 pairing builds and runs on 1.7.99") and ianpatt
(round/static + loader vcxproj); clean CRLF churn from diffs first.

## Addendum (same day, after first launch attempt)

First staged loader popped SKSE's own "newer version than supported" gate:
`sheets/Runtime.props` in ianpatt's repo hardcodes
`RUNTIME_VERSION=0x01061430` (1.6.323) for all solution builds - the release
process overrides it externally, the sln sheet rotted. Bumped to 0x01070630
(1.7.99) + Common.props TargetName `_1_6_323` -> `_1_7_99`; rebuilt dll,
loader, and relinked skee64 (it statically links skse64 objs compiled with
that macro). Restaged: loader 88008075, skse64_1_7_99.dll c13e0569,
skee64.dll b73e9a99. Added to the ianpatt upstream report: sln version sheet
needs bumping at release time (or derive RUNTIME_VERSION from skse_version.h).

## Addendum 2 (Aug 25): loader swap-back

Self-built master loader passed the version gate after the props fix but hit
"something has started the runtime outside of skse64_loader's control" (Steam
re-spawn race) and the chain exited - master's launch flow includes WIP
sig-check/date-range logic the release does not exercise. Resolution: restored
the RELEASED 2.3.0 loader (accepts 1.7.99, battle-tested launch flow) while
keeping the self-built master runtime dll c13e0569 (the piece carrying
Expired's fixes). Self-built loader preserved as
skse64_loader.exe.selfbuilt-master. For the ianpatt report, not worth
debugging further locally.

## Addendum 3 (Aug 25): SKSE runtime reverted to Nexus pair

Pairing matrix, empirically established:
- release loader + self-built dll: REJECTED ("Bad SKSE DLL" - release loader
  Authenticode-verifies the dll; ours is unsigned by design)
- self-built loader + self-built dll: injects, then game process dies pre-init
  (no skse64.log; ResumeThread anomaly; master carries WIP addr-lib
  declaration logic never shipped in a release) - steam_appid.txt did not help
- release loader + release dll: the Aug-23 known-good launch config -> RESTORED

Kept: self-built skee64.dll (its header fixes describe GAME structs, valid on
any SKSE), Engine Fixes 7.0.21 official, all wave updates. Both self-built
SKSE binaries preserved as *.selfbuilt-master. Consequence: ianpatt's release
dll still has the Papyrus natives Expired called broken - IF showracemenu
crashes, RaceMenu re-parks until SKSE's next official release (page active
Aug 20, author committing daily; watcher armed). Game itself is playable for
visual shakedown either way.

## Addendum 4 (Aug 25 overnight): STABLE LAUNCH ACHIEVED

Closed-loop launch session (user authorized autonomous launching). Root causes
found and fixed, in order:
1. Popup-then-abort class: stale CommonLib DLLs pop format-5 box, abort on
   dismiss (= every "ucrtbase 0xc0000409 crash"). Popup spammers found by the
   watchdog: Skill Uncapper (9 boxes/8s), SSE Display Tweaks. All stale DLL
   mods PARKED: Bug Fixes SSE, Scrambled Bugs, TNG, Skill Uncapper, Display
   Tweaks, JContainers, PapyrusUtil (SKSE's disabled-plugin summary box was
   the "plugin failed, recommends exiting" popup).
2. MO2 FLUSHES modlist.txt from memory on exit - edits made while
   ModOrganizer.exe runs get silently reverted. Protocol: kill MO2 BEFORE
   editing profile files. (Also: two self-inflicted PowerShell file
   corruptions - modlist newlines, plugins.txt stars. PS file edits banned
   from this pipeline; python only.)
3. THE crash: engine NIF-parser regression (Expired's exact description) -
   AV at SkyrimSE.exe+0EDBAB6 parsing overlay NiTriShapes ("Body [Ovly]",
   "Feet [Ovly]") during SUR player build. skee64's bEnableOverlays=0 did NOT
   stop it (ungated InstallOverlay path - upstream bug for Expired). Fixed in
   OUR skee64 build: choke-point guard at OverlayInterface::InstallOverlay.
   Two symbolicated crash logs on file (crash-2026-08-25-00-50-55/00-56-11).
4. Steam launch chain needs no stale MO2 holding the lock; a Steam cycle
   cleared a stuck rungameid state.

FINAL: VERDICT STABLE - 156s uptime, 1.9GB, zero popups, 58 plugins enabled,
7 DLLs loaded (ConsoleUtil, CrashLogger, EngineFixes 7.0.21, KID, po3 Tweaks,
skee64 self-built+overlay-guard, Underwear 1.3.1). Game closed per user
instruction. Popup watchdog: scratchpad popup_watchdog.ps1 (WM_CLOSE mode).

## Addendum 5 (Aug 25 evening): REBUILD-FORWARD PROGRAM (user directive)

USER RULES (permanent): never downgrade the game version; REBUILD OR REMAKE
any mod not updated for the latest runtime; no idle waiting. The staged
1.6.1170 downgrade was cancelled and its watcher killed.

Launch-blocker discovered by screenshot: user was playing Octopath Traveler -
Steam refuses a second game; all "no process appeared" launches during that
window were Steam refusals, not failures. No launch attempts while Steam is
occupied.

Rebuild queue (sources cloned to repos/_rebuild_*): MCM-Helper (Exit-9B; in
progress - CommonLibSSE submodule retargeted to alandtse/CommonLibSSE-NG
6.7.0, vcpkg baseline pinned ddd0023b, NG deps added), SSEDisplayTweaks
(SlavicPotato), KernalsEgg/SKSE64Plugins (Bug Fixes + Scrambled Bugs),
TheNewGentleman (ModiLogist), OpenAnimationReplacer (ersh1), JContainers
(ryobg), po3 suite (SPID/BOS/PapyrusExtender/LightPlacer - author actively
shipping, ours is insurance). Skill Uncapper = Rust rewrite
(TheDreadedAndy/SkyrimAEUncapper-Rust, needs cargo). PapyrusUtil/EVLaS: no
repo linked on page - source hunt pending. SKSE master dll init-AV diagnosis
pending a free Steam slot (WER LocalDumps armed, RVA symbolication tooling
ready in scratchpad/symbolicate.py).

## Addendum 5 (2026-08-26): CMake rebuild WORKS - .sln path was the whole bug

Root causes found by the 2026-08-26 audit (workflow wf_35880592-44a):
- The .sln path never passed skse64/skse64.def to the linker: StartSKSE was
  not exported and LTCG dead-stripped the runtime (255,488 B dll, 1 export).
  The loader's inject shellcode calls export ORDINAL 1 unconditionally; with
  the .def absent, ordinal 1 was the SKSECore_Version DATA object, so the
  remote thread executed .data -> DEP AV 0xc0000005 at +0x3ab08, pre-init.
- The official Nexus 2.3.0 dll was compiled with pre-1.7.99 struct offsets:
  1.7.99 inserted BSTEventSink<BSSystemEvent> into PlayerCharacter at 0x2D0
  (tintMasks 0xB18->0xB20 etc.). papyrusGame::GetNthTintMaskColor indexed the
  stale-offset NULL array -> the +0x420D0 Papyrus crash. Fixed upstream in
  master commit 6498c52 (unreleased).

Rebuilt via ianpatt's own CI recipe (VS2022 + CMake, sibling common repo,
CMAKE_INSTALL_PREFIX=repos/extern). Acceptance gates: dll ~1.2 MB, exports
exactly StartSKSE @1 + SKSECore_Version @2 - PASSED.

Additional source patch (popup doctrine, user mandate 2026-08-26: everything
logs, nothing pops): PluginManager::ReportPluginErrors +
UpdateAddressLibraryPrompt + PrintLoaderError are log-only, no MessageBox,
no TerminateProcess. Maintained on fork github.com/Ensrick/skse64 branch
ensrick/headless-log-only (commit 9e9f9fa); skee64 patches (ILogger fmt +
InstallOverlay ini guard) on github.com/Ensrick/SKSE64Plugins branch
ensrick/1.7.99-headless (commit 748ca80).

DEPLOYED 2026-08-26 ~00:33: game root skse64_loader.exe FE4AD0F0 (246,784 B) +
skse64_1_7_99.dll 7536E8DD (1,201,152 B) + matching PDB; official 2.3.0 pair
preserved as .bak.v2.3.0-nexus. First launch through the full Steam->MO2->SKSE
chain: STABLE (83s+/2.2GB, 11 plugins checked, 0 refused, no popups, no crash
log). The prior Papyrus-crash trigger (gameplay scripts) still needs the user's
in-game New Game pass for final confirmation.
