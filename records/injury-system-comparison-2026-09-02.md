# Injury-system comparison: SCI, Wounds, and Underdog

**Decision:** keep all injury mechanics deferred. Simple Combat Injuries 2.1
is the cleanest technical base for a future permissioned patch; Wounds 4.0 is
the richer survival design but is not first-playthrough ready without a
combined script repair and compatibility rebuild. Underdog is an animation
anthology, not an injury engine, and does not replace either system.

This comparison corrects an earlier ambiguity: Simple Combat Injuries contains
91 **replacement animation clips**, but every one belongs to its bruised OAR
package. That is plausible because the set covers sex, movement, stance, and
equipped-weapon permutations. It does not mean there are 91 unique bruised
performances.

## Simple Combat Injuries 2.1

- Source: [Simple Combat Injuries](https://www.nexusmods.com/skyrimspecialedition/mods/104843)
- Archive: `104843-749266.7z`, SHA-256
  `98ea4e1f3bdf98ce49a3af4281a329c63d3a75f67225e95c3924d89a61842e46`
- Mechanics: player and NPC injury delivery through engine perk entry points;
  SPID for NPC distribution; SkyPatcher for four vendor tomes.
- Plugin: ESL-flagged, 63 new records, no vanilla overrides, two masters.
- Runtime: one small Papyrus script with source and no native DLL.
- Animation evidence: exactly 91 `.hkx` files, all beneath
  `meshes/actors/character/animations/OpenAnimationReplacer/SCI/00Bruises`.
  The root and package `_conditions.json` files gate the set on
  `SCI_KWDBruised`. Inspection of the plugin shows that keyword on effects in
  `SCI_SPL_Bruised`; no equivalent OAR package exists for cuts, punctures,
  broken bones, or concussion.
- Main defects for this pack: deliberately strong concussion blur/double
  vision/DOF, hard-coded aggressive chances and durations, stackable NPC cut
  bleeding, no creature-inflicted injuries, no mage-armor handling, no MCM or
  INI, and a reported Scrambled Bugs brawl interaction.
- Redistribution: restrictive. Do not publish modified records or animations
  without the author's permission.

**Verdict:** competent implementation, unsuitable stock configuration. If the
author grants permission, build a separate balance/compatibility plugin and
remove the concussion image-space modifier. This is the lowest-conflict route
of the mechanics mods examined.

## Wounds 4.0

- Source: [Wounds](https://www.nexusmods.com/skyrimspecialedition/mods/17581)
- Archive: `17581-55704.rar`, SHA-256
  `12e04f015c100b7b5cd96faddcd3c86eb4a16fcaefc4092cada7c718271470c8`
- Mechanics: cuts, bruises, broken bones, and concussions across six body
  regions and multiple severities, with treatment items and time-based
  recovery. It is player-only.
- Plugin: 536 records, not ESL-flagged, with 12 direct vanilla overrides: eight
  ingredients and four vendor/potion leveled lists.
- Runtime: seven compiled scripts with source. Player injury detection is an
  `OnHit` alias event; healing advances on recurring game-time updates rather
  than per-frame polling.
- Confirmed code defects:
  - the `OnHit` condition rejects every event with a non-null `akProjectile`,
    so arrows cannot inflict injuries despite the public description;
  - the mage-defense test repeats `MagicArmorSpell` on both sides of its OR,
    while the declared `MagicWard` property is never used;
  - current user reports describe cuts and broken arms that fail to heal.
- Two current repairs do not compose as published:
  [Optimised Scripts for Wounds](https://www.nexusmods.com/skyrimspecialedition/mods/156855)
  and [Wounds - Eternal Cuts Bug Fix](https://www.nexusmods.com/skyrimspecialedition/mods/162436)
  both replace `_W_QuestScript.pex`. The optimized player-alias script moves
  detection to PAPER `OnImpact`, but still rejects `akProjectile` and therefore
  does not repair arrow injuries.
- Redistribution: the Wounds author explicitly permits separate patches that
  require, credit, and link the original. A combined derivative replacement
  script still needs careful permission/credit treatment.

**Verdict:** the closest conceptual match for deep survival, but not suitable
unchanged. Adopting it means maintaining a tested compatibility project, not
merely forwarding a few ESP fields.

## Wounds Simplified 0.3

- Source: [Wounds Simplified](https://www.nexusmods.com/skyrimspecialedition/mods/147567)
- Archive: `147567-621322.zip`, SHA-256
  `ae451a760ee2b6a998ff32c3181790248b9c7061fcd0cd41005a3c5d467967a3`
- Standalone replacement using the `Wounds.esp` identity; five ranks, one
  general infection state, and reduced treatment detail.
- Plugin: 336 records, not ESL-flagged. It has a larger vanilla conflict
  surface than Wounds: one QA container, Cure Disease, six ingredients, and
  nine leveled lists.
- Direct source inspection found the same projectile exclusion and duplicated
  mage-armor test as Wounds 4.0.
- Permissions are more restrictive than the original.

**Verdict:** reject as the pack foundation. It is newer and smaller, but it
inherits the important detection bugs, adds conflict surface, loses the richer
survival treatment model, and is harder to maintain legally.

## Underdog Animations 3.0.2

- Source: [Underdog Animations](https://www.nexusmods.com/skyrimspecialedition/mods/51811)
- Role: broad conditional animation replacement, not persistent injuries,
  treatment, infection, or healing.
- Requirements include Open Animation Replacer, OAR Detection Plugin, and
  True Directional Movement.
- The supplied 3.0 OAR index lists nine player injured groups and nine NPC
  injured groups: jumps plus minor, medium/stumbling, and severe/hurting
  idle/walk/run behavior. These react principally to health thresholds; they
  do not create Wounds/SCI state.
- It overlaps EVG Conditional Idles and is a large general animation package,
  so adopting it only for the injured subset would be disproportionate.

**Verdict:** not a substitute for an injury engine. Revisit only as part of the
general animation-stack decision, after the OAR runtime hang gate is closed.

## Wounds animation add-on

[Wounds injury animations](https://www.nexusmods.com/skyrimspecialedition/mods/54870)
advertises more than 5,000 files. That number likewise represents an animation
matrix—body region, injury severity/treatment state, movement, equipment, and
other condition permutations—not thousands of independently authored motions.
It gives Wounds much more state-specific coverage than SCI, but inherits the
current OAR gate and reported priority/stuck-animation risks.

## Recommended sequence

1. Resolve Open Animation Replacer issue #140 and validate the already parked
   EVG Conditional Idles installation.
2. Keep SCI, Wounds, Wounds Simplified, and Underdog outside Keep until a
   mechanics choice is made and actually installed.
3. For the lower-risk route, obtain SCI patch permission and prototype a
   no-blur, tunable, non-stacking balance layer.
4. For the deeper-survival route, prototype Wounds in a disposable profile with
   one combined source-built script repair, non-overriding distribution, and a
   deterministic MCM preset. Test projectile wounds and every healing path
   before a first-playthrough recommendation.

## Verification boundary

All conclusions above are static: archives, plugin records, OAR conditions,
Papyrus source, and the Underdog OAR index were inspected. Spriggit round trips
passed for Wounds and Wounds Simplified. No injury mechanics mod was installed
or enabled, and no game launch was claimed.
