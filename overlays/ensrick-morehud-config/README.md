# Ensrick - moreHUD Configuration

A moreHUD preset, not a patch. Ships `SKSE/Plugins/moreHUD/Ensrick.json`, which
appears on moreHUD's **Presets** MCM page. Loading it there applies the five
settings below. Until it is loaded it changes nothing, because moreHUD keeps
its settings in global variables that live in the save rather than on disk.

## Scope

**User, 2026-09-11:** *"turn off seeing enemy magika and stamina bars. I don't
mind seeing their level, health, and name."*

| Key | Value | Effect |
|---|---|---|
| `!AHZShowEnemyMagickaMeter` | 0 | no magicka bar under the health bar |
| `!AHZShowEnemyStaminaMeter` | 0 | no stamina bar |
| `!AHZShowEnemyMagickaStats` | 0 | no magicka numbers |
| `!AHZShowEnemyStaminaStats` | 0 | no stamina numbers |
| `!AHZShowEnemySoulLevel` | 0 | no "Petty" |

"Petty" is not a difficulty rating. `AHZmoreHUDPlugin.dll` reads the game
settings `sSoulLevelNamePetty` / `Lesser` / `Common` / `Greater` / `Grand` and
exposes `soul` to the widget, so it is the target's **soul size**. It is off
here because it was named alongside the stamina bar on 2026-09-11; say the word
and it comes back.

**Untouched on purpose:** enemy level, enemy health and its numbers, the name,
and `AHZShowIngredientWidget`. The ingredient effects are wanted and are not
the source of the third-person popup - see below.

## The bars themselves

`AHZmoreHUD.bsa` ships `interface/exported/morehud/enemystaminameter.swf` and
`enemymagickameter.swf`, and its `config.txt` stacks them under the health
meter in the order `Health, Magicka, Stamina`. The health bar itself is vanilla
Skyrim's target bar, so turning these off leaves it exactly as it was.

## Not the source of the third-person popup

The fading widget that appears over every harvestable plant is **Better Third
Person Selection**, not moreHUD. BTPS draws a 3D widget on whatever its
selection algorithm picks, with `fWidgetFadeInDelta` / `fWidgetFadeOutDelta`
controlling the fade, and its `bAdjustMoreHudWidgets = 1` pins moreHUD's text
to that widget. That is why the ingredient text looks like it is floating on
the plant. Levers live in
`mods/Better Third Person Selection/MCM/config/BetterThirdPersonSelection/`.

## Why a partial file is safe

`ahzconfigmenu.psc`, state `LoadSelectedConfigBN`, reads every key as
`JSONUtil.GetPathIntValue(file, key, <current value>)`. An absent key falls
back to what is already set, so this preset carries only these five decisions.

## Requirements

PapyrusUtil (13048, installed and enabled). moreHUD checks for it before the
Presets page lists anything: DLL and script version must both be above 31.
