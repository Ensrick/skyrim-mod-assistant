# Handoff — Codex to Claude — 2026-08-29

## Purpose

This is the current operational handoff for the Skyrim SE/AE modpack project.
It supersedes the execution order in the 2026-08-26 and 2026-08-27 handoffs
where the later roadmap, compatibility sweep, and runtime records disagree.
Older handoffs remain useful as historical evidence only.

The user is actively reducing the Nexus **Keep** list and will continue to run
mod ideas past the assistant. Keep that conversation responsive while longer
engineering work runs in isolated worktrees or delegated agents.

## Non-negotiable owner rules

- Do not install a mod merely because the user asks about, compares, or likes
  it. Installation requires an explicit request.
- When the user explicitly elects to try a mod, add it to Keep and remove its
  author from the exclusion list if necessary. Do not broaden that approval to
  other files or mods.
- Do not infer incompatibility from `for ENB` in a title. Inspect the actual
  current requirements, variants, description, and payload. Community Shaders,
  Effects 11, and dual-use assets make names unreliable compatibility signals.
- Do not modify author-supplied mod directories. Local DLLs, configurations,
  generated patches, and fixes belong in separately named Ensrick MO2 overlays
  with provenance, hashes, licensing, and rollback boundaries.
- Resolve content conflicts with owned, reproducible patches. Prefer ESL flags
  when technically safe. Bring genuine winner/design decisions to the user.
- Never bundle or publish restricted vendor assets. Track exact external
  downloads and permissions. A public modpack may reference author-hosted
  downloads and separately distribute only reviewed Ensrick-owned outputs.
- Avoid modal dialogs, visible helper windows, audible errors, or other desktop
  disruption. Background tooling must be truly headless and errors must return
  to the agent. Builds run hidden, at low/idle priority, and with capped
  parallelism.
- Do not launch Skyrim or foreground GUI tools unless requested. The user's
  eyes are the acceptance gate for display, lighting, interaction, and gameplay.
- Preserve unrelated dirty work. Do not clean, reset, overwrite, or fold it into
  another commit without establishing provenance.

## Repository and runtime state

- Repository: `C:\Users\danjo\source\repos\skyrim-mod-assistant`
- Active branch: `ensrick/modpack-roadmap-2026-08-28`
- Committed HEAD: `14f3e20bb41793e079aa2dbf7d1841941ce333b6`
  (`audit active profile semantic conflicts`)
- HEAD is 14 commits ahead of `origin/main` and zero behind.
- Runtime target: `SkyrimSE.exe` 1.7.104.0.
- MO2 instance: `C:\Users\danjo\source\repos\mo2-instances\skyrim-se`
- Active profile: `Default`.
- Latest independent equipment scan: 96 enabled MO2 mods, 99 active plugins,
  30 parsed masters, zero parse errors or unresolved FormKeys.
- Do not derive counts with a naïve `*`/`+` line count: profile files contain
  comments and implicitly loaded Bethesda/Creation Club entries.

### Dirty root — preserve and classify before committing

Modified:

- `BASELINE.md`
- `audit/install_mod.py`
- `docs/CS_FEATURES.md`
- `docs/DATED-IDEA-BANK.md`
- `docs/KEEP_REVIEW.md`
- `records/installed-mods.json`
- `records/restricted-mods.json`

Untracked:

- `docs/DISPLAY-UNBOUND-LIGHTING-FIXES-2026-08-28.md`
- `docs/VENDOR-INTEGRITY-2026-08-29.md`
- `docs/HANDOFF-2026-08-29-CODEX-TO-CLAUDE.md`
- `records/synthesis/water-seams-fix/README.md`
- `records/synthesis/water-seams-fix/settings.json`

Known coherent groupings, not permission to commit blindly:

1. ENB-title/Community-Shaders doctrine and Water for ENB decision:
   `BASELINE.md`, `docs/CS_FEATURES.md`, `docs/KEEP_REVIEW.md`, and the related
   ledger/restriction additions.
2. Headless installer path correction: `audit/install_mod.py` now resolves the
   executable from the production instance instead of an old validation build.
3. Display, Unbound, and HDR fixes: the untracked display document plus related
   effective configuration/ledger changes.
4. Vendor-integrity audit: the untracked vendor document; no normalization has
   been performed from this audit.
5. Water seam synthesis evidence: the untracked `water-seams-fix` directory.
6. Idea decisions from the present conversation: `docs/DATED-IDEA-BANK.md`.

Review the actual diff and provenance before splitting these into commits.

## Current compatibility work

### Existing Lux/Water patch — installed, do not replace

`Ensrick Lux Water CS Patch.esp` is the existing generated 559-record water
patch. It remains enabled and requires foreground acceptance under GitHub issue
#46. Do not disable, replace, or collapse it casually.

### General compatibility patch — built in isolation, not installed

GitHub issue #47 Decision A was approved for implementation. An implementation
agent produced a separate 14-record override-only patch on:

- Worktree: `C:\Users\danjo\source\repos\_agent_worktrees\skyrim-issue-47`
- Branch: `agent/issue-47-compat-patch`
- Initial commit: `d7589e7fb287ceb7b643c1511dda1c8830532da1`
- Review-reconciliation commit:
  `0e4dd924fb87bfc23eec0903a5422dadd44a6b63`

It contains 12 WRLD and two CELL overrides, introduces no forms, carries the
ESL flag, and passed deterministic generation, link/master/record audits,
Spriggit round-trip, packaging, and build checks. It was not installed, pushed,
or promoted.

Independent review approved the record selection and required reconciliation:

- retain the 559-record Lux/Water patch and load the new patch after it;
- declare `Lux Orbis CS.esp` as a hard semantic/binary master, producing the
  natural seven-master set;
- preserve an explicit LOOT rule after the existing Ensrick water patch;
- record exact input hashes and expected field values against the 99-plugin
  profile; and
- document Sovngarde and both CELL overrides as intentional ITM assertions that
  automatic cleaning must not remove.

The reconciliation is complete. The final patch has the exact seven-master
order, retains the explicit rule after the existing Lux/Water patch, pins the
99-plugin inputs and reviewed expected values, and documents all three
intentional ITMs. Final deterministic artifacts:

- ESP SHA-256:
  `ADAED3D2704F98E491773284F3BEE0C480FA72088F5D519D4566EC784B906334`
- Spriggit tree SHA-256:
  `D71650F7DA239C89C797F068A50AF7B6BAFB502823C3DAC6BB44EDE0CF183DA0`
- Package SHA-256:
  `3A633723CFE528BB7A8647334920CEA965C2BA232E661342A6684B1817246163`
- Expected-values evidence SHA-256:
  `73B8C750AA78E044F0242235E9E7901F6036298CE07A2E2327E29309AF794E08`

Two byte-identical generations, 374 selected-field checks, 48 final-water
checks, 62 link checks, Spriggit round-trip, package audit, locked restore/build,
self-test, formatting, parsing, and dependency-vulnerability checks passed.
There is one non-fatal pre-existing compiler/analyzer-version warning, CS9057.
The worktree is clean. Nothing was installed, promoted, pushed, or launched.

Decision B from issue #47 — a union `Underwear.ini` overlay — remains a separate
owner choice and is not approved by the compatibility-patch implementation.

## No Mere Bandits equipment catalog — built in isolation, not integrated

The user retained **No Mere Bandits** as a major late-stage flagship project in
the ongoing effort against generic Skyrim. Full faction/spawn/location work is
deferred until the mod list is substantially settled, but equipment tracking
must begin now.

An agent created the catalog foundation on:

- Worktree: `C:\Users\danjo\source\repos\_agent_worktrees\equipment-catalog`
- Branch: `agent/equipment-catalog`
- Commit: `fa3f73a3d828af583075e92bfde8ea6ac3ab49d0`
- Catalog SHA-256:
  `7671E2B242238FD2EC06342C75E271F52C8EFC8806B17E81C3F4D450F8A47170`

Coverage at generation time:

- 96 enabled MO2 mods and all 99 active plugins inspected;
- 30 equipment-relevant sources;
- 3,283 armor and 1,029 weapon records;
- 2,263 items with material-keyword signals;
- 1,945 items found in leveled lists and 203 in outfits;
- 1,118 items with crafting or tempering recipes;
- zero aesthetic/faction/region/power-tier/encounter-role decisions invented.

Five deterministic tests, cross-process hash-seed reproducibility, a
byte-identical live-profile rebuild, semantic validation, and JSON Schema
validation passed. The branch deliberately used committed ledgers and did not
absorb newer dirty-root facts.

Review before integration. Important extensions still needed later include
SPID/SkyPatcher/script/quest/container/placed-reference distribution, BSA and
effective-VFS asset provenance, localized strings, inherited templates, and
reviewed author/licence/redistribution facts.

The final No Mere Bandits output must be deterministic and inspectable. AI may
classify catalog items and propose faction assignments, but released NPC,
equipment, spawn, and leveled-list data must be fixed game records generated by
auditable rules, not nondeterministic runtime AI.

## Idea-bank decisions from 2026-08-29

- **The Vast Expanse:** permanently rejected after the user explored its severe
  worldspace and compatibility cost with other mod authors. Do not revisit.
- **Lost Akaviri Island:** permanently rejected. Do not revisit.
- **No Mere Bandits:** retained as described above; late-stage, modular, and
  catalog-driven. Roaming actors, equipment distribution, leveled lists, fort
  occupation, and authored ruin integration are separate systems.
- **Armor/Weapon Derivative Variants:** not rejected, but remains an unapproved
  future concept. If retained, it should be modular, purposeful, permission-
  aware, and feed the No Mere Bandits equipment catalog.

## Foreground acceptance still needed

Do not call the current setup stable until the user tests the exact effective
profile and logs are audited afterward.

Combined test targets:

1. Borderless focus and cursor behavior with `LockCursor=true`: wheel must not
   scroll a browser while Skyrim owns focus; Windows key and Alt-Tab must release
   the cursor without terminating Skyrim.
2. Skyrim Unbound Reborn: no restored cart-title flash; after RaceMenu, Enter
   should expose **Current Settings**, or the MCM's **Begin Your Adventure**
   should leave the starting room.
3. Community Shaders/Lux lighting: SDR path selected, no blown-out character
   face, and plausible normal-interior range.
4. Existing Lux/Water patch: inspect seams, interior boundaries, waterfalls,
   transitions, underwater entry/exit, reflections, and Lux lighting in cells
   containing water.
5. Native/runtime stack: Proteus, ConsoleUtil, RaceMenu/SKEE, JContainers,
   PapyrusUtil, QuickLoot, Community Shaders, and other enabled SKSE plugins must
   initialize without refusals, modal errors, or a new crash log.

After exit, run the established launch triage and classify every current warning
under issue #37. A successful main menu alone is not gameplay acceptance.

## Vendor-integrity normalization — required before public packaging

The untracked `docs/VENDOR-INTEGRITY-2026-08-29.md` identifies in-place local
state in JContainers, RaceMenu, SKSE Menu Framework, SSE Display Tweaks, The New
Gentleman, and Skyrim Unbound Reborn. The desired end state is pristine vendor
packages below separately named Ensrick binary/configuration overlays.

No normalization has been performed from that audit. Each remediation must be
transactional: capture effective hashes, create the overlay, restore the exact
official archive, confirm unchanged effective behavior, and rerun profile,
master, ledger, and DLL-provider audits. Do not improvise replacements or alter
content-record winners during this cleanup.

## GitHub/source notes

- `Ensrick/SSEDisplayTweaks`: master branch protection was configured to block
  force-push/deletion, enforce pull-request review and conversation resolution,
  enforce admins, and require linear history. No required CI check was added
  because the repository currently has no workflow to require.
- `Ensrick/FUCK` is a legitimate automated fork of Fuzzlesz's intentionally
  named source repository for FLICK — Fuzz's Legally Intelligible Core Kit.
  Claude created it during a 1.7.99 compatibility investigation for Kaputt. The
  fork is not evidence of compromise.
- FLICK/FUCK is **not installed**: it is pinned-not-deployed, absent from the MO2
  mod directory, active mod list, and installed ledger. Its compatibility branch
  must not be confused with an active dependency.
- Skyrim-related original work should converge under the professional monorepo,
  but dirty third-party forks and repositories with distinct upstream/licence
  history must not be flattened carelessly. Follow issue #30.

## Recommended execution order for Claude

1. Read this handoff, `docs/MODPACK-ROADMAP-2026-08-28.md`, issues #23, #37,
   #46, and #47, then inspect the root status without modifying it.
2. Review issue-47 commits `d7589e7` and `0e4dd92` together with the independent
   audit. The seven-master and ordering conditions now agree. Integrate the
   branch only after code review; do not install or promote yet.
3. Review the equipment-catalog branch, refresh it only after reconciling the
   dirty ledgers, and integrate it as infrastructure—not as faction decisions.
4. Split and commit the dirty root in provenance-safe coherent units. Do not mix
   idea decisions, vendor-integrity findings, active-profile ledger changes, and
   code fixes into an opaque commit.
5. Normalize vendor-directory mutations into separate overlays while preserving
   exact effective hashes.
6. Ask the user to perform the combined foreground acceptance pass when the
   profile is in its final normalized state, then audit the logs.
7. Resume Keep-list reduction and candidate evaluation. No candidate becomes an
   install request by implication.

## Do not assume

- An isolated branch, built DLL, generated ESP, Nexus archive, Keep entry, or
  favorable research result is installed.
- The old 1.7.99 handoff order is current; the runtime is now 1.7.104.
- A dirty ledger entry is committed truth.
- A plugin called `for ENB` requires ENBSeries.
- An intentional ITM in an owned assertion patch is safe to clean automatically.
- Source availability alone grants redistribution rights for bundled mod assets.
