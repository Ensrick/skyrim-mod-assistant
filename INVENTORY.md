# Skyrim SE — Mod Inventory & Keep/Discard Tracker

> **SUPERSEDED (2026-08-26):** historical 2026-06-09 snapshot of the old
> Vortex-managed collection. Live state is BASELINE.md + the MO2 portable
> instance (`repos\mo2-instances\skyrim-se`) + `records/installed-mods.json`.
> Runtime is now 1.7.104; the historical table below does not reflect current
> reality. Current hair delta: FSMP 4.1.1 AVX, Vanilla Hair Remake SMP 1.0.3
> main (`63979/510409`) and the official 1.0.1 NPC package (`63979/500742`)
> are installed and enabled in MO2. The old Skyrim-1.6-only SMP-NPC Crash Fix
> is deliberately absent because FSMP 3.0+ integrated the correction. Exact
> hashes, conflict winners, and the remaining foreground checks are in
> `records/vanilla-hair-remake-smp-2026-08-30.md`.
> Current tree delta: full Nature of the Wild Lands 3.14 is the placement
> authority, with Ulvenwald 3.3.2 assets consumed through Tree Diversity
> Project 1.0.1; `Ulvenwald.esp` is deliberately disabled. Exact evidence is in
> `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`.
> Current grass delta: Freak's Floral Fields 3.2.3 and DrJacopo's 3D Grass
> Library 16.53 are enabled using the recorded realistic regional mix, with
> Freak's Floral Solstheim 1.0.1 and Freak's Floral Veil 1.0 extending it to
> Solstheim and the Soul Cairn. All nine plugins are light, every effective
> texture stays within the 4096-axis cap, and a private one-file overlay
> enforces that cap for the base FFF package. Exact evidence is in
> `records/freaks-floral-fields-3.2.3-2026-08-30.md`.

Snapshot of the existing Vortex-managed collection, captured **2026-06-09** before resetting to a vanilla baseline.
Source of truth: Vortex staging `%APPDATA%\Vortex\skyrimse\mods` (27 mods, 15.3 GB) + downloads (30 archives) + the two preserved deployment manifests in `records\`.

Runtime: **Skyrim SE 1.6.1170** (AE) · SKSE 2.2.6 · all SKSE plugins must target 1.6.1170 or be Address-Library version-independent.

**Legend** — Deployed: ✓ live in `Data\` / ⛔ staged but not deployed / (dl) download-only helper.
Decision is **yours** during the review; "My read" is just a suggestion. Versions are *installed*; latest-version check happens once the Nexus API key is set.

## Core frameworks / dependencies — other mods need these
| Mod | Nexus ID | Installed | Role | Deployed | Decision | My read |
|---|---|---|---|---|---|---|
| Skyrim Script Extender (SKSE64) | 30379 | 2.2.6 | Script extender (core) | ✓ root | — | keep (core) |
| All in one Address Library (AE) | 32444 | v11 | SKSE plugin dependency | ✓ | — | keep (dependency) |
| PapyrusUtil AE SE | 13048 | 4.6 | Scripting framework | ✓ | — | keep (dependency) |
| JContainers SE | 16495 | 4.2.9 | Data framework | ✓ | — | keep (dependency) |
| ConsoleUtilSSE NG | 76649 | 1.5.1 | Console framework | ✓ | — | keep (dependency) |
| SkyUI | 12604 | 5.2 | UI / MCM framework | ✓ | — | keep |
| UIExtensions | 17561 | 1.2.0 | UI menu framework | ✓ | — | keep (dependency) |
| Base Object Swapper (BOS) | 60805 | 3.3.1 | Object-swap framework | ✓ | — | keep (dependency) |
| SkyPatcher - AE | 106659 | 3.3.2 | Record-patch framework | ✓ | — | keep (dependency) |
| powerofthree's Tweaks | 51073 | 1.13.1 | Engine fixes/framework | ✓ | — | keep |
| Fuz Ro D'oh | 15109 | 2.5 | Silent-voice framework | ✓ | — | keep |
| AnimObject Swapper | 75167 | 1.1.0 | Swap framework | (dl) | — | keep IF Sharpen Swords kept |

## Stability / crash fixes — low-risk
| Mod | Nexus ID | Installed | Role | Deployed | Decision | My read |
|---|---|---|---|---|---|---|
| Actor Limit Fix (AE) | 32349 | v9 | Crash fix | ✓ | — | keep |
| Animation Queue Fix | 82395 | 1.0.1 | Bug fix | ✓ | — | keep |
| Animated Static Reload Fix NG | 69331 | 1.0.1 | Bug fix | ✓ | — | keep |
| SrtCrashFix AE | 31146 | 0.4.1 | Crash fix | ✓ | — | keep |
| SMP-NPC crash fix | 91616 | 1.1 | Historical Vortex download; obsolete with current FSMP and incompatible with runtime 1.7.104 | ⛔ | — | do not activate |

## Physics (HDT-SMP)
| Mod | Nexus ID | Installed | Role | Deployed | Decision | My read |
|---|---|---|---|---|---|---|
| Faster HDT-SMP | 57339 | 4.1.1 current MO2 | Cloth/hair physics engine (AVX) | ✓ | Keep | active |
| Vanilla hair remake SMP | 63979 | 1.0.3 main + 1.0.1 NPCs | Physics-enabled vanilla replacer; 568-file player layer + 2,436 NPC FaceGen meshes | ✓ | Keep queued | active; foreground smoke remains #27 |

## Gameplay / QoL
| Mod | Nexus ID | Installed | Role | Deployed | Decision | My read |
|---|---|---|---|---|---|---|
| Alternate Perspective | 50307 | 4.0.3 | Alternate start (325 files) | ✓ | — | review (taste) |
| Instant Container Access v2 | 6851 | 2.0 | Loot-without-opening QoL | ✓ | — | review (taste) |
| Auto Input Switch | 54309 | 1.2.3 | Gamepad/KBM auto-switch | ✓ | — | review (taste) |
| Crafting Categories for SkyUI | 81409 | 1.1.1 | Crafting menu categories | ⛔ | — | review |

## Visual / gear — main "keep?" candidates
| Mod | Nexus ID | Installed | Role | Deployed | Decision | My read |
|---|---|---|---|---|---|---|
| Kinda Believable Weapons | 100845 | 1.21 | Weapon retexture (41 files) | ✓ | — | review (taste) |
| Base Coat | 46850 | 1.1 | Weapon material retexture | ✓ | — | review (taste) |
| FX Glow Remover (BOS) | 138246 | 1.0 | Removes enchant glow | ✓ | — | review (taste) |
| Sharpen Other Swords II | 75237 | 0.2.3 | AnimObject sword visual | ⛔ | — | review (taste) |
| AE - Bone Wolf Patch | — | v2.6 | Creation Club Bone Wolf fix | ✓ | — | keep IF using that CC |

## Notes
- Historical Vortex-only staged files still include SMP-NPC Crash Fix, Crafting
  Categories for SkyUI, and Sharpen Other Swords II. None is active in MO2;
  SMP-NPC Crash Fix must remain inactive with FSMP 4.1.1.
- **Texture-BSA orphan**: 9 `Skyrim - Textures*.bsa.vortex_backup` files exist in `Data\` — evidence a texture overhaul was installed and removed at some point. Vortex Purge restores the vanilla BSAs.
- **Downloads (30) > staged (27)**: extras are the AnimObject Swapper helper + a duplicate FX Glow Remover archive.
- **Read on the set**: a frameworks-heavy foundation with light content. The dependencies + fixes are near-automatic keeps; the real review is ~7 taste items (visual/gear + alt-start + physics-hair) plus a latest-version check on everything.
