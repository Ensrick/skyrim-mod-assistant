# Ensrick Guard Scaling Patch

Issue: [#51](https://github.com/Ensrick/skyrim-mod-assistant/issues/51). User rule
(2026-08-29): ordinary hold, city, Imperial and Stormcloak guards scale 1:1 with
the player, minimum level 5, no +20 offset. Named guards, captains, commanders,
quest actors and mod-added guard equivalents are audited separately and are not
touched.

## What it does

`Ensrick Guard Scaling Patch.esp` is an ESL-flagged, override-only ESP with three
NPC_ records, the templates every ordinary guard inherits its stats from:

| record | vanilla | patch |
|---|---|---|
| `EncGuardImperialTemplate` (0F6F37:Skyrim.esm) | PC x1.0, min 20, max 50 | PC x1.0, min 5, max 50 |
| `EncGuardSonsTemplate` (0F6F38:Skyrim.esm) | PC x1.0, min 20, max 50 | PC x1.0, min 5, max 50 |
| `DLC2RRGuardTemplate` (0195AF:Dragonborn.esm) | PC x1.0, min 20, max 50 | PC x1.0, min 5, max 50 |

Every other field is the current winner's (USSEP for the two Skyrim.esm
records), forwarded unchanged. Masters: `Skyrim.esm`, `Dragonborn.esm`. No new
forms, no assets, no vendor file modified.

Why these three and nothing else: the record audit
(`records/guard-scaling-audit-2026-09-02.md`, rendered by `report.py` from
`work/guard-audit.json`) shows the level-20 guard is vanilla, not a mod: the
placed `Guard*` records all use their template's stats and the chain ends at
those templates. `policy.json` names the targets and every exclusion with its
reason; the generator refuses to touch anything not listed.

## Reproduction

```powershell
pwsh ./mods/guard-scaling-patch/regenerate.ps1 `
  -ToolchainManifest ./toolchain.json `
  -InstanceRoot C:/Users/danjo/source/repos/mo2-instances/skyrim-se `
  -DataFolder "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/Data"
```

The script verifies the pinned MO2 and Spriggit hashes, builds the locked .NET 9
generator (Mutagen 0.54.4 / Synthesis 0.36.6, warnings as errors), runs the
record audit and two generations through the MO2 VFS on profile `Default`,
requires byte-identical output, link-audits it, round-trips it through Spriggit
0.41.0 (`spriggit/` is the committed text form), and writes a deterministic
one-file zip plus `work/regeneration-result.json`. `work/` and `package/` are
local; a previous tree is renamed `.bak.v<stamp>`, never recursively deleted.

Re-run after any change to USSEP, Dragonborn's Redoran guard template, or the
profile's load order; the output only reflects the winners at generation time.

## Load order

LOOT rule in `config/loot/userlist.yaml`: group `Ensrick Generated Patches`,
after `Ensrick CRF Semantic Patch.esp`. Anything that overrides the three
templates and loads later would silently undo the rule; the audit's override
chains are the check.

## Distribution

Distributable: our own override records only, no vendor assets, generator source
under the repository's MIT license. Ledger row in `records/installed-mods.json`,
build record in `records/source-builds/ensrick-guard-scaling-patch.json`.
