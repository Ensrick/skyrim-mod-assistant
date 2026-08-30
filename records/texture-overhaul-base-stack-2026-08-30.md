# Skyrim SE/AE texture-overhaul base stack — 2026-08-30

Status: research complete; no install, enable/disable, Keep/Skip, plugin, MO2
profile, game, or Nexus-curation state was changed.

## Decision summary

For this build, the strongest stable and performance-conscious starting point
is **Skyland AIO 1K as the broad architecture-and-landscape base**, installed
after SMIM, with its water-colour, road-sign, lit-sign and pre-generated LOD
options omitted. This is not a blanket endorsement of every optional component.
The current 1K archive is a mixed-resolution package: it retains 2K and a small
number of 4K assets where the author did not reduce them, while containing
nothing above 4K. That is a better match for the project's source-aware texture
policy and the machine's RTX 3080 Ti (12,288 MiB VRAM) than either a uniform 2K
or 4K base.

**Skyrim 202X should not be installed wholesale over Skyland.** Its current 1K
downscale collides with 846 Skyland DDS paths while also supplying more than a
thousand unrelated paths. The result would be neither a coherent Skyland look
nor a coherent 202X look, and would increase mesh, parallax, clutter and
permission-management work. If the user strongly prefers an individual 202X
surface after an in-game comparison, use the original author's package as a
selective overwrite source and document every winning path. Do not redistribute
extracted or modified 202X assets.

There are two legitimate landscape alternatives, not upgrades that should be
blindly stacked:

- **Skyking Fantasia Landscapes 1.6** is the current colourful, high-fantasy
  art-direction alternative. It replaces almost all of Skyland's landscape
  layer while leaving Skyland architecture useful underneath.
- **Vanaheimr Landscapes AIO 5.5** is the strongest current grounded landscape
  competitor and has vanilla, complex-material and True PBR editions. Its PBR
  edition is materially more complicated and should be treated as the later
  high-fidelity branch, not slipped into the stability baseline.

No released “Skyland PBR” package supersedes Skyland AIO as of the audit date.
The 2026 Skyland AIO optional file is **complex parallax/material**, not True
PBR. Skyking's PBR and Complex Parallax Toolkit is a creator/conversion tool,
not a replacement texture suite.

## What is currently in the live profile

Read-only inspection of the active MO2 `Default` profile found:

- SMIM, SMIM Quality Addon and the Farming CC patch;
- Community Shaders AIO, source-built for runtime 1.7.99;
- Lux, Lux CS, Lux Orbis, Lux Via and their current resources/patch layer;
- Water for ENB, its USSEP patch and the project Lux/Community Shaders water
  patch;
- Skyking Signs, Skyking Unique Signs and their Bruma/Interesting NPCs patches.

It did **not** find Skyland AIO, standalone Skyland Landscapes, Fantasia,
Vanaheimr, Skyrim 202X, Skyland Bits and Bobs, Skyland LODs, or Nature of the
Wild Lands enabled. Nature of the Wild Lands remains a separate, explicitly
deferred tree decision. The installed Skyking sign mods are not evidence that a
Skyland texture base is installed.

## Do not conflate the Skyking products

| Product | Current role | Current file state checked 2026-08-30 | Recommendation |
|---|---|---|---|
| [Skyland AIO](https://www.nexusmods.com/skyrimspecialedition/mods/34179) | Broad architecture, dungeons and landscapes, with some meshes and FOMOD options | Main 2K file 4.32 / 6,681 MiB and 1K file 4.32 / 1,998 MiB were uploaded 2023-11-18. Page activity in 2026 is the new optional CP file, not a new main AIO texture pass. | Preferred mature base; use 1K initially. |
| [Skyland – A Landscape Texture Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/3820) | Landscape-only Skyland 5.2 | 1K 378 MiB and 2K 1,341 MiB files uploaded 2023-09-27 | Redundant when AIO's landscape component is selected. Relevant only if using Skyland landscape without Skyland architecture. |
| [Skyking Fantasia Landscapes](https://www.nexusmods.com/skyrimspecialedition/mods/107256) | Newer, bold and colourful landscape-only art direction | 1.6 files uploaded 2026-02-13; page/addon updated 2026-04-29; 1K/2K/4K at 461/1,532/6,015 MiB | Alternative landscape layer, not an AIO successor. Use over Skyland architecture if chosen. |
| [Skyland Bits and Bobs](https://www.nexusmods.com/skyrimspecialedition/mods/95032) | Clutter and furniture complement with meshes; explicitly not included in AIO | Main/full and Performance payloads are 1.91 from 2024-09-05; CP addon 1.94 uploaded 2026-07-23 | Separate decision. Performance file is the only plausible starting point, followed by object-scale policy review. |
| Skyland AIO Complex Parallax optional file | Material/height maps for AIO | File 791745, version 4, 1,042 MiB, uploaded 2026-08-18 | Current AIO CP addon; use instead of the older standalone Skyland landscape CP packages. Not PBR. Defer until the non-parallax base is stable. |
| Fantasia Complex Parallax | Material/height maps plus Terrain Helper ESP for Fantasia | Current single-resolution-independent CP package 1.6; green/yellow tundra variants | Only with Fantasia; not with Skyland landscapes or a PBR landscape layer. |
| Bits and Bobs Complex Parallax | Material maps for Bits and Bobs | 1.94, 314 MiB, uploaded 2026-07-23 | Only after Bits and Bobs is accepted and its mesh conflicts are resolved. |
| [Skyland LODs](https://www.nexusmods.com/skyrimspecialedition/mods/87412) | Pre-generated vanilla-world architecture/landscape LOD and Occlusion plugin based on Skyland | 1.1, 1,266 MiB, uploaded 2023-03-20 | Preview/convenience only. Do not ship it as final LOD for this modlist. Generate LOD from the final worldspace, trees, cities and texture winners. |

Skyland's author describes AIO as the architecture/landscape component and Bits
and Bobs as the clutter component, and explicitly identifies the LOD and complex
parallax downloads as companions rather than replacements. The Fantasia author
likewise calls it a new, deliberately unconstrained fantasy approach rather
than another Skyland-compatible landscape pass.

## Current comparison matrix

| Candidate | Coverage and gaps | Art direction | Material workflow | Resolution/performance | 2026 judgment |
|---|---|---|---|---|---|
| Skyland AIO 4.32 | Very broad vanilla/DLC architecture, settlements, forts, Nordic/Dwemer ruins, caves/mines and landscapes. Does not replace the separate full clutter suite, actors, gear, plants or trees. | Cohesive, grounded, photogrammetry-derived and close to the user's historical/mythic target. | Conventional diffuse/normal base; current optional complex-parallax material pack. A few base `_p` files are masks, not proof of parallax. | Author 1K and 2K choices; 1K archive already preserves some larger surfaces. | Best mature baseline. Main payload is older, but the broad coverage is stable and the CP companion is actively maintained. |
| Fantasia 1.6 | Landscapes, roads, bridges, mountains, caves, mines, resources and all DLC; not city architecture. Whiterun city grass remains a city-texture concern. | Stronger colour, larger bold forms, explicitly fantasy-inspired. | Optional complex parallax; author directs users to PGPatcher and Terrain Helper. | Author 1K/2K/4K choices. | Best Skyking landscape alternative if the user wants a markedly more fantastical world. Less aligned with the current grounded brief. |
| Skyrim 202X 10.5.2 | Broad architecture, landscapes, dungeons, clutter, plants, some actors/armor, plus 334 meshes in the 1K archive. Not a clean category-bounded base. | High-contrast, photoreal/material-showcase look. Quality and colour language vary across its long development history. | Legacy/current complex-parallax workflow; separate Complex Terrain Parallax 1.5 was last updated in 2022. Not True PBR. | Original current three-part set is about 24.3 GiB compressed. Official downscales are 1K/2K/4K at 1.61/5.13/13.01 GiB. | Still credible, but no longer the cleanest full base for this project. Use only as a deliberate alternative base or for individually approved winners. |
| Vanaheimr AIO 5.5 | Full worldspace ground, ice, mountains and roads across Tamriel, Solstheim, Forgotten Vale and Soul Cairn. Excludes architecture/farmhouses, Northern Roads, mines/caves and ore veins. | Realistic, restrained and Skyrim-faithful. | Separate vanilla, complex-material and True PBR editions. PBR uses redirected `textures/pbr` assets, PBR meshes/JSON and an ESP. | 1K/2K/4K in every material workflow. Current PBR files are 665 MiB/2,142 MiB/5,288 MiB. | Best current landscape competitor and the preferred high-fidelity PBR landscape, but not the low-risk first layer. |
| [Vanilla PBR AIO 1.33](https://www.nexusmods.com/skyrimspecialedition/mods/174091) | Broad vanilla/DLC architecture, clutter, actors and dungeons; explicitly omits landscapes and gear, although it includes mountains. | Vanilla-faithful PBR conversion. | True PBR, Community Shaders and PGPatcher; designed around SMIM. | One 11.49 GiB archive; author says typical maps are 2K diffuse/1K normal/1K RMAOS/512 height, with some 4K and a few 8K. | Cutting-edge 2026 architecture option, but presently fails the project's hard 4K ceiling without an authorised lower-resolution edition and is young relative to Skyland. Do not adopt wholesale now. |
| Atlantean 2.0 / Tomato 4.1 | Competitive landscape-only packs | Stylised-realistic alternatives | Complex material/parallax, not True PBR | Both offer 1K/2K/4K | Credible alternatives, but neither supplies a decisive advantage over the more cohesive Skyland baseline or the current Vanaheimr PBR branch. Keep as comparison references, not stack layers. |

## Archive-level findings

Current author archives were downloaded through the official Nexus API into the
ignored `work/texture-overhaul-2026` evidence area and inspected without adding
them to MO2. DDS dimensions, mip counts and DX compression were read from
headers; paths were normalised to Skyrim `Data`-relative destinations. For
FOMOD archives, duplicate option sources were collapsed by destination, so raw
Skyland counts describe the set of available payloads rather than one exact
FOMOD selection. Vanaheimr's effective example is core + blue ice + mixed
tundra.

| Inspected payload | Unique DDS | NIF | DDS size distribution (max dimension) | Formats | Approx. full resident mip-chain footprint* |
|---|---:|---:|---|---|---:|
| Skyland AIO 1K 4.32 | 1,920 | 172 | 44 ≤512, 1,612 ≤1K, 253 ≤2K, 11 ≤4K, 0 >4K | 1,064 BC7; 712 BC1; 143 BC3; 1 uncompressed | 2,495 MiB |
| Fantasia 1K 1.6 main | 352 | 0 | 11 ≤512, 314 ≤1K, 15 ≤2K, 12 ≤4K, 0 >4K | 352 BC7 | 597 MiB |
| Skyrim 202X 1K 10.5.2 | 1,860 | 334 | 114 ≤512, 1,585 ≤1K, 128 ≤2K, 33 ≤4K, 0 >4K | 1,199 BC7; 350 BC1; 156 BC3; 127 BC4; 28 BC2 | 2,277 MiB |
| Skyland Bits and Bobs Performance 1.91 | 674 | 135 | 28 ≤512, 503 ≤1K, 143 ≤2K, 0 >2K | 658 BC7 plus 16 other | 1,046 MiB |
| Vanaheimr PBR 1K 5.5 effective example | 505 | 199 (+258 PGPatcher JSON) | 9 ≤512, 453 ≤1K, 35 ≤2K, 8 ≤4K, 0 >4K | 299 BC7; 114 BC4; 92 BC1 | 654 MiB |
| Skyland AIO CP 4 | 908 | 0 | 9 ≤512, 783 ≤1K, 113 ≤2K, 3 ≤4K | 875 BC7; 31 BC4; 2 BC1 | 1,382 MiB |
| Fantasia CP 1.6 | 260 | 0 | 1 ≤512, 241 ≤1K, 12 ≤2K, 6 ≤4K | 259 BC7; one 1×1 uncompressed cubemap | 439 MiB |
| Bits and Bobs CP 1.94 | 293 | 0 | 10 ≤512, 225 ≤1K, 58 ≤2K | 289 BC7 plus 4 other | 469 MiB |

\*This is a relative upper-bound calculation from block-compressed dimensions
and the shipped mip count, not an assertion that the engine keeps every map
resident simultaneously. It is useful for comparing the pressure created by
base + material add-ons. At 4K output resolution, the frame buffers,
Community Shaders, trees, city additions and generated LOD also consume GPU
memory; a nominally capable 12 GiB card is not a reason to fill all 12 GiB with
texture payload.

Important path facts:

- Skyland AIO and Skyrim 202X share **846 DDS destinations**. A full 202X layer
  would replace about 44% of the inspected Skyland DDS set while leaving the
  rest Skyland, then add 1,348 other files. This is a blend, not a clean upgrade.
- Fantasia shares **342 of its 352 DDS destinations** with Skyland AIO. That is
  exactly the expected landscape-replacement relationship: use one landscape
  winner, not both as independent content.
- Bits and Bobs shares **280 paths with current SMIM** (164 DDS, 116 NIF).
  This is intentional but makes overwrite direction material. The author says
  Bits and Bobs should load after SMIM; the final conflict report must verify
  every losing SMIM mesh is paired with the expected texture path.
- Skyland AIO shares **96 paths with SMIM** (80 DDS, 16 NIF). Skyland's own
  SMIM option/patch should be selected and Skyland should win those intended
  conflicts.
- The inspected Skyland AIO payload and Water for ENB share only
  `textures/water/defaultwater.dds` and `textures/water/riverflow.dds`.
  Omit Skyland water-colour choices and let Water for ENB win both.
- Vanaheimr PBR appears to have little direct texture-path overlap because its
  material textures live under `textures/pbr`; it replaces the rendered
  material through meshes, JSON generation and plugin records. A low loose-file
  conflict count therefore does **not** mean low integration cost.

### Resolution-policy result

The inspected 1K variants contain no DDS dimension over 4096. That satisfies
the absolute ceiling. The name “1K” is not literal: every candidate preserves
some larger atlases or large-surface maps. A `/clutter/` path is also not enough
to classify an asset as small clutter—several are workbenches, statues,
braziers, large signs or shared atlases. The following still needs object-scale
review before Bits and Bobs can be declared fully policy-compliant:

- Bits and Bobs Performance has 116 `/clutter/`-path DDS files whose maximum
  dimension exceeds 1K;
- Skyrim 202X 1K has 51;
- raw Skyland AIO options have 76, heavily dominated by optional road-sign
  atlases that should not be selected because Skyking Signs already owns them.

This is not grounds to privately downscale and redistribute the files. These
authors restrict modification and redistribution. Use a compliant author file,
obtain permission, or omit an asset.

### Mipmap QA finding

All inspected Fantasia and 202X main textures have mip chains. Skyland AIO 1K
contains eight world-surface DDS files with a one-level mip chain:

```
textures/dungeons/caves/icecavewall01.dds
textures/dungeons/caves/icecavewall02.dds
textures/dungeons/caves/icecavewall04.dds
textures/dungeons/caves/icefrozen01.dds
textures/dungeons/mines/minefloordirt01_n.dds
textures/architecture/riften/riftenmarble01.dds
textures/architecture/farmhouse/rope01.dds
textures/architecture/windhelm/whlogend_n.dds
```

These are not all UI/lookup textures, so missing mips can produce distance
aliasing/shimmer and unnecessary bandwidth. This is a concrete acceptance-test
item: verify the winning files in the exact FOMOD selection and compare the 2K
archive/author response before the base is frozen. Because Skyland's permissions
require author approval for modifications, a public modpack must not ship
privately regenerated versions without permission. No upstream or project issue
was opened during this research because Skyland has not been accepted or
installed yet and intent has not been established.

## Recommended stable/performance branch

This is an installation plan for later approval, not an installation performed
by this task.

1. Keep SMIM and its accepted mesh patches as the mesh foundation.
2. Install **Skyland AIO 1K** after SMIM.
3. In Skyland's FOMOD, select the broad vanilla/DLC architecture and landscape
   modules, Blended Roads and the SMIM integration. Choose one restrained
   farmhouse/mountain/tundra colour set after screenshot comparison.
4. Do not select Skyland road signs, lit signs or sign add-ons; current Skyking
   Signs/Unique Signs should remain the winner. Do not select Skyland water
   colour or water textures; Water for ENB should remain the winner. Treat the
   night sky as a separate visual decision, not a default part of the base.
5. Do not install Skyland LODs in the final list.
6. Leave Skyland AIO Complex Parallax disabled for the first stability and
   visual-cohesion pass. Once the ordinary texture/mesh base is stable, test the
   current AIO CP addon as its own reversible layer with PGPatcher and the active
   Community Shaders build.
7. Evaluate **Bits and Bobs Performance** separately. If accepted, place it
   after SMIM and Skyland AIO, audit its 280 SMIM conflicts, and let later
   dedicated hero-object replacers win. Do not install the full-resolution file
   under the current policy.
8. Let Lux/Lux CS win any lighting-specific meshes or textures only where that
   is required for functional light behaviour; resolve individual mesh conflicts
   by evidence, not a global “Lux always wins” rule.
9. Install future city overhauls, trees/flora (including a later Nature of the
   Wild Lands decision), water and targeted unique replacers after the broad
   base according to their verified path/record requirements.
10. After the worldspace, texture, tree and patch set is final, run PGPatcher if
    used, generate terrain LOD with xLODGen, then TexGen and DynDOLOD. The final
    generated outputs must reflect Bruma, Beyond Reach, later city expansions,
    final tree meshes and every texture winner.

This branch gives a coherent world immediately, retains the user's 4K hard cap,
and leaves room in 12 GiB VRAM for Community Shaders, Lux, dense locations,
future trees and the 4K display target. It also makes visual A/B testing useful:
any later replacer has a known Skyland baseline rather than a half-Skyland,
half-202X floor.

## Optional higher-fidelity branch

If the user chooses material realism over the lower-risk baseline, the coherent
2026 branch is:

1. SMIM;
2. **Vanilla PBR AIO** for architecture/clutter/dungeons/actors;
3. **Vanaheimr Landscapes AIO PBR 1K initially**, with 2K considered only after
   captured VRAM and frametime tests;
4. Vanaheimr's current documented mesh requirements: Enhanced Rocks and
   Mountains, Icy Mesh Remaster meshes/fixes, and Better Dynamic Snow 3.6 with
   the exact author choices;
5. Community Shaders True PBR support and PGPatcher, run with **True PBR only**
   for Vanaheimr (Complex Material and Parallax disabled), then final LOD
   generation.

This is more “cutting edge” than Skyland CP, but it is not presently the
recommended build because:

- Vanilla PBR AIO ships a few 8K textures and has no compliant lower-resolution
  package, violating the project's hard 4K ceiling;
- it is an 11.49 GiB single archive introduced in March 2026 and remains a
  faster-moving integration target;
- Vanaheimr PBR brings 199 meshes, 258 generator JSON files and an ESP, plus
  exact snow/rock/ice requirements and plugin-record conflict work;
- PBR LOD remains documented as work in progress by DynDOLOD, although current
  xLODGen/TexGen/DynDOLOD perform the needed sRGB-to-linear conversions;
- the live profile already has visual/runtime issues under investigation, so a
  renderer-wide material migration would obscure those tests.

The project should revisit this branch when an author-provided ≤4K Vanilla PBR
edition exists or permission is secured for a distributable compliant variant.
Vanaheimr alone cannot replace Skyland architecture; putting Vanaheimr PBR
landscapes on conventional Skyland architecture is technically possible, but it
creates a mixed material response that should be accepted only after a visual
test.

## Compatibility notes

- **Community Shaders:** conventional Skyland works without parallax. Skyland,
  Fantasia and Bits CP are complex-material/parallax packs; Vanaheimr PBR and
  Vanilla PBR are True PBR packs. These are distinct shader/data workflows.
  A closed 2026 Community Shaders issue reported broken terrain CP in 1.5.2 with
  Skyland AIO plus an older landscape CP package. It is not proof of a current
  1.7.99 defect, but the project's source build must be runtime-tested before a
  CP layer is accepted.
- **SMIM:** Skyland AIO and Bits and Bobs are designed around it, but both ship
  overlapping meshes/textures. Use their documented SMIM integration and keep a
  durable conflict map. Skyrim 202X calls SMIM a requirement and similarly
  expects its assets to overwrite SMIM, increasing the mixed-mesh risk if added
  selectively.
- **Water for ENB:** it is compatible with Community Shaders in the chosen
  Natural Shades setup. “for ENB” is not an exclusion rule. Water for ENB should
  own the two direct Skyland water conflicts; omit Skyland water colouring.
- **Lux/Lux CS:** texture-only architecture is generally compatible with cell
  lighting, but mesh replacements can affect light placement, emissives and
  shadow behaviour. Preserve Lux functional meshes unless a verified patch
  deliberately combines both changes.
- **Nature of the Wild Lands:** no tree overhaul is currently installed. Load
  the eventual tree pack after the broad texture base, resolve any landscape or
  plant-path overlaps intentionally, and generate tree LOD from final assets.
  Do not use third-party pre-generated tree billboards as the final answer.
- **City overhauls:** texture replacers normally cover vanilla texture paths used
  by JK/Spaghetti/Great City-style edits. Custom assets keep their own look.
  Overhauls that supply modified meshes or remapped UVs need per-path inspection;
  loading a diffuse from a different UV layout is not automatically safe.
- **New lands:** Skyland/Fantasia/Vanaheimr cover Bethesda's vanilla/DLC
  worldspaces, not arbitrary custom texture namespaces. Bruma, Beyond Reach and
  later new lands retain their own assets unless a purpose-built patch exists.
- **DynDOLOD/TexGen:** pre-generated Skyland LOD cannot represent the final
  modlist. Official DynDOLOD guidance requires finalising texture, tree,
  exterior and patch winners first; terrain LOD is generated from full landscape
  textures. PGPatcher must run before TexGen/DynDOLOD so their model matching can
  consume `ParallaxGen_Diff.json`.

## Distribution and permissions

Skyland AIO, Fantasia, Bits and Bobs, Skyrim 202X and Vanaheimr all prohibit
third-party reupload of their texture payloads and require permission to modify
their assets. Vanaheimr specifically permits reuse of its meshes/ESPs and
patches/LOD but says its textures may not be included in other mods. Vanilla PBR
AIO prohibits wholesale reuploads and requires contacting/commenting to obtain
permission for transformative asset use, with inherited rug permissions also
applying.

A public installer/Collection may record original Nexus dependencies, file IDs,
FOMOD choices and conflict rules so the user's account downloads author-hosted
files. It must not contain extracted texture payloads, private downscales or
modified copies without the required permission. Project-authored ESP/ESL
record patches, generator configs and original scripts can be distributed when
their inputs and licenses permit it.

## Decisions required from the user

1. **Grounded or colourful landscapes?** Recommended: grounded Skyland. Choose
   Fantasia only if its bolder, brighter fantasy direction is wanted.
2. **Baseline material model?** Recommended: ordinary Skyland first, then test
   the current Skyland CP addon later. True PBR is a separate migration.
3. **Broad base resolution?** Recommended: Skyland AIO 1K on the current 12 GiB
   GPU and 4K display. The archive already retains selected 2K/4K surfaces.
   Upgrade only specific large/hero surfaces after measured tests.
4. **Clutter complement?** Decide whether Bits and Bobs Performance should move
   to a full object-scale audit. It is not part of this report's automatic base
   approval.
5. **Mipmap gate:** decide whether Skyland remains provisional pending an author
   answer/comparison for the eight no-mip files, or whether a controlled visual
   test is acceptable before that is resolved.

No Keep/Skip decision should be recorded until the user answers these choices.

## Evidence and primary sources

Nexus file metadata was read from the official v1 API on 2026-08-30 without
printing or copying the private API key. Primary descriptions and permissions:

- [Skyland AIO](https://www.nexusmods.com/skyrimspecialedition/mods/34179)
- [Skyland standalone Landscapes](https://www.nexusmods.com/skyrimspecialedition/mods/3820)
- [Skyking Fantasia Landscapes](https://www.nexusmods.com/skyrimspecialedition/mods/107256)
- [Skyland Bits and Bobs](https://www.nexusmods.com/skyrimspecialedition/mods/95032)
- [Skyland LODs](https://www.nexusmods.com/skyrimspecialedition/mods/87412)
- [Skyrim 202X](https://www.nexusmods.com/skyrimspecialedition/mods/2347)
- [Skyrim 202X Downscale](https://www.nexusmods.com/skyrimspecialedition/mods/68307)
- [Skyrim 202X Complex Terrain Parallax](https://www.nexusmods.com/skyrimspecialedition/mods/54860)
- [Vanaheimr Landscapes AIO](https://www.nexusmods.com/skyrimspecialedition/mods/145439)
- [Vanaheimr PBR installation article, edited 2026-07-28](https://www.nexusmods.com/skyrimspecialedition/articles/10866)
- [Vanilla PBR AIO](https://www.nexusmods.com/skyrimspecialedition/mods/174091)
- [PGPatcher](https://www.nexusmods.com/skyrimspecialedition/mods/120946)
- [Community Shaders source](https://github.com/community-shaders/skyrim-community-shaders)
- [Closed Community Shaders terrain-CP regression #2379](https://github.com/community-shaders/skyrim-community-shaders/issues/2379)
- [DynDOLOD generation instructions](https://dyndolod.info/Generation-Instructions)
- [DynDOLOD Community Shaders/PBR guidance](https://dyndolod.info/Mods/Community-Shaders)
- [xLODGen terrain-LOD guidance](https://dyndolod.info/Help/xLODGen)

Inspected archive provenance:

| Nexus mod/file | Local evidence archive SHA-256 |
|---|---|
| Fantasia CP 107256/721164 | `8D5256223E4001F197667F95DA876F13A06AA74DCB4EC3C335A2EA91DC187058` |
| Fantasia 1K 107256/721230 | `FA1683AFA3F31AF13543A9930D4E37EC5E48BC940C111949F3025DB9C219CDAD` |
| Vanaheimr PBR 1K 145439/700531 | `A34402ACEE26780F8870ADEA6F937DBA252A075D8BD4A62B4CD31F609B21FDF5` |
| Skyland AIO 1K 34179/443516 | `490F02EC34487FA9CFFD76E9CCFB69A2C17AD5207A2416CC6B1AAD027D15D734` |
| Skyland AIO CP 34179/791745 | `4ACC2A1C4CFDA9E9DCE5661F8EAB9298780F342530F60285226AD96D6976CFFD` |
| Skyrim 202X 1K 68307/652624 | `0494A89AD34D0F5DB263DC8276130557E950E23892371DB151EE039FC3182BF3` |
| Bits and Bobs Performance 95032/538816 | `0394DD98189C827671E8F7FEF46F5E8B369870DF92A1FA3FEF2BF0DE3B0AFB89` |
| Bits and Bobs CP 95032/780407 | `0E419620B1EE44A66AED2FAD177774BA099FA769160831A13DA5B3ECEAD511DE` |

