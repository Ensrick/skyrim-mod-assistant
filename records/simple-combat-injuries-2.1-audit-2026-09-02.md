# Simple Combat Injuries 2.1 audit

**Decision:** conditional hold. Do not install the stock mod in the active
profile and do not add it to Keep. It is a technically sound, modern base, but
its current balance and visual behaviour do not meet this modpack's design
rules.

## Artifact and method

- Nexus: [Simple Combat Injuries](https://www.nexusmods.com/skyrimspecialedition/mods/104843)
- Version/file: 2.1, main file 749266, uploaded 2026-05-06
- Local audit archive: `mo2-instances/skyrim-se/downloads/104843-749266.7z`
- Size: 441,590 bytes
- SHA-256: `98ea4e1f3bdf98ce49a3af4281a329c63d3a75f67225e95c3924d89a61842e46`
- The archive was extracted outside MO2's `mods` directory and was not
  installed or enabled.
- `Simple Combat Injuries.esp` completed a Spriggit serialize/check
  round-trip. Records, SPID/SkyPatcher configuration, OAR conditions and the
  supplied Papyrus source were then inspected directly.

## What is good

- The plugin is ESL-flagged, has only `Skyrim.esm` and `Dawnguard.esm` as
  masters, and adds 63 new records without overriding vanilla records.
- The payload is small: 98 files, comprising 91 HKX animations, two INIs, two
  JSON files, one ESP, one compiled Papyrus script and its source. It contains
  no native DLL and no BSA, so there is no game-runtime-version coupling.
- The sole script only applies and removes the concussion image-space modifier
  on the player. The injury mechanics themselves use engine perk entry points.
- SPID distributes the controller perk to NPCs. A start-game-enabled, run-once
  quest gives the player the corresponding ability. SkyPatcher injects only
  four Restoration tomes and avoids direct leveled-list overrides.
- Blocking suppresses injuries, armor keywords affect injury chance, and the
  conditions exclude several non-biological targets plus vampire/werewolf
  forms. The author is still maintaining the mod and moved distribution to
  modern tools in 2.1.

## Reasons not to adopt it unchanged

1. **It violates the no-screen-distortion rule.** `SCI_ConcussionIMOD`
   explicitly uses blur radius, double vision, motion blur, radial blur and
   depth-of-field values. `ConcussionIMODScript` cross-fades that modifier in
   when the concussion starts and removes it only when the long concussion
   effect ends. This is not an incidental vanilla hit flash.
2. **The chances and durations are hard-coded and aggressive.** There is no
   MCM or INI. Examples from the plugin are an 80% bruise chance after a
   qualifying unblocked hit, 99% piercing chance with clothing/no armor, and a
   99% broken-bone chance when unarmored. Bruises last 30 minutes, piercing
   debuffs 60 minutes and broken bones two hours.
3. **Cuts are intentionally stackable on NPCs.** A July 2026 Nexus report says
   the stacking bleed can trivialize combat. That follows from the inspected
   design rather than being only a speculative conflict.
4. **Animation coverage is much narrower than the injury system.** All 91 OAR
   files share the single `SCI_KWDBruised` condition. Concussions, cuts,
   piercing wounds and broken bones have no distinct animation state, and the
   bruised set is broad but not complete for every weapon/movement family.
5. **Creature injuries and mage armor are absent.** The author's own future
   plans list both. The current weapon-keyword conditions do not make animals
   inflict injuries, while armor handling is based on worn armor/clothing
   keywords rather than effective magical armor.
6. **There is a live integration hazard with Scrambled Bugs.** A user traced a
   brawl failure to `perkEntrypoints.castSpells=true` and reported that setting
   it false resolved the problem. Scrambled Bugs is parked in this profile now,
   but the conflict must be treated as a gate if it returns.
7. **The 2.1 plugin retains authoring residue.** Three old weapon-speed/damage
   magic effects are unreferenced after the 2.1 rebalance, and the internal
   broken-bone hit spell carries a suspicious `BaseCost: 80414`. These are not
   proven runtime failures, but they show incomplete cleanup.
8. **The published figures and plugin are not identical.** The page says a
   regular cut is 1 HP/second for 15 seconds; the shipped effect is 0.5
   HP/second for 30 seconds. The total damage is the same, but the timing and
   stacking behaviour are not.
9. **An injury magic effect refers directly to vanilla `GetHit` image-space
   data.** The current no-blur override may neutralize it through the winning
   record, but that must be verified in the final load order; the reference is
   unnecessary for this build's stated visual policy.

## Packaging and patch boundary

The Nexus permissions prohibit reupload, asset reuse and modification without
the author's permission. The original archive therefore cannot be bundled or
silently edited. A separately distributed compatibility/balance plugin that
requires the original may be possible, but permission should be obtained before
assuming that author-owned records or animations can be redistributed in any
derived form.

## Recommended route

Keep EVG Conditional Idles as the current generic wounded-animation layer once
Open Animation Replacer issue #140 is solved. Hold Simple Combat Injuries as a
reference/candidate, not as an installed mod. Reconsider it only if either:

- the author adds tunable chances, a no-visual-effects option, safer NPC bleed
  behaviour and the missing compatibility coverage; or
- the author permits a separate Ensrick balance/compatibility patch that
  removes every screen effect and retunes the probabilities and durations.

If neither occurs, an Ensrick-owned injury engine is the cleaner long-term
route because the existing archive's restrictive permissions and hard-coded
design make it a poor foundation for a public, curated pack.

## Verification status

Static audit only. Spriggit round-trip passed; no game launch was warranted
because Simple Combat Injuries was not installed and EVG remains parked behind
the unresolved OAR runtime gate.
