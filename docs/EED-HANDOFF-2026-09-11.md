# EnsrickEquipmentDisplay: handoff, 2026-09-11

Written when the Fable session's model quota ran out mid-R3-close-out. Everything
below is verified on disk, not recalled. **Nothing is "finished": the user has not
seen the mod in game.**

Entry points: issue [#269](https://github.com/Ensrick/skyrim-mod-assistant/issues/269)
(the build), [#36](https://github.com/Ensrick/skyrim-mod-assistant/issues/36) (the
rules the build implements), `docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md`
(the spec), and the receipts under `records/source-builds/ensrick-equipment-display-*.json`.

---

## 1. What this is

The user's own replacement for Immersive Equipment Displays, which is dead on
runtime 1.7.104 (its framework repo was deleted; audit
`docs/IED-REBUILD-FEASIBILITY-2026-09-10.md`) and whose author is excluded
(`docs/EXCLUDED_AUTHORS.md`, 2026-09-10). User directive, verbatim: *"Revive IED,
make our own version."* Then: *"Well, finish it."*

It also has to replace **Simple Dual Sheath** (50049) and, later, **SSE Display
Tweaks** (34705), because both are by the same excluded author and both are still
installed. Exclusion rule 1: the function is replaced first, then the mod comes out.
Those two are the only rows preflight still reports, and they are expected.

**Repo:** `skyrim-tools-source/EnsrickEquipmentDisplay`, branch `main`, remote
`github.com/Ensrick/EnsrickEquipmentDisplay` (private). Worktrees
`-r2` and `-r3` are spent; they can be removed with `git worktree remove`.

**Licence: GPL-3.0-or-later** as of tree commit `522862b` (0.5.2), by the user's
decision on 2026-09-11 (#277). It statically links CommonLibSSE-NG and carries
Ersh's OAR API headers, both GPL. Do not reintroduce an MIT claim.

## 2. Where it got to

| Milestone | State | Receipt |
|---|---|---|
| R0 phase-2 verification | done; found the Load3D loader-thread trap | `...-phase2-r0.json` |
| R1 display of carried weapons | verified, 0 crashes in 4 launches | `...-r1.json` |
| R2 limit = slots, pickup refusal, packed daggers | verified, 18/18 on a live actor | `...-r2.json` |
| R3 staff rule, ESL stash, Walking Stick parity | verified, 55/55 twice | `...-r3.json` |
| **R4 (next)** | **not started** | -- |

Tree `main` is at `522862b`; the last verified build is **0.5.1** (`edd2c06`),
plus the licence commit on top, which changes no code.

**Proven in game** (headless, private desktop, fresh characters): every carried
weapon appears at its slot; the slot board refuses a pickup when nothing is free
and leaves the item in the world with a HUD line; two daggers pack hidden; a
weapon hides while drawn and returns when sheathed; a staff takes a free hand
(off-hand first) and goes to the long-term stash on unequip, on a two-handed
equip, or on arrival with both hands taken; overflow goes to the stash, not the
floor; sitting hides the hand display and standing restores it; the two Walking
Stick OAR conditions register and evaluate, confirmed in OAR's own log. Zero
crashes across twelve launches.

**Never verified, and only the user can do most of it:** how any of it *looks* on
the body; NPC displays; the swimming and riding gates; save/load persistence.

## 3. R4, the remaining milestone

From the spec's milestone table (14-22 h): co-save serialization so hand state and
overrides survive a reload; texture swaps on fresh loads; the scabbard split; a
first-person option; NPC polish; performance counters; then **remove Simple Dual
Sheath** and re-verify, which is what finally clears one of preflight's two rows.
After that, the user plays it and says whether it looks right. That play session
is the acceptance gate for the whole project.

## 4. How to run a verification launch

Read `records/source-builds/ensrick-equipment-display-r2.json` and the R3 receipt
first; the drivers are in `records-work/eed-r0-ui.ps1` and in each snapshot.

1. Claim: `py -3 audit/claim.py acquire --owner <you> --purpose "..." --ttl 90 --wait 3600`,
   then **renew every 30 minutes**. An expired claim reads as abandoned and another
   session will take it.
2. Never launch on the user's desktop. `audit/launch_skyrim_isolated.ps1` only:
   private desktop, muted clone profile, `LocalSaves=true`. The user clicks into any
   game window he sees.
3. Fresh character through Skyrim Unbound via MenuPilot. Never the old Adventurer3
   saves (#262, #268). Wait for Unbound's gear hand-out, which lands ~13 s after
   "Begin", before running a scenario.
4. Honour the human-at-controls guard (#164). Check processes with PowerShell
   `Get-Process`, never Git Bash `tasklist /FI`.
5. Leave the mod **disabled** at exit, regenerate the weapon-balance and full-cloak
   proofs for the resulting plugin count, and confirm preflight is back to the two
   expected rows.

## 5. Traps already paid for

- **Load3D runs on the loader thread** with a half-built skeleton. Marshal display
  work to the main thread through SKSE tasks, or you will measure a tree with the
  nodes missing.
- **Never `AddTask` from inside a task.** The engine drains its task queue until
  empty each frame, so a self-requeuing task hangs the game. Written into the
  tree's `docs/DESIGN.md`.
- **Reproducible builds:** an incremental link reuses the PDB and bumps its age,
  which `/Brepro` folds into the image; and CommonLibSSE-NG embeds absolute
  checkout paths. Both are fixed and gated by CTest (`reproducible_link`,
  `no_checkout_path`). Only ever launch clean-build bytes, hash-checked against
  the receipt.
- **No modal anything.** The DLL imports no USER32 at all, enforced by
  `no_modal_imports`, by building CommonLibSSE-NG from the fork branch
  `ensrick/no-modal-fail-v6.7.1`. A hidden MessageBox is what froze the game on
  2026-09-07 (#254).
- **Plugin-order drift (#253)** re-drifts on every MO2 GUI exit. Check before a
  launch, restore against the vetted manifest.

## 6. Open, and the user's to answer

1. **18 leftover build directories**, ~60 GB, all named
   `build/relwithdebinfo-se-only.bak.v*` under `EnsrickEquipmentDisplay` (6) and
   `EnsrickEquipmentDisplay-r2` (12, including the 0.4.4 pair). Every build is
   reproducible from its commit and the hashes are in the receipts. He has been
   asked to approve deleting them as a **named list**, never a wildcard sweep
   (global rule 1: no recursive deletes).
2. **Nexus upload** of the mod, when it is finished, needs its own authorization.

## 7. Related open issues

`#269` build, `#36` rules, `#270` Walking Stick adoption (held until the framework
is live), `#277` licence (answered; close it when the user confirms), `#273`
audio-thread AV seen once and never since, `#262` fresh-save stability acceptance,
`#253` order drift, `#94`/`#201` closed as superseded.
