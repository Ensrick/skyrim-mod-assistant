# Crash256 recovery: current-profile verification refresh

**Later follow-up:** [BTPS control-map repair](BTPS_CONTROLMAP_REPAIR_2026-09-09.md)
now documents a concrete native fix and targeted save/cold-reload verification.
The maintenance results below remain valid; their original-crash pending status
is superseded by that report, not by these freshness checks alone.

This is prerequisite maintenance, not a claim that the original input crash
has been fixed. No new third-party mods or balance choices were introduced.

## Verified installations

- Weapon balance: 383 inputs, 3,504 WEAP overrides, 47 masters, all 16 explicit
  rules resolved. Two builds match ESP/report/all 27 localized sidecars.
  Semantic comparison permits only Speed changes. All 4,225 target/preserve
  rows pass the final-provider/speed audit. Installed freshness passes.
  ESP remains `52A5E2C4…E48D12`; only metadata changed. Final managed priority307
  was restored in transaction `20260909T075550797Z-b72d8a16c58b`.
  Install: `20260909T170040731Z-cb6cd2b1fa13`, same enabled mod/priority246.
- Cloak exclusivity: 384 plugins, 8,975 ARMO and 4,473 ARMA declarations;
  240 unchanged directives, 576 model paths, 569 parsed present meshes,
  seven previously tracked absences, zero parse errors or slot58 partition
  collisions. Forty winning SkyPatcher configs inspected. Installed check
  returns no errors. Install `20260909T170235928Z-78e0fb62e9f6`, priority295.
  This neither adds physics nor removes spare NPC inventory.

Receipts: `records/source-builds/ensrick-weapon-speed-balance.json` and
`records/source-builds/ensrick-full-cloak-exclusivity.json`; corresponding
installed-ledger rows updated. Local logs/artifacts are under
`records-work/crash256-weapon-*`, `records-work/crash256-cloak-20260909`, and
`mods/weapon-balance/artifacts/crash256-weapon-nested-20260909`.

## Background-tool fault and containment

The first normal MO2Vfs tool run displayed an **Elevation required** Steam
advisory. This violated the no-popups requirement. Only the owned MO2 process
was terminated; no elevation was accepted and Steam was not restarted.
No patch output was installed from that attempt. MO2's original INI was restored.

`audit/QuietWorker.cs` now launches a suspended worker on a private desktop,
assigns it to an outer kill-on-close job and an inner breakaway-compatible job,
then resumes it. MO2 `spawn.cpp` explicitly requests CREATE_BREAKAWAY_FROM_JOB.
A single prohibiting job made its spawn fail with access denied5; the nested
design permits leaving the inner job while retaining outer containment.
This follows [Windows nested-job semantics](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs).
No desktop switch, OS input, elevation, or global settings change is involved.

`audit/run_weapon_refresh_isolated.ps1` owns a temporary remembered **No / Continue
without elevation** response for that specific Steam advisory, runs the build
or final audit, and restores/verifies the original INI bytes with bounded retries.
Direct worker invocation outside its private desktop is rejected. Strict UTF8
decoding rejects unsupported input rather than corrupting temporary configuration.
Before-image SHA256: `DFE909806CECF03AB08ACA4115C348DC9CF62671E33EE7B80AD600D3EBD8E615`.

Tests verify private-desktop placement, child exit7 propagation, cleanup of
ordinary and explicit-breakaway children, timeout124, and direct-worker refusal.
Real MO2 generation and final audit succeeded on the private desktop. A bounded
read-only Fable5 review identified restoration-race, argument-validation and
writable-command-buffer concerns; these were addressed. The final hardened
wrapper's containment tests were rerun. Timeout124 is reserved by this wrapper;
it is not a general distinction from an arbitrary child deliberately exiting124.
Job termination is asynchronous, which is why restoration retries are required.

Windows restarted at 03:19:35 local during follow-up commands; their interrupted
exits are not Skyrim crash evidence. After resumption, no owned game/worker was
running and the MO2 INI matched its before-image. Latest Skyrim crash report
still dated September8 23:26. Packaging and cloak checks then completed.

## Remaining scope

The latest removed-script/Papyrus failure and the original September7 input
failure are distinct. Fresh-game/cold-load success does not certify a damaged
older save, combat, transactions, focus transitions, or representative-world
stability. Currency native0.2.2 has its own runtime acceptance report.
CRF/Lux resolver choice, missing ledger coverage and remaining Papyrus warnings
are not waived by these two green maintenance checks. Saves and vendor assets
remain untouched; local generated record/translation outputs are not published.
