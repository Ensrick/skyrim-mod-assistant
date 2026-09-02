# Deferred decision register

Canonical register for delegated work that still needs either a user decision
or an implementation/promotion step. A completed agent report is not considered
delivered until its result appears here and has been surfaced to the user.

GitHub master tracker: [issue #62](https://github.com/Ensrick/skyrim-mod-assistant/issues/62).

Every item awaiting a decision is **Unreviewed** in the Nexus curator. Under
`docs/CURATION_POLICY.md`, Keep means installed and enabled now; Skip means
explicitly rejected. A favorable recommendation or future installation plan is
not a Keep decision.

## Ready for the user's decision

| Item | Evidence-backed recommendation | Decision still needed |
|---|---|---|
| Simple Hunting Overhaul butchering extension / issue #72 | SHO 1.16, its recommended Papyrus DAK 1.02, and exact Bruma support are installed and verified. SHO charges time only for pelt removal; meat remains immediately removable, and Simple Hunterborn does not repair that gap. Build a separate owned ESP-FE + event-driven Papyrus extension with a persistent once-per-carcass token; use a native Quick Loot pre-take adapter only if blocking transfer is required. Hunterborn 7900 is Skip. Optional carcass/animation additions remain unclassified. Full record: `records/simple-hunting-overhaul-95943-2026-08-30.md`. | Choose one combined field-dressing charge versus separate meat/skinning charges; automatic post-transfer charge versus explicit Butcher activation; meat-first visual treatment; the time/XP curve; and whether a processed carcass remains carryable. No custom extension has been implemented. |
| Modern cloak system / issue #95 | Hold installation. Keep FSMP 4.1.1. The preferred first asset audition is More Scarves 1.4.0 for current lowered hooded capes plus Bocksten 1.1 for ordinary cloth cloaks, with Pelts 'o' Plenty 4.3.1 as the optional regional fur expansion. Helmet Toggle 2 3.6.2 plus the new GPL DAV compatibility overlay is the credible player/follower hood-state path, but DAV needs a 1.7.104 foreground smoke. Seasonal Clothing Framework and WeatherBehaviorNG have strong NPC designs but their released DLLs predate Address Library format 5 and their source repositories are unlicensed; neither is deployable as shipped. ICE 1.0 (185408) was exact-archive audited on 2026-09-02 and also held: it contains 54 unrelated Solstheim overrides, relies on undeclared FLM configuration, lacks Survival warmth, permanently injects inventory items, and has a broken mannequin exclusion. Full records: `records/modern-cloak-system-research-2026-08-30.md` and `records/ice-immersive-conditional-effects-185408-audit-2026-09-02.md`. | Choose asset breadth; player/follower/generic-NPC automatic scope; generic-cloak enchantability; warmth tiers and NPC density; and whether to authorize a 1.7.104 Survival Control Panel port plus author-permission or a clean owned NPC weather framework. No cloak candidate was installed or curated. |
| Orc Strongholds AIO (150246) | **Hold.** v1.2.1 is a valid v1.71 ESP-FE today, but it has 4,099 records, 2,776 new temporary placed refs, 151 NAVM (59 new), and reaches local FormID `0xFFF`. Static NAVI/door-index checks pass, but every NAVM retained by the current public fix has an unchanged CRC; the May-July 2026 Atub routing reports remain unresolved. Alaxouche 1.4.2 is a same-name replacement main, not an overlay. It incorporates ZX/cleanup, but the old Lux Via LAND patch conflicts with its four newer terrain winners. USSEP, Lux Orbis, and Nordic Cut conflicts are headlessly patchable; DA06 routing/topology needs a disposable quest route and CK work if reproduced. Full record: `records/orc-strongholds-aio-150246-exact-audit-2026-08-29.md`. | Decide whether to accept the separately fetched replacement-vendor dependency model and authorize a disposable DA06/terrain test. Nothing was installed in `Default`. |
| City/interior direction | The historical matrix supports Grand Solitude + Solitude Docks Updated and the selected separated Snazzy houses. Full NotWL is now installed with the normal Grand Solitude and Docks placement patches; the matrix's Nordic-specific branch is obsolete. eFPS Docks planes should not enter the first stability pass. | Remaining city scope—JK city/Bards/Blue Palace/Outskirts modules—still needs a separate decision and route audit. Full historical matrix: `records/solitude-city-interior-cell-matrix-2026-08-30.md`. |
| Apparel Preview (185334) | Source port for runtime 1.7.104 is complete and validated, but enabling it alone exposes no useful feature. Show Player In Inventory (178689) is the likely companion and brings FLICK plus No Furniture Camera; its author forbids AI-authored ports. | Approve the published companion/dependencies for audit and installation, or leave Apparel Preview staged and inactive. |
| Interesting NPCs Party Banter (104014) | Base 3DNPC is now installed. Party Banter is a separate small ESP-FE adding rare conversations among specific 3DNPC followers—principally Amalee, Anum-La, Rumarin, Valgus, and Zora—when at least two travel together. It does not add banter for Varinia or arbitrary followers. Audio is spliced from original recordings and has no MCM/frequency control. | Keep/install for a multi-3DNPC-follower playthrough, audition first, or Skip. |
| Publican's Perch + Samples of Stools | Hold current releases. Publican 1.0.8 is a strong regional counter candidate but references four missing material/environment maps and has overly broad BOS options. Samples has a missing Pale material, a broken Cities Only condition, zero FURN object bounds, repeated meshes up to ~28.1K triangles, and five actual 4K maps. | Wait for author updates, authorize owned private repairs later, or choose a lighter fallback. |

## Approved design awaiting implementation follow-through

| Item | Required work |
|---|---|
| General compatibility patch / issue #47 | The approved 14-record override-only ESL must remain separate from the existing 559-record water patch, load after it, declare semantic Lux Orbis/Water/Bruma masters, regenerate against the then-current corrected sorted profile, and pass the recorded acceptance suite before promotion. |
| Cutting Room Floor 3.1.26 compatibility / issue #71 | Three exact official patches are installed. Build one separate owned ESP-FE to merge CRF's Dark Chasm XLCN with Water for ENB, CRF's WhiterunLocation arrays with NFF, three CRF/Lux location semantics, and CRF's Tasius condition with Skyrim Unbound. Validate the Hall of the Dead XLCN choice and the recorded CRF routes before a long save. Public distribution is blocked until CRF compatibility-patch permission is documented. Full record: `records/cutting-room-floor-3.1.26-compatibility-audit-2026-08-30.md`. |
| 3D trellises and market stalls | User selected Whiterun Simple 3D Wooden Trellis (178881) plus Rally's Market Stalls (81282) as the preferred pair, but they remain Unreviewed until installation is explicitly authorized and completed. The dense 42472 package is not selected. |

## Completed information result

| Item | Result |
|---|---|
| Believable Weapons retextures | Xavbio Silver Armor and Weapons Retexture SE 2.1.1 is directly compatible with Believable Weapons' silver sword and greatsword; no patch is needed. Believable's silver scabbards deliberately use steel texture paths. Full matrix: `records/believable-weapons-retexture-compatibility-2026-08-29.md`. |
| SSE Display Tweaks official migration | Official v0.5.25 is now the enabled immutable vendor runtime; the Ensrick config-only overlay remains enabled above it and the emergency DLL rebuild is disabled for rollback. All headless audits passed. |
| Skyking Signs - Bruma Patch | Official optional file 481004 is installed and enabled. Its ESL-flagged plugin makes one Snowstone Rest sign override and contains no scripts, cells, navmeshes, or new forms. |
| Solitude city/interior cell matrix | Exact current archive/plugin audit completed without installation or curation changes. Grand+Docks has an official five-record terrain patch and no shared NAVM FormID; Snazzy AIO is only six houses; SFCO3, Lux, Lux Orbis, AI Overhaul, 3DNPC, Nordic Cut, eFPS, Water, and JK/Ryn boundaries are classified. Current Lux Orbis file `796263` has a public-name/payload mismatch and must not be trusted automatically. Full record: `records/solitude-city-interior-cell-matrix-2026-08-30.md`. |
| Received-hit visual removals | Disable Screen Blood, No More Blur on Hit, and 3rd Person Camera Stagger Remover are installed as three immutable vendor mods. The owned Clear Damage View proposal is unnecessary locally; a public pack must fetch the restricted external files. |
| Interesting NPCs | Main 4.5 plus 4.54 update and the exact active-profile ILS, Skyrim Unbound prison, Cat-and-Mouse, Survival, NFF, Lux, and Skyking patches are installed. All headless audits pass. Party Banter remains a separate decision. |
| Skyland + NotWL/Ulvenwald tree foundation | User selected Skyland AIO 1K 4.32 as the broad base and full NotWL 3.14 as the placement authority. Ulvenwald 3.3.2 is now a lowest-priority asset-only dependency, with its plugin deliberately disabled; Tree Diversity Project 1.0.1 applies the official NotWL-base/Ulvenwald-swap BOS configuration. The active 14 swaps resolve all 13 models and 39 textures. Only NotWL's exact Bruma, Tundra Homestead, CRF, Lux Via, Grand Solitude, and Solitude Docks placement patches remain active. Nordic Cut and Mild Lands are absent. Static MO2, order, master, asset, and conflict audits pass. Runtime tree/frame-time/LOD routes remain on issue #29. Full records: `records/skyland-notwl-foundation-install-2026-08-30.md` and `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`. |
| Katana - Yoto Hatamonba (187162) | **Skip**, explicitly decided by the user after the competing-port audit. Nothing was installed. Apply the live curator change only through a fresh guarded compare-before-write state. |
| Scrambled Updates (189511) | **Skip**, explicitly decided by the user on 2026-08-30. It is an AI-assisted compatibility shim for the older Scrambled Bugs-family DLLs, not an official Scrambled Bugs update. Nexus 1.1.0 cannot operate on the current SKSE gate, while the unreleased workaround mutates vendor DLLs and raises a restart modal. The underlying rebuild/replacement work remains tracked separately on issue #87. Nothing was installed. The guarded curator relay refused the live mutation because the mod had not appeared in a page report that day; apply it after a fresh compare-before-write page state. |
| Varinia missing dialogue fragments and 3DNPC overlap | The omission is a proven packaging / generated-source defect, not intentionally disabled content. A private, non-distributable six-PEX overlay is compiled, bytecode-validated, installed, and enabled without changing the vendor files. All 17 Varinia/3DNPC shared chains were audited; current winners lose no material 3DNPC/USSEP value, so no compatibility ESL is warranted. Runtime dialogue-route testing remains. Full record: `records/varinia-private-fragment-fix-2026-08-30.md`. |

## Running now

| Item | Scope |
|---|---|
| None | All currently delegated work has completed. |

## Queued behind running work

| Item | Assigned after |
|---|---|
| None | All previously authorized queued research has either completed or is running. |

## Curation cursor

Codex's frozen newest-first cursor has completed Better fur - Fine clothes
(69240), which the user explicitly kept and installed. The next frozen-export
entry is Nexus SSE 72351 (`Forest Cat`); do not infer subsequent items from
Nexus ID order. Better fur - Merchant's hat (70589) was separately kept and
installed ahead of its cursor position and is already decided when reached.
Claude owns the oldest-first cursor.
Every decision is checked by game domain plus Nexus ID before either cursor
advances.
