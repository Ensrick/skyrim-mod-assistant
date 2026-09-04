# Deferred combat decisions

The 0.1.0 release intentionally implements weapon speeds only.

## Recorded speed policy

The seven target values are deliberately reciprocal to the Dragonbone damage
ladder: one-handed classes target a record-level `damage * speed` index of 15,
and two-handed classes target 20. The targets are dagger `1.25`, sword `1.0`,
war axe `0.9375`, mace `0.88235295`, greatsword `0.8`, battleaxe `0.7692308`,
and warhammer `0.71428573`.

The patch operates on the current winning record, includes conventional
NPC-only weapons, and excludes utility/test/creature records whose editor IDs
contain `Dummy` or `GiantClub`. It uses standard weapon-type keywords first,
falls back only to unambiguous one-handed and greatsword animation types, skips
ambiguous two-handed-axe animation records, and reports multiple-keyword
records instead of choosing silently.

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

Deferred with locational damage. Proposed rule: killing arrows stick;
nonlethal headshots bounce; nonlethal body shots stick only at or below 50%
post-hit health. Damage is unaffected.

## Passive health regeneration

Deferred until the combat framework is selected. The intended rule removes
passive regeneration in and out of combat without disabling deliberate healing
from spells, potions, treatment, food, or an explicitly approved rest system.
