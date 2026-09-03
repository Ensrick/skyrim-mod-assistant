# Tree overhaul and Morthal Swamp Bald Cypress audit

Date: 2026-08-29; decision superseded and implemented 2026-08-30
Status: full NotWL 3.14 installed and enabled; historical comparison retained below
Decision owner: user

## Current user direction (2026-08-30)

The user selected **full Nature of the Wild Lands 3.14** with its normal
placements and ordinary main textures. Nordic Cut is rejected from the stack:
it is not installed, must not be Keep, and must not appear as a patch master.
Nature of Mild Lands is not authorized or installed. The one 8192-square NotWL
log diffuse is handled by a separate deterministic local-only 4096 policy
overlay; the vendor folder remains immutable.

## Implemented decision

Full NotWL 3.14 is the baseline. Its exact official Bruma, CC Tundra Homestead,
Cutting Room Floor, and Lux Via patches are enabled, along with the normal
Grand Solitude and Solitude Docks full-placement patches. Nordic-specific
plugins from this historical comparison were not installed. See
`records/skyland-notwl-foundation-install-2026-08-30.md`.

The genuinely new challenger is **Nordskog - Northern Forest Trees 2.0** (2026-08-17). It is the cleanest stability/performance design on paper because it is a vanilla-path mesh/texture replacer with no plugin, scripts, reference placements, landscape, or navmesh edits. It also deliberately targets alpha overdraw, sub-pixel foliage, wind, and draw-call cost. It cannot be the default yet, however, because its current archive contains many 8192-pixel textures, its license forbids modification/derivatives without express permission, and it ships no dedicated LOD or Seasons files. It therefore fails the present texture policy as distributed. Ask the author for a sanctioned 4K option or permission before treating it as eligible for the production list.

**Morthal Swamp Bald Cypress 1.1 is a conditional candidate, not an automatic add.** Use the **ESP-FE** archive, not the full `.esl`, if the user elects to test it. It adds a distinctive Hjaalmarch swamp sub-biome and its assets stay within the 4K cap, but it is heavier per tree than either main finalist, has no custom 3D LOD or Seasons configuration, and conflicts at the record level with Nature of the Wild Lands/Nordic Cut. It needs a controlled Morthal A/B test and almost certainly an owned late compatibility patch once the final Morthal/location stack is known.

## Ranked shortlist

### Historical candidate 1 (rejected composition): NotWL + Mild Lands + Nordic Cut

Best overall fit for the intended list.

- NotWL is current enough to remain a leading candidate: 3.14 was updated 2025-09-02 and includes accumulated fixes. It replaces nearly all vanilla trees/plants and adds more than 400 trees, plants, and forest objects. It affects the DLC regions too.
- The current tree meshes average about 6,000 triangles. Version 3 atlased trees to reduce draw calls, simplified collision, added collision materials and dynamic navcuts, and removed landscape/navmesh edits. This is substantially safer than older dense forest overhauls that simply place many collision-bearing trees.
- It supports Seasons and includes hybrid 3D LOD for about 120 common meshes. Those LODs are roughly 600-1,500 triangles and are designed for TexGen/DynDOLOD 3 Ultra generation.
- Nordic Cut 1.2.2 (updated 2026-08-12) returns normal trees mostly to vanilla placement, retains NotWL shrubs/debris, favors robust spruce silhouettes, and slightly trims Morthal. This is a sensible response to NotWL's density and compatibility burden without losing its regional ground detail.
- Nordic Cut requires a **new game** and is not compatible with normal NotWL placement patches. Only Nordic Cut-specific patches should be used. Its patch collection currently covers Grand Solitude, JK's Solitude Outskirts, Bruma, COTN/Redbag Morthal, multiple Ryn locations, Northern Roads, Lux, Lux Via, and other relevant expansions.
- Beyond Reach and Wyrmstooth use separate worldspaces and do not inherently conflict with Skyrim-worldspace reference edits. They will inherit any vanilla-path mesh replacement used by their authors, but require visual inspection because their custom tree paths may remain untouched. Bruma has a Nordic Cut patch.
- Water for ENB has no direct loose-asset overlap with the audited tree packages and Morthal Cypress makes no LAND edits. Trees placed in or beside water still require spatial inspection; absence of a named patch is not proof that no tree intersects modified water geometry.
- Lux and Lux Via have current Nordic Cut patches. The audited collection exposes a `Lux.esp` patch, not an explicit Lux Orbis patch; exterior light/tree proximity still needs the final xEdit/spatial audit.
- The NotWL main archive itself contains assets above 4K. The already-audited Mild Lands archive replaces all 413 NotWL textures and has a 4K maximum, so Mild Lands must win every NotWL texture conflict. Do not enable the current NotWL PBR archive yet because its PBR path also contains 8K assets.
- Begin without the animation add-on and without PBR. Add each only after the base tree/shadow/LOD result is stable. This isolates the user's foliage-shadow complaint instead of changing mesh, animation, and shaders simultaneously.

Primary sources: [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604), [Nordic Cut](https://www.nexusmods.com/skyrimspecialedition/mods/161936), [Nature of Mild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/112765).

### 2. Nordskog - Northern Forest Trees 2.0, pending a compliant 4K distribution

Best technical challenger, but not policy-compliant as distributed.

- Version 2.0 was released 2026-08-17 and updated 2026-08-18. It uses realistic Picea abies, quaking aspen, Reach trees, and a gnarled oak Gildergreen while preserving vanilla placements.
- It is an asset-only replacer: no ESP/ESL, scripts, SKSE component, BOS config, reference placement, landscape, or navmesh record. That gives it the lowest patch burden with Grand Solitude, JK/HS/Ryn interiors, Lux/Community Shaders, Water for ENB, Bruma, Beyond Reach, and Wyrmstooth.
- The author specifically designed 2.0 to reduce alpha overdraw, sub-pixel triangles, pixel-shader cost, and draw calls. The page says trees top out near 6,000 triangles and use one draw call. The archive confirms a restrained 24 live meshes and generally 1-2 geometry/shader shapes per normal tree, but the one-draw-call claim is **not independently proven**: several live pine/aspen meshes contain two `BSTriShape` and two lighting-shader blocks, possibly mediated by a switch node.
- The snow pines inspected at 1,827-3,386 triangles and one shape; the Reach tree is 3,052; tundra driftwood is 6,635. The two unique Gildergreen meshes are exceptional at approximately 81,000 triangles and 6-7 shapes each. They are not forest-wide, but should be included in the Whiterun frame-time test.
- The archive has no plugin and no dedicated billboard, 3D LOD, DynDOLOD rule, Seasons INI, or seasonal texture/mesh set. TexGen can generate billboards, but no purpose-built hybrid 3D tree LOD is supplied. The page does not document current 2.0 DynDOLOD or Seasons support.
- The main archive contains four 8192x4096 live tree atlases and twelve 8192x8192 Gildergreen textures. This violates the user's “nothing over 4K ever” rule. The optional `FarBranchesFix` is for branch visibility below 4K or observed distant dropout; it is not a sanctioned 4K downscale.
- The included license prohibits modification, derivatives, and redistribution without express written permission. Do not privately generate and then silently normalize a modified Nordskog build as part of the production pack. Request a 4K file or written permission.
- Do not combine with another tree replacer, Lightwood Trees, or Skyrim Is Windy. Fabled Forests is technically compatible at the placement level but explicitly discouraged because its density plus Nordskog's low branches damages visibility.

Archive evidence: Nexus file 791380, 471,464,088 bytes, SHA-256 `73298458ff25ca44b9c12177476ec9aef3dccf469140a36b996aa9f94ef5731d`; 49 files total (24 DDS, 24 NIF, one license), no plugin or configuration files.
Primary source: [Nordskog 2.0](https://www.nexusmods.com/skyrimspecialedition/mods/121141).

### 3. Happy Little Trees 2.03 with current LOD support

The conservative fallback.

- HLT is older at its core (2.03, last base update 2023-12-23), but it remains widely exercised, comparatively lightweight, and has a robust compatibility/LOD ecosystem.
- Use the current official DynDOLOD add-on 2.1.2 (updated 2025-03) and the current HLT DynDOLOD optimizations 1.1 (2025-09) if their exact files are compatible rather than stacking blindly.
- A current Community Shaders PBR conversion exists (1.0.4, 2026-05), but PBR should remain a later A/B layer, not part of initial fault isolation.
- It provides less regional/ecological transformation than NotWL and does not answer the desire for a striking modern forest as strongly. Its value is predictable performance and simpler troubleshooting.

Sources: [Happy Little Trees](https://www.nexusmods.com/skyrimspecialedition/mods/50961), [official DynDOLOD add-on](https://www.nexusmods.com/skyrimspecialedition/mods/56907), [DynDOLOD optimizations](https://www.nexusmods.com/skyrimspecialedition/mods/158587), [Community Shaders PBR conversion](https://www.nexusmods.com/skyrimspecialedition/mods/159171).

### 4. Traverse the Ulvenwald 3.3.2

Visually rich but no longer the best stability/performance baseline.

- It remains attractive and season-aware, with 370+ models and good regional variety.
- The author categorizes it for medium/high systems and reports roughly 2-4 average FPS loss, rising to 4-10 in Falkreath depending on the scene. It also has wind-animation interaction with Skyrim Is Windy and a more involved 3D LOD path.
- Its last main update was 2023-11-21. It is still viable, but newer alternatives have either a stronger maintenance/patch story (NotWL/Nordic) or much lower plugin burden (Nordskog).

Source: [Traverse the Ulvenwald](https://www.nexusmods.com/skyrimspecialedition/mods/57874).

### 5. Fabled Forests 2.1A / Sprigganlands 1.3a / blend projects

Do not use for the initial stability baseline.

- Fabled Forests changes or adds roughly 45,000 tree references and intentionally increases density. Its HLT asset base is efficient, but the placement volume increases patching, occlusion, and draw burden. It was last updated in 2024 and remains a specialized “dense forest” choice rather than a conservative foundation.
- Sprigganlands is genuinely current (1.3a, 2026-08-24) and visually ambitious, but the inspected 2K Performance file still has roughly 10-18K triangles per full tree on average; its author lists further triangle reduction and 3D LOD as future work. It is too young and heavy for the first stable baseline.
- Tree Diversity Project, BOS mashups, Blubbo layers, and Happy Little Shrubs can add variety, but they also multiply art-direction, asset-path, Seasons, and LOD failure modes. They should be considered only after one coherent tree baseline has passed testing. NotWL already covers shrubs/debris comprehensively.

Sources: [Fabled Forests](https://www.nexusmods.com/skyrimspecialedition/mods/94462), [Sprigganlands](https://www.nexusmods.com/skyrimspecialedition/mods/187865), [Tree Diversity Project](https://www.nexusmods.com/skyrimspecialedition/mods/155974).

## Morthal Swamp Bald Cypress 1.1 archive audit

### Exact file and plugin facts

- Preferred archive: Nexus file 795152, `Marsh Cypress Trees` v1.1, **ESP-FE**.
- Downloaded bytes: 56,630,785. SHA-256: `cda87380822d2c803e29ed20a2ea050af15537f7daafddce9d46769fcf7af1a6`.
- Darker NotWL texture option: file 795154, 1,248,574 bytes, SHA-256 `00d92b143ba46377029a9df0fd80ac7c44ed4eb19d8bd536190de9a72330b233`.
- Contents: one ESL-flagged ESP, 10 NIFs, 13 DDS files. No scripts, DLL, BSA, DynDOLOD rule, billboard/LOD asset, Seasons INI, or seasonal mesh/texture set.
- The ESP masters only Skyrim, Update, Dawnguard, HearthFires, and Dragonborn. Header flag is `0x200`; all 135 new records are compact-range. It consumes a light slot, not a full plugin slot.
- Record types: 10 TREE, one Tamriel WRLD override, 23 CELL overrides, and 207 placed references. There are 125 new references and 82 Skyrim reference overrides. Eighty-one of those existing references change their base object to a new cypress; one appears unchanged/bookkeeping.
- Actual placed content: 122 full cypress trees, 84 cypress knees, and one unchanged vanilla reference, with scales from 0.58 to 2.07.
- Placement is concentrated west/southwest of Morthal in Tamriel grids x=-15..-10, y=14..20, including MorthalExterior, the tundra Doomstone/waterfall transition, and the Fort Snowhawk area.
- No NAVM or LAND records are present. This avoids direct navmesh/landscape conflicts, but it does **not** prove AI safety: new collision-bearing placements have no audited navcut metadata and must be path-tested.

### Mesh, material, texture, and LOD facts

- Six full trees are SSE NIF version 100 with 3 `BSTriShape` objects and three shader/texture sets: trunk, foliage, and hanging moss. Each uses two alpha-property blocks.
- Full trees measure approximately 11,497-14,404 triangles and 11,087-14,006 vertices. This is around twice the NotWL average and materially above Nordskog's normal-tree target. With 122 full placements, Morthal is the correct place to measure 0.1% lows and GPU frametime before acceptance.
- Four cypress knees are 609-835 triangles with one shape and collision.
- Full trees use `BSTreeNode`, animated trunk bones, multi-bound data, and capsule collision. This is a proper animated/collidable tree asset, not a static decorative card.
- Textures are well bounded and mipmapped: bark diffuse/normal 4096x2048 BC7; branch diffuse/normal 2048 square BC7; branch subsurface/specular 512 square; four knee diffuse/normal pairs 2048 square. Nothing exceeds 4K.
- The optional darker package changes only the branch diffuse. Alpha coverage is identical to the base texture, while non-transparent luminance is about 14% lower. It is a color-match option, not a foliage-density or performance change.
- The branch atlas is still alpha-masked card foliage. Approximately 77% of the full atlas is completely transparent, with about 11.5% fully opaque and 11.5% intermediate alpha. UV use may crop those regions, so this is not a direct overdraw measurement, but the asset cannot eliminate card-shadow aliasing by itself.
- No dedicated hybrid/3D LOD is supplied. TexGen can generate billboards and Community Shaders can light complex tree billboards when its integrated tree-LOD features and DynDOLOD complex atlases are configured, but the cypress remains billboard-based at distance unless a permitted custom hybrid LOD is authored later.
- There are no winter/spring/autumn swaps. The `_summer` asset names do not constitute Seasons support. Cypress will remain green in winter unless a separate patch is made.

### Conflict facts

- Loose asset-path overlap with the audited NotWL archive is zero: the cypress meshes/textures do not overwrite NotWL files.
- Plugin conflict is substantial and intentional. Exact record-key comparison found 76 shared records with NotWL 3.14 and 105 shared records with Nordic Cut 1.2.2. Most are the vanilla tree references being changed into cypress plus shared CELL/WRLD headers.
- With Nordskog or HLT, the cypress asset paths remain clean and those base mods do not themselves add a competing placement plugin. This is the simplest technical combination.
- With NotWL + Nordic Cut, the darker texture is the intended visual option, but load order alone is not sufficient for the final build. Loading Cypress after Nordic lets its cypress substitutions win; loading it after every location patch can also reintroduce a tree that a Grand Solitude/Morthal/location patch intentionally disabled. The correct production answer is a small owned late ESP-FE compatibility patch after Nordic Cut, the selected Nordic patches, Cypress, and all relevant Morthal/location plugins.
- Grand Solitude has a current Nordic Cut patch. It is not in the core Morthal cypress placement area, but the final record audit still applies. Bruma also has a Nordic Cut patch. Wyrmstooth and Beyond Reach are separate worldspaces and do not share these Tamriel references.
- Botanically, bald cypress is native to southeastern North America rather than historical Scandinavia. It can work as an intentionally unusual fantasy marsh sub-biome, but it is not a historically Nordic flora choice.

Primary source: [Morthal Swamp Bald Cypress](https://www.nexusmods.com/skyrimspecialedition/mods/189488).

### ESP-FE versus full ESL

Choose **ESP-FE**.

- Both variants are light-slot eligible; the full `.esl` gives no meaningful slot-count advantage.
- A full `.esl` is forced into the master load group and is therefore poorly suited to a placement mod that must win selected conflicts against regular ESP location/tree plugins.
- An ESL-flagged `.esp` can be positioned late and can be mastered by our own late ESL-flagged patch. This is precisely the flexibility the final compatibility workflow needs.

## Why the reported flat-leaf shadow issue may persist

Every practical Skyrim forest overhaul still uses alpha-masked foliage to some degree. What looks like “z-fighting” on thin leaves may be true coplanar geometry, but it may instead be alpha-test shimmer, shadow-map aliasing, temporal instability, or screen-space shadow reprojection. Changing tree meshes can reduce overlapping cards and alpha overdraw, but it cannot guarantee that all flat foliage shadows disappear.

For diagnosis, compare the same mesh twice with Community Shaders screen-space shadows/tree subsurface options held fixed and then toggled one at a time. If the artifact follows the shader toggle rather than the mesh package, treat it as a CS/shadow configuration issue rather than stacking another tree replacer.

The old standalone Community Shaders Tree LOD Lighting feature has been incorporated into current Community Shaders; do not install the obsolete standalone feature. For current DynDOLOD billboard lighting, use the integrated feature with `TreeNormalMaps`/`TreeLODComplexAtlas` as applicable to the generated profile.

## Staged A/B test plan

1. Use a disposable MO2 profile and a new save. Nordic Cut explicitly requires a new game.
2. Freeze weather, lighting, grass, Community Shaders settings, camera positions, INIs, and all non-tree visual mods.
3. Profile A: NotWL 3.14 -> Mild Lands 1.0 -> Nordic Cut 1.2.2 -> exact selected Nordic Cut patches. Disable NotWL PBR and the animation add-on initially. Generate fresh TexGen and DynDOLOD 3 output for this exact profile.
4. Profile B only after a compliant file/permission exists: Nordskog 2.0, no `FarBranchesFix` at native 4K output resolution. Generate separate TexGen/DynDOLOD output. Add the fix only if distant branch dropout is actually observed.
5. Optional fallback C: HLT 2.03 plus its currently compatible LOD resources; again generate dedicated output.
6. Use repeatable routes: Riverwood/Falkreath forest, Rift aspens, Morthal swamp and waterfall, Reach, snowy Winterhold route, Solstheim, Whiterun Gildergreen, Grand Solitude approach, and Bruma if active.
7. At sunrise and noon, take a static capture and a slow camera pan. Record average, 1%, and 0.1% frame time; VRAM; traversal stutter; canopy visibility; leaf shimmer; shadow crawl; wind discontinuity; tree pop; LOD color/shape transition; collision; arrow impact; and NPC pathing.
8. Toggle only the relevant Community Shaders foliage/screen-space-shadow option for one duplicate pass to separate mesh artifacts from shader artifacts.
9. Add Morthal Cypress ESP-FE only to the winning baseline. Use base texture for Nordskog/HLT; use the darker option for NotWL/Nordic. Regenerate TexGen/DynDOLOD and rerun the Morthal route.
10. Run final xEdit conflict review and spatial inspection with the chosen Morthal/city, Lux/Lux Via/Lux Orbis, road, and Water for ENB stack. Create one owned late compatibility ESP-FE for intentional winning values and disabled/repositioned references.

Suggested acceptance gates: no new floating/clipping/cell-boundary tree defect on the route; no NPC stuck on a repeated road/path pass; no hard 0.1% low regression greater than approximately 5% from the chosen baseline without a consciously accepted visual benefit; no VRAM budget overrun; and acceptable billboard/hybrid LOD color and silhouette transitions.

## Archive provenance and method

All downloads were made through the official Nexus API using the existing private local credential mechanism. No key, authenticated URL, or token was printed or copied into this repository.

Archive inspection used 7-Zip listing/extraction, the repository's `audit/modasset.py` DDS/NIF parser, plugin header/record parsing, `skyrim-record-cli`, exact FormID record-key comparison, and direct texture statistics. The downloaded archives were left in the existing MO2 downloads cache and extracted only under the ignored `_audit_tmp` workspace; nothing was installed or enabled.

This record supersedes the provisional ordering in `docs/LANDSCAPE-TREES-2026-08-26.md` only where the newly released Nordskog 2.0 archive and the exact Morthal Cypress v1.1 inspection add evidence. The final production decision remains pending the user's visual A/B choice and measured gameplay results.
