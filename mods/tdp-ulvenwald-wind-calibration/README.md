# Ensrick TDP–Ulvenwald Wind Calibration

Issue: [#29](https://github.com/Ensrick/skyrim-mod-assistant/issues/29).

This is a CK-native, ESL-flagged compatibility patch for the selected **Nature
of the Wild Lands base + Tree Diversity Project Ulvenwald swap** configuration.
It corrects eleven `TREE` records whose selected Ulvenwald meshes were being
driven by Tree Diversity Project values calibrated for other meshes.

The symptom was species-specific, extreme sway south of Falkreath. The largest
mismatch was branch flexibility `6.0` on a mesh for which Ulvenwald uses `1.0`.
Across the eleven records, the mismatch was about 2.5x–6x. No Dynamic Wind or
Skyrim Is Windy installation is present in the profile.

## Scope

The plugin overrides exactly eleven forms in `Tree_Diversity_Project.esp` and
changes only four named motion fields:

- `TrunkFlexibility`
- `BranchFlexibility`
- `LeafAmplitude`
- `LeafFrequency`

Every value is copied from Ulvenwald 3.3.2's `TREE` record for the exact same
NIF path. Every other TDP field remains byte-for-text identical in the authored
Spriggit representation, including object bounds and the opaque animation-data
blob. The TDP swamp target is not overdriven and the willow target comes from
NotWL, so neither is touched.

| TDP target | model | trunk | branch | leaf amplitude | leaf frequency |
|---|---|---:|---:|---:|---:|
| `TDP_sycamore_small01_summer` | `AutumnSycamoreSmall01.nif` | 1.3 | 1.75 | 3.5 | 1.5 |
| `TDP_sycamore_tall02_summer` | `AutumnSycamoreTall02.nif` | 1.3 | 1.75 | 3.5 | 1.5 |
| `TDP_sycamore_medium01_summer` | `AutumnSycamoreMedium01.nif` | 1.3 | 1.75 | 3.5 | 1.5 |
| `TDP_ash_common02_summer` | `AshTree02.nif` | 1.3 | 1.75 | 3.5 | 1.5 |
| `TDP_ash_medium01_summer` | `AshMedium01.nif` | 1.3 | 1.75 | 3.5 | 1.5 |
| `TDP_oak_mother01_summer` | `MotherOak01.nif` | 1.3 | 1.75 | 2.0 | 1.5 |
| `TDP_oak_mother_clump01_summer` | `MotherOakClump01.nif` | 1.3 | 1.75 | 2.0 | 1.5 |
| `TDP_pine_forest_big04_summer` | `treepineforest04.nif` | 1.0 | 1.0 | 2.0 | 1.0 |
| `TDP_pine_forest_big01_summer` | `treepineforest01_large.nif` | 1.0 | 1.0 | 2.0 | 1.5 |
| `TDP_pine_forest_bigst01_summer` | `PineTree01.nif` | 1.75 | 2.0 | 3.5 | 1.5 |
| `TDP_pine_forest_medium01_winter` | `PineMedium01_winter.nif` | 1.3 | 1.75 | 3.5 | 1.5 |

## Build

The committed Spriggit YAML is the source and the change. There is no code
generator. With the repository-pinned Spriggit 0.41.0 binary:

```powershell
& $spriggit deserialize `
  --InputPath ./mods/tdp-ulvenwald-wind-calibration/spriggit `
  --OutputPath './Ensrick TDP Ulvenwald Wind Calibration.esp' `
  --PackageName Spriggit.Yaml.Skyrim `
  --PackageVersion 0.41.0 `
  --BackupDays 0
```

Two clean deserializations are byte-identical. A checked serialize/deserialize
round trip is semantically identical; Spriggit omits the final newline in its
generated `spriggit-meta.json`.

## Requirements and load order

- Tree Diversity Project 1.0.1, file 680001
- its official `NOTWL base + Ulvenwald swap` option
- Traverse the Ulvenwald 3.3.2 assets, file 444742, with `Ulvenwald.esp`
  disabled as required by that option

Load this plugin after `Tree_Diversity_Project.esp`. It contains no new forms,
scripts, assets, cells, worldspaces, references, or navmesh.

## Distribution

The patch contains only Ensrick's compatibility override and requires the two
official mods. It does not redistribute either vendor plugin or any Ulvenwald
mesh/texture. Tree Diversity Project's author explicitly permits modification;
Ulvenwald remains an external download under its restrictive asset terms.

Static validation is complete. Final acceptance is a user-observed pass through
Falkreath under calm and high-wind weather before TexGen/DynDOLOD generation.
