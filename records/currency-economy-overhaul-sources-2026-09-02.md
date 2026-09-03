# Currency and economy overhaul: source notes

**Research date:** 2026-09-02; currentness and implementation rechecked
2026-09-03.

This file records the evidence boundary for
`currency-economy-overhaul-research-2026-09-02.md`. Author pages and source
repositories are treated as primary evidence for current features; local plugin
inspection is treated as primary evidence for the active load order and record
contents. Community lists are used only as adoption/risk signals.

## Currentness gate (2026-09-03)

The authenticated Nexus API was queried again immediately before the final
integration build. Every selected primary file is still the newest applicable
SE/AE main file; VR variants were explicitly excluded:

| Component | Current applicable file |
|---|---|
| Address Library | v13, file `795954`, Skyrim 1.7.104 |
| C.O.I.N. | v3.5.3, file `765231` |
| M.I.N.T. | v1.0.6, file `756598` |
| Exchange Currency Enhanced | v4.1.1, file `758183` |
| Currency Swapper | v2.2.0, file `749947` |
| Container Distribution Framework | v3.1.0, file `754532` |
| Dynamic Dialogue Replacer | v1.4.1, file `748293` |
| Base Object Swapper | v3.5.0, file `794962` |
| Keyword Item Distributor | v4.1.0 SE/AE, file `794743` |
| SkyPatcher | v7.0.3 AE, file `796107` |
| powerofthree's Tweaks | v1.17.1, file `794717` |
| Notification Filter | v1.3.0 for 1.7.104, file `797725` |
| Inventory Interface Information Injector | v1.1.1 SE, file `796498` |
| SkyUI | v6.11, file `749043` |
| WiZkiD Ancient Imperial Septims | v1.3 Classic Gold, file `447129` |

The page-level `version` field for SkyUI still reports 6.9, but its sole current
main file is explicitly v6.11; the file record, not the stale page field, is the
installed authority. Beyond Skyrim - Bruma remains v1.6.4. Exchange Currency SE
remains v3.00/file `15057`; its newer upload is an unrelated Coins of Tamriel
optional patch, not a replacement main file.

| Source | Evidence used | Confidence / limitation |
|---|---|---|
| [C.O.I.N. Nexus page](https://www.nexusmods.com/skyrimspecialedition/mods/51439) | v3.5.3, 2026-06-18; currency families, documented exchange values, BOS/CDF integration, Bruma support, pickup conversion, permissions | High for released documentation; the released ESP was subsequently inspected and its effective Drakr rate is 0.15, matching source rather than the page's 0.25 |
| [C.O.I.N. source](https://github.com/Currency-Series/C.O.I.N/) | Papyrus conversion flow, current source defaults, configuration design | High for source-visible behavior; repository exposes no conventional license, so source-visible does not mean freely redistributable |
| [M.I.N.T. Nexus page](https://www.nexusmods.com/skyrimspecialedition/mods/178940) | v1.0.6, 2026-05-27; Dram/Ulfric/Sancar/Gibber modules, no-office/no-stall variants, requirements and permissions | High |
| [M.I.N.T. source](https://github.com/Currency-Series/M.I.N.T/) | Source-visible module and integration structure | High for code; third-party asset/voice permissions still govern redistribution |
| [Currency Swapper Nexus page](https://www.nexusmods.com/skyrimspecialedition/mods/127686) | v2.2.0, 2026-05-08; supported transaction paths, runtime requirement, state notes | High |
| [Currency Swapper repository](https://github.com/SeaSparrowOG/CurrencySwapper) | Current development source and current AGPL-3.0 license | High for `main`; it is not the same licensing boundary as the released tag |
| [Currency Swapper v2.2.0 license](https://raw.githubusercontent.com/SeaSparrowOG/CurrencySwapper/v2.2.0/LICENSE) | Apache-2.0 license at the released v2.2.0 tag | High; any fork must pin the exact base commit/tag and preserve the applicable license |
| [Currency Swapper current license](https://raw.githubusercontent.com/SeaSparrowOG/CurrencySwapper/main/LICENSE) | AGPL-3.0 license on current `main` | High as of research date; recheck before future fork work |
| [CommonLibSSE TESForm source](https://github.com/powerof3/CommonLibSSE/blob/master/include/RE/T/TESForm.h) | Engine wrapper identifies native gold by exact `0000000F` FormID | High; explains why a valuable custom MISC is not automatically legal tender |
| [Exchange Currency Enhanced Nexus page](https://www.nexusmods.com/skyrimspecialedition/mods/141884) | v4.1.1, 2026-05-31; denominations, weights, notes, purse randomization, regional modes, Bruma/Project AHO support, requirements, UI limitations, change history | High for author-documented behavior; no public source repository was identified, so runtime claims require black-box and plugin/script inspection |
| [Container Distribution Framework](https://www.nexusmods.com/skyrimspecialedition/mods/120152) | v3.1.0, 2026-05-20; runtime container distribution, reset behavior, random conditions | High |
| [Base Object Swapper](https://www.nexusmods.com/skyrimspecialedition/mods/60805) | Stable/random/location chance primitives and distribution syntax | High; exact rule precedence was also checked against the locally maintained source build |
| [DynDOLOD BOS documentation](https://dyndolod.info/Mods/Base-Object-Swapper) | Stable-chance compatibility for generated LOD and BOS version expectations | High |
| [M.I.N.T. - Borders of Coin](https://www.nexusmods.com/skyrimspecialedition/mods/187837) | v2.3.0 on 2026-09-02; whole-hold currency scope, feature claims, recent bug-fix history | Medium: extremely recent and rapidly changing; defer pending source/plugin/runtime audit |
| [M.I.N.T. exchange helper](https://github.com/Currency-Series/M.I.N.T./blob/main/Source/Scripts/DES_CurrencyFramework_Functions.psc) | Published rounding implementation uses `Math.Ceiling` in both exchange directions | High for published source; packaged PEX and profitable-loop behavior still require verification |
| [M.I.N.T. Dram BOS config](https://github.com/Currency-Series/M.I.N.T./blob/main/_release/01%20MorrowindMint/MorrowindUsesDrams_SWAP.ini) | Published distribution includes bare `|60` fields; BOS 3.5.0 leaves chance at its 100% default unless the field contains `chance` | High; the selected Nexus 1.0.6 archive was verified to contain the same four fields, and the installed owned override changes them to `chanceS(60)`; runtime sampling remains open |
| [Ruin Coins](https://www.nexusmods.com/skyrimspecialedition/mods/88859) | v1.5, 2025-06-07; narrower alternative scope and integrations | High for comparison; not recommended to combine with C.O.I.N. |
| [C.O.I.N. Treasury Exchange](https://www.nexusmods.com/skyrimspecialedition/mods/131682) | Current dedicated ancient-currency exchange option | High |
| [Grand Solitude - C.O.I.N. Bank Exchange](https://www.nexusmods.com/skyrimspecialedition/mods/157596) | v1.1.1, 2026-08-29; Bank of Haafingar integration and current M.I.N.T. record forwarding | High; still requires active-city-stack conflict audit |
| [Trade & Barter](https://www.nexusmods.com/skyrimspecialedition/mods/23081) | v2.2, 2025-01-24; barter, merchant-gold, faction/race/location price controls | High |
| [Evolving Economy](https://www.nexusmods.com/skyrimspecialedition/mods/149830) | v3.0.1; regional, seasonal, Civil War, and reputation price behavior; recent concurrency fixes | High for author documentation; runtime interaction with other price writers needs isolated tests |
| [Trade Routes](https://www.nexusmods.com/skyrimspecialedition/mods/12358) | 3.0 beta age, initialization and periodic update model, historical new-land scope | High for published behavior; old beta status makes it a weak stability-first candidate |
| [Nordic Souls 3 Currency](https://www.nexusmods.com/skyrimspecialedition/mods/180794) | Contemporary example combining Currency Swapper, ECE, C.O.I.N., M.I.N.T., purses, and exchange; author warning about wealth growth | Medium/community evidence only; its patch is specific to that list and must not be copied |

## Local primary evidence

The active MO2 profile at research time contains these relevant new-land
plugins:

- `arnima.esm` (Beyond Reach)
- `BSAssets.esm`, `BSHeartland.esm`, and `BS_DLC_patch.esp` (Bruma)
- `Wyrmstooth.esp`
- `moonpath.esp`
- `Gray Fox Cowl.esm`
- `Vigilant.esm`

The installed archive ledger pins the principal content versions used by the
scan:

| Content | Version | SHA-256 |
|---|---:|---|
| Beyond Reach | 4.8 | `e3b3d90dd363a185443d83c486115e4883e78cb636fc75f13f6c27817d510e1f` |
| Beyond Skyrim - Bruma | 1.6.4 | `006ef609f37dc172dbcbf82532ceeac5122a6bb3ba7368ec5f68d1b759538736` |
| Wyrmstooth | 1.20.3 | `e996175c2b49ab07cc86647cda837ff8930f39eb212f62affe749fad847e6c4d` |
| Moonpath to Elsweyr | 1.16.1 | `81fdbed9a79f13ae00808aab69130f4e2be7553771ad0b84c1590d527fa2eb31` |
| The Gray Cowl of Nocturnal | 1.51 | `08dbcd5ca06775a38544c78e347d6fecb81ee381cf4b429b242d056faed6407f` |
| VIGILANT | 1.8.2 | `7f44723212d5abac44075ccf959c9b42740f5d264bfa7238ab4535099eea9445` |

Direct plugin-record inspection established the counts and location tags used in
the main report:

- Bruma: native Ayleid currency assets, 95 placed Ayleid coins, 990 placed
  `Gold001`, with 19 of the latter in a Nordic-tagged site.
- Beyond Reach: 235 loose `Gold001`; no spendable native tender; five useful
  ancient-location tags.
- Wyrmstooth: 116 loose `Gold001`; 24 already in Nordic or Dwemer/Falmer-tagged
  locations.
- Moonpath: no directly placed `Gold001`, direct gold container/leveled-list
  entries, native currency, or relevant ruin keywords were found.
- Gray Cowl: 79 loose `Gold001`, five placed value-200 `AnotherWorldCoin`
  records, and some Dwemer-tagged locations.
- VIGILANT: no loose `Gold001`; gold appears in 17 leveled-list entries and two
  container/NPC entries; most visible coin heaps are non-lootable statics.
- Dragonborn/Solstheim: 174 loose `Gold001`, five container entries, four NPC
  entries, and 19 leveled-list entries.

The original counts came from an ad hoc Python 3.13 TES4 binary parser using
`struct` and `zlib`, invoked from PowerShell against the active plugins. A later
independent winning-record scan checked 2,486,676 major records and the exact
surviving Dragonborn pile routes, but that scan was also inline: no standalone
script or machine-readable output was retained. The results are adequate for
the current static integration gate and are summarized below, but are not yet a
reproducible public-release artifact. Before publishing the modpack, promote
the scanner into a reviewed utility and retain versioned JSON beside the
load-order/archive manifest.

The profile already contains SkyPatcher 7.0.3, Base Object Swapper 3.5.0,
Keyword Item Distributor, powerofthree's Papyrus Extender/Tweaks, Address
Library, and SkyUI.

As of the 2026-09-03 implementation pass, the profile contains CDF, Currency
Swapper, C.O.I.N., M.I.N.T., ECE, Notification Filter, Dynamic Dialogue
Replacer, I4, Exchange Currency SE and WiZkiD Ancient Imperial Septims. CDF,
Currency Swapper and Dynamic Dialogue Replacer require source-built 1.7.104
overlays because their released DLLs parse the obsolete Address Library format
2 rather than the installed format 5.

The final v0.2.4 release receipt is
`records/source-builds/ensrick-regional-currency-integration-0.2.4.json`.
Independent winning-record inspection parsed 2,486,676 major records across
342 active plugin inputs without an error and followed every surviving
Dragonborn silver/gold pile base through the enabled BOS rules. It found 92
winning references in five cells: Shadowfoot Sanctum stays Septim; Forgotten
Seasons Autumn's Bells becomes Nchuark; Beyond Reach's Nest stays Septim;
Fahlbtharz's five piles are all Nchuark (three are already forwarded by the ECE
C.O.I.N. patch); and Gyldenhul's eighty piles stay their authored silver/gold
Septim forms after the KID/BOS exception correction. No placed Dram-pile leak
was found in the current load order. This is static route proof; visual pickup
and transaction reconciliation remain part of the in-world matrix.

## Unresolved evidence gaps

- **Resolved 2026-09-03:** the released C.O.I.N. alias VMAD does not override
  `DES_CoinExchanger.autoExchange`; the compiled/source initializer and MCM
  reset both set it to true. It is per-save state, not an INI setting. The
  owned runtime-default quest therefore enforces false on initialization,
  player load, bounded delayed retries, and Journal-menu close.
- C.O.I.N.'s first-build compatibility-coin array path appears to retain a
  `coinsMaxIndex = -1` initialization defect. It does not block the selected
  known currencies, which are explicitly protected with `DES_NoExchange`, but
  remains a future compatibility risk.
- Disassemble and trace compiled reward/service logic for Beyond Reach,
  Moonpath, Gray Cowl, and VIGILANT.
- **Resolved statically 2026-09-03:** ECE's 1/25/100 denomination decomposition
  is exactly value-preserving, while the selected fixed regional transactions
  are exact with the exchange perk and intentionally lossy without it. Seventeen
  currency-to-ingot COBJ records create serious repeatable arbitrage and are
  disabled by owned overrides under issue #208. Runtime menu, reset, and
  rapid-reopen behavior still needs the disposable-save matrix.
- **Resolved for this build:** applicable Nexus file versions were rechecked on
  2026-09-03. Permissions and licenses are pinned in the integration manifest
  and source-build records; they must be rechecked again before a public pack
  release.
