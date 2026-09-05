# Lost LongSwords private integration

Approved 2026-09-05; implementation tracker [#237](https://github.com/Ensrick/skyrim-mod-assistant/issues/237).
This supersedes the July balance design. Build/deployment receipts, not this
design document, establish which artifact is installed and which tests passed.

## Owned scope

Keep the separately installed `LostLongSwords.esp`, converted meshes and textures
immutable. `Ensrick Lost LongSwords Curation.esp` is a separate private ESPFE:
nine WEAP overrides, two new leveled lists at local IDs 000800/000801, and three
master-stage leveled-list compatibility forwards. No vendor forms are compacted or
deleted. No meshes, textures, scripts or native binaries are bundled in this
overlay.

The same owned MO2 mod also contains the small
`Ensrick Lost LongSwords Stormcloak Distribution.esp`. It isolates the three
reviewed Sons of Skyrim weapon/gear lists in a later-loading plugin, so it can
legally depend on Sons of Skyrim without moving the early restoration layer.

Retained longswords use Speed 1.0, Reach 1.15, Stagger 0.9, two-handed skill,
two-handed sword animation and BothHands equipment. Their base damage is:
Iron 12; Steel, Silver, Imperial and Stormcloak 13; Orcish 14; Skyforge 16;
Ebony 18; Daedric 19. The Silver sword's script/perk and all other fields are
preserved. Weight, value and critical data are not silently recalibrated.

Dragonbone remains absent from the private base conversion. Elven, Dwarven and
Glass forms remain intact but their acquisition/recipe paths are suppressed.
The four original placed Iron/Silver weapons remain. Existing saved inventories
are not purged. Future private redesign of the four rejected models is deferred
under #237, not an authorization to restore them now.

These are Dragonbone-referenced **damage × Speed indices**, not measured DPS.
See [the approved numerical comparison](SEPTEMBER_BALANCE_PROPOSAL.md) and the
[mandatory future balancing standard](../../docs/WEAPON_BALANCING_STANDARD.md).
The global generator recognizes the nine exact custom-class records and checks
their winning private provider and damage rather than treating them as ordinary
greatswords.

## Distribution

The latest user instruction permits two exceptions to military exclusion:

| Recipient | Selection rule | Intended rate |
| --- | --- | --- |
| Ordinary Stormcloak soldier | Add Stormcloak longsword to an isolated copy of the three-entry Sons of Skyrim two-handed branch; redirect only the ordinary soldier inventory | 1/4 of that branch; about 1/12 across the ordinary three-branch weapon selection |
| Ordinary Imperial soldier | Replace only the ordinary soldier's inventory-template weapon branch with an owned choice, preserving other equipment | 1/12 at list level 5+; none below 5 |
| Guards, commanders, named/unique actors | No new military longsword distribution | Excluded |

These are leveled-list selection probabilities, not a claim that exactly every
twelfth NPC in a save will carry one. Existing inventories and scripts can affect
observed results. The faction swords must not reach the opposite military.
The other seven longswords stay out of military pools. Bandit/loot, smith,
Skyforge and Silver Hand routes are explicitly enumerated in the policy.

Direct ordinary-bandit equipment injection through `037C21:Skyrim.esm` is
deferred: the current shared graph also feeds guards, named actors and Dremora
warlocks. It is not changed merely because its editor ID says Bandit. Clean
bandit-chief equipment and bandit loot routes remain. A later targeted
No Mere Bandits integration can revisit ordinary bandit weapon selection
without redirecting the 56 shared consumers indiscriminately.

NPC replacement rules explicitly cover the ordinary Imperial root 01B547 and
its Inventory-inheriting children 041B2E/054A7A, and the ordinary Stormcloak
root 01B54B and child 054A7D. The explicit child rules cover either inventory
copying order around SkyPatcher's DataLoaded event; they do not change template
flags. This source-level precaution does not replace runtime inventory testing.

SkyPatcher configuration first removes the vendor's broad additions, then adds
only approved routes. It also removes the vendor's Hadvar/Irileth assignments,
suppresses the rejected recipes and unrelated duplicate recipes, and removes
the two old merchant-container injections while preserving later vendor stock.
The crafting selector is `filterByCobjs`, not `filterByConstructibleObjects`.
The latter is unknown to the installed parser and was rejected before deployment
because an ignored filter could make a recipe edit match every recipe. Validation
checks the installed parser and bounded selector/action pairs independently of
the generator's own expected strings.

An Imperial overhaul is **not installed by this change**. When one is adopted,
review the ordinary Imperial inventory template and weapon pool again. Likewise,
Sons of Skyrim, USSEP, distribution-framework, new equipment and load-order
changes require this compatibility/distribution audit to be revisited.

## Conflict handling

Load `LostLongSwords.esp` and then the private curation ESP early in the regular
ESP stage, before later regular-plugin winners such as Sons of Skyrim and Lux.
Do not put an ordinary ESP before master-flagged plugins or alter vendor flags.
The separate Stormcloak distribution plugin loads after Sons of Skyrim; it
does not override the shared SoS lists used by guards or commanders.
The global weapon balance output loads last after all its inputs.

The cross-master audit identifies the functional USSEP overlap at LVLI
`088515:Skyrim.esm` (`LootDraugrWeapon25`). Its forward preserves USSEP's nine
entries without the vendor's broad longsword route. Two additional vanilla
gear lists, `10FAFC:Skyrim.esm` and `10FAFD:Skyrim.esm`, restore their full
current-master contents: the original mod replaced their native Imperial
sword rather than simply adding another choice. Merely removing the custom
entry would leave those lists without a weapon. Later regular-plugin winners
still take precedence over these early compatibility records.

The Silver Hand list `017113:Skyrim.esm` is a separate, explicit weighted-slot
substitution: one of three native `10AA19` entries is replaced by the retained
Silver longsword, with six total entries in the reviewed list. Validation
allows that exact approved difference, not arbitrary non-vendor list drift.

The four CELL overlaps do **not** justify CELL overrides. WhiteRiverWatch01
0151F9 and Orotheim01 015233 have identical scalar fields. Warmaidens 01DB4E
and HelgenKeep01 05DE24 differ only in Version2 bookkeeping, which xEdit defines
as ignored Version Control Info 2. Persistent, temporary and navmesh children
are separate records/groups and survive independently. Therefore the private
patch does not add 3DNPC/Landscape masters or copy child records merely because
those plugins also touch a CELL. Existing placed-reference nudges remain a
separate documented vendor behavior, not something this patch erases.

## Reproduction and acceptance

`private-curation-policy.json` is the exact machine-readable scope.
`build-private-curation.ps1` verifies the approved proposal and immutable inputs,
generates the private plugin/configuration, and checks a two-generation Spriggit
round trip. `test-private-curation.py` performs the static payload/distribution
checks against the current profile. Run its `--help` for planned versus installed
audit modes. Install only a passing candidate through the claimed MO2 workflow,
then regenerate the global balance patch and audit actual final winners.

Runtime acceptance remains separate: use a fresh disposable character to sample
soldier inventories, guards, crafting, vendors, placements, tempering and both
animation perspectives. No successful static audit proves actual swing cadence,
stamina efficiency, menu/load stability or in-game distribution execution.

Only original policy/tool source is published. Vendor-derived ESP output remains
private unless redistribution is separately cleared; a public collection must
obtain the authorized source downloads and generate/validate the result locally.
