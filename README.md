# Skyrim Mod Assistant

Auditable, source-only automation for a Skyrim Special Edition modding
toolchain. The repository records toolchain decisions, launches checksum-pinned
tools without opening interactive windows, and keeps reproducible local recipes
for generated compatibility patches and private ports.

## Publication boundary

This repository contains only original scripts, documentation, configuration
examples, and factual audit metadata. It does **not** contain Bethesda game
files, Nexus downloads, third-party binaries, generated ESP files, converted
meshes or textures, deployment manifests, logs, or private build output. See
[`REDISTRIBUTION.md`](REDISTRIBUTION.md) for the full policy.

The deny-by-default `.gitignore` is intentional: this checkout may coexist with
a private working tree, but only the reviewed allowlist can be committed.

## Included workflows

- `run-headless-tool.ps1` verifies pinned SHA-256 values before launching LOOT,
  Synthesis, or Spriggit with redirected logs.
- `run-through-mo2.ps1` runs those tools, including the source-built zMerge
  Headless worker, through an audited MO2 profile and refuses ambiguous
  forwarding to an already-running MO2 process.
- `mods/katana-two-handed` documents and audits a generated, load-order-aware
  katana patch. The patcher itself is maintained in
  [KatanaTwoHandedPatcher](https://github.com/Ensrick/KatanaTwoHandedPatcher).
- `mods/bounded-encounters` contains the source-built Bounded Encounters SKSE
  population framework, deterministic simulator, tests, and reproducible
  release tooling. Its first test candidate ships in observe-only mode.
- `ports/lost-longswords` records a private, asset-free port recipe and its
  validation criteria. It does not grant or imply redistribution permission.
- `records/restricted-mods.json` is the machine-readable redistribution ledger.
- `NEXUS_API.md` records the non-secret Nexus credential lookup and read-only
  metadata/download procedure used by the local tooling.
- `collections/draft-manifest.json` is the reviewed source-of-truth for the
  private collection while Vortex's generated working state remains local.
- `docs/TEXTURE_POLICY.md` defines the source-matched resolution budget: at
  most one justified step upward, a 1K cap for dedicated small clutter, and an
  absolute 4K-per-axis ceiling.
- `docs/EQUIPMENT_INTAKE_POLICY.md` requires an item-by-item role, balance,
  acquisition, permission, patch-ownership, compatibility, and verification
  record for every adopted weapon, armor, clothing, or jewelry mod.
- `docs/MODPACK-ROADMAP-2026-08-28.md` indexes the playable-baseline roadmap and
  its canonical GitHub issues.
- `docs/MONOREPO-CONSOLIDATION-PLAN.md` defines this repository's role as the
  Skyrim modpack control plane without absorbing unlicensed third-party work.
- `docs/MCM-PERSISTENCE-2026-08-28.md` defines how save-local MCM choices and
  file-backed settings become reproducible across characters and profiles.
- `docs/WILDLIFE-WOLVES-2026-08-28.md` records the vanilla spawning evidence
  and the cross-worldspace generated-patch design for non-routine wolf combat.
- `docs/ENCOUNTER-POPULATION-2026-08-28.md` audits the current dynamic-spawn
  candidate and defines the allowlist-first population requirement.

## Local setup

1. Install or build each external tool under its own license.
2. Copy `toolchain.example.json` to the ignored `toolchain.json`.
3. Replace every example path and hash with the audited local value.
4. Run PowerShell 7 with an explicitly selected disposable profile first.

Example:

```powershell
pwsh ./run-headless-tool.ps1 loot -- --game SkyrimSE --help
```

The scripts fail closed when a tool is absent or its checksum differs. They do
not download software, assets, or mods.

## Safety status

The public surface deliberately excludes older local Vortex purge and xEdit
master-cleaning scripts. Those scripts are machine-specific and mutate game
files; they require generalization, dry-run support, and dedicated tests before
they are suitable for publication.

## License

The original source in this repository is licensed under the MIT License.
Third-party software and content remain governed by their respective licenses
and permissions.
