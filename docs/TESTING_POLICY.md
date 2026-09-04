# Skyrim build verification and save policy

The user is the playtester, not the test harness. Automation must establish
that the build launches, initializes, creates a fresh character, exercises the
changed feature where practical, survives a save/load round trip and produces
diagnostic evidence. The user then judges feel, appearance, balance and the
emergent defects scripted tests are poor at noticing.

## Default: a new disposable character for every verification batch

No disposable character or save is reused across build fingerprints. This is
the default even for an asset-only change because it removes ambiguity and is
cheap once automated.

There are two separate lanes:

- **Disposable acceptance lane.** A genuinely new game/character for the
  current build. This is the technical source of truth.
- **Campaign compatibility lane.** A backed-up long-lived save used only to
  test a specifically supported migration. Passing it does not replace the
  disposable test, and failing it never licenses destructive save cleaning.

An old save is especially unfit for diagnosing Papyrus `None` calls, stale
properties, aliases, leveled-list contents, MCM registrations or serialization
because it carries historical state from builds that no longer exist.

## Mandatory fresh-save changes

A fresh character is non-negotiable after any of the following:

- adding, removing, updating, enabling or disabling a plugin;
- Papyrus scripts, SKSE DLLs, serialization, MCM, quests or aliases;
- SPID, SkyPatcher, KID, BOS, CDF or leveled-list/distribution changes;
- races, NPC templates, perks, spells, inventories or progression rules;
- worldspaces, cells, navmesh, persistent references or alternate-start logic;
- generated animation, BodySlide, grass cache, xLODGen, TexGen, DynDOLOD or
  Occlusion output;
- a mod author or LOOT instruction which says “new game required”;
- removing or downgrading anything whose state may already be baked into a
  save.

The campaign lane is attempted only after the disposable lane passes and the
change is documented as update-safe.

## Verification stages

Each batch has a unique build fingerprint (profile files, ledger, effective
plugin order, watched configuration and owned-artifact hashes) and a unique
fresh-character ID.

| Stage | Automated criterion | Failure means |
|---|---|---|
| V0 static | profile reconciliation, Keep coverage, masters/order, LOOT, DLL admission, patch freshness and package/provenance gates pass | do not launch |
| V1 boot | real main menu in under 60 seconds; no modal/popup; all expected SKSE plugins finish loading | build is not viable |
| V2 fresh start | select **New Game**, observe SKSE `kNewGame`, reach a controllable fresh character/Skyrim Unbound state, and assign a new test ID | initialization/alternate start is broken |
| V3 feature probes | execute the issue's deterministic scenario and assert logs/forms/config/results | change is unverified |
| V4 round trip | make a uniquely named disposable save, exit cleanly, relaunch and load that exact save successfully | serialization/save compatibility is broken |
| V5 log diff | archive SKSE/Papyrus/mod logs and compare with the accepted baseline; zero new crash, missing-master, refused-DLL, stack-dump or clamp signatures | regression remains open |
| V6 soak | bounded idle/travel/combat repetition proportional to risk | stability claim is premature |
| V7 human play | user evaluates visual quality, feel, balance and unscripted interactions | record observation on an issue |

V1 alone is only a loader smoke test. V2–V5 are the minimum technical
acceptance for a normal plugin/config change. Native serialization and crash
fixes require repeated V2–V4 cycles; issue-specific matrices can demand ten or
more. Asset-only work still receives V0–V2 and a visual scenario, but V4 may be
recorded `not applicable` with a reason.

## Fresh-character automation contract

The harness must use the game's own main-menu **New Game** flow; loading a
copied “clean save” is not a fresh game. MenuPilot can read the selected main
menu entry and send engine-layer input without stealing focus. The driver must:

1. query and verify the selected entry before every `Accept`;
2. navigate specifically to `$NEW`, never by a blind fixed count;
3. handle only recognized confirmation dialogs and otherwise stop safely;
4. require LaunchProbe's `kNewGame` event;
5. wait for a documented ready signal from Skyrim Unbound/RaceMenu rather than
   assuming a timer means control exists;
6. attach a random test ID to the save name and test record;
7. leave no pending MenuPilot command file for the next launch;
8. exit through the game's menu, never kill a session a person has touched.

Until the V2 driver is implemented and acceptance-tested, a report may say
`V2 MANUAL`, but it may not call an old-save autoload a fresh-character pass.

## Diagnostics owned by automation

Every run archives, with timestamps and hashes:

- LaunchProbe and MenuPilot timelines;
- `skse64.log`, Crash Logger output and every loaded SKSE plugin log;
- Papyrus log with counts grouped by signature and originating mod/script;
- Community Shaders compilation/error logs and shader-cache identity;
- FSMP/Pandora/OAR distribution/animation logs when relevant;
- LOOT report, active plugins, active file/record conflict reports;
- the exact test commands, expected observations and actual observations;
- process exit, main-menu/new-game/save/load timings and the final verdict.

Known noise is an explicit, versioned allowlist with issue links. Thresholds
never hide a new signature. The CDF `429496728x` clamp warning, missing script
classes, stale Papyrus property bindings and DLL refusal are failures, not
“warnings we usually see.”

## When the user should test

Ask the user to play only after V0–V5 pass or when a visual/feel decision is the
specific remaining test. Give a short route and expected observation, not a
console-debugging assignment. Their report becomes an issue or evidence on an
existing issue; automation then reproduces and diagnoses it where possible.

## Saves and rollback

Before any launch, retain bounded backups with a manifest. Disposable saves
are isolated from campaign saves and can be deleted only by the retention
policy after their verification record is durable. Never clean, resave or
overwrite the campaign save to make a mod update appear compatible. A failed
migration restores the backup and remains an open issue.

Related: `docs/MOD_LIFECYCLE.md`, `docs/CURATION_POLICY.md`,
`audit/launch_verify.py`, `audit/launch_triage.py`, `audit/human_presence.py`
and issue #102.
