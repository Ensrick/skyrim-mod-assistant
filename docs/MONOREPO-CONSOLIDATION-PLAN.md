# Skyrim repository consolidation plan

Tracker: [GitHub issue #30](https://github.com/Ensrick/skyrim-mod-assistant/issues/30)

## Decision

`skyrim-mod-assistant` is the owner-facing monorepo and control plane for the
modpack. It owns the roadmap, policy, decision records, audit tooling,
publication-safe metadata, generated-patch source, test fixtures that we have a
right to publish, and reproducible build recipes.

Consolidation does not mean copying every third-party codebase, game asset,
Nexus archive, or locally built binary into one repository. Upstream forks keep
their own histories and licenses. The monorepo records a pinned dependency and
the reason it exists; it may use a submodule or external-source manifest where
that materially improves reproducibility.

## Current repository map

| Checkout | Role | Planned treatment |
|---|---|---|
| `skyrim-mod-assistant` | Modpack control plane | Keep as the canonical public repository. |
| `modorganizer` | Source fork for background MO2 control | Keep as a separate fork; pin and document its build here. |
| `zedit-headless` | Source fork for the zMerge worker | Keep as a separate fork; pin and document its build here. |
| `skse64` | Runtime/tooling fork | Keep separate while derived from upstream and preserve its history/license. |
| `SKSE64Plugins` | RaceMenu/SKEE source work | Keep separate pending license review; reference private build provenance here. |
| `MCM-Helper` | Third-party native dependency | Keep separate; repair/rebuild on a dedicated branch and pin it here. |
| `MergeMapper` | Conditional third-party runtime | Keep separate; do not adopt merely because it is available. |
| `sse-build-resources` | Shared native build dependency | Keep separate and pinned. |
| `nexus-local-curator` | Owner-authored Nexus workflow | Migrate reusable, non-secret source into this monorepo after a history and license review. |
| `skyrim-body-framework` | Owner-authored experimental framework | Review ownership and maturity, then import under `projects/` if it is truly modpack-specific. |
| `skyrim-tooling-research`, `skyrim-tools-source`, `skyrim-tools-builds`, `mo2-builds`, `mo2-instances` | Working storage rather than public repositories | Keep outside Git; reference only hashes, manifests, and reproducible recipes. |

Temporary `_rebuild_*` directories are working checkouts, not projects. They
must not be treated as authoritative source or imported until the corresponding
changes are committed to the proper fork.

## Intended monorepo layout

```text
skyrim-mod-assistant/
  audit/          read-only profile, archive, plug-in, and runtime checks
  collections/    public, source-only collection manifests
  docs/           decisions, roadmaps, testing, and handoff records
  mods/           original mod and generated-patcher source
  ports/          asset-free private-port recipes and provenance
  projects/       other owner-authored Skyrim components after review
  records/        hashes, licenses, installed-state facts, and test evidence
  scripts/        reproducible orchestration and build entry points
  tests/          publication-safe automated tests and fixtures
```

## Migration gates

1. Identify the owner, upstream, license, dirty state, secrets, binaries, and
   third-party assets for every candidate checkout.
2. Commit or preserve outstanding work in its existing repository before any
   history rewrite or physical move.
3. Import only owner-authored, publication-safe material. Preserve history when
   it has engineering or attribution value.
4. Replace copied third-party payloads with source URLs, pinned revisions,
   checksums, and build instructions.
5. Run secret, license, large-file, and redistribution checks before publishing.
6. Update the monorepo dependency manifest and archive the superseded owner
   repository only after links, builds, and documentation resolve correctly.

## Never commit

- Nexus API keys, temporary download links, browser state, or credentials.
- Bethesda game files, Creation Club files, saves, crash dumps, or personal INI
  state.
- Nexus archives, extracted third-party assets, or generated derivatives whose
  permissions do not explicitly allow redistribution.
- Live MO2 instance/profile state or Vortex deployment state.
- Local build output merely because its source is open; publication requires a
  reproducible build, dependency notices, and an explicit license review.

## Operational rule

The monorepo records a single authoritative status for every modpack decision:
`idea`, `researched`, `approved`, `installed`, `validated`, `held`, or
`rejected`. Only explicit user approval advances a mod to `approved`; only a
transactional profile change advances it to `installed`; and only recorded
testing advances it to `validated`.
