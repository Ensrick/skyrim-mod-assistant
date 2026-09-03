# Rule 0 pass: prior art for every Ensrick artifact

Audit date: 2026-09-03. Remediation item 0 of
`records/ck-first-audit-2026-09-03.md`. Rule: `docs/CK_FIRST_DOCTRINE.md` §0 -
*"Look at how vanilla and existing mods already solved it. First."*

**Nothing was installed, changed, enabled or launched by this pass.** Four
archives were downloaded into the session scratchpad only, to produce byte
receipts; no file under `mods/`, `overlays/`, `mo2-instances/` or `profiles/`
was touched.

## Method and receipts

- **Vanilla / USSEP**: `skyrim-record-cli`
  (`skyrim-tools-builds/skyrim-record-cli-1f3c8d9/skyrim-record-cli.exe`,
  toolchain-pinned) `record-fields` / `records` / `plugin-info` against
  `Dawnguard.esm`, `Skyrim.esm` and
  `USSEP/unofficial skyrim special edition patch.esp` 4.3.9a.
- **Nexus**: the official API per `NEXUS_API.md` (key resolved from the
  sibling `crusader-de-tweaker` ignored file; validated 2026-09-03, user
  25820485, premium, 19,516 daily requests remaining). Name search used the
  v2 GraphQL `mods(filter:{name:{op:WILDCARD}})` endpoint; metadata, file
  lists, descriptions and changelogs came from v1
  `/games/skyrimspecialedition/mods/{id}[.json|/files.json|/changelogs.json]`.
  Anonymous page fetches return HTTP 403, so no page was scraped.
- **Downloads for verification only** (scratchpad, never installed): Skyland
  Solitude 1k 1.8 (file 428567), Scale Nord Armor "Medium Textures" (file
  163924), Pelagius's Wildlife AI 1.2.1 (file 614825), kahvipannu84's env-map
  resource (file 692490).
- Where a claim is not backed by an artifact it is marked **[unverified]**.

## Two corrections to the CK-first audit's sample

The 2026-09-03 sample said "zero of ten" artifacts recorded a prior-art
search. Two of those ten do, and the sample looked in the wrong file:

- **Bloodskal Blade 4 Static Glow** - the ledger row's `note` opens *"built
  here because the mod page ships no such option - only MAIN (pulsing +
  embers), No Glow, No Guard Engravings and a Sheath."* That is a correct,
  specific prior-art check against the author's four released files. The
  sample read `records/active-file-conflicts.md` instead.
- **Scoped Werewolf Totem Skull 98175** - the sample recorded *"no record
  found"*. `records/source-builds/ensrick-scoped-werewolf-totem-98175.json`
  has an `alternatives` array naming three released candidates (175588,
  28882, 98703) with versions, dates, an archive SHA-256 and a finding for
  each. It is the **best** rule-0 record in the project.

So the real score on that sample is **two of ten**, not zero. The finding
still stands for the other eight, and the pattern this audit confirms is
narrower and more useful than "nobody searched": **asset fixes were
researched against the vendor's own page; record patches and runtime plugins
were not researched at all.** Every artifact below with released prior art is
a record patch, a runtime plugin, or a texture cap.

---

# Per-artifact findings

## Asset fixes - environment masks and texture paths

### 1. `Ensrick - Skyking Signs Env Mask Fix`

1. **Problem.** [Skyking Signs](https://www.nexusmods.com/skyrimspecialedition/mods/112902)
   2.1's parallax option rewrites the wooden post/bracket shape of every sign
   from a Default shader to an EnvironmentMap shader (EnvMapScale 1.0, 1x1
   black cubemap) whose env-mask slot points at eleven `_m` textures that
   nothing in the load order ships. Under Community Shaders' Dynamic Cubemaps
   a missing mask leaves a full-strength reflection on matte wood, stone, rock
   and ground. Eleven 4x4 black masks restore the vanilla look.
2. **Vanilla?** No, and this is checked, not assumed: vanilla ships no `_m`
   for any of the eleven diffuses, and vanilla `loadscreenblackbriar01.nif`
   parsed out of `Skyrim - Meshes1.bsa` has all four landscape shapes on the
   Default shader with slots 4/5 empty (`overlays/…/build.py` docstring;
   `records/envmask-missing-scan-2026-09-02.md`).
3. **Released mod?** **No.** Searches: Nexus name `Skyking` (63 hits, all
   Skyking2020's own mods), `environment mask` (1 hit, unrelated), `envmask`
   (0), `Reflection Fix` (10), `Missing Textures` (8), `Texture Path Fix` (5).
   Skyking Signs' full changelog (v1.1 → v2.1, 2026-05-13) has no `_m` or
   env-map entry; the author's 28 files include a "Skyking Signs - Blank
   Diffuse Textures" misc file (538517) but no masks.
   [Unofficial Material Fix](https://www.nexusmods.com/skyrimspecialedition/mods/21027)
   1.18.0 - installed and enabled here - fixes **havok** material errors
   (footsteps, impact sounds, arrow collision), not shader env masks.
   [ENB Texture Fixer](https://www.nexusmods.com/skyrimspecialedition/mods/85253)
   converts *transparent* `_m` maps, a different defect. The one mod in the
   same class,
   [Random Env map textures that are missing from vanilla game](https://www.nexusmods.com/skyrimspecialedition/mods/165764)
   v1.00 (2025-11-29, kahvipannu84), was downloaded and enumerated: **104 DDS,
   zero under `architecture\` or `landscape\`**, and none of our eleven paths.
   It also solves the opposite problem - it *adds* painted metallic
   reflections where a mesh wants them; ours *removes* an unintended one.
4. **Verdict: NO PRIOR ART FOUND.** Kept. One doctrine note: the CK-native
   alternative is to clear the `Environment_Mapping` shader flag on Skyking's
   NIFs, which is what
   [Assorted mesh fixes](https://www.nexusmods.com/skyrimspecialedition/mods/32117)
   does for vanilla meshes. That would make the overlay vendor-derived
   (`recipe`) instead of our own bytes (`distributable`), so the mask route is
   also the better distribution choice. Worth reporting to Skyking2020.

### 2. `Ensrick - CC Madness Longsword Env Mask Path Fix`

1. **Problem.** Creation Club Saints & Seducers ships the Madness longsword
   mask as `…\madness_longsword01_em.dds`; its own meshes and
   [Believable weapons](https://www.nexusmods.com/skyrimspecialedition/mods/37737)
   1.5's loose replacements both ask for `…\Madness_LongSword_01em.dds`. The
   underscore is on the wrong side of "01". The overlay copies the CC texture
   byte-for-byte to the asked-for path.
2. **Vanilla?** The typo **is** vanilla - it is Bethesda's, parsed out of
   `ccbgssse025-advdsgs.bsa`. Vanilla does not solve it.
3. **Released mod?**
   [Unofficial Skyrim Creation Club Content Patches](https://www.nexusmods.com/skyrimspecialedition/mods/18975)
   v8.5 (2026-08-03, garthand) is the correct home and demonstrably ships this
   class of fix - changelog 5.11: *"Elven Hunter Armor: The male body armor,
   the male first person meshes, and the armor ground model weren't set to use
   their EM map"*. All **81 changelog versions** were fetched and searched for
   `madness|env|texture path|_em|longsword`: there is **no entry for this
   defect**. Note USCCCP is not installed in this build. Believable Weapons
   1.5 (2022-01-30) is its last update and inherited the typo. Searches:
   `Creation Club` (475), `Saints and Seducers` (150), `Unofficial Skyrim`
   (174), `Believable Weapons` (13).
4. **Verdict: NO PRIOR ART FOUND.** Kept. **Report upstream to garthand** -
   this is a two-line USCCCP mesh fix and belongs there.

### 3. `Ensrick - Skyland Solitude Manhole Texture Path Fix`

1. **Problem.** [Skyland AIO](https://www.nexusmods.com/skyrimspecialedition/mods/34179)
   1K 4.32's `smanhole.nif` asks for
   `textures\arechitecture\solitude\smanhole_{e,m}.dds` - "arechitecture"
   misspelled. Skyland ships both files under the correctly spelled folder.
   The overlay copies them to the misspelled path.
2. **Vanilla?** No. Vanilla `smanhole.nif` is a plain Default shader with no
   slots 4/5, so the reflection is Skyland's own authoring.
3. **Released mod?** **No - and the author's own claimed fix never shipped.**
   [Skyland - Solitude](https://www.nexusmods.com/skyrimspecialedition/mods/24252)
   (the standalone, same author) changelog reads: 1.55 *"Updated manhole mesh
   paths."*; 1.6 *"Once again, fixing the manholes. This time it's actually
   right! I didn't need the _m map or the cubemap."*; 1.7 *"Fixed manhole
   reflections."* That looked like superseding prior art, so it was checked
   directly. Skyland Solitude 1k v1.8 (file 428567, 2023-09-24, archive
   SHA-256 `BDF854F27F58A3FD75B5F0CEB888DA4688DE7B063171F47FB1C442E37C21CEAA`,
   96,225,262 B) was downloaded and its `smanhole.nif` extracted:

   | mesh | SHA-256 | texture slots 4/5 |
   |---|---|---|
   | Skyland - Solitude 1.8 (standalone, current MAIN) | `f989ced6799ae460cf8086337f44b9a35e3da8f4cd0406c80b487bb2f861b6a1` | `textures\arechitecture\solitude\smanhole_e.dds`, `…_m.dds` |
   | Skyland AIO 1K 4.32 (installed) | `f989ced6799ae460cf8086337f44b9a35e3da8f4cd0406c80b487bb2f861b6a1` | identical |

   **Byte-identical, and the typo is still there in the current release.** The
   1.6 changelog entry describes a change that is not in the shipped file.
   Searches: `Skyland Solitude` (2), `Texture Path Fix` (5),
   `Missing Textures` (8), plus the Skyland AIO changelog (15 versions; 4.3
   *"Fixed Solitude texture (no more hotfix needed)"* is a different file).
4. **Verdict: NO PRIOR ART FOUND.** Kept, with the strongest negative in this
   document. Worth reporting to Skyking2020 with the hash.

## Asset fixes - meshes and skins

### 4. `Ensrick - Bloodskal Blade 4 Static Glow`

1. **Problem.** [Bloodskal Blade 4](https://www.nexusmods.com/skyrimspecialedition/mods/120399)'s
   MAIN mesh animates the blade glow on three controllers (brightness,
   emissive colour, ember V-scroll). User ruling 2026-08-30: *"The pulse looks
   bad on Bloodskal Blade… Just the simple glow version."* The overlay freezes
   all three curves to constants, 42 bytes changed, file length identical.
2. **Vanilla?** Not applicable - a third-party art asset.
3. **Released mod?** **Yes, an adjacent one, and it was already checked.** The
   author ships **Bloodskal Blade 4 - No Glow** (file 505409, 2024-05-27,
   *"Removes the glow and embers"*) plus No Guard Engravings (513808) and a
   Sheath (666612). No file gives a *static* glow. Wider search `Bloodskal`
   (53 hits) surfaced
   [Bloodskal Blade - Tweaks and Enhancements](https://www.nexusmods.com/skyrimspecialedition/mods/55988),
   [Dynamic Bloodskal Blade - Lag Fix](https://www.nexusmods.com/skyrimspecialedition/mods/65530)
   and
   [Bloodskal Weapon art - MCO fix and Artifact remake](https://www.nexusmods.com/skyrimspecialedition/mods/114317)
   - all gameplay/effect mods, none a static-glow mesh.
4. **Verdict: PRIOR ART EXISTS, OURS STILL BETTER** - the released option
   deletes the glow entirely; the user asked for a constant glow, not none.
   Kept. **This artifact's ledger note already contained this finding.**

### 5. `Ensrick - Vanilla Skin Soft-Light Maps`

1. **Problem.** Both installed skin sets ship a near-black or all-black
   subsurface `_sk` (CBBE 2.0.3 mean luminance 0.03-0.06; The New Gentleman
   4.2.5 a 4x4 black stub; Reverie 4x4 black). `_sk` is the texel the vanilla
   soft-lighting wrap multiplies by (`Lighting.hlsl:1526,1830`), so with
   Advanced Skin off (#144) the wrap is gone and baked eye makeup reads as a
   hard ring. The overlay supplies the six vanilla `_sk` maps
   (`femalehead/body_1/hands_1`, `malehead/body_1/hands_1`).
2. **Vanilla?** **Yes - the fix *is* the vanilla asset.** Vanilla means are
   0.37/0.44 (female head/body) and 0.19/0.18 (male), measured from the game's
   own `Skyrim - Textures0.bsa` in
   `records/face-eye-makeup-audit-2026-09-02.md`.
3. **Released mod?** **Yes.**
   [CS Subsurface Scattering SK](https://www.nexusmods.com/skyrimspecialedition/mods/169723)
   v3.2, updated **2026-09-03** (Ali / Z3rdPro, 177 endorsements, 21,446
   downloads) ships purpose-authored `_sk` thickness maps with separate files
   for **3ba** (CBBE-UV compatible), **Himbo**, COTR and UBE. Its description:
   *"These are thickness maps that allow either shader (subsurface scattering
   or advanced skin) to know how far light is able to penetrate a surface…
   Tuned for unreleased advanced skin."* Also
   [Blank Werewolf Subsurface Textures](https://www.nexusmods.com/skyrimspecialedition/mods/68276)
   and
   [Subsurface Scattering Shaders for Skins](https://www.nexusmods.com/skyrimspecialedition/mods/14238).
   Searches: `Subsurface` (5), `skin subsurface` (2), `SK map` (122).
4. **Verdict: PRIOR ART EXISTS, OURS STILL BETTER *for the stated goal*.**
   169723 is tuned for the **Advanced Skin / CS_SKIN** path, which this build
   has switched off; the consumer here is the **soft-light wrap**, and the
   goal is explicitly "zero art change, restore vanilla". A thickness map
   authored for a different shader is not the same lever. **But this is a real
   new-mod adoption candidate the user has never been shown** - if Advanced
   Skin is ever turned back on, 169723 is the right answer and this artifact
   should be revisited. Suggest, do not install.

### 6. `Ensrick - Vanilla Hair Remake SMP NPC Compatibility` (+ the XML fix overlay)

1. **Problem.** Two things. (a) VHR SMP - NPCs' BSA has three Dawnguard Snow
   Elf FaceGen meshes still referencing the removed `darkelf01.xml`; the
   current SMP main ships the sex-specific `darkelf01m.xml`. (b) VHR's archive
   wins 29 FaceGen paths that USSEP also supplies with deliberate race, sex,
   head-part or morph corrections; the overlay restores the exact USSEP meshes
   at those 29 paths.
2. **Vanilla?** Not applicable - a conflict between two third-party archives.
3. **Released mod?** **No, and (a) is still live upstream.** Receipt: on
   [Vanilla hair remake](https://www.nexusmods.com/skyrimspecialedition/mods/63979)
   the **"Vanilla hair remake SMP - NPCs" file is still v1.0.1** (file 500742,
   2024-05-13) while the SMP main is v1.0.3 (file 510409, 2024-06-11). The
   1.0.1 changelog entry is *"Fixed broken physics in DarkElf01"* - the mesh
   references were not re-pointed. Nearby mods, none of which does the USSEP
   forward:
   [Faithful Faces - Vanilla Hair Remake SMP - Consistency Patches](https://www.nexusmods.com/skyrimspecialedition/mods/143247)
   v1.0 (2025-09-09, 829 endorsements) regenerates FaceGen for **third-party
   NPC-adding mods** (Arthmoor villages, Cutting Room Floor, Schlitzohr,
   Environs, JK's, Inigo, …) and does not touch USSEP;
   [Weight adjustment for Vanilla Hair Remake SMP](https://www.nexusmods.com/skyrimspecialedition/mods/161949);
   [Facegen Meshes for Nordic Faces and Vanilla Hair Remake](https://www.nexusmods.com/skyrimspecialedition/mods/119776);
   [Vanilla Hair Remake Unlocked](https://www.nexusmods.com/skyrimspecialedition/mods/117861).
   Search `Vanilla Hair Remake` returned 22 mods; all were reviewed.
4. **Verdict: NO PRIOR ART FOUND.** Kept. Report (a) to jg1 - it is a stale
   optional file, not a design decision.

### 7. `Ensrick - Better Fur Fine Clothes CBBE-HIMBO Refit`

1. **Problem.** [Better fur - Fine clothes](https://www.nexusmods.com/skyrimspecialedition/mods/69240)
   v2 replaces the fine-clothes outfit meshes wholesale, discarding the
   installed CBBE / HIMBO Refits body geometry. The overlay clones only jg1's
   separately weighted fur shape onto each installed body-refit NIF.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No.** Searches: `Better Fur` (9 - the author's own fine
   clothes, merchant's hat and wedding outfit, plus
   [Better fur - Fineclothes hat](https://www.nexusmods.com/skyrimspecialedition/mods/84429)
   by SadovnikMuller, a hat), `Fineclothes` (1, the same hat), `Fine Clothes`
   (24), `CBBE Refit` (12), `HIMBO Refit` (203), `Bodyslide` (2,629). Nothing
   refits Better Fur's fine clothes to CBBE or HIMBO. 69240's own file list is
   three files (main, standalone mantle, wedding outfit) - no BodySlide data.
4. **Verdict: NO PRIOR ART FOUND.** Kept.

### 8. `Ensrick - Assorted Mesh Fixes SE Mesh Port`

1. **Problem.** [Assorted mesh fixes](https://www.nexusmods.com/skyrimspecialedition/mods/32117)
   0.139.3 ships some meshes in Oldrim NIF format on an SE mod page. The
   overlay re-serialises them to SSE stream 100.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No.** Receipt for the defect itself, taken from the
   installed vendor mod by parsing every loose NIF header: **416 loose NIFs,
   of which 57 at BS stream 83 (Oldrim) and 359 at stream 100**; our overlay
   holds exactly 57, all at stream 100. Searches: name `Assorted Mesh Fixes`
   across all games returned six mods -
   [Assorted mesh fixes](https://www.nexusmods.com/skyrimspecialedition/mods/32117)
   (SE, 0.139.3),
   [Assorted Bruma Mesh Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/69919),
   [Assorted Mesh Fixes LE -Updated-](https://www.nexusmods.com/skyrim/mods/109575)
   (an LE backport, the opposite direction),
   [Cities of the North - Assorted Mesh Fixes Patch](https://www.nexusmods.com/skyrimspecialedition/mods/62900),
   [Assorted Mesh Fixes](https://www.nexusmods.com/skyrim/mods/108246) (LE),
   and a Milllogpile patch - **none is an SSE re-optimisation.** 32117's
   description (read in full via the API) never mentions NIF format, LE meshes
   or optimisation. `Mesh Fixes` (71 hits) surfaced no successor.
4. **Verdict: NO PRIOR ART FOUND.** Kept. The community-standard answer here
   is *a tool run locally* - SSE NIF Optimizer or Cathedral Assets Optimizer -
   which is exactly the `recipe` class this artifact already carries. **Report
   to wSkeever**: 57 files out of 416 is an oversight, not a decision.

### 9. `Ensrick - Vikings Weaponry SE Mesh Port`

1. **Problem.** [Vikings Weaponry SE - Johnskyrim](https://www.nexusmods.com/skyrimspecialedition/mods/14409)
   ships its six meshes at NIF stream 83 inside its BSA despite the SE
   listing. The overlay converts them to stream 100 / BSTriShape with rescaled
   Havok collision.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No.** 14409's entire file list is four uploads, all
   v1.0-v1.3 from January 2018; the mod has not been touched in eight years.
   Searches: `Vikings` (21), `Johnskyrim` (11) - the only other results are
   three translations, an
   [SPID distribution config](https://www.nexusmods.com/skyrimspecialedition/mods/124983),
   an [OCF keyword patch](https://www.nexusmods.com/skyrimspecialedition/mods/153099),
   and
   [Vikings Weapons and Armor SE Port](https://www.nexusmods.com/skyrimspecialedition/mods/79128),
   which is a port of naghaplaj85's **different** mod, not johnskyrim's.
4. **Verdict: NO PRIOR ART FOUND.** Kept.

### 10. `Ensrick - Scoped Werewolf Totem Skull 98175`

1. **Problem.** [High Poly 3D Wolf Skull - Werewolf Totem Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/98175)
   1.3's totem NIF is wanted, but two of its eight textures sit under
   `textures/ingredients/hagfeather` and so retexture the hag-feather
   ingredient globally. The overlay remaps all eight references under
   `textures/ensrick/werewolf_totem_98175`.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No scoped variant exists** - 98175 has a single MAIN
   file (416610). Search `Werewolf Totem` returned exactly three mods, and the
   artifact's own record already evaluated all the relevant ones:
   [Rally's Werewolf Totems](https://www.nexusmods.com/skyrimspecialedition/mods/28882)
   v1.0 (3,932 endorsements) - a texture-only replacer on the vanilla mesh, so
   it has no hag-feather side effect but also none of the scanned geometry;
   [My PBR Conversion Hub - High Poly 3D Wolf Skull](https://www.nexusmods.com/skyrimspecialedition/mods/175588)
   (2026-03-25) - *"its patcher rules use the original global hag-feather
   paths"*, i.e. it reproduces the defect;
   [JJerem Skull Downscale](https://www.nexusmods.com/skyrimspecialedition/mods/98703)
   - redundant at 1.3. The third search result,
   [Werewolf Totems Underforge Free Access](https://www.nexusmods.com/skyrimspecialedition/mods/77916),
   is unrelated.
4. **Verdict: NO PRIOR ART FOUND** (and **this record already proved it**).
   Kept.

## Asset fixes - texture caps

These enforce `docs/TEXTURE_POLICY.md` locally. The prior-art question for a
cap is narrow and worth asking every time: **does the author already publish a
lower-resolution file?**

### 11. `Ensrick - Scale Nord Armor Texture Cap` - the one that fails this test

1. **Problem.** [Scale Nord Armor](https://www.nexusmods.com/skyrimspecialedition/mods/41118)'s
   main archive ships `ScaleArmor_m` at 4096 and `ScaleBG_m` /
   `ScaleHelmet_m` at 2048, two to three steps above the 512 vanilla steel
   analogue. The overlay downscales all three to 1024 with texconv.
2. **Vanilla?** Vanilla ships every steel `_m` at 512 - the measurement that
   set the target.
3. **Released mod? YES - the author's own optional file.** 41118 publishes
   **"Medium Textures"** (file 163924, 2020-10-04, 8,649,658 B) alongside
   "Full 4k textures" (163923). It was downloaded and its DDS headers parsed:

   | file | vendor MAIN | author "Medium Textures" | our overlay |
   |---|---:|---:|---:|
   | `ScaleArmor_m.dds` | 4096, 13 mips | **2048**, 12 mips | 1024, 11 mips |
   | `ScaleBG_m.dds` | 2048, 12 mips | **1024**, 11 mips | 1024, 11 mips |
   | `ScaleHelmet_m.dds` | 2048, 12 mips | **1024**, 11 mips | 1024, 11 mips |

   The author's released file lands **exactly on our target for two of the
   three masks**, one step above on the third - and it caps the diffuse and
   normal maps too (58 MB → 8.4 MB for the whole set).
4. **Verdict: SUPERSEDED (partially).** The correct action was a *file
   choice* - install "Medium Textures" instead of the main archive - not an
   overlay. Ours is one step stricter on `ScaleArmor_m` only. **Deletion
   candidate**, conditional: switching the installed file is a vendor-file
   change and needs the user's approval like any adoption.

### 12. `Ensrick - Nature of the Wild Lands Texture Cap`

1. **Problem.** One violation in the whole of
   [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604)
   3.14: `textures/true forest/log/log01.dds` at 8192x8192 BC7 (89,478,660 B),
   downscaled to 4096 (22,369,796 B).
2. **Vanilla?** Not applicable.
3. **Released mod?** **No for this file.** The author does publish **"NotWL -
   textures options"** (file 613488, v3.10, 1.65 GB), whose description
   enumerates its contents: *"4K bark diffuse maps, 4K bark normal maps, 2K
   branch diffuse maps, 2K bark diffuse maps with BC1 compression."* Bark and
   branch - **not** the `true forest/log` atlas.
4. **Verdict: NO PRIOR ART FOUND** for the one capped file. Kept. The author's
   options file should still be evaluated on its own merits as a VRAM measure
   - that is a separate, unopened question.

### 13. `Ensrick - Freak's Floral Fields Texture Cap` - the model example

1. **Problem.** The selected 2K FOMOD tier ships `Twigs_Freak.dds` at
   4096x8192.
2. **Vanilla?** Not applicable.
3. **Released mod? Yes - and it is what the artifact ships.** The overlay is
   the **vendor archive's own 1K-tier atlas**, verbatim, placed at the 2K-tier
   path (archive `Freaks Floral Fields-125349-3-2-3-1786549491.zip` SHA-256
   `D82616F1…BBB`, entry SHA-256 `E4CC21AE…AF`, byte-equal to the installed
   file).
4. **Verdict: PRIOR ART EXISTS AND WAS USED.** No new bytes were authored.
   This is the shape rule 0 wants, and it is the pattern the Scale Nord cap
   should have followed.

### 14. `Ensrick - Bloodskal Blade 4 Texture Cap`

1. **Problem.** Two 8K textures on
   [Bloodskal Blade 4](https://www.nexusmods.com/skyrimspecialedition/mods/120399)
   capped to 4K.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No.** 120399's four files are MAIN, No Glow, No Guard
   Engravings and Sheath - no resolution option.
4. **Verdict: NO PRIOR ART FOUND.** Kept.

### 15. `Ensrick - Quicksilver's Sword Pack Texture Cap`

1. **Problem.** [Quicksilver's Sword Pack](https://www.nexusmods.com/skyrimspecialedition/mods/77594)
   ships all twelve maps at 4096; eleven capped against measured vanilla
   analogues.
2. **Vanilla?** Yes, and vanilla is the yardstick: diffuse 2048, normal 1024,
   env-mask 256, measured from `Skyrim - Textures*.bsa`.
3. **Released mod?** **No.** 77594 has one file (326302, v1.0, 2022-10-24) and
   no resolution options.
4. **Verdict: NO PRIOR ART FOUND.** Kept.

### 16. `Ensrick - Vikings Weaponry Texture Cap`

1. **Problem.** Env masks two steps over source and five uncompressed
   A8R8G8B8 normals; 128 MB → 31 MB.
2. **Vanilla?** Yes - vanilla steel/dwarven weapon `_m` measure 512.
3. **Released mod?** **No.** 14409's four uploads are all the same mod at
   v1.0-1.3; the 2K choice is a FOMOD option inside them, with no lower tier.
4. **Verdict: NO PRIOR ART FOUND.** Kept.

## Record patches and runtime plugins

### 17. `Ensrick Wolf Territorial Patch` - the worst result in this audit

1. **Problem.** Make wolves territorial rather than instantly hostile, by
   changing three AI-data numbers on nine `NPC_` records: `Warn` 0 → 2500,
   `WarnOrAttack` 2000 → 1200, `Attack` 1500 → 640 (issue #42).
2. **Vanilla?** Vanilla *is* the model, and the design doc found it: `EncBear`
   already ships 2500/2000/1500 and `EncHorker` 850/640/320
   (`docs/WILDLIFE-WOLVES-2026-08-28.md`). The vanilla half of rule 0 was done
   properly here. USSEP does not override `EncWolf`
   (`skyrim-record-cli record-fields … EncWolf` → *"Record not found"*).
3. **Released mod? YES, and it is not close.**
   [Pelagius's Wildlife AI - Skypatcher](https://www.nexusmods.com/skyrimspecialedition/mods/144909)
   v1.2.1 (2026-04-01, pelagiuswingmods, 146 endorsements) - *"Using
   Skypatcher, updates animal aggro settings (level, attack/warn radius, etc.)
   … Does not touch NPC/animal records, spawns, AI packages … Covers several
   wildlife/animal mods as well as Vanilla animals."* The file (614825,
   32,280 B, SHA-256
   `13F561E32E3C4B6343DADFAEF03C68E317EA0B6537B13493B3844227B85783E4`) was
   downloaded. `SKSE\Plugins\SkyPatcher\npc\PelagiusWildlifeAI\WildlifeNPCs\Skyrim.esm.ini`
   lines 102-103 are:

   ```
   ; Skyrim.esm - EncWolf
   filterByNPCs=Skyrim.esm|23ABE:setAggression=aggressive:setConfidence=average:setAssistance=helpsallies:aggressionRadiusBehavior=true:aggressionRadiusRanges=attack~100, warn~300, attackandwarn~0
   ```

   `23ABE:Skyrim.esm` is **the exact record** our 830-line C# generator
   rewrites, and `aggressionRadiusRanges=attack~…, warn~…, attackandwarn~…`
   are **the exact three fields** it changes. The mod covers all nine wolf
   variants plus modded animals across 28 config files. Adjacent released mods
   in the same space:
   [SkyTEST - Realistic Animals and Predators SE](https://www.nexusmods.com/skyrimspecialedition/mods/1104)
   v1.65.22 (45,386 endorsements),
   [Realistic Wildlife Behaviours](https://www.nexusmods.com/skyrimspecialedition/mods/4804),
   [Wildlife Harmony](https://www.nexusmods.com/skyrimspecialedition/mods/159413),
   [Custom NPC and Wildlife Behaviour - SkyPatcher](https://www.nexusmods.com/skyrimspecialedition/mods/180162),
   [Bite - Wildlife Combat Enhancement](https://www.nexusmods.com/skyrimspecialedition/mods/34843).
   **No record in this project mentions any of them.**
4. **Verdict: PRIOR ART EXISTS AND SUPERSEDES THE MECHANISM.** The *tuning* is
   ours and defensible - Pelagius pacifies (attack 100 / warn 300, aggression
   raised to `aggressive`); our design keeps `Unaggressive` and makes the wolf
   territorial at bear-like distances. But the **mechanism is a solved problem
   with a released, maintained, plugin-free implementation, and this project
   already ships three SkyPatcher INI overlays of its own.** **Top deletion
   candidate**: delete the ESP and the generator, keep the
   template-inheritance audit script, and re-express the policy as nine
   `filterByNPCs=` lines. Adopting 144909 outright would be a new-mod adoption
   and needs the user's approval; converting our own patch to an INI does not.

### 18. `Ensrick Guard Scaling Patch`

1. **Problem.** Guards are floored at level 20 (*"like fighting a level 20 at
   level 1"*, #51). Three NPC templates get `calcMinLevel` 20 → 5 with
   `levelMult` and the level cap unchanged.
2. **Vanilla?** Vanilla sets the floor at 20; USSEP owns two of the three
   records (`skyrim-record-cli record-fields "USSEP/…esp" EncGuardImperialTemplate`
   returns `0F6F37:Skyrim.esm`, type `Npc`), which is why the patch forwards
   from the winner rather than from vanilla.
3. **Released mod? Yes, with different semantics.**
   [Rescaled Guards SSE](https://www.nexusmods.com/skyrimspecialedition/mods/36421)
   v1.0.0 (2020-05-25, Gnago, 64 endorsements, 1,603 downloads) - *"Keeps
   guards at a specific level regardless of player level"*, with fixed-level
   options at 5, 10, 20, 25, 40, 50, 65, 80, 100, 175 and 256, covering Skyrim
   and Redoran guards. It **removes** PC scaling; ours keeps `levelMult 1.0`
   and only lowers the floor. It also predates USSEP 4.3.9a and forwards
   nothing. Related but not equivalent:
   [Unscaled Skyrim Guards](https://www.nexusmods.com/skyrim/mods/37467) (LE),
   [Dynamic NPC Scaling](https://www.nexusmods.com/skyrimspecialedition/mods/180306),
   [True Unleveled Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/18342),
   [Relevel NPCs](https://www.nexusmods.com/skyrimspecialedition/mods/11209).
   Searches: `Guard Level` (3), `Guards Level Scaling` (0), `Level Scaling`
   (14), `Scaling` (88), `Guards` (295).
4. **Verdict: PRIOR ART EXISTS, OURS STILL BETTER** on semantics - the named
   defect in the alternative is that it discards player scaling entirely,
   which is not what #51 asked for. **But the mechanism is again avoidable**:
   SkyPatcher's `npc` block exposes level fields alongside the
   `aggressionRadiusRanges` syntax receipted above
   ([NPC Patcher usage article 6092](https://www.nexusmods.com/skyrimspecialedition/articles/6092)
   references `setPcLevelMult`, `calcLevelMin`, `calcLevelMax`) - **[exact key
   names unverified**; confirm against
   [SkyPatcher](https://www.nexusmods.com/skyrimspecialedition/mods/106659)
   7.0.3's own documentation before converting]. **Deletion candidate for the
   532-line generator and the ESP, not for the policy.**

### 19. `Ensrick Wolf Encounter Thinning` (generated and staged, not installed)

1. **Problem.** 191 of 622 exterior wolf references retired by clustering at a
   2000-unit radius, so the world thins without deleting whole packs.
2. **Vanilla?** The vanilla audit was done and is in
   `docs/WILDLIFE-WOLVES-2026-08-28.md` (leveled lists remain eligible at every
   player level; no vanilla mechanism thins them).
3. **Released mod? Yes.**
   [True Hunter - fewer animals per square meter](https://www.nexusmods.com/skyrimspecialedition/mods/25628)
   v6.2 (2026-05-29, lilebonymace, 1,949 endorsements, 362,737 downloads):
   *"adding a chance of disabling each animal on cell loading… Predators 12%,
   Prey 45%, Ambient 20%"*, with an MCM. Also
   [Certainly Less Annoying Wildlife Spawns - CLAWS](https://www.nexusmods.com/skyrimspecialedition/mods/43992)
   and
   [No Road Predators Redone](https://www.nexusmods.com/skyrimspecialedition/mods/24366).
4. **Verdict: PRIOR ART EXISTS, OURS STILL BETTER - with the defect named by
   the alternative's own author.** True Hunter's description, limitation 3:
   *"Since the spawn chance is individual for each animal, the chance to
   encounter a group of animals … is drastically reduced… Fixing this is too
   complicated and unreliable."* That is precisely what our clustering solves -
   387 clusters at a 2000-unit link radius, retiring 30.7% while holding 12
   clusters that contain an ineligible member. It also excludes persistent and
   enable-parented refs, which True Hunter cannot disable at all. Keep.

### 20. `Ensrick - Cloak Distribution Balance`

1. **Problem.** A generic NPC's cloak was 1.0% Cloaks of Skyrim against 54.8%
   fur across 24 shared leveled lists; four tunables plus four structural
   fixes in a SkyPatcher INI bring it to 23.8% (#200).
2. **Vanilla?** Not applicable - the graph being measured is RMB's, not
   Bethesda's.
3. **Released mod?** **No equivalent rebalance**, and the artifact's own record
   already names the released alternative for one tunable: the GUARDS block
   carries `"deleteIf": "RMB SPIDified - Sons of Skyrim 83340 is adopted (#195)
   - that package performs the merge properly"`. Searches: `Cloaks of Skyrim`
   (77), `Cloaks` (261), `RMB SPIDified` (53). The ecosystem here is
   [RowanMaBoot's framework](https://www.nexusmods.com/skyrimspecialedition/mods/63625)
   plus
   [Cloaks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/6369),
   [Winter Is Coming](https://www.nexusmods.com/skyrimspecialedition/mods/4933),
   [Cloaks and Capes](https://www.nexusmods.com/skyrimspecialedition/mods/2019)
   and
   [Detailed NPCs - Cloaks of Skyrim for NPCs (SPID)](https://www.nexusmods.com/skyrimspecialedition/mods/80610);
   none measures or rebalances the shared-list probability.
4. **Verdict: NO PRIOR ART FOUND**, and the artifact is already in the
   ecosystem's own light form. Keep. Second model example after FFF.

### 21. `Ensrick - Cloaks of Skyrim Unique Placement`

1. **Problem.** [RMB SPCH - Cloaks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/116030)
   1.5.3 writes `objectsToAdd=Skyrim.esm|<id>` for ten items whose FormIDs live
   in `Cloaks - RMB SPCH.esp`, and truncates Krosis's filter to
   `Skyrim.esm|767` instead of `100767`. SkyPatcher logs no miss on an npc
   `objectsToAdd`, so all ten failed silently. Ten corrected lines (#187).
2. **Vanilla?** Not applicable.
3. **Released mod?** **No.** 116030 is current at 1.5.3 (2026-05-06); the
   defect is unfixed upstream. No third-party patch appears in the 77-mod
   `Cloaks of Skyrim` or 53-mod `RMB SPIDified` result sets.
4. **Verdict: NO PRIOR ART FOUND.** Kept. **Report to RowanMaBoot** - this is
   a ten-line bug in a shipping config.

### 22. `Ensrick - Death Hound Loot Fix`

1. **Problem.** Undead death hounds drop dog meat. One SkyPatcher
   `removeFromLLs` line (#199).
2. **Vanilla?** **Checked, and vanilla is the cause.**
   `skyrim-record-cli record-fields "…/Dawnguard.esm" DLC1DeathItemDeathHound`
   → `00D6F7:Dawnguard.esm`, `LeveledItem`, `Flags: UseAll`, `ChanceNone`
   inverse 100%, three entries (`LootSmallTreasure10`, `FoodDogMeat`,
   `DLC1DeathHoundCollar`). `UseAll` + chanceNone 0 means the meat is
   guaranteed. **USSEP 4.3.9a does not override it** - the same query against
   `unofficial skyrim special edition patch.esp` returns *"Record not found:
   DLC1DeathItemDeathHound"*.
3. **Released mod?** **No.** Search `Death Hound` returned 18 mods, all
   retextures, sounds, animations, loading-screen and pet mods
   ([RUSTIC DEATH HOUND and GARGOYLE](https://www.nexusmods.com/skyrimspecialedition/mods/17740),
   [Death Hound Loading Screen Eye Fix](https://www.nexusmods.com/skyrimspecialedition/mods/98210),
   [Barghest](https://www.nexusmods.com/skyrimspecialedition/mods/53619), …).
   [Simple Hunting Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/95943)
   1.16 overrides 24 death-item lists and this is not one of them, recorded at
   adoption.
4. **Verdict: NO PRIOR ART FOUND.** Kept - one INI line, already the right
   weight.

### 23. `Ensrick CRF Semantic Patch`

1. **Problem.** Six override records forwarding Cutting Room Floor semantics
   over nwsFollowerFramework, Skyrim Unbound, Lux and Water for ENB (#71).
2. **Vanilla?** Not applicable - a conflict between five third-party plugins.
3. **Released mod?** **No.** Search `Cutting Room Floor` returned 82 mods:
   translations, NPC replacers, No-Snow-Under-the-Roof and
   [Landscape and Water Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/73025)
   patches,
   [Interesting NPCs - CRF Patch](https://www.nexusmods.com/skyrimspecialedition/mods/29194)
   (installed). None targets this combination. A load-order-specific forward
   cannot be a released mod - it is only meaningful for this order.
4. **Verdict: NO PRIOR ART FOUND / structurally not applicable.** The CK-first
   PARTIAL verdict (analysis in code, output hand-authored) stands
   independently.

### 24. `Ensrick - Collectibles Helper USSEP Forward`

1. **Problem.** [Collectibles Helper](https://www.nexusmods.com/skyrimspecialedition/mods/130354)
   1.0.3 overrides 47 Dragonborn records without USSEP as a master and writes
   vanilla values back over twelve USSEP fixes. Eight forward records.
2. **Vanilla?** Vanilla is the wrong side of this - USSEP is the authority, and
   its licence explicitly permits the forward: *"You may also copy any needed
   fixes into your own work to use without the USSEP as a master."*
3. **Released mod?** **No.** Search `Collectibles Helper` returned 11 mods:
   130354 itself and **ten translations** (CHS x2, Deutsch x2, RU, ES, PL, FR,
   TR, IT). No patch. 130354 is current at 1.0.3 (2025-03-27) and still omits
   USSEP.
4. **Verdict: NO PRIOR ART FOUND.** Kept. **Report to Jonx0r** - adding USSEP
   as a master is the upstream fix. The CK-first VIOLATION verdict (204 lines
   of C# for what xEdit's "Copy as override" does) stands.

### 25. `Ensrick General Compatibility Patch`

1. **Problem.** Fourteen override-only records (twelve WRLD, two CELL)
   resolving stale override families while keeping the final Water for ENB
   water fields, with three intentional ITMs as future-order guards (#47).
2. **Vanilla?** Not applicable.
3. **Released mod?** **No** - fourteen records chosen for a specific
   327-plugin order cannot exist as a released mod. The generic released
   answers are a Wrye Bash bashed patch, a Mator Smash patch, or a Synthesis
   patcher.
4. **Verdict: NOT APPLICABLE.** Kept.

### 26. `Ensrick Lux Water CS Patch` - prior art used, correctly

1. **Problem.** Preserve the latest non-water CELL/WRLD state while forwarding
   only Water for ENB-owned water fields: 559 override records, 0 new forms.
2. **Vanilla?** Not applicable.
3. **Released mod? The *patcher* is the prior art, and it was used.** The
   plugin is generated by **mindflux's own GPL-3.0
   [WaterForENBPatcherCS](https://github.com/mindflvx/WaterForENBPatcherCS)**
   (upstream `0c26a28`, Ensrick fork merge `f7d459b`). No released patch for
   this pairing exists: the current file lists of
   [Water for ENB](https://www.nexusmods.com/skyrimspecialedition/mods/37061)
   2.21, [Lux](https://www.nexusmods.com/skyrimspecialedition/mods/43158) 7.1,
   [Lux Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/113002)
   7.1 and
   [Lux CS](https://www.nexusmods.com/skyrimspecialedition/mods/153919) 2.6.0
   were all enumerated - mindflux ships a "Water Multiplier xEdit Script CS"
   (file 703695) and location patches for Wyrmstooth, Skyrim Sewers and
   others, but nothing for Lux CS; the Lux hubs ship 40+ patches, none for
   Water for ENB.
4. **Verdict: PRIOR ART EXISTS AND WAS USED.** Keep. The best-practice example
   among the record patches.

### 27. `Ensrick - Varinia Dialogue Fragment Fix`

1. **Problem.** Six dialogue-fragment PEX recompiled from the author's own PSC
   with restored property declarations.
2. **Vanilla?** Not applicable.
3. **Released mod?** **No, and it is still live upstream.**
   [Varinia - Custom Voiced Retired Spy and Companion](https://www.nexusmods.com/skyrimspecialedition/mods/148853)
   is current at v1.1.0 (2025-12-14); all four changelog entries (1.0.0, 1.0.1,
   1.0.2, 1.1.0) were read and none mentions fragment scripts or property
   declarations. Search `Varinia` returned six mods - the base mod, three
   visual replacers, and two translations.
4. **Verdict: NO PRIOR ART FOUND.** Kept. The record already says *"upstream
   fix preferred"*; **report to Maplespice.**

### 28. `Ensrick - Conditional Arrow Embedding` - the second-worst result

1. **Problem.** A bespoke SKSE plugin (own repo
   `github.com/Ensrick/ConditionalArrowEmbedding`, commit `50201f5`, v0.1.0,
   2026-09-02) hooking a native post-damage callsite to apply an
   arrow-embedding policy: `bodyStickBelowHealthRatio: 0.5`, head-node
   detection by ancestor depth and name tokens.
2. **Vanilla?** Vanilla controls this with game settings
   (`iMaxArrowsStuckInActor` and friends) - a settings-level lever the released
   mods below all use. Not checked before building; our record contains no
   vanilla-settings analysis.
3. **Released mod?** **Nothing implements this exact policy, but an entire
   framework exists for the job and was never considered.**
   [Core Impact Framework (CIF)](https://www.nexusmods.com/skyrimspecialedition/mods/146873)
   v2.0.5 (updated **2026-09-02** - the same day our DLL was built - 7,232
   endorsements, 1,830,239 downloads, Seb263): *"a hierarchical system of fully
   configurable filters and modifiers … criteria such as armor type, weapon
   used, target state … operates without plugins or scripts."* Whether CIF can
   gate arrow **attachment** specifically, as opposed to impact VFX/SFX/
   physics, is **[unverified]** - it needs a read of Seb263's documentation,
   which is the check that should have happened first. Neighbours:
   [No Arrow in my Body AE](https://www.nexusmods.com/skyrimspecialedition/mods/155839)
   (removes all body arrows),
   [Persistent Arrows for Thee](https://www.nexusmods.com/skyrimspecialedition/mods/159432)
   (built *on* CIF, player-vs-NPC split),
   [More Arrows On Bodies](https://www.nexusmods.com/skyrimspecialedition/mods/5675),
   [Stay Arrow Stay - S.A.S.](https://www.nexusmods.com/skyrimspecialedition/mods/4911),
   [Headshots Kill SKSE](https://www.nexusmods.com/skyrimspecialedition/mods/181461)
   v1.41 (2026-06-09 - native C++ projectile/head/helmet detection, the same
   engine problem our `fallbackHeadNodeTokens` solves by name matching). Also
   [MIF - Mu Impact Framework](https://www.nexusmods.com/skyrimspecialedition/mods/95624)
   and
   [Object Impact Framework](https://www.nexusmods.com/skyrimspecialedition/mods/149484).
4. **Verdict: NO EXACT PRIOR ART FOUND, but the search was not done.** A C++
   SKSE plugin with a native callsite hook was written for a policy decision,
   in a space with three released impact frameworks and a released SKSE
   headshot plugin. **Deletion candidate pending one check**: read CIF's
   documentation and Headshots Kill's feature list; if either expresses the
   policy in config, the DLL should go.

### 29. `Ensrick - Weapon Speed Balance`

1. **Problem.** Undetermined from the repo - **this artifact has no
   `records/source-builds/*.json`, no ledger row and no design doc.** Parsed
   directly: `WeaponBalancePatch.esp`, 1,586,973 B, **3,007 `WEAP` override
   records** across **34 masters** (Skyrim/DLC, 20 CC plugins, USSEP, 3DNPC,
   Bruma, Wyrmstooth, arnima, Vigilant, Gray Fox Cowl, ISC, Varinia, Sons of
   Skyrim, One-handed warhammers).
2. **Vanilla?** Not assessable without the policy.
3. **Released mod?** Adjacent releases exist but none normalises the whole
   order by rule:
   [Weapon Speed Effects Fix](https://www.nexusmods.com/skyrimspecialedition/mods/27677),
   [Weapon Speed Mult Fix](https://www.nexusmods.com/skyrimspecialedition/mods/45502),
   [Weapon Speed Fix](https://www.nexusmods.com/skyrimspecialedition/mods/32859),
   [Customize Weapon Speed](https://www.nexusmods.com/skyrimspecialedition/mods/22100),
   [Weapon Speed - IPM](https://www.nexusmods.com/skyrimspecialedition/mods/96828),
   [Skill Based Weapon Speed](https://www.nexusmods.com/skyrimspecialedition/mods/168856),
   [Two Handed Weapons Speed Customization](https://www.nexusmods.com/skyrimspecialedition/mods/33004).
   Search `Weapon Speed` (27 hits) reviewed in full.
4. **Verdict: UNDETERMINED - insufficient record.** A 3,007-record override
   plugin with no source-build record, no ledger row and no stated rule is a
   bigger governance problem than any prior-art question. **Open an issue** to
   document or retire it before the list ships.

## Configurations - not candidates for a mod

### 30-32. `MLO2 Foundation Config`, `Media Keys Fix Configuration`, `SSE Display Tweaks Configuration`

1. **Problem.** Our settings for three installed SKSE plugins:
   `SKSE/Plugins/MLO.ini` (shadow-caster and torch-light suppression, fake
   glow-orb removal, colour consistency at RGB 255/161/60, five whitelist
   entries for Lux, ENB Light, Grand Solitude, Solitude Docks and Snazzy);
   `MediaKeysFix.ini` (three booleans, all false);
   `SSEDisplayTweaks_Custom.ini` (borderless, 119 FPS cap, uncapped Havok,
   cursor lock).
2. **Vanilla?** Not applicable.
3. **Released mod?** Not applicable - a config naming this build's own mods and
   this machine's own refresh rate cannot be a mod. The upstream defaults were
   the starting point in each case.
4. **Verdict: NOT APPLICABLE.**

### 33. `Pandora Output - Ensrick`

Generated behaviour output, regenerated by the headless Pandora fork.
**NOT APPLICABLE.**

### Out of scope

`Ensrick - Regional Currency Integration` is Sol's in-flight work
(`mods/currency-integration`) and was not audited here, per the CK-first
audit's note to coordinate rather than touch it. The vendor DLL source
rebuilds (Light Placer, ConsoleUtilSSE, JContainers, PapyrusUtil, Proteus,
RaceMenu/skee64, QuickLoot IE, Seasonal Clothing Framework, MenuPilot,
LaunchProbe, Pandora headless, MO2Headless, CDF/DDR/currency-swapper) are
excluded by the task and by the doctrine's scope.

---

# Summary

| # | Artifact | Verdict |
|---|---|---|
| 11 | Scale Nord Armor Texture Cap | **SUPERSEDED** (author's "Medium Textures", file 163924) |
| 17 | Wolf Territorial Patch | **PRIOR ART, MECHANISM SUPERSEDED** (Pelagius's Wildlife AI) |
| 18 | Guard Scaling Patch | **PRIOR ART, ours better; mechanism avoidable** (Rescaled Guards SSE) |
| 4 | Bloodskal Blade 4 Static Glow | PRIOR ART, ours better (author's "No Glow") |
| 5 | Vanilla Skin Soft-Light Maps | PRIOR ART, ours better *for this shader path* (CS Subsurface Scattering SK) |
| 19 | Wolf Encounter Thinning (staged) | PRIOR ART, ours better - alternative's author names the defect (True Hunter) |
| 13 | Freak's Floral Fields Texture Cap | **PRIOR ART USED** (vendor's own 1K tier) |
| 26 | Lux Water CS Patch | **PRIOR ART USED** (mindflux's own GPL patcher) |
| 28 | Conditional Arrow Embedding | **NO EXACT PRIOR ART, BUT SEARCH NOT DONE** (Core Impact Framework unchecked) |
| 1 | Skyking Signs Env Mask Fix | NO PRIOR ART FOUND |
| 2 | CC Madness Longsword Env Mask Path Fix | NO PRIOR ART FOUND |
| 3 | Skyland Solitude Manhole Texture Path Fix | NO PRIOR ART FOUND (byte-verified) |
| 6 | VHR SMP NPC Compatibility + XML fix | NO PRIOR ART FOUND |
| 7 | Better Fur Fine Clothes CBBE-HIMBO Refit | NO PRIOR ART FOUND |
| 8 | Assorted Mesh Fixes SE Mesh Port | NO PRIOR ART FOUND (57/416 NIFs at stream 83) |
| 9 | Vikings Weaponry SE Mesh Port | NO PRIOR ART FOUND |
| 10 | Scoped Werewolf Totem Skull 98175 | NO PRIOR ART FOUND (already recorded) |
| 12 | Nature of the Wild Lands Texture Cap | NO PRIOR ART FOUND |
| 14 | Bloodskal Blade 4 Texture Cap | NO PRIOR ART FOUND |
| 15 | Quicksilver's Sword Pack Texture Cap | NO PRIOR ART FOUND |
| 16 | Vikings Weaponry Texture Cap | NO PRIOR ART FOUND |
| 20 | Cloak Distribution Balance | NO PRIOR ART FOUND (alternative already recorded) |
| 21 | Cloaks of Skyrim Unique Placement | NO PRIOR ART FOUND |
| 22 | Death Hound Loot Fix | NO PRIOR ART FOUND (vanilla + USSEP checked) |
| 23 | CRF Semantic Patch | NO PRIOR ART FOUND / not applicable |
| 24 | Collectibles Helper USSEP Forward | NO PRIOR ART FOUND |
| 25 | General Compatibility Patch | NOT APPLICABLE |
| 27 | Varinia Dialogue Fragment Fix | NO PRIOR ART FOUND |
| 29 | Weapon Speed Balance | **UNDETERMINED - no record exists** |
| 30-33 | MLO2 / Media Keys / SSE Display Tweaks / Pandora Output | NOT APPLICABLE |

| verdict | count |
|---|---:|
| SUPERSEDED | 1 |
| PRIOR ART EXISTS, OURS STILL BETTER | 5 |
| PRIOR ART EXISTS AND WAS USED | 2 |
| NO PRIOR ART FOUND | 18 |
| NOT APPLICABLE | 5 |
| UNDETERMINED | 1 |

## Deletion candidates, most confident first

Every swap to a released mod below is a **new-mod adoption and needs the
user's approval** (standing rule: suggest, never install). Converting one of
our own artifacts to a lighter form of itself does not.

1. **`Ensrick Wolf Territorial Patch`** - highest confidence. A released,
   maintained SkyPatcher mod writes the same three fields on the same record
   from one text line. Cheapest correct action: **convert our own patch to
   nine `filterByNPCs=` lines** (no approval needed, keeps our tuning, deletes
   830 lines of C# and an ESP). Adopting
   [Pelagius's Wildlife AI](https://www.nexusmods.com/skyrimspecialedition/mods/144909)
   instead needs approval and would change the tuning.
2. **`Ensrick - Scale Nord Armor Texture Cap`** - the author's released
   "Medium Textures" file hits our exact target on two of three masks and caps
   the diffuse and normals too. Needs approval (it changes which vendor file is
   installed).
3. **`Ensrick Guard Scaling Patch`** - delete the 532-line generator and the
   ESP; keep the policy as a SkyPatcher `npc` line once the key names are
   confirmed against SkyPatcher 7.0.3's documentation. No approval needed.
4. **`Ensrick - Conditional Arrow Embedding`** - conditional on one unfinished
   check. Read
   [Core Impact Framework](https://www.nexusmods.com/skyrimspecialedition/mods/146873)'s
   documentation; if the policy is expressible as a CIF config, retire the DLL.
   Adopting CIF needs approval.
5. **`Ensrick - Vanilla Skin Soft-Light Maps`** - keep for now (different
   shader path), but put
   [CS Subsurface Scattering SK](https://www.nexusmods.com/skyrimspecialedition/mods/169723)
   in front of the user, and revisit if Advanced Skin is ever re-enabled.
6. **`Ensrick Wolf Encounter Thinning`** (staged, not installed) - keep;
   [True Hunter](https://www.nexusmods.com/skyrimspecialedition/mods/25628) is
   the released equivalent and is worse on the one axis that matters here, by
   its own author's admission.
7. **`Ensrick - Bloodskal Blade 4 Static Glow`** - keep unless the user decides
   the author's "No Glow" is close enough; that is a taste call.

## Follow-ups this audit generated

Upstream reports - each a real defect in a shipping mod, with a receipt
already in hand:

- **Skyking2020 / Skyland - Solitude 24252**: the 1.6 changelog says the
  manhole `_m` and cubemap were removed; the 1.8 mesh (`f989ced6…b6a1`) still
  references `textures\arechitecture\solitude\`.
- **garthand / USCCCP 18975**: CC Saints & Seducers Madness longsword meshes
  ask for `Madness_LongSword_01em.dds`; the BSA ships
  `madness_longsword01_em.dds`.
- **wSkeever / Assorted mesh fixes 32117**: 57 of 416 loose NIFs are at BS
  stream 83.
- **jg1 / Vanilla hair remake 63979**: the SMP - NPCs optional file is stalled
  at 1.0.1 and three Snow Elf FaceGen meshes still reference the removed
  `darkelf01.xml`.
- **RowanMaBoot / RMB SPCH - Cloaks of Skyrim 116030**: ten `objectsToAdd`
  entries name the wrong plugin and Krosis's filter is truncated.
- **Jonx0r / Collectibles Helper 130354**: 47 Dragonborn overrides without
  USSEP as a master revert twelve USSEP fixes.
- **Maplespice / Varinia 148853**: six dialogue fragments lost their property
  declarations.
- **Skyking2020 / Skyking Signs 112902**: the parallax option's post shapes
  carry an EnvironmentMap shader pointing at eleven `_m` textures nothing
  ships.

Governance:

- **`Ensrick - Weapon Speed Balance` has no record of any kind** and overrides
  3,007 weapon records across 34 masters. Open an issue.
- Add a **"prior art searched"** field to the `records/source-builds/*.json`
  schema, alongside rule 7's "why code". Two artifacts already carry the
  content in prose (Bloodskal's `note`, the werewolf totem's `alternatives`
  array); the werewolf totem's shape is the one to standardise on.
