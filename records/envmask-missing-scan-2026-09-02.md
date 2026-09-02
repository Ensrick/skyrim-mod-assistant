# Env-mask / cubemap missing-texture sweep, 2026-09-02 (#159 follow-up)

**Question:** after the Skyking sign-post fix, are there any other meshes in
the load order whose environment-map shader points at a mask (or cubemap)
that nothing ships? Same defect class as #159: under Community Shaders'
Dynamic Cubemaps a missing env mask leaves the engine's substitute texture
scaling a full-strength reflection.

**Tool:** `audit/envmask_scan.py` (new; reuses `audit/modasset.py` for the
BSA name tables and the block walker from the #159 parse). For every enabled
mod in profile `Default` (MO2 priority order, `overwrite/` on top) it parses
every loose `meshes/**/*.nif`, decodes each `BSLightingShaderProperty` that
is EnvironmentMap-typed (1), EyeEnvmap-typed (15) or carries SLSF1
`Environment_Mapping` (bit 7), reads its `BSShaderTextureSet`, and resolves
slot 4 (cubemap) and slot 5 (env mask) against loose files (priority order),
every `*.bsa` in an enabled mod folder, and the game's 92 `Data\*.bsa`.

## Scope and timing

| Item | Count |
|---|---:|
| Enabled sources (207 mods + overwrite) | 208 |
| Loose files indexed | 40,824 |
| Loose NIFs parsed (0 unreadable) | 11,351 |
| Env-mapped shapes decoded | 4,999 |
| Mod BSAs (name tables) | 59 |
| Vanilla / CC BSAs (name tables) | 92 |
| Archive entries indexed | 353,526 |
| Shapes with an unresolved slot | 103 |
| Mods affected | 10 |
| Wall time (loose 0.7 s, BSA index 0.7 s, NIF parse 8.2 s) | 9.6 s |

NOT opened on this pass: NIFs packed inside vanilla BSAs and NIFs packed
inside mod BSAs (texture resolution does cover every BSA by name). Vanilla
loose `Data\textures` contributed 0 files. A BSA in an enabled mod folder is
treated as loaded whether or not its plugin is active (same convention as
the #159 sweep); none of the missing paths would have resolved either way.
Run at 2026-09-01 23:47 local; raw results in the session scratchpad
(`envmask-scan.json`, `bsa-name-index.json`).

## Results (every NIF whose mask or cubemap resolves nowhere)

| Mod | Slot | Missing texture | NIFs | Shadowed | Example NIF |
|---|---|---|---:|---|---|
| Believable Weapons | mask | `textures/creationclub/bgssse025/weapons/madness/madness_longsword_01em.dds` | 2 | no | `meshes/creationclub/bgssse025/weapons/madness/1stpersonmadnesssword.nif` |
| ERM - Fix and Addon | mask | `textures/landscape/mountains/mountainslab02_m.dds` | 1 | no | `meshes/dungeons/mines/rocks/minecboulderl02.nif` |
| HIMBO Refits | mask | `textures/armor/orcish/orc_armor_male_body_m.dds` | 4 | no | `meshes/armor/orcish/1stpersoncuirassm_0.nif` |
| HIMBO Refits | mask | `textures/armor/orcish/orc_armor_male_boot_m.dds` | 2 | no | `meshes/armor/orcish/bootsm_0.nif` |
| HIMBO Refits | mask | `textures/armor/orcish/orc_armor_male_glove_m.dds` | 2 | no | `meshes/armor/orcish/gauntletsm_0.nif` |
| Lux Orbis | mask | `textures/architecture/solitude/sdoor01_m.dds` | 1 | all | `meshes/architecture/solitude/sbridge01.nif` |
| Skyking Signs | mask | `textures/architecture/markarth/mrkdeco01_m.dds` | 1 | no | `meshes/architecture/markarth/mrkalchemysign.nif` |
| Skyking Signs | mask | `textures/architecture/markarth/mrkinnwindows01_m.dds` | 2 | no | `meshes/architecture/markarth/mrksigngeneralgoods01.nif` |
| Skyking Signs | mask | `textures/architecture/riften/riftenlogdetails01_m.dds` | 1 | no | `meshes/clutter/signage/riften/signrtorphanage01.nif` |
| Skyking Signs | mask | `textures/landscape/fieldgrass01_m.dds` | 1 | no | `meshes/loadscreenart/loadscreenblackbriar01.nif` |
| Skyking Signs | mask | `textures/landscape/mountains/mountainslab02_m.dds` | 1 | no | `meshes/loadscreenart/loadscreenblackbriar01.nif` |
| Skyking Signs | mask | `textures/landscape/rocks01_m.dds` | 1 | no | `meshes/loadscreenart/loadscreenblackbriar01.nif` |
| Skyking Signs | mask | `textures/landscape/tundra01_m.dds` | 1 | no | `meshes/loadscreenart/loadscreenblackbriar01.nif` |
| Skyking Unique Signs | mask | `textures/architecture/markarth/mrkdeco01_m.dds` | 1 | no | `meshes/clutter/signage/generic/signthehagscure.nif` |
| Skyking Unique Signs | mask | `textures/architecture/markarth/mrkinnwindows01_m.dds` | 1 | no | `meshes/clutter/signage/generic/signarnleifandsons.nif` |
| Skyland AIO 1K | cubemap | `textures/arechitecture/solitude/smanhole_e.dds` | 1 | no | `meshes/architecture/solitude/smanhole.nif` |
| Skyland AIO 1K | mask | `textures/arechitecture/solitude/smanhole_m.dds` | 1 | no | `meshes/architecture/solitude/smanhole.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/dungeons/dwemerruins/dwemetalbars01_m.dds` | 5 | no | `meshes/bb's art supplies/bbframes/gm_rec_side_dwe.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/dungeons/dwemerruins/dwemetalsheet01_m.dds` | 5 | no | `meshes/furniture/alchemyworkbenchdwemer.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/dungeons/dwemerruins/dwemetaltiles01_m.dds` | 3 | no | `meshes/furniture/alchemyworkbenchdwemer.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/dungeons/dwemerruins/dwemetaltiles02_m.dds` | 3 | no | `meshes/clutter/weaponrack/gm_wrplaqueleft01_dwe02.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/dungeons/dwemerruins/dwemetaltiles03_m.dds` | 12 | no | `meshes/clutter/weaponrack/gm_wrplaque01_dwe01.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/gm misc textures/gm_rugs & tapestries/gm_draperybrown03a_m.dds` | 1 | no | `meshes/architecture/whiterun/wrclutter/gm_wrintcastlewallstrwin01drapery01_red02a.nif` |
| Snazzy Furniture and Clutter Overhaul 3 - BOS | mask | `textures/gm misc textures/gm_rugs & tapestries/gm_draperybrown03b_m.dds` | 2 | no | `meshes/architecture/whiterun/wrclutter/gm_wrintcastlewallstrwin01drapery01_blue03b.nif` |
| Sons of Skyrim | mask | `textures/nordwar/sonsofskyrim/splintedbg_m.dds` | 10 | no | `meshes/nordwar/sonsofskyrim/bg/splintedboots_gnd.nif` |
| Water for ENB | cubemap | `textures/cubemaps/waterfall_e.dds` | 1 | no | `meshes/dungeons/nordic/exterior/walls/norextwallbg1way01water.nif` |
| Water for ENB | mask | `textures/themilkdrinker/tmdwaterfalls/waterfallwater_m.dds` | 1 | no | `meshes/dungeons/nordic/exterior/walls/norextwallbg1way01water.nif` |

Shapes per mod: SFCO 3 66, Sons of Skyrim 10, Skyking Signs 9, HIMBO Refits
8, Believable Weapons 4, Skyking Unique Signs 2, Skyland AIO 1K 2 (1 mask +
1 cubemap), Water for ENB 2 (1 + 1), ERM 1, Lux Orbis 1. "Shadowed" = the
mod's copy of the NIF loses to a higher-priority mod and never renders.

## Verdict per mod

**Masked by the overlay (black-mask-safe: matte wood, carved stone, ground,
rock; vanilla ships no `_m` for the texture and renders the same surface with
the Default shader, so a black mask reproduces the vanilla look):**

- **Skyking Signs** - 7 remaining masks (EnvironmentMap, EnvMapScale 1.0,
  1x1 black cubemap, same terms as the four post masks). The vanilla
  `loadscreenblackbriar01.nif` was parsed from `Skyrim - Meshes1.bsa`: all
  four landscape shapes are Default with empty slots 4/5.
- **Skyking Unique Signs** - the same two Markarth masks
  (`mrkdeco01_m`, `mrkinnwindows01_m`); covered by the same files.
- **ERM - Fix and Addon** - `minecboulderl02.nif` (mine boulder, rock) wants
  `mountainslab02_m`; covered by the same file.

The overlay `Ensrick - Skyking Signs Env Mask Fix` was rebuilt with all 11
paths (`overlays/ensrick-skyking-signs-envmask-fix/build.py`; every file
212 B, sha256 `9D4C494A...DBA29`; zip sha256 `3B9B6F82...1C0D`; each read by
texconv 2026.4.1.1 without error) and re-staged with MO2Headless
`mod-stage --replace`, transaction `20260902T045315225Z-7d160abddf8d`,
priority kept at 228 (modlist row 4, above ERM row 21, Skyking Unique Signs
row 108, Skyking Signs row 109), enabled, audit `errors: []`, 11/11 installed
files re-hashed. Claim `envmask-sweep` taken and released; no game or MO2
process during the change. Ledger row carries the file list and recipe.
If a texture pack later ships real complex-material masks at any of these
paths, disable this overlay (it would shadow them).

**NOT masked - for the user's eyes (intentional metal / water reflection, a
path typo with the real file beside it, or a missing texture set; a black
mask would remove an authored effect or hide a bigger defect):**

- **HIMBO Refits** - male orcish armor, 8 NIFs (`cuirassm_0/_1`,
  `1stpersoncuirassm_0/_1`, `bootsm_0/_1`, `gauntletsm_0/_1`):
  EnvironmentMap, EnvMapScale 0.4, cubemap `Ore_Obsidian_e`, masks
  `orc_armor_male_{body,boot,glove}_m.dds` exist nowhere. Vanilla renders the
  same textures with the Default shader (no mask, parsed from
  `Skyrim - Meshes0.bsa`). HIMBO added the env map expecting a retexture's
  masks. Options: a black mask at the three paths (restores the vanilla matte
  look), or install an orcish retexture that ships those masks. Issue #171
  (needs-decision).
- **Snazzy Furniture and Clutter Overhaul 3 - BOS**, Dwemer set - 18 NIFs
  (weapon-rack plaques, alchemy/enchanting Dwemer workbenches, Dwemer bed,
  vampire enchanting station, two frames) reference five
  `dwemerruins/dwemetal*_m.dds` masks. No vanilla or installed texture ships
  any `_m` under `dungeons/dwemerruins`; Skyland AIO 1K wins the diffuse and
  normal. Metal, so the reflection is authored: not black-safe. Fix is a
  Dwemer retexture with complex-material masks, or accept. Issue #171
  (needs-decision).
- **SFCO 3, Whiterun castle drapery** - 3 BOS-swapped NIFs
  (`gm_wrintcastlewallstrwin01drapery01_red02a`, `..._blue03b`,
  `...drapery02_blue03b`), EnvMapScale 2.0, cubemap `shinycontrast_e`. The
  masks are referenced under `gm misc textures/gm_rugs & tapestries/` but
  SFCO ships them under `textures/architecture/whiterun/`
  (`gm_draperybrown03a_m`, `03b_m`); the diffuse textures
  (`gm_draperyblue03b.dds`, `gm_draperyred02a.dds`) resolve nowhere at all.
  Archive check 2026-09-02 (`113045-783076.7z`): no `gm misc textures`
  folder in any option and no `GM_DraperyBlue03b.dds` anywhere
  (`Textures_desat`, `Textures_Alternate\Drapery01`, `Textures_Addons`);
  `GM_DraperyRed02a.dds` and both brown masks live under
  `architecture\whiterun`. No installer option supplies the asked-for paths.
  Packaging defect in SFCO 3 (paths), upstream-worthy; a mesh-path fix, not
  a black mask. Issue #169.
- **Sons of Skyrim** - 10 splinted-armor NIFs (`splintedboots*`,
  `splintedgauntlets*`), EnvMapScale 0.7, cubemap `metalic_e`: the mask
  `splintedbg_m.dds` AND the diffuse `splintedbg.dds` are absent everywhere.
  RESOLVED 2026-09-02 as no in-game defect: `NW_Sons_of_Skyrim.esp` names
  only the `BootsSplinted*` / `GauntletsSplinted*` meshes (6 + 6 string hits,
  0 for `splintedboots` / `splintedgauntlets`), and those meshes use
  `bg_iron_splinted.dds` + `_m` + `_n`, which the mod ships. The ten
  `SplintedBoots*` / `SplintedGauntlets*` NIFs are orphaned legacy files
  inside the same archive (68656 file 448133, `Data\Meshes\...\BG\`); no
  installer option or extra download is involved. Nothing to install.
  Issue #172 (closed on opening).
- **Believable Weapons** - CC Madness longsword, 2 NIFs
  (`1stpersonmadnesssword`, `3rdpersonmadnesssword`), EnvMapScale 0.25,
  cubemaps `opal_e` / `Ore_Moonstone_e`: the mesh asks for
  `madness_longsword_01em.dds`; `ccbgssse025-advdsgs.bsa` ships
  `madness_longsword01_em.dds`. The vanilla CC meshes inside that BSA carry
  the identical `_01em` path (parsed 2026-09-02), so the typo is Bethesda's
  and Believable Weapons inherited it. FIXED 2026-09-02 by overlay
  `Ensrick - CC Madness Longsword Env Mask Path Fix`
  (`overlays/ensrick-cc-madness-longsword-envmask-path-fix/build.py`: byte
  copy of the CC texture, sha256 `813B130D...66FF`, 2,796,336 B, to the
  asked-for path; transaction `20260902T050602046Z-725b51195af0`, priority
  234, audit errors `[]`; ledger `distribution: recipe`). Issue #167.
- **Skyland AIO 1K** - `smanhole.nif` (Solitude manhole, metal,
  EnvMapScale 1.5): both slots say `textures\arechitecture\solitude\...`;
  Skyland ships `smanhole_m.dds` and `smanhole_e.dds` under the correctly
  spelled folder. Vanilla `smanhole.nif` is a Default shader (diffuse +
  normal only), so the reflection is Skyland's own authoring. Vendor typo,
  upstream-worthy. FIXED 2026-09-02 by overlay
  `Ensrick - Skyland Solitude Manhole Texture Path Fix`
  (`overlays/ensrick-skyland-smanhole-texture-path-fix/build.py`: byte copy
  of Skyland's `smanhole_m.dds` (sha256 `D8F956EF...739F`) and
  `smanhole_e.dds` (`4522140D...995A`) into the misspelled folder;
  transaction `20260902T050602116Z-cbe4e3d83cbb`, priority 235, audit
  errors `[]`; ledger `distribution: recipe`, local only under Skyland's
  terms). Issue #168.
- **Water for ENB** - `norextwallbg1way01water.nif` (Nordic exterior wall
  water sheet, diffuse `black.dds`, EnvMapScale 1.0): cubemap
  `cubemaps/waterfall_e.dds` and mask
  `themilkdrinker/tmdwaterfalls/waterfallwater_m.dds` are not installed (no
  `tmdwaterfalls` folder, no BSA). Archive check 2026-09-02
  (`x37061-784038`, v2.21): the NIF comes from `waterfalls-common` (fomod
  step "Waterfalls And Effects Add-On", already chosen in
  `records/fomod-plans/37061-water-for-enb-cs.json`); no option folder
  contains a `tmdwaterfalls` directory or a `waterfall_e.dds`, and the NIF
  is the only file in the archive mentioning `tmdwaterfalls`. Not supplied
  by any option of 37061; likely the author's separate waterfall mod
  [unverified]. Issue #170.
- **Lux Orbis** - `sbridge01.nif` (`sdoor01_m`) loses to Assorted Mesh
  Fixes' copy and never renders. No action.

## Method notes

- Paths were read from the NIF blocks, never typed: `mrkinnwindows01_m` is
  spelled as Skyking's `BSShaderTextureSet` spells it. The Skyking parse
  reproduces the #159 numbers exactly (8 / 14 / 9 / 5 post NIFs plus the
  seven others, all EnvMapScale 1.0 with `dynamic1pxcubemap_black`).
- The four masks installed on 2026-09-01 now resolve to
  `loose:Ensrick - Skyking Signs Env Mask Fix`; they no longer appear as
  missing, which is the scanner's own regression check.
- Re-run: `py -3 audit/envmask_scan.py --json OUT --md OUT --index CACHE`;
  the `--index` cache skips re-reading the 151 archives when unchanged.
