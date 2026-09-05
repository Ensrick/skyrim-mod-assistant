# Weapon Speed Balance: selection and freshness defects

2026-09-05, read-only audit; repair issue #239, parent governance issue #212; related intake #237
and source PR #179. **Not fixed or regenerated in the live profile.** The
current user asked for a numerical review before approving the new longsword
balance. Ordinary selector defects are engineering work, not a taste decision.

## Confirmed source selection defect: steel misidentified as creature weapons

`mods/weapon-balance/src/WeaponBalancePatcher/Program.cs` defines
`CreatureWeaponKeyword = FormKey.Factory("01E719:Skyrim.esm")` and excludes
every weapon carrying it. Inspection of Skyrim.esm resolves that FormKey to
**WeapMaterialSteel**, not a creature-only classification. Therefore the 759
records logged as utility exclusions cannot be treated as a valid safety count.
Ordinary steel equipment was skipped. All seven newly installed
`NW_Steel_Plate_Armors.esp` weapons carry the same material keyword and would
still be skipped by an otherwise up-to-date rebuild.

The opposite error also exists: eight unkeyworded animation-fallback records
were normalized, including Bitter Mercy, two Riekling spears, `testVorpalSword`,
Wyrmstooth fork/knife, and Vigilant invisible giant-knuckle/witch-knife records.
These require an explicit role decision or utility/creature/test exclusion;
do not blanket-classify them as ordinary human swords merely from animation.

## Installed artifact and load-order drift

- Enabled MO2 folder: `Ensrick - Weapon Speed Balance`.
- Enabled light plugin: `WeaponBalancePatch.esp`, **3,007 WEAP overrides**.
- Installed SHA-256:
  `74532E4375AC376B13EDDD7B3481E7BA01BDA3C0487062095D2070CB2765FA09`.
- Classes: dagger 420, sword 45, war axe 428, mace 763, greatsword 496,
  battleaxe 441, warhammer 414. Sword records already at 1.0 are intentionally
  absent; an absent override alone is not proof a weapon is unbalanced.
- Generated September 2 against 307 enabled inputs. The current 341-plugin
  profile includes additional plugins and the output itself. An exact input
  manifest, not the count alone, must be used as the freshness gate.
- **3,006 of the 3,007 records remain winning**. `0956B5:Skyrim.esm`, Wuuthrad,
  is later overridden by `RMB SPID - Legacy of Ysgramor - Wuuthrad.esp`, returning
  Speed to 0.7 instead of the selected battleaxe 0.7692308.
- Later new WEAP records not covered by the artifact: NordWar Steel Plate 7,
  QSSwordPack 3, Baltimore 6, Vikings 4, Lost LongSwords 12 = **32**. Some can
  already have the desired Speed; inspect rather than declare all 32 wrong.
- Generic regeneration would classify Lost LongSwords as greatswords and set
  them to 0.8. The new proposed custom class requires explicit per-FormKey
  ownership at Speed 1.0 and reviewed damage values.

## The source is not lost, but the canonical checkout lacks it

Source, tests, design and build receipt exist in the clean isolated worktree
`C:/Users/danjo/source/repos/_codex_worktrees/weapon-balance`, branch
`codex/weapon-balance-20260902`, audited HEAD `7fcf2e2`.

Principal paths: `mods/weapon-balance/README.md`, `DECISIONS.md`,
`src/WeaponBalancePatcher/Program.cs`, `BalanceRules.cs`, `settings.json`,
`tests/WeaponBalancePatcher.Tests/Program.cs`, and
`records/source-builds/ensrick-weapon-speed-balance.json`.

The installed artifact matches that build receipt. Issue #212's “no source or
design” concern should be corrected to **not integrated into the canonical
checkout/records**; the source and prior design do exist in PR #179/worktree.

## Numerical scope

This is a fixed class-Speed policy calibrated to Dragonbone
`base damage * Speed` indices of 15 (one-handed) and 20 (two-handed), not a
per-record equal-DPS patch. See `ports/lost-longswords/SEPTEMBER_BALANCE_PROPOSAL.md`
for the exact table, per-tier caveats and approval gates. Animation-rate inputs,
the two-handed game setting, attack clips, recovery, enchantments and stamina
must not be represented as measured real-time DPS. No change to the two-handed
GMST is authorized by this audit.

## Required repairs and acceptance

- [ ] Correct the steel-as-creature selector. Add a regression fixture proving
  ordinary steel equipment remains eligible.
- [ ] Replace the inadequate creature/test/utility heuristic with explicit,
  reviewed classifications; assert each of the eight observed fallback cases.
- [ ] Audit signature unique speeds (e.g. Ebony Blade, Longhammer) rather than
  flattening their identities without an explicit policy. Preserve all other
  winning fields, including current meshes, enchantments and distribution.
- [ ] Integrate source/build records into the canonical project workflow without
  discarding other assistants' uncommitted work.
- [ ] Add current input plugin hashes, activation/order and patch-rule versions
  to regeneration freshness checks; compare actual winning records after build.
- [ ] Update the current 32-later-weapon coverage inventory and Wuuthrad winner.
- [ ] Give the nine retained longswords an explicit custom-class rule after
  user numerical approval, with rejection of all four unwanted acquisition sets.
- [ ] Expand tests beyond included-record Speed: selection/exclusion coverage,
  immutable non-Speed fields, current winners, ESL flag and exact dependencies,
  custom-class precedence, deterministic build and regeneration invalidation.
- [ ] Run the normal static gates and disposable-save timing/acquisition tests
  before claiming the updated live balance complete.

No plugin, mod activation, Keep decision, input asset, or user save was modified
by this audit. Live fixes wait for the reviewed repair/integration transaction;
the engineering defects above do not require the user to diagnose them.
