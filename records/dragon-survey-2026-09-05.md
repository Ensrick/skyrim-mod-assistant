# Dragon mods across the 19 surveyed lists (2026-09-05)

Answers "what dragon mods are common in our survey?" (asked 2026-09-05 while
reviewing Diverse Dragons Collection from an Ask Claude batch). Companion to
`docs/ECOSYSTEM-SURVEY-2026-08-30.md`, which has no dragons slot.

## Method

- The 19 Load Order Library exports named in the survey's source table were
  pulled through the public API on 2026-09-05 (`api.loadorderlibrary.com/v1/lists/<slug>`).
  Three exports carry only plugin names (Gate to Sovngarde and ElderTeej:
  `loadorder.txt`; Constellations: `loadorder.txt` + `plugins.txt`), so their
  counts rest on ESP filenames. The Wunduniik export is the Reloaded v1 beta,
  not the Wabbajack 7.3 build.
- Entries whose name or plugin matched a dragon keyword were classified per
  list by one agent each (species pack / AI-combat / visuals / fix /
  quest-story / unrelated), the top 28 canonical mods were identified on Nexus
  through the API, and a critic re-grepped every export to correct membership.
  Corrected counts are what appears below.
- Presence counts are "in the export at all" (enabled or not). DCA is
  disabled in Tuxborn.

## Adoption (3 lists or more)

| Mod | Nexus | Class | Lists | Where |
|---|---|---|---|---|
| Paarthurnax - Quest Expansion | 51711 | quest | 11/19 | LoreRim, Nordic Souls, GTS, Nolvus, Wunduniik, Apostasy, Septimus, Tuxborn, Wildlander, Tempus, Constellations |
| Simpler Dragon Targeting (TDM node config) | 81417 | QoL | 6/19 | LoreRim, Nordic Souls, Wunduniik, Apostasy, Anvil, NGVO |
| Dragon Breath VFX Edit (Kittytail) | 118431 | visuals | 6/19 | LoreRim, Nolvus, Wunduniik, Tuxborn, Tempus, NGVO |
| Vigilant's Molag Bal Dragon Retexture | 82040 | visuals (Vigilant only) | 6/19 | LoreRim, Nordic Souls, Nolvus, Wunduniik, Apostasy, Tempus |
| Dragonactorscript Infinite Loop Fix | 87940 | fix | 6/19 | Tuxborn, Tempus, Eldergleam, LotF, SME, Wunduniik |
| DCA - Dragon Combat Animations (OAR) | 123113 | combat anims | 5/19 | LoreRim, Wunduniik, Apostasy, Tuxborn (disabled), NGVO |
| Ryn's Dragon Mounds Collection | 85647 | world | 5/19 | LoreRim, Nordic Souls, Nolvus, Wunduniik, Apostasy |
| Dragons SE (4thUnknown replacer) | 132218 | visuals | 4/19 | LoreRim, Nordic Souls, Wunduniik, Anvil |
| GoT Dragons (KaienHash replacer) | 79252 | visuals | 4/19 | Nolvus, Apostasy, Eldergleam, NGVO |
| HotD Dragons (Xila replacer) | see page | visuals | 4/19 | Apostasy, Eldergleam, Nolvus (KSDO2 variants), ElderTeej (fix plugin) |
| Dragon War (Delta, SKSE DLL) | 51310 | AI overhaul | 4/19 | Nordic Souls, GTS, Apostasy, Winds of the North |
| Diplomatic Dragons | 70803 | pacing | 4/19 | LoreRim, Nordic Souls, Apostasy, Winds of the North |
| Dragon Hunting (SPID) | 99193 | loot/quest | 4/19 | LoreRim, Nordic Souls, Apostasy, Winds of the North |
| Distant Dragon Roars (SRD) | 112185 | audio | 4/19 | Nolvus, Wunduniik, Anvil, Tuxborn |
| Dragons Fall Down (SPID) | 56317 | death physics | 4/19 | Nolvus, Tempus, GTS, Wunduniik |
| Dragon Mounds - Better Collision | 112062 | fix | 4/19 | LoreRim, Apostasy, Anvil, NGVO |
| Cult of the World Eater | 83274 | Alduin balance | 4/19 | LoreRim, Nordic Souls, Tempus, GTS |
| Diverse Dragons Collection SE | 695 | species pack | 3/19 | Nolvus, Tempus, Eldergleam (LoreRim has only its Settings Loader) |
| Infinite Dragon Variants (SPID+RaceMenu) | 74983 | recolor | 3/19 | GTS, Tuxborn, Winds of the North |
| Immersive Dragons (skeleton) | 18957 | visuals | 3/19 | Tuxborn, Eldergleam, LotF |
| Shouting Provokes Dragons (SPID) | 112664 | AI tweak | 3/19 | Wunduniik, Apostasy, ElderTeej |
| Mount Anthor Dragon Fix | 38510 | fix | 3/19 | Apostasy, Anvil, SME |
| True Teacher Durnehviir | 44969 | fix | 3/19 | LoreRim, Nordic Souls, Winds of the North |
| HD Serpentine Dragon and Mesh Fix | see page | fix/visuals | 3/19 | Nordic Souls, Tempus, LotF |
| Broken Horn for Paarthurnax (Addons for Dragons SE) | see page | visuals | 3/19 | LoreRim, Anvil, Wunduniik |

Two-list mods worth knowing: Splendor - Dragon Variants (Tempus, Tuxborn),
Dynamic Random Dragons (Apostasy, WotN), Rustic Dragons (NGVO, Tuxborn),
Talkative Dragons (Nordic Souls, Wunduniik), Durnehviir Resurrected (Apostasy,
Tempus), Majestic Dragons (Anvil, Wunduniik), USSEP Frost and Fire Dragon
Correction (Apostasy, NGVO). Single-list only: KS Dragon Overhaul 2 and
Ultimate Dragons (Nolvus), Dragons Use Thu'um and Serio's Enhanced Dragons
(Tempus), Diverse 4thUnknown Dragons (LoreRim).

Absent from every export: Bellyaches New Dragon Species, Deadly Dragons (only
Requiem's own patch in Constellations), Elemental Dragons, Dragon Combat
Overhaul.

## What the ecosystem converges on

1. **Fixes and QoL**, not content: loop fix, mound collision, Anthor, TDM
   targeting, breath VFX. These are the only dragon rows above 5/19.
2. **One visual replacer per list**, mutually exclusive: Dragons SE (4),
   GoT (4), HotD (4), Rustic (2), Bellyaches HD (1). No shared winner.
3. **No AI or combat overhaul consensus**: Dragon War (4, the Simonrim lists),
   KSDO2 + Ultimate Dragons (Nolvus only), Dragons Use Thu'um (Tempus), DCA
   animations (5) are disjoint camps.
4. **Species packs are a minority**: DDC 3, Splendor 2, D4D 1, Dynamic Random
   Dragons 2. The lists that carry DDC are 2024-2025 exports; the 2026 lists
   (LoreRim, Nordic Souls, Wunduniik, Apostasy) do not.
5. **Paarthurnax - Quest Expansion is the one near-universal dragon-adjacent
   mod** (11/19). The Paarthurnax Dilemma is in 0/19; The Paarthurnax
   Resolution in 1/19 (LotF).

## Read for this build

- Diverse Dragons Collection SE (695, v2.1.3, 2017): 3/19 and falling. Its
  leveled-list injection runs through Papyrus at runtime (dirty uninstall).
  The 2026 lists that want variety use Dragons SE plus Diverse 4thUnknown
  Dragons (146462) via SkyPatcher instead. The survey does not support a
  species pack as a slot; it supports the fix layer plus one replacer.
- Fix layer to consider regardless of the dragon package decision:
  Dragonactorscript Infinite Loop Fix (87940), Dragon Mounds - Better
  Collision (112062), Mount Anthor Dragon Fix (38510), True Teacher Durnehviir
  (44969). All DLL-free.
- Paarthurnax: Quest Expansion (51711) is the ecosystem pick by a wide margin.

Raw pulls: `%TEMP%\claude\...\scratchpad\lol\*.json` (session-local, not
committed); the workflow run was wf_604b5c99-ea3 (48 agents).
