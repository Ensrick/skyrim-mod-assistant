# Face eye-makeup audit - 2026-09-02 (#165)

Status: **diagnosed, no change made**. Read-only pass over MO2 `Default`
(modlist.txt snapshot 2026-09-02), the vanilla BSAs, and the Community Shaders
1.8 source that ships in this build. Numbers come from
`audit/mip_retention.py` decoding (texconv 2026.4.1.1 -> R8G8B8A8) plus the
scratch scripts named in "Method"; nothing was launched.

## Verdict in one paragraph

The dark ring is Bethesda's own baked NPC makeup: every vanilla NPC head
carries a pre-rendered tint texture (eyeliner + upper/lower eye-socket
layers) in `Skyrim - Textures*.bsa`, and no installed mod replaces those
files or the NPC tint data. What changed against a vanilla game is not the
ring but what fills it: both installed skin sets ship a near-black or
all-black subsurface (`_sk`) map, which is the texture the vanilla
soft-lighting wrap multiplies by. With that wrap gone (and Advanced Skin off
since #144) shadowed sockets are lit only by direct diffuse, so the baked
makeup reads as a hard, unnatural ring. The installed head diffuses
themselves make the ring slightly *lighter* than vanilla, not darker.

## Winning files (loose files beat BSAs; MO2 priority = enabled-mod index, 0 = top of modlist.txt)

| texture | winner | prio | stored | loser(s) |
|---|---|---|---|---|
| `female/femalehead.dds` | CBBE 2.0.3 | 141 | 1024 BC7, 11 mips | Reverie - Skin 1.11.2 (202): 4096 BC7 |
| `female/femalehead_msn.dds` (+ per-race `*female/femalehead_msn.dds`) | CBBE | 141 | 1024 BC7 | Reverie: 2048 BC7 |
| `female/femalehead_s.dds` | CBBE | 141 | 2048 BC4 | Reverie: 4096 BC4 |
| `female/femalehead_sk.dds` | CBBE | 141 | 1024 BC7, mean lum 0.03-0.06 | Reverie: 4x4 BC1 **black** |
| `female/femaleheaddetail_age40/age50/rough/frekles.dds` | Reverie - Skin | 202 | 2048 BC7 | vanilla 1024/512 BC1 (CBBE ships none) |
| `male/malehead.dds` (+ per-race `_msn`) | The New Gentleman 4.2.5 | 198 | 2048 BC7 | SkySight Skins 2.0.2 (201): 2048 BC7 |
| `male/malehead_msn.dds` | The New Gentleman | 198 | 2048 BC7 | SkySight: 2048 BC7 |
| `male/malehead_s.dds` | The New Gentleman | 198 | 2048 BC4 | SkySight: 2048 BC7 |
| `male/malehead_sk.dds`, `malebody_1_sk.dds`, `malehands_1_sk.dds` | The New Gentleman | 198 | 4x4 BC1 **black** (152 bytes) | vanilla 512/256 BC1 (SkySight ships none) |
| `male/maleheaddetail_age40/age40rough/age50/rough01/rough02.dds` | SkySight Skins | 201 | 2048 BC7 | vanilla |
| `male/blankdetailmap.dds` | CBBE | 141 | 64 BC3, shader factor 1.016 (neutral) | TNG 4x4 (1.000), SkySight, Reverie, vanilla (1.038) |
| `character assets/tintmasks/female{upper,lower}eyesocket.dds`, `femalenordeyelinerstyle_01.dds` | CBBE | 141 | 512 BC1 | Reverie 2048; vanilla 512 RGB |
| male tintmasks (`male{upper,lower}eyesocket`, `redguardmaleeyelinerstyle_01`) | vanilla | - | 512 RGB | none |

Both installed "intended" sets lose: BASELINE.md:184 records Reverie as the
female skin and :186 SkySight as the male skin, but CBBE sits above Reverie
(41 texture collisions, `records/active-file-conflicts.md:58`) and TNG's
bundled skin sits above SkySight (29 textures, :59). The FOMOD plan for
Reverie installed its CBBE-compat core (`records/fomod-plans/64314-reverie.json`),
i.e. it was meant to overwrite CBBE. Separate decision; see "Options".

## Who supplies NPC faces

`facegendata` providers in the enabled set (facegeom NIF / facetint DDS):
vanilla BSAs (2549 skyrim.esm heads), Vanilla Hair Remake SMP - NPCs
(2436 facegeom NIFs in its BSA, **no facetint** - it re-exports heads for SMP
hair and leaves the baked tint alone), Ensrick VHR compatibility (32 loose
facegeom), USSEP 88/86, Interesting NPCs 644, Beyond Reach 686 + 263 loose +
233, Bruma 1177, VIGILANT 110/112 loose, Wyrmstooth 86, Gray Cowl 75, CRF 14,
Moonpath 37, Solitude Docks 33, INIGO 5/10. No NPC beauty overhaul is
installed, so vanilla NPCs wear Bethesda's facegen.

A facegen head NIF (checked `facegeom/skyrim.esm/0001325c.nif` in vanilla and
`dragonborn.esm/0001773b.nif` in the VHR BSA) binds: slot 0 the race head
diffuse (`Actors\Character\Female\FemaleHead.dds`), slot 1 the per-race
`_msn`, slot 2 `FemaleHead_sk.dds`, slot 3 the detail map
(`BlankDetailmap.dds` or `FemaleHeadDetail_*.dds`), slot 6 the baked tint
`FaceGenData\FaceTint\Skyrim.esm\<id>.dds`, slot 7 `FemaleHead_S.dds`. Both
profile INIs leave `bUseFaceGenPreprocessedTextures` at its default (1), so
NPCs use that baked tint; tintmasks only touch the player.

Reference counts across the 2549 vanilla skyrim.esm heads: 1395 use the
blank detail map, 297 `maleheaddetail_age40`, 180 `age40rough`, 152
`rough01`, 118 `femaleheaddetail_age40`, 79/77/74/71/62 the rest - so the
Reverie/SkySight detail maps that leak through the losing mods are on ~45%
of NPC faces.

## How the face shader combines them (CS `package/Shaders/Lighting.hlsl:674-682`, vanilla-equivalent)

```
detail = 3.984375 * (detailTexel + 1/255)          // ~1.0 at texel 63/255
tint   = 2 * tintTexel * raw * (1 - raw)           // tintTexel = baked facetint
base   = (raw * raw + tint) * detail               // raw = head diffuse
```

A black tint texel gives `raw^2`: the darkness of the ring is authored in
the facetint, then scaled by the diffuse.

Soft lighting (`Common/LightingEval.hlsli:119,138`):
`diffuse += lightColor * GetSoftLightMultiplier(NdotL) * rimSoftLightColor`,
where `rimSoftLightColor` is the `_sk` texel (`Lighting.hlsl:1526,1830`). A
black `_sk` removes the wrap entirely. `material.SubsurfaceColor = skinsk`
(`:1850`) is only reached under `CS_SKIN`, i.e. Advanced Skin, which #144
turned off. The CS "Subsurface Scattering" feature is loaded
(CommunityShaders.log 09:34:10) and is a screen-space blur; its source does
not read `_sk`.

## Eye-region measurements

Masks: union of vanilla `femaleuppereyesocket` + `femalelowereyesocket`
(luminance > 40/255) = 10,609 px at 512; reference = vanilla `femalehead_cheeks`
minus the eye mask = 22,459 px. Male: 14,684 / 17,709 px. Masks are nearest-
resampled to each texture's own size. Luminance 0-1, mip 0.

Head diffuse, eye mean / cheek mean:

| sex | vanilla | winner | loser |
|---|---|---|---|
| female | 0.250 / 0.293 = **0.854** | CBBE 0.237 / 0.265 = **0.895** | Reverie 0.259 / 0.277 = 0.935 |
| male | 0.284 / 0.274 = **1.037** | TNG 0.280 / 0.287 = **0.976** | SkySight 0.272 / 0.285 = 0.954 |

Shader composite `raw^2 + 2*tint*raw*(1-raw)` with each of 12 vanilla
skyrim.esm facetints (blank detail), eye / cheek luminance:

| sex | vanilla diffuse | winner | loser |
|---|---|---|---|
| female | 0.273 / 0.344 = **0.787** | CBBE 0.258 / 0.313 = **0.815** | Reverie 0.280 / 0.326 = 0.847 |
| male | 0.238 / 0.254 = **0.967** | TNG 0.235 / 0.267 = **0.905** | SkySight 0.227 / 0.265 = 0.884 |

The baked facetints carry the ring: eye / cheek luminance of the tint texel
per female NPC = 0001325c 0.67, 00013267 **0.51**, 00013268 0.65, 00013269
0.82, 00013289 0.76, 0001326a 0.91, 00013277 0.94, 00013282 0.98, 00013265
1.03, 00013271 1.05, 00013278/0001327a 1.00. Males: 0001328d **0.53**,
0001328f 0.64, 00013264 0.81, 00013288 0.81, 00013298 0.83, 00013284 0.89,
rest 1.00-1.06 (00013275 1.58 is a dark-elf tint).

Detail maps (shader factor, eye / cheek): vanilla age40 1.000/0.975, Reverie
age40 1.009/1.007; vanilla rough 1.029/0.939, Reverie rough 0.974/0.958;
vanilla frekles 0.972/0.928, Reverie 0.991/0.976; male age50 vanilla
0.824/0.836 vs SkySight 0.881/0.901. All within 3% of neutral around the
eyes; not a source.

Subsurface `_sk` (soft-light wrap colour), mean luminance, RGB:

| map | vanilla | winner | loser |
|---|---|---|---|
| femalehead_sk | 0.37 (0.48, 0.33, 0.30) | CBBE 0.03-0.06 (0.09-0.15, 0.02, 0.02) | Reverie 0.00 (4x4 black) |
| femalebody_1_sk | 0.44 (0.55, 0.40, 0.36) | CBBE 0.04 (0.11, 0.02, 0.01) | Reverie 0.00 |
| malehead_sk | 0.19 (0.30, 0.14, 0.13) | TNG 0.00 (4x4 black) | - |
| malebody_1_sk | 0.18 (0.28, 0.14, 0.12) | TNG 0.00 | - |

Normal-map slope in the eye region (|xy|/z, vanilla-space): female vanilla
11.4 vs cheek 2.05; CBBE 1.21 / 1.85; Reverie 1.97 / 1.99. Male vanilla 2.47
/ 44.7; TNG 0.93 / 36.7; SkySight 1.48 / 50.6. The installed normals are
flatter around the eyes than vanilla (less self-shadowing, so the ring is
tint, not geometry).

Specular eye / cheek (values are 0.01-0.05): female vanilla 1.19, CBBE 0.83,
Reverie 0.89; male vanilla 0.80, TNG 1.04, SkySight 1.32.

**Male lids are the one place the modded diffuse does darken.** On the
upper-lid band (the earlier pass's `eye_region.json`, lid mask rather than
the socket union above) the male diffuse reads vanilla 0.90 of cheek, TNG
0.77, SkySight 0.68; the socket-union numbers above agree in direction
(vanilla 1.037, TNG 0.976, SkySight 0.954). Reordering SkySight above TNG
therefore does **not** lighten male eyes; it darkens the lid band slightly
more. Female lids are Bethesda's baked eyeliner either way (upper-lid tint
0.88 of cheek on average, 10th percentile 0.52).

Tintmasks (player only): CBBE's eye masks integrate to 0.29 / 0.39 / 0.23 of
vanilla (upper socket / lower socket / eyeliner), Reverie's 0.56 / 0.56 /
0.58. The player character gets *less* makeup than vanilla; NPCs are
unaffected because their tint is baked.

## Options, narrowest first (user decides; nothing installed)

1. **Restore the soft-light wrap only.** Hide (MO2 `.mohidden`) TNG's three
   4x4 `_sk` stubs so vanilla `malehead_sk/malebody_1_sk/malehands_1_sk`
   load, and provide vanilla `femalehead_sk/femalebody_1_sk/femalehands_1_sk`
   above CBBE. Vanilla assets cannot be redistributed, so the female half is
   a *recipe* (extract from the user's own `Skyrim - Textures0.bsa`; the male
   half is a hide list, distributable). Zero art change; A/B by eye in game.
   Same lever moves #166's "matte".
2. **Put the intended skins on top** (Reverie above CBBE, SkySight above
   TNG). Fixes the mixed sets, but Reverie also ships a black `_sk`, so
   option 1's female half is still needed; SkySight ships no `_sk`, so
   vanilla's returns for males automatically.
3. **Change the makeup itself.** The ring is NPC tint data + Bethesda's
   bake. Levers: (a) an Ensrick *recipe* that lightens the eyeliner/socket
   band of the winning facetint DDS files in place (mask from the vanilla
   `female*eyesocket`/`eyeliner` tintmasks, lift the tint texel toward the
   cheek tint by a chosen fraction, recompress BC3; regenerated locally from
   the user's own BSAs, never shipped, because the inputs are Bethesda's), (b)
   an NPC facegen pack that re-bakes with lighter alphas (none installed;
   permissions + regeneration recipe needed), or (c)
   `bUseFaceGenPreprocessedTextures=0` in `Skyrim.ini` so NPC tints are
   composited at runtime from the installed (weaker) CBBE masks [unverified
   in this build; runtime cost and known face-mismatch risk, INI-only so
   trivially reversible for an A/B].
4. **Live discriminator before any of the above:** toggle CS Screen Space GI
   / ambient occlusion in the CS menu while looking at a female NPC. If the
   ring softens with SSGI/AO off, the socket darkness is shading (options 1
   and 2 apply); if it stays, it is the bake (option 3).

Status 2026-09-02 10:06 (team-lead ruling, executed): options 1 and 2 are
live and reversible. (1) `Ensrick - Vanilla Skin Soft-Light Maps` (top
row, transaction `20260902T150554695Z-a8bcf3daafe6`) puts Bethesda's six
`_sk` maps above every skin mod - `overlays/ensrick-vanilla-skin-soft-light-maps/build.py`,
ledger `distribution: recipe`. (2) Reverie now sits directly above CBBE
(90 vs 89) and SkySight directly above TNG (13 vs 12, meshes hidden). Launch
PASS `records/launch-verify-20260902-100735.md` (menu 31.4 s, save 41.7 s).
Not yet seen in game. The reorder does not lighten male lids (SkySight's
diffuse is darker there than TNG's); the overlay is the lever for the
socket shading.

**A/B for the user (same NPC, same light):** stand in front of Gerdur or
Delphine in Riverwood (or any female NPC indoors), look at the eye ring;
then in MO2 untick `Ensrick - Vanilla Skin Soft-Light Maps` only, relaunch,
same spot. Ticked = vanilla soft-light wrap back (sockets filled with warm
subsurface colour); unticked = the stubs (hard ring). Rollback of either
fix = one checkbox (the overlay) or the two priority transactions above.
For the make-up itself the test is with CS SSGI/AO toggled (option 4).

## Method

Scratch scripts (session scratchpad, not committed): `resolve_winners.py`
(loose + BSA provider resolution against `profiles/Default/modlist.txt` and
`plugins.txt`), `extract_and_info.py`, `nif_and_stubs.py` (NIF texture-slot
strings, detail-map reference counts), `eye_region.py` and `sk_s_region.py`
(mask-based means, composite). Shader lines quoted from
`C:\Users\danjo\source\repos\_rebuild_CommunityShaders\package\Shaders`.
Companion: `records/skin-distance-detail-audit-2026-09-02.md` (#166).
