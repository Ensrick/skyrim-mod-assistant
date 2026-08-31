# Modpack playable-baseline roadmap — 2026-08-28

Canonical tracker: [GitHub issue #23](https://github.com/Ensrick/skyrim-mod-assistant/issues/23)

This document is the local, version-controlled index for the current playable-
baseline work. GitHub owns discussion, status, and acceptance evidence; this
repository owns durable decisions, reproducible configuration, scripts, and
publication-safe audit records.

No item in this document is installation authorization. A candidate is not an
adopted mod until the user explicitly approves it, it passes archive and
licensing review, and its resulting profile state is recorded.

## Immediate audit result

- The latest completed foreground session produced no new crash log. Community
  Shaders, Proteus, QuickLoot IE, FSMP, ConsoleUtil, and Survival Mode Improved
  loaded. Remaining warnings are tracked in issue #37.
- Full Nature of the Wild Lands 3.14 is the active placement authority;
  Ulvenwald 3.3.2 supplies lowest-priority assets through Tree Diversity
  Project 1.0.1's controlled BOS mix. `Ulvenwald.esp` is deliberately disabled.
  Skyland AIO 1K 4.32 is the active broad architecture/landscape base. Nordic
  Cut and Mild Lands are not installed.
- Freak's Floral Fields 3.2.3 is the active grass overhaul with DrJacopo's
  3D Grass Library 16.53. Its realistic regional FOMOD mix, seven light
  plugins, and one-file 4096-axis texture-cap overlay are recorded in
  `records/freaks-floral-fields-3.2.3-2026-08-30.md`. Grass utilities and
  generated cache remain separate, unapproved decisions.
- Immersive Equipment Displays, Open Animation Replacer, and Skill Uncapper
  are installed but disabled. MCM Helper is now active on its official 1.6.3
  runtime build; its foreground MCM/settings-write smoke test remains open.
- VioLens is enabled. Its desired rules still need to be made portable through
  the MCM configuration pipeline.
- Starfrost and Survival Mode Improved are intentionally used together.
  Starfrost currently caps Survival Mode Improved penalties at 50 percent and
  provides no wetness system, which explains why the experience feels light.
- Community Shaders now detects the display as HDR-capable but selects SDR, as
  intended by the current configuration.

## Work register

| Area | Issue | Current state | Next acceptance step |
|---|---|---|---|
| Terrain seams | [#24](https://github.com/Ensrick/skyrim-mod-assistant/issues/24) | Needs location evidence | Capture cell, coordinates, view angle, and screenshot before choosing a mesh/landscape fix. |
| Sword draw/sheathe | [#25](https://github.com/Ensrick/skyrim-mod-assistant/issues/25) | IED and OAR disabled | Restore the frameworks, then test placement-aware draw/sheathe animations against one- and two-handed swords. |
| One-handed idles | [#26](https://github.com/Ensrick/skyrim-mod-assistant/issues/26) | Framework blocked | Select restrained OAR conditions and verify first/third person, shield, spell, and dual-wield transitions. |
| Vanilla-plus hair | [#27](https://github.com/Ensrick/skyrim-mod-assistant/issues/27) | VHR SMP 1.0.3 player + 1.0.1 NPC package installed; USSEP/CRF FaceGen precedence reconciled | Foreground-check player/beast hair, helmets, the 31 preserved non-SMP faces, Proteus swaps, and crowded-scene frame time before closing. |
| Vanilla asset coverage | [#28](https://github.com/Ensrick/skyrim-mod-assistant/issues/28) | Diagnostic candidate identified | Use johnskyrim's Visualize Vanilla only in a disposable diagnostic profile. |
| Trees and plant shadows | [#29](https://github.com/Ensrick/skyrim-mod-assistant/issues/29) | Full NotWL 3.14 placements plus verified Ulvenwald 3.3.2 assets through TDP 1.0.1; only NotWL patches active | Runtime-test frame-time, wind, shadows, clipping, routes, and LOD transitions for the selected mixed-asset/full-NotWL-placement stack. |
| Grass | [#112](https://github.com/Ensrick/skyrim-mod-assistant/issues/112) | Freak's Floral Fields 3.2.3 realistic regional mix + required DrJacopo library enabled; static audits clean | Foreground-check density, biome fit, pop-in, seams and frame time, then decide utilities/cache and separate Solstheim coverage. |
| Repository consolidation | [#30](https://github.com/Ensrick/skyrim-mod-assistant/issues/30) | Control plane selected | Inventory ownership/licenses and migrate original work without disturbing dirty third-party forks. |
| Survival visibility/depth | [#31](https://github.com/Ensrick/skyrim-mod-assistant/issues/31) | Current stack is deliberately light | Choose one coherent needs/exposure model, then add compatible widgets, wetness, clothing warmth, and cloak physics. |
| Imperial armor | [#32](https://github.com/Ensrick/skyrim-mod-assistant/issues/32) | Candidate direction identified | Audit NordwarUA New Legion plus current SPID/SkyPatcher distribution before approval. |
| Attributes/injuries/disease | [#33](https://github.com/Ensrick/skyrim-mod-assistant/issues/33) | Design required; zero starting gold is now specified | Verify Skyrim Unbound can enforce exactly 0 starting gold, verify post-start regeneration, define zero-magicka progression, then select one injury/disease system. |
| Leveling curve | [#34](https://github.com/Ensrick/skyrim-mod-assistant/issues/34) | No curve mod active | Model target levels by playtime and implement the smallest reproducible settings patch. |
| 4K UI | [#35](https://github.com/Ensrick/skyrim-mod-assistant/issues/35) | SkyUI 6 active | Compare Norden UI/current Nordic stacks without overwriting or downgrading SkyUI 6 files. |
| Inventory/visible gear | [#36](https://github.com/Ensrick/skyrim-mod-assistant/issues/36) | IED disabled | Restore IED first, then define visible slots and a realistic but playable carry model. |
| Runtime log triage | [#37](https://github.com/Ensrick/skyrim-mod-assistant/issues/37) | No latest-run crash; actionable warnings remain | Rebuild/repackage Community Shaders features coherently and classify optional developer-bridge noise. |
| Killmoves | [#38](https://github.com/Ensrick/skyrim-mod-assistant/issues/38) | VioLens enabled | Record and replay approved MCM rules; test melee, ranged, dragons, and camera behavior. |
| Portable MCM setup | [#39](https://github.com/Ensrick/skyrim-mod-assistant/issues/39) | Official MCM Helper 1.6.3 enabled; static audits clean | Foreground-smoke the helper, then create a deterministic settings export/replay workflow. |
| MCM persistence | [#40](https://github.com/Ensrick/skyrim-mod-assistant/issues/40) | Save-local behavior not yet inventoried | Classify each MCM as save-local, file-backed, helper-backed, or replayed and back it up accordingly. |
| TexGen/DynDOLOD | [#41](https://github.com/Ensrick/skyrim-mod-assistant/issues/41) | Deferred correctly | Freeze landscape/tree/grass/load order, then run pinned headless generation through MO2's VFS. |
| Wolves as wildlife | [#42](https://github.com/Ensrick/skyrim-mod-assistant/issues/42) | Record-level design needed | Audit fixed and leveled wolves across all adopted worldspaces before creating a narrow generated patch. |
| Selective extra enemies | [#43](https://github.com/Ensrick/skyrim-mod-assistant/issues/43) | Upstream 3.1 held after source audit | Design an allowlist-first 1.7.104 implementation for humanoid and undead categories only. |
| Music | [#44](https://github.com/Ensrick/skyrim-mod-assistant/issues/44) | Current framework identified | Evaluate Personalized Music SSE - Modernized and keep user-owned audio in a local-only manifest. |
| Informative console | [#48](https://github.com/Ensrick/skyrim-mod-assistant/issues/48) | Selection and provenance visibility required | Research a maintained 1.7.104-compatible console that exposes selected reference/base-form and source/winning plugin information; do not install without approval. |
| Face-paint/beard artifact | [#49](https://github.com/Ensrick/skyrim-mod-assistant/issues/49) | Angle-dependent loading-screen defect observed once | Capture the exact Nord model, cosmetics, camera angle, and runtime evidence before isolating shader, alpha/depth, mesh, and texture interactions. |
| Period underlayers | [#50](https://github.com/Ensrick/skyrim-mod-assistant/issues/50) | Vendor-default pool is not accepted; Ragged Robes are an approved candidate garment | Build a verified FormID pool in an Ensrick-owned overlay while retaining removable garments and full nudity. |
| Guard level scaling | [#51](https://github.com/Ensrick/skyrim-mod-assistant/issues/51) | Target rule specified: player level at 1:1, minimum 5, no +20 offset | Audit ordinary and special guard winners separately, then generate a narrow ESL patch and test several player levels. |

## Current candidate shortlist

These are research results, not an install queue:

- Hair: [Vanilla Hair Remake](https://www.nexusmods.com/skyrimspecialedition/mods/63979), active on its optimized FSMP path. Main 1.0.3 replaces the player hairs; the optional 1.0.1 BSA supplies SMP FaceGen to 2,405 vanilla NPC paths after 29 USSEP and 2 CRF face winners are preserved.
- Asset coverage: [Visualize Vanilla](https://www.nexusmods.com/skyrimspecialedition/mods/84265), disposable diagnostic profile only.
- Trees: full Nature of the Wild Lands 3.14 owns placements, while Ulvenwald
  3.3.2 assets enter only through Tree Diversity Project's official NotWL-base
  configuration. Nordic Cut is rejected and Mild Lands is not authorized.
  Happy Little Trees remains only a measured-performance fallback if the mixed
  stack misses the runtime gate. See
  `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`.
- Draw/sheathe: [Weapon Styles - Draw-Sheathe Animations for IED](https://www.nexusmods.com/skyrimspecialedition/mods/85085), only after IED/OAR are working.
- Imperial armor: [RMB SPIDified - New Legion](https://www.nexusmods.com/skyrimspecialedition/mods/84974), subject to distribution and balance audit.
- UI: [Norden UI](https://www.nexusmods.com/skyrimspecialedition/mods/166086), subject to dependency and 4K scaling review.
- Injuries: [Simple Combat Injuries](https://www.nexusmods.com/skyrimspecialedition/mods/104843) is the narrower modern starting point; Wounds remains the deeper alternative.
- Selective populations: [Dynamic Enemy Spawns SKSE](https://www.nexusmods.com/skyrimspecialedition/mods/178556) is held: its 3.1 source was audited and lacks the required allowlist and a complete reproducible 1.7.104 build. See `ENCOUNTER-POPULATION-2026-08-28.md`.
- Music: [Personalized Music SSE - Modernized](https://www.nexusmods.com/skyrimspecialedition/mods/174068).

## Baseline gate

Before expanding the mod list, the current profile should pass several hours of
play without a new crash, modal background error, refused native plug-in, or
unexplained save-state loss. Visual and gameplay additions then enter one
coherent subsystem at a time, with a recorded before/after test. DynDOLOD output
is generated only after worldspace, terrain, tree, and grass decisions settle.
