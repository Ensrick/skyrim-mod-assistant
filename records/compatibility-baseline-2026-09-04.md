# LOOT compatibility baseline, 2026-09-04

Audit date: 2026-09-04
Runtime: Skyrim SE `1.7.104`; SKSE `2.3.1`; LOOT/libloot `0.29.6`;
LootCLI `1.8.0`
Profile: `mo2-instances\skyrim-se\profiles\Default`
Tracker: [issue #234](https://github.com/Ensrick/skyrim-mod-assistant/issues/234)
Profile mutation gate: [issue #102](https://github.com/Ensrick/skyrim-mod-assistant/issues/102)

## Disposition

This is a **read-only compatibility audit**. No mod was installed or reinstalled,
no plugin or mod was enabled or disabled, no sort was run, and the game was not
launched. Vendor archives and installed vendor files were not modified. The
protected `records/installed-mods.json` and `CHANGELOG.md` were not touched.
The concurrently regenerated `records/active-file-conflicts.*` and
`records/active-record-conflicts.*` receipts in the live checkout were read as
evidence and left untouched for their Fable owner.

The baseline has two real compatibility defects, two demonstrated LOOT false
positives, and three inactive optional plugins with intentionally absent
masters. The repository changes accompanying this record only prepare exact
future selections and ordering. Applying them to the profile remains blocked by
#102, and the landscape repair also has one genuine visual decision gate.

| Finding | Exact outcome | Action prepared here |
|---|---|---|
| AOS + EBT Lite | true defect | select AOS's own ESL patch; follow it with a private one-record ESPFE that restores ISC's assigned impact sound |
| LFfGM + CRF | true defect | select the current official ESL patch only as one transaction with a private current-winner merge |
| Engine Fixes Part 2 | false positive | no runtime change; LOOT tests an obsolete root filename, while native SKSE preload is proven |
| ENB Light / Particle Patch | false positive | no rename or extraction; the required archived asset is present under the current official basename |
| SLaWF Water, Lux Wraithguard, Lux Myrwatch | inactive intentional debt | deterministic future archive plans omit these wrong-variant patches |

## Frozen LOOT and profile receipt

The inspected `loot-report.json` is 77,316 bytes, modified
`2026-09-04T18:06:30Z`, and has SHA-256
`9184619559AD71F01BD88839A0A9816D8FA95B98D03291456D4AAE4A9683D65A`.
It contains 331 plugin rows and reports a 3,000 ms run. The corresponding
`plugins.txt` contains 269 listed plugins, 265 active, and has SHA-256
`912DCB2047092CFCA8DDF7A26FA95392CF0B4333F89E2B9B04E8B084DAF0B5BA`.

The local LOOT masterlist is the exact Git blob
[`17e71d0f54cbdaf04d2b01144c3d24be33bcab09`](https://github.com/loot/skyrimse/blob/e3c591ba9c041f23f407a0a0f87f72cc6325aa43/masterlist.yaml)
from commit
[`e3c591ba9c041f23f407a0a0f87f72cc6325aa43`](https://github.com/loot/skyrimse/commit/e3c591ba9c041f23f407a0a0f87f72cc6325aa43),
1,119,090 bytes, SHA-256
`95CAF8492923B77386FC725150D38C635A581A16BF0E546C3A44EEC85AFBE484`.

### Every global message

There are three informational messages and one warning:

1. `[Latest LOOT thread](https://loot.github.io/latest-thread/).`
2. `Your Skyrim Anniversary Edition is up-to-date.`
3. `Your SKSE Anniversary Edition is up-to-date.`
4. warning: Engine Fixes v7.0+ appears installed, but LOOT believes the
   `(Part 2) Engine Fixes 7.0 - skse64 Preloader ONLY` requirement is missing.

### Every plugin message

There are six informational messages and one warning:

| Plugin | Type | Message or effect |
|---|---|---|
| `SurvivalModeImproved.esp` | info | requires a new save and should not be used with an existing save |
| `Audio Overhaul Skyrim.esp` | info | read AOS compatibility notes |
| `Audio Overhaul Skyrim.esp` | info | EBT Lite is active but its included compatibility patch is not enabled |
| `Landscape Fixes For Grass Mods.esp` | info | CRF is active but its mod-page compatibility patch is not enabled |
| `RaceMenuPlugin.esp` | info | plugin is optional |
| `nwsFollowerFramework.esp` | info | recommends Fuz Ro D-oh - Silent Voice |
| `ENB Light.esp` | warning | appears to require Particle Patch resources |

LOOT also inventories three light plugins with missing masters. All three are
unstarred in `plugins.txt`, so none enters the runtime load order:

- `Landscape and Water Fixes - Patch - LFfGM - Water for ENB.esp` lacks
  `Water for ENB.esm`;
- `Lux - Wraithguard patch.esp` lacks `wraithguardvaultfixer.esp`; and
- `Lux - Myrwatch patch.esp` lacks `myrwatchhomefixer.esp`.

`Particle Patch.esp` is separately recognized as an active light master that
loads an archive and is clean at CRC `0x7F28E20B` under SSEEdit `4.1.5g`.

The relevant current profile lines are `Particle Patch.esp` 33, EBT Lite 34,
AOS 38, ISC 39, AOS/ISC Integration 40, LFfGM 50, CRF 55, the inactive SLaWF
Water patch 60, inactive Lux Wraithguard 213, inactive Lux Myrwatch 214, Water
for ENB Shades 255, and ENB Light 259.

## True defect 1: AOS 4.1.3, EBT Lite, and ISC

### Exact vendor payload

[Audio Overhaul for Skyrim 4.1.3](https://www.nexusmods.com/skyrimspecialedition/mods/12466)
Nexus file `387525` is retained as `downloads/12466-387525.7z`:

- 268,039,608 bytes;
- SHA-256
  `49C115916E610C7CD7B6B2227AAA43346151D7C60E47161E18190ADA20ACDBB8`;
- contains `00 Patch Plugins/AOS_EBT LITE Patch.esp`.

The included patch is 667 bytes, SHA-256
`5D7B82ADF707819B387C355605DD5BF3BB300F2F7F97FACCB1299B2F063B14B0`,
already ESL-flagged, and has exactly three masters:

1. `Skyrim.esm`;
2. `dD - Enhanced Blood Main LITE.esp`; and
3. `Audio Overhaul Skyrim.esp`.

It contains exactly two `IPCT` overrides, no new records, and no deleted
records:

- `0193B2:Skyrim.esm`, `WPNArrowVsFleshImpact`; and
- `0F0EB1:Skyrim.esm`, `WPNAxeLargeVsFleshDraugrImpact`.

Relevant installed plugin receipts are:

| Plugin | Bytes | SHA-256 | Records relevant to this result |
|---|---:|---|---|
| `dD - Enhanced Blood Main LITE.esp` | 18,235 | `55371AEC416743FE50A328F26036D55108C49B6DF6E4D0A783F154BED2AA5A77` | 21 IPCT among 59 records |
| `Audio Overhaul Skyrim.esp` | 665,294 | `9C1AA7391D10AED8FFAA678BB65FE23F2D0CFA0DC016F4A598EDD336173DE01F` | 221 IPCT among 2,491 records |
| `Immersive Sounds - Compendium.esp` | 1,048,415 | `5A1B36A7961D767C0937957767055DCF1BCB53B79B574003A40A66D382D3350E` | 574 IPCT among 3,050 records |
| `AOS_ISC_Integration.esp` | 309,912 | `337D2A7C508410B89F5385B030F07F836F272D38BFF7CBB9A00013A7810FF846` | 848 overrides: 820 SNDR, 21 IPDS, 7 SNCT; **zero IPCT** |

### Record-level result

For `0193B2`, EBT Lite supplies the larger blood decal and its texture set;
AOS currently wins with its smaller decal, alpha-blending flag, vanilla texture
set, and no second sound. The official patch correctly combines EBT's decal
dimensions and texture set with AOS's alpha blending and sound behavior. ISC
does not touch this record.

For `0F0EB1`, EBT Lite supplies the `20 x 50` decal (`8 x 25` minimum), while
AOS supplies alpha blending and AOS `Sound1` `061D33`. ISC currently wins and
keeps the AOS-sized decal but changes `Sound1` to
`08AB3B:Immersive Sounds - Compendium.esp`. The included AOS/EBT patch restores
the EBT dimensions but returns `Sound1` to AOS. The active AOS/ISC Integration
plugin cannot repair that loss because it does not override either IPCT.

The [AOS/ISC Integration](https://www.nexusmods.com/skyrimspecialedition/mods/36761)
vendor documentation explicitly assigns **Impacts** to ISC and puts AOS and
ISC patches after the integration plugin. Therefore restoring ISC `Sound1` is
not a new audio taste choice; it is the published integration policy.

### Resolution boundary

Use the untouched vendor `AOS_EBT LITE Patch.esp`, followed by a separate
owned/private ESL-flagged plugin containing only the `0F0EB1` override. That
override starts from the official AOS/EBT winner and changes only `Sound1` to
ISC `08AB3B`. Expected output: one IPCT override, zero new records, zero deleted
records. Its deliberate fail-closed master set is Skyrim, EBT Lite, AOS, ISC,
and the vendor AOS/EBT patch; the last dependency enforces the two-file
transaction even though it introduces no new referenced form.
`AOS_ISC_Integration.esp` is an ordering input but need not be a master because
it supplies no field on this record.

AOS permits dependent patches and ISC permits credited fixes, but the
adult-gated EBT permission grid was not available as a durable receipt. No
derived binary or serialized third-party record is committed. A source recipe
may generate the one-record output privately from verified installed winners;
public binary distribution remains gated on a recorded EBT permission result.

The updated `records/fomod-plans/12466-aos.json` makes the vendor patch an exact
future archive selection. LOOT metadata names the private overlay
`Ensrick AOS EBT ISC Patch.esp`; neither file was installed here.

## True defect 2: LFfGM 5.8 and CRF 3.1.26

### Exact vendor payload

[Landscape Fixes For Grass Mods](https://www.nexusmods.com/skyrimspecialedition/mods/9005)
optional Nexus file `646587`, `Patches for Arthmoor's Town add-ons` v1.0.11,
is retained as `downloads/9005-646587.zip`:

- 642,458 bytes;
- SHA-256
  `DA166B88A2D2A17077FF93B6F27A2BF653F1F270D182CA9C02FF855AA20ECDE4`;
- contains `Landscape Fixes For Grass mods - Cutting Room Floor Locations.esp`.

That plugin is 133,286 bytes, SHA-256
`23BF94D72655DC20CFFF1E4EA87604628BB9FDB83D6E84D062A89FE2EBC52B84`,
already ESL-flagged, and contains 23 overrides: one `WRLD`, eleven `CELL`, and
eleven `LAND`; zero new and zero deleted records. Its masters are:

1. `Skyrim.esm`;
2. `Update.esm`;
3. `Dawnguard.esm`;
4. `HearthFires.esm`;
5. `Dragonborn.esm`;
6. `Unofficial Skyrim Special Edition Patch.esp`;
7. `Landscape Fixes For Grass Mods.esp`; and
8. `Cutting Room Floor.esp`.

The eleven cell/land pairs are exact:

| CELL / LAND | Grid | Editor ID |
|---|---:|---|
| `009366` / `00A366` | `-21, 18` | `CRFFrostRiverFarmEast` |
| `009367` / `00A367` | `-22, 18` | `CRFFrostRiverFarmWest` |
| `009368` / `00A368` | `-23, 18` | none |
| `009387` / `00A387` | `-21, 17` | `CRFFrostRiverSE` |
| `009388` / `00A388` | `-22, 17` | `CRFFrostRiverSmithCell` |
| `009389` / `00A389` | `-23, 17` | `CRFIrontreeMill` |
| `009618` / `00A618` | `7, -3` | `ChillfurrowFarmExterior` |
| `00961B` / `00A61B` | `4, -3` | `WhiterunExterior01` |
| `00961C` / `00A61C` | `3, -3` | `WhiterunExterior14` |
| `009A90` / `00AA90` | `-7, -7` | `CRFBarleyDarkFarmEast` |
| `009A91` / `00AA91` | `-8, -7` | `CRFBarleydarkFarmWest` |

The FOMOD describes grass-clipping/path fixes at Frost River, Barleydark Farm,
and the Whiterun stable/farm. It references an older CRF 3.1.7 baseline. The
profile has CRF 3.1.26 and SLaWF 10.6, including both the LFfGM and LFfGM/GotT
compatibility plugins:

| Input | Bytes | SHA-256 |
|---|---:|---|
| `Landscape Fixes For Grass Mods.esp` | 7,890,908 | `A1D4EB8DAD86CA9C903BC8FF3416E698969BE62114872AB0C8DE5B6A0E9B1F10` |
| `cutting room floor.esp` | 1,294,488 | `AD30BABF608A69860921EE19EE0C0876BC9EA249067352D11FC87E02327B9F32` |
| SLaWF archive `26138-790624.7z` | 82,578,636 | `D4B6BC2A3729EAA6593B047437DC1531D3708B96E0149AE4A79C76BBAA478623` |
| `Landscape and Water Fixes.esp` | 18,197,537 | `D63CAC717CD5EE57C4D749D1B7941B37EF53B19C9346811FAD315C997EB8C33B` |
| SLaWF LFfGM patch | 11,439,913 | `F263DF1991621E43172A47F4DC54BC13254C298A6BE66B8219D8C07A1D98F283` |
| SLaWF LFfGM/GotT patch | 10,901,940 | `2A6283CF2C2BE1CE91E1DD08B737B1539592E7BFB9F1DE262F86B50F9D05885F` |

### Multi-way LAND comparison

The comparison used absolute height vertices, three-byte normal vectors, and
texture/layer/quadrant/position keyed alpha entries. It ignored only `Unused`
padding. “SLaWF outcome” is the later active LFfGM/GotT winner compared with the
LFfGM record; it is identical to the preceding SLaWF LFfGM patch on these three
LAND records.

| LAND | Official LFfGM/CRF delta | Active SLaWF delta | Exact overlap | Outcome |
|---|---|---|---|---|
| `00A618` | 25 height vertices, 201 normal vectors, 21 alpha entries | 19 alpha entries | 2 alpha entries, both same | mechanical union |
| `00A61B` | 4 normal vectors, 9 alpha entries | 11 alpha entries | none | mechanical union |
| `00A61C` | 19 height vertices, 208 normal vectors, 46 alpha entries | 175 normal vectors, 41 alpha entries | 175 normals: 167 same, **8 different**; 16 alpha: 3 same, **13 different** | genuine visual decision |

The difference at `00A61C` is not record padding or float noise. Eight normal
vectors and thirteen alpha weights have two different authored outcomes. A
load-order winner would silently discard one result; the audit does not choose
between LFfGM/CRF's path and clipping treatment and SLaWF's current terrain
painting.

`00AA91` looked shared in a raw binary comparison but is not a genuine
collision. Relative to Skyrim.esm, SLaWF changes no height vertex, normal,
base texture, or color. Its 701 apparent alpha differences are all opacity
quantization at or below `1/255`. The official patch makes the substantive
change: 78 height vertices, 638 normal vectors, one base-texture quadrant, and
573 alpha entries differing by more than `1/255`. Taking the official `00AA91`
record therefore loses no demonstrated SLaWF intent.

The other seven LAND records are not shared with another active managed plugin;
the official patch is their only CRF/LFfGM merge.

### Current-version CELL comparison

CRF 3.1.26 adds region `1E58ED:cutting room floor.esp` to Frost River cells
`009366`, `009367`, `009387`, `009388`, and `009389`; the official v1.0.11
patch omits it. Current later Lux Orbis CRF and Nature of the Wild Lands CRF
patches preserve that region where they win today. Cell `009368` has the same
region set in the official patch and the current Nature of the Wild Lands
winner, with ordering only. The Whiterun cells also have later Lux Via/Orbis/CS
winners. A late official plugin by itself would consequently restore its land
but regress current CELL headers.

### Resolution boundary

The official patch is valid input, but **not a safe standalone winner** in this
profile. Use it unchanged, then generate a separate private ESPFE from the full
current load order. The generated output must:

- start each of the eleven structural `CELL` records from its current winner;
- restore any official LFfGM/CRF fields without dropping current CRF 3.1.26,
  Lux, Lux Orbis, Lux Via, or Nature of the Wild Lands fields;
- mechanically merge `00A618` and `00A61B`;
- use the official `00AA91` result; and
- stop before writing `00A61C` until its 8-normal/13-alpha choice is explicit.

No plugin is committed now. A likely minimal final topology is one structural
WRLD, the eleven current-winner CELL headers, and the three shared Whiterun LAND
records, all overrides and no new/deleted forms; the exact emitted set and
masters must be treated as generated evidence, not promised in advance.

[SLaWF's current permission terms](https://www.nexusmods.com/skyrimspecialedition/mods/26138)
require permission to modify or use its assets and forbid reuploading its file.
The generated plugin may be used privately after the user decision, but it must
not be published until permission is documented. The repository carries only
selection/ordering metadata and this independently written analysis.

`records/fomod-plans/9005-lffgm-crf.json` selects the one official CRF plugin.
LOOT metadata names the future private merge
`Ensrick LFfGM CRF Landscape Patch.esp`. Both are transaction-gated; neither was
installed here.

## False positive 1: Engine Fixes Part 2

LOOT's complete predicate is:

```text
version("SKSE/Plugins/EngineFixes.dll", >=, "7.0.0")
and not file("../d3dx9_42.dll")
```

It does not inspect native SKSE preload support or runtime evidence.

The installed `EngineFixes.dll` is version `7.0.21.0`, 2,564,608 bytes,
SHA-256
`26AF56098F739821558AC07E1B5730A223BCD8DD7AF87EF1EDB0288C22CAE179`.
The adjacent zero-byte `EngineFixes_preload.txt` has the same vendor timestamp.
There is intentionally no live root `d3dx9_42.dll`; the legacy 88,576-byte
preloader is parked as `d3dx9_42.dll.bak.v7.0.20-preloader`, SHA-256
`CF366987DA6237559EB6E113EA717EC21762C9EEC3A87D9DC4FA9DDFE7789C26`.

The current [SKSE plugin manager](https://github.com/ianpatt/skse64/blob/master/skse64/PluginManager.cpp)
discovers `SKSEPlugin_Preload` and the
[SKSE initialization path](https://github.com/ianpatt/skse64/blob/master/skse64/skse64.cpp)
calls the preload phase before ordinary plugin load.

Runtime receipt `EngineFixes.log` is 5,621 bytes, modified
`2026-09-04T02:10:48Z`, SHA-256
`4FAA754CFC00D6CF3ECCF658F2C7C206E76E15F25542D7BD76C6606571511D05`.
It records:

- `2026-09-03 21:10:06.909`: `EngineFixes v7.0.21 PreLoad`;
- every enabled pre-load hook installed without an error;
- `21:10:07.161`: `EngineFixes SKSE Load`; and
- `21:10:48.739`: main menu reached in 41,830 ms.

`skse64.log`, SHA-256
`86FDFBD239F410F749E275DEEE81D0BF91DE1CFD392894CA49781AF5DA1B9972`,
independently records runtime `1.7.104`, SKSE `2.3.1`, Engine Fixes check,
preload, ordinary load, and `loaded correctly`.

Outcome: the warning is a masterlist false positive for this native-preload
runtime. Do not reactivate the legacy DLL and do not change Engine Fixes.

## False positive 2: ENB Light and Particle Patch

LOOT's complete resource predicate warns when all of the following are true:

```text
not (file("Particle Patch for ENB.bsa")
     and active("Particle Patch for ENB.esp"))
and not file("textures/effects/gradients/gradillusiondark01m.dds")
and not file("textures/WiZkiD/iron_e.dds")
```

The current [Particle Patch](https://www.nexusmods.com/skyrimspecialedition/mods/65720)
FOMOD deliberately supports configurable plugin/BSA names. This profile uses
the current `Particle Patch` basename and BSA mode:

- retained v1.4.6 archive `downloads/65720-790711.zip`: 182,391,569 bytes,
  SHA-256
  `4FE0E966B7D63B3C9136454EB724F34E4E1A3B36A41DC08867A5B52969F2EECD`;
- `Particle Patch.esp`: 5,942 bytes, SHA-256
  `F9B60DFE74F057030DD23DFFC06DB991B1823CDC49E1B867374DA30E1F29BA51`;
- `Particle Patch.bsa`: BSA v105, 625 entries, 61,926,141 bytes, SHA-256
  `BD31836F49D2F38FFFBB8FC3E49D6F2A414552FF6883DF2D22EE62E0EB094B44`;
- archived `textures/effects/gradients/gradillusiondark01m.dds`: 22,052
  bytes, SHA-256
  `C189970851C5691EB2904ADAD2DB3809492E6D2AD3D106B5EA98A85E9D6AE73E`.

Outcome: the resource exists and its loader plugin is active. LOOT recognizes
only the legacy basename pair or a loose-file probe and does not inspect the
renamed archive. Do not rename the vendor pair and do not extract its BSA.

## Inactive, intentional missing-master debt

### SLaWF wrong Water variant

`Landscape and Water Fixes - Patch - LFfGM - Water for ENB.esp` is
ESL-flagged, 1,362,586 bytes, SHA-256
`3D1171C7B774CC2CEEAEBD449EA3C0DD9CC44E6E18986F069F5C128C7F3942F7`,
and contains 293 overrides: one WRLD, 146 CELL, and 146 LAND; zero new or
deleted records. Its masters are Skyrim, Update, HearthFires, SLaWF,
**`Water for ENB.esm`**, LFfGM, and the SLaWF LFfGM patch.

The profile's chosen Water variant is instead
`Water for ENB (Shades of Skyrim).esp`. The absent ESM is not a missing
requirement; this is the wrong optional patch. The future SLaWF archive plan no
longer selects `Patches/Water for ENB - LFfGM`.

### Lux optional fixer variants

| Inactive plugin | SHA-256 | Masters | Records |
|---|---|---|---:|
| `Lux - Wraithguard patch.esp` | `B080DFE13B6E31E24BB88C2B017B5B0379C82174A51C24871A85391F7AFBD6A8` | Skyrim, Wraithguard CC, **`wraithguardvaultfixer.esp`**, Lux | 166: 3 CELL + 163 REFR; 90 overrides + 76 new |
| `Lux - Myrwatch patch.esp` | `E73D4AB2D726E4BBCC56244B6924B503705A6A21E1464D36593E8AFB17D31F8F` | Skyrim, Dragonborn, Myrwatch CC, **`myrwatchhomefixer.esp`**, Lux Resources, Lux | 590: 4 CELL + 574 REFR + 10 STAT + 2 TXST; 285 overrides + 305 new |

Both are ESL-flagged and inactive. Their fixer masters are intentionally not
installed, so enabling either patch would be wrong.

Lux Creation Club bundle Nexus file `415225` is 987,049 bytes, SHA-256
`1963CF42ADF781E70A1DADA453BD8A735C72E7D995F33C2660747C00EC6241AA`,
with 24 plugins and one mesh tree. Exactly 22 plugins are active and valid for
this profile. `records/fomod-plans/43158-lux-cc-active-profile.json` selects
those 22 plus the mesh tree and omits only Myrwatch and Wraithguard.

The current inactive files were not deleted or hidden. The plans make the next
authorized clean rebuild omit them without editing or repackaging the retained
vendor archives.

## Decisions and gates

### Decided by evidence; no user taste choice

- AOS's included ESL patch is the correct two-way visual patch.
- ISC's `Sound1` must be restored on `0F0EB1`; the integration author's own
  feature allocation makes this objective.
- The official LFfGM/CRF plugin is required input, but current CELL winners and
  SLaWF's non-overlapping fields must be preserved.
- `00A618`, `00A61B`, and `00AA91` have deterministic record-level outcomes.
- Engine Fixes and Particle Patch warnings are false positives; neither runtime
  should be changed to appease a filename-only test.
- The three inactive missing-master plugins target unchosen dependency
  variants and should be absent from the next deterministic installation.

### True user decision

Choose the authored visual result for the 8 normal vectors and 13 alpha entries
that conflict on `LAND 00A61C`:

1. prefer the official LFfGM/CRF path and grass-clipping outcome at those exact
   overlaps;
2. prefer the current SLaWF/LFfGM terrain outcome at those exact overlaps; or
3. defer until an upstream combined patch or controlled in-game visual A/B
   supplies stronger evidence.

All non-overlapping fields are preserved in every option. No other finding in
this audit requires a taste decision.

### Operational and publication gates

- #102 must be resolved before any profile transaction, enable/disable, sort,
  or launch.
- Generate and inspect both owned ESPFEs against the exact input hashes above;
  do not commit generated plugins or third-party serialized records.
- Record EBT permission before publishing the AOS-derived output and obtain
  SLaWF permission before publishing the landscape-derived output. Private
  source-generated testing is the interim boundary.
- Install each official patch and its owned repair in one fail-closed
  transaction. The LFfGM/CRF vendor patch must never be left as the final
  standalone winner.
- Re-run LOOT, master/link/order audits, the full record scan, and deterministic
  double-generation. AOS and LFfGM compatibility messages should disappear;
  Engine Fixes and ENB Light may remain as documented false positives until
  upstream LOOT metadata becomes archive/basename aware.
- Reconcile concurrent profile ownership first. During this audit another
  owner changed live reconciliation state while the compatibility inputs above
  remained stable. The latest read-only reconcile reported 18 errors: seven
  CS/CRD enabled-state mismatches; eight unledgered folders (Proteus hotkeys,
  TDP wind calibration, FSMP, IED, NFF-RDO support, RDO Lite, Unbound-RDO Lite,
  and the Water conflict patch); Azurite and Proteus inventory mismatches; and
  one stale duplicate FSMP entry. Keep coverage itself was clean at `0/0/0`.
  These are concurrent profile/ledger ownership issues, not evidence that
  changes the compatibility classifications above. Do not mix their repair
  into this patch and do not use this record as authority to edit protected
  profile state.

## Primary/vendor sources

- [LOOT Skyrim SE masterlist at the exact audited commit](https://github.com/loot/skyrimse/blob/e3c591ba9c041f23f407a0a0f87f72cc6325aa43/masterlist.yaml)
- [Audio Overhaul for Skyrim 4.1.3](https://www.nexusmods.com/skyrimspecialedition/mods/12466)
- [AOS - ISC Integration](https://www.nexusmods.com/skyrimspecialedition/mods/36761)
- [Immersive Sounds - Compendium](https://www.nexusmods.com/skyrimspecialedition/mods/523)
- [Landscape Fixes For Grass Mods](https://www.nexusmods.com/skyrimspecialedition/mods/9005)
- [Skyrim Landscape and Water Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/26138)
- [Cutting Room Floor](https://www.nexusmods.com/skyrimspecialedition/mods/276)
- [Particle Patch](https://www.nexusmods.com/skyrimspecialedition/mods/65720)
- [SSE Engine Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/17230)
- [SKSE native plugin preload implementation](https://github.com/ianpatt/skse64/blob/master/skse64/PluginManager.cpp)
- [Lux](https://www.nexusmods.com/skyrimspecialedition/mods/43158)
