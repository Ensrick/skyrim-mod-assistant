# Current-profile compatibility sweep — 2026-08-29

## Outcome

The `Default` profile is structurally valid, but it is not yet ready to call a
first-playthrough baseline. The sweep found no missing or late masters, no
managed-mod installation drift, no SKSE loader refusal, and no unexplained
native-code collision. It did find two families of stale record overrides that
need one owned compatibility patch:

1. older `PROTEUS.esp` / `Skyrim Unbound.esp` worldspace records undo fields
   deliberately supplied by Lux Orbis and Lux Orbis CS; and
2. old Moonpath/Bruma and Water for ENB overrides erase Bruma worldspace
   climate, location, and bounds data.

No game launch was performed. No vendor plugin was edited. The live `Default`
load order was not sorted or otherwise changed.

## Frozen live baseline

| File | SHA-256 |
|---|---|
| `modlist.txt` | `58DF125EC754D31DA69D4D90C9A0750F393B0B7B15ED8167D71555CC7EB789DA` |
| `plugins.txt` | `798D089AE4C49ADC9225B9D629D8515DC8C5583D373C2B6ACE2BE9B701492C69` |
| `loadorder.txt` | `0F2B6939535B6679719533A52E6F637DA40744C0E61B99761ECCF830504DA5B4` |

An unselected disposable clone, `Compatibility Audit 2026-08-29`, preserves
the starting state. `Default` was explicitly reselected after every isolated
sort test.

## Structural and file-layer evidence

- 99 active plugins; all masters exist and load earlier.
- 97 ledger entries verified with zero installation problems.
- 19,360 ordinary shared FormKey chains inventoried with zero parser failures.
- 12 file-local NAVI records were excluded from conflict counts; NAVI is not an
  ordinary override/winner record.
- 23,881 managed files inspected; 1,627 paths have multiple providers.
- Only 21 collisions are code, configuration, interface, or plugin files.
- Twenty are explained by intentional runtime overlays, byte-identical shared
  UI files, or replacement/update packages.
- The remaining file-level decision is the `Underwear.ini` pool; it is not a
  launch or save-safety blocker.

## LOOT findings

The source-built LootCLI 1.8.0 / libloot 0.29.6 audit found two upstream
metadata gaps:

- the masterlist recognizes an older Lux/Water patch filename and otherwise
  sorts the official patch after the generated patch; and
- it does not enforce Lux CS' own requirement that `Lux Orbis CS.esp` load
  after Lux Orbis and all Orbis patches.

Tracked local rules now encode both constraints. In an isolated sorted clone:

- all active Orbis patches load before `Lux Orbis CS.esp`;
- the official Lux/Water patch loads before the generated Water patch; and
- `Ensrick Lux Water CS Patch.esp` remains last.

The rules are installed for future hidden LOOT runs, but the sorted clone has
not been promoted to `Default`. Changing record order invalidates the current
generated patch and therefore requires regeneration and another audit first.

LOOT's Engine Fixes Part 2 warning is inapplicable to the installed official
Engine Fixes 7.0.21 beta for Skyrim 1.7.99: that release explicitly no longer
requires the preloader. Fuz Ro D-oh is only a recommendation for NFF, not a
hard dependency. Dirty metadata was limited to shipped Creation Club masters;
vendor masters were not cleaned in place.

## Lux Orbis CS semantic conflict

Lux CS 2.6.0 is current as of this sweep. Its documentation and FOMOD say its
plugins must overwrite their masters and that `Lux Orbis CS.esp` belongs after
Orbis patches. The current profile instead lets older records win.

After eliminating Water for ENB's intended water assignments, the current
final winners discard these Lux CS fields:

| Record | Fields to preserve from Lux Orbis CS |
|---|---|
| `DLC2SolstheimWorld` | `MaxHeight` |
| `MarkarthWorld` | `Flags` (`NoGrass`), `MaxHeight` |
| `RiftenWorld` | `Flags` (`NoGrass`), `MaxHeight`, `Parent` image-space inheritance |
| `SolitudeWorld` | `Flags` (`NoGrass`), `MaxHeight`, `Parent` image-space inheritance |
| `Sovngarde` | `MaxHeight` |
| `Tamriel` | `MaxHeight` |
| `WhiterunWorld` | `MaxHeight`, `Parent` image-space inheritance |
| `WindhelmWorld` | `Flags` (`NoGrass`), `MaxHeight`, `Parent` image-space inheritance |

The targeted CELL pass compared 75 chains after `Lux Orbis CS.esp`. All visual
header fields survive. Before the vendor-required LOOT correction, PROTEUS also
erases `Location` from `SolitudeOrigin` and `WhiterunPlainsDistrict04`; sorting
Lux Orbis CS after PROTEUS restores those two without a patch. The final patch
generator must nevertheless assert them so a future order change cannot
silently regress location-aware mechanics.

## Bruma semantic conflict

The current final `BSHeartland` worldspace loses Bruma's climate and location
and shrinks its maximum cell bound from `(64, 73)` to `(64, 65)`. The sequence
proves this is stale forwarding: Bruma supplies the data, the old Moonpath
synergy patch erases it, the Water for ENB patch restores it, and the newer
Moonpath compatibility plugin erases it again.

Water for ENB also nulls the climate on `CYRBiomeTesting`,
`CYRGreenLeafGlade`, and `CYRTestWorld`. The water assignment itself is
intentional and must remain. Restoring climate even on the two test worlds is
cheap, deterministic, and avoids carrying demonstrably incomplete overrides.

Beyond Reach and Wyrmstooth were checked with the same field-level process.
Their worldspace differences are limited to intended Water for ENB water data,
and their relevant CELL chains show no unexplained semantic regression.

## Patch decision

The recommended resolution is one new, shareable, ESL-flagged,
override-only plugin owned by this project. It should:

- begin with the final active winner for every target;
- forward Lux Orbis CS' non-water WRLD fields listed above;
- retain Water for ENB's final `Water` / `LodWater` fields;
- restore Bruma's `Climate`, `Location`, and `ObjectBoundsMax` where identified;
- assert the two Lux CS CELL `Location` values;
- add no new forms, scripts, quests, aliases, persistent references, or NAVM;
- leave every vendor archive and installed vendor mod byte-for-byte unchanged;
- be generated reproducibly, serialized with Spriggit, link-audited, and tested
  against the isolated LOOT order before promotion.

This patch is awaiting the user's conflict-resolution approval. The current
generated Lux/Water patch remains enabled and unchanged until that decision.

## Remaining preference decision

`Underwear.ini` currently comes from the `Underwear.dll` package. Period
Underlayers supplies one additional form (`6C1DA`) and Vilja/Sofia blacklist
entries, while the winner supplies `8F19A`. The recommended shareable result is
an owned configuration-only overlay containing the union of intended forms and
the harmless future-facing blacklists. This choice is independent of the ESL
record patch.

## Explicit non-actions

- Skyrim was not launched.
- `Default` was not sorted.
- no new Nexus mod was downloaded, installed, or added to Keep;
- no author exclusion or Keep state changed;
- no vendor master or plugin was cleaned or edited;
- the obsolete Engine Fixes preloader was not reinstalled; and
- Fuz Ro D-oh was not installed.
