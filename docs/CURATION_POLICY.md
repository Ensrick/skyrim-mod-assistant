# Nexus curation state policy

Effective 2026-08-30, revised 2026-09-02, the three practical states are:

- **Keep**: at least one file from that Nexus mod page is **installed** in the
  current `Default` MO2 profile. Enabled or disabled does not matter. Keep is
  the inventory of what this build carries, not a wishlist or a candidate
  shortlist.
- **Skip**: the user has explicitly rejected the mod for the current modpack.
- **Unreviewed**: the mod is not installed and has not been rejected. It may be
  weighted, deferred, under investigation, awaiting dependencies, awaiting a
  patch, or simply not reviewed yet.

Research and a favorable recommendation do not create a Keep entry. The normal
adoption sequence is explicit user approval, archive/licence audit, headless
installation and enablement, verification, and only then Keep plus removal of
the selected mod's author from Excluded. If an installed mod is **removed from
disk**, clear Keep back to Unreviewed unless the user separately chooses Skip.

## Installed implies Keep (user, 2026-09-02)

*"Make sure that our processes and procedures doctrine makes adding to keeps
necessary for installed mods."*

**Adding the Keep is a required step of installing a mod, not a follow-up.**
An install that has not produced its Keep is an incomplete install, in the same
way that an unverified launch is an incomplete change.

The rule and its two corollaries:

1. **Every installed mod directory that resolves to a Nexus id carries a Keep**
   for that id, whether or not the mod is enabled in the profile. Disabling a
   mod - parking it for a rebuild, superseding it with a source build or an
   Ensrick overlay, holding it behind an overlap check - does **not** clear its
   Keep. The mod is still in the build; only its activation changed.
2. **A Skip must not be installed.** If a mod is rejected, its directory leaves
   the MO2 mods tree: move it to `mo2-instances\_archived-rejects\<name>` and
   drop its line from `modlist.txt`. Never delete it, and never resolve the
   conflict by flipping the user's Skip to Keep.
3. **Our own artifacts have no Nexus id and therefore no Keep.** `Ensrick - *`
   overlays and patches, `* Native Overlay - Ensrick` rebuilds, source builds,
   and harness mods (`LaunchProbe`, `MenuPilot`, `Pandora Output - Ensrick`)
   are exempt. Where a rebuild sits above a vendor row, the vendor row is the
   one that carries the Keep.

Why the revision: the previous "installed **and enabled**" definition silently
dropped 14 mods out of the Keep list the moment they were parked, superseded,
or held for an overlap check - so the curator stopped describing what the build
actually contains, and re-browsing a parked mod on Nexus showed no decision at
all. Audit that found it: `records/keep-install-audit-2026-09-02.md`.

**The Keep goes at the END of a successful install, never before it.**
`install_mod.py` queues it as its last step for a reason: a Keep applied ahead
of its install makes the curator claim something the build does not have, and on
2026-09-02 it deadlocked two agents - one could not launch because the gate saw
a Keep with nothing installed, and the other could not install because the first
held the profile claim. Download, install, verify, then Keep.

**The gate:** `py -3 audit/keep_coverage.py` is the enforcement. It fails when
an installed Nexus id has no Keep, when a Keep has nothing installed, or when a
Skip is installed. It runs inside `audit/preflight.py`, so a batch cannot reach
a verification launch with the Keep list out of step - with one deliberate
asymmetry: inside the LAUNCH gate a Keep with nothing installed is a WARNING,
because it puts no files in the tree and cannot affect a launch, while a Skip
that IS installed and an install that produced no Keep stay blocking. The
standalone gate remains strict on all three. `audit/install_mod.py`
prints the Keep obligation for every id it installs.

For a mod that adds weapons, shields, armor, clothing, undergarments, or
jewelry, adoption also opens a mandatory item-by-item integration record under
`docs/EQUIPMENT_INTAKE_POLICY.md`. Keep still means the approved vendor mod is
installed; it does not imply that unresolved balance, lore role, or
distribution choices were silently decided.

The live curator is reconciled against MO2 state with
`nexus-local-curator/scripts/reconcile-installed-keeps.py`. That controller
still reads the **enabled** set, so its "clear inactive Keeps" half is now
wrong under this policy - use it for the "set missing Keeps" half only, or use
`audit/keep_coverage.py --plan`, until the controller is updated. Queued
mutations use compare-before-write guards and map cleared Keeps to Unreviewed,
never to Skip.

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

## Textures are judged at distance, not zoomed in (user, 2026-09-02)

"A lot of modded textures look really nice when zoomed in completely, but then
completely lose all texture when you zoom out. The vanilla textures, despite
being lower res, often have better design and overall detail when you zoom
out." Acceptance for any texture mod (skin, armor, architecture, landscape):

- Evaluate at mid and far camera distance, i.e. at mip 2-4, not at mip 0.
- The asset inspector's mip-retention metric (high-frequency energy at mip 2-4
  relative to mip 0, compared against the vanilla texture it replaces) is the
  receipt; a screenshot is not.
- Matte, single-tone at distance is a defect even when the close-up is good.
- A texture that fails can be salvaged by an Ensrick mip-regeneration recipe
  (sharpened mip chain) before it is rejected.
