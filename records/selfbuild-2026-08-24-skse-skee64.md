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
