# Audit: every Ensrick artifact against the CK-first doctrine

Audit date: 2026-09-03. Rules: `docs/CK_FIRST_DOCTRINE.md`.
Ordered worst first. No artifact was changed by this audit; it is a verdict list.

## SCOPE CORRECTION, added after the user asked whether this audited everything

**It did not.** This audit was written before rule 0 existed, and it covers only
the code-versus-hand-authoring axis - rules 3, 4 and 6. Two gaps:

1. **Nothing was audited against rule 0** ("was prior art searched before this
   was designed?").
2. The 13 artifacts marked CORRECT below were classified **by category** -
   textures, ini overlays, mesh work - not examined individually. Being the
   light *tool* does not mean the artifact should exist at all.

**First measurement of the rule 0 gap.** Ten Ensrick artifacts sampled against
their own records, searching for any evidence that an existing mod or a vanilla
mechanism was checked before building ours:

| artifact | record | prior-art mentions |
|---|---|---:|
| Skyking Signs Env Mask Fix | ensrick-overlay-distribution | **0** |
| Bloodskal Blade 4 Static Glow | active-file-conflicts | **0** |
| Vanilla Hair Remake SMP NPC Compat | ensrick-overlay-distribution | **0** |
| Vanilla Skin Soft-Light Maps | face-eye-makeup-audit | **0** |
| Assorted Mesh Fixes SE Mesh Port | ensrick-overlay-distribution | **0** |
| Vikings Weaponry SE Mesh Port | ensrick-overlay-distribution | **0** |
| Skyland Solitude Manhole Path Fix | envmask-missing-scan | **0** |
| CC Madness Longsword Env Mask Fix | envmask-missing-scan | **0** |
| Better Fur Fine Clothes Refit | ensrick-overlay-distribution | **0** |
| Scoped Werewolf Totem Skull 98175 | *no record found* | - |

**CORRECTED 2026-09-03 by the full prior-art pass: it is two of ten, not zero.**
The grep above searched the wrong place - narrative records - and missed prior
art recorded in structured fields. `Bloodskal Blade 4 Static Glow`'s ledger
`note` opens with a correct check of the author's four released files, and
`Scoped Werewolf Totem Skull 98175` - logged here as "no record found" - carries
an `alternatives` array in its source-build JSON naming three candidates with
versions, dates and an archive hash. **That is the best rule-0 record in the
project and is the shape to standardise on.**

The real pattern is sharper than "nobody researched anything": **asset fixes
were researched against the vendor page; record patches and runtime plugins
were not researched at all.** Full findings:
`records/prior-art-audit-2026-09-03.md`.

Every other artifact in the sample did go from symptom straight to our own fix,
with no recorded search for an existing solution. Several have probable prior art -
Assorted Mesh Fixes very likely has a released SE conversion, env-mask defects
are the kind of thing authors and community patches ship, and vanilla `_sk`
soft-light maps may exist as a mod rather than something to extract by hand.

A proper rule 0 pass over every artifact is queued as remediation item 0 below.
Until it runs, **treat the CORRECT column as "right tool", not as "should
exist"**.

## Summary

| verdict | count |
|---|---:|
| **VIOLATION** - code where hand-authoring was right | 4 |
| **PARTIAL** - generation justified, weight not | 1 |
| **JUSTIFIED** - genuinely generative | 2 |
| **CORRECT** - already the light tool | 13 |
| **N/A** - source rebuilds of vendor DLLs, not authoring | 14 |

The pattern is narrow and consistent: **plugin-producing patches reached for a
.NET generator regardless of size, because one precedent existed and every
later agent copied it.** Nothing else in the project has this problem.

---

## VIOLATIONS

### 1. `Ensrick Wolf Territorial Patch` - the worst case

**830 lines of C# across 7 files → a 3,959-byte plugin changing three numbers
on nine NPC records.** ~92 lines of code per changed field.

The entire semantic content, already present in the repo as readable text at
`mods/wolf-territorial-patch/spriggit/Npcs/EncWolf - 023ABE_Skyrim.esm.yaml`:

```yaml
AIData:
  AggroRadiusBehavior: True
  Warn: 2500          # was 0
  WarnOrAttack: 1200  # was 2000
  Attack: 640         # was 1500
```

**Should have been:** edit nine spriggit YAML files, serialize back. Or nine
records in xEdit.

**Partial defence, recorded honestly:** the generator *measures* which records
inherit the AI data through their template and fails if the policy disagrees.
That guard is real and worth keeping - but it is an audit script, and it did
not need to also be the authoring mechanism.

### 2. `Ensrick Guard Scaling Patch`

**532 lines of C# → a 3,488-byte plugin with three NPC overrides.** Same shape,
same verdict. 4 spriggit YAML records exist alongside it.

### 3. `Ensrick - Collectibles Helper USSEP Forward`

**204 lines of C# → a 1,860-byte plugin.** A forward of USSEP values into one
mod's records is the single most standard xEdit operation there is - right
click, "Copy as override", done.

### 4. The Papyrus set-bonus script (advice, not an artifact)

Never installed here, but given as advice and acted on by a third party. A
`ReferenceAlias` script with SKSE `GetWornForm` calls on every equip and
unequip, replacing one condition function. Full analysis:
`records/matching-set-perk-mechanism-2026-09-03.md`.

---

## PARTIAL

### `Ensrick CRF Semantic Patch`

**364 lines of C# → a 9,927-byte plugin, 10 spriggit records.** The semantic
comparison that decided *which* Cutting Room Floor records needed forwarding is
genuine analysis and belongs in code. Emitting ten records afterwards did not.

**Verdict:** keep the analysis, hand-author the output. This is the exact split
rule 4 draws.

---

## JUSTIFIED - leave alone

### `Ensrick Wolf Encounter Thinning`

191 references selected by clustering 622 exterior refs at a 2000-unit radius,
with an eligibility rule excluding persistent and enable-parented refs from
retirement while still counting them toward cluster size. Not hand-authorable,
and the rule is the artifact. Rule 4, first and third clauses.

The guard rail also caught a real error - excluding ineligible refs from the
*clustering* turned pairs into fake singletons and produced a 71.6% cut instead
of 30.7%. Hand-authoring would not have surfaced that.

### `Ensrick - Cloak Distribution Balance`

Required computing an actual probability across 24 shared leveled lists to
discover a generic NPC's cloak was 1.0% Cloaks of Skyrim against 54.8% fur.
The output is a SkyPatcher INI - the light artifact - and only the measurement
was code. Rule 4, second clause. **This is the shape the others should have
had.**

---

## CORRECT - already the right weight

No plugin, no generator; a config line or an asset:

- `Ensrick - Death Hound Loot Fix` - one `removeFromLLs`
- `Ensrick - Cloaks of Skyrim Unique Placement` - ten SkyPatcher `filterByNpcs`
- `Ensrick - Media Keys Fix Configuration`, `- SSE Display Tweaks
  Configuration`, `- MLO2 Foundation Config` - ini overlays
- `Ensrick - Skyking Signs Env Mask Fix`, `- CC Madness Longsword Env Mask Path
  Fix`, `- Skyland Solitude Manhole Texture Path Fix`, `- Bloodskal Blade 4
  Static Glow`, `- Vanilla Skin Soft-Light Maps` - texture and mesh assets
- `Ensrick - Vanilla Hair Remake SMP NPC Compatibility` and its XML fix
- `Ensrick - Better Fur Fine Clothes CBBE-HIMBO Refit`, `- Assorted Mesh Fixes
  SE Mesh Port`, `- Vikings Weaponry SE Mesh Port` - mesh work, correctly not
  code

## N/A - vendor source rebuilds

Light Placer, ConsoleUtilSSE, JContainers, PapyrusUtil, Proteus, RaceMenu/skee64,
QuickLoot IE, Seasonal Clothing Framework, MenuPilot, LaunchProbe, Pandora
headless, MO2Headless, CDF/DDR/currency-swapper. These are **compiling upstream
C++ for runtime 1.7.104** - not authoring game records, and outside this
doctrine entirely.

---

## Remediation, in priority order

0. **Run the rule 0 pass on every artifact** - for each, search Nexus and the
   vanilla records for an existing solution, and record the finding either way.
   Any artifact with released prior art becomes a candidate for deletion in
   favour of the existing mod. This is the audit this document did not do.
1. **Convert wolf territorial and guard scaling to spriggit YAML.** No gameplay
   change; both become xEdit-openable and reviewable. Keep the wolf generator's
   template-inheritance check as a standalone audit script.
2. **Convert Collectibles Helper USSEP Forward** the same way.
3. **Split CRF Semantic Patch** - analysis stays code, the ten records become
   hand-authored.
4. **Fold the remaining generators into one**, driven by per-patch policy, per
   rule 6. `mods/currency-integration` is Sol's and in flight - coordinate
   rather than touching it.
5. **Add the "why code" sentence** to every `records/source-builds/*.json` for a
   generated plugin, per rule 7.

Nothing here changes what the game does. It changes whether a modder receiving
this list can read the patches.
