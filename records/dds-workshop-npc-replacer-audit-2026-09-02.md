# DDS Workshop NPC Replacer: AE private-port audit

**Decision:** rejected on 2026-09-02 after confirming that no official SE/AE
release exists. The author's latest build is still an Oldrim/Legendary Edition,
UNP-only preview covering 78 female NPCs and would require a substantial private
conversion. Nothing was installed or enabled. Research is retained only to
prevent this candidate from being reconsidered under the mistaken impression
that it has an official AE release. The closed conversion proposal is tracked
in [#194](https://github.com/Ensrick/skyrim-mod-assistant/issues/194).

## Correct source version

- The linked DDS Workshop page hosts preview build 0.3. It is a Legendary
  Edition-only preview covering 36 female NPCs.
- The same author published the complete build 0.55 on 2022-08-23. The author
  says it supersedes all earlier versions and patches and covers 78 NPCs.
- Build 0.55 remains an Oldrim/Legendary Edition, UNP-targeted release. Its
  stated resources are the Unofficial Skyrim Legendary Edition Patch, ALT2,
  Eyes Mod 2, and KS Hairdos; only textures are needed from the last three.
- Source: [DDS Workshop preview 0.3](https://www.ddsworkshop.net/npc_replacer)
  and [author's complete 0.55 post](https://boosty.to/khisartin/posts/9488539c-21b5-4ac0-bca5-61f4b556d854).

The 0.3 archive was used only as an early conversion feasibility sample. It
must not be installed or mistaken for the approved trial build.

## Feasibility evidence from build 0.3

- The archive contained 52 NIFs and 329 DDS files. The plugin held 38 NPC
  overrides plus new head parts, armor addons, armor, and texture sets.
- All 52 meshes were valid LE stream-83 NIFs. The source-built
  `nif-port-cli convert-sse --headparts` prototype produced valid SSE
  stream-100 meshes containing `BSDynamicTriShape` geometry and preserved
  shape names, vertex/triangle counts, skin state, bone lists, and normalized
  texture paths.
- A Spriggit text conversion changed the game release to Skyrim SE, replaced
  the USLEEP master with USSEP, and deserialized successfully with form version
  44. All seven USLEEP-owned package references used by that sample existed at
  the same FormIDs and record types in the installed USSEP.
- That proves a controlled port is technically possible; it does not prove the
  0.55 data is safe or that its NPC overrides are compatible with this list.

## Known risk areas

1. The author explicitly requires manual SSE eye-mesh settings in addition to
   generic NIF optimization. The final mesh audit must compare the converted
   eye shapes and shader flags with valid SSE eye meshes.
2. A straight re-save would carry old NPC records into a modern load order.
   The owned compatibility output must preserve current winning non-appearance
   fields from USSEP, Cutting Room Floor, AI/gameplay mods, outfits, inventory,
   packages, factions, and scripts while applying the intended appearance.
3. The active list uses CBBE, Reverie for women, SkySight for men, Vanilla Hair
   Remake SMP, and an NPC SMP-hair distribution layer. Build 0.55 says UNP only
   and supplies custom skin/armor records for at least some NPCs. Its exact
   body texture and outfit assumptions must be resolved locally; ALT2 must not
   be installed globally over the selected skin stack.
4. Build 0.3's dependency scan found unresolved ALT2, Eyes Mod 2, and KS
   Hairdos texture paths, confirming that the resource requirement is real.
   The private output should contain only the exact files referenced by build
   0.55 rather than installing the complete resource mods.
5. The original permissions are closed: no use or redistribution of the
   archive as a whole or in parts. Neither original nor converted assets or
   plugin data may be committed or bundled. A public pack can at most use a
   source-only local recipe that consumes downloads the user obtained from the
   author, subject to a final permissions review.

## Trial gates

- [ ] Hash, integrity-test, and inventory the complete 0.55 archive.
- [ ] Convert and semantically compare every LE mesh; validate eye shaders.
- [ ] Replace USLEEP dependencies only after reference validation against the
  installed USSEP.
- [ ] Generate an owned local compatibility plugin from current winning NPC
  semantics rather than allowing old gameplay fields to win.
- [ ] Include only exact referenced ALT2, Eyes Mod 2, and KS Hairdos resources.
- [ ] Verify all plugin links, masters, facegen paths, texture paths, and loose
  file conflicts.
- [ ] Stage the private port disabled in MO2 and record it as restricted.
- [ ] Run a disposable-profile launch check, then ask for a foreground visual
  inspection before considering it active.

## Acquired-source evidence

- NPC Replacer 0.55 archive: 2,124,466,262 bytes; SHA-256
  `0953DFDCBE3A7874F81FCD9DC2D6C309690A2A099EA3BA988AB72B339641E767`;
  7-Zip integrity test passed; 960 files and 8,703,025,460 extracted bytes.
- ALT2 CBBE 2K-4K Balanced archive: 1,716,065,409 bytes; SHA-256
  `EC607264F28DA00E8DA75157964EDA0B0B31294FDA78EB9E522E37EC7E49001C`;
  7-Zip integrity test passed. Its readme also requires permission to use or
  redistribute the archive as a whole or in parts.
- Eyes Mod 2 Main 2K and current KS Hairdos SSE archives were integrity-tested
  for dependency feasibility. They were not installed.

The conversion was abandoned. Nothing from this replacer or its dependencies
was installed or enabled in the active profile.
