# Solitude city/interior cell and patch matrix

Status: **research complete; no installation or curation authority.** This is a
2026-08-30 archive/plugin audit of a possible Solitude architecture. Nothing in
this record authorizes enabling a mod in `Default`, changing Keep/Skip, or
shipping another author's plugin.

**Superseding tree decision, 2026-08-30:** full Nature of the Wild Lands 3.14
is installed with the normal Grand Solitude and Solitude Docks patches. Nordic
Cut is not installed and every Nordic-specific branch below is historical
comparison evidence only.

## Executive result

`Grand Solitude 1.3.1` and `Solitude Docks Updated 3.2c` are a technically
credible pair. Their current official combination patch is an ESL-flagged
five-record terrain/cell reconciliation, and the two base plugins do not
override the same NAVM records. They are not, however, independent: both edit
Tamriel cells `00009278`, `00009279`, and `0000927A`, with the patch also
reconciling `LAND` and `WRLD` data.

The name **Snazzy** describes two different layers that must not be conflated:

- `Snazzy Solitude AIO 2.3` is only six house interiors: Bryling, Erikur,
  Evette San/Jala/Addvar (the Mid-Houses module), and Vittoria Vici. It does
  **not** redesign Castle Dour, the Temple, the Bards College, Fletcher, or the
  Solitude blacksmith. Its AIO and separated plugins therefore have no shared
  REFR or NAVM override with Grand's reconstructed interiors.
- `Snazzy Furniture and Clutter Overhaul 3` (`SFCO3`, BOS edition) is a
  furniture/clutter replacement system. The current SFCO3 patch hub has exact
  add-on patches for Grand, Docks, Snazzy Solitude AIO, and every separated
  Snazzy Solitude module. The legacy `Grand Solitude - SFCO patch.esp` in the
  Grand hub targets the old non-BOS `Snazzy Furniture and Clutter
  Overhaul.esp`; it is not the current SFCO3 solution.

The remaining unresolved work is small in record count but important in
semantics: a late owned ESP-FE should reconcile Grand+Docks with Water for ENB,
Lux Orbis, the selected tree patch, and final CELL/WRLD winners. No ordinary
record-forwarding patch should replace an authored NAVM merge.

## Audit basis

Current Nexus metadata was queried through the authenticated Nexus API and the
following current archives were opened without installation:

| Component | Audited current file |
|---|---|
| Grand Solitude | 1.3.1, Nexus file `796423` (2026-08-28) |
| Grand Solitude Patch Collection | 1.5, file `797296` (2026-08-30) |
| Solitude Docks Updated | 3.2c, file `511162` |
| Snazzy Solitude AIO | 2.3, file `760311` |
| Snazzy Interiors Patch Collection | 2.8, file `786655` |
| SFCO3 Patch Collection | 1.22, file `797290` (2026-08-29) |
| Lux Patch Hub | 7.1, file `695703` |
| Lux Orbis Patch Hub | 4.7 main plus current Grand file `796261` and Docks file `742495` |
| Nordic Cut + patch collection | 1.2.2, files `789072` and `789073` |
| JK's Solitude Outskirts Patch Collection | 1.13.1, file `741878` |
| eFPS Official Patch Hub | 1.7a, file `273650`; Grand eFPS patch 1.1, file `679953` |

The plugins were parsed directly for masters, flags, record signatures, FormIDs,
cell ownership, placed-reference counts, and NAVM counts. Spatial proximity of
new exterior references was checked where two plugins did not override the
same reference. This establishes the conflict surface; it does not replace a
camera-route, door-link, NPC pathing, lighting, or waterline test in game.

## Physical footprint

### Grand Solitude

Grand is a full ESP with 30,291 records, 25,465 new records, 4,826 overrides,
and 112 NAVM records. It changes both the closed `SolitudeWorldspace`
(`00037EDF`) and Tamriel around the gate, arch, and northern approach.

Its major reconstructed vanilla interiors are:

| Vanilla cell | Grand scope | Grand NAVM records in cell |
|---|---:|---:|
| `000169FE` Fletcher | 1,056 placed refs | 3 |
| `00016A02` Temple of the Divines | 3,995 refs | 2 |
| `00016A0C` Bards College | 1,472 refs | 1 |
| `000213A0` Castle Dour | 5,201 refs | 2 |
| `00037EE0` Solitude Blacksmith | 1,277 refs | 2 |

Grand has only narrow, mostly door/link/header touches in Blue Palace
`00016A04`, Castle Dour Dungeon `00056E88`, Thalmor Headquarters `00071FFE`,
and the Emperor's Tower `00019454`; those are not Grand interior redesigns.

Grand's named new playable interiors are House of Clan Frost-Will, Squall Gate
Tower, House of Clan Elk-Heart, House of Clan Snowfire, Castle Dour Q-Store,
Horst's House, Manserand Manor, Exquisite Pastries, Erik's House, Ulrecht House,
Banking Quarters, A New Page, Unvald Family House, Pepilium Family House, The
Squall Gate Inn, Giltrius House, Lundgeir's House, Storm Gate Barracks, and Bank
of Haafingar. The plugin also contains clearly named author test/storage cells;
those are not user-facing locations.

The heaviest in-city exterior cells are `00037EE2`, `00037EE4` through
`00037EEA`, and persistent cell `00037EF0`. Its Tamriel approach footprint
includes `00009216`, `00009236`-`38`, `00009257`-`5A`, `00009277`-`7C`, and
`00009298`-`9E`, among neighboring header cells.

### Solitude Docks Updated

Docks is a full ESP with 8,839 records, 8,690 new records, 149 overrides, and
72 NAVM records. Its physical layout is in Tamriel below and around the arch,
not in the closed Solitude worldspace. Its edited exterior cells are chiefly:

`000091D3`, `000091F4`, `00009214`-`16`, `00009235`-`36`, `00009256`-`57`,
`00009278`-`7A`, `0000929A`-`9C`, `000092BB`-`BD`, and `000092DB`-`DD`.

It adds 25 named interiors: Dockside Barracks, Ivan's House, Moldy Storage
Room, Captain Rodmar's House, Ruins of Fort Bulwark, Green-Beard Brothers
House, Salt Spray Shanty, Myrna's Revenge, a second Dockside Barracks cell,
Bread and Batter, Mara's Mercy Chapel, Cliff Cottage, Ondiel's Warehouse,
Ethlam's House, Ondiel's House, Sea Side Farm, Marsh View, Shadow Side, The
Fo'c's'le, Break Water Farm, Ghost Sea Trading Company, Marsh View Cellar,
Under the Arch Smithy, Gatehouse Barracks, and Old Nan's House.

### Exact Grand + Docks contact surface

The bases have common overrides for Tamriel `WRLD 0000003C`, `NAVI 00012FB4`,
Solitude location `LCTN 00018A5A`, `LAND 000A027A`, the persistent cell, and
eight CELL headers. They have **no common NAVM FormID**.

The current `Grand Solitude - Solitude Docks patch.esp` is ESL-flagged and has
only five overrides: `WRLD 0000003C`, `CELL 00009278`, `CELL 00009279`, `CELL
0000927A`, and `LAND 000A027A`. Those three cells are therefore the exact
terrain/header seam that must never be resolved by simply choosing either base
plugin as the final winner.

### Snazzy Solitude AIO 2.3

| Module | Interior cells | Exterior contact | NAVM |
|---|---|---|---:|
| Bryling's House | `00016A0B` | `00037EE1`; persistent/header touches in `37EE6`, `37EF0` | 1 |
| Erikur's House | `00016A09` | `00037EE3`; persistent/header touches in `37EE6`, `37EF0` | 1 |
| Mid-Houses | Evette San `00016A08`, Jala `00016A05`, Addvar `00016A0D` | persistent `00037EF0` | 3 |
| Vittoria Vici's House | `00016A07` | wedding/house exterior `00037EEA`; headers `37EE6`, `37EF0` | 1 |
| AIO | all six houses above | combined exterior/header footprint | 6 |

Grand and each Snazzy module share only WRLD/NAVI/CELL-header records; they do
not share a placed reference or NAVM override. A coordinate audit found no new
Grand/Snazzy references within 200 units for Bryling, Erikur, or Mid-Houses.
Vittoria had seven Grand laundry-line references 132-198 units from Snazzy's
wedding-area additions. That is not proof of clipping, but it makes Vittoria's
exterior the one mandatory visual inspection point. Separated modules are
useful for testing and rollback; the AIO is not technically a Castle/Temple
conflict.

## Combination and module matrix

| Layer or optional module | Current exact support | What still needs ownership or visual validation |
|---|---|---|
| Grand + Docks | `Grand Solitude - Solitude Docks patch.esp` from Grand patch hub 1.5 | Keep the exact terrain patch; inspect arch, switchback, gate, and harbor waterline. No custom NAVM merge is indicated by shared FormIDs. |
| SFCO3 BOS + Grand | `SFCO3-Addons - Grand Solitude patch.esp` plus `zeSFCO3-GrandSolitude-BOS_SWAP.ini` in SFCO3 hub 1.22 | Use this current SFCO3 route, not Grand's legacy SFCO patch. |
| SFCO3 BOS + Docks | `SFCO3-Addons - Solitude Docks Updated patch.esp` | Six Docks interiors are explicitly covered. |
| SFCO3 BOS + Snazzy Solitude | Exact AIO and exact separated-module add-on patches and BOS swap INIs | Match the patch to AIO **or** separated choice; never both. |
| Snazzy AIO/separated + Grand | No named Grand patch, but no shared REFR/NAVM override | Final CELL/WRLD/NAVI semantic review; visual check at Vittoria exterior. No CK navmesh work is presently evidenced. |
| Lux interiors + Grand | `Lux - Grand Solitude patch.esp` in Lux hub 7.1; 2,331 records, 24 Grand interiors, no NAVM | Required if Lux remains the interior-lighting choice. |
| Lux interiors + Docks | `Lux - Solitude Docks patch.esp`; 729 records, all 25 Docks interiors, no NAVM | Its exterior CELL headers include `9278/9279`; retain Lux's added refs but let an owned final semantic patch reconcile headers with Grand+Docks. |
| Lux interiors + Snazzy | Exact AIO and separated Lux patches in Snazzy hub 2.8 | Pick the exact AIO/separated variant. Grand/Docks interiors are disjoint, so a universal triple interior patch is unnecessary. |
| Lux Orbis + Grand | Current `Lux Orbis - Grand Solitude patch.esp`, file `796261`; ESL, 182 records, 17 exterior cells, no NAVM | This is now official exact support. It overlaps the Grand+Docks patch at `WRLD` and `CELL 9279`; a tiny owned semantic final patch is safer than blind load-order winning. |
| Lux Orbis + Docks | Current `Lux Orbis - Solitude Docks Updated patch.esp`, file `742495`; ESL, 36 records, 10 cells, no NAVM | It overlaps Grand+Docks at `WRLD`, `9278`, and `9279`; preserve Orbis light refs and combination terrain/header data. |
| Water for ENB 2.21 | No exact Grand/Docks combination patch found | Grand has 11 and Docks 15 WRLD/CELL overlaps with Water, but no shared NAVM. Final owned ESP-FE should preserve Water's water type/height/flags while preserving the city stack's terrain, region, location, visibility, and lighting semantics. Test water seams under the arch and along both quays. |
| Nature of the Wild Lands + Nordic Cut | Nordic Cut 1.2.2 patch collection includes its own `Grand Solitude - Nature of the Wild Lands patch.esp` with Grand, NotWL, and Nordic Cut masters | Use the Nordic-specific patch, not the normal Grand+NotWL patch. Docks has no named Nordic Cut patch; it has one true placed-reference overlap with Nordic Cut plus headers, requiring an owned winner and route inspection. |
| AI Overhaul 1.9.5 + Grand | Exact `Grand Solitude - AI Overhaul patch.esp`; 40 records, packages/refs/cells, no NAVM | The patch expects the full AI Overhaul/USSEP patch route. AI Overhaul Lite is a different architecture and must not inherit this plan automatically. |
| AI Overhaul + Snazzy | Exact AIO and separated patches; AIO patch's substantive Solitude change is tiny | Select only if full AI Overhaul is selected. Docks' custom residents use Docks packages; no current Docks-specific AI Overhaul patch was found. |
| 3DNPC + Grand | Exact `Grand Solitude - 3DNPC patch.esp`; exact `Grand Solitude - JKs Bards College + 3DNPC patch.esp` also exists | No substantive REFR/NAVM conflict was found with the six Snazzy houses or Docks. 3DNPC remains a permanent-save content decision, not a prerequisite for this architecture. |
| eFPS + Grand | `Grand Solitude - eFPS patch.esp` 1.1 disables problematic eFPS planes and forwards compatible ones; it is not a custom optimized Grand occlusion build | Grand's FOMOD explicitly forbids DynDOLOD Resources' **Solitude Occlusion Planes** option. Start validation without Docks' eFPS planes; a final optimized solution needs CK occlusion placement and camera-route testing. |
| eFPS + Docks | `Occ_Skyrim-Solitude_Docks_Patch.esp` from official eFPS hub | There is no exact Grand+Docks+eFPS triple. Grand eFPS and Docks eFPS share headers but not REFR FormIDs; Docks planes can still occlude Grand geometry spatially. Record compatibility alone cannot certify them. |
| JK's Skyrim inside Solitude + Grand | Exact `Grand Solitude - JKs Skyrim patch.esp`; 1,010 records, 977 refs, 16 NAVM | This is a genuine authored layout/navmesh merge, not a decor add-on. Use the exact patch or omit the JK city layer; do not reproduce it with forwarding. |
| JK's Bards College + Grand | Exact `Grand Solitude - JKs Bards College patch.esp`; 1,702 records, 3 NAVM | Exact 3DNPC, AI, and SFCO3 combinations exist. The freshly uploaded file discussed below appears to be a Lux triple, but its Nexus metadata/payload mismatch blocks automatic trust. |
| JK's Blue Palace 2.0.2 + Grand | Grand shares only WRLD/NAVI/three CELL headers with JK Blue Palace, with no shared REFR/NAVM; Grand itself adds only one Blue Palace ref | No explicit Grand patch found. Do a final header/NAVI audit and test both Blue Palace doors and the Pelagius route before acceptance. |
| JK's Solitude Outskirts + Grand + Docks | Current Outskirts hub has authored Grand and Docks core patches plus exact five-record `JKs Solitude Outskirts - Solitude Docks Updated + Grand Solitude patch.esp` | The core Grand patch carries 7 NAVM; the core Docks patch carries 50 NAVM. These exact authored merges are mandatory if Outskirts is selected. The five-record triple is only the final terrain/header consistency layer. |
| JK Outskirts + Lux/Orbis | Current Outskirts hub has Docks combination patches for Lux, Lux Via, and Lux Orbis | These do not eliminate the need for the Grand+Docks consistency winner. Inspect the complete selected master chain, not filenames in isolation. |
| Ryn's Farms 2.0 | No combination patch indicated by exact records | Grand/Ryn and Docks/Ryn share only generic persistent WRLD/CELL/NAVI headers; no LAND, NAVM, or REFR record, and no new references were within 500 units. Ryn's Farms is not a material Solitude-stack collision. Audit other Ryn modules by location. |

## The current Lux Orbis hub packaging defect

The Nexus entry/file `796263` is currently titled **Lux Orbis - Grand Solitude
JK's Skyrim patch**. The downloaded archive does not contain such a plugin. Its
sole payload is `Lux - Grand Solitude + JKs Bards College patch.esp`, with
masters for Grand, JK's Bards College, Lux, both base Lux/Grand/JK patches, and
the Grand+JK Bards merge. It is an ESL-flagged 204-record Bards College lighting
patch with no NAVM.

That payload may be exactly the missing Lux interior triple, but the public file
identity is wrong. Do not install it automatically as either an Orbis+JK's
Skyrim patch or a trusted Lux+Bards patch until the author corrects or explains
the upload. File `796261` (Grand+Orbis) and `742495` (Docks+Orbis) have payloads
matching their names and masters.

## Patch ownership boundary

An owned final compatibility plugin can safely handle the remaining override
semantics when it contains no new layout or NAVM:

1. carry forward the exact Grand+Docks `LAND`, `CELL`, `WRLD`, location, and
   region result;
2. preserve Water for ENB water fields;
3. preserve Lux/Lux Orbis light and cell fields appropriate to the selected
   Community Shaders stack;
4. preserve the Nordic Cut/NotWL placed-reference decision;
5. forward AI/3DNPC packages and enable states only from their exact patches;
6. remain ESP-FE if no compacting-unsafe new records are introduced.

Creation Kit work is required only if validation reveals topology, door-link,
occlusion, or geometry problems that cannot be represented as semantic record
merges. It is mandatory for authoring/re-finalizing NAVM or custom occlusion
planes. For any selected JK layout, treat the upstream combination plugin's
NAVM and NAVI data as authoritative, then validate final door triangles and
pathing rather than reconstructing them in an owned xEdit patch.

## Acceptance routes after a user selection

- Walk from Katla's Farm through every lower-docks road, under the arch, up the
  switchback, through the main gate, and around both city wall directions.
- Send followers and non-player residents through doors and across every patch
  seam; test civil-war and execution crowd routes.
- Visit all six Snazzy houses; inspect Vittoria's wedding exterior and every
  Grand-added laundry line nearby.
- Test Castle Dour, Temple, Fletcher, blacksmith, Bards College, Blue Palace,
  Pelagius wing, and the Emperor's Tower after any selective JK module.
- Sweep the harbor at dawn, midday, dusk, and night for Orbis bulbs, Lux
  exterior leakage, water seams, z-fighting, and disappearing geometry.
- Test from the arch, docks, Blue Palace approach, and both wall roads with
  eFPS/occlusion off before attempting a custom occlusion build.
- Run xEdit error checks and deleted-reference/navmesh checks on the final
  winning order, then regenerate grass/LOD/DynDOLOD only after geometry is
  frozen.

## Primary/current sources

- [Grand Solitude](https://www.nexusmods.com/skyrimspecialedition/mods/157506)
  and [Grand Solitude Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/157450)
- [Solitude Docks Updated](https://www.nexusmods.com/skyrimspecialedition/mods/33777)
- [Snazzy Solitude AIO](https://www.nexusmods.com/skyrimspecialedition/mods/147618),
  [Snazzy Interiors Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/91604),
  and [SFCO3 patch collection](https://www.nexusmods.com/skyrimspecialedition/mods/114482)
- [Lux Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/113002)
  and [Lux Orbis Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/114169)
- [JK's Solitude Outskirts Patch Collection](https://www.nexusmods.com/skyrimspecialedition/mods/103927)
- [Nature of the Wild Lands](https://www.nexusmods.com/skyrimspecialedition/mods/63604)
  and [Nordic Cut](https://www.nexusmods.com/skyrimspecialedition/mods/161936)
- [Water for ENB](https://www.nexusmods.com/skyrimspecialedition/mods/37061)
- [eFPS Official Patch Hub](https://www.nexusmods.com/skyrimspecialedition/mods/54998)
- [AI Overhaul SSE](https://www.nexusmods.com/skyrimspecialedition/mods/21654)
- [xEdit issue #1265: door/navmesh triangle checking limitations](https://github.com/TES5Edit/TES5Edit/issues/1265)
  and [xEdit 4.1.6 development notes](https://github.com/TES5Edit/TES5Edit/blob/dev-4.1.6/whatsnew.md)
