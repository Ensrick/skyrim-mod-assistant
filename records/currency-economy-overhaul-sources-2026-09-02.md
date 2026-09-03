# Currency and economy overhaul: source notes

**Research date:** 2026-09-02.

This file records the evidence boundary for
`currency-economy-overhaul-research-2026-09-02.md`. Author pages and source
repositories are treated as primary evidence for current features; local plugin
inspection is treated as primary evidence for the active load order and record
contents. Community lists are used only as adoption/risk signals.

| Source | Evidence used | Confidence / limitation |
|---|---|---|
| [C.O.I.N. Nexus page](https://www.nexusmods.com/skyrimspecialedition/mods/51439) | v3.5.3, 2026-06-18; currency families, documented exchange values, BOS/CDF integration, Bruma support, pickup conversion, permissions | High for released documentation; released ESP property still needs inspection because one source default differs |
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
| [M.I.N.T. Dram BOS config](https://github.com/Currency-Series/M.I.N.T./blob/main/_release/01%20MorrowindMint/MorrowindUsesDrams_SWAP.ini) | Published distribution includes bare `|60` fields; BOS 3.5.0 leaves chance at its 100% default unless the field contains `chance` | High for published-source behavior; verify whether the Nexus archive differs before patching |
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

These counts came from an ad hoc Python 3.13 TES4 binary parser using `struct`
and `zlib`, invoked from PowerShell against the active plugins. The exact command
remains in the private task transcript, but no standalone script or
machine-readable output was retained. The counts are adequate static research
evidence, not yet a reproducible release artifact. Before generating the patch,
rerun them through a reviewed, committed audit utility and retain its versioned
JSON output beside the load-order/archive manifest.

The profile already contains SkyPatcher 7.0.3, Base Object Swapper 3.5.0,
Keyword Item Distributor, powerofthree's Papyrus Extender/Tweaks, Address
Library, and SkyUI.

It does not presently contain CDF, Currency Swapper, C.O.I.N., M.I.N.T., ECE,
Notification Filter, Dynamic Dialogue Replacer, or the other ECE-only
requirements identified in the main report.

## Unresolved evidence gaps

- Inspect the released C.O.I.N. ESP property values, rather than assuming the
  website or repository default wins.
- Audit the apparent C.O.I.N. source array-compaction condition before relying
  on that path.
- Disassemble and trace compiled reward/service logic for Beyond Reach,
  Moonpath, Gray Cowl, and VIGILANT.
- Inspect ECE's packaged scripts/plugin and prove value preservation, reset
  behavior, and every Currency Swapper transaction path in runtime.
- Recheck all versions, permissions, and licenses on the actual download date;
  this ecosystem changed several times during the weeks before the audit.
