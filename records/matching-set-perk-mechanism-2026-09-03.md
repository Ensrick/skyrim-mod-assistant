# How vanilla implements a full-armour-set bonus

Investigated 2026-09-03, from `Skyrim.esm` directly (raw CTDA decode of the
record plus a keyword EditorID dump through the pinned record CLI). No mod
involved, nothing installed.

**Why this exists:** the user was asked by someone how to grant a perk for
wearing a full set of glass armour, advised in an earlier session to write a
Papyrus script, and then corrected by a third party who said vanilla does it
with conditions on a perk entry point. This record settles which is right, with
the actual game data, so the answer is checkable rather than recalled.

## The record

`MatchingSet`, FormKey **`051B17:Skyrim.esm`**, display name "Matching Set".
Effect type `PerkEntryPointModifyValue`. It carries **11 CTDA conditions**,
decoded from the raw subrecords:

| # | operator | function | parameter | value |
|---|---|---|---|---|
| 1 | Equal | 448 (`HasPerk`) | perk `00051B1B` | 1.0 |
| 2 | Greater-or-equal | 277 (`GetBaseActorValue`) | actor value `0x0C` | 70.0 |
| 3-11 | Equal, **OR**-chained | **722** | one armour keyword each | **4.0** |

The nine keywords in conditions 3-11, resolved:

```
0x0006BBD6  ArmorMaterialDragonscale
0x0006BBD9  ArmorMaterialElven
0x0006BBDB  ArmorMaterialLeather
0x0006BBDC  ArmorMaterialGlass
0x0006BBDD  ArmorMaterialHide
0x0006BBDE  ArmorMaterialScaled
0x000AC13A  ArmorMaterialStormcloak
0x0010FD61  ArmorNightingale
0x0010FD62  ArmorDarkBrotherhood
```

## What this means

Function **722 takes a keyword and is compared against 4** - it returns a
**count of worn apparel carrying that keyword**, not a boolean. That is
`WornApparelHasKeywordCount`. So the whole "full set" test vanilla uses is a
single condition:

```
WornApparelHasKeywordCount( ArmorMaterialGlass ) == 4
```

`ArmorMaterialGlass` is literally condition 6 of the vanilla perk. The exact
question asked - "a perk if you wear a full set of glass armour" - is already
solved in the base game, declaratively, with one condition and no script.

*Caveat on the function name:* the index-to-name mapping is inferred from the
data shape (a keyword-typed parameter compared against a count of 4, inside the
Matching Set perk) plus the documented existence of
`WornApparelHasKeywordCount`. The numeric index was decoded from the file; the
name was not read from a decoded function table. Everything else here is
measured.

## Consequence for the advice given

`WornHasKeyword` genuinely cannot express a full set - it is true if *any* worn
item carries the keyword. That part of the earlier advice was correct. But the
conclusion drawn from it, "so you'll probably want a script", does not follow,
because a different native condition function does exactly this job.

The Papyrus approach works, and the Creation Kit setup notes given alongside it
were accurate (`bAllowMultipleMasterLoads`, SKSE sources needing to be present
for `GetWornForm` to resolve, unfilled properties, quest not Start Game
Enabled - all real failure modes). It is not broken advice. It is the heavier
tool, and it costs:

- a hard **SKSE dependency**, since `GetWornForm` is SKSE, not vanilla Papyrus;
- Papyrus handlers firing on **every equip and unequip**;
- a `ReferenceAlias` script **baked into every save**.

None of which the vanilla mechanism needs.

## Credit, stated correctly

This record verifies an answer other people gave; it did not originate it.

- **TheScatCat, 2026-09-01,** posted a Creation Kit screenshot of a Perk Entry
  whose condition list shows `WornApparelHasKeywordCount ... == 4.00` five
  times, OR-chained under `HasPerk 'MatchingSet'`, driving
  `Modify Armor Rating -> Multiply Value 1.20`. The keywords are the Dragonborn
  light set: `DLC2ArmorMaterialBonemoldLight`, `...ChitinLight`,
  `...NordicLight`, `...StalhrimLight`, `DLC2ArmorMaterialMoragTong`. The
  function name was therefore already on screen, before anyone named it in text.
- **km816, later,** named the function explicitly and linked the UESP page.
- This record's contribution is narrow: confirming vanilla's base-game record
  (`051B17`) uses the same pattern with the nine base keywords, and the exact
  comparison value.

## The ability route, from TheScatCat's second screenshot

`DLC2dunKolbjornSetAbility` is Type `Ability`, Casting `Constant Effect`, and
the condition sits on the **Effect Item**, not on the spell record:

```
WornApparelHasKeywordCount( DLC2dunKolbjornAhzidalItem ) == 4.00
```

Two things follow that the raw record dump could not show, because the CLI
renders `Effects` as an opaque overlay:

1. For the ability route the condition goes on the **magic effect inside the
   spell**, not the spell itself.
2. The keyword does not have to be an armour-material keyword. Ahzidal's set
   uses a bespoke `DLC2dunKolbjornAhzidalItem` - which is the pattern to copy
   for a **modded** set that is not glass, steel, or any vanilla material.

## The recipe to hand someone

1. Make the ability or perk that carries the effect.
2. Put the condition `WornApparelHasKeywordCount( ArmorMaterialGlass ) == 4` on
   the perk entry point, or on the magic effect if using an ability.
3. Copy the shape from `051B17` in xEdit or the CK - it is 11 conditions, and
   conditions 3-11 show the OR-chaining pattern for supporting several
   materials at once.

For an ability rather than a perk, `DLC2dunKolbjornSetAbility`
(`027332:Dragonborn.esm`, a `ConstantEffect` spell) is the vanilla example of
that shape.

## Reproduce

```
py -3 - <<'PY'
# locate PERK 00051B17 in Skyrim.esm, walk subrecords, decode each CTDA:
#   byte 0 operator/flags, float at 4, uint16 function index at 8,
#   uint32 param1 at 12, param2 at 16, runOn at 20
PY
```

Keyword EditorIDs resolved with
`skyrim-record-cli record-selected-fields-by-type <Skyrim.esm> Keyword EditorID`.
