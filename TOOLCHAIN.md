# Skyrim Toolchain Decision Record

Audited: 2026-08-01 (America/Chicago)

## Selected stack

| Role | Selection | Pinned source | Background status |
|---|---|---|---|
| Mod/profile manager and VFS | Mod Organizer 2 2.5.2 + MO2Headless 0.1.0 | `Ensrick/modorganizer@23de14e` | Source-built full distribution; transactional JSON controller and USVFS launcher are fully background-safe |
| Load-order metadata and sorting | MO2 LootCLI 1.8.0 + libloot 0.29.6 | `Ensrick/modorganizer-lootcli@c455fe0` + `Ensrick/libloot@136f398` | Source-built, tested, and hidden-launch ready; designed for MO2's virtual filesystem |
| Record editor, inspection, cleaning | xEdit 4.1.5q source | `Ensrick/TES5Edit@fd1e360` | Source and every recursive submodule pinned; build blocked on a user-licensed Delphi 12 toolchain |
| Reproducible patch pipelines | Synthesis 0.36.5 | `Ensrick/Synthesis@e585f45` | Built and tested; hidden CLI supports `run-pipeline` |
| Plugin text serialization and review | Spriggit 0.41.0 | `Ensrick/Spriggit@8edce84` | Built and tested; hidden CLI supports deterministic serialize/deserialize |
| NIF inspection and LE-to-SE conversion | local `nif-port-cli` + current nifly | `ousnius/SSE-NIF-Optimizer@dbba8b3`, `nifly@846518b` | Source-built, fully headless, fail-closed conversion with post-save reload validation |
| Installed-master record inspection | local `skyrim-record-cli` + Mutagen 0.54.2 | local source | Source-built, fully headless JSONL export used for balance checks |
| Katana conversion and balance | local `KatanaTwoHandedPatcher` + Synthesis 0.36.5 / Mutagen 0.54.2 | local source | Source-built, fully headless load-order patcher with conservative detection and explicit include/exclude settings |
| Programmatic MO2/plugin control | houseCARL 1.9.0 | `Ensrick/houseCARL@6386941` | Built, audited, and staged; deliberately not installed into live Codex/MO2 yet |

Exact executable paths and SHA-256 values are recorded locally in the ignored
`toolchain.json`; `toolchain.example.json` documents its public shape.

## Supersession decisions

- **zEdit** is not the general-purpose core. Its last published version is 0.6.7
  (2022), its build stack is old Electron/Python 2.7-era technology, and current
  work is sparse. Keep it only when a chosen mod explicitly requires a legacy
  zPatcher or zMerge workflow.
- **zMerge** is not our default merge strategy. Skyrim SE's ESL/ESL-flagged
  plugins remove much of the old need to merge plugins, and merging can obscure
  provenance and complicate updates.
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
  snapshot/apply, unmanaged DLC preservation, audit, USVFS exit propagation, and
  a five-process hidden-window observation. The real katana archive audited
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
- Runs use hidden processes and per-run logs.
- Writes target a new patch/output location by default.
- No live MO2 profile or Codex plugin registration is changed until the selected
  Skyrim instance/profile is known and a dry-run audit succeeds.
- LOOT and xEdit must run through the chosen MO2 profile/VFS for a real mod list;
  invoking either directly against the physical game `Data` folder would miss
  MO2-managed files.
