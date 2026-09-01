# New-lands survey - 2026-08-31

Research only. Nothing downloaded, nothing installed. The question asked was
narrow: **what else adds a place that actually exists in Elder Scrolls
lore/geography**, the way Bruma does, and is it polished (or polishable)?

Falskaar is the calibration point for a rejection: an invented island, dropped
2026-08-22 on writing, empty worldspace, and a dead companion ecosystem
(`memory/reference_skyrim_ecosystem_currency_filter.md`). So "invented island"
is a disqualifier on the canonicity axis, not a demerit to be traded away.

## Method and evidence classes

| Class | Source | Read on |
|---|---|---|
| Nexus metadata (author, version, last update, endorsements, unique downloads, main-file size) | official Nexus v1 API, `games/skyrimspecialedition/mods/{id}.json` and `/files.json` | 2026-08-31 |
| Adoption | the same 19 Load Order Library exports the ecosystem survey used, re-read through `api.loadorderlibrary.com/v1/lists/{slug}`; a mod counts only if it appears on an **enabled** modlist/plugins line | 2026-08-31 |
| Mod behaviour (worldspace, requirements, compatibility) | the author's own Nexus description text | 2026-08-31 |
| Release state of unreleased projects | project sites and press | 2026-08-31 |

**What is NOT verified here.** Nothing was downloaded, so exact worldspace
counts, plugin/ESL flags, record footprints, and NPC-leak numbers of the kind we
have for VIGILANT (3 of 1,755) are `[unverified]` for every candidate. Those are
install-time audit work (`audit/worldspace.py`, `audit/guildleak.py`,
`audit/inspect_mod.py`), not desk research.

## 1. Already installed - not re-pitched

Bruma (10917), Wyrmstooth (45565), Beyond Reach (3008), Moonpath (4341), Gray
Cowl 10th (141327), VIGILANT (11849). Wyrmstooth and VIGILANT are quest content
in and beside Skyrim rather than provinces.

## 2. Canonical-place candidates that are downloadable now

Ordered by how well the place matches the Bruma standard.

| Mod | Nexus | Author | Version / last update | Endorse | Unique DL | Main file | Canonical place? |
|---|---|---|---|---|---|---|---|
| Journey to Baan Malur and Morrowind | 114518 | pancake | i1.1.9b / 2025-05-29 | 1,091 | 159,070 | 734 MB | **Partly.** Morrowind province, Julan-Shar region - a Tamriel Rebuilt / Tamriel Data construct, not an Arena or TES III place. Blacklight (its overhaul add-on) and the Velothi Mountains are canon |
| Morrowind - Vvardenfell Return - West Gash | 158653 | Demoklesz | v0.3.3 / 2026-03-26 | 216 | 2,921 | 1,402 MB | **Yes.** Gnisis, Ald Velothi, Khuul, Caldera, Ald'ruhn, Maar Gan, Bal Isra, Yasammidan, Ashalmawia - all TES III places |
| Silgrad - The Great Valley of Morrowind | 141362 | Caenraes | v2 / 2025-12-11 | 232 | 4,366 | 3,387 MB | **Yes.** Silgrad Tower is an Arena city-state south of Blacklight |
| Vvardenfell The New South | 129761 | Angelio | v1 / 2024-09-29 | 167 | 3,594 | 403 MB | **Yes** (Vvardenfell / mainland cities) |
| Blacklight - Baan Malur Overhaul | 166401 | Angelio | v1.0 / 2025-12-14 | 75 | 1,739 | 0.5 MB | **Yes.** Renames and rebuilds Baan Malur as Blacklight, Morrowind's post-Red-Year capital |
| Fat Skyrim | 107721 | vykaz | 1.3.3 / 2026-05-26 | 806 | 35,906 | 1,698 MB | **Region yes, settlements no.** Silgrad Pass (S. Morrowind), Jade Valley (Jerall Mountains), Sulmaad Valley (Hammerfell), plus Orsinium and High Rock stubs |
| Rigmor of Cyrodiil | 21566 | Rigmor | v1.0 / **2021-09-19** | 8,492 | 117,435 | 2,031 MB | **Yes.** Cyrodiil, County Bruma outward |
| Summerset Isle | 72004 | yourenotsupposedtobeinhere | v1.522 / 2024-07-17 | 2,577 | 69,665 | 2,393 MB | **Yes.** Summerset, the Altmer homeland |
| Isle of Artaeum (SSE) | 57934 | Pyromanius | v1.7 / **2022-09-11** | 961 | 57,795 | 809 MB | **Yes.** The Psijic Order's island |
| Isle of Artaeum - Season 3 | 33150 | Pyromanius | v2.0 / **2021-08-12** | 465 | 5,988 | 299 MB | as above (separate, earlier release) |
| Systres Islands | 43629 | ELAF (from PresidentMendes) | v1 / **2023-12-17** | 142 | 1,684 | 939 MB | **Yes.** Systres archipelago, High Rock (ESO High Isle) |
| Nyhus and the Border of Cyrodiil | 4016 | JoopvanDie | v9 / 2026-07-22 | 3,703 | 69,370 | 260 MB | **Province yes, town no.** No UESP lore entry for Nyhus |
| Haafstad and the Border of High Rock | 4017 | JoopvanDie | v9.8.1 / 2026-08-29 | 3,512 | 65,453 | 547 MB | **Province yes.** Haafstad, Kirkmore, Lordship Pinemarch are invented |
| Folkstead and the Border of Hammerfell | 4018 | JoopvanDie | v5.5.2 / 2026-08-19 | 3,640 | 83,220 | 582 MB | **Province yes**, Folkstead invented |
| Solstheim Expansion - Dunmer Style Additions | 180133 | WangJuhua | v1.1 / 2026-06-20 | 51 | 661 | 461 MB | **Yes**, but it is a settlement expansion of vanilla Solstheim, not a new land |
| GLEN-MORIL SE | 32998 | Vicn | **0.96.80b pre-alpha** / 2026-08-09 | 7,431 | 332,575 | 1,140 MB | **Name yes, geography no.** Glenmoril Coven is canon; the worldspaces are Vicn's otherworlds |
| Unslaad SE | 11789 | Vicn | v3.0.6 / 2026-07-14 | 9,472 | 623,348 | 1,166 MB | **Thematic.** Dragon/half-dragon realms, same idiom as the installed VIGILANT |

### Invented places - judged and rejected on the stated axis

Listed so they are visibly judged, not overlooked. Several are excellent mods;
they simply are not what was asked for.

| Mod | Nexus | Why it fails the axis | Note |
|---|---|---|---|
| Project AHO | 15996 | Sadrith Kegran, an invented Telvanni enclave | The best-polished "land" on Nexus: 20,702 endorsements, 6/19 adoption, fully voiced |
| The Forgotten City | 1179 | invented Dwemer city | 47,386 endorsements, 7/19. A self-contained dungeon-city, not a land |
| Midwood Isle | 28120 | invented island | 6,777 endorsements, active (2026-07-10), 2/19 |
| Land of Vominheim | 31472 | invented island | 4,731 endorsements, active (2026-07-21), 0/19 |
| Darkend | 10423 | invented island | last updated 2018-04-24 |
| Sirenroot | evgSIRENROOT | invented cavern | 9/19 - the highest adoption of any recent content mod, and still invented |
| Chanterelle, Clockwork, Maelstrom, Undeath | - | invented | Undeath 8/19 is realm content, not a land |
| Falskaar | 2057 | invented island | already rejected 2026-08-22 |

## 3. Adoption across the 19 surveyed modlists

Enabled-line presence in the same LOL exports the ecosystem survey used
(lorerim, nordic-souls, gts, nolvus-awakening, wunduniik-chapter-v, apostasy,
anvil, csvo, septimus, tuxborn, wildlander, tempus-maledictum, elderteej,
eldergleam, winds-of-the-north, ngvo, constellations, legends-of-the-frost,
skyrim-modding-essentials).

| Mod | Count | Lists |
|---|---|---|
| VIGILANT *(installed)* | 12/19 | lorerim, nordic-souls, gts, nolvus, wunduniik, apostasy, septimus, tuxborn, wildlander, tempus, elderteej, constellations |
| Gray Cowl *(installed)* | 11/19 | lorerim, nordic-souls, gts, nolvus, wunduniik, septimus, tuxborn, tempus, elderteej, eldergleam, constellations |
| Wyrmstooth *(installed)* | 10/19 | lorerim, nordic-souls, gts, nolvus, apostasy, septimus, tuxborn, tempus, elderteej, winds-of-the-north |
| Sirenroot | 9/19 | lorerim, nordic-souls, gts, nolvus, wunduniik, apostasy, tuxborn, tempus, constellations |
| Bruma *(installed)* | 8/19 | lorerim, nordic-souls, gts, nolvus, septimus, tuxborn, tempus, constellations |
| The Forgotten City | 7/19 | lorerim, nordic-souls, gts, nolvus, tuxborn, tempus, elderteej |
| Project AHO | 6/19 | gts, nolvus, septimus, tuxborn, tempus, elderteej |
| **Unslaad** | 5/19 | nordic-souls, nolvus, apostasy, tuxborn, tempus |
| Beyond Reach *(installed)* | 4/19 | nolvus, wunduniik, tuxborn, tempus |
| Moonpath *(installed)* | 4/19 | nolvus, septimus, tuxborn, elderteej |
| **Glenmoril** | 3/19 | wunduniik, tuxborn, tempus |
| Falskaar *(rejected)* | 3/19 | nolvus, tuxborn, elderteej |
| Midwood Isle | 2/19 | nolvus, tuxborn |
| **Journey to Baan Malur** | 1/19 | lorerim - and with a full support stack: LOD file, Baan Malur Landscape Overhaul (undeleted), FWMF paper map, JK's Raven Rock patch, `Journey to Baan Malur - Patched.esp` |
| Summerset Isle | 1/19 | wunduniik - and only inside a *DynDOLOD TexGen fix* entry, not as the mod itself |
| Vominheim, Nyhus, Folkstead, Haafstad, Fat Skyrim, West Gash, Silgrad, Rigmor, Shezarrine, Systres, Chanterelle | 0/19 | - |

Skyblivion appears twice (lorerim, nolvus) but only as armour assets
(`SKYBLIVION - Umbra`, `SkyblivionNecromancerRobes.esp`); it is not a modlist
entry for the project.

## 4. Per-candidate detail

### Journey to Baan Malur and Morrowind - 114518

- **Where it lives:** inside the **Solstheim worldspace** ("LOD is provided for
  the Solstheim worldspace, as this is where the new region is"), reached by
  ferry from Raven Rock or east of Windhelm through the Dwemer ruin of
  Kalbthurz. Roughly one Skyrim hold in size.
- **Quarantine:** the author's own list of vanilla changes is short - a boat in
  Raven Rock, and "There are no edits made to vanilla quests." Over 100 NPCs,
  all inside the new region. `[unverified]` until an install-time leak audit.
- **Voice:** every NPC is voiced, but from **repurposed vanilla voice lines**,
  not new performances - "sometimes it might not flow too well".
- **Quests:** five plus bounties, Morrowind-styled: **no map markers**, journal
  directions only. That is a taste call, not a defect.
- **Requirements:** `bBorderRegionsEnabled=0` (or Skyrim Borders Disabled 7011);
  FSMP **or** the page's No-SMP patch (**FSMP 4.1.1 is installed and enabled
  here**); Creation Club Ayleid textures from `Textures03.bsa`, or Ayleid Ruins
  Retexture (83802). No SKSE DLL, so **no 1.7.104 gate exposure**.
- **Compatibility:** native support for CoMAP and C.O.I.N. **Hard incompatible
  with Worldspace Transition Tweaks** (48889) - not installed here, and the
  ACMOS FOMOD record already notes WTT absent, so this costs nothing.
- **Our stack:** no Lux, ACMOS, or Water for ENB patch exists. ACMOS covers the
  Solstheim worldspace globally, so the region will sit on the Solstheim map
  without dedicated map coverage; the mod's own map support is an **FWMF** paper
  map (137315), which is the wrong family for our A Clear Map choice
  `[unverified whether it can be used standalone]`. DynDOLOD for Solstheim
  should be regenerated (the author says this is optional).
- **Family add-ons, all canonical-place, all early:** West Gash (158653),
  Silgrad (141362), Vvardenfell The New South (129761), Blacklight overhaul
  (166401), Baan Malur Landscape Overhaul (152707), Pryai (122335), Llethrin
  Fel (140281). They hang off this mod, so it is the gateway to the whole
  "Journey to Tamriel" Morrowind cluster.

### Fat Skyrim - 107721

- Expands the **Tamriel worldspace behind the border gates**: Silgrad Pass, Jade
  Valley, and Sulmaad Valley are "99% finished"; Northern Morrowind and Orsinium
  are landscape and dungeons only. About one hold per province when complete.
- Author is a Beyond Skyrim team member and states the mod does not compete with
  Beyond Skyrim - it fills the strip immediately beyond Skyrim's borders.
- **Not quarantined by construction:** the content is contiguous Skyrim
  worldspace, which is the opposite of the Vigilant model. On the other hand it
  is landscape-led rather than NPC-led, so the *quest and NPC* leak risk that
  the quarantine doctrine actually targets is low `[unverified]`.
- Self-declared WIP. Regions change between updates - a live save is exposed to
  landscape churn.
- No modlist adoption at all, and no patches for Lux, ACMOS, or Water for ENB.

### Rigmor of Cyrodiil - 21566

- Genuinely Cyrodiil, DLC-sized, 8,492 endorsements - but **frozen at v1.0 since
  2021-09-19** and **0/19 adoption**.
- Structurally the opposite of quarantined: it is a companion-escort story that
  begins in Bruma and drives long scripted sequences; it requires Rigmor of
  Bruma first. The author's documented stance on other mods running alongside is
  restrictive.
- Judgement: the place is right, the shape is wrong for a modlist that assigns
  one questline per character and prizes save-neutrality.

### Summerset Isle - 72004

- Canonical province, 2.4 GB, updated 2024-07-17.
- Documented user reports of exponential load and save-time growth, infinite
  loading screens when stacked with other large land mods, and users banned from
  the mod page for reporting it (Steam discussion threads).
- Gated behind Arch-Mage status, so it also conscripts the College questline.
- 1/19, and that single hit is a DynDOLOD/TexGen fix entry rather than the mod.

### JvD Border Trilogy - Nyhus 4016, Haafstad 4017, Folkstead 4018

- The most actively maintained canonical-*province* option: all three updated
  July-August 2026, ~3,500-3,700 endorsements each.
- But the settlements are invented (no UESP lore entries for Nyhus, Folkstead,
  Haafstad, Kirkmore, or Lordship Pinemarch), and the mods deliberately place
  content **inside Skyrim's own worldspace** - an island offshore northwest, a
  town south of Falkreath, towns northeast of Windhelm. That is the leak profile
  the quarantine preference exists to avoid.
- Voice acting is "real voices + **ElevenLabs**"; the author lists further AI
  voice work and dialogue rewriting as still-to-do.
- 0/19 across every surveyed list.

### Vicn's Glenmoril (32998) and Unslaad (11789)

- The strongest *stack fit* of anything here: same author as the installed
  VIGILANT, and **Lux Patch Hub officially patches Bruma, Wyrmstooth, Vigilant,
  Glenmoril, and Unslaad** (BASELINE, interior-lighting row) - the only
  candidates in this survey with first-party Lux coverage.
- Requirements are SKSE, SkyUI, PapyrusUtil 3.3+, Fuz Ro D-oh, with SSE Engine
  Fixes recommended. Installed here: SkyUI 6.11, PapyrusUtil 4.7, Engine Fixes
  7.0.21. **Fuz Ro D-oh (15109) is not installed** - that is the one gap, and it
  is a small SKSE plugin that would need the 1.7.104 gate.
- **Unslaad** is v3.0.6 and has an English voiced release by the Skyrim Voice
  Alliance (11896), plus an xVASynth pack (65959). 5/19 adoption.
- **Glenmoril** is still labelled **"Pre-Alpha (for tester)"** at 0.96.80b,
  ships Japanese natively (English translation 33146 required), and the page
  warns that an ESP/BSA version mismatch risks CTDs. 3/19 adoption.
- Canonicity: Glenmoril Coven is a real Skyrim location and Unslaad is
  dragon-lore, but neither depicts a mapped province. If Bruma is the standard,
  these are a different thing that happens to be good.

### Isle of Artaeum (57934) / Systres Islands (43629) / Solstheim Expansion (180133)

- Artaeum: the right place (Psijic island), 961 endorsements, but frozen since
  2022-09 and 0/19. Season 3 (33150) is a separate, older, smaller release.
- Systres: the right place (High Rock archipelago), but 142 endorsements, 1,684
  unique downloads, last touched 2023-12, and its own description advertises
  Monkey Island references and Witcher-derived creatures - a tone mismatch with
  this build.
- Solstheim Expansion: canonical, but published 2026-05-16 with 51 endorsements
  and 661 unique downloads. Too new to have any evidence either way, and it is a
  settlement expansion rather than a land.

## 5. Not released - report, do not plan around

| Project | Actual state 2026-08-31 |
|---|---|
| Beyond Skyrim: Cyrodiil (beyond Bruma), Hammerfell, High Rock, Elsweyr, Argonia, Morrowind | In development. The project FAQ states none are close to done and there are no release dates. Bruma remains the only released module |
| Beyond Skyrim: Roscrea | In development, furthest along of the small provinces; running on 10-15 core contributors; will release complete, no pre-release |
| Beyond Skyrim: Atmora | On hold roughly 1-2 years, team redirected to Roscrea, largely back to concept art |
| Skyblivion | Officially delayed out of 2025; targeting some point in **2026**. Imperial City is the largest remaining blocker |
| Skywind | No release date, no launch window; late-stage production, 100+ volunteers |
| Tamriel Rebuilt | Morrowind-engine project. Not applicable to this build - relevant only because Baan Malur's region name comes from it |
| Yneslea, Thras, Pyandonea, Yokuda | Nothing downloadable found |

Beyond Skyrim's shipped non-province supplement does exist: **Wares of Tamriel**
(31519, v1.5.3 / 2026-07-08, 9,261 endorsements, 624,967 unique downloads, 208
MB) distributes province goods to Skyrim merchants. It is not a land, and it
injects into vanilla space by design.

## 6. Ranked shortlist

1. **Journey to Baan Malur and Morrowind (114518)** - the only canonical-province
   land shipping now with real evidence behind it: 159k unique downloads, LoreRim
   ships it with a five-piece support stack, actively maintained, no DLL, author
   states no vanilla quest edits. *Polish cost:* one INI line for border regions,
   a CC-texture or retexture dependency, DynDOLOD regen for Solstheim, and a map
   answer (its FWMF paper map is the wrong family for our ACMOS/A Clear Map). Its
   dialogue is stitched from vanilla voice lines - the real limit.
2. **Unslaad (11789)** - the highest-confidence *install*: stable v3.0.6, English
   voiced, first-party Lux patch, 5/19 adoption, same quarantined idiom as the
   VIGILANT we already run. *Polish cost:* add Fuz Ro D-oh through the 1.7.104
   gate; pick voiced vs xVASynth. **Fails the canonical-place axis** - this is a
   "you liked Vigilant" pick, not a "Bruma is a real place" pick.
3. **Fat Skyrim (107721)** - canonical border strips of four provinces, active
   (2026-05), landscape-led so low script risk, and it answers the "what is
   behind the border gate" itch that Bruma opened. *Polish cost:* no patches for
   anything in our stack, no adoption anywhere, WIP landscape churn against a
   live save, 1.7 GB.
4. **West Gash Projekt (158653)**, as a Baan Malur add-on - the most
   unambiguously canonical geography in this entire survey (Gnisis, Ald'ruhn,
   Caldera, Khuul, Maar Gan). *Polish cost:* v0.3.3, 216 endorsements, 2,921
   unique downloads, and page text that suggests the writing will need the same
   read-through Falskaar failed. Watch it; do not build a character around it.
5. **Glenmoril (32998)** - only if Unslaad lands well. Lux-patched, 332k unique
   downloads, but a **pre-alpha** that needs a translation mod plus a synthesised
   voice pack, and its canonicity is a name rather than a place.
6. **Rigmor of Cyrodiil (21566)** - listed because the place is exactly right and
   the endorsement count is real. Everything else argues against: 2021-frozen,
   0/19, escort-companion structure, prerequisite chain, restrictive
   compatibility stance.

## 7. Canonical but not worth it yet

| Mod / project | Why not |
|---|---|
| Beyond Skyrim Cyrodiil / Hammerfell / Roscrea / Atmora / Morrowind / Elsweyr | Not released. Roscrea is closest; Atmora is nearly dormant |
| Skyblivion, Skywind | Not released; Skyblivion slipped out of 2025 into 2026, Skywind has no window |
| Summerset Isle (72004) | Documented load/save-time degradation and infinite-loading reports, author bans critics, Arch-Mage gate, 1/19 |
| JvD Border Trilogy (4016 / 4017 / 4018) | Canonical provinces but invented towns, ElevenLabs voices, self-declared WIP, 0/19, and content placed inside Skyrim's worldspace against the quarantine preference |
| Isle of Artaeum (57934, 33150) | Right place, frozen 2021-22, 0/19 |
| Systres Islands (43629) | Right place, 142 endorsements, frozen 2023, jokey content |
| Silgrad (141362), Vvardenfell The New South (129761), Blacklight overhaul (166401) | Right places, but 75-232 endorsements and under 4,400 unique downloads each; all ride on Baan Malur, so they are decisions to make *after* it, not instead of it |
| Solstheim Expansion (180133) | Published 2026-05, 51 endorsements. No evidence yet, and it is a settlement expansion |
| Beyond Skyrim - Wares of Tamriel (31519) | Excellent and current, but a merchant distributor, not a land, and vanilla-space by design |

## 8. Where taste decides, not quality

- **Unslaad and Glenmoril.** Both are good; neither depicts a mapped province.
  If "actual place in the lore" is the hard rule, they are out on principle
  despite being the best stack fit available.
- **Baan Malur's vanilla-voiceline dialogue and marker-less quests.** Deliberate
  Morrowind-style design. Either it reads as authentic or as unfinished.
- **Fat Skyrim's contiguous-worldspace model.** It trades quarantine for the
  feeling that Skyrim's borders are real. That is a preference about what a new
  land is for.
- **Invented settlements inside canonical provinces** (JvD trilogy, Fat Skyrim's
  valleys, Baan Malur itself). Bruma is a named Oblivion city; these are new
  towns in the right province. Only the user can say whether that clears the bar.

## Sources

Nexus Mods v1 API (per-mod JSON, read 2026-08-31) for every figure in the tables
above; Load Order Library v1 API exports for the adoption counts; author
descriptions on the linked Nexus pages for behaviour and requirements;
[Beyond Skyrim FAQ](https://wiki.beyondskyrim.org/wiki/FAQ),
[Beyond Skyrim: Cyrodiil](https://beyondskyrim.org/project/cyrodiil),
[Skyblivion delay announcement](https://skyblivion.com/dev_diary/delay-announcement/),
[Nexus Creation Mod Con 2026 news](https://www.nexusmods.com/news/15582) for
Roscrea and Atmora state;
[UESP Lore:Silgrad Tower](https://en.uesp.net/wiki/Lore:Silgrad_Tower),
[UESP Lore:Blacklight](https://en.uesp.net/wiki/Lore:Blacklight),
[UESP Tamriel Rebuilt:Julan-Shar](https://en.uesp.net/wiki/Tamriel_Rebuilt:Julan-Shar)
for place canonicity. Local evidence: `BASELINE.md` (worldspaces and quarantine
rows), `docs/ECOSYSTEM-SURVEY-2026-08-30.md`, `records/acmos-56367-2026-08-30.md`
(ACMOS worldspace coverage), `records/installed-mods.json` (FSMP, PapyrusUtil,
SkyUI, Engine Fixes present; Fuz Ro D-oh and Skyrim Borders Disabled absent).
