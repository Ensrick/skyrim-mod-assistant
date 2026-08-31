# Verification and test plan

The first release is an instrumented test candidate. Verification is layered so
pure mathematics, package integrity, engine integration, and long-session save
safety can be evaluated independently.

## Test environments

Record these inputs for every game test:

- Skyrim executable and distribution;
- SKSE version;
- Address Library package/database;
- Windows version and CPU architecture;
- exact Bounded Encounters commit and package SHA-256;
- configuration, seed, load order, and mod-manager profile;
- whether the save is new, existing, or disposable; and
- Crash Logger version and resulting report, if any.

The initial supported environment is defined in
[Runtime compatibility](compatibility.md).

## Automated unit tests

The pure model test binary must cover:

- zero growth at and below the baseline;
- exact expectations at representative levels;
- linear rather than compound growth;
- `maxMultiplier`, per-source, category-cell, and global-cell caps;
- disabled and excluded categories;
- deterministic repeatability for the same seed/source/level;
- one stable per-source threshold producing monotonic uncapped outcomes across
  increasing levels;
- different source identities producing independent fractional thresholds;
- stable per-source results when source order changes before cap saturation;
- no overflow or non-finite result at boundary values;
- malformed JSON, unsupported schema, invalid radii, and inconsistent hostile
  caps failing closed; and
- observe-only parsing, non-empty official source allowlisting, and
  case-insensitive plugin-list uniqueness;
- a statistical sweep whose sample mean remains within a documented tolerance
  of the expected fractional outcome.

Run through CTest in Release mode. Warnings are errors.

## Simulator checks

For every shipping configuration:

1. execute the simulator at source counts `1`, `4`, `8`, `16`, and `64`;
2. inspect levels `1`, `5`, `10`, `20`, `30`, `40`, `50`, `75`, and `100`;
3. confirm sampled additions never exceed any applicable cap;
4. confirm expected totals are monotonic until capped;
5. repeat with the same seed and byte-compare output; and
6. change only the seed and confirm expectations stay fixed while at least some
   fractional outcomes change.

Archive the smoke output as a CI artifact.

## Static artifact checks

- clean checkout with recursively pinned submodules;
- pinned vcpkg baseline and no network-fetched unpinned source;
- Release build produced with reproducibility flags;
- x64 PE DLL and simulator executable;
- expected SKSE exports and plugin metadata;
- no imports or strings for `MessageBox` or other intentional modal UI;
- no Bethesda, Nexus, Address Library, save, or log payload;
- only expected archive paths;
- shipping JSON validates against `BoundedEncounters.schema.json`; parser tests
  also cover documented cross-field and finite-runtime constraints that plain
  JSON Schema cannot fully express;
- shipping JSON has `observeOnly: true` and only the five official masters in
  `allowedSourcePlugins`;
- sorted SHA-256 manifest verifies every packaged file;
- SPDX SBOM parses as JSON and names the source commit;
- the binary archive contains CommonLibSSE-NG `COPYING` and `EXCEPTIONS.md`;
- every direct vcpkg dependency has packaged license text and a reviewed SPDX
  identifier;
- the matching deterministic CommonLibSSE-NG corresponding-source archive,
  manifest, and archive hash are present and identify the exact Ensrick fork
  build commit and its upstream `v7.0.0` base;
- two packages built from the same inputs and `SOURCE_DATE_EPOCH` are byte
  identical; and
- package SHA-256 recorded in the GitHub prerelease.

## Headless runtime smoke test

Where an isolated harness is available, test plugin query/load against the exact
supported runtime and matching Address Library. The test must not display a
window, play audio, write into the user's active MO2 profile, or launch the game
on the user's interactive desktop. A harness is not a substitute for an actual
game test.

## In-game functional matrix

Use a dedicated disposable MO2 profile with only required dependencies, a crash
logger, a reproducible test save, and the candidate enabled. Run the entire
classification matrix first with `observeOnly: true`; verify that `created=0`
in every cell audit. Only then repeat the actor-creation scenarios with
`observeOnly: false` on a disposable save.

| Scenario | Expected result |
| --- | --- |
| Level at/below baseline | No added actors. |
| Ordinary bandit leveled sources | Bounded additions; companions independently resolve from the original list when available. |
| Fixed generic hostile | No additions in the initial safety candidate. |
| Animals/beasts | Lower category curve and cap. |
| Giants/mammoths | Strict category curve and cap. |
| Dragon encounter | No additions. |
| Named/unique NPC | No additions. |
| Essential/protected/quest-alias actor | No additions. |
| Summoned/commanded/teammate actor | No additions. |
| Location boss | No additions. |
| Denied source plugin | No additions. |
| Unallowlisted override or leveled-list entry | Source graph rejected before creation. |
| Mod-authored source absent from allowlist | No additions. |
| Reviewed mod-authored leveled source in allowlist | Bounded additions; experimental compatibility evidence only. |
| Repeated cell-load signal | No recursive or repeated growth. |
| Dense interior/exterior | Category, addition, and total-hostile ceilings hold. |
| Placement near walls/ledges | No actor embedded in geometry; failure is skipped and logged. |

At least one test should use a mod-added leveled list and one a scripted quest
location, even though the latter should be excluded.

## Save and lifecycle matrix

Perform with generated actors alive, dead, in combat, and out of combat:

1. save, quit to desktop, relaunch, and load;
2. quick-save/quick-load repeatedly without leaving the cell;
3. make two saves in different cells and revert between them;
4. cross interior/exterior boundaries during combat;
5. wait long enough for a cleared cell to reset, then revisit;
6. start a new game without restarting the process if supported;
7. disable the plugin after a clean save/quit and load the disposable save; and
8. inspect the save for generated dynamic references and missing forms.

Acceptance criteria are listed in
[Spawn lifecycle and save safety](save-lifecycle.md).

## Performance and endurance

- sample frame time before and after entering a dense cell;
- capture scan duration, eligible-source count, planned count, successful count,
  skipped placements, and cap reasons from structured logs;
- verify no per-frame scan or unbounded queue;
- traverse at least 30 mixed cells in one session;
- run a minimum two-hour combat/travel session before beta promotion; and
- run multiple ordinary play sessions totaling at least 20 hours before a
  stable Nexus release.

Memory and actor counts should return toward baseline after leaving/resetting
processed cells. Any monotonic growth blocks release.

## Exit criteria

### GitHub alpha test candidate

- automated tests and simulator pass;
- static artifact checks pass;
- exact runtime gate and logging verified;
- x64/SKSE export and forbidden modal/focus/process/audio import audit passes;
- package manifest/SBOM generated; and
- CommonLib GPL/exception texts and corresponding-source artifact generated;
- known risks disclosed in the prerelease notes.

### Nexus beta

- all functional scenarios pass on the supported runtime;
- save/lifecycle matrix passes on disposable saves;
- no unexplained crash-logger findings; and
- at least two hours of endurance testing completed.

### Stable

- at least 20 cumulative hours on representative gameplay profiles;
- no unresolved save-integrity, recursion, cap, or crash defects;
- reproducible tagged artifact and verified manifest; and
- documentation matches the shipped schema and behavior.
