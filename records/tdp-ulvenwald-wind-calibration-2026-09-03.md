# TDP–Ulvenwald wind calibration — 2026-09-03

Status: source-complete and statically verified; live installation and
owner-observed Falkreath acceptance pending.

Issue: [#29](https://github.com/Ensrick/skyrim-mod-assistant/issues/29).

## Report and root cause

During the September 3 playtest, most tree motion was normal, but some trees
south of Falkreath moved as if exposed to hurricane-force wind. The runtime SMP
log showed an active weather wind value of 80, normalized to 0.31, but that did
not by itself identify the faulty layer.

The active profile uses full NotWL as placement authority, Ulvenwald 3.3.2 as
an asset-only dependency, and Tree Diversity Project's official NotWL-base +
Ulvenwald-swap BOS configuration. `Dynamic Wind` and `Skyrim Is Windy` are not
installed or enabled.

The swap configuration selects 13 unique TDP TREE forms. Matching the model
path of each form against every Ulvenwald TREE record proved that eleven forms
apply substantially stronger TDP motion values to an Ulvenwald mesh than
Ulvenwald applies to that exact mesh. The branch multiplier is roughly 2.5x to
6x. The isolated species behavior follows directly from this per-form mismatch.

The remaining two targets are excluded intentionally:

- `TDP_swamp01`: branch flexibility 1.0, below Ulvenwald's 1.75, so it is not
  the reported overdrive;
- `TDP_willow_twisted_big01_summer`: the winning mesh comes from NotWL and has
  no same-path Ulvenwald record.

## Prior art and CK-native answer

The prior-art order required by `docs/CK_FIRST_DOCTRINE.md` was followed:

1. Installed records: TDP and Ulvenwald were serialized with the pinned
   Spriggit build and matched by exact NIF path. This exposed the eleven
   mismatches.
2. Vanilla/engine shape: `TREE` is the native base-object record containing the
   trunk, branch, and leaf motion values. No runtime script is required.
3. Creation Kit wiki: the wiki's object/file documentation confirms ordinary
   plugin master/override authoring, but its dedicated `/Tree` page is absent;
   no CK-wiki field reference for these four values was available.
4. Mod documentation: Beyond Skyrim's *Tree Animations* documentation confirms
   that TREE forms control trunk/branch flexibility and leaf frequency.
   `Dynamic Wind - Ulvenwald Patch` independently documents the same
   model/value mismatch symptom and likewise takes the values from Ulvenwald's
   exact-mesh records.

CK-native answer: override the eleven TDP TREE forms and edit their four named
motion fields to the values from Ulvenwald's exact-mesh form. That is the whole
fix. The checked-in Spriggit YAML is the authored plugin source; no Papyrus,
SKSE DLL, SkyPatcher rule, or one-off .NET generator exists.

Sources:

- https://ck.uesp.net/wiki/Object_Window
- https://wiki.beyondskyrim.org/wiki/Arcane_University:Tree_Animations
- https://www.nexusmods.com/skyrimspecialedition/mods/155974
- https://www.nexusmods.com/skyrimspecialedition/mods/187634

## Exact inputs

| input | version/file | SHA-256 |
|---|---|---|
| Tree Diversity Project archive | 1.0.1 / Nexus file 680001 | `606224ADE3AEE68444C681453712635DC45C4E66456D06E35EC7509F38185FCD` |
| `Tree_Diversity_Project.esp` | 131,068 bytes | `6530379EDDF5864F69B88D0D16120FA8B09230D07542D8FA7F5E651280E2F3FD` |
| selected BOS INI | NotWL + Ulvenwald | `72CC2A9458DB0F23F1049D298EFE33071E9D54515ACE10B3FBEEF9566939182B` |
| Ulvenwald archive | 3.3.2 / Nexus file 444742 | `6FD168C2F063A3C8DD4D3D5B8D1BC5D596B76721F3364542ACA80056DB0A7379` |
| extracted `Ulvenwald.esp` | 4,865,499 bytes | `1BB684C5AA845090B68138B85081F2E0F2DA1045344DDAEDBB7AE7FC5DBE00B1` |
| Spriggit executable | 0.41.0 | `D55E9733FAA4A45D9166D9981225F51DCC003A91B4166F1AD88B955D1B3EAE68` |

The official archives and live vendor folders were read only. `Ulvenwald.esp`
was extracted into a temporary audit directory and remains disabled in MO2.

## Verification receipt

- 11 TREE overrides, 0 new forms, 1 master (`Tree_Diversity_Project.esp`)
- ESL flag `0x200`
- 44 motion-field comparisons against same-path Ulvenwald records: pass
- 11 comparisons proving all non-motion YAML fields equal TDP: pass
- full record inventory: exactly the intended 11 FormKeys
- link audit: 0 unresolved
- two independent Spriggit deserializations: byte-identical
- plugin: 2,644 bytes, SHA-256
  `424BCD2EAB9491513292593368730C956DED84ED8CA2661404782D45FE17426F`
- two deterministic ZIP builds: byte-identical
- archive: 1,115 bytes, SHA-256
  `752BA2F86AF27C1D108FAADC3E01D7175B44C174A0424484DBA1DF0308273B2F`
- checked Spriggit semantic round trip: pass; the sole textual diff is the
  tool's omission of a final newline in `spriggit-meta.json`

## Remaining acceptance

Installation is safe to test mid-save because it changes base-object motion
data only, but it is not called complete until:

1. a bounded main-menu and existing-save loader verification passes;
2. the user revisits the affected Falkreath route in calm and strong wind;
3. adjacent NotWL-only trees and all eleven selected species show plausible
   relative movement;
4. no new near/LOD transition or culling issue appears.

TexGen/DynDOLOD remains deferred until the exterior stack is frozen.
