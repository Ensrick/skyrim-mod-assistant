# Deferred combat decisions

The 0.1.0 release intentionally implements weapon speeds only.

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
