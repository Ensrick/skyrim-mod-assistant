# Skyrim log triage and Bards College flicker audit

Date: 2026-09-05 CDT / 2026-09-06 UTC
Mode: read-only log, record, and asset inspection; no game launch, INI change,
profile write, or city-mod change.

## Result

The retained current-session logs contain two actionable runtime defects and one
missing morph asset. They do **not** identify the reported wall flicker near the
Bards College. A bounded record/asset inspection found no exact duplicate placed
building at the reported site. Grand Solitude deliberately places its Bards
College building and a small ground-overlay mesh at the same transform; that is
a plausible visual inspection point, not proof of the reported culprit.

## Evidence boundary

- Latest retained game session: 2026-09-05 20:03:53--21:02:44 CDT. The last
  LaunchProbe event is a quicksave in `CYRSerpentsTrail01` at 21:02:43, not a
  Solitude/Bards College reproduction.
- `Papyrus.0.log` ends at 21:02:43; `skee64.log` and `hdtSMP64.log` end at
  21:02:44. The corresponding `usvfs-2026-09-06_01-03-49.log` ends at
  21:02:47 with no matched error/warning/failure/denial/exception severity.
- Only four rotating Papyrus logs survive: September 3, 4, and two sessions on
  September 5. Most SKSE component logs are overwritten on each game start.
  Therefore absence from the retained logs is not proof that an older visual
  incident produced no diagnostic output.
- There is no CrashLogger crash artifact newer than 2026-09-01 18:43:46. This
  establishes only that no newer crash log was retained; LaunchProbe does not
  record a clean-exit event for the latest session.
- Load-order snapshot used for the city check:
  `profiles/Default/loadorder.txt` SHA-256
  `352A2A391F6727177B4B3931888C4AAFC11CF36AF4EE82011A593A335DF289B1`
  and `plugins.txt` SHA-256
  `7E8756DBA50184A2CD594DA91BB06BC3740E25865AA812646B395488C49E5663`.
  Their current mtime is 2026-09-05 21:19:55, after the approved Sons of Skyrim
  physics installation. The game-session logs above predate that installation,
  so the HDT warnings below are a pre-install baseline, not acceptance evidence.

## Ranked current findings

### 1. Exchange Currency Enhanced dereferences an empty crosshair target

This is current and reproducible in both September 5 Papyrus logs.
`Papyrus.0.log` contains 44 event groups between 20:07:18 and 20:59:32; each
group reports all three of these failures:

- `Cannot call GetBaseObject() on a None object`
- `Cannot call GetName() on a None object`
- assignment of `None` to temporary variable 27

Every stack points to
`EC_septimsScript.checkMintExchanger()` in `ec_septimsfunctions.psc` line 210.
`Papyrus.1.log` contains 11 more groups. The winning vendor source directly
chains
`(Game.GetCurrentCrosshairRef() as Actor).GetBaseObject().GetName()` without
checking either the cast or base form. A narrow null guard can preserve the two
recognized exchanger names while removing this log storm. Track under the
existing regional-currency issue #209 rather than treating it as a save or
engine fault.

The older `Papyrus.3.log` also contains 316
`HasKeywordString()`-on-`None` failures from
`EC_septimsScript.OnLocationChange()` line 180. This path is absent from the
three newer retained logs, but those sessions do not prove every location route
was revisited. Treat it as historical/route-bound and reproduce before changing
that separate code path.

### 2. Container Distribution Framework sees a negative count as unsigned

`ContainerDistributionFramework.log` line 1322 reports:

> Leveled-list count 4294967284 exceeds the engine limit; clamping to 32767

`4294967284` is the 32-bit unsigned representation of `-12`. The clamp can turn
an invalid/underflowed count into an enormous insertion, so this is actionable
even though the log does not identify the responsible form or rule. It is
tracked in issue #230. The reviewed PR #2 guard has since been installed and
passes its static/source-build checks; see
`records/source-builds/ensrick-cdf-nonpositive-counts-20260906.json`. The log
above predates that install, so runtime confirmation remains open and still
needs the original route or equivalent instrumented reproduction.

### 3. One active RaceMenu morph path has no winning TRI

`skee64.log` reports eight failures to load:

`meshes\armor\barbarianfurloin02\forswornarmor.tri`

No active loose winner exists at that path. The only similarly named retained
file is under `HIMBO Refits\meshes\clothes\forswornarmor\forswornarmor.tri`,
which is not the requested path. Expected impact is loss of morphing for the
affected barbarian/forsworn garment rather than a general engine failure. The
next useful check is the winning armor-addon model and its body-morph provider;
do not copy or rename the unrelated TRI by filename alone.

### 4. One stale RMB cloak rule targets a missing list, but owned policy repairs it

Current `SkyPatcher.log` reports that
`Cloaks - Dawnguard.esp|800` cannot be found. The source is line 104 of the
upstream `RMB SPCH - Cloaks of Skyrim` leveled-list INI. The owned
`Ensrick - Cloak Distribution Balance` rule explicitly redirects the relevant
core definition to the surviving `Cloaks - RMB SPCH.esp|984` list. This is a
real stale upstream diagnostic, but current evidence does not show a resulting
distribution hole. Cleanup is low priority and must preserve the owned route.

## Current noise that is not a demonstrated blocker

- Follower compatibility checkers probe absent optional plugins (Xelzaz,
  Redcap, Auri, Khash, Gore, Yazakh, Thogra, and Val Serano). Campfire similarly
  probes optional Frostfall, VR, and legacy SkyUI identities. These
  `IsPluginLoaded`/mod-check results are optional discovery, not missing-master
  failures.
- Repeated startup binding/property warnings from Creation Club and USSEP
  scripts are consistent with stale serialized properties or version drift.
  The retained logs contain no suspended-stack or stack-dump event. They merit
  symptom-led investigation, not a blanket script reinstall.
- RaceMenu logs one-per-race default-morph vertex mismatches and invalid body
  morph forms. No corresponding crash or reported visual symptom was retained.
- The current `hdtSMP64.log` has no `[E]` entries and many missing
  `HDT_Cloak`-bone warnings. It predates the approved Sons of Skyrim HDT overlay
  installed later that evening, so it cannot validate or refute that new layer.

## Historical crash context

Sixteen CrashLogger files survive from August 25 through September 1. Their
already-diagnosed clusters include old RaceMenu/IED failures, an August 27
Effects11 failure, an August 28 ScreenSpaceGI `E_INVALIDARG`, the resolved
August 29 Survival Mode Improved FormLoader problem, September 1 save/load
engine failures, and two later MenuPilot tooling-misuse crashes. See
`docs/CRASH-2026-08-31-DEEP-DIVE.md`, `records/hang-rootcause-2026-09-01.md`,
and `docs/MENUPILOT.md`. None is evidence for the current Bards College wall
flicker, and no retained crash artifact follows September 1 18:43.

## Bards College wall-flicker diagnosis

The current city stack includes Grand Solitude and its Grand/Docks, Lux,
Lux Orbis, Lux Via, Nature of the Wild Lands, SFCO3, and 3DNPC compatibility
layers. There is no active JK's Bards College or eFPS Bards module in the
audited order. The existing cell matrix correctly states that Grand rebuilds
interior cell `00016A0C` (1,472 placed references and one NAVM) and that visual
z-fighting cannot be certified from record conflicts alone.

The reported wording says "near" the Bards College, so the bounded exterior
inspection used Grand's Solitude worldspace rather than assuming the interior:

- Vanilla marker `02DCF7` is at approximately
  `(-55266.26, 105245.82, -8704.00)`.
- Grand persistent cell `00037EF0` places `AFC5BE`, base `AFC5BB`
  (`WSBardsCollege`), at
  `(-54401.883, 105002.04, -8512.0)`, Z rotation `0.7853982`.
- `AFC5BF`, base `AFC5BC` (`WSBardsCollegeTeather`), is nearby.
- `AFC5C0`, base `AFC5BD` (`WSBardsGroundGag`), shares the building's exact
  transform. Its NIF has three moss/grass shapes and appears to be an intentional
  ground/decal overlay.

A scan of 186 placed references within 2,600 game units found no same-base,
same-pose duplicate. Similar-looking forms `AF742C`/`AFC5C1` belong to Tamriel
cell `00009278`, not the simultaneously loaded Solitude worldspace, so they are
not duplicate live geometry at this site.

The three relevant winning NIFs resolve to Grand's BSA only:

| Model | Shapes | Abbreviated SHA-256 |
|---|---:|---|
| `WSBardsCollege.nif` | 31 | `7B14ED74...A9E8` |
| `WSBardsCollegeTeather.nif` | 6 | `36A9BFC9...AD8` |
| `WSBardsGroundGag.nif` | 3 | `341E2DBA...EF1` |

This narrows inspection to Grand forms `AFC5BE` and `AFC5C0`, but does not
establish either as faulty. Z-fighting and depth/LOD transitions commonly leave
no Papyrus or SKSE diagnostic, so the correct next evidence is a screenshot or
short video at the exact camera angle, plus the console-selected reference ID,
`player.getpos x/y/z`, time, weather, and whether the surface is the wall, roof, ground,
or moss overlay. Only then should an isolated profile A/B test or a mesh/record
fix be considered. Do not disable the city stack or edit the overlay based on
this audit alone. Issue #243 is the appropriate open investigation.

## Recommended next actions

1. Install no city change for the visual report yet; collect the exact Bards
   College reproduction evidence above.
2. Keep the bounded `checkMintExchanger()` null guard staged under the existing
   currency tracking issue until its compiled-artifact boundary is deterministic
   and proves all non-target functions unchanged; then test both named-exchanger
   outcomes before deployment.
3. Keep the CDF underflow on #230 and reproduce the original path against the
   now-installed, statically verified guard before runtime closure.
4. Trace the missing barbarian-fur-loin TRI from the winning ARMA/model records;
   do not substitute the unrelated HIMBO file by name.

## Isolated currency candidate produced by this audit

A source-only candidate was built under ignored
`records-work/log-triage-2026-09-06/currency-mint-null-guard/build-04`.
It was **not installed**. Its pinned inputs are the current ECE source
`5AAE6184...F690A` (12,220 bytes) and sole loose winning PEX
`C969F0B2...AC30` (12,629 bytes). The source diff is confined to
`checkMintExchanger()`: reset `MintExchanger`, guard both the Actor cast and
base Form, then preserve exact recognition of Eyrir and Galos Andrano.

Caprica 0.3.0 produced two byte-identical normalized candidates:
`EC_septimsFunctions.pex`, 13,075 bytes, SHA-256
`04C3E718CC4C7398A3C0A4F5BF8EFE4E2183695D948BE6C5CFD5C5919B13ED26`.
The nine compiler warnings are the pinned pre-existing eight unnecessary Bool
casts plus one unused `str` variable. Champollion lossless assembly inspection
confirms the false reset, both null branches, both names, and the true result.
Its high-level decompiler cannot reconstruct the unrelated pre-existing
`craftConversion` control flow, so no broader decompile-equivalence claim is
made. `receipt.json` records all input, tool, source, and output hashes.

This Caprica candidate is **not suitable for integration or deployment yet**.
The vendor PSC was reconstructed by Champollion, so unchanged source text outside
`checkMintExchanger()` does not by itself prove that recompiling the whole class
preserves unrelated bytecode, especially the control flow that the high-level
decompiler cannot reconstruct.

A second ignored prototype transplanted only the target function at the CK
assembler level. An unmodified disassemble/reassemble round trip preserved the
canonical instruction bodies of all 17 functions plus every variable and
property block. The target-only prototype preserved all 16 non-target function
bodies after label and case normalization and exactly matched the donor target
body. However, two assemblies from the identical PAS input were not
byte-deterministic: both were 12,672 bytes, but their SHA-256 values were
`0D37BC0E...C103` and `942EBD96...0422`, with 8,275 differing bytes beginning at
offset 366. That cannot satisfy the existing repeat-build oracle without adding
a new deterministic PEX rewriter or stronger semantic verifier, which is outside
this bounded repair.

Accordingly, no 0.2.7 replacement package was built, the clean 0.2.6 recipe and
package remain unchanged, and nothing was installed. The homologous unsafe
function in `EC_altCurrencyFunctions` was not exercised by the current log and
remains deliberately outside this one-script candidate. A future accepted build
still needs foreground tests for Eyrir and Galos Andrano across
Dialogue -> Barter/Crafting -> close, plus actor, non-actor, and empty-crosshair
menu opens; static inspection cannot prove nested-menu crosshair behavior.
