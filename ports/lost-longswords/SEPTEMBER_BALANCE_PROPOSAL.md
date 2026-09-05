# Lost LongSwords: September balance and private integration proposal

**Follow-up:** The user approved this proposition on 2026-09-05 and requested
implementation. This document preserves the pre-approval analysis below;
deployment and verification status belong to the subsequent build/install
receipt. See [the reusable standard](../../docs/WEAPON_BALANCING_STANDARD.md).
The [private integration design](PRIVATE_INTEGRATION.md) records the audited
implementation, including isolated soldier lists and rejected unsafe shared
distribution routes. The proposal JSON remains the immutable approval input;
its historical status is not the current installation receipt.

2026-09-05; [issue #237](https://github.com/Ensrick/skyrim-mod-assistant/issues/237).
User requested the numbers **before approval**. No balance, distribution,
exclusion, Keep, live profile, or game-launch changes have been made in this
review. The JSON beside this report is a proposal, not an installed patch.

## The answer and the important qualification

A hypothetical Dragonbone longsword with **base damage 20 and Speed 1.0** has
`20 * 1.0 = 20`. It can remain a genuine `TwoHandSword`/`TwoHanded` weapon,
using both hands and the two-handed sword animations/perks. Its Dragonbone
model does not need to be included to use that numerical design reference.

Here and in the old balance patch, `damage * Speed` is a **balance index**, not
a measured number of points of health removed per real-world second. `Speed`
scales animation playback. Different animations, attack sequences, hit-event
timing, recovery, power attacks, buffs, armor and enchantments affect actual
damage throughput. Matching the one-handed sword's numeric `1.0` does not prove
that the two-handed animation has the same swing interval or recovery window.
Do not reclassify it as one-handed to manufacture that equivalence.

There is also a separate `fWeaponTwoHandedAnimationSpeedMult` setting. The
[Comprehensive Attack Rate Patch implementation](https://github.com/NoahBoddie/ComprehensiveAttackRatePatch/blob/main/src/Main.cpp)
multiplies the actor's effective rate by that setting for two-handed sword/axe
animation types, then by the weapon's Speed. This is implementation evidence
for the distinction, **not a recommendation to install CARP**. The vanilla
setting is 1.5; 1.5 times 1.0 still does **not** mean 1.5 hits per second.
The installed-plugin/config audit found no override of that setting; runtime
memory was not inspected. This common multiplier cancels when comparing two
weapons using the same two-handed sword animation, but cannot establish a
cross-handed 15-versus-20 real-DPS ratio.
Compare clip durations and hit/recovery events, not just that scalar. The
vanilla Ebony Blade demonstrates that a Speed-1.0 two-handed sword is valid;
its current global-patch treatment must be checked separately.

## Dragonbone comparison

Numbers checked against the local Dawnguard master and installed
`WeaponBalancePatch.esp`. “Selected” is the current global class policy; the
longsword row is a new proposal. Base damage is untempered and excludes skill,
perks, enchantments and target mitigation. Ranged weapons are outside this
melee-speed policy.

| Weapon | Base damage | Vanilla Speed | Vanilla index | Selected Speed | Selected index |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dagger | 12 | 1.30 | 15.60 | 1.250000 | 15.00 |
| Sword | 15 | 1.00 | 15.00 | 1.000000 | 15.00 |
| War axe | 16 | 0.90 | 14.40 | 0.937500 | 15.00 |
| Mace | 17 | 0.80 | 13.60 | 0.882353 | 15.00 |
| Greatsword | 25 | 0.70 | 17.50 | 0.800000 | 20.00 |
| Battleaxe | 26 | 0.70 | 18.20 | 0.769231 | 20.00 |
| Warhammer | 28 | 0.60 | 16.80 | 0.714286 | 20.00 |
| **Longsword, hypothetical and excluded** | **20** | n/a | n/a | **1.000000** | **20.00** |

Exact class targets are `15/12`, `15/15`, `15/16`, `15/17`, `20/25`,
`20/26`, `20/28`. Float storage accounts for the last-digit differences in
the binary. The dagger currently uses the earlier 1.25 cap: 15, not 15.6.
Keeping vanilla 1.30 instead would retain a 15.6 index and is not the current
selected policy.

The 15/20 targets hold **at Dragonbone tier**, not exactly at every tier.
For example, the standard iron sword's 7 damage produces index 7 at Speed 1;
fixed class speeds do not turn it into a 15-index weapon. Fixed class speeds
also do not guarantee exact equality among sword/axe/mace at each lower tier,
because their underlying damage progression is not proportional.

The existing Dragonbone longsword source record, removed from the installed
port, was **22 damage, 0.8 Speed**. Merely changing it to Speed 1.0 would give
22, not 20: the proposed class requires a damage change as well.

## Material progression: proposed nine retained weapons

Use the same class Speed at every ordinary material tier, not a different
Speed that makes an iron weapon equal a Dragonbone weapon. That preserves
equipment progression. Weapon records store integer base damage, so small
rounding/tier compromises are unavoidable.

Recommended longsword rule: **vanilla one-handed sword damage + 5**, Speed
**1.0**. It reaches Dragonbone 20, preserves distinct ordinary material tiers,
and stays close to the corresponding greatsword's `damage * 0.8` index.
Simply rounding `0.8 * greatsword damage` makes steel and orcish both 14;
the proposed rule avoids that unwanted collapse.

| Retained longsword | Installed damage / Speed | Proposed damage / Speed | Equivalent greatsword index | Difference |
| --- | ---: | ---: | ---: | ---: |
| Iron | 13 / 0.80 | 12 / 1.00 | 12.0 | 0.0% |
| Steel | 15 / 0.80 | 13 / 1.00 | 13.6 | -4.4% |
| Orcish | 16 / 0.80 | 14 / 1.00 | 14.4 | -2.8% |
| Ebony | 20 / 0.80 | 18 / 1.00 | 17.6 | +2.3% |
| Daedric | 22 / 0.80 | 19 / 1.00 | 19.2 | -1.0% |
| Skyforge Steel | 18 / 0.80 | 16 / 1.00 | 16.0 | 0.0% |
| Silver | 15 / 0.84 | 13 / 1.00 | 13.6 | -4.4% |
| Imperial, proposed steel grade | 15 / 0.80 | 13 / 1.00 | 13.6 | -4.4% |
| Stormcloak, proposed steel grade | 17 / 0.80 | 13 / 1.00 | 13.6 | -4.4% |

Imperial and Stormcloak have no direct vanilla greatsword equivalent here;
steel is a **proposed** comparator, not a discovered fact about author intent.
Their acquisition role is still a decision because the user excludes both
armies from distribution. Their inclusion does not authorize assigning them
back to soldiers. Skyforge belongs with its specialist smith/Companions access;
Silver keeps its existing silver effect and needs a specialist acquisition
route rather than indiscriminate bandit distribution.

Keep original reach **1.15** and stagger **0.90** as the lighter two-handed
niche (greatswords generally 1.30/1.10). The proposal retains weights, prices,
models, silver behavior and recipes unless a specific defect or integration
decision calls for a separate change. Critical-damage fields and power-attack
stamina require explicit audit; neither is guaranteed balanced by this table.

Faster per-hit enchantment application and flat tempering bonuses still favor
the fast weapon. At an equal base index the longsword lands smaller, more
frequent hits than a greatsword using the same animation family. Its lower
reach/stagger and loss of the free hand are meaningful costs, but this is not
proof that every build, power attack or stamina efficiency is equal. Keep
those trade-offs visible when approving the baseline.

## Current-patch completeness: it is not complete

- The global patch is enabled and has 3,007 WEAP overrides, but was generated
  on September 2 against 307 enabled input plugins. The current profile has
  341 enabled plugins. New additions require a fresh, reviewed generation.
- Lost LongSwords has **no FormKeys in that patch** and retains the July
  statistics. Its active converted ESP hash is
  `436E46C2BE9D25B0FD726271712421265C6309DB8C69D8A8AE8C7FF06EC5B54D`.
- The global generator assigns one Speed per class. It does not give every
  weapon the same final damage index; that is intentional for material tiers.
- **Confirmed selector bug:** its purported creature keyword
  `01E719:Skyrim.esm` is actually `WeapMaterialSteel`. Ordinary steel weapons
  are incorrectly skipped. A fresh generation without fixing that bug would
  still be incomplete.
- Its animation-type fallback also caught eight unkeyworded/special records,
  including Riekling spears, invisible creature weapons and test/utility items.
  They need explicit exclusion/special-case review before regeneration.
- Special and unique weapon speeds must be inventoried, not assumed uniform
  or safe to overwrite. Their signature properties and later mod winners are
part of the global-patch follow-up under
[#239](https://github.com/Ensrick/skyrim-mod-assistant/issues/239), parent #212.
The current output reduces the Longhammer from 0.8 to 0.714286 and the Ebony
Blade from 1.0 to 0.8, removing their relative speed identities within their
now-normalized classes. A later Wuuthrad patch also overwrites its target.
- A future generic rebuild must not overwrite the longswords back to the
  greatsword target 0.8. Give the nine exact FormKeys their own declared class
  or apply/verify the private override after regeneration. Never rely only on
  an incidental load-order position.

## Exclusions, distribution and save safety

Confirmed user exclusion set: **Dragonbone, Elven, Dwarven (Dwemer), Glass**.
Dragonbone is already absent from the installed port. The other three remain
present today; the new exclusion layer has not been activated while numerical
approval is pending. Nine weapon records/eight distinct models would remain
usable; Skyforge Steel shares the Steel mesh.

The CK-native solution is an ordinary override patch: remove acquisition
entries from appropriate LVLIs, suppress unwanted crafting/tempering recipes,
undo vendor actor/inventory assignments while forwarding other mods' winners,
and suppress excluded placed items where present. Keep existing weapon FormIDs
and the immutable private asset layer; do not delete or compact the source
plugin and break existing saves. Existing acquired items and already-generated
NPC inventories do not automatically vanish. Use a disposable fresh save for
acceptance; a live-save cleanup is a separate migration, not a hidden script.

Observed source routes that must be reviewed/neutralized:

- `CWSoldierImperialGear`, `CWSoldierImperialGearNoTorch`,
  `CWSoldierImperialGearNoTorchNoBow`, `LItemSoldierSonsWeapon2H`;
- `LootCWImperialsWeapon100/15`, `LootCWSonsWeapon100/15`;
- shared `LItemWeaponAny2H`, `LItemWeaponAny2HSpecial`, `LItemWeaponAny2HTown`;
- direct Hadvar and Irileth edits; blacksmith chest overrides;
- source-specific nested longsword lists, crafting/tempering records and
  placed-reference data beneath four CELL headers.

Do **not** simply forward the old source records: its Solitude/Windhelm
blacksmith edits can undo Sons of Skyrim and its draugr loot can undo USSEP.
Do **not** equate “edited a CELL header” with “merged the placed references.”
No layout/navmesh changes are proposed. Any actual placement ambiguity goes to
visual/CK review rather than a fabricated merge.

Proposed constrained integration: tier-gated ordinary bandit/bandit-boss
two-handed pools and ordinary blacksmith/loot access, with rare high-tier
equipment and separate Skyforge/Silver access. Trace **all incoming paths**
before accepting a list as non-military. Shared lists are not faction filters;
if an eligible list also feeds protected actors, isolate that route instead.
Guards, Imperials and Stormcloaks are negative acceptance tests, not optional
preferences. No additional named NPC assignment or monster pool is approved
merely by this plan. Exact rarity and the two faction-looking variants' role
remain visible decisions, not silently chosen constants.

## Acceptance and open decisions

1. User approves the numerical baseline and lighter/faster two-handed trade-off.
2. Resolve the Imperial/Stormcloak swords' non-military acquisition role;
   confirm final rarity with the broader equipment distribution project.
3. Build separate private ESP-FE curation/integration layer; record master and
   rule dependencies, preserve vendor bytes and existing FormIDs.
4. Assert all nine stats and every excluded weapon's acquisition paths;
   prove no protected actor has a route into the injected lists. Reconcile
   current winners and regenerating global balance/other generated patches.
5. Disposable-save timing: first/third person, standing/moving, repeated light
   attacks and power attacks, NPC use, reach/contact, sheathing, enchantment
   application rate and stamina expenditure. Same numeric index is not a
   substitute for these tests.
6. Forge/temper/merchant/loot tests and saved-inventory migration checks.
   Document results before claiming integrated or gameplay-verified.

Future private-art task: revisit the four rejected models, including possible
private remeshing/retexturing, only on a later request. Preserve original
archives as provenance. No model edits or distribution rights are assumed.

## Public conversion route

For TCOSS, the companion `ports/chronicles-of-steel/convert.py` now provides a
headless original-ZIP front end around the validated equipment review recipe.
It is explicitly a review prototype, not a finished balanced port. Its fourteen
safety/preflight tests and real-archive/toolchain read-only preflight pass. The
backend was structurally tested in the preceding TCOSS audit; the new wrapper
has not re-run a redundant multi-gigabyte conversion. Remaining TCOSS balance,
three missing mip chains, distribution and runtime gates remain on #238.

The modlist should distribute original tooling/recipes and require each user
to obtain the original archives, then generate private local assets/plugin
data. It must not bundle the restricted assets or represent user-side
conversion as permission to publish them. Lost LongSwords still uses its own
mod-specific recipe; this is not yet one universal converter.
