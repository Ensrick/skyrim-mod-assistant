# RMB Core duplicate cloak-injector shadow

Issue: [#200](https://github.com/Ensrick/skyrim-mod-assistant/issues/200)

Candidate: `Ensrick - Cloak Distribution Balance` 2026-09-04.1

Status: source and deterministic archive complete; **not installed**

## CK-first answer

This does not need a plugin, Papyrus, SKSE code, or Creation Kit work. MO2 can
replace one virtual file by exact path. The owned overlay therefore supplies a
comment-only file at the accidental vendor file's exact `outfit\Headgear` path.
The legitimate `outfit\Cloaks` file remains visible and unmodified.

The Python component is validation and packaging only. It does not generate
game data: it rejects changed vendor input, checks that the hand-authored
shadow is still a no-op, and produces a deterministic ZIP.

## Pinned provenance

Immutable prerequisite: RMB SPIDified - Core Framework 6.3.0, Nexus SSE 63625,
file 754890, archive
`RMB SPIDified - Core Framework-63625-6-3-0-1779405589.zip`.

- Archive SHA-256:
  `59AA7240BC7CACB3C8E29D0FEE8F3B282730A2A054D35D0E9340628E7BE6960D`
- Both extracted inputs are 9,623 bytes and SHA-256
  `B3AA37FA441FCBA10BB4CB219866F9B9C312DDD2CCF746F78ECE580D2AA9D9EA`:
  - `SKSE/Plugins/SkyPatcher/outfit/Cloaks/RMB SPID - Core Definitions.esp.ini`
  - `SKSE/Plugins/SkyPatcher/outfit/Headgear/RMB SPID - Core Definitions.esp.ini`
- Both contain the same 58 active `filterByOutfits` directives.

The validator fails before packaging if either path is missing, the two inputs
are no longer byte-identical, the size/hash changes, or the directive count is
not 58. This makes an upstream fix or restructuring a re-audit event rather
than silently preserving an obsolete shadow.

No complete vendor file payload appears in the package. The shadow is 1,060
bytes of original comments and zero active directives.

## Owned payload

| Path | Bytes | SHA-256 |
|---|---:|---|
| `SKSE/Plugins/SkyPatcher/leveledList/zz Ensrick Cloak Balance/Ensrick - Cloak Balance.ini` | 11,305 | `6A51AA41BD0B4E5B5102141171785B7CACD34DBB8EF60EBB8B246ABA5AA1E47A` |
| `SKSE/Plugins/SkyPatcher/outfit/Headgear/RMB SPID - Core Definitions.esp.ini` | 1,060 | `A8AC4627CAF91DB255295F0EA54AD79748DF695897E84F4D94AFBF34E21BF2D9` |

The leveled-list file's rules are behaviorally unchanged. Its comments now
correct two forensic errors: SkyPatcher does not guarantee lexical `zz` order,
and B6C-B74 cover thirteen hold-guard outfits while the separate
`MQ304StormcloakOutfit` overlap receives B69.

Archive:
`Ensrick-Cloak-Distribution-Balance-2026-09-04.1.zip`, 12,865 bytes,
SHA-256
`5B36DB0301DB6759E83C342A938279935BB30B68D8B1D8EB32F0C22C2B1D81BD`.

The archive uses stored members, sorted POSIX paths, a fixed timestamp and
fixed Unix mode. Two independent builds were byte-identical.

## Reproduction and regression gates

From the repository root:

```powershell
py -3 audit/cloak_duplicate_shadow.py `
  --vendor-root "<RMB Core 6.3.0 Data-root>" `
  --verify-only

py -3 -m unittest discover -s audit -p 'test_*.py' -v

py -3 audit/cloak_duplicate_shadow.py `
  --vendor-root "<RMB Core 6.3.0 Data-root>" `
  --output "dist/issue-200/Ensrick-Cloak-Distribution-Balance-2026-09-04.1.zip"
```

Eleven tests pass. They cover exact-input acceptance, non-identical-source and
identical-pair hash drift, directive-count drift, an active-directive/exact
owned-file-set gate, comment-only owned-file hash drift, unexpected owned files,
immutable-snapshot packaging under a reproduced concurrent mutation, explicit
rejection of a complete vendor payload embedded in an owned file, and
byte-identical archives. CI runs the same suite.

## Exact live acceptance test

This candidate has not touched the MO2 profile. When the user authorizes the
install and no game/user/other assistant owns the profile:

1. Acquire the profile claim and update the existing
   `Ensrick - Cloak Distribution Balance` entry in place. Do not add a second
   mod and do not edit RMB Core. The owned entry must have higher MO2 file
   priority than RMB Core.
2. Run `py -3 audit/file_conflicts.py <isolated-output-directory>`. This is the
   **deterministic acceptance gate**. In the
   report, the exact Headgear path must have winner
   `Ensrick - Cloak Distribution Balance`, SHA-256 `A8AC4627...`; its losing
   RMB provider must be `B3AA37FA...`. The sibling `outfit/Cloaks` path must
   still resolve to RMB Core at `B3AA37FA...` with no owned replacement.
3. Run the normal `py -3 audit/launch_verify.py` gate. In the newly written
   `SkyPatcher.log`, both the Cloaks and Headgear virtual paths must be read
   once, with no parse failure. The effective Headgear provider is already
   proven directive-free by step 2; the Cloaks provider contains 58 rules.
4. Run this **probabilistic behavior smoke test** on a **new disposable save**,
   not the September 2 character. It supplements rather than proves the
   deterministic provider result in step 2. At the console
   enter `tcai`, then `player.placeatme 0001BCD8 20`. This base is
   `EncBandit01Melee1HNordM`; vanilla assigns target outfit `0C0197`, to which
   the legitimate injector adds B5F once. Select each new actor and run
   `showinventory`. Acceptance: no actor has more than one item resolved from
   the CoS/Pelts cloak pools. With one list entry, the result is zero or one;
   two results indicate the duplicate path is still active.
5. Still in the disposable session, enter `player.placeatme 00099CE5 10`.
   This is `GuardWhiterunCityGeneric`, assigned target outfit `0D33C6`/B73.
   Acceptance: each new guard has no more than one visually full cloak. A
   shoulder collar/mantle is recorded separately and is not counted as a full
   cloak.
6. Toggle `tcai` back and discard the test save. Do not run `ResetInventory`
   on the real save: it removes added, removed and calculated inventory and is
   not an automatic migration strategy.

If steps 2-3 pass but an actor in step 4 carries two newly rolled cloak-pool
items, stop and re-audit; do not compensate by adding another chance or reset
rule.

## Scope boundary

This candidate fixes only the objective duplicate execution (116 outfit-list
pushes down to the intended 58). It does not make an unapproved choice about
collar-only Sons of Skyrim outfits, overhaul cloak visuals/physics, or erase
inventory already persisted in old saves.
