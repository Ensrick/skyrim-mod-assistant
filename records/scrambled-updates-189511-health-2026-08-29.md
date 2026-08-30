# Scrambled Updates 1.1.0 health audit

Read-only audit completed 2026-08-29 for Skyrim `1.7.104`, SKSE `2.3.1`,
Address Library format 5, disabled Scrambled Bugs `21`, and active Engine Fixes
`7.0.21`. Nothing was installed or enabled, Keep/Skip was not changed, and no
game or visible application was launched.

## Decision

**Hold the current Nexus file.** The idea is sound and no public mod supersedes
it, but Nexus `1.1.0` does not work on this exact stack. SKSE `2.3.1` rejects
all three 2023 target DLLs before Scrambled Updates' preload callback can patch
them. The current GitHub main fixes a separate unsafe-build-identification bug,
and an open branch addresses the SKSE `2.3.1` gate, but neither is released.
The open solution also edits vendor DLLs on disk and raises an in-game restart
message, so it is not acceptable unchanged under this project's immutable-vendor
and no-popup policies.

Reclassify to **Keep** only after either an upstream release or our owned
GPL-compatible bridge passes the silent acceptance plan below without modifying
the three vendor installations.

## Official file and source provenance

- Nexus: [Scrambled Updates](https://www.nexusmods.com/skyrimspecialedition/mods/189511)
- Author: doodlum
- Current file: `794612`, version `1.1.0`, uploaded 2026-08-24
- Archive SHA-256:
  `2fc7a7f05372134978336ee920009c04606982181cabc9ce6c84d5e4c827f88f`
- Shipped DLL SHA-256:
  `00327880f72c2fe946d79a895e8d215ec9e6c4a29543be5158c04f1c64aa444d`
- Payload: `ScrambledUpdates.dll`, its PDB, GPL `COPYING`, and the project's
  linking exceptions; no plugin, scripts, configuration, or assets.
- Source: [doodlum/ScrambledUpdates](https://github.com/doodlum/ScrambledUpdates),
  GPL-3.0-or-later with explicit modding-library linking exceptions.

The source repository has no tag, GitHub release, or CI workflow tying the
Nexus artifact to a commit. Its vcpkg baseline is pinned, but the required
CommonLibSSE-NG prebuilt bundle is not pinned by release, commit, or hash. That
prevents a bit-reproducible rebuild from the repository alone.

The shipped DLL nevertheless maps cleanly to source commit
`f3bdab635ed32eebb3656549ffa3031803bfdfb6` (`1.1.0`): it exports the same four
SKSE symbols, declares version `1.1.0`, contains the `plugin version ... expected`
guard and the same module/error strings, and its shipped PDB names the same
source files. That exact commit compiled successfully in the audit environment.
The local binary is not byte-identical because the Nexus file used linker
`14.51` while the available audit toolchain is MSVC `19.44`, and the unpinned
CommonLib bundle also differs.

Current main is commit `69c62e68455d485bb1cf47310bd7c4d460220613`, internally
versioned `1.1.1`. It compiled successfully and replaces the weak plugin-version
guard with exact CodeView build-GUID matching. The open
[SKSE 2.3.1 compatibility PR #4](https://github.com/doodlum/ScrambledUpdates/pull/4),
commit `a81486ac20230210eb61d827a836a05291a89f28`, also compiled successfully.
No corresponding Nexus `1.1.1+` file exists as of this audit.

## What the preloader does

SKSE scans all plugin DLL resources first, then invokes `SKSEPlugin_Preload`
for accepted preload-capable plugins before invoking normal plugin loads.
Scrambled Updates uses that early phase to:

1. read the current format-5 Address Library through CommonLibSSE-NG;
2. register `LdrRegisterDllNotification`;
3. detect each target DLL as Windows maps it, before its normal initialization;
4. replace the target's old `AddressLibrary::Header::Read` and
   `AddressLibrary::Read` functions with format-5-aware implementations; and
5. correct three Scrambled Bugs instructions for the eight-byte
   `PlayerCharacter` layout shift introduced in runtime `1.7.99`.

The v21 instructions were verified directly in the shipped DLL:

| RVA | Shipped operand | Patched operand | Purpose |
|---|---:|---:|---|
| `0x0060ED` | `0xBE3` | `0xBEB` | enchanted-weapon charge read |
| `0x0060FF` | `0xBE3` | `0xBEB` | enchanted-weapon charge write |
| `0x00690E` | `0xB00` | `0xB08` | difficulty-state read |

This is a precise compatibility shim, not a replacement implementation of
Scrambled Bugs. The DLL notification remains registered for the process life;
after all three targets are patched its residual cost is trivial. If optional
targets are absent, it continues checking for them whenever another DLL loads,
also a very small cost.

## Two release-blocking defects

### 1. Nexus 1.1.0 is unsafe against rebuilt targets

Nexus `1.1.0` accepts only the exported plugin version (`21`, `1`, or `1`) before
writing absolute jumps to hard-coded RVAs. A rebuilt DLL can retain that version
while moving the target functions, which would make the shim overwrite unrelated
code. Current main `1.1.1` fixes this by checking the exact PDB/CodeView GUID:

| Target | Required CodeView GUID |
|---|---|
| `ScrambledBugs.dll` | `72FF555D-9E17-4A7B-9A64-50DC1030A5E4` |
| `ScriptEffectArchetypeCrashFix.dll` | `76879527-999C-4CA2-BF31-0643B8A4F22A` |
| `VendorRespawnFix.dll` | `1EF99E87-85DB-47B3-8D02-CC447AD34F61` |

All three official AE DLLs match those GUIDs. This fix is essential and is not
present in current Nexus `1.1.0`.

### 2. SKSE 2.3.1 rejects the targets before preload can help

SKSE `2.3.1` checks plugin compatibility while scanning the directory, before
any preload callback executes. For an old DLL that claims post-AE Address
Library independence and was linked before 2025-05-26, it requires the new
`AddressLibraryV5` bit in `versionIndependenceEx`.

All three target DLLs were linked on 2023-03-10 and omit that bit:

| Target | `versionIndependence` | `versionIndependenceEx` | SKSE 2.3.1 result |
|---|---:|---:|---|
| Scrambled Bugs 21 | `0x5` | `0x0` | rejected |
| Script Effect Archetype Crash Fix 1 AE | `0x1` | `0x1` | rejected |
| Vendor Respawn Fix 1 AE | `0x5` | `0x0` | rejected |

Rejected plugins are never added to SKSE's plugin list and are never mapped for
normal load, so the DLL notification has nothing to patch. Nexus `1.1.0` then
reaches `kDataLoaded`, concludes that none of its targets are installed, and
shows the misleading message that it is inactive.

PR #4 works around the scan gate by validating each vendor DLL's CodeView GUID
and setting the missing bit in the file. That edit is only recognized on the
next launch. It is technically narrow—one byte per DLL—but it mutates files in
the vendor mod folders through `Data/SKSE/Plugins`, needs a two-launch workflow,
and deliberately calls `RE::DebugMessageBox` to request a restart. It also
depends on the game working directory being the Skyrim root. The current
headless launcher does set that directory, but the other policy violations
remain.

## Required target files

Scrambled Updates' page asks for all three KernalsEgg components. The base is
not a FOMOD; the two optional archives are separate FOMODs:

1. [Scrambled Bugs](https://www.nexusmods.com/skyrimspecialedition/mods/43532)
   main file `368378`, version `21`.
   - Archive SHA-256:
     `8412974b83426e10925865527e7d4764ea79db0e88a3666e79c108fad9d88ebd`
   - DLL SHA-256:
     `dd8b458e623fe9362a0e0acaa32223dad5a25a798019305dc8ffa987f9d6b969`
2. Optional file `368379`, Script Effect Archetype Crash Fix `1`.
   - Select `1.6.318.0+ (Anniversary Edition)` for runtime `1.7.104`.
   - Archive SHA-256:
     `23f1b65652eb516842d978fef186fa61c7b63d3f8a93e49337e2f3fa35e07a8e`
   - Selected DLL SHA-256:
     `dfabdfd5bc489b675e3d035c64bc15547aa689c2ddf490660289b352e36cf1f1`
3. Optional file `368380`, Vendor Respawn Fix `1`.
   - Select `1.6.629.0+ (Anniversary Edition)` for runtime `1.7.104`.
   - Archive SHA-256:
     `e66e61fd16b4634ad7bd0928846c28b00f9295432f05ed85c71a6cfec4251dc8`
   - Selected DLL SHA-256:
     `86e23d7dc98e2f58c0de4ad1a351616603ef83e917e049f1473b17d707a47821`

The empty log option in each FOMOD is unnecessary; the DLL creates its log.
The current MO2 profile contains only disabled Scrambled Bugs `21`. Neither
optional DLL is installed. Address Library already supplies
`versionlib-1-7-104-0.bin`.

## Engine Fixes and active-stack compatibility

Engine Fixes `7.0.21` and Scrambled Bugs address different named defects. No
semantic duplicate was found between the active `EngineFixes.toml` fixes and
the Scrambled Bugs `21` list, and there is no documented blanket incompatibility.
Both use SKSE's new preload phase. Engine Fixes loads first and Scrambled Updates
registers its DLL notification before the non-preload target DLLs are normally
loaded; that ordering is compatible.

This does not prove every optional gameplay patch is compatible with every
future perk/combat overhaul. In particular, Scrambled Bugs' `Apply Multiple
Spells` patch changes perk-entry-point selection semantics and needs explicit
patches for some perk overhauls. It is currently disabled.

The current Scrambled Bugs JSON is mostly default but is not “bug fixes only.”
Its enabled gameplay-affecting patches include:

- experience on every lockpick rather than only the first;
- all effects of multi-effect enchantments scaling with Enchanting;
- source-to-target casting semantics for perk-entry-point spells;
- multiple paused-game hit effects; and
- reflect damage above 100 percent.

Those need a design review before activation, especially because the user wants
slower leveling. `powerAttackStamina` is currently false despite the user's
survival/combat direction and should be decided separately, not silently
changed during compatibility work.

## Error and popup behavior

This stack is not currently automation-safe:

- Nexus `1.1.0` and current main call `RE::DebugMessageBox` at `kDataLoaded`
  when no target patched or a target failed. This is an in-game modal and is not
  intercepted by the local SKSE fork's `MessageBoxA/W` import redirection.
- The unreleased PR #4 also uses that in-game modal after editing DLLs to ask
  for a restart.
- KernalsEgg's old Address Library error path invokes native `MessageBoxA` and
  then terminates the process. If a target's GUID/RVA patch fails, that can run
  during DLL initialization before SKSE has a chance to redirect the target's
  imports. Offline exact-build validation is therefore mandatory.
- CommonLib's fatal Address Library/log-directory path invokes native
  `MessageBoxW` and terminates. The local SKSE fork can redirect that for
  Scrambled Updates when `SKSE_AUTOMATION_SILENT_UI=1`, but an ordinary user
  launch still can display it.

Successful operation writes only `ScrambledUpdates.log` plus each target's own
log. No network, telemetry, shell command, browser launch, or background worker
was found in the source. Runtime overhead after initialization is negligible.

## Supersession check

No current Nexus mod replaces this bridge for runtime `1.7.104`; Nexus search
finds Scrambled Updates as the only dedicated modern compatibility shim. The
KernalsEgg source repository has newer, unreleased Scrambled Bugs source that
identifies itself as interface version `22`, but there is no released binary,
and that repository has no declared software license. It is not a stable or
redistributable substitute for v21. Engine Fixes and po3 Tweaks overlap only in
the broad category “engine fixes,” not in this complete feature set.

## Silent, stability-first promotion plan

Do not use Nexus `1.1.0` or enable the three targets in the live profile now.
When the user authorizes an early port instead of waiting upstream:

1. Fork current GPL source, include the GUID gate, pin the exact CommonLib
   release/commit and vcpkg baseline, add CI, and change every recoverable
   failure to log-only status. Remove all `RE::DebugMessageBox` calls.
2. Preserve the three vendor archives byte-for-byte. Do not adopt PR #4's
   runtime file mutation. The preferred internal solution is an exact-GUID
   compatibility exception in our already-owned SKSE core so SKSE accepts only
   these three known binaries; Scrambled Updates can then patch them in memory.
   This requires a separate SKSE license/distribution review before publication.
3. Headlessly stage the base and the two exact AE FOMOD selections as three
   separate immutable vendor mods. Stage the GPL bridge as a fourth owned mod.
4. Before any launch, verify all archive/DLL hashes, CodeView GUIDs, SKSE flags,
   the three original Scrambled Bugs operands, the `1.7.104` Address Library
   file, plugin exports, and bridge imports. Refuse unknown builds.
5. Run a disposable profile on the isolated hidden desktop with
   `SKSE_AUTOMATION_SILENT_UI=1`. The first accepted run must require no restart
   and create no visible UI.
6. Accept only if `skse64.log` shows all four DLLs accepted,
   `ScrambledUpdates.log` reports format-5 addresses and all three targets
   patched (`3`, `0`, and `0` displacement corrections), each target log reaches
   normal load, and no `SUPPRESSED PLUGIN UI`, unexpected format, missing ID,
   or fatal-load line appears.
7. In a disposable save, exercise player enchantment charge across save/reload,
   merchant inventory across save/reload and cell reset, concurrent script-effect
   projectiles, difficulty damage, and repeated save/load cycles. Only then
   promote the exact configuration to the real profile.

## Evidence integrity

Official archives were obtained through the local read-only Nexus audit cache.
Source and all three audit builds stayed under the ignored audit directory. No
API credential was printed, copied, or written to this repository. No vendor
DLL was edited during this audit.
