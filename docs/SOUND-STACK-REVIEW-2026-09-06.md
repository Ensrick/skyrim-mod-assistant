# Sound stack review — 2026-09-06

Research only. No installs, Keep/Skip changes, game launch, INI edits or changes
to the main ecosystem survey. **Recommendation: retain the current sound
foundation. Sounds of Skyrim Complete remains maintained and usable, but is
an optional ambience choice, not a missing essential or an automatic upgrade.**
The owner already likes the sound; add more only for a specific audible gap.

## What is actually active

Re-read `records/installed-mods.json` and MO2's live `Default/modlist.txt` and
`plugins.txt`, rather than treating the August survey as inventory.

| Installed component | Version / Nexus file | Role |
|---|---|---|
| [Audio Overhaul for Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/12466) | 4.1.3 / 387525 | Broad mix, propagation/reverb, footsteps, weapons, magic, creatures and environmental ambience |
| [Immersive Sounds Compendium](https://www.nexusmods.com/skyrimspecialedition/mods/523) | 3.0 / 221873 | More varied action/item/equipment/impact sounds; installed default selections |
| [AOS–ISC Integration](https://www.nexusmods.com/skyrimspecialedition/mods/36761) | 1.1.0 / 280412 | Reconciles those two sound packages |
| [Sound Record Distributor](https://www.nexusmods.com/skyrimspecialedition/mods/77815) | File labelled 1.5.4 / 794646 | Runtime distribution framework; not itself an ambience library |

All four MO2 folders are enabled. The three plugins are active in the intended
AOS → ISC → integration sequence. SRD's mod-page/binary version is 1.5.3 while
the installed release file is labelled 1.5.4; the [intake audit](../records/sound-stack-2026-08-30.md)
already records that distinction. Current official API metadata agrees with
the installed AOS/ISC/integration versions. AOS already includes regional
ambience: our forests and dungeons are not still using only vanilla sound.

No Sounds of Skyrim Complete, Regional Sounds Expansion, Reverb Interior
Sounds Expansion, Acoustic Space Improvement Fixes, Wildwood Echoes or Murder
of Songbirds main package appears in the active profile. Moonpath's music and
weather fixes are active, but are location-specific, not a broad sound overhaul.
Music selection and the earlier custom-music plan are separate from ambience.

## What the survey actually says

The [August 30 survey](ECOSYSTEM-SURVEY-2026-08-30.md) recorded AOS 16/19,
SRD 15/19, ISC 11/19 and ASIF 8/19. Those are historical sample counts, not
today's installed inventory or a popularity ranking.

For this review, re-fetched the same 20 public exports used by the
[September 6 census](REQUESTED-SLOTS-CENSUS-2026-09-06.md), retaining its same
15 eligible 2025–26 MO2 exports and nine 2026-only exports. Read-only reuse of
`audit/survey_requested_slots.py`'s fetch/text validation with an in-memory
audio filter; no script or survey changed. Main enabled folder names were
manually separated from patches, disabled choices and mere mentions. The
joined-modlist hashes matched the existing census. Numbers below are source
modlist line numbers, making presence auditable; a dash means no recognized
main folder, not proof no bundled or renamed content exists.

| Export | SRD | AOS | ISC | RSE | RISE | ASIF | SoS Complete | Wildwood | Songbirds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| [LoreRim](https://loadorderlibrary.com/lists/lorerim) | 403 | 405 | 406 | 409 | 408 | — | — | 436 | 437 |
| [Nordic Souls](https://loadorderlibrary.com/lists/nordic-souls) | 192 | 193 | 194 | 210 | 197 | 196 | — | 213 | 212 |
| [Nolvus](https://loadorderlibrary.com/lists/nolvus-awakening) | 313 | 315 | 316 | 318 | 319 | 314 | — | 339 | 340 |
| [Wunduniik](https://loadorderlibrary.com/lists/wunduniik-chapter-v) | 96 | 431 | 440 | 449 | 453 | 426 | — | 467 | 445 |
| [Apostasy](https://loadorderlibrary.com/lists/apostasy) | 39 | 460 | 461 | 466 | 467 | 465 | — | 503 | 487 |
| [Anvil](https://loadorderlibrary.com/lists/anvil) | 36 | 261 | — | — | — | — | — | — | 274 |
| [CSVO](https://loadorderlibrary.com/lists/csvo) | 145 | 159 | 160 | 162 | 163 | 164 | — | — | — |
| [Septimus](https://loadorderlibrary.com/lists/septimus) | 31 | — | — | 109 | 110 | — | — | — | — |
| [Tuxborn](https://loadorderlibrary.com/lists/tuxborn) | 179 | 366 | — | — | — | — | — | 369 | 368 |
| [Eldergleam 4.0.2](https://loadorderlibrary.com/lists/eldergleam-a-next-gen-modlist-4-0-2) | 163 | 385 | 390 | 388 | 387 | 386 | 411 | 434 | 435 |
| [Mages & Vikings](https://loadorderlibrary.com/lists/mages-vikings) | 3594 | 3595 | — | — | — | — | — | 3609 | 3608 |
| [Kirbyking's](https://loadorderlibrary.com/lists/kirbykings-modlist-3) | 212 | 356 | 357 | 362 | 359 | 360 | — | — | — |
| [Invicta](https://loadorderlibrary.com/lists/invicta-12) | 120 | 125 | 126 | 129 | 130 | 131 | — | 143 | 144 |
| [Vagabond Remastered](https://loadorderlibrary.com/lists/vagabond-remastered) | 38 | 384 | 385 | 389 | 390 | 388 | — | 393 | 420 |
| [Tempus](https://loadorderlibrary.com/lists/tempus-maledictum) | 103 | 417 | 424 | — | — | — | — | — | — |
| **Total / 15** | **15** | **14** | **11** | **11** | **11** | **9** | **1** | **10** | **11** |
| **2026-only / 9** | **9** | **8** | **7** | **8** | **8** | **6** | **0** | **6** | **6** |

RSE = Regional Sounds Expansion; RISE = Reverb Interior Sounds Expansion;
ASIF = Acoustic Space Improvement Fixes. ASIF counts include named SkyPatcher
main versions, not their add-ons. ISC excludes SRDified, Cleaned Plugin and
Creation Club patch-only entries. Both integration routes remain represented:
ten exports name the AOS–ISC integration family, while Eldergleam names Redux.

GTS and ElderTeej are plugin-only and excluded from absence counts; NGVO,
Winds of the North and Wildlander exports predate 2025. Wildlander's 2022
export contains SoS Complete, but is not evidence of its current release.
Some mirrors, especially Nolvus/Wunduniik, are third-party snapshots, and list
families are not independent. The [current official Nolvus manifest](https://www.nolvus.net/awakening)
independently lists AOS/ISC integration, RSE, RISE and several Clofas ambience
modules; its pinned RSE 2.0 does not supersede the author's current 2.1.0.
This supports a modular trend, **not a finding that SoS is broken or obsolete**.

## Sounds of Skyrim Complete specifically

[SoS Complete](https://www.nexusmods.com/skyrimspecialedition/mods/8286) is
**3.1.0**, main file **668992**, uploaded **2025-09-24**, confirmed by the
official API and [files page](https://www.nexusmods.com/skyrimspecialedition/mods/8286?tab=files).
It combines Civilization, Wilds and Dungeons: additional contextual animal,
settlement, dungeon and weather sounds, not a replacement for weapon impacts
or the whole existing mix. Release 3.1.0 replaced the looping interior-rain
sound, made assets loose, and added an **Azurite Weathers III patch**. MCM
allows individual sounds to be disabled. Its Light choice removes several
intrusive crowd/insect/novelty sounds; that is a taste-oriented reduction,
not a statement that the full version is defective.

Our concern is overlap and integration, not age: SoS changes cells/regions
while Lux and location overhauls also touch them. [Lux's changelog](https://www.nexusmods.com/skyrimspecialedition/mods/43158)
documents SoS compatibility work; current patches live in the
[official patch hub](https://www.nexusmods.com/skyrimspecialedition/mods/113002).
An Azurite patch plus a Lux patch is not automatically a verified combined
winner. Inspect exact current records before adoption. Additional background
crowds or animals may also imply activity with no corresponding visible NPC.
No archive or patch was downloaded/audited in this review.

## More targeted options — alternatives, not installation decisions

| Candidate | Current release | What it would add / important limit |
|---|---|---|
| [Regional Sounds Expansion](https://www.nexusmods.com/skyrimspecialedition/mods/77829) | 2.1.0, 2025-05-23 | Updated AOS-derived regional ambience through SRD, with timing/volume adjustments and a wind slider. Compatible by design with AOS; partly an alternative mix of shared territory, not wholly new coverage. |
| [Reverb Interior Sounds Expansion](https://www.nexusmods.com/skyrimspecialedition/mods/77947) | 1.5.0, 2023-01-31 | Room-response tuning and weather-aware interior ambience. Works with AOS and dynamically integrates RSE. SRD supports regional sounds; Engine Fixes preserves sliders. Old release date alone is not a defect. |
| [Acoustic Space Improvement Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/78992) | 1.3.3, 2025-05-21 | Corrects inconsistent room acoustic assignments. Potentially the most focused improvement, if those inconsistencies are noticeable. See route caveat below. |
| [Wildwood Echoes](https://www.nexusmods.com/skyrimspecialedition/mods/112008) | 1.4, 2026-04-14 | Forest wildlife, wood/branch and environmental sounds through SRD. Latest revision adjusts density/volume and removes the old Quieter Trees choice. |
| [Murder of Songbirds](https://www.nexusmods.com/skyrimspecialedition/mods/111766) | 1.2, 2024-04-09 | Region/time-specific bird and bat ambience; installer offers weather gating and WAV/XWM choices. Does not add visible birds or change actual wildlife spawning. |

**ASIF correction to the older intake:** a Lux plugin patch is not mandatory
for every modern route. [Current files](https://www.nexusmods.com/skyrimspecialedition/mods/78992?tab=files)
include SkyPatcher file **629457**, with a stripped plugin and no CELL edits;
the author says its separate plugin-version patches are unnecessary. However,
the author recommends plugin/manual patching, file **629459**, for interiors
whose layout/materials have been substantially rebuilt. Runtime injection
avoids record overwrite disputes, but cannot determine whether an acoustic
assignment suits a newly designed room. Our city/interior plan still matters.

SRD reduces record conflicts; it does not guarantee that stacking every
ambience library sounds good, avoids duplicate events, or has zero audio/CPU
cost. AOS's instruction to remove obsolete **AOS weather patches** prevents
duplicate regional sounds; it is not permission to omit a SoS-specific
Azurite compatibility patch. [AOS installation guidance](https://www.nexusmods.com/skyrimspecialedition/mods/12466).

## Recommended next step and verification boundary

Keep the present sound design unchanged unless the owner identifies a missing
effect. If more is desired, audition one focused candidate at a time: ASIF for
room consistency, RISE for indoor weather, or selected regional/wildlife
ambience for wilderness variety. Do not add SoS plus every modular alternative
as a blanket improvement. SoS Light remains a reasonable trial if its
particular samples are preferred; that requires explicit approval and patch
inspection first.

The existing [#89](https://github.com/Ensrick/skyrim-mod-assistant/issues/89)
remains open for previously measured AOS/ISC reversions of some USSEP
non-audio fields. It deserves a current winner-level recheck before expanding
the stack; SoS does not fix that issue. This review did not rerun those record
comparisons or verify sound playback, SRD runtime logs, performance, or all
new-land coverage. The owner's positive playtest is welcome evidence of taste,
not a substitute for those technical checks.
