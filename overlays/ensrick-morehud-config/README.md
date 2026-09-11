# Ensrick - moreHUD Configuration

A moreHUD preset, not a patch. Drops `SKSE/Plugins/moreHUD/Ensrick.json`, which
appears on moreHUD's **Presets** MCM page; loading it applies the settings
below. Until it is loaded from that page it changes nothing, because moreHUD
keeps its settings in global variables that live in the save.

## Why these six

From two observations while playing (2026-09-11):

> "there's some kind of 3rd person gui that makes fade-in-fade-out popups for
> every single harvestable alchemical plant that crosses my view"

> "there's a mod that makes every enemy show a rating like 'petty' I guess, and
> it's stamina bar... I like the healthbars under the compass. I think being
> able to visually tell when an enemy is wounded, fine, but being able to see
> how much stamina and magika they have, not cool."

Both are moreHUD (Nexus 12688, Ahzaab). Receipts:

| Symptom | Source |
|---|---|
| Plant popups | MCM toggle `Show Ingredient Effects`, described in `interface/translations/ahzmorehud_english.txt` as *"shows the ingredient effects when targeting an object that can be harvested or an ingredient"* |
| "Petty" | `AHZmoreHUDPlugin.dll` reads the game settings `sSoulLevelNamePetty` / `Lesser` / `Common` / `Greater` / `Grand` and exposes `soul` to the widget. It is the target's **soul size**, not a difficulty rating. |
| Stamina and magicka bars | `AHZmoreHUD.bsa` ships `interface/exported/morehud/enemystaminameter.swf` and `enemymagickameter.swf`; its `config.txt` stacks them under the health meter, `Health, Magicka, Stamina` |

The health bar itself is vanilla Skyrim's target bar. moreHUD only stacks the
two extra meters beneath it, so turning these off keeps the bar the user wants.

## What the preset sets

| Key | Value | Effect |
|---|---|---|
| `!AHZShowIngredientWidget` | 0 | no plant/ingredient popup |
| `!AHZShowEnemySoulLevel` | 0 | no "Petty" |
| `!AHZShowEnemyMagickaMeter` | 0 | no magicka bar |
| `!AHZShowEnemyStaminaMeter` | 0 | no stamina bar |
| `!AHZShowEnemyMagickaStats` | 0 | no magicka numbers |
| `!AHZShowEnemyStaminaStats` | 0 | no stamina numbers |

**Deliberately left alone**, because they were not raised and are separate
calls: `AHZShowEnemyLevel` (numeric level with a colour scale),
`AHZShowEnemyHealthStats` (health numbers next to the bar),
`AHZShowEffectsWidget` (the same popup for enchanted items, scrolls, potions
and food), and `AHZActivationMode`, which can put every target widget behind a
hotkey instead.

## Why a partial file is safe

`ahzconfigmenu.psc`, state `LoadSelectedConfigBN`, reads every key as
`JSONUtil.GetPathIntValue(file, key, <current value>)`. A key that is absent
falls back to what is already set, so this preset carries only the six
decisions and disturbs nothing else.

## Requirements

PapyrusUtil (13048, installed and enabled). moreHUD checks for it before the
Presets page will list anything: DLL and script version must both be above 31.
