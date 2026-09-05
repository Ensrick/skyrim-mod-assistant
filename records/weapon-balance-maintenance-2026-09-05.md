# Weapon Speed Balance: current repair status and historical audit

## Superseding status — global 0.3 installed; static gates pass, runtime pending

This section supersedes the live-state and completion-status conclusions in the
historical audit below. The original findings and unchecked acceptance list are
retained as provenance, not presented as current status.

- Global 0.3 source is pinned at commit
  `043ccfdff83c4c4d492dc86daa1f62fc5ae72533`.
- The generated and installed `WeaponBalancePatch.esp` has SHA-256
  `6BFE4E47DE61A6A8B5E717213A13B992B9A8DA7B2944F5CE874CA23026F92F92`:
  **3,481 WEAP overrides**, **40 masters**, and **347 generation inputs**. The
  strict semantic audit passes with Speed as the only changed WEAP field.
- The localized output contains exactly **27 sidecars across nine languages**;
  an exact double build passes determinism checks.
- The installed global plugin is at managed plugin priority **271** (the mod
  folder remains priority 237) and runtime position **347 (last)**. The
  final-winner audit passes all **4,191
  rows** and Wuuthrad is now winning at the reviewed value.
- The separate private Lost LongSwords integration is installed; its exact
  installed-profile verifier passes **215/215** checks and all six installed
  payload hashes remain equal to the approved artifacts.
- All 32 later weapons from the historical gap are accounted for: **16 changed**,
  **13 already at target**, and **three reviewed exclusions**.
- This repair cycle found and fixed three additional engineering defects:
  localized text loss in the generated output, the empty backing-cache
  comparator, and nondeterministic string-ID assignment under parallel writing.
  The corresponding source fixes and offline regressions pass.

Final archive packaging and installed freshness pass. The complete build,
localization, input and transaction receipt is
`records/source-builds/ensrick-weapon-speed-balance.json`; the prior 0.1 receipt
is retained separately as historical evidence. All 79 original private vendor
files are bit-identical; no game Data root files changed; unrelated mod/plugin
activation and relative ordering are unchanged by the global replacement.

### Remaining acceptance and receipt fields

- Final archive SHA-256:
  `E8740E57A08319954C301A2000775C2CA5B786889068E6F49E09B0EB1D02E5BA`.
  31 payload files / 7,692,854 installed bytes; final transaction
  `20260905T224239482Z-9c692e563731` at 22:42:39 UTC.
- Canonical and installed freshness: PASS, no VFS and zero files written.
- Ledger/order/Keep gates: PASS; 194 installed Nexus IDs match 194 live Keeps.
- Game-side activation now exactly matches all 268 profile entries in order.
  Its only added active plugins are the two owned curation plugins; the old
  activation file is backed up. Two existing entries also move to the verified
  profile order: LostLongSwords active index 205 to 30 and WeaponBalancePatch
  118 to 267 (zero-based active rows). All other 264 existing rows retain their
  relative order. No launch, Steam cycling or INI changes.
- Preflight: zero failures; three warnings (Steam overlay state not
  disk-verifiable, five existing Fable-owned ledger gaps #102, and the
  temporary root claim).
- Runtime and fresh-save gameplay acceptance remain pending.
- The **848 review candidates are a review queue, not 848 exclusions**.
- Optional katana integration remains inactive and was not activated.

## Historical audit — preserved 2026-09-05 snapshot

The remainder records the initial read-only audit. Its live-state statements and
unchecked acceptance items describe that point in time, not the superseding
status above.

2026-09-05, read-only audit; repair issue #239, parent governance issue #212; related intake #237
and source PR #179. **Historical state at audit time: not fixed or regenerated
in the live profile.** The
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
- Generated September 2 against 307 enabled inputs. The originally reported
  341-plugin current-profile count omitted implicit official entries. The
  corrected complete inventory is **348 runtime plugins**, including the output,
  or **347 generation inputs**. An exact input manifest, not the count alone,
  must be used as the freshness gate.
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
