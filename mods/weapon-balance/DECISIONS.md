# Deferred combat decisions

The 0.3.0 generator intentionally implements weapon speeds only. It follows
the repository-wide `docs/WEAPON_BALANCING_STANDARD.md`.

## Recorded speed policy

The seven ordinary-class targets are deliberately reciprocal to the Dragonbone damage
ladder: one-handed classes target a record-level `damage * speed` index of 15,
and two-handed classes target 20. The targets are dagger `1.25`, sword `1.0`,
war axe `0.9375`, mace `0.88235295`, greatsword `0.8`, battleaxe `0.7692308`,
and warhammer `0.71428573`. The approved Lost Longsword custom class uses speed
`1.0`, anchored to a hypothetical 20-damage Dragonbone longsword.

The patch operates on the current winning record and includes conventional
NPC-only weapons. Generic records require exactly one recognized type keyword
and its coherent animation type. Unkeyworded/mismatched records are
default-denied; there is no animation-only fallback. `Dummy`, `GiantClub`, and
`NotUsedInNormalCombat` remain utility guards. Exact reviewed rules preserve
both Ebony Blade records and The Longhammer, classify nine Lost Longswords,
and exclude their three rejected forms. The Lost Longsword rules pin the
private curation winner and approved damage so generation fails closed if the
damage layer is absent or stale. They also require the Greatsword type keyword,
two-handed skill, two-hand sword animation, and `BothHands` equip type so the
custom class cannot silently inherit one-handed behavior or lose perk routing.

## Localization and artifact integrity

A speed-only override must not discard source translations or turn a missing
description into authored text. The full-profile 0.2.0 candidate exposed this
with Rulnik's Dagger from `ccKRTSSE001_Altar.esl`: nine source languages became
English only. That candidate was rejected before deployment. Version 0.3.0
uses localized output and preserves source-language content with explicit
tests for mixed localized/inline-English inputs and empty descriptions.

The output string tables are part of the artifact, not optional packaging
extras. Deterministic builds, installed-winner checks, and read-only freshness
checks cover them. Relevant source string tables and archives containing those
tables are also input dependencies: unchanged ESP bytes alone cannot prove
that a previous translation-preserving build is current.

## Armor matchups

Deferred until the locational-damage layer is selected. Proposed design:

- swords/greatswords: +10% against a struck location not protected by light or
  heavy armor;
- war axes/battleaxes: +10% against light armor;
- maces/warhammers: +10% against heavy armor;
- daggers: no matchup bonus.

Before implementation, decide whether the target's struck body location or its
torso armor defines the matchup, and audit stacking with Bladesman/Deep Wounds,
Hack and Slash/Limbsplitter, and Bone Breaker/Skull Crusher.

## Projectile attachment

Outside this generator's scope; implementation and current acceptance belong
to the separate projectile project. The requested rule is: killing arrows stick;
nonlethal headshots bounce; nonlethal body shots stick only at or below 50%
post-hit health. Damage is unaffected.

## Passive health regeneration

Deferred until the combat framework is selected. The intended rule removes
passive regeneration in and out of combat without disabling deliberate healing
from spells, potions, treatment, food, or an explicitly approved rest system.
