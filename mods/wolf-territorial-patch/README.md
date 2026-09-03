# Ensrick Wolf Territorial Patch (and Encounter Thinning)

Issue: [#42](https://github.com/Ensrick/skyrim-mod-assistant/issues/42). User design
2026-09-02, after playing: wolves should be **territorial, not hunting** - "attack when
you get close, like horkers and bears" - and there should be **fewer encounters but
still packs of 2-3**. Measurements behind every number here are in the 2026-09-02
appendix of `docs/WILDLIFE-WOLVES-2026-08-28.md`.

Two plugins come out of one generator, because the two requirements are different
shapes of change. Both are ESL-flagged, override-only, and reversible by disabling
one mod.

| plugin | what it changes | state |
|---|---|---|
| `Ensrick Wolf Territorial Patch.esp` | 9 `NPC_` records: the AI aggro-radius bands on 8 ambient wolf bases, plus 1 de-inherit | **installed and enabled**, launch-verified |
| `Ensrick Wolf Encounter Thinning.esp` | 191 placed-actor `Initially Disabled` flags (381 records with parent cells) | **generated and staged only** - the cut size is a user decision |

## 1. Territorial behaviour

The wolf/bear difference is one AI Data field, and it is not the aggression enum.
`EncWolf` and `EncBear` are both `Unaggressive` with `AggroRadiusBehavior` on, both
`WarnOrAttack` 2000 and both `Attack` 1500. The difference is `Warn`: bear **2500**,
wolf **0**. Bears have a warning band; wolves cross straight into attack at 1500 units
(about 21 m at 1 unit = 1.428 cm). `EncHorker`, the other actor the user named, is
`Aggressive` but attacks only inside **320**.

The rule, in `policy.json`:

| field | vanilla wolf | this patch | vanilla bear | vanilla horker |
|---|---:|---:|---:|---:|
| `Warn` | 0 | **2500** | 2500 | 850 |
| `WarnOrAttack` | 2000 | **1200** | 2000 | 640 |
| `Attack` | 1500 | **640** | 1500 | 320 |

Untouched on purpose: `Aggression` stays `Unaggressive`; `Confidence`, `Assistance`,
`Mood`, `Responsibility` and `EnergyLevel` are forwarded; the combat style `csWolf`
(`057BE8`, `DATA` flag `0x2` flanking, `FlankDistance` 0.5, `StalkTime` 0.4) is not
edited, so a pack still flanks like a pack; and **no faction record is touched** -
`PredatorFaction -> PreyFaction = Enemy` is what makes wolves hunt deer, and bears and
sabre cats share it, so editing it would neuter them too.

Eight targets, all carrying the identical vanilla signature `Unaggressive / radius on /
0 / 2000 / 1500`, verified at generation time before anything is written:

| record | placed refs | worldspace |
|---|---:|---|
| `023ABE:Skyrim.esm EncWolf` | 107 | Skyrim |
| `023C34:Gray Fox Cowl.esm manny_GF_Animal_DesertWolf` | 41 | Alikr |
| `003C86:BSHeartland.esm CYREncWolf` | 15 | Bruma |
| `0718E4:BSHeartland.esm CYREncWolfTimber` | 4 | Bruma |
| `0F544B:arnima.esm EncWolfarnima2` | 3 | Beyond Reach |
| `024C7A:arnima.esm EncWolfarnima` | 1 | Beyond Reach |
| `0B559B:BSHeartland.esm CYREncWolfHighland` | 0 (leveled) | Bruma |
| `0B559D:BSHeartland.esm CYREncWolfDire` | 0 (leveled) | Bruma |

Records that take AI data from a target through their template follow for free. The
generator **measures** that set from the load order and fails if `policy.json` claims
a different one, so the blast radius can never drift silently:

- from `EncWolf`: `EncWolfRed`, `EncWolf_Indoor`, `EncWolfSprigganCompanion`,
  `dunWhiteRiverWatchWolf`, `dunPOITrappedWolf`, `dunShadowgreen_AmbushWolf`,
  `dunFellglow_WarlockWolf`
- from `CYREncWolf`: `CYREncWolf_Indoor`, `CYREncWolfSprigganCompanion`
- from `CYREncWolfTimber`: `CYREncWolfTimber_Indoor`, `CYREncWolfTimberSprigganCompanion`

One heir is deliberately taken out of that set: `0877EB:Skyrim.esm SummonFireStorm`,
the conjured Flaming Familiar, is **de-inherited** and pinned to the pre-patch
0/2000/1500. A summon answers to its summoner, not to a territory.

52 other wolf records are excluded with a reason each in `policy.json`: `EncWolfIce`
(VeryAggressive on purpose - whether the snow keeps a wolf that hunts on sight is an
open user decision), bandit and pit wolves, Companions spirit wolves, Howl summons,
Creation Club bone wolves, Beyond Reach quest wolves, 3DNPC named wolves, and the
Proteus and BSAssets template zoos. The generator refuses to touch anything not listed
as a target.

## 2. Encounter thinning (staged, not installed)

Frequency and pack size pull against each other through the leveled lists. Every
placed reference rolls its regional predator list independently, so thinning wolves
out of `LCharAnimalForestPredator` lowers frequency **and** turns a three-point site
into a wolf, a bear and a spider. Retiring whole spatial **clusters** does not: it
lowers frequency and leaves pack size exactly as Bethesda placed it.

Measured over the live load order, 622 exterior references on the seven wolf-bearing
regional predator actors form **387 clusters** at a 2000-unit link radius (about 29 m):

```
size 1: 203 clusters      size 2: 137      size 3: 43      size 4: 4
```

The patch retires the singleton clusters - the lone predator between packs, which is
what makes the wilderness feel crowded - and leaves every pack whole:

```
retired 191 references (30.7%), 12 singleton clusters held back
remaining 431 references in 196 clusters, all of size >= 2
by base: Forest 45, MountainSnow 41, Canyon 34, Plains 29, CoastSnow 26, Hills 15, SnowFields 1
```

Four rules keep it honest:

1. **Nothing is deleted.** A deleted `ACHR` is a UDR; the references are flagged
   `Initially Disabled`, so rollback is disabling one plugin.
2. **Ineligible references still cluster.** Persistent references (171), enable-parented
   ones (13) and already-disabled ones (1) are never retired, but they count towards
   cluster size. Dropping them from the clustering instead is how a pair becomes a fake
   singleton - that error turned a 31% cut into 72% on the first run.
3. **All or nothing per cluster.** A cluster holding an untouchable reference is left
   whole, so no encounter is half-retired. That is the 12 held clusters.
4. **A guard rail.** The run refuses if it would retire more than
   `maxRetiredFraction` (40%) of the candidates.

`LCharAnimalForestSnowPredator` has **0 wolf entries**, so its 30 placed references are
out of scope entirely.

**This half is not installed.** How much wilderness to empty is the user's call, and it
leaves a hole for [#43 Bounded Encounters](https://github.com/Ensrick/skyrim-mod-assistant/issues/43)
to fill: 191 discrete, already navmeshed, already encounter-zoned exterior positions.

## Reproduction

```powershell
pwsh ./mods/wolf-territorial-patch/regenerate.ps1 `
  -ToolchainManifest ./toolchain.json `
  -InstanceRoot C:/Users/danjo/source/repos/mo2-instances/skyrim-se `
  -DataFolder "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/Data"

pwsh ./mods/wolf-territorial-patch/regenerate-thinning.ps1 -ToolchainManifest ... (same arguments)
```

Each script verifies the pinned MO2 and Spriggit hashes, builds the locked .NET 9
generator (Mutagen 0.54.4 / Synthesis 0.36.6, warnings as errors), runs two generations
through the MO2 VFS on profile `Default` and requires byte-identical output, link-audits
the result, round-trips it through Spriggit 0.41.0 (`spriggit/` is the committed text
form), and writes a deterministic one-file zip plus `work/regeneration-result.json`.
`regenerate.ps1` additionally runs the wolf record audit into `work/wolf-audit.json`
(60 wolf records and 29 reference controls over 323 plugins, 24,207 placed actor
references) - that file is the receipt for every claim in `policy.json`.

Re-run after any change to USSEP, Beyond Skyrim: Bruma, Beyond Reach, The Gray Cowl of
Nocturnal or the profile load order; the output only reflects the winners at generation
time. Removing one of those worldspaces makes the behaviour patch a missing-master
error until it is regenerated.

## Load order

LOOT rule in `config/loot/userlist.yaml` and the live userlist: group
`Ensrick Generated Patches`, after `Ensrick Guard Scaling Patch.esp`. No LOOT sort was
run when the behaviour patch went in - it already lands last in `plugins.txt` and
`audit/verify_order.py` is CLEAN - so the rule takes effect at the next sort.

## Distribution

`distributable`: our own override records only, no vendor assets. Generator source is
under the repository's MIT license; Spriggit text tree, `policy.json` and both
`thinning/policy.json` rules are committed. Build record
`records/source-builds/ensrick-wolf-territorial-patch.json`.

## What is still unverified

The numbers, not the mechanism. `2500 / 1200 / 640` is a play-feel choice: 1500 is
"charges you across a field", 320 is "you basically stepped on it". It needs an
in-game approach and retreat test before it is fixed, and `Confidence` is a second
lever nobody has pulled yet - every wolf in the game is `Foolhardy`, which is why they
never break off.
