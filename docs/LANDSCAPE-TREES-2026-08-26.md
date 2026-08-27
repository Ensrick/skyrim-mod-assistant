# Landscape and tree stack review — 2026-08-26

Status: reviewed candidates, archives cached for inspection, **not installed**.
This record distinguishes a visual preference from an installation decision.

## Provisional decision

- Landscape: [Vanaheimr - Landscapes - AIO](https://www.nexusmods.com/skyrimspecialedition/mods/145439)
  5.5, PBR 2K variant. It is the closest current match for the grounded
  historical-mythic art direction and has a maintained Community Shaders PBR
  workflow.
- Trees: [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604)
  3.14 with [Nordic Cut](https://www.nexusmods.com/skyrimspecialedition/mods/161936)
  1.2.2. Nordic Cut uses vanilla placement for most normal trees while retaining
  NotWL shrubs/debris and its regional character. This is the preferred
  composition; the original dense placement is not the performance baseline.
- Texture economy: use [Nature of the Mild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/112765)
  3.14 loose files over the NotWL base while PBR is disabled. It is an
  author-permitted downscale made specifically for NotWL 3.14.
- Hold [NotWL PBR](https://www.nexusmods.com/skyrimspecialedition/mods/150319)
  1.0.4 until the Community Shaders/PGPatcher runtime path is active and its
  texture budget has a compliant answer.
- Hold the [NotWL animation add-on](https://www.nexusmods.com/skyrimspecialedition/mods/148132)
  initially. Its author records CPU overhead and requires its meshes to be
  disabled for TexGen/DynDOLOD generation.

This is not yet an installation authorization. A new game is required for
Nordic Cut; it must not enter a real campaign mid-save.

## Archive evidence

| Component | Nexus file | SHA-256 | Findings |
|---|---:|---|---|
| Vanaheimr PBR 2K 5.5 | 700529 | `959e7127f5c025bc748b9bdda30982b59e8146b29effa7e043d759326cd19f51` | 521 DDS, 199 NIF, ESL-flagged ESP; every dimension is at most 4096. Two core road meshes report Oldrim user version 83 and require repair or exclusion before acceptance. |
| NotWL 3.14 | 661793 | `86b83a9a3b26d5a54dbb3ea40c4e638b18e7be4ba47f880fea6779ecb011054a` | 413 DDS and 1,082 NIF across the archive; 6,276,345 static triangles counted. The selected main payload contains an 8192-square log diffuse and many 4096-square debris/log/stump maps despite the advertised 2K-trunk/1K-branch default. |
| Nordic Cut 1.2.2 | 789072 | `5dbb82dcfe9d605ef6db882d0458f75b5dae628bc3259224a647fd31cadabe17` | One ESL-flagged plugin plus configuration metadata; no loose mesh or texture payload and no packaging warning detected. |
| Nordic Cut patch collection 1.2.2 | 789073 | `d84e84c9c6de5744a2dce443af41444f48af3ec1a03b1918ce333078c118dfa1` | 78 selectable plugins. Includes current Lux, Lux Via, Bruma, Alternate Start, Northern Roads, city and Ryn patches. Install only patches whose masters are present. |
| Nature of the Mild Lands loose 3.14 | 709121 | `0704fbf9b0c7a7626bf6c34b1673b780526d46cd15ec33b54b73a19a594823fa` | Replaces all 413 NotWL textures at half dimensions: mostly 1K/512, with 44 at 2K and one large log diffuse at the absolute 4K ceiling. No dimension exceeds 4096. |
| NotWL PBR 1.0.4 | 792330 | `7bbb815eeda3c80b5be209c4ef46306844a4005431d28696942152bacc9d59d5` | 655 DDS and 187 TruePBR JSON files. It mirrors the base archive's 8192-square log diffuse and therefore fails the absolute texture ceiling as shipped. The non-PBR downscaler does not overwrite `textures/pbr`. |
| Sprigganlands 2K Performance 1.3a | 794511 | `0ddb89bb40744b214e912ec63a03d4d473195cc77b1dd1d770ab245bc3e6573b` | 78 SSE-format NIFs, 840,574 triangles including supplied LOD meshes, and 413 DDS with no dimension over 4096. No plugin; it is a vanilla-path mesh/texture replacer. Ships a stray MO2 `meta.ini` containing the author's local path. |

The generic texture analyzer flags missing normals and solid normal-map alpha in
both NotWL sets. These are not automatic rejection findings: leaf/subsurface
materials and PBR RMAOS layouts do not obey the same basename and gloss-alpha
assumptions as ordinary opaque materials. The 8K dimensions, however, are
direct DDS-header facts.

## Why the alternatives did not win

- [Traverse the Ulvenwald](https://www.nexusmods.com/skyrimspecialedition/mods/57874)
  3.3.2 and [Fabled Forests](https://www.nexusmods.com/skyrimspecialedition/mods/94462)
  2.1A remain legitimate lighter alternatives, but their bases have not been
  updated since 2023 and 2024 respectively.
- Sprigganlands 1.3a is the newest serious challenger and its 2K Performance
  archive obeys the hard texture ceiling. It is nevertheless a very young,
  high-poly vanilla replacer: the author states 10,000–18,000 triangles per
  tree and lists triangle reduction and further LOD work as future plans. It
  does not yet have NotWL/Nordic Cut's placement, patch, and regression history.
- Happy Little Trees remains the fallback when measured frame-time or draw-call
  testing shows that NotWL/Nordic Cut is too costly. It is the performance
  choice, not the visual-diversity choice.

## Required installation and validation order

1. Install NotWL 3.14 with only selected FOMOD options.
2. Install Nature of the Mild Lands 3.14 loose files after NotWL while PBR is
   held. Do not redistribute either archive.
3. Install Nordic Cut 1.2.2, then only the relevant entries from its 1.2.2 patch
   collection. Load the patch collection late as its author directs.
4. Resolve conflicts against Lux/Lux Via, Bruma, Alternate Start, city mods and
   Vanaheimr before generating LOD.
5. Generate TexGen and DynDOLOD once the landscape/tree/grass set is frozen.
6. Validate on a disposable new game: frame-time in Falkreath/Riften/Morthal,
   VRAM use, tree pop/LOD transitions, floating or clipping trees, NPC pathing,
   seasonal variants, and save/reload stability.

Do not enable Nordic Cut's unsupported larger-tree BOS scaling or its Happy
Little Trees swap for the baseline. Both complicate clipping and matching LOD.

## Licensing and collection boundary

NotWL assets may not be modified or redistributed without permission, although
the author allows patches. Nordic Cut's plugin is closed for modification and
distribution. Nature of the Mild Lands is also closed and explicitly disallows
paid-modlist use. A public free collection may reference the original Nexus
files; it must not embed these archives or derived textures. Record the
collection's free/non-commercial status and re-check page permissions before
publication.
