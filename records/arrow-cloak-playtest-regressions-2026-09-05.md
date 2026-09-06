# Arrow and cloak playtest regressions — 2026-09-05

Status: arrow 0.3.2 and full-cloak exclusivity 0.1.0 installed; physics awaits approval. In-game acceptance remains open.

## User reproductions

- A full-health player in godmode retained every incoming arrow.
- A Sons of Skyrim full cloak could be worn together with a full fur cloak.
- The Sons of Skyrim cloak had no visible physics.

These are separate defects. Leveled-list distribution cannot fix player equipment-slot compatibility, and a loaded FSMP DLL does not prove a particular cloak contains a physics rig.

## Arrow evidence

The latest local `ConditionalArrowEmbedding.log` reports version 0.3.1 on Skyrim 1.7.104.0 / SKSE 2.3.1. At 18:47:18 local it records target `00000014`, body hit, post-hit health ratio `1.0000`, `killedByHit=false`, **`livingHumanoid=false`**, and `action=preserve-vanilla`. The normal physical-hit hook is reached. The latest save header identifies `BretonRace`.

Source and compiled-code inspection identified a direct inherited `Actor::IsReanimated()` call using the compile-time ActorState base layout instead of `AsActorState()`'s version-aware layout. On this runtime the state word must be read at Actor+0xC8, not Actor+0xA8. Unrelated memory can therefore exclude a living humanoid as reanimated. The old log does not record individual eligibility gates, so it cannot by itself prove which gate rejected that particular hit. This confirmed native defect and observed incorrect classification do not rely on dismissing godmode as an invalid test.

The fix must use the runtime-aware accessor, include an actual-layout regression test, and provide bounded player-specific eligibility diagnostics. Full-health eligible humanoids must also bounce when head/body metadata is unknown, since both policies select bounce at that health. The existing threshold stays **strictly below 50%** for nonlethal body embedding; lethal hits and excluded creatures retain vanilla behavior.

Runtime gate reopened: https://github.com/Ensrick/ConditionalArrowEmbedding/issues/1

Installed 0.3.2 at 19:29:54 local using transaction `20260906T002954272Z-de310310bb6d`. DLL hash matches the clean source build, priority/enabled state/configuration are preserved, and all 364 modlist entries retain exact order. Only the generated-by comment changed in modlist.txt. Plugin list is byte-identical. Controller audit has zero errors. Details: `records/source-builds/conditional-arrow-embedding-0.3.2.json`. No gameplay success is implied by these static checks.

## Cloak evidence and repair boundary

The active Pelts full cloaks occupy slot 57, while Sons of Skyrim full cloaks occupy 40+46. These do not exclude each other. An owned configuration can add a shared exclusion bit to an explicit full-cloak allowlist without deleting existing rendering slots or rewriting vendor meshes, but the bit must not introduce collisions with mantles/accessories. Short scarves, hoods and non-cloak fur collars must not be classified as full cloaks.

The proposed slot-57 union was **rejected before deployment**: the older audit's 109 "Pelts cloaks" includes 99 full-cloak IDs and 10 mantle IDs. Giving cloth cloaks slot 57 would wrongly block those mantles. Inigo's Mr Dragonfly wearable accessories also use that slot. A whole-profile free-slot audit is required before choosing an alternative reservation; do not silently move accessories or collars to another slot.

The completed audit reserves **slot 58/index 28** for 240 exact full-cloak records. It found no existing slot-58 use in 348 plugins (8,747 ARMO plus 4,315 ARMA declarations, including losing overrides). The exact mesh scope includes 302 explicit paths plus 274 derived weight-zero companions: 569 present winners parse with no partition-58 use; seven existing absences are tracked as absence sentinels, not valid meshes. No excluded item shares a changed ARMA. Original slots/meshes and all ten Pelts mantle-family pieces remain unchanged.

Installed at 19:58:02 local, transaction `20260906T005802828Z-936f950b7292`, priority 286. Twenty-one cloak tests and twelve strict-reader tests pass; installed input/mesh freshness and MO2 audit pass. No plugin activation or order changed. See `records/source-builds/ensrick-full-cloak-exclusivity.json` and the reproducible recipe `audit/cloak-exclusivity.md`. Existing collar/cloth slot-46 and mantle/fur slot-57 conflicts remain; this repair introduces no new restriction on those accessories and does not migrate their original slots.

Sons of Skyrim physics compatibility research is separate. All 59 current SoS cloak/cape NIF paths (48 worn, 11 ground) resolve to the original SoS mod. None contains an SMP config reference, and neither SoS nor Xtudo supplies physics XML. The actual main archive supplies `capeM_SoS.xml` and `capeF_SoS.xml`, which are absent from the enabled stack. Representative current mesh: `Meshes/NordWar/SonsOfSkyrim/Cloack/CloackM_1.nif`, SHA-256 `2F217D297210B3B2A8B75EB7E4688746228986521829C386AA7334597F7B6814`.

The direct candidate is [Sons of Skyrim - HDT-SMP Cloaks](https://www.nexusmods.com/skyrimspecialedition/mods/114690), main v1.1 file **483316** (18,252,655 bytes), intended for the SoS 2.0 generation used here. Authenticated API metadata corrected an erroneous research file ID before any download: **484635 is the Sentinel OPTIONAL patch**, not the main file. It requires an archive/ESP audit against Xtudo and our slot solution; do not use the Sentinel optional patch in this non-Sentinel profile. User approval was requested asynchronously; no new third-party physics mod has been adopted. The installed CoS/ElSopa receipt separately leaves Artesian physics integration unfinished under #193.

Read-only archive inspection is complete for file 483316, SHA-256 `C2037FE08D4CF4EA6B3B8BB24E1C7C3B64F608F72D491C59C8E5D3C32DC97FB0`: 48 NIFs, two XMLs, one ESP, one PNG. Its `SonS_HDT_patch.esp` contains only 12 existing SoS ARMO overrides, with masters Skyrim.esm and NW_Sons_of_Skyrim.esp. Compared with the installed SoS source, each changes the biped mask from 40+46 to 46 and reorders the same keywords; other decoded fields are equal. Xtudo's installed plugin does not override these 12 cloak ARMO records. This explains why an assets-only install is not automatically equivalent to the author's complete patch. No assets were installed and no Keep entry changed.

Tracking: equipment https://github.com/Ensrick/skyrim-mod-assistant/issues/240; distribution https://github.com/Ensrick/skyrim-mod-assistant/issues/200; missing source meshes https://github.com/Ensrick/skyrim-mod-assistant/issues/241; master https://github.com/Ensrick/skyrim-mod-assistant/issues/95.

## Acceptance tests — still required in the engine

1. Reload the game with the rebuilt DLL; verify its version and the player's eligibility gates in the log. Previously embedded arrows are not an acceptance test: the hook governs new impacts.
2. Repeat the user's full-health godmode incoming-arrow test. Confirm both a visible bounce and the corresponding eligible player decision; also repeat without godmode.
3. Test a nonlethal headshot, body hits above/exactly at/below 50% post-hit health, and a one-shot kill from full health. Damage must remain unchanged; killing hits preserve vanilla embedding.
4. Test an ordinary non-player living humanoid and excluded undead/creature targets.
5. Equip a full fur cloak, then a Sons of Skyrim full cloak, and reverse the order. Only one full cloak may remain equipped; preserve the distinct non-cloak mantle/scarf cases.
6. Separately inspect a newly equipped cloak and a newly spawned NPC for physics. Old stacked NPC inventories may require an equipment refresh; do not reset the user's real-save inventories as a diagnostic shortcut.

No game, editor, desktop window or audio was launched for this investigation. Static policy, binary and asset checks must not be reported as successful gameplay tests.
