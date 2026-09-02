# Skyrim Toolchain Decision Record

Audited: 2026-08-27 (America/Chicago)

## Selected stack

| Role | Selection | Pinned source | Background status |
|---|---|---|---|
| Mod/profile manager and VFS | Mod Organizer 2 2.5.2 + MO2Headless 0.2.1 | `Ensrick/modorganizer@fa8cb528` (GUI still `3769ece`) | Source-built; transactional JSON controller and USVFS launcher are fully background-safe; since 0.2.0 `run` preserves plugin activation and emits `stateDelta`, every mutation stamps `headless/controller.version` and an older build refuses a newer-stamped instance, `--replace` keeps priority; 0.2.1 fixes the stale-row edge case (a plugin whose mod was disabled before the run is reported `missing`, not re-enabled), regression 40/40, deployed 2026-09-02 09:14 from `mo2-builds/headless-core-33589364228-fa8cb528/` with 0.2.0 kept as `MO2Headless.exe.bak.v6ed40ae7` (`docs/MO2-HEADLESS-BUILD-2026-09-01.md`) |
| Load-order metadata and sorting | MO2 LootCLI 1.8.0 + libloot 0.29.6 | `Ensrick/modorganizer-lootcli@c455fe0` + `Ensrick/libloot@136f398` | Source-built, tested, and hidden-launch ready; designed for MO2's virtual filesystem |
| Record editor, inspection, cleaning | xEdit 4.1.5q source | `Ensrick/TES5Edit@fd1e360` | Source and every recursive submodule pinned; build blocked on a user-licensed Delphi 12 toolchain |
| Reproducible patch pipelines | Synthesis 0.36.5 | `Ensrick/Synthesis@e585f45` | Built and tested; hidden CLI supports `run-pipeline` |
| Plugin text serialization and review | Spriggit 0.41.0 | `Ensrick/Spriggit@8edce84` | Built and tested; hidden CLI supports deterministic serialize/deserialize |
| NIF inspection and LE-to-SE conversion | local `nif-port-cli` + current nifly | `Ensrick/nif-port-cli@c69d745` (PRs #2 and #3 merged; upstream `ousnius/SSE-NIF-Optimizer@dbba8b3`, `nifly@846518b`) | Source-built, fully headless, fail-closed conversion with post-save reload validation; explicit `convert-sse --headparts` asserts dynamic geometry, while `--se-eye-shaders` normalizes and verifies the SE eye convention; inspection exposes shader flags and packed eye data; 52/52 DDS Workshop 0.3 base NIFs preserved shape names, geometry, skinning, bones, and texture paths in an audit conversion |
| Texture downscale / recompress for the texture-cap overlays | texconv (DirectXTex) 2026.4.1.1 | winget `Microsoft.DirectXTex.Texconv` 2026.3.31, pinned by path + SHA-256 in `toolchain.json` (`tools.texconv`) | Stock Microsoft binary; every texture-cap ledger row records its per-file command, input hash and output hash (#160) |
| Installed-master record inspection | local `skyrim-record-cli` + Mutagen 0.54.3 | `Ensrick/skyrim-record-cli@1f3c8d9` | Source-built, fully headless JSONL inventory and selected-field export used for balance and semantic conflict checks |
| Katana conversion and balance | local `KatanaTwoHandedPatcher` + Synthesis 0.36.5 / Mutagen 0.54.2 | local source | Source-built, fully headless load-order patcher with conservative detection and explicit include/exclude settings |
| Conditional plugin merging | zMerge Headless 0.6.7-headless.1 | `Ensrick/zedit@fd8df93` | Source-built JSON worker; zero visible UI; inventory, validation, and external-output builds tested through MO2 |
| Programmatic MO2/plugin control | houseCARL 1.9.0 | `Ensrick/houseCARL@6386941` | Built, audited, and staged; deliberately not installed into live Codex/MO2 yet |

Exact executable paths and SHA-256 values are recorded locally in the ignored
`toolchain.json`; `toolchain.example.json` documents its public shape.

## Supersession decisions

- **zEdit** is not the general-purpose core. Its last published version is 0.6.7
  (2022), so our fork packages only zMerge automation as a fail-closed JSON
  worker. Production builds cannot display the legacy desktop interface,
  networking is blocked, and native dependencies are rebuilt from pinned source.
- **zMerge** is available but is not our default merge strategy. Skyrim SE's ESL/ESL-flagged
  plugins remove much of the old need to merge plugins, and merging can obscure
  provenance and complicate updates. Our source build can inventory, validate,
  and build externally without changing the profile. MergeMapper 1.6.1 is
  current, Apache-2.0, source-buildable, and statically 1.7.99-compatible, but it
  is conditional runtime infrastructure rather than a reason to merge. The
  profile contains no adopted zMerge output, so MergeMapper remains uninstalled.
  Reviews: `docs/ZMERGE-HEADLESS-REVIEW-2026-08-27.md` and
  `docs/MERGEMAPPER-REVIEW-2026-08-27.md`.
- **Mator Smash** is not our unattended conflict-resolution core. It has no
  comparably current, well-tested source/headless path.
- **Wrye Bash** remains useful for a Bashed Patch when leveled-list/import-tag
  behavior is actually needed, but its programmatic/headless Bashed Patch work is
  unfinished. It is an optional, supervised tool rather than part of automation.
- **LOOT desktop** remains useful for an interactive report. MO2's LootCLI is the
  better automation component because it is the sorter MO2 itself invokes. Our
  build pairs it with source-built libloot 0.29.6, newer than LOOT desktop
  0.29.1.
- **Synthesis does not replace xEdit.** Synthesis owns reproducible specialized
  patchers; xEdit owns deep record inspection, manual conflict resolution, and
  supported cleaning.
- **Spriggit is not a conflict patcher.** It gives generated/manual plugins a
  diffable, reviewable text representation and reproducible provenance.

## Validation completed

- MO2Headless: full and core source builds plus formatting checks passed;
  redirected help, version, invalid-option, and missing-command probes returned
  with no window; a disposable Steam Skyrim SE instance passed profile/mod/plugin
  operations, deterministic FOMOD installation, byte-exact rollback,
  snapshot/apply, unmanaged DLC preservation, audit, USVFS exit propagation,
  a five-process hidden-window observation, and preservation of a single
  `SKSE/Plugins` Data-root staging tree. The real katana archive audited
  cleanly, and source-built LootCLI produced an 81-plugin sorted list and a
  41,749-byte report through the virtual filesystem.
- Synthesis: 426 unit tests passed, 1 skipped; all 48 integration tests passed;
  dependency vulnerability scan clean.
- Spriggit: 129 core tests passed, 1 skipped; all 11 Windows/plugin tests passed;
  dependency vulnerability scan clean.
- Spriggit Skyrim fixture: ESP -> YAML -> ESP -> YAML produced identical text-tree
  digests when the plugin basename was preserved.
- Lost LongSwords NIF audit: the 2024 upload's 12 meshes were proven to remain
  LE stream 83; the local converter produced stream-100/BSTriShape output and
  successfully reloaded all converted meshes without unknown blocks.
- Lost LongSwords record audit: the local inspector loaded the installed
  Skyrim.esm and generated plugin, allowing balance comparison against the
  actual game master rather than external tables.
- Katana patch: all 14 installed Skyrim/Dawnguard/Creation Club targets passed
  field-level assertions; two successive headless runs produced the same SHA-256;
  Spriggit's checked text round-trip passed.
- houseCARL: 109/109 CI probes plus its freshness/capture guard passed; a hidden
  stdio MCP handshake returned protocol `2025-03-26` and 45 tools; dependency
  vulnerability scan clean.
- libloot 0.29.6: 1,124 Rust tests and all 1,798 C++ wrapper tests passed on
  Windows.
- LootCLI: source build passed; a direct hidden failure test returned exit 1,
  and an end-to-end Skyrim SE run produced a sorted list and JSON report whose
  runtime stats identify LootCLI 1.8.0 and libloot 0.29.6.
- Hidden launcher: Synthesis and Spriggit help invocations completed without a
  visible window and wrote separate stdout/stderr logs under
  `records/tool-runs`.
- zMerge Headless: 7 contract tests and the complete pinned native source build
  passed; bare launch, MO2 inventory, validation, and a disposable build all had
  zero window handles. The build produced 51 hashed files outside the profile;
  post-build plugin membership exactly matched the pre-build inventory.

## Security hardening

The released Synthesis and Spriggit dependency graphs contained packages with
known vulnerabilities when restored today. The forks pin direct, current
versions and were rebuilt and retested:

- Synthesis: `System.Security.Cryptography.Xml` 10.0.10.
- Spriggit: `Microsoft.Build.Tasks.Core` 18.8.2,
  `Microsoft.Build.Utilities.Core` 18.8.2, and
  `System.Security.Cryptography.Xml` 10.0.10.

Draft pull requests preserve the changes and their validation:

- `Ensrick/Synthesis#1`
- `Ensrick/Spriggit#1`

## Remaining compiler gate

xEdit upstream recommends Delphi 12 and depends on IDE-installed Project
Magician, DDevExtensions, JCL, JVCL, VirtualTrees, and FileContainer packages.
There is no Delphi compiler/license on this workstation. Community Edition also
has eligibility and license terms that only the user can accept. The source is
ready, but no source-built xEdit binary will be claimed until that toolchain is
legitimately installed and the result is tested.

The current published xEdit 4.1.5f binary is retained only as an operational
fallback. It is not represented as a source build of 4.1.5q.

## Operating policy

- Every background executable is checksum-pinned before launch. The MO2
  controller, GUI executable, and distributable archive are pinned separately.
  Electron workers also pin `app.asar` and native companions because their EXE
  is a generic host and does not identify the application code.
- Runs use hidden processes and per-run logs.
- Writes target a new patch/output location by default.
- No live MO2 profile or Codex plugin registration is changed until the selected
  Skyrim instance/profile is known and a dry-run audit succeeds.
- LOOT and xEdit must run through the chosen MO2 profile/VFS for a real mod list;
  invoking either directly against the physical game `Data` folder would miss
  MO2-managed files.

## Game launch (2026-08-23)

The Steam Play button IS the modded launch: Skyrim SE's Steam LaunchOptions
(userdata\250855163\config\localconfig.vdf, backup .bak.v2026-08-23 beside it)
run `mo2-instances\skyrim-se\ModOrganizer.exe "moshortcut://:SKSE" %command%`,
so Steam starts MO2 portable, which mounts the VFS and runs the SKSE entry
(#1 in customExecutables). Steam shows "Running" while MO2/game are open -
normal. Revert: clear Launch Options in game Properties or restore the backup.
Never launch the game from a shell; edits to localconfig.vdf require Steam to
be fully exited first (steam.exe -shutdown).

## Post-launch triage + update watch (2026-08-23)

After EVERY launch attempt: `py -3 audit/launch_triage.py` - parses skse64.log
for refused plugins and scans fresh per-plugin logs for error lines. The SKSE
stack logs everything; the failure mode was nobody reading it.
`py -3 audit/plugin_watch.py` - polls the 1.7.99-blocked pages (Engine Fixes,
RaceMenu, PapyrusUtil, JContainers, SKSE) and prints NEW when files appear;
state in records/plugin-watch.json. When a page updates: install the new
build, re-enable the parked MO2 mod, rerun triage on next launch.
