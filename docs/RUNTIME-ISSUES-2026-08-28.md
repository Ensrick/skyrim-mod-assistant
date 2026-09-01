# Runtime repair report — 2026-08-28

This report distinguishes proved runtime results from items that still need an interactive user test. It does not authorize installing additional mods.

## Proteus dependency chain — native loader gate passed

### Original failure

On Skyrim 1.7.104, SKSE rejected all four native components needed for a useful Proteus test:

- `Proteus.dll`
- `JContainers64.dll`
- `PapyrusUtil.dll`
- RaceMenu's `skee64.dll`

Each component was rebuilt locally for 1.7.104. The first bounded launch still showed the old failures, but the source builds were not at fault: the deployed overlay folders contained `Plugins/<dll>` instead of `SKSE/Plugins/<dll>`. An older `MO2Headless` build had incorrectly unwrapped `SKSE` as though it were a disposable archive wrapper. The enabled overlays therefore never contested the older DLLs supplied by the base mods.

### Repair

The four overlays were replaced transactionally with a temporary `Data/SKSE/Plugins` staging wrapper, producing the correct installed `SKSE/Plugins/<dll>` paths:

| Component | Overlay priority | Replacement transaction |
|---|---:|---|
| Proteus | 106 | `20260828T190513023Z-6e1b13b95633` |
| JContainers | 107 | `20260828T190513098Z-1d554b4917bb` |
| PapyrusUtil | 108 | `20260828T190513175Z-b435e7e05918` |
| RaceMenu | 109 | `20260828T190513252Z-d0e12c1d0e27` |

The current `MO2Headless` source contains the permanent normalization fix (`3769ece0`, *Preserve single Bethesda data roots during staging*). GitHub Actions run `33024105521` successfully built that exact revision. Its artifact was tested against a disposable portable instance: staging `SKSE/Plugins/preserve-root-probe.txt` retained the complete path and the disposable-instance audit passed.

The verified controller is now deployed to the live portable instance:

- Installed SHA-256: `FEBD3C0A505689A41FF3CECF14569017DD9A36071D681AAEE6AC854CE0257A89`
- Previous SHA-256: `18469B00520CDC6C1924D6A2D5BBC5EF982C3AD3804EDABD9E14B277A52F1921`
- Previous executable retained recoverably under `backups/headless-controller`
- Post-deployment `status` and `audit` both passed

### Runtime evidence

A bounded 120-second launch began at `2026-08-28T19:05:34Z` on a separate Windows desktop. It reached the main menu and stayed alive for the full window. The controller returned its documented timeout result (`75`); this is a successful bounded-run outcome, not a game crash.

- SKSE checked 21 DLL plug-ins and refused zero.
- `JContainers64.dll`, `PapyrusUtil.dll`, `Proteus.dll`, and `skee64.dll` all logged `loaded correctly`.
- JContainers loaded the database for `SkyrimSE.exe` 1.7.104.0 and registered its functions.
- PapyrusUtil initialized its offsets and registered its functions.
- Proteus reported local build `1.1.0.104` and registered its Perk, Spell, Item, Actor, Utility, and Form native function groups.
- RaceMenu initialized; its remaining Argonian default-morph messages are asset-binding diagnostics, not a loader rejection.
- No new `crash-*.log` was created.

### Still unproved

Native initialization does not prove Proteus's user-facing workflow. The remaining acceptance test is interactive:

1. Confirm the Proteus MCM appears after MCM registration settles.
2. Create a disposable character snapshot.
3. Switch characters.
4. Save, reload, and switch again.
5. Check inventory, appearance, perks/spells, location, follower handling, and global quest-state behavior.

## Nested 2560×1440 image — configuration cause corrected

### Root cause

The output window and swap chain were already correct:

- Windows primary output: 3840×2160.
- `SkyrimPrefs.ini`: 3840×2160 borderless windowed.
- SSE Display Tweaks runtime log: `3840x2160`, windowed, flip-discard, three buffers.

The active Community Shaders AIO settings selected DLSS quality upscaling (`upscaleMethod: 3`). A 3840×2160 quality-mode render uses a 2560×1440 internal image—the exact size mistaken for the secondary display. The secondary monitor was not selected as Community Shaders' output; its resolution merely matched the DLSS internal target.

### Repair and evidence

The active user settings now select native TAA and disable frame generation:

- `Upscaling.frameGenerationMode: 0`
- `Upscaling.upscaleMethod: 1`
- `Upscaling.upscaleMethodNoDLSS: 1`

The next log still says that the DLSS library is available and loaded. That only describes feature availability; it is not evidence that DLSS is selected. SSE Display Tweaks continued to request a 3840×2160 windowed swap chain, and Community Shaders initialized HDR10 at that output.

An interactive visual confirmation is still required because a hidden desktop cannot prove what the user's primary monitor presents. Acceptance criteria remain: one full 3840×2160 image, clean Alt-Tab, cursor release to the second monitor, and no forced minimize.

## Background-test disturbance and policy correction

The separate desktop suppressed windows but did not suppress Skyrim's audio session. The main-menu music was audible to the user during the successful smoke run. This violated the no-disturbance requirement.

The isolated launcher now uses a dedicated `Codex Smoke - Muted` MO2 profile. Before any run it refreshes that profile from `Default`, copies the current game INIs into the isolated profile, forces `LocalSettings=true`, and sets `fAudioMasterVolume=0.0000`. It does not alter the Default profile or the user's persistent audio setting. The script also treats controller code 75 as the expected bounded timeout and still performs exact-process cleanup.

No further launch was performed after adding the mute control. A later background launch must first retain this isolated profile and zero-volume gate; otherwise it is prohibited.

## Other issues exposed by the same run

- QuickLoot IE's DLL loaded but disabled itself because `QuickLootIE.esp` had been left disabled. The existing plug-in was enabled transactionally (`20260828T192717004Z-887500895fab`) and the Default profile audit passed. Runtime menu behavior remains to be confirmed during the next user launch.
- ConsoleUtilSSE NG's official DLL reported two failures resolving VM class type 61. Source inspection mapped them to selected-reference Papyrus registration and an outdated pre-fix CommonLib layout. A public `1.6.1.104` source rebuild at commit `ad5e6e5` passed clean CI run `33208154245` and is installed as a priority-110 DLL-only overlay (transaction `20260828T204303046Z-84343993f71e`). The MO2 audit passed; the next foreground launch must still prove that the VM errors are gone and Proteus's selected-reference path works. See `CONSOLEUTIL-1.7.104-REBUILD-2026-08-28.md`.
- Base Object Swapper and KID warn that MergeMapper did not answer. This is expected while no MergeMapper implementation is active, but should be revisited before merged plug-ins are introduced.
- SKSE Menu Framework falls back from missing `MainFont.ttf` to `SkyrimMenuFont.ttf`; functional, but untidy.
- Community Shaders' `devbench` dispatch warnings indicate an absent optional development listener, not a renderer failure.
