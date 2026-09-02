# MO2Headless 0.2.0 deployed build record

Date: 2026-09-01

Status: built from fork source on GitHub Actions, regression tested in a
disposable instance, deployed to the live instance, pinned in `toolchain.json`.
Supersedes `docs/MO2-HEADLESS-BUILD-2026-08-28.md` (0.1.0 at 3769ece).

## Why

`docs/PROCESS-AUDIT-2026-08-30.md` F0/F2/F13, issues #105, #91, #103: four
plugins were unstarred twice in one day by LOOT sorts driven from worktree
copies of the tooling, a `--replace` reinstall hoisted MCM Helper to the top
of the priority order, and nothing stopped an older controller build from
mutating the live instance. The fixes below live in the controller so no
script copy, old or new, can reintroduce them.

## Provenance

- Repository: `Ensrick/modorganizer`, branch `ensrick/headless-controller`
- Commit: `6ed40ae7` - "Headless: preserve plugin activation across run, stamp
  controller build, keep priority on --replace" (on top of `3769ece0`)
- Build sequence (committer epoch, what the version stamp compares): `1788305193`
- GitHub Actions run: `33571039440` (`build.yml`, workflow_dispatch), Qt 6.11.1
  (mob.ini), same minor as the instance's `Qt6Core.dll`
- Artifact: `modorganizer` -> `mo2-builds/headless-core-33571039440-6ed40ae7/`

## What changed in the controller

| Change | Behaviour | Refs |
|---|---|---|
| `run` preserves plugin activation | Snapshot of the active set under the instance lock before the child starts; after exit every previously-active plugin that still exists is re-enabled (child keeps ORDER); a plugin the child dropped but that still exists is appended; one whose mod is gone is reported as `missing`. Journaled as `run-preserve-plugins`; result carries `stateDelta` {activeBefore, activeAfter, restored, appended, missing, newlyActive, orderChanged, transaction}. `--no-preserve-plugins` opts out. A timed-out child now returns JSON (exit 75) so the restore still runs. | #105, #73, F0/F2 |
| Instance version stamp | Every mutating verb writes `headless/controller.version` {version, hash, sequence, stampedAt, command}. A controller whose `sequence` is lower than the stamp's refuses with exit 78 and a clear JSON error; `--allow-older-controller` overrides and leaves the newer stamp. `status` reports `controllerBuild` + `instanceStamp`; `--version` prints the build. | #105 F0 |
| `--replace` keeps the row | Priority and enabled state of the replaced mod are preserved unless `--priority` / `--enable` / new `--disable` are given; result carries `replaced`, `previousPriority`, `previousEnabled`. | #91 F13 |

## Regression (disposable instance, never the live one)

Script: scratch `controller_test.ps1` with `FakeMO.exe` (a C# stand-in for
`ModOrganizer.exe headless-run` that rewrites `plugins.txt` like a LOOT sort:
markers stripped, order reversed, optional plugin dropped, exit code chosen).

Result on build `6ed40ae7` (0.2.0): **39 of 40 checks pass.**

| Group | Checks |
|---|---|
| version / init / stamp | `--version` carries hash + sequence; `init` writes `headless/controller.version`; `status` reports matching build and stamp |
| `run` preservation | 3 active plugins survive a child that strips every marker and reverses the order (activeBefore/After 3/3, `restored` 3, `orderChanged` true, journaled); `loadorder.txt` follows the child's order; a plugin the child dropped but that still exists is appended and active again; a failing child (exit 7) still restores; `--no-preserve-plugins` really drops the markers; a child that outlives `--timeout` returns exit 75 JSON with `stateDelta` |
| `--replace` (#91) | reports `previousPriority`; the row keeps its priority and enabled state; `--disable` disables; `--priority 0` still honoured; a fresh mod still goes to the top |
| version stamp | a stamp with a higher sequence refuses with exit 78 and names both builds; `--allow-older-controller` overrides and leaves the newer stamp; read-only verbs unaffected; `--dry-run` still refuses |
| audit | clean |

The one failure: a previously active plugin whose mod was disabled BEFORE the
run, and which the child left in `plugins.txt`, is re-enabled instead of
reported as `missing` (the restore only checked existence for rows the child
removed). Fixed in `fa8cb528` (0.2.1, "restore markers only for plugins still
in the effective tree"), build run `33589364228`, artifact downloaded to
`mo2-builds/headless-core-33589364228-fa8cb528/` (`MO2Headless 0.2.1 (build
fa8cb528fbb2, sequence 1788321827)`, SHA-256
`C9753382FA3BCD021937AADAFAC59409DD2DD80BDD55011C1B08270CAC851B04`): the same
regression passes **40 of 40** at 23:58. Not deployed - the smoke below ran on
0.2.0, and the deployed state stays the verified one until the next
`launch_verify` covers 0.2.1 (morning checklist).

## Deployment

Under the instance work claim (`harden-project-2`, 23:05), with no
SkyrimSE / MO2Headless / ModOrganizer / skse64_loader process alive:

| Step | Result |
|---|---|
| artifact `MO2Headless.exe` | `MO2Headless 0.2.0 (build 6ed40ae74272, sequence 1788305193)`, SHA-256 `E484A21C5CB58410B38679C35275BA805E42B4D22B3D5A91E4EEBB65C95E2DB4`; artifact `Qt6Core.dll` 6.11.1.0 = instance 6.11.1.0 |
| instance copy | `mo2-instances\skyrim-se\MO2Headless.exe` replaced; the 3769ece binary (`FEBD3C0A...`) kept beside it as `MO2Headless.exe.bak.v3769ece` |
| first stamp | `plugin-disable Ensrick-Deploy-Stamp-NoSuchPlugin.esp` (changes nothing, stamps): `headless/controller.version` = `6ed40ae74272` / `1788305193` at 04:05:48Z |
| `toolchain.json` | `tools.mo2` re-pinned: root/path/sha256/guiPath/guiSha256 -> the new build dir, `controllerVersion` 0.2.0, `commit` `6ed40ae742727dffe0deadf4eae01847eac31b11`, `githubActionsRun` 33571039440 |
| `mo2-builds` | `headless-core-33024105521-3769ece0` left in place (pin moved off it); `MO2-2.5.2-headless-23de14e2-full` remains the README-only tombstone from #105 |

## Live checks after deploy

- `status`: ok, `controllerBuild.hash` = `instanceStamp.hash` = `6ed40ae74272`
- `audit`: ok, no errors
- `plugin-list`: 235 plugins, 231 active (unchanged by the deploy)
- `mod-list`: 308 mods
- `install_mod.py --verify`: `0 problem(s)` (the JSON contract the audit scripts read is unchanged)
- `preflight.py`: clean
- first live mutations through the new build: `mod-enable "Light Placer"`
  (transaction `20260902T040611304Z-adf6b75b4bcf`) and, after its validation
  launch failed on the DLL itself, `mod-disable "Light Placer"`
  (`20260902T040821246Z-9f247bd920d9`); both journaled, both stamped
- first live `run` through the new build: the 23:10 smoke launch
  (`launch_verify` direct chain, `MO2Headless --timeout 0 run skse64_loader.exe`);
  stamp now reads `command: run` at 04:10:28Z; 231 active plugins before and
  after, so no `run-preserve-plugins` transaction was needed

No game process was launched for these checks; the launch smoke is recorded
separately in `CHANGELOG.md` (hardening package 3/3).

## 0.2.1 deployment (2026-09-02 09:14, morning-ops)

Under the instance work claim (`morning-ops`, purpose `controller 0.2.1
deploy`, 09:14:47), with no SkyrimSE / MO2Headless / ModOrganizer /
skse64_loader process alive (checked immediately before the swap). The
team-lead's 09:13 verification launch (`records/launch-verify-20260902-091326.md`,
PASS on 0.2.0) had released the claim.

| Step | Result |
|---|---|
| artifact `MO2Headless.exe` | `MO2Headless 0.2.1 (build fa8cb528fbb2, sequence 1788321827)`, SHA-256 `C9753382FA3BCD021937AADAFAC59409DD2DD80BDD55011C1B08270CAC851B04` (matches the 23:58 download); artifact `Qt6Core.dll` 6.11.1.0 = instance 6.11.1.0 |
| instance copy | `mo2-instances\skyrim-se\MO2Headless.exe` replaced; the 0.2.0 binary (`E484A21C...`) kept beside it as `MO2Headless.exe.bak.v6ed40ae7` (the 3769ece backup is still there too) |
| first stamp | `plugin-disable Ensrick-Deploy-Stamp-NoSuchPlugin.esp` (`changed: false`): `headless/controller.version` = `fa8cb528fbb2` / `1788321827` / `0.2.1` at 14:14:47Z |
| `toolchain.json` | `tools.mo2` re-pinned: root/path/sha256/guiPath/guiSha256 -> `mo2-builds/headless-core-33589364228-fa8cb528`, `controllerVersion` 0.2.1, `commit` `fa8cb528fbb220fc6e79e1dfb5b5705f5c2ba728`, `githubActionsRun` 33589364228, `githubArtifactDigest` `BA551DC9...`; `TOOLCHAIN.md` row updated; `records/source-builds/mo2-headless-0.2.1-fa8cb528.json` written |
| `mo2-builds` | `headless-core-33571039440-6ed40ae7` left in place (pin moved off it) |

Live checks after deploy: `status` ok, `controllerBuild.hash` =
`instanceStamp.hash` = `fa8cb528fbb2`; `audit` 0 errors, 0 warnings;
`plugin-list` 236 plugins, 232 active; `mod-list` 314 mods (the counts moved
since the 0.2.0 deploy because of the overnight staging, not the controller);
`install_mod.py --verify` `0 problem(s)`; `preflight.py` exit 0 (2 warnings:
Steam overlay unverifiable, claim held by morning-ops).

Launch smoke on 0.2.1: `launch_verify --claim-owner morning-ops` PASS at 09:16:22
(`records/launch-verify-20260902-091622.md`: main menu 30.4 s, save loaded
41.3 s, 32 SKSE plugins checked, 0 refused) through the direct chain
(`MO2Headless --timeout 0 run skse64_loader.exe`); the stamp now reads
`command: run` / `fa8cb528fbb2` at 14:15:36Z and 232 plugins stayed active.
The 0.2.0 binary stays beside it as the rollback (`MO2Headless.exe.bak.v6ed40ae7`).
