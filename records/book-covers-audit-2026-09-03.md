# Book Covers Skyrim audit: adopt the assets, refuse the plugin

Audit date: 2026-09-03.

Runtime: Skyrim SE `1.7.104`. MO2 instance `mo2-instances\skyrim-se`, profile
`Default` (251 enabled mods, 262 active plugins).

Subjects: [Book Covers Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/901)
(`901`, v4.2, 2017-12-03, DanielCoffey, 65,418 endorsements) and its companion
[Book Covers Skyrim - Lost Library](https://www.nexusmods.com/skyrimspecialedition/mods/902)
(`902`, v2.2, 2019-06-15, 9,642 endorsements). Both **Unreviewed** in the
curator, neither installed.

**Disposition: audit only.** Nothing was installed, no profile file was touched,
no curator decision changed, the game was never launched, and the instance claim
(held by Sol, `sol/currency-stack`) was not taken. Archives went to the MO2
download cache and were extracted to `downloads\x*`, outside `mods\`.

---

## Only your eye can settle these

1. **Book covers at shelf distance: clean, or flat?** Measured against the
   vanilla 256px shelf-book textures at the same sampled width, BCS covers carry
   **hf x0.61 (256 px) and x0.58 (128 px)** — under the project's 0.70 floor on
   25/40 and 31/40 of the sample. Against the vanilla 1024px read-model textures
   the same files score **x0.79 and x0.87**, and at 512 px they are **x1.12 to
   x1.57**, clearly ahead. Both readings are real; they differ because vanilla
   ships the same book art twice, small and large (receipt in §3). The 0.70
   floor was calibrated on *skin*, where "matte at distance" is a defect. A book
   cover is a flat printed object, and much of vanilla's high-frequency energy at
   256 px is the dither noise of a 256px source. I can measure it; I cannot tell
   you whether x0.61 reads as *flat* or as *clean*.
2. **The renaming scheme.** BCS deliberately re-titles books into a sorting
   catalogue: `Katria's Journal` becomes `Journal - Katria's`, `Cicero's Journal
   - Final Volume` becomes `Journal - Cicero's, Part 5`. That is **211 renames**
   on records USSEP does not touch, plus **31 more** where it overwrites a USSEP
   name fix (§2). It is not a bug and no patch reverts it by default — it is a
   taste call about how your inventory reads.
3. **Whose page paper?** BCS replaces the two vanilla page textures every book
   uses. On `largebookpaper01.dds` — the page that fills half the screen when you
   read — BCS measures **hf x0.39** against vanilla and
   [Better Books and Letters](https://www.nexusmods.com/skyrimspecialedition/mods/68909)
   measures **x0.90**. Letting BBL win that file is measurably better but pairs
   BCS's covers with upscaled *vanilla* paper instead of BCS's own. Numbers say
   BBL; the look is yours.
4. **Lost Library: 295 new books, or not?** Its record footprint is clean and
   small; its textures are not (hf x0.24–x0.32 at distance, **24 of 25 sampled
   covers below the floor** — the worst measured set in this audit). It is a
   *content* mod whose art is weak. Do you want the books enough to accept that?

Everything else below is decided by evidence.

---

## Recommendation

**Adopt with conditions — as an asset pack, not as a plugin.**

Take the **Original** MAIN file `40352` for its two BSAs, and drive it with
[Book Covers Skyrim - SkyPatched](https://www.nexusmods.com/skyrimspecialedition/mods/109254)
(`109254`, ESLfy file `467900`) plus
[Book Covers Skyrim - SkyPatched Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814)
(`149814`, v1.0.3, updated 2026-05-22) instead of DanielCoffey's ESP. SkyPatcher
is **already installed and enabled** in this build
(`mods\SkyPatcher\SKSE\Plugins\SkyPatcher.dll`).

Why: the shipped ESP overrides 1,185 vanilla records, of which **640 are also
written by USSEP**, and on **355 of the 566 shared BOOK records** its version
differs from USSEP's. The SkyPatched ESP keeps all 1,330 of BCS's *new* records
at byte-identical FormIDs and EditorIDs and drops **every one** of the 1,185
overrides, applying the model / alternate-texture / inventory-art swap at runtime
instead. The conflict does not need resolving; it stops existing.

Pair it with **Better Books and Letters** (`68909`, 2K-1K file `287896`), which
is a plugin-free upscale of the vanilla book art. It fixes the one place BCS
measurably regresses (page textures, §3), and it is the only thing that improves
the **1,012 of 1,586 books in this load order that BCS does not cover at all**
(§3) — Vigilant, Beyond Reach, 3DNPC, Wyrmstooth, Arnima and 29 Creation Club
books all keep vanilla covers under BCS.

**Lost Library: skip for now.** The plugin is well behaved but the textures are
the weakest measured here, and it collides with USSEP and `arnima.esm` on three
vanilla leveled lists (§6).

---

## 1. Rule 0 — prior art

### What already touches book assets in this build: nothing

Scan of all 251 enabled mods, loose files and BSAs, for anything under
`textures/clutter/books`, `textures/interface/books`, `meshes/clutter/books`,
`meshes/dlc0*/clutter/books`, `meshes/dlc02/dungeons/apocrypha`
(`scratchpad\bcs\scan_books.py`, run against
`profiles\Default\modlist.txt`):

| mod | files | what they are |
|---|---|---|
| Snazzy Location Resources | 21 | new `GM_*` note art + its own `meshes/Snazzy Location Resources/...` namespace; only the `openbooknew/` page textures sit on shared paths |
| INIGO | 18 (BSA) | new `textures/clutter/books/images/*.png` for Inigo's journal |
| Grand Solitude | 9 (BSA) | 6 `openbooknew/book page NN.dds` + 2 `openbooknew*.nif` |
| USSEP | 7 (BSA) | Apocrypha mesh fixes, no book covers |
| Unofficial Material Fix | 2 | `apotentaclestatue01.nif`, `apowarpbook01.nif` |
| Assorted Mesh Fixes | 1 | `notetornpaper.nif` |
| Interesting NPCs / Varinia / Beyond Reach / Gray Cowl | 1 each | their own journal images / one Yokudan book mesh |

**No installed mod replaces a single vanilla book cover or note texture.** The
slot is empty. Nothing collides with BCS's added paths.

### What else does this job on Nexus

| mod | id | version | updated | what it is | verdict |
|---|---|---|---|---|---|
| [Book Covers Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/901) | 901 | 4.2 | 2017-12-03 | 910 unique covers via a 2,515-record ESP | the subject |
| [Book Covers Skyrim - SkyPatched](https://www.nexusmods.com/skyrimspecialedition/mods/109254) | 109254 | 4.2 | 2024-02-05 | same assets, **zero vanilla overrides**, SkyPatcher INIs | **the answer to the plugin problem** |
| [BCS - SkyPatched Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814) | 149814 | 1.0.3 | 2026-05-22 | +401 INI lines the base SkyPatched set omits | required for full coverage |
| [Better Books and Letters - Cleaned and Upscaled](https://www.nexusmods.com/skyrimspecialedition/mods/68909) | 68909 | 1.0 / 1.1 | 2022-06-10 | 167 files, 100% vanilla paths, **no plugin** | the lighter rival; complementary, not exclusive |
| [Vanilla-like Tweaks and Fixes for BCS (USSEP and CRF)](https://www.nexusmods.com/skyrimspecialedition/mods/59669) | 59669 | 1.8 | **2026-04-27** | ESL patch forwarding USSEP over BCS + a CRF patch | the answer *if* you keep the vendor ESP |
| [Book Covers Skyrim PBR](https://www.nexusmods.com/skyrimspecialedition/mods/155254) | 155254 | 2.0.0 | 2025-09-17 | CS TruePBR conversion, 527.7 MB + 155.6 MB | hard-requires 901 and 902; TruePBR must be on |
| [BCS - Lost Library REDUX 4K-2K](https://www.nexusmods.com/skyrimspecialedition/mods/70272) | 70272 | 1.0 | 2023-02-13 | XilaMonstrr's 4K/2K rebuild of 902, **ESP-FE plugin** | supersedes 902 if Lost Library is ever wanted |
| [Book Covers Skyrim - Wrye Bash Edition](https://www.nexusmods.com/skyrimspecialedition/mods/81641) | 81641 | 5.0 | 2022-12-30 | ESL import source for a Bashed Patch | only relevant if you run Wrye Bash |
| [Books of Skyrim SE - Reimagined](https://www.nexusmods.com/skyrimspecialedition/mods/46991) | 46991 | 6.7 | 2026-08-02 | rewrites book *text*, 6.6 MB | orthogonal, not a retexture |
| [Book Cover Skyrim Enhanced Textures](https://www.nexusmods.com/skyrimspecialedition/mods/178820) | 178820 | 1 | 2026-04-30 | Topaz Gigapixel upscale of BCS, 6.2 GB (4K) / 1.6 GB (2K) | 23 endorsements, 1,138 downloads; an AI upscale of an 8-year-old source. Not recommended |

Searched: Nexus v1 API (`/mods/<id>.json`, `/mods/<id>/files.json`) for every id
above; web search on `nexusmods skyrimspecialedition "book covers" PBR parallax
books retexture` and `"Book Covers Skyrim REDUX" OR "Book Covers Skyrim -
Improved" ESL flagged plugin patch`; the LOOT masterlist entry at
`masterlist.yaml:18717`; and the full enabled-mod asset scan above. **Nothing
newer replaces BCS's job.** What has moved since 2017 is not the art, it is the
*delivery*: SkyPatched (2024) and Missing Books (2026) exist precisely because
the plugin is the problem.

### The ecosystem survey scores 0 — and that means nothing here

Confirmed: `grep -ic "book covers" docs/ECOSYSTEM-SURVEY-2026-08-30.md` returns
**0**, and `901`/`902` appear nowhere in it. But that survey never surveys a
book-cover slot at all — the only mention of books is inside one
"Clutter/furniture" row summarising the Eldergleam visual stack
(`docs/ECOSYSTEM-SURVEY-2026-08-30.md:155`). Zero mentions therefore means *the
slot was not surveyed*, not *the ecosystem dropped it*. The currency evidence
that does exist points the other way: LOOT carries a full masterlist entry with
live patch conditions for Requiem and Wintersun, and the surrounding ecosystem
shipped updates in **2024 (SkyPatched), 2025 (PBR), 2026-04 (Vanilla-like Tweaks
1.8), 2026-05 (Missing Books 1.0.3)**. BCS is 2017 art with a 2026 support
ecosystem — the `reference_skyrim_ecosystem_currency_filter` case for dropping
Falskaar does not apply.

---

## 2. The plugin's record surface, and what it does to USSEP / CRF / Lux

`skyrim-record-cli-1f3c8d9 plugin-info "Book Covers Skyrim.esp"`
(sha256 `61fade1a…6e7e`, 3,043,481 bytes, masters Skyrim/Update/Dawnguard/
Hearthfires/Dragonborn):

```
2,515 records — Book 910, TextureSet 709, Static 621, PlacedObject 210, Cell 63, Worldspace 2
```

Split by FormID source: **1,330 new** (621 STAT + 709 TXST) and **1,185
overrides** (910 BOOK, 210 REFR, 63 CELL, 2 WRLD).

### The plugin is dirty, by LOOT's own record

`zlib.crc32` of the shipped ESP is **`0x32587221`** — one of the two CRCs LOOT
lists under `clean:` for this plugin (`masterlist.yaml:18746-18750`). Lost
Library's ESP is **`0xDA570813`**, likewise listed (`masterlist.yaml:18769`).
Both shipped files need SSEEdit QuickAutoClean. LOOT also tags BCS
`Graphics, Names, ObjectBounds, Sound, Stats` — its own view that this plugin
carries far more than graphics.

The Original and Desaturated MAIN archives ship a **byte-identical** plugin
(both sha256 `61fade1a…6e7e`), as does the English folder of the Language Pack
`40350`. For an English install the Language Pack is a no-op.

### USSEP: 640 shared FormKeys, 355 records that disagree

`scratchpad\bcs\overlap.py` inventoried all 262 active plugins and intersected
them with BCS's 1,185 overrides:

| plugin | shared FormKeys | breakdown |
|---|---|---|
| **unofficial skyrim special edition patch.esp** | **640** | Book 566, Cell 60, REFR 12, WRLD 2 |
| Lux.esp | 62 | Cell 60, WRLD 2 |
| SFCO3-BOS - Addons.esp | 44 | Cell 43, WRLD 1 |
| Navigator-NavFixes.esl | 23 | Cell |
| 3DNPC.esp | 23 | Cell |
| Water for ENB (Shades of Skyrim).esp | 21 | Cell 21 |
| Ensrick Lux Water CS Patch.esp | 18 | Cell 18 |
| Landscape and Water Fixes.esp | 17 | Cell |
| Unofficial Skyrim Modders Patch.esp | 10 | Cell 9, Book 1 |
| Grand Solitude | 9 | Cell |
| **cutting room floor.esp** | **9** | Book 7, Cell 2 |
| Skyrim Unbound.esp | 7 | Cell 6, Book 1 |
| Lux - USSEP patch.esp | 5 | Cell |
| …33 more plugins | 1–4 each | almost all Cell |

**`Ensrick CRF Semantic Patch.esp` shares nothing with BCS.** It is active
(`plugins.txt`) and writes none of BCS's 1,185 FormKeys — no collision at all.

Field-level, three-way (vanilla master / USSEP / BCS, English strings only,
`scratchpad\bcs\threeway.py`) over the 566 shared BOOK records:

| field | agree | BCS reverts a USSEP fix | BCS's own change | both changed, differently |
|---|---|---|---|---|
| Name | 324 | 5 | 211 | 26 |
| BookText | 341 | 95 | 3 | 127 |
| Value | 562 | 1 | 3 | 0 |
| PickUpSound | 562 | 2 | 2 | 0 |
| Description | 564 | 2 | 0 | 0 |
| Keywords / Weight / Teaches / Type / Flags / VMAD | 566 | 0 | 0 | 0 |

**355 of 566 records differ from USSEP on at least one field.** Concretely, if
BCS loads after USSEP:

- **BookText, 222 records.** BCS carries a 2017 snapshot. Its own v4.2 changelog
  says "Reflect USSEP changes to…" and lists ~20 books — that was the last sync,
  eight and a half years ago. Examples measured by `difflib`:
  `DLC1LD_AetheriumWars` keeps `dwarven cities` where USSEP has `Dwarven cities`
  (3 runs); `DLC1LD_KatriaJournal` keeps `scheming elf` and `'Friend and
  Colleague'` where USSEP has `scheming Elf` and `"Friend and Colleague"` (15
  runs); `DLC1DarkfallPassageNote01` keeps two double-spaces USSEP collapsed.
- **Names, 242 records.** 211 are BCS's catalogue scheme on records USSEP never
  touched; 31 overwrite a USSEP correction (`Butcher Journal #1` → USSEP
  `Butcher's Journal #1` → BCS `Journal - Butcher's, Part 1`; `Hand-written Note`
  → USSEP `Handwritten Note` → BCS `Note to Interrogator`).
- **`DLC2FrostmothLetter01/02/03` value 5 → 0**, `DLC2HrodulfsHouseNote01`
  value 0 → 1.
- **`DLC2HrodulfsHouseNote01` and `WIAddItem03Contract` lose the book PickUpSound**
  (`0C7A54:Skyrim.esm`) USSEP added.
- **`dunMiddenTreasureMap` and `dunTreasMapRiverwood` regain the vanilla
  Description** USSEP blanked.

### Cutting Room Floor: 9 FormKeys, 7 of them books

`DunHillgrundsTombValsVeransLetter`, `TG05GallusJournal`, `MGR01Book1`,
`FreeformWinterholdCollegeANotes`, `FavorRunilJournal`, `dunRagnvaldBook01`,
`dunMzinchaleftGuardNote`, plus cells `FellglowKeep01` and `SolitudeCastleDour`.
Small, and mod `59669` ships a two-record `Patch - BCS CRF.esp` (ESL, 3,846
bytes) for exactly these.

### The cells are dirt, and Lux is downstream of them

BCS's 63 CELL records were compared field-by-field against their masters
(`scratchpad\bcs\cell_diff.py`, 21 semantic fields):

- **42 of 63 are identical to vanilla on every semantic field** — pure ITMs.
- The other 21 differ only in incidental fields: WaterHeight 16, Music 2, Grid 2,
  AcousticSpace 1, SkyAndWeatherFromRegion 1, Owner 1, Lighting 1.
- The 210 PlacedObject overrides look the same; the sampled `000E7D:Skyrim.esm`
  matches its master field for field.

**60 of those 63 cells are Lux cells**, and BCS's vanilla copies differ from Lux
on `Lighting`, `LightingTemplate`, `ImageSpace` and `SkyAndWeatherFromRegion` —
Winterhold Arcanaeum, Dragonsreach, Blue Palace, Bards College, Castle Dour, Sky
Haven Temple, Vlindrel Hall, Thalmor Embassy, Helgen Keep, Twilight Sepulcher and
50 more. Loading BCS after Lux would revert Lux's interior lighting in all sixty.

Under a LOOT sort it does not: `Lux.esp` is in group `Cell Weather & Lighting`
(`masterlist.yaml:5390`), which loads after the default group
(`masterlist.yaml:848-850`), and BCS has no group. So Lux wins. That is a
guardrail, not a fix — it depends on nobody ever hand-placing BCS. Both routes
below remove the risk entirely: cleaning the plugin deletes the ITMs, and the
SkyPatched plugin has **no CELL records at all**.

### The route that dissolves the whole section

`skyrim-record-cli records` on SkyPatched's `Book Covers Skyrim.esp`
(sha256 `0bfc3a22…e3b1` non-ESL / `e114d548…9483` ESL-flagged, both 218,703
bytes, `0x200` set on the second):

```
1,330 records — Static 621, TextureSet 709.  Book 0, Cell 0, PlacedObject 0, Worldspace 0.
```

Verified against BCS's own records: **all 1,330 FormKeys identical, 0 EditorID
mismatches, 0 extra records** — it is BCS's plugin with the 1,185 overrides
deleted and nothing else changed. It keeps the same filename, so BCS's two BSAs
still load. The graphics swap moves to SkyPatcher INIs:

```
filterByBooks=Skyrim.esm|10F776:model=clutter\books\BCSSENote.nif
  :alternateTexturesToAdd=BCS_NoteRecipeAtronach01R~Note Back~0,BCS_NoteRecipeAtronach01F~Note Front~1
  :inventoryArt=BCS_Note_RecipeAtronach01
```

Only `model`, `alternateTexturesToAdd` and `inventoryArt` — Name, BookText,
Value and PickUpSound are never touched, so USSEP stays the winner on all 566.
Coverage: base SkyPatched ships **508** `filterByBooks` lines, Missing Books adds
**401**, for **909 lines / 899 distinct BOOK FormKeys** against BCS's 910
overrides. Both are needed.

What SkyPatched gives up: BCS's 63 CELL and 210 REFR overrides. Since those
measure as ITMs (above), the loss is nil.

---

## 3. Textures at distance, mip chains and compression

### #188 does not recur here

Header scan of every DDS in both BSAs (`scratchpad\bcs\tex_headers.py`, via the
project's BSA reader):

| set | files | resolutions | formats | mip chains |
|---|---|---|---|---|
| BCS Original | 1,571 dds (546.4 MB uncompressed-in-BSA) | 1024x512 ×1038, 512x512 ×355, 1024x1024 ×177, 2048x1024 ×1 | BC1 892, BC3 679 | **1,571 / 1,571 full. 0 mipless.** |
| BCS Desaturated | 1,571 dds (537.6 MB) | identical | identical | identical |
| Lost Library | 608 dds (252.7 MB) | 1024x512 ×592, 512x512 ×11, 1024x1024 ×5 | BC1 306, BC3 302 | **608 / 608 full. 0 mipless.** |

By map kind: **892 diffuse BC1, 678 normal BC3, zero uncompressed, zero BC1
normals.** This is the opposite of
[#188](https://github.com/Ensrick/skyrim-mod-assistant/issues/188) (Cloaks of
Skyrim: 19 mipless, 46 uncompressed). The 463.7 MB download is 1,571 hand-drawn
1K covers, not bloat. Also 641 NIFs (BCS) and 302 (Lost Library).

One resolution regression: **`largebookpaper01_n.dds` ships at 512x512 where
vanilla is 1024x1024** — a halved normal map on the most-referenced texture in
the mod (538 of 641 BCS meshes point at the `largebookpaper01` pair).

### The two regimes are a vanilla design fact, not a judgement call

Scanning every vanilla `meshes/clutter/books/*.nif` for embedded texture paths
(`scratchpad\bcs\nif_tex.py`, 83 meshes, 0 unmatched):

- **38 shelf/world meshes** (`basicbook01.nif` … `basicbook07a.nif`,
  `book01.nif`, `book02da*lowpoly.nif`) reference the **256px** `book0N.dds` +
  `book01paper.dds`.
- **45 read/held meshes** (`book02/character assets/*.nif`,
  `book01/character assets/*.nif`) reference the **1024px** `largebook*.dds` +
  `largebookpaper01.dds`.

So "at distance" means the 256px set and "in hand" means the 1024px set. BCS
collapses the split: five generic world meshes
(`bcssebookstandard/booktall/journal/note/treasuremap.nif`, cover swapped per
book by AlternateTextures) and 538 per-book `*ca.nif` read models all draw the
**same 1024x512 cover sheet**.

### Measured, 40-cover random sample (seed 20260903), median vs the median vanilla reference

`audit/mip_retention.py` `compare()` + `distance_verdict()`; ratios are
mod/vanilla at matched sampled width; the floor is 0.70.

**BCS 1024x512 covers vs the median of vanilla `book01–07` (the shelf set):**

| sampled width | hf | tone | below floor |
|---|---|---|---|
| 512 px | **x1.57** (0.73–3.01) | x1.38 | 0/40 |
| 256 px | **x0.61** (0.29–1.27) | x0.75 | 25/40 |
| 128 px | **x0.58** (0.25–1.51) | x0.82 | 31/40 |
| 64 px | x0.71 (0.41–1.65) | x0.96 | 19/40 |

**BCS 1024x512 covers vs the median of vanilla `largebook01–07` (the read set):**

| sampled width | hf | tone | below floor |
|---|---|---|---|
| 512 px | **x1.12** (0.52–2.14) | x1.00 | 7/40 |
| 256 px | **x0.79** (0.37–1.63) | x1.01 | 15/40 |
| 128 px | **x0.87** (0.37–2.25) | x1.05 | 13/40 |
| 64 px | x0.86 (0.50–2.00) | x1.06 | 12/40 |

Layout-independent framing, since the sheets differ in aspect: BCS's 1024x512
cover is **524,288 texels per book**, against vanilla's 65,536 on the shelf (×8)
and 1,048,576 in hand (÷2). BCS therefore carries eight times the shelf texture's
budget and shows x0.58–0.61 of its high-frequency energy at the same sampled
width — the extra resolution buys legible, distinct cover art and title text, not
grain. Whether that reads as *clean* or *flat* is shortlist item 1.

Notes fare worse: BCS's 1024x1024 note diffuses measure **hf x0.43–x0.52** and
tone x0.68–x0.76 against the vanilla note set at 256 and 128 px, 8–10 of 12 below
the floor.

### The five true vanilla-path replacements — the strict policy test

Only **20 of BCS's 2,212 payload files sit on vanilla paths** (15 spell-tome
NIFs + 5 textures). The textures:

| file | vanilla | BCS | mid/far hf | tone | verdict |
|---|---|---|---|---|---|
| `book01paper.dds` | 256² BC1 | 512² BC1 | **x1.19** (x1.36 @256) | x1.25 | **pass** |
| `book01paper_n.dds` | 256² BC3 | 512² BC3 | x0.35 | x3.17 | flatter, deeper relief |
| `largebookpaper01.dds` | 1024² BC1 | 1024² BC1 | **x0.39** (x0.90 @mip0) | x0.65 | **fail** |
| `largebookpaper01_n.dds` | 1024² BC3 | **512² BC3** | **x0.19** | x0.20 | **fail + downres** |
| `dragonparchment_d.dds` | 2048x1024 BC3 | 2048x1024 BC3 | x0.47 | x1.47 | less grain, more contrast |

Original and Desaturated score **identically** on all five — the desaturation was
applied to coloured cover art only, not to neutral paper.

### The lighter rival, measured

[Better Books and Letters](https://www.nexusmods.com/skyrimspecialedition/mods/68909)
2K-1K (`287896`, 345,491,711 bytes, sha256 `3d4d5b64…0bf021`): 167 files,
**167/167 on vanilla paths, 0 new paths, no plugin**, all BC7, 0 short mip chains
(1024² ×119, 2048² ×42, 512² ×6). Against vanilla, mid/far **hf median x0.83**
(0.57–1.15), tone x0.99, **5 of 92 diffuses below the floor**. It passes the
project standard where BCS's page textures do not.

It is not a substitute — it upscales seven generic covers, it does not create 910
unique ones — but it is **complementary**, and it wins where it overlaps. The two
mods share exactly **4 files**:

| shared file | BCS | BBL |
|---|---|---|
| `book01paper.dds` | **x1.19** | x0.81 |
| `book01paper_n.dds` | x0.35 | **x0.87** |
| `largebookpaper01.dds` | x0.39 | **x0.90** |
| `largebookpaper01_n.dds` | x0.19 | **x1.05** |

BBL wins three of four, including both halves of the page you actually read.
Let it win the file conflict (higher in `modlist.txt`, which is stored in
descending priority). Note also that BBL ships loose and BCS ships BSA-packed —
in SSE, loose assets take precedence over archived ones, so this likely resolves
in BBL's favour regardless of MO2 order. *[unverified — not tested in-game.]*

### Coverage on THIS load order

Counting every BOOK FormKey defined anywhere in the 262 active plugins against
BCS's 910 (`scratchpad\bcs\coverage.py`):

**1,586 books in the active order. BCS covers 910. 1,012 get nothing:**
Vigilant 179, Beyond Reach (`BSHeartland`) 163, 3DNPC 137, `BSAssets` 135,
Wyrmstooth 96, Arnima 94, Campfire 43, Gray Cowl 29, Creation Club 29
(`ccbgssse025-advdsgs` 21 + `ccbgssse001-fish` 8), Inigo 16, plus stragglers.

**BCS covers 57% of the books in this build.** The other 43% keep vanilla art —
which is the strongest argument for adding Better Books and Letters, since that
is the art all 1,012 of them still use.

---

## 4. Original vs Desaturated

The plugin is byte-identical between them, so this is purely a texture decision.
Measured on the same 60-file sample decoded from each BSA
(`scratchpad\bcs\tone.py`; sat = mean HSV saturation, chroma = mean (max−min)
across RGB in 0–255 units, all medians):

| set | mip 0 sat | mip 0 chroma | mip 3 chroma | luminance | contrast (lum sd) |
|---|---|---|---|---|---|
| BCS **Original** | 0.375 | **52.8** | 52.8 | 91.5 | 34.2 |
| BCS **Desaturated** | 0.213 | **26.2** | 26.2 | 91.3 | 34.2 |
| vanilla book textures (n=32) | 0.268 | **41.1** | 40.9 | 75.7 | 28.2 |

Paired, file by file, the Desaturated set is mechanically exact:

```
BCS  mip0/2/3  Desat/Orig:  saturation x0.575/0.570/0.569
                            chroma     x0.498/0.499/0.498
                            luminance  x0.977   contrast x0.971
```

**Desaturated is Original with chroma cut to exactly half.** Luminance and
contrast are untouched, and the effect is identical at every mip, so it changes
nothing about the distance behaviour in §3 — only the colour.

Against vanilla's own book palette (chroma 41.1): Original is **x1.29**,
Desaturated is **x0.64**. In ratio terms Original sits 1.29× from vanilla and
Desaturated 1.57× the other way, so **Original is the closer match to the palette
Bethesda shipped**.

For this build specifically: the lighting stack is Azurite Weathers III + Azurite
III CS + Lux / Lux Orbis / Lux Via / Lux CS + Community Shaders AIO (1.7.99
source build) + ENB Light — all confirmed enabled in `modlist.txt`. Books are
overwhelmingly an interior object, and Lux's interiors are darker than vanilla's
flat ambient; less light on a surface subtracts apparent chroma, so starting from
a set that has already given away half its chroma compounds the loss, while a
saturated weather suite does not add chroma back to an interior. *[That last
sentence is reasoning from how the stack works, not a measurement — the measured
part is the x0.50 chroma cut and the vanilla comparison above.]*

**Take Original, file `40352`.** Desaturated would be the pick only if you find
vanilla books too colourful, which the numbers say you do not, since vanilla sits
between them and nearer Original.

---

## 5. Permissions and distribution class

Fetched from the Nexus pages (browser UA; the v1 API does not expose
permissions), quoted verbatim.

**Book Covers Skyrim (901) and Lost Library (902) — identical terms:**

> Upload permission: You can upload this file to other sites but you must credit
> me as the creator of the file
> Modification permission: You are allowed to modify my files and release bug
> fixes or improve on the features so long as you credit me as the original creator
> Asset use permission: You are allowed to use the assets in this file without
> permission as long as you credit me
> Asset use permission in mods/files that are being sold: not allowed

901's author note goes further:

> You don't need ask me for permission to use the contents of this mod for any
> reason. You have it. You can add to, subtract from, alter, enhance, embellish,
> patch, improve to your hearts content. … I only request ONE thing in return.
> 1) You acknowledge the work I've done, and the work of those that I have credited.

Related mods: **SkyPatched (109254)** — modify and use assets "without permission
or crediting me", upload elsewhere with credit. **Missing Books (149814)** — same
as BCS. **PBR (155254)** — modify/use without credit. **Vanilla-like Tweaks
(59669)** — *"You are not allowed to upload this file to other sites under any
circumstances"*, but modification and asset use are free, and the author note
says "please feel free to use this as a base for any further patches going
forward".

### Distribution class per `docs/PATCH_INTENTS.md`

Per the lead ruling of 2026-09-02 (#160), the Ensrick collection carries only our
own work; an unmodified third-party release is a **vendor row** regardless of how
permissive its licence is. Therefore:

- **BCS `901`, SkyPatched `109254`, Missing Books `149814`, Better Books and
  Letters `68909`, Vanilla-like Tweaks `59669`** — vendor rows. Record source
  URL, file id and archive SHA-256 on the ledger row; no `distribution:` field.
  `59669` additionally forbids re-upload, so it is a hard required-download.
- **A load-order or ordering note** (BBL must win the four shared page files) —
  documentation, no artifact.
- **If we ever author a USSEP forward ourselves** instead of using `59669`: our
  own bytes, ESP-FE, **`distributable`**. BCS's permissions explicitly allow it
  with credit, and it contains only our records, not BCS's assets.
- **If we ever regenerate `largebookpaper01_n.dds` at 1024²** from BCS's source
  (or re-sharpen a mip chain): a modified vendor asset — **`recipe`**, never
  bundled, regenerated locally, exactly like the Lost LongSwords precedent in
  `REDISTRIBUTION.md`. Note this one is probably unnecessary if BBL wins that
  file anyway.

Nothing here lands in **local-only**.

---

## 6. Lost Library, judged separately

`skyrim-record-cli plugin-info "Book Covers Skyrim - Lost Library.esp"`
(sha256 `2a699b21…645d`, 1,899,295 bytes, CRC `0xDA570813` — on LOOT's clean
list):

```
1,094 records — TextureSet 300, Static 299, Book 298, PlacedObject 130,
                Cell 38, LeveledItem 16, Container 9, Worldspace 3, Quest 1
```

**1,040 new, 54 overrides.** Far better behaved than the base mod: it adds 295
books rather than rewriting vanilla ones, and it touches **no vanilla BOOK
record at all**.

**Leveled lists.** 6 new lists (`BCSLL_Books_List_Cheap70/Common60/Valuable50/
Rare40/Religious50/Morrowind50`) injected into **10 vanilla lists**:
`LItemBook1All`, `LItemBook2All`, `LItemBook3All`, `LItemBook4All`,
`LItemBookClutter`, `LootSilverHandBooks10`, `LItemVigilantBooks`,
`LootForswornRandomWizard`, `LootWarlockRandom`, `LootThalmorRandomWizard`.
Merchant stock is driven by a single new quest, `BCSLL_VendorQuest`, with one
Papyrus script (`BCSLL_VendorScript.pex`) and 9 new containers.

**Collisions in this load order** (`scratchpad\bcs\overlap_ll.py`):

- **`LItemBook2All`, `LItemBook3All`, `LItemBookClutter` are written by USSEP**,
  and `LItemBook3All` + `LItemBookClutter` also by **`arnima.esm`**. Loading
  Lost Library later drops both mods' entries on those three lists. LOOT tags
  Lost Library `[ Delev ]` (`masterlist.yaml:18767`) precisely because it expects
  a Bashed Patch to merge them. Without a Bashed Patch this build would need a
  hand-authored forward.
- **38 cell overrides**, of which USSEP writes 33, Lux 29, SFCO3-BOS 16, Water
  for ENB 13, `Ensrick Lux Water CS Patch` 13, Navigator 13 — same shape as the
  base mod's cell problem, on a different 38 cells (`WhiterunAmrensHouse`,
  `SolitudeBardsCollege`, `TowerOfMzark`, `BlackBriarLodge01`, four Solstheim
  interiors, three Blackreach cells, …). These are *real* edits (it places new
  book statics and containers), so they cannot simply be cleaned away.
- 3 worldspace overrides (Tamriel, Solstheim, Soul Cairn), touched by ~40 active
  plugins already — routine.

**The art is the problem.** 25-cover random sample, same method as §3:

| vs | 512 px | 256 px | 128 px | 64 px | below floor |
|---|---|---|---|---|---|
| vanilla `book01–07` | hf x0.60 | **x0.25** | **x0.24** | x0.36 | 24–25 of 25 |
| vanilla `largebook01–07` | x0.43 | x0.32 | x0.36 | x0.43 | 24 of 25 |

Tone x0.46–0.63. This is the weakest measured set in the audit by a wide margin —
worse at distance than anything in the cloak audit except the PBR pack. Format
hygiene is fine (BC1 diffuse / BC3 normal, 608/608 full mip chains, 1024x512),
but the source art simply carries very little high-frequency detail.

Desaturated vs Original behaves the same way as the base mod: chroma x0.500,
luminance x0.973.

**Verdict: skip 902.** If the 295 books are wanted later, start from
[Lost Library REDUX 4K-2K](https://www.nexusmods.com/skyrimspecialedition/mods/70272)
(`70272`, XilaMonstrr, ESP-FE plugin file `294218`, 2K files `294299`/`294316`,
LoTD patch `359410`) rather than 902 — LOOT's own masterlist links REDUX from the
902 entry — and budget a leveled-list forward for USSEP and Arnima either way.

---

## What adoption would take

1. Install **BCS Original `40352`** for its two BSAs; do **not** enable
   `Book Covers Skyrim.esp` from that archive.
2. Install **SkyPatched `109254` file `467900`** (ESLfy) over it — same filename,
   so the BSAs still load; the plugin is ESP-FE and costs no full slot.
3. Install **Missing Books `149814` file `755004`** (`0-Required` INI folder;
   the FOMOD's `1-Treasure` ESP options are only for the vendor-ESP route).
4. Install **Better Books and Letters `68909` file `287896`** and let it win the
   four shared page files.
5. Ledger rows for four vendor mods (source URL, file id, archive SHA-256), four
   Keeps queued at the *end* of the install per `docs/CURATION_POLICY.md`, a
   `CHANGELOG.md` entry naming this record, and a `py -3 audit/launch_verify.py`
   PASS before any of it is called done.
6. `py -3 audit/file_conflicts.py` afterwards to confirm the only BCS/BBL
   collision is the expected four files.

**If instead the vendor ESP is kept** (because the 211 catalogue renames are
wanted, and SkyPatcher does not do names): clean it with SSEEdit QuickAutoClean
(CRC `0x32587221` is on LOOT's list), then add **`59669` file `746258`**
(`Patch - BCS USSEP.esp`, ESL, 465 BOOK + 3 CELL + 3 REFR forwards) and
**file `247720`** (`Patch - BCS CRF.esp`, ESL, 2 records). That patch is v1.8,
updated 2026-04-27 — actively maintained. It restores USSEP's text and stats
while keeping BCS's models; it does **not** restore USSEP's names, which is the
point of shortlist item 2.

Not recommended either way: `178820` (6.2 GB AI upscale, 23 endorsements) and
`155254` (PBR) — the latter hard-requires both 901 **and** 902, and 902 is a skip.
TruePBR ships in the installed CS build (`Shaders/Features/TruePBR.ini`) but
whether it is enabled at runtime was not determined from disk. *[unverified]*

---

## Receipts

**Archives** (MO2 download cache
`mo2-instances\skyrim-se\downloads`, extracted to sibling `x<id>-<file>` dirs):

| file | bytes | sha256 |
|---|---|---|
| `901-40352.7z` (Original) | 486,228,148 | `a93548075a094cce92b4330b8d092d7bbad5ac104ae991f0b6ad88ed01a0e429` |
| `901-40355.7z` (Desaturated) | 478,881,187 | `22e456b3d321a5350dd5eb3dfb4c9ff30e9ca0b7d1e2327c3f4936d52c8e7be7` |
| `901-40350.7z` (Language Pack) | 5,523,066 | `63a993da51d42b638994c80357c2007c056b83ef30d69e73a72eb83a507bfde3` |
| `902-96086.7z` (LL Original) | 201,428,339 | `ac1c46087e0b236696c7ee719732bfe6676a6fef7fada246777f3d116cad7511` |
| `902-96090.7z` (LL Desaturated) | 199,231,020 | `5489d0a8687db1c00ee85f0500a69ca4ecae1c90096721bbcaab826fa6c9298a` |
| `68909-287896.7z` (BBL 2K-1K) | 345,491,711 | `3d4d5b645750bb04f5833385cc611f89965e7be5b60f143144351021360bf021` |
| `109254-461289.zip` (SkyPatched) | 38,417 | `abf05dbb392ab7fbddab2698a016866c404b4087761defa790653635a105465f` |
| `109254-467900.zip` (SkyPatched ESLfy) | 24,835 | `af85844bb420cd918b30e991ec76376fece46ce1363a95c49e21cf242a62c0f1` |
| `149814-755004.7z` (Missing Books) | 10,230 | `962cb27fcf82ea22087566cd35f6a753e229fa5dd461e5c421da8fc71e21d19d` |
| `59669-746258.7z` (Vanilla-like Tweaks USSEP) | 469,527 | `7e290116a2eaa43e0f855612a3a76e0756c82acdc2b6ec79faed0367f9692a11` |
| `59669-247720.7z` (BCS CRF patch) | 2,104 | `9575f26aea9ec0cc3f75beba40844845ba376a6735aec2cadfbd630522ddc2bf` |

**Plugins**

| plugin | bytes | sha256 | CRC32 | ESL |
|---|---|---|---|---|
| `Book Covers Skyrim.esp` (901, both variants + lang pack EN) | 3,043,481 | `61fade1a8a8d40d40686d06a9a1a43d07a7d062be0397c883f722d5e4dab6e7e` | `0x32587221` | no |
| `Book Covers Skyrim - Lost Library.esp` | 1,899,295 | `2a699b21db781ac9051258bdc122ba1deff50a0058e8b9ab0c446010cfec645d` | `0xDA570813` | no |
| `Book Covers Skyrim.esp` (SkyPatched) | 218,703 | `0bfc3a22b61ce651a91ef00a8c5a4127ea2f39b2b67e6259943ba7e51525e3b1` | — | no |
| `Book Covers Skyrim.esp` (SkyPatched ESLfy) | 218,703 | `e114d548a2e9fe0fdd88a87f89cbe20592f02e2536eadbcbe4224ea2c91c9483` | — | **yes** |

**Tools.** `skyrim-tools-builds\skyrim-record-cli-1f3c8d9\skyrim-record-cli.exe`
(`plugin-info`, `records`, `record-fields`,
`record-selected-fields-by-type`); `audit/mip_retention.py`
(`level_stats`/`compare`/`distance_verdict`); `audit/modasset.py` BSA + DDS
readers; `audit/vanilla_index.json` (197,582 entries); `audit/verify_order.py`
for the live plugin index; LOOT masterlist
`%LOCALAPPDATA%\LOOT\games\Skyrim Special Edition\masterlist.yaml`.

**Working scripts** (scratchpad, not committed):
`C:\Users\danjo\AppData\Local\Temp\claude\C--Users-danjo-source-repos\8cb7eb06-e1bd-4a5c-a603-fe2544d83e14\scratchpad\bcs\`
— `scan_books.py`, `bsa_inventory.py`, `tex_headers.py`, `overlap.py`,
`book_diff.py`, `threeway.py`, `cell_diff.py`, `measure.py`, `measure2.py`,
`exact.py`, `pages.py`, `tone.py`, `nif_tex.py`, `bcs_meshes.py`, `bbl.py`,
`coverage.py`, `overlap_ll.py`, `flags.py`, `perms.py`.

**Related records.** `records/cloak-layer-audit-2026-09-02.md` (method model),
`docs/CK_FIRST_DOCTRINE.md` rule 0 and rule 3, `docs/CURATION_POLICY.md`
("Textures are judged at distance"), `docs/PATCH_INTENTS.md` (distribution
classes), [#188](https://github.com/Ensrick/skyrim-mod-assistant/issues/188)
(mip/compression precedent).
