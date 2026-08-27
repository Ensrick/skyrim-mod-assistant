# Sons of Skyrim installation record

Installed into the MO2 `Default` profile on 2026-08-26 without launching the
game or any desktop UI.

## Selected stack

| Layer | Nexus/file | Version | SHA-256 |
|---|---:|---:|---|
| Sons of Skyrim, standard Main Files | 68656 / 448133 | 2.0.2 | `3EC662E95D5415787EA17E4426EA97E094C9F2A28CBED39335947B2875003061` |
| Xtudo default fixes | 104126 / 617660 | 3.3 | `EC3AF23A6F1BD2691F0A550F344010EB6A50C7EFC9EB2FB37991F60A515607D9` |
| More Patches, Lux Orbis selection only | 104261 / 782421 | 1.3.1 | `8EFA01FCBD8D408D04FF1D227DCF79E72AD6D76EB03E224755ED2B6908816D33` |

The Xtudo page version is 3.9 because newer optional LOTD files were added;
3.3 remains the current default fixes file. The SkyPatcher conversion was not
selected: the conventional plugin stack is already compatible, while that
conversion would add another runtime-sensitive SKSE DLL to the 1.7.99 build.

The optional 940 MB HD texture archive was omitted. The standard archive has
315 DDS textures: 137 at 2K square, 155 at 1K square, smaller ancillary maps,
and three 4K maps used by the Riften shield. This is the performance-oriented
choice while preserving the authored appearance.

The 2026-08-26 texture-policy review found vanilla shields ranging from 1K to
2K, with the comparable Stormcloak shield at 2K. The Riften shield's 4K maps
therefore occupy the permitted single step above that analogue and exactly the
absolute ceiling; they are not precedent for selecting 4K elsewhere. See
`docs/TEXTURE_POLICY.md`.

## Compatibility and validation

- Xtudo's patch carries USSEP fixes, adds Survival warm keywords, repairs
  records and first-person meshes, and is ESL-flagged.
- The selected Lux Orbis patch removes torches from the added guard outfits to
  preserve Lux Orbis lighting behavior and is ESL-flagged.
- LOOT 0.29.6 / LootCLI 1.8.0 sorted the profile successfully.
- The master/provider/order audit passed for all 82 active plugins.
- MO2's transactional profile audit returned no errors.
- No loose-file collision exists with another enabled mod, excluding generated
  `meta.ini` files. Xtudo intentionally overrides 22 base Sons of Skyrim files.
- Six later record overrides were inspected. Skyrim Unbound forwards identical
  Windhelm cell/dialogue data; Lux and its USSEP patch intentionally win cell
  lighting fields while forwarding the relevant ownership/location values.
- No runtime smoke test was performed on the active desktop.

The installed armor meshes remain the author's vanilla-shape meshes. A HIMBO
BodySlide conversion can be evaluated separately if matching clothed male body
proportions becomes important; it is not required for correct rendering.

## Publication boundary

All three archives remain in ignored local download storage. The collection
may reference their Nexus mod and file identifiers but must not bundle them.
Exact permissions are recorded in `records/restricted-mods.json`.
