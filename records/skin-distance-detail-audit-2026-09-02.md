# Skin distance-detail audit - 2026-09-02 (#166)

Status: **measured, no change made**. Metric: `audit/mip_retention.py` (new
this pass; wired into `inspect_mod.py` as the `soft-at-distance` finding).
Every number below is from the mip chain *as shipped* in the winning file,
decoded with texconv 2026.4.1.1, compared with the vanilla texture from
`Skyrim - Textures0.bsa` at the **same pixel size** (a 4096 replacer's mip 3
is scored against vanilla 2048's mip 2, because that is what the GPU picks
at a given screen density). "mid/far" = minimum over the 512/256/128 px
levels, where a body or head sits from conversation to across-the-room
distance. `hf` = RMS 4-neighbour Laplacian of luminance (fine detail),
`tone` = luminance standard deviation (single-tone collapses this). Diffuse
maps exclude near-black UV padding.

Winners are the ones resolved in `records/face-eye-makeup-audit-2026-09-02.md`:
female CBBE 2.0.3 (prio 141) over Reverie 1.11.2 (202); male The New
Gentleman 4.2.5 bundled skin (198) over SkySight Skins 2.0.2 (201).

## Mid/far ratio vs vanilla (hf / tone; 1.00 = vanilla)

Female:

| map | vanilla | CBBE (winner) | Reverie (losing) | CBBE resharpened u1.0 | u1.5 |
|---|---|---|---|---|---|
| `femalebody_1.dds` | 2048 BC1 | 4096 BC7 **0.62 / 0.70** | 4096 BC7 0.66 / 0.89 | **1.04** / 0.72 | 1.17 / 0.73 |
| `femalebody_1_msn.dds` | 2048 BC1 | 4096 BC7 0.85 / 0.94 | 4096 BC7 1.58 / 1.86 | - | - |
| `femalebody_1_s.dds` | 2048 BC1 | 2048 BC4 **0.34** / 0.93 | 4096 BC4 0.71 / 1.78 | - | - |
| `femalehead.dds` | 1024 BC1 | 1024 BC7 **0.48** / 1.37 | 4096 BC7 0.47 / 0.75 | 0.71 / 1.44 | 0.80 / 1.46 |
| `femalehead_msn.dds` | 1024 raw | 1024 BC7 **0.47** / 1.01 | 2048 BC7 1.04 / 1.18 | - | - |
| `femalehead_s.dds` | 1024 BC1 | 2048 BC4 **0.26 / 0.37** | 4096 BC4 0.31 / 0.47 | - | - |
| `femalehands_1.dds` | 1024 BC1 | 1024 BC7 0.56 / 1.11 | 2048 BC7 0.79 / 0.60 | - | - |
| `femalehead_sk.dds`, `femalebody_1_sk.dds` | 256 BC1 | 1024/2048 BC7 0.11-0.13 / 0.11-0.13 | 4x4 black | - | - |

Male:

| map | vanilla | TNG (winner) | SkySight (losing) | TNG resharpened u1.0 | u1.5 |
|---|---|---|---|---|---|
| `malebody_1.dds` | 2048 BC1 | 4096 BC7 **0.29 / 0.42** | 4096 BC7 0.46 / 0.67 | 0.47 / 0.43 | 0.52 / 0.44 |
| `malebody_1_msn.dds` | 2048 BC1 | 4096 BC7 **0.41** / 1.10 | 4096 BC7 0.81 / 1.10 | - | - |
| `malebody_1_s.dds` | 2048 BC1 | 2048 BC4 **0.46 / 0.38** | 4096 BC7 0.42 / 0.39 | - | - |
| `malehead.dds` | 1024 BC1 | 2048 BC7 **0.33 / 0.69** | 2048 BC7 0.66 / 1.48 | 0.54 / 0.71 | 0.59 / 0.71 |
| `malehead_msn.dds` | 1024 raw | 2048 BC7 **0.44** / 1.15 | 2048 BC7 0.56 / 1.04 | - | - |
| `malehead_s.dds` | 1024 BC1 | 2048 BC4 **0.20 / 0.42** | 2048 BC7 0.39 / 0.84 | - | - |
| `malehands_1.dds` | 1024 BC1 | 2048 BC7 **0.27 / 0.51** | 4096 BC7 0.47 / 0.99 | - | - |
| `malehead_sk.dds`, `malebody_1_sk.dds` | 512/256 BC1 | 4x4 black | none shipped (vanilla returns) | - | - |

(Hands and `_sk` rows are from the earlier pass's `retention_matrix.json`,
same metric; every shared row matches this pass to two decimals.)

Per-mip hf for the two body diffuses (matched width 2048/1024/512/256/128):

| | 2048 | 1024 | 512 | 256 | 128 |
|---|---|---|---|---|---|
| vanilla `femalebody_1` | 6.17 | 4.32 | 3.52 | 3.73 | 4.72 |
| CBBE (mip 0 at 4096 = **1.00**) | 1.44 | 1.86 | 2.18 | 2.70 | 3.69 |
| CBBE resharpened u1.0 | 2.21 | 2.99 | 3.67 | 4.79 | 6.55 |
| vanilla `malebody_1` | 13.85 | 14.02 | 12.09 | 11.78 | 12.84 |
| TNG (mip 0 at 4096 = 6.93) | 6.39 | 4.84 | 3.72 | 3.42 | 4.29 |
| SkySight | 11.65 | 8.49 | 6.33 | 5.37 | 6.33 |
| TNG resharpened u1.0 | 10.72 | 8.13 | 6.02 | 5.51 | 7.84 |

## Reading

- **The complaint is measured, and it is worst on males.** At play distance
  the male body shows 29% of vanilla's fine detail and 42% of its tonal
  range; the male head 33% / 69%. Female body 62% / 70%, head 48% (tone is
  higher than vanilla on the CBBE head because of large blotches, not pores).
- **Female is salvageable for detail, not for tone.** Regenerating CBBE's
  body chain (Lanczos from mip 0 + unsharp 100%, radius 1 px, recompressed
  BC7, same 22.4 MB) lifts mid/far hf to 1.04-1.39x vanilla; tone stays 0.72
  because the art is single-tone at mip 0 too. Head goes 0.48 -> 0.71 (0.80
  at 150%). Halo risk rises with strength; u1.0 is the recipe candidate.
- **Male is not salvageable by resharpening.** TNG's mip 0 already holds half
  the detail vanilla has at half the size (6.93 vs 13.85), so no mip filter
  recovers it: 0.29 -> 0.47 (0.52 at u1.5), tone unchanged at 0.43.
  SkySight, which is installed and is BASELINE.md:186's intended male skin,
  beats TNG's bundle on every map except body spec (0.46/0.67 body,
  0.66/1.48 head, 0.81 body normal) simply by being placed above it.
- **Specular and subsurface flatten the rest.** The winning `_s` maps carry
  20-46% of vanilla's mid/far hf with tone 0.37-0.42 (uniform sheen), and
  both winners' `_sk` maps are black or near-black, which zeroes the vanilla
  soft-light wrap (mechanism and numbers in the #165 record). #144 did not
  remove specular; it turned Advanced Skin off, so these flat `_s`/`_sk` maps
  are what the vanilla path now renders.
- The 4K containers are mostly empty: CBBE's 4096 mip 0 has hf 1.00 against
  vanilla 2048's 6.17. A 2K downscale would cost nothing visible at distance.

## Candidate replacements (web research by subagent, 2026-09-02; nothing downloaded)

Selection rule that follows from the numbers: the resharpen recipe restores
fine detail but not tone (0.43-0.73x stays after sharpening), so a candidate
must bring **tonal variation at play distance** - visible colour and value
change across the skin at mip 2-4 - not merely a large normal map. Before
install every candidate gets the table above; the acceptance bar is tone
>= 0.85 of vanilla at 512-128 px on the body diffuse AND hf >= 0.70, or it
is not an improvement on what is installed. Of the installed pairs, Reverie
(tone 0.89) and SkySight (0.67 body, 1.48 head) are the only maps near it;
the two "true to vanilla" candidates below are the ones whose design
statement promises it and they are still unmeasured until an archive is on
disk.

Nexus returned 403 to page fetches; metadata came from the v2 GraphQL API and
"Permissions and credits" blocks from the classic page where the page is not
adult-gated. Adult-gated pages' formal permission blocks **could not be
fetched** and are marked; description-text permission lines are quoted
instead. No candidate lists a source repository. HIMBO accepts SoS-type
(vanilla-UV) male textures; CBBE SE is its own body UV, head UV is vanilla.

Female (CBBE UV):

| mod | author, version | distance design | permissions | note |
|---|---|---|---|---|
| **Lucid Skin (53030)** | Novelyst, 1.5.0 (2021-10-05) | "true-to-vanilla skin texture set ... a true vanilla improvement as opposed to a dissimilar replacement"; CBBE-UV build | upload to other sites "but you must credit me"; modification allowed with credit; conversion and asset use allowed with credit; not for sale | top pick: vanilla-styled by design, most open terms, same author as Reverie |
| Reverie (64314, installed) | Novelyst, 1.11.2 (2024-09-26) | none stated; measured body tone 0.89, normals 1.58x | identical block to Lucid | reorder above CBBE fixes tone; ships black `_sk` (needs the #165 option-1 female half) |
| Tempered Skins for Females (8505) | traa108, 1.32 (2020-10-31) | "hand painted veins"; normal option "rougher - vanilla-like" | formal block not fetched (adult); description: rework/reupload "contact me" | restrictive by the author's own text |
| BnP Female Skin (65274) | TheNorthSisters, 2.0 (2024-06-03) | photoscan micro-detail (not vanilla-like) | formal block not fetched (adult) | KEEP_REVIEW.md:49 already parked it behind Reverie |
| CBBE 4K-8K Upscaled (71405) | XilaMonstrr, 1.01 (2022) | same art as the installed CBBE default | not fetched (adult) | not a fix: same mip-0 content |

Male (vanilla/SoS UV, HIMBO-compatible):

| mod | author, version | distance design | permissions | note |
|---|---|---|---|---|
| **SkySight Skins 2025 (6580, installed)** | fadingsignal, 2.0.2 (2025-05-28) | "True to vanilla style ... carefully optimized for its resolution to ensure proper texel density" | upload "not allowed ... under any circumstances"; modification allowed with credit; conversion not allowed; asset use allowed with credit; dependent mods may publish "AS LONG AS IT REQUIRES THE ORIGINAL MOD" | top pick: already owned, measured 0.46/0.67 body and 0.66/1.48 head; FOMOD plan installed the BETTERMALES_UNCUT body option (BASELINE says HIMBO-Uncut - recheck on reorder) |
| Simply Skin Male (107637) | SpringHeelJon, 2.1 (2025-01-08) | "true to vanilla style ... referencing Bethesda's original textures"; 2x vanilla (2K face, 4K body) | "offered free to use in your own projects without needing to contact me first ... Share your own mod with the same open permissions ... CANNOT sell" | most open terms; "VANILLA BODY ONLY" (HIMBO nude fit [unverified]) |
| Fried's Male Skin (23854) | TheFriedturkey, 2.0 (2019-03-09) | "hand sculpted ... simply a vanilla texture replacer" | upload not allowed; modification allowed with credit; conversion not allowed; asset use with credit | old; vanilla-UV feet |
| Tempered Skins for Males (7902) | traa108, 2.06 (2020-09-29) | "hand painted veins"; normals "much closer to vanilla"; HIMBO-recommended | not fetched (adult); description as 8505 | |
| Vitruvia (9112) | mandragorasprouts, 1.07 (2019-09-29) | "hand-painted diffuse"; face normals "close to vanilla look" | not fetched (adult) | |

Also seen: BnP Male 2.2 (photoscan, gated), LOVERBOY 2.6 ("Upscayl ...
upscale vanilla assets", gated), Fine Face Textures for Men (face only,
"NEXUS EXCLUSIVE", no modification).

## What this implies

1. Male: put SkySight above The New Gentleman. Measured gain on every map;
   also restores vanilla `_sk`. SkySight also ships 22 meshes (high-poly
   feet + 18 open-toed footwear) that lose to HIMBO / TNG / HIMBO Refits /
   Lords of the Reach today and would flip 18 HIMBO-shaped footwear meshes
   to vanilla-shape after the move, so its `meshes` folder is hidden
   (`meshes.mohidden`, reversible) as part of the restore: texture-only
   effect, no VFS change for any mesh.
2. Female: reorder Reverie above CBBE (tone 0.89, better normals; needs
   vanilla `_sk` restored separately) - the BASELINE decision - with Lucid
   Skin CBBE (vanilla-styled, open terms) as the measured trial if tone is
   still short. An Ensrick "sharpened mip chain" recipe on whichever female
   diffuse wins is the cheap distance fix (hf 1.04x at u1.0); it does not
   address tone.

Status 2026-09-02 10:06 (executed): SkySight 10 -> 13 (TNG 12,
transaction `20260902T150554430Z-ad9da584547b`, `meshes.mohidden`),
Reverie 9 -> 90 (CBBE 89, `20260902T150554563Z-2186a81b488a`), plus
`Ensrick - Vanilla Skin Soft-Light Maps` at row 237
(`20260902T150554695Z-a8bcf3daafe6`, six vanilla `_sk` maps, recipe
`overlays/ensrick-vanilla-skin-soft-light-maps/build.py`). Launch PASS
`records/launch-verify-20260902-100735.md` (menu 31.4 s, save 41.7 s).
Post-move matrix on the files that win now (mid/far hf / tone vs vanilla):

| map | before (winner) | after (winner) |
|---|---|---|
| femalebody_1 | CBBE 0.62 / 0.70 | Reverie 0.66 / **0.89** |
| femalebody_1_msn | CBBE 0.85 / 0.94 | Reverie 1.58 / 1.86 |
| femalebody_1_s | CBBE 0.34 / 0.93 | Reverie 0.71 / 1.78 |
| femalehead | CBBE 0.48 / 1.37 | Reverie 0.47 / 0.75 |
| femalehead_msn | CBBE 0.47 / 1.01 | Reverie 1.04 / 1.18 |
| femalehead_s | CBBE 0.26 / 0.37 | Reverie 0.31 / 0.47 |
| malebody_1 | TNG 0.29 / 0.42 | SkySight **0.46 / 0.67** |
| malebody_1_msn | TNG 0.41 / 1.10 | SkySight 0.81 / 1.10 |
| malebody_1_s | TNG 0.46 / 0.38 | SkySight 0.42 / 0.39 |
| malehead | TNG 0.33 / 0.69 | SkySight **0.66 / 1.48** |
| malehead_msn | TNG 0.44 / 1.15 | SkySight 0.56 / 1.04 |
| malehead_s | TNG 0.20 / 0.42 | SkySight 0.39 / 0.84 |
| all six `_sk` | black / near-black stubs | overlay = vanilla, 1.00 / 1.00 |

Still short of the bar on body tone (0.89 female is at it, 0.67 male is
not) and on every spec map; the Lucid Skin trial (female) and a male
candidate remain user decisions on #166. Not yet seen in game.
3. Any new skin gets the same table before install: `py -3 audit/inspect_mod.py`
   now flags `soft-at-distance` below 0.70 of vanilla; `mip_retention.py`
   gives the per-map table.

## Method

`mip_retention.py` decode/compare/resharpen; scratch driver `mip_run.py`
(session scratchpad) with resharpened outputs under `scratchpad/mip_female`
and `scratchpad/mip_male` only. Resharpen recipe: decode mip 0 -> Lanczos
downsample each level from mip 0 -> Pillow UnsharpMask(radius=1.0,
percent=100|150, threshold=0) on RGB -> uncompressed RGBA DDS -> texconv
`-f BC7_UNORM -bc x`. Output byte size equals the source (22,369,796 for
the 4K bodies).
