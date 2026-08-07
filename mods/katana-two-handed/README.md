# Katana Two-Handed Combat

Status: generated and record-audited against the installed Skyrim SE/AE load
order on 2026-08-01.

This mod turns recognized katanas into true two-handed weapons. It is generated
from the current load order so later weapon mods can be incorporated without a
pile of hand-authored compatibility patches.

`KatanaTwoHandedPatch.esp` is ESL-flagged and therefore does not consume a full
plugin slot.

## Combat profile

- Speed: 0.85 (quick for a two-hander; vanilla greatswords are normally 0.70)
- Reach: 1.20 (below a normal greatsword's 1.30)
- Stagger: 0.90 (below a normal greatsword's 1.10)
- Damage: tier-normalized to compensate for requiring both hands at the faster
  swing speed
- Skill/animation/equip type: Two-Handed / two-handed sword / both hands
- Perk keyword: `WeapTypeGreatsword`
- Integration keyword: `KWA_WeapTypeKatana2H`

Weight, value, enchantments, meshes, names, recipes, tempering recipes, and
leveled lists are left alone.

## Installed-game records covered

The generated plugin contains 14 weapon overrides:

- Blades Sword
- Bolar's Oathblade
- Dragonbane (all five leveled variants)
- Ebony Blade (both underlying records)
- Akaviri Sword
- Harkon's Sword
- Goldbrand
- Bloodthirst
- Dawnfang/Duskfang

Mod-added katana, nodachi, odachi, uchigatana, nagamaki, tsurugi, and dai-katana
records are detected conservatively. Exact exceptions can be placed in the
patcher's `ForceInclude` or `Exclude` arrays.

## Files

- `package/KatanaTwoHandedPatch.esp`: generated local plugin (intentionally not
  committed)
- `regenerate.ps1`: fully headless regeneration against a chosen Data folder and
  plugins.txt
- `ANIMATION-INTEGRATION.md`: optional Japanese-style hip scabbard and matching
  draw/sheathe setup

The patcher source is maintained in
[KatanaTwoHandedPatcher](https://github.com/Ensrick/KatanaTwoHandedPatcher).

## Load order

Place the generated plugin late enough to win weapon-record conflicts. Regenerate
it whenever weapon mods or broad balance overhauls change. It contains no scripts
and is safe to replace between saves.
