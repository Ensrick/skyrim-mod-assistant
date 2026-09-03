# Cloak distribution: why fur floods, why Cloaks of Skyrim never appears, and where the doubles come from

Measurement date: 2026-09-02 (evening).

Runtime: Skyrim SE `1.7.104.0` / SKSE `2.3.1`. MO2 instance `mo2-instances\skyrim-se`,
profile `Default`, 243 active plugins, 327 discoverable.

Trackers: [#200](https://github.com/Ensrick/skyrim-mod-assistant/issues/200)
(distribution), [#187](https://github.com/Ensrick/skyrim-mod-assistant/issues/187)
(unique cloaks), [#195](https://github.com/Ensrick/skyrim-mod-assistant/issues/195)
(RMB SPIDified Sons of Skyrim, held), [#189](https://github.com/Ensrick/skyrim-mod-assistant/issues/189)
(cloak warmth). Companion records: `records/cloak-layer-audit-2026-09-02.md`,
`records/cloak-install-2026-09-02.md`.

Mods involved, all installed and enabled:
[Cloaks of Skyrim 6369](https://www.nexusmods.com/skyrimspecialedition/mods/6369),
[Pelts o Plenty - Fur Pelt Gear 120726](https://www.nexusmods.com/skyrimspecialedition/mods/120726),
[RMB SPCH - Cloaks of Skyrim 116030](https://www.nexusmods.com/skyrimspecialedition/mods/116030),
[RMB SPCH - Pelts o Plenty 179354](https://www.nexusmods.com/skyrimspecialedition/mods/179354),
[RMB SPIDified - Core Framework 148689](https://www.nexusmods.com/skyrimspecialedition/mods/148689),
[Sons of Skyrim 68656](https://www.nexusmods.com/skyrimspecialedition/mods/68656),
[SkyPatcher 106659](https://www.nexusmods.com/skyrimspecialedition/mods/106659) 7.0.3.
Deliberately absent: [RMB SPIDified - Sons of Skyrim 83340](https://www.nexusmods.com/skyrimspecialedition/mods/83340) (#195).

Everything below is read off the installed plugins and config files, or computed
from them. Tooling: `records-work/cloak-dist-2026-09-02/` - `lvli.py` (LVLI/OTFT
parser), `resolve.py` (winning override per FormKey across the live load order),
`ratio.py` (entry-count table), `outfit_probe.py` (what a patched outfit already
holds), `simulate.py` (exact leveled-list probabilities). No guesses; each claim
below names the record it came from.

---

## 1. How a cloak actually reaches an NPC in this build

The SPID half of RMB distributes **keywords only**. All 39 `*_DISTR.ini` files in
`RMB SPIDified - Core Framework` contain `Keyword =` and `ExclusiveGroup =` lines
and nothing else - no `Item =`, no `Outfit =`. Nothing consumes those keywords for
cloaks in this build.

Every cloak an NPC gets therefore comes from exactly one place: the **58
`filterByOutfits` lines** in
`SKSE\Plugins\SkyPatcher\outfit\Cloaks\RMB SPID - Core Definitions.esp.ini`,
which add one RMB leveled list to one vanilla outfit each. No outfit is targeted
twice - verified by sorting the 58 targets, all unique.

Those lists then resolve through RMB's tree:

```
outfit -> RMB_Superlist_CLO_Any (B5F)  -> 4x RMB_List_CLO_CommonAny (B96) + 1x RMB_List_CLO_RareAny (B9B)
                                          B96 -> B97 ThinCommon | B98 ThinCommonDark | B99 WarmCommon | B9A WarmCommonDark
                                          B9B -> B9C ThinRare   | B9D ThinRareDark   | B9E WarmRare   | B9F WarmRareDark
outfit -> RMB_Sublist_CLO_Guard<Hold>  (B6C..B74)      -- guards, one per hold
outfit -> RMB_Sublist_CLO_Faction<X>   (B61..B6B)      -- Stormcloak, Imperial, Thalmor, ...
```

The eight leaf buckets and the guard/faction sublists are **empty in the plugin**.
They are filled at runtime by the two RMB SPCH packages' `addToLLs` directives,
and that is where the two mods collide.

## 2. The ratio, by entry count

`ratio.py`. Odds inside a leveled list are uniform over its entries, so entry
count is the odds. Dead injections (targets whose plugin is not installed) are
excluded.

| shared sublist | form | Cloaks of Skyrim | fur | CoS share |
|---|---:|---:|---:|---:|
| RMB_Sublist_CLO_FactionDawnguard | B62 | 0 | 5 | 0.0% |
| RMB_Sublist_CLO_FactionForsworn | B63 | 1 | 1 | 50.0% |
| RMB_Sublist_CLO_FactionGreybeards | B64 | 1 | 4 | 20.0% |
| RMB_Sublist_CLO_FactionImperial | B65 | 1 | 6 | 14.3% |
| RMB_Sublist_CLO_FactionNecromancers | B66 | 1 | 2 | 33.3% |
| RMB_Sublist_CLO_FactionStormcloak | B69 | 1 | 6 | 14.3% |
| RMB_Sublist_CLO_FactionThalmor | B6A | 3 | 3 | 50.0% |
| RMB_Sublist_CLO_GuardEastmarch | B6C | 1 | 7 | 12.5% |
| RMB_Sublist_CLO_GuardFalkreath | B6D | 1 | 4 | 20.0% |
| RMB_Sublist_CLO_GuardHaafingar | B6E | 1 | 4 | 20.0% |
| RMB_Sublist_CLO_GuardHjaalmarch | B6F | 1 | 3 | 25.0% |
| RMB_Sublist_CLO_GuardPale | B70 | 1 | 6 | 14.3% |
| RMB_Sublist_CLO_GuardReach | B71 | 1 | 3 | 25.0% |
| RMB_Sublist_CLO_GuardRift | B72 | 1 | 5 | 16.7% |
| RMB_Sublist_CLO_GuardWhiterun | B73 | 1 | 4 | 20.0% |
| RMB_Sublist_CLO_GuardWinterhold | B74 | 1 | 4 | 20.0% |
| RMB_Sublist_CLO_ThinCommon | B97 | 2 | 12 | 14.3% |
| RMB_Sublist_CLO_ThinCommonDark | B98 | 0 | 2 | 0.0% |
| RMB_Sublist_CLO_WarmCommon | B99 | 0 | 6 | 0.0% |
| RMB_Sublist_CLO_WarmCommonDark | B9A | 0 | 2 | 0.0% |
| RMB_Sublist_CLO_ThinRare | B9C | 2 | 14 | 12.5% |
| RMB_Sublist_CLO_ThinRareDark | B9D | 0 | 2 | 0.0% |
| RMB_Sublist_CLO_WarmRare | B9E | 0 | 8 | 0.0% |
| RMB_Sublist_CLO_WarmRareDark | B9F | 0 | 2 | 0.0% |
| **total** | | **21** | **115** | **15.4%** |

**#200's 7:1 for B6C is right and is the smaller of the two problems.** Two
things the entry count already shows:

- Pelts reaches **all eight** generic buckets; Cloaks of Skyrim reaches **two**
  (B97, B9C). A generic NPC picks a bucket uniformly, so three quarters of the
  time it lands in a bucket with no cloth cloak in it at all.
- Two injections are inert and were already known: `Cloaks - Dawnguard.esp|800`
  for the Dawnguard bucket (the plugin is not installed - the SkyPatcher log
  prints `[C] leveled Lists FE04EB62 Form not found: Cloaks - Dawnguard.esp|800`
  on every launch), and both packages' `RMB SPID - Sons of Skyrim.esp.ini` /
  `RMB SPID - NordwarUA GAR - Outfits.esp.ini` (#195).

## 3. The bigger half of the ratio: chanceNone

Entry count is not the whole story, and this is the finding that explains
*"I don't ever recall seeing the cloaks of skyrim."*

**Every Pelts o Plenty leveled list rolls `chanceNone = 0`. The Cloaks of Skyrim
lists roll 25 to 90.**

| Cloaks of Skyrim list | form | chanceNone | | Pelts list | chanceNone |
|---|---:|---:|---|---|---:|
| LitemCloaksCommon | 804 | **70** | | RMB_PoP_ListCloaksAnyShortStandard 800 | 0 |
| LitemCloaksDarkCommon | 805 | **66** | | RMB_PoP_ListCloaksAnyStandard 801 | 0 |
| LitemCloaksDarkEnch | 806 | **70** | | RMB_PoP_SublistMantlesAny 805 | 0 |
| LitemCloaksEnch | D6C | **50** | | RMB_PoP_SublistPauldronsAny 808 | 0 |
| LitemCloaksThalmor | 83F | **90** | | every per-animal superlist 80A-814 | 0 |
| LitemCloaksForsworn / Necro | 89E / 8C8 | 66 | | | |
| hold cloak lists (Whiterun, Solitude, ...) | | 25-50 | | | |

Those numbers are Cloaks of Skyrim's own, from 2017, when the mod injected
straight into vanilla leveled lists and had to gate its own rarity there. Inside
RMB the outer lists already gate rarity (`CloakChances.ini`, 35 everywhere), so
the inner roll double-dips - and only on one of the two mods.

## 4. What that actually produces (exact probabilities, before)

`simulate.py` walks the patched graph exactly: roll `chanceNone`, else pick
uniformly among entries, recurse.

| entry point | no cloak | Cloaks of Skyrim | fur | CoS share of cloaks |
|---|---:|---:|---:|---:|
| bandit / generic (B5F) | 44.7% | 0.6% | 54.8% | **1.0%** |
| common generic (B60) | 18.1% | 0.8% | 81.1% | 0.9% |
| rare generic (B7E) | 1.9% | 1.2% | 96.9% | 1.3% |
| hunter (B82) | 40.4% | 0.0% | 59.6% | 0.0% |
| guard Eastmarch (B6C) | 37.7% | 5.4% | 56.9% | 8.7% |
| guard Whiterun (B73) | 39.3% | 8.7% | 52.0% | 14.3% |
| guard Hjaalmarch (B6F) | 39.1% | 12.2% | 48.8% | 20.0% |
| faction Stormcloak (B69) | 38.1% | 6.2% | 55.7% | 10.0% |
| faction Imperial (B65) | 39.6% | 4.6% | 55.7% | 7.7% |
| faction Thalmor (B6A) | 57.2% | 10.3% | 32.5% | 24.1% |
| faction Dawnguard (B62) | 35.0% | 0.0% | 65.0% | 0.0% |

Full table in `records-work/cloak-dist-2026-09-02/tables.txt`.

**One in a hundred cloaks on a generic NPC was a Cloaks of Skyrim cloak.** The
report is accurate to the data.

## 5. The doubles: found, and it is not a leveled-list roll

`outfit_probe.py` expanded all 58 patched outfits through the live load order and
asked which ones can already produce a biped-slot-46 or slot-57 item without the
RMB injection. **Fourteen can, and all fourteen are Sons of Skyrim overrides:**

| outfit | winner | RMB adds | already contains |
|---|---|---|---|
| GuardWindhelm | NW_Sons_of_Skyrim.esp | B6C | `0_Windhelm_Guards_ARMORS` -> 4 cloaks |
| GuardFalkreathOutfit | NW_Sons_of_Skyrim.esp | B6D | `6_Falkreath_Armor_SET` -> 3 |
| ArmorHaafingarAllOutfit | NW_Sons_of_Skyrim.esp | B6E | `3_Solitude_Armor_SET` -> 1 |
| ArmorHaafingarAllOutfitNoHelmet | NW_Sons_of_Skyrim.esp | B6E | `0_Solitude_Cloak` |
| GuardOutfitHjaalmarch | NW_Sons_of_Skyrim.esp | B6F | `7_Morthal_Armor_SET` -> 1 |
| GuardPaleOutfit | NW_Sons_of_Skyrim.esp | B70 | `5_Dawnstar_Armor_SET` -> 3 |
| ReachHoldGuardOutfit | NW_Sons_of_Skyrim.esp | B71 | `4_Markarth_Armor_SET` -> 1 |
| GuardOutfitRift, ...NoShield | NW_Sons_of_Skyrim.esp | B72 | `2_Riften_Armor_*` -> 2 |
| GuardWhiterunOutfit, ...NormalHelmet, ...NoHelmet | NW_Sons_of_Skyrim.esp | B73 | `1_Whiterun_Armor_SET` -> 4 |
| GuardWinterholdOutfit | NW_Sons_of_Skyrim.esp | B74 | `1_Winterhold_Armor_Light` -> 1 |

The other 44 patched outfits hold no cloak-slot item, so a bandit, a Thalmor
soldier or a hunter gets exactly one cloak. Guards get two.

The slots make it visible rather than harmless. **Every Pelts o Plenty item -
all 109 cloaks, mantles and pauldrons - is on biped slot 57**, and the ten fur
hoods on 31 (`audit/esp.py` over `Pelt Cloaks.esp`: 109 at slot 57, 10 at 31, 1
at 32). **Every Sons of Skyrim hold cloak is on slot 46** (+40 tail), including
`0_Fur_Collar_Brown` and `0_Fur_Collar_Brown_P`, which are fur. So a Whiterun
guard can wear a Sons of Skyrim fur collar on 46 and a Pelts fur cloak on 57 at
the same time; when RMB's roll comes up a Cloaks of Skyrim cloak instead, that
one is also slot 46 and collides with the Sons of Skyrim cloak, so one is worn
and one is carried. Both halves of the report are the same mechanism.

This is precisely the merge `RMB SPIDified - Sons of Skyrim` 83340 performs and
which this build does not have (#195): its `00 Shared` configs merge the hold
cloak sublists into Sons of Skyrim's own guard cloak lists instead of adding a
second list beside them. Both SPCH packages ship those merge files, and the
SkyPatcher log skips both every launch because `RMB SPID - Sons of Skyrim.esp` is
absent.

## 6. Three vendor defects found on the way

1. **`Cloaks - Dawnguard.esp|800`** does not exist here; the merged list survived
   as `Cloaks - RMB SPCH.esp|984` (`DLC1LItemCloaksDawnguard`, 2 entries). The
   Dawnguard bucket was 100% fur as a result.
2. **The dark buckets.** RMB's Cloaks of Skyrim config puts `LitemCloaksDarkCommon`
   and `LitemCloaksDarkEnch` into `ThinCommon`/`ThinRare` and leaves
   `ThinCommonDark`/`ThinRareDark` entirely to fur.
3. **Three duplicate Pelts lists.** `RMB_PoP_ListCloaksAnyShortStandardTrimmed_UNUSED`
   (807), `...AnyStandardTrimmed_UNUSED` (806) and `...AnyHeavyTrimmed_UNUSED`
   (802) hold entry lists identical, member for member, to 800, 801 and 803. Where
   both are injected into the same bucket the duplicate only doubles that branch's
   weight.

Also confirmed while measuring: `RMB SPID - Core Definitions.esp` has **zero
override records** (1123 new: 773 LVLI, 349 OTFT, 1 KYWD), so none of this is a
record conflict; it is entirely runtime SkyPatcher behaviour.

## 7. The fix, and what it produces

`Ensrick - Cloak Distribution Balance`, one SkyPatcher config at
`SKSE\Plugins\SkyPatcher\leveledList\zz Ensrick Cloak Balance\`. SkyPatcher walks
`leveledList\` root files first and then sub-directories in name order, so `zz ...`
is processed last - confirmed in `SkyPatcher.log` 2026-09-02 23:18:28, after
`Headgear\` and every RMB config. No vendor file is touched.

Four dials, each one number:

| # | dial | default | what it does |
|---|---|---:|---|
| 1 | **GUARDS** - `chanceNone` on B6C..B74 | **100** | the RMB guard roll always returns nothing, so a guard wears exactly one cloak, the Sons of Skyrim one. 0 restores RMB's second cloak. Delete the block if 83340 is ever adopted. |
| 2 | **RATIO** - `chanceNone` on the 20 Cloaks of Skyrim lists | **0** | puts cloth on the same footing as fur. Raise to make cloth rarer; 70 is roughly the vendor default. |
| 3 | **FREQUENCY** - `chanceNone` on the outfit-facing lists | **55** | share of covered NPCs with no cloak. RMB ships 35. |
| 5 | **WARM PARITY** - 4 `addToLLs` | **on** | puts Cloaks of Skyrim into the four warm buckets. Comment out to leave warm all-fur. |

Section 4 is structural, not a dial: the Dawnguard repoint, the two dark-bucket
entries, and nine `removeFromLLs` lines dropping the duplicate `_UNUSED` lists
from the buckets that also carry the original.

A fifth defect was fixed while setting the frequency dial: RMB puts 35 on **both**
`B5F` and its children `B96`/`B9B`, so a generic NPC rolled the same gate twice
and came out 58% cloakless rather than 35%. Only the outfit-facing lists are
gated now; `B96`, `B9B`, `B97` and `B99` are set to 0.

### Result

| entry point | no cloak | Cloaks of Skyrim | fur | CoS share of cloaks |
|---|---:|---:|---:|---:|
| bandit / generic (B5F) | 55.0% | 10.7% | 34.3% | **23.8%** (was 1.0%) |
| common generic (B60) | 55.0% | 10.8% | 34.2% | 24.1% (was 0.9%) |
| rare generic (B7E) | 55.0% | 10.2% | 34.7% | 22.8% (was 1.3%) |
| hunter (B82) | 55.0% | 10.4% | 34.6% | 23.0% (was 0.0%) |
| every guard (B6C..B74) | 100.0% | - | - | one Sons of Skyrim cloak, no second |
| faction Stormcloak (B69) | 55.0% | 9.0% | 36.0% | 20.0% |
| faction Imperial (B65) | 55.0% | 9.0% | 36.0% | 20.0% |
| faction Thalmor (B6A) | 55.0% | 27.0% | 18.0% | 60.0% |
| faction Forsworn (B63) | 55.0% | 22.5% | 22.5% | 50.0% |
| faction Necromancer (B66) | 55.0% | 15.0% | 30.0% | 33.3% |
| faction Greybeard (B64) | 55.0% | 11.2% | 33.8% | 25.0% |
| faction Dawnguard (B62) | 55.0% | 9.0% | 36.0% | 20.0% (was 0.0%) |

Thalmor at 60% and Forsworn at 50% are the two the defect fixes swing furthest,
and both read correctly: the Thalmor bucket now drops the duplicate fur branch
and keeps three cloth lists, and the Forsworn bucket was already 1 goat pelt to
1 Forsworn cloak.

### The one thing the numbers assume

SkyPatcher applies configs in file order and a later `chanceNone` replaces an
earlier one. The processing order is proven from the log; **last-write-wins for
`chanceNone` is not** - it cannot be read off disk. If it turned out to be
first-write-wins, dials 1-3 would be no-ops and the four `addToLLs`/nine
`removeFromLLs` lines would still apply. The first play session settles it: if
guards still carry two cloaks, that assumption was wrong.

## 8. Verification

`records/launch-verify-20260902-231840.md` - **PASS**, main menu 32.0 s, save
loaded 40.4 s, 243 active plugins, 36 SKSE plugins checked, 0 refused, no crash
log. `SkyPatcher.log` shows all three new configs loaded and processed with no
errors, and the two leveled-list ones processed after every RMB config.
`install_mod.py --verify` 0 problem(s); `verify_order.py` CLEAN;
`file_conflicts.py` reports no collision on any of the three new files.

In-game behaviour is **unverified**: proving a distribution change needs NPCs
walked past, not a save load.
