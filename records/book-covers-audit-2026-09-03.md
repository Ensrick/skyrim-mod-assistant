# Book Covers Skyrim audit: candidate routes and corrected evidence

## Review corrections — 2026-09-06

**Research only; no installation or Keep/Skip decision is authorized by this
document.** This review supersedes the categorical recommendations in the
September 3 audit. Historical archive inventories and measurements below have
not been rerun against the current profile and must not be presented as current
acceptance evidence.

- **LOOT was read backwards.** The cited CRCs are under `clean:`, not `dirty:`.
  They identify recognized clean plugins, not instructions to QuickAutoClean.
  Record overlaps still merit conflict review, but overlaps and a partial field
  comparison are not proof of ITMs or safe-to-delete records.
- **SkyPatched needs the matching treasure-map plugin.** The
  [Missing Books author](https://www.nexusmods.com/skyrimspecialedition/mods/149814)
  explicitly supplies a small ESP-FE for 12 vanilla treasure maps, whose drawing
  overlays cannot be handled by those INIs alone. Select the variant matching
  the actual SkyPatched ESP/ESP-FE and filename. It is not exclusive to an
  original-plugin installation. The INI-only instructions below were wrong.
- **ESLfy compacts every owned resource FormID.** Fresh September 6 payload
  inspection of file `467900` verifies the same 1,330 record bodies and
  EditorIDs by EditorID, but **all 1,330 FormIDs differ from original BCS**.
  The old identical-FormKey statement must not be applied to the ESLfy
  variant. Use Missing Books' `1-Treasure - OG ESPFE` variant for the unchanged
  `Book Covers Skyrim.esp` filename; original/non-ESL resource links are not
  interchangeable. See the current [approved-batch record](../docs/APPROVED-INSTALL-BATCH-2026-09-06.md).
- **Coverage numbers are retracted pending a distinct-FormKey recount.** The
  prior combination of 1,586 total, 910 covered and 1,012 uncovered is internally
  inconsistent. `BSHeartland.esm` is Beyond Skyrim: Bruma, not Beyond Reach;
  `arnima.esm` is Beyond Reach. A texture-path audit is also required before
  claiming that every uncovered mod-added book uses vanilla covers.
- **Image-frequency statistics are not art-quality verdicts.** The historical
  samples measure different images and a threshold calibrated on skin. They
  cannot establish that smoother paper is defective, a cover is worse, Original
  is the user's preferred palette, or Lost Library should be skipped. Retained
  measurements are descriptive, unvalidated observations, not a pass/fail gate.
- **The traditional patch route is still viable.**
  [Vanilla-like Tweaks and Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/59669)
  v1.8 (2026-04-27) updates USSEP content and deliberately restores mostly
  vanilla names, with its own series-title conventions; it does not preserve
  all of BCS's cataloguing names. Do not combine its original-plugin patches
  blindly with the SkyPatched replacement route.
- **Do not reject PBR solely because Lost Library is unselected.** The
  [PBR files page](https://www.nexusmods.com/skyrimspecialedition/mods/155254?tab=files)
  has separate 1K Original and Lost Library downloads, although the shared
  dependency table lists both. Inspect the Original package's actual JSON and
  assets before deciding whether it has any cross-dependency. This optional
  route also needs working TruePBR and a PGPatcher-generated mesh layer.
- **Texture policy still applies.** Better Books and Letters offers a
  [1K/512 standalone option](https://www.nexusmods.com/skyrimspecialedition/mods/68909);
  the previously recommended 2K/1K option is not blanket-compliant with the 1K
  small-clutter ceiling. Shared reading-page assets need an explicit scope
  decision, not an assumed exemption.

Current recommendation: BCS remains a viable unique-cover candidate. For this
SkyPatcher-enabled build, evaluate its assets plus SkyPatched, Missing Books and
the correctly matched treasure-map ESP-FE. Traditional BCS plus maintained
compatibility patches is an alternative, not a disproven route. Original versus
Desaturated, optional vanilla-page textures, PBR and Lost Library content remain
user decisions. [BCS Updated REDUX (69568)](https://www.nexusmods.com/skyrimspecialedition/mods/69568)
is currently hidden (since 2024-07-18), so it is not a generally available
replacement recommendation. No binary audit was repeated for this correction.

---

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
   x1.57** in that metric. The readings differ because vanilla
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
   measures **x0.90**. Letting BBL win changes the measured texture detail but pairs
   BCS's covers with upscaled *vanilla* paper instead of BCS's own. The metric
   does not select the better-looking paper; that remains a visual decision.
4. **Lost Library: 295 new books, or not?** Its record footprint is clean and
   small; its textures are not (hf x0.24–x0.32 at distance, **24 of 25 sampled
   covers below the historical threshold**). This does not establish poor art
   quality. It is a separate *content* decision, with a visual comparison needed.

The September 6 corrections above qualify the historical conclusions below.

---

## Recommendation

**Candidate route, not an adoption decision: assets plus SkyPatched.**

Take the **Original** MAIN file `40352` for its two BSAs, and drive it with
[Book Covers Skyrim - SkyPatched](https://www.nexusmods.com/skyrimspecialedition/mods/109254)
(`109254`, ESLfy file `467900`) plus
[Book Covers Skyrim - SkyPatched Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814)
(`149814`, v1.0.3, updated 2026-05-22), including its correctly matched
treasure-map ESP-FE, instead of DanielCoffey's ESP. SkyPatcher
is **already installed and enabled** in this build
(`mods\SkyPatcher\SKSE\Plugins\SkyPatcher.dll`).

Why: the shipped ESP overrides 1,185 vanilla records, of which **640 are also
written by USSEP**, and on **355 of the 566 shared BOOK records** its version
differs from USSEP's. The SkyPatched ESP keeps all 1,330 of BCS's *new* records
with matching record bodies and EditorIDs; **the ESLfy variant compacts all
1,330 FormIDs**. It drops **every one** of the 1,185
overrides, applying the model / alternate-texture / inventory-art swap at runtime
instead. This avoids that override surface; the complete result still requires
coverage, model-link, treasure-map and runtime verification.

**Better Books and Letters** (`68909`) is an optional plugin-free upscale of
vanilla book art, not a required fix. Its 1K/512 option is the starting candidate
under the small-clutter policy; the earlier 2K/1K measurement is historical only.
It can improve shared vanilla assets, but the old audit did not establish exact
active-book coverage or that every uncovered book uses those paths (§3).

**Lost Library: separate unresolved content decision.** Historical inspection
reports overlaps with USSEP and `arnima.esm` on three vanilla leveled lists (§6).
Image-frequency scores alone are not a reason to skip its books.

---

## 1. Rule 0 — prior art

### Historical September 3 book-asset inventory, not current-state proof

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
| [BCS - SkyPatched Missing Books](https://www.nexusmods.com/skyrimspecialedition/mods/149814) | 149814 | 1.0.3 | 2026-05-22 | historical count +401 INI lines, plus matching treasure-map ESP-FE | completes the author's intended route; combined coverage must still be verified |
| [Better Books and Letters - Cleaned and Upscaled](https://www.nexusmods.com/skyrimspecialedition/mods/68909) | 68909 | 1.0 / 1.1 | 2022-06-10 | 167 files, 100% vanilla paths, **no plugin** | the lighter rival; complementary, not exclusive |
| [Vanilla-like Tweaks and Fixes for BCS (USSEP and CRF)](https://www.nexusmods.com/skyrimspecialedition/mods/59669) | 59669 | 1.8 | **2026-04-27** | ESL patch forwarding USSEP over BCS + a CRF patch | the answer *if* you keep the vendor ESP |
| [Book Covers Skyrim PBR](https://www.nexusmods.com/skyrimspecialedition/mods/155254) | 155254 | 2.0.0 | 2025-09-17 | separate Original and Lost Library 1K conversions, 527.7 MB / 155.6 MB | needs TruePBR + PGPatcher; inspect actual package dependencies rather than infer both content mods are mandatory |
| [BCS - Lost Library REDUX 4K-2K](https://www.nexusmods.com/skyrimspecialedition/mods/70272) | 70272 | 1.0 | 2023-02-13 | standalone upscale with **ESP-FE plugin**, also 1K/512 option | alternate packaging, not proof of universally better art; old compatibility patches do not work with its changed plugin |
| [Book Covers Skyrim - Wrye Bash Edition](https://www.nexusmods.com/skyrimspecialedition/mods/81641) | 81641 | 5.0 | 2022-12-30 | ESL import source for a Bashed Patch | only relevant if you run Wrye Bash |
| [Books of Skyrim SE - Reimagined](https://www.nexusmods.com/skyrimspecialedition/mods/46991) | 46991 | 6.7 | 2026-08-02 | rewrites book *text*, 6.6 MB | orthogonal, not a retexture |
| [Book Cover Skyrim Enhanced Textures](https://www.nexusmods.com/skyrimspecialedition/mods/178820) | 178820 | 1 | 2026-04-30 | Topaz Gigapixel upscale of BCS, 6.2 GB (4K) / 1.6 GB (2K) | not a direct fit for the 1K small-clutter cap; no visual-quality verdict established |

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

### LOOT recognizes these checksums as clean

`zlib.crc32` of the shipped ESP is **`0x32587221`** — one of the two CRCs LOOT
lists under `clean:` for this plugin (`masterlist.yaml:18746-18750`). Lost
Library's ESP is **`0xDA570813`**, likewise listed (`masterlist.yaml:18769`).
These entries do **not** prescribe QuickAutoClean: the original audit inverted
their meaning. Verify any different archive checksum separately. LOOT also tags BCS
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
Mod `59669` ships a two-record `Patch - BCS CRF.esp` (ESL, 3,846 bytes).
Two records do not by themselves prove that all nine overlapping FormKeys need
or receive a patch; field-level conflict review remains necessary.

### Historical cell-overlap inspection; cleaning conclusion withdrawn

BCS's 63 CELL records were compared field-by-field against their masters
(`scratchpad\bcs\cell_diff.py`, 21 semantic fields):

- **42 of 63 matched vanilla on the sampled semantic fields.** This is not a
  complete-record ITM determination.
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
guardrail, not proof of current ordering. The historical SkyPatched inventory
has **no CELL records at all**, avoiding those particular overrides. The former
claim that cleaning would necessarily remove them is withdrawn; LOOT recognizes
the cited original-plugin CRC as clean.

### The route that dissolves the whole section

`skyrim-record-cli records` on SkyPatched's `Book Covers Skyrim.esp`
(sha256 `0bfc3a22…e3b1` non-ESL / `e114d548…9483` ESL-flagged, both 218,703
bytes, `0x200` set on the second):

```
1,330 records — Static 621, TextureSet 709.  Book 0, Cell 0, PlacedObject 0, Worldspace 0.
```

The historical identical-FormKey statement did not distinguish variants.
Fresh September 6 inspection of ESLfy file `467900` verifies **all 1,330
record bodies identical by EditorID, 0 EditorID mismatches, 0 extra resource
records, and all 1,330 owned FormIDs compacted** relative to original BCS.
It is therefore not only an override deletion, and original/non-ESL patches
must not be used against its compacted resources. It keeps the same filename,
so BCS's two BSAs still load. The graphics swap moves to SkyPatcher INIs:

```
filterByBooks=Skyrim.esm|10F776:model=clutter\books\BCSSENote.nif
  :alternateTexturesToAdd=BCS_NoteRecipeAtronach01R~Note Back~0,BCS_NoteRecipeAtronach01F~Note Front~1
  :inventoryArt=BCS_Note_RecipeAtronach01
```

Only `model`, `alternateTexturesToAdd` and `inventoryArt` — Name, BookText,
Value and PickUpSound are never touched, so USSEP stays the winner on all 566.
Historical INI coverage: base SkyPatched ships **508** `filterByBooks` lines,
Missing Books adds **401**, for **909 lines / 899 distinct BOOK FormKeys**
against BCS's 910 overrides. These are not a complete coverage count: the
Missing Books author handles 12 vanilla treasure maps through the matching
ESP-FE, not those INIs. Recount the combined plugin-and-INI result before claiming
complete coverage.

What SkyPatched gives up: BCS's 63 CELL and 210 REFR overrides. Their absence is
verified by the historical inventory; the original assertion that all were ITMs
and their loss was necessarily nil is unsupported by the partial comparison.

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

Notes have lower measured frequency: BCS's 1024x1024 note diffuses measure **hf x0.43–x0.52** and
tone x0.68–x0.76 against the vanilla note set at 256 and 128 px, 8–10 of 12 below
the floor.

### The five true vanilla-path replacements — historical measurements

The old pass/fail quality labels are withdrawn. Different paper artwork can have
different frequency content without being defective; only measured resolution
and format facts below are independent of that visual judgement.

Only **20 of BCS's 2,212 payload files sit on vanilla paths** (15 spell-tome
NIFs + 5 textures). The textures:

| file | vanilla | BCS | mid/far hf | tone | verdict |
|---|---|---|---|---|---|
| `book01paper.dds` | 256² BC1 | 512² BC1 | **x1.19** (x1.36 @256) | x1.25 | descriptive measurement only |
| `book01paper_n.dds` | 256² BC3 | 512² BC3 | x0.35 | x3.17 | flatter, deeper relief |
| `largebookpaper01.dds` | 1024² BC1 | 1024² BC1 | **x0.39** (x0.90 @mip0) | x0.65 | descriptive measurement only |
| `largebookpaper01_n.dds` | 1024² BC3 | **512² BC3** | **x0.19** | x0.20 | lower source resolution; visual effect unverified |
| `dragonparchment_d.dds` | 2048x1024 BC3 | 2048x1024 BC3 | x0.47 | x1.47 | less grain, more contrast |

Original and Desaturated score **identically** on all five — the desaturation was
applied to coloured cover art only, not to neutral paper.

### The lighter rival, measured

[Better Books and Letters](https://www.nexusmods.com/skyrimspecialedition/mods/68909)
2K-1K (`287896`, 345,491,711 bytes, sha256 `3d4d5b64…0bf021`): 167 files,
**167/167 on vanilla paths, 0 new paths, no plugin**, all BC7, 0 short mip chains
(1024² ×119, 2048² ×42, 512² ×6). Against vanilla, mid/far **hf median x0.83**
(0.57–1.15), tone x0.99, **5 of 92 diffuses below the historical threshold**.
This does not prove a general visual-quality advantage. The 2K/1K archive also
exceeds the 1K small-clutter limit on some files; the author's 1K/512 option is
the policy-aligned candidate for a future audit.

It is not a substitute — it upscales seven generic covers, it does not create 910
unique ones — but it is **complementary**, and it wins where it overlaps. The two
mods share exactly **4 files**:

| shared file | BCS | BBL |
|---|---|---|
| `book01paper.dds` | **x1.19** | x0.81 |
| `book01paper_n.dds` | x0.35 | **x0.87** |
| `largebookpaper01.dds` | x0.39 | **x0.90** |
| `largebookpaper01_n.dds` | x0.19 | **x1.05** |

BBL is closer to the vanilla high-frequency measurement on three of four files;
whether those pages should replace BCS's paper is a user choice. If approved,
verify it wins the intended files. BBL ships loose and BCS ships BSA-packed —
in SSE, loose assets take precedence over archived ones, so this likely resolves
in BBL's favour regardless of MO2 order. *[unverified — not tested in-game.]*

### Coverage on THIS load order

Counting every BOOK FormKey defined anywhere in the 262 active plugins against
BCS's 910 (`scratchpad\bcs\coverage.py`):

**Retracted: no reliable total, uncovered count or coverage percentage was
established.** The prior report gave mutually inconsistent totals (1,586 total,
910 covered and 1,012 uncovered), apparently mixing counting scopes. Do not
reuse the associated 57%/43% claim or the per-mod figures without recounting
distinct active BOOK FormKeys and the complete SkyPatched/treasure-map output.
`BSHeartland.esm` belongs to **Beyond Skyrim: Bruma**; `arnima.esm` belongs to
**Beyond Reach**. Neither the old counts nor an unmatched FormKey proves the
book uses a vanilla texture path. Shared vanilla retextures help only where
the winning mesh/material actually references those files.

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

**Original versus Desaturated remains a user decision.** The historical sample
describes palette differences, not the user's preference, and does not measure
the result under the current lighting configuration. Neither option was adopted.

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
(sha256 `2a699b21…645d`, 1,899,295 bytes, CRC `0xDA570813` — recognized clean
by LOOT, not marked for cleaning):

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

**Historical image-frequency sample, not an art-quality verdict.** 25 covers,
same method as §3:

| vs | 512 px | 256 px | 128 px | 64 px | below floor |
|---|---|---|---|---|---|
| vanilla `book01–07` | hf x0.60 | **x0.25** | **x0.24** | x0.36 | 24–25 of 25 |
| vanilla `largebook01–07` | x0.43 | x0.32 | x0.36 | x0.43 | 24 of 25 |

Tone x0.46–0.63. These lower frequency measurements do not establish that the
art is worse than vanilla, cloaks or PBR. Historical format inspection found
BC1 diffuse / BC3 normal, 608/608 full mip chains and 1024x512 cover sheets.
Visual acceptance remains untested.

Desaturated vs Original behaves the same way as the base mod: chroma x0.500,
luminance x0.973.

**No Keep/Skip decision.** If the 295 books are wanted later, compare 902 with
[Lost Library REDUX 4K-2K](https://www.nexusmods.com/skyrimspecialedition/mods/70272)
(`70272`, XilaMonstrr, ESP-FE plugin file `294218`, 2K files `294299`/`294316`,
LoTD patch `359410`; a 1K/512 option also exists). LOOT links REDUX, but that is
not a quality or universal-supersession verdict. Its author warns its ESP-FE
does not work with previously made patches. Audit integration with USSEP and
Beyond Reach (`arnima.esm`) for whichever route is chosen.

---

## What adoption would take, if separately approved

1. Install **BCS Original `40352`** for its two BSAs; do **not** enable
   `Book Covers Skyrim.esp` from that archive.
2. Install **SkyPatched `109254` file `467900`** (ESLfy) over it — same filename,
   so the BSAs still load; the plugin is ESP-FE and costs no full slot.
3. Install **Missing Books `149814` file `755004`**, including its required INIs
   **and the treasure-map ESP-FE matching the selected SkyPatched ESP/ESP-FE and
   filename**. Inspect the FOMOD and links; do not select the variant by guesswork.
4. Only if separately approved, evaluate **Better Books and Letters `68909`**
   (start with the 1K/512 option) and verify intended shared-page winners.
5. Ledger rows for each approved vendor mod (source URL, file id, archive SHA-256),
   matching Keeps queued at the *end* of the install per `docs/CURATION_POLICY.md`, a
   `CHANGELOG.md` entry naming this record, and a `py -3 audit/launch_verify.py`
   PASS before any of it is called done.
6. `py -3 audit/file_conflicts.py` afterwards to confirm the only BCS/BBL
   collision is the expected four files.

**If instead the vendor ESP route is chosen:** CRC `0x32587221` is on LOOT's
**clean** list, not an instruction to QuickAutoClean. Evaluate **`59669` file `746258`**
(`Patch - BCS USSEP.esp`, ESL, 465 BOOK + 3 CELL + 3 REFR forwards) and
**file `247720`** (`Patch - BCS CRF.esp`, ESL, 2 records). That patch is v1.8,
updated 2026-04-27 — actively maintained. It restores USSEP's text and stats
while keeping BCS's models. Contrary to the original audit's claim, its author
explicitly restores mostly vanilla names, with separate conventions for series,
notes and journals. Select naming behavior deliberately and check the current
USSEP/CRF versions; do not mix original-plugin patches into the SkyPatched route.

The 2K/4K `178820` downloads are not direct fits for the 1K small-clutter ceiling;
neither source age nor endorsement count establishes visual quality. `155254`
(PBR) remains an optional material upgrade: its separate Original and Lost
Library downloads need a dependency/JSON inspection, working TruePBR and
PGPatcher output. Presence of `Shaders/Features/TruePBR.ini` alone did not prove
the feature was enabled at runtime. *[unverified]*

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
