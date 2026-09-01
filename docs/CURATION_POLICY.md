# Nexus curation state policy

Effective 2026-08-30, the three practical states are:

- **Keep**: at least one file from that Nexus mod page is installed and enabled
  in the current `Default` MO2 profile. Keep is the active load-order list, not
  a wishlist or candidate shortlist.
- **Skip**: the user has explicitly rejected the mod for the current modpack.
- **Unreviewed**: the mod is not installed and has not been rejected. It may be
  weighted, deferred, under investigation, awaiting dependencies, awaiting a
  patch, or simply not reviewed yet.

Research and a favorable recommendation do not create a Keep entry. The normal
adoption sequence is explicit user approval, archive/licence audit, headless
installation and enablement, verification, and only then Keep plus removal of
the selected mod's author from Excluded. If an installed mod is disabled or
removed, clear Keep back to Unreviewed unless the user separately chooses Skip.

For a mod that adds weapons, shields, armor, clothing, undergarments, or
jewelry, adoption also opens a mandatory item-by-item integration record under
`docs/EQUIPMENT_INTAKE_POLICY.md`. Keep still means the approved vendor mod is
installed and enabled; it does not imply that unresolved balance, lore role,
or distribution choices were silently decided.

The live curator is reconciled against enabled MO2 state with
`nexus-local-curator/scripts/reconcile-installed-keeps.py`. Its queued mutation
uses compare-before-write guards and maps inactive Keeps to Unreviewed, never
to Skip.

## Changelog discipline

Effective 2026-08-31, `CHANGELOG.md` at the repo root is part of build state.

- No change lands without a changelog entry naming its source - the user's
  words, the issue number, the agent, or the research record that caused it.
  A change with no nameable source does not land.
- No batch is called done until a verification launch passes: main menu in
  under 60 seconds and the test save loaded. Until then every entry in the
  batch stays `UNVERIFIED`.
- A `FAILED` verification makes the whole unverified pile suspect. The batch
  is bisected before anything else lands; installing forward past a failed
  launch is how the 2026-08-29 to 2026-08-31 backlog happened.

The entry format and the verification statuses are defined at the top of
`CHANGELOG.md`.

## Launch verification is the definition of done

Effective 2026-09-01 (#140). An unpark, a DLL swap, a native overlay, an INI
or runtime-config change, or a source-built mod is **not done** until a
`py -3 audit/launch_verify.py` PASS follows it - main menu within 60 seconds
of process start AND the test save loaded, with the record path
(`records/launch-verify-*.md`) named in the changelog entry. The SKSE version
gate (`audit/skse_version_data.py`) is necessary and never sufficient: Open
Animation Replacer passed it and hung the load. No agent reports "unparked" or
"swapped" as a completed item without the PASS.

Every profile-mutating step runs under the instance work claim
(`audit/claim.py`, `docs/AGENT_WORK_QUEUE.md` "Instance work claim"); a step
taken without the claim is a process fault even when the result is right.

## Source builds record their feature defaults

Effective 2026-09-01 (#144). A mod built from source ships whatever defaults
its headers carry, which is not what the upstream release carries and not
what anyone decided. At build time the build record in
`records/source-builds/<name>.json` gets a `featureDefaultsDiff` from

```
py -3 audit/feature_defaults_diff.py <upstream defaults> <built defaults> --record records/source-builds/<name>.json
```

Every entry in `changed` / `onlyInBuilt` is a decision: either it is set back
to upstream's value in the shipped config, or the changelog entry names why the
build differs. A source build with no `featureDefaultsDiff` in its record is
not installed.
