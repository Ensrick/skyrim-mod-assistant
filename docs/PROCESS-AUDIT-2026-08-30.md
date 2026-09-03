# Process and QA audit - 2026-08-30

Read-only audit of the headless Skyrim pipeline: how mods are installed,
recorded, verified and managed. Nothing was installed, enabled, sorted or
committed. Evidence was captured 2026-08-30 between 12:00 and 12:40 local
while other sessions were writing to the profile (last profile write
11:53:58, last journal entry 11:48:13 UTC-5); anything that looks mid-change
is marked as such.

Scope: repo `skyrim-mod-assistant`, MO2 instance `mo2-instances\skyrim-se`
profile `Default`, controller `MO2Headless.exe` (source
`modorganizer/headless/main.cpp` at `3769ece`), runtime SkyrimSE 1.7.104.

Severity: **blocker** = the profile is wrong right now and no tool will
notice; **high** = will silently corrupt state or lose work on the next
routine operation; **medium** = drift, waste or reproducibility gap;
**low** = hygiene.

## Numbers first

| Measure | Value | Source |
|---|---|---|
| Mod folders / modlist rows | 189 / 189 (169 `+`, 20 `-`) | `profiles/Default/modlist.txt`, `mods/` |
| Ledger rows | 173 | `records/installed-mods.json` |
| Enabled mods with no ledger row | **13** | list in F4 |
| Disabled mods with no ledger row | 3 | Water for ENB - Generated Conflict Patch, Immersive Equipment Displays, Proteus 1.7.99 Native Overlay |
| Ledger `enabled:true` but modlist `-` | 6 (all six `CS *` feature rows) | ledger vs modlist |
| Ledger `enabled:false` but modlist `+` | 1 (Proteus) | ledger vs modlist |
| Ledger `plugins` list differs from folder | 3 (Azurite III Darker Nights, Azurite III HDR, Proteus) | ledger vs disk |
| plugins.txt entries / discovered / active | 192 / 192 / 186 | `MO2Headless plugin-list` |
| Unstarred plugins with a `disabledPlugins` record | 2 (Lux Myrwatch, Lux Wraithguard: masters genuinely absent) | ledger row Lux CC Patches |
| Unstarred plugins with **no** record | **4** | F1 |
| Masters resolving only via Data (not ccc, not active) | 0 | TES4 header scan |
| `.esl` extension without ESL flag | 0; `.esp` with ESM flag: 15 (fine) | header scan |
| SKSE DLLs in enabled mods failing the version gate | 4 (all shadowed by a passing overlay) + msdia140 (not a plugin) | `audit/skse_version_data.py` logic |
| Parked DLLs that pass the gate | 2 (Community Shaders core, SSE Display Tweaks - both superseded, correctly off) | same |
| DDS over 4096 px in enabled mods | 8 files, 3 effective violations | F3 |
| Vendor folders shadowed by an overlay that are byte-identical to their archive | 7 of 7 checked | 7z CRC vs disk |
| Leftover staging + trash in instance root | 155 `.mo2-headless-stage-*` dirs, 19 GB; `.mo2-headless-trash` 15 GB | `du` |
| Journal transactions | 5,410 (5,107 are `plugin-enable`) | `headless-journal/` |

## Findings, ranked

### F0 - BLOCKER - Four checkouts of the tooling operate on one live profile; three still run the pre-fix code and a pre-fix controller

`grep -c was_active audit/install_mod.py` is 0 in
`_agent_worktrees/codex-integration` (1c89b1f), `equipment-catalog` (fd2bd7b)
and `skyrim-issue-47` (0e4dd92): all three carry the ledger-driven
`sort_order()` that caused today's silent disables. All three also hard-code
`MO2 = mo2-builds\MO2-2.5.2-headless-23de14e2-full\MO2Headless.exe`
(`18469b00...`), the controller build **before** commit 3769ece "Preserve
single Bethesda data roots during staging" - so a `mod-install` from any of
them re-creates the `SKSE\` strip defect as well. The main tree uses the
instance copy (`febd3c0a...`, 3769ece).

Evidence it already bit: after the four plugins in F1 were re-enabled at
15:15Z, a sort from one of these checkouts at 16:47Z (loot-report.json mtime
11:47:34 local, 186 `plugin-enable` journal entries 16:47-16:48Z) unstarred
them again. The 11:53:58 profile write is that sort's `run`.

Why a script fix cannot hold: every git worktree, agent clone and
`.codex-tmp` copy is an independent copy of `audit/install_mod.py` with its own
`MO2` path; nothing forces them to agree, and agents check out from whatever
commit they were spawned at.

Durable fix, in order of strength:

1. **Move enable-state preservation into MO2Headless `run`** (holds the lock
   already, `main.cpp:1704-1751`): snapshot `plugins.txt` before starting the
   child; after exit, re-read it, restore `*` on every entry that was active
   and still exists, keep the child's new order, journal the write and emit a
   `stateDelta` in the JSON. Then no script copy, old or new, can drop
   markers; LOOT's rewrite becomes an order change only. Same place is right
   for the F2 fail-closed comparison.
2. **One canonical controller path**: `run`, `mod-install` and every script
   must resolve `MO2Headless.exe` from the instance (or `toolchain.json`), and
   the controller should refuse to mutate an instance whose
   `headless/controller.version` is newer than itself (write that file on
   every mutation). That closes the 23de14e2 regression class.
3. **One canonical script path**: `install_mod.py` re-execs
   `C:\Users\danjo\source\repos\skyrim-mod-assistant\audit\install_mod.py`
   when `REPO` is not that path (or refuses), so a worktree copy cannot act on
   the live profile. Until 1-2 land: rebase the three worktrees onto the
   main-tree tooling, or forbid installs from them.

Issue: #105.

### F1 - BLOCKER - Four load-bearing plugins are off with no record, and the documents disagree about whether they should be

`profiles/Default/plugins.txt` lines 53, 78, 79, 191 are unstarred:
`PROTEUS.esp`, `QuickLootIE.esp`, `TerrainHelper.esp`,
`Ensrick Lux Water CS Patch.esp`. None has a `disabledPlugins` entry in the
ledger (Proteus's row has `plugins: []`; the other three mods have no row at
all), so `install_mod.py --verify` reports zero problems and every future
`--sort` leaves them off (`sort_order()` restores only the pre-sort active
set).

The record disagrees with itself:

- Issue #73 (2026-08-30) calls all four "deliberately disabled" and re-disabled
  them after the old sort re-enabled them (transactions `...151558286Z` to
  `...151558762Z`).
- `docs/HANDOFF-2026-08-29-CODEX-TO-CLAUDE.md` "Existing Lux/Water patch -
  installed, do not replace": "remains enabled ... Do not disable".
  `config/loot/userlist.yaml` and the General Compatibility Patch (#47) are
  built to load *after* it.
- `docs/HANDOFF-2026-08-27.md` Proteus addendum: "The Default profile now
  enables both layers and `PROTEUS.esp`"; `BASELINE.md:156-160` treats Proteus
  as the campaign pillar and says the overlay "logged loaded correctly".
  With `PROTEUS.esp` off the DLL loads but the mod is inert.
- QuickLoot IE and TerrainHelper are named in the same #73 list; no document
  records a reason for either to be off.

Fix: the user rules on each of the four. Then either `plugin-enable` them or
add ledger rows with `disabledPlugins` (create rows for the three unledgered
mods). Add to `verify()` a check that every unstarred discovered plugin has a
record (see F4). Issue: #100.

Status 12:16 local: team-lead re-enabled all four and added ledger rows for the
three unledgered mods (ledger now 176 rows); the 16:47Z recurrence came from a
worktree copy of the old sort (F0). The ruling on whether each should be on is
still owed.

### F2 - HIGH - `sort_order()` rewrite is correct on the main path but keeps four holes

`audit/install_mod.py:140-198`. Verified: the snapshot comes from
`plugin-list` (read-only, no lock, atomic reads), the empty-snapshot guard at
:166 fails closed, `restore` and `fresh` are disjoint, and LOOT's marker drop is
handled. Remaining holes:

1. **Stale parked rows still override live state** (:182-185). `deliberate`
   includes every plugin of a ledger row with `enabled:false`, and
   `restore = was_active - deliberate`. A mod re-enabled by hand whose ledger
   row was never flipped back is force-disabled on every sort. This is the
   original bug class (ledger outranks live state) narrowed to parked rows.
   Not triggered today only because all parked rows currently have
   `plugins: []` - including Proteus, whose folder ships `PROTEUS.esp`.
   Checked the overlay-pair variant (a parked base row listing a plugin that
   an enabled Ensrick overlay provides): the live `deliberate` set is exactly
   the two Lux CC patches, and no plugin basename exists in both a disabled
   and an enabled folder - the five native overlays ship DLLs only, so no such
   pair exists today. The exposure is the parked-row-with-enabled-folder case
   (Proteus), not overlays.
2. **`fresh` re-enables hand-disabled plugins** (:190-194). Any plugin of a
   ledger-enabled row that is unstarred without a `disabledPlugins` entry is
   treated as "never active" and enabled. That is exactly the semantic #73
   objects to; it only spares today's four because they have no rows.
3. **Return values ignored** (:187, :194). `mo2('plugin-enable')` can fail
   (lock contention exit 75 after 30 s, "not present in the effective data
   tree") and the summary still counts it as restored.
4. **No fail-closed comparison.** Nothing checks that the post-sort active set
   equals `was_active | fresh`; #73 acceptance items 3-5 are unmet.
5. Snapshot-to-lock window (:164 to :173): a plugin enabled by another session
   between the snapshot and MO2Headless taking `.mo2-headless.lock` for the
   LOOT run is missing from `was_active`; if its mod has no ledger row it is
   lost.

Fix: make the ledger advisory only. `restore = was_active` (drop `deliberate`
from the subtraction), keep `fresh` but restrict it to plugins whose mod
folder mtime is newer than the snapshot or that the caller names; check every
`plugin-enable` result; after restoring, re-read `plugin-list` and abort with a
delta report if `active != was_active | fresh`. Consider `snapshot` +
`apply STATE.json` (both exist in MO2Headless) instead of ~190 `plugin-enable`
processes and journal entries per sort. Posted as a comment on #73.

### F3 - HIGH - The 4096 texture cap is not enforced anywhere in the install path

`audit/install_mod.py` contains no DDS check (grep for `4096|cap|TEXTURE` is
empty); `docs/TEXTURE_POLICY.md:20-23` says every DDS is capped at 4096 on
either axis. Header scan of every `.dds` in enabled mods:

| Mod | File | Dimensions | Effective? |
|---|---|---|---|
| Baltimore Weapons | `textures/billyro/baltimore/battleaxe_d.dds`, `falchion_d.dds` | 8192x2048 | **yes** - no cap overlay exists |
| Azurite Weathers III | `textures/sky/skyrimcloudsheet01.dds`, `skyrimgalaxy.dds` | 1024x8192, 8192x4096 | **yes** |
| Community Shaders AIO | `textures/terrain/HeightMaps/DLC2SolstheimWorld...dds` | 6144x6144 | **yes** (generated terrain data) |
| Community Shaders AIO | `Shaders/ScreenSpaceGI/fast_2uges.dds` | 128x8192 | yes (LUT) |
| Bloodskal Blade 4 | `bloodskal_d.dds`, `fxglow.dds` | 8192x2048, 8192x1024 | no - shadowed by `Ensrick - Bloodskal Blade 4 Texture Cap` (modlist line 51 above 53) |

The policy also requires a GitHub issue per downscale overlay
(`TEXTURE_POLICY.md:78-85`); only the tracking issue #64 exists, none for the
Bloodskal, Quicksilver, Scale Nord or Vikings caps.

Fix: add a post-install DDS header sweep to `install()` that prints every
file over 4096 and exits non-zero unless `--allow-oversize <reason>` is given;
record the reason in the ledger row. Decide Baltimore/Azurite/CS exceptions
explicitly. Issue: #101.

### F4 - HIGH - The ledger is not the source of truth and `--verify` cannot tell

Enabled mods with no ledger row (13): Ensrick - CRF Semantic Patch, Ensrick -
General Compatibility Patch, Ensrick - Scoped Werewolf Totem Skull 98175,
Ensrick - Lux Water CS Patch, the five `* 1.7.104 Native Overlay - Ensrick`
mods, Community Shaders AIO - 1.7.99 Source Build, QuickLoot IE - Ensrick
1.7.99, Misc Effects ENB Light - Believable Weapons, Believable Weapons.
Plus the 6+1 enabled-flag mismatches and 3 plugin-list mismatches in the table
above. `verify()` (`install_mod.py:111-137`) iterates ledger rows only, so an
unledgered plugin can be disabled forever without a warning - which is how F1
happened.

Note `Believable Weapons` and `Misc Effects ENB Light` were installed from
`downloads/37737-260562.7z` and `downloads/_staging/65070-270746-rooted`
(meta.ini `installationFile`), i.e. through the normal path, and still have no
row - the row is written by `install_mod.py`, not by MO2Headless, so any
install that bypasses the script (direct `mod-install`, `mod-stage`) is
invisible.

Fix: (a) a `--reconcile` mode that walks `modlist.txt` and `mod-list` JSON,
creates stub rows (`modId: 0`, `source: local`) for every folder without one,
and flags every `enabled` mismatch and every unstarred plugin lacking a
`disabledPlugins` record; (b) run it inside `verify()`; (c) record locally
built mods with `records/source-builds/*.json` (only 3 of 12 overlays have
one - F8). Issue: #102.

### F5 - HIGH - Two sessions plus the MO2 GUI share the profile; only MO2Headless mutators are serialised

Shared state and what protects it:

| File / dir | Writers | Protection |
|---|---|---|
| `profiles/Default/{modlist,plugins,loadorder,lockedorder}.txt` | MO2Headless mutators (journaled); `ModOrganizer.exe headless-run` on every `run` (writes all five profile files, **not journaled** - the 11:53:58 write today); the Steam-launched MO2 GUI on exit | `.mo2-headless.lock` (`main.cpp:1128-1135`) covers MO2Headless only; the GUI "does not yet participate" (`headless/README.md`) |
| `records/installed-mods.json` | every `install_mod.py` in every session | none - `load()`/`save()` is read-modify-write; two concurrent installs lose one row |
| `records/plugin-watch.json`, `loot-report.json`, LOOT `%LOCALAPPDATA%` masterlist/userlist | scripts | none |
| `downloads/` | `modasset.download()` | `.part` + `os.replace`; benign |
| `docs/KEEP_REVIEW.md`, `AGENT_WORK_QUEUE.md`, `DEFERRED_DECISIONS.md` | both assistants | git only |

Specific holes:

- `run-through-mo2.ps1:107-127` refuses to run if `ModOrganizer.exe` is
  running **at the pinned `guiPath`** (`mo2-builds\headless-core-...`). The
  Steam launch path and every `run` use
  `mo2-instances\skyrim-se\ModOrganizer.exe` (different file, hash
  `f27115f4...` = the older `23de14e2` build, not the pinned `9cbd793c...`), so
  the guard never fires for the GUI that actually runs.
- `install_mod.py` has no running-GUI check at all.
- `mo2()` never passes `--lock-timeout`; the default is 30 s
  (`main.cpp:1063`) while a `run` holds the lock for the whole LOOT sort (up
  to 900 s). A concurrent install fails with exit 75; `install()` prints
  "install failed" and does not retry.
- `mod-install` writes `modlist.txt` and `plugin-enable` writes both
  `plugins.txt` and `loadorder.txt` (`main.cpp:1636-1642`, rebuilt without the
  Bethesda masters); the next `run` puts them back. Harmless but it means
  `loadorder.txt` mtime is not evidence of anything.

Fix: (1) `install_mod.py` refuses to start if any process named
`ModOrganizer.exe` exists (by name, not path); (2) take a repo-level pipeline
lock (`records/.pipeline.lock`, `msvcrt.locking`) around
download-install-ledger-sort so two sessions queue instead of racing;
(3) pass `--lock-timeout 1200000` explicitly; (4) ledger writes re-read under
the lock before merging. Issue: #103.

### F6 - HIGH (safety) - A recursive delete and a Steam kill live in tracked scripts

- `ports/lost-longswords/stage-private-port.ps1:19`
  `Remove-Item -LiteralPath $output -Recurse -Force`. Guarded (`-Clean` flag,
  path must sit under the work root) but it is exactly the construct the
  standing rule forbids; rename to `.bak.v<stamp>` instead.
- `audit/launch_skyrim.ps1:22,40` `Stop-Process -Name SkyrimSE, ModOrganizer,
  skse64_loader -Force` and `Stop-Process -Name steam, steamwebhelper -Force`
  - kills the user's Steam client and any MO2 GUI without checking what it is
  doing (an install through the GUI would be cut mid-write).
- Root-level `purge.ps1`, `clean-baseline.ps1`, `clean-master(s).ps1`,
  `finalize-clean.ps1` are Vortex-era scripts that delete files in the game
  `Data` folder and QuickAutoClean the Bethesda masters in place. Tracked by
  #1; they should move under `tools/legacy/` so nobody runs them by habit.

MO2Headless itself is clean: trash requires `--yes`, nothing is recursively
deleted, archives with `..` or absolute paths are rejected
(`main.cpp:805-815`). Issue: #104.

### F7 - MEDIUM - Path-shape sweep: the SKSE-strip class is fixed; two other shapes remain

`normalizedContentRoot()` (`main.cpp:773-807`) now refuses to unwrap a single
known Data directory. Sweep of all 189 folders: no top-level `Plugins\`, no
retained `Data\` wrapper, no stray `meta.ini` below root, no DLL outside
`SKSE/Plugins` except the CS upscaler runtime DLLs (correct location). Left:

- `Crash Logger`: `fomod/` plus `ae/`, `ae17/`, `se/`, `vr/` variant trees each
  containing `SKSE/Plugins/*.pdb` - a FOMOD installed with every branch
  (pre-dates the `--install-plan` rule; `meta.ini` points at the retired
  `%TEMP%\modassets` cache). Inert but unreproducible.
- `BodySlide and Outfit Studio`: `fomod/` left in the mod.
- `Nether's Follower Framework/Readme/*.zip` packaging junk.
- The known-data-dir list omits `SkyPatcher`, `Source`, `DialogueViews`,
  `NetScriptFramework`, `Platform`, `OpenAnimationReplacer`,
  `CraftingRecipeDistributor`, `LightPlacer`, `PBRNifPatcher`. An archive whose
  only top-level entry is one of these would still be unwrapped one level too
  high. Also: `dirs.size() == 1 && files.isEmpty()` means an archive with
  `Data\` **plus** a readme keeps the `Data\` wrapper (nothing installed that
  way today).

### F8 - MEDIUM - Overlays: vendor folders are pristine, overlays win, but 9 of 12 have no recorded recipe

CRC comparison of every file in the vendor folder against the ledger archive
(`7z l -slt` vs `zlib.crc32`): Bloodskal Blade 4, Quicksilver's Sword Pack,
Scale Nord Armor, Vikings Weaponry, Varinia, High Poly Wolf Skull, SSE Display
Tweaks Official, Baltimore Weapons, Azurite Weathers III, Proteus, PapyrusUtil
SE, ConsoleUtilSSE NG, Water for ENB, Cutting Room Floor: identical. Every
overlay sits above its vendor in `modlist.txt` (22>23, 39/40>41, 44>45, 50>71,
51>53, 68>69, 72>73, native overlays 84-88 > 131-185).

Still mutated in place (matches `docs/VENDOR-INTEGRITY-2026-08-29.md`):
RaceMenu (`skee64.dll`, `skee64.ini`, 3 `.bak` files), Skyrim Unbound Reborn
(`skyrimunbound.json` + `.bak`), The New Gentleman (DLL, `tng_mcm.pex/.psc`,
`.bak`), SKSE Menu Framework (DLL, `_preload.txt`, `.bak`), Lux CS
(`_install_choices.txt`). JContainers SE ledger row has `fileId: -2` and no
archive in `downloads/` (GitHub artifact), so its vendor state cannot be
verified against anything.

Recipes: `records/source-builds/` holds only crf-semantic-patch, lux-water-cs-
patch and werewolf-totem. The Bloodskal Static Glow, three Texture Cap
overlays and the Vikings mesh port were installed from
`AppData\Local\Temp\claude\...\scratchpad\*.zip` (meta.ini
`installationFile`), QuickLoot IE from `.codex-tmp`, CS AIO from
`_rebuild_CommunityShaders/dist`, the five native overlays from
`headless/packages/`. The ledger `note` is the only recipe. Staleness against
newer vendor uploads was not checked (`update_sweep.py` covers that; not run
here).

### F9 - MEDIUM - Records sprawl: which document owns what

| Document | Claims authority for | Reality |
|---|---|---|
| `BASELINE.md` | build manifest, slot status | Authoritative for slots, but internally stale: `:138-139` "JContainers ... PARKED", `:104-106` "RE-PARKED", `:92` "outvoted by the enabled ... overlays" (modlist: both enabled); `:150` "FSMP - in keeps - install with first physics outfit" (ledger 4.1.1 enabled, `hdtsmp64.dll` in skse64.log); `:173` renderer row names six CS feature packs that are all `-` in modlist while the ledger marks them `enabled:true` |
| `TOOLCHAIN.md` + `toolchain.json` | pinned binaries | `guiSha256` is not the GUI the instance runs (F5) |
| `docs/CURATION_POLICY.md` | Keep/Skip semantics | Consistent; `KEEP_REVIEW.md:7-13` repeats it |
| `SLOT_DECISIONS.md` | "superseded by BASELINE" (its own header) | Reference only; fine |
| `docs/KEEP_REVIEW.md` (1,318 lines) | per-mod decisions, both assistants' cursors | No same-ID contradictions found by parse; 149 uncommitted lines |
| `docs/DEFERRED_DECISIONS.md` | "canonical register" of delegated work + cursor | "Running now: None" |
| `docs/AGENT_WORK_QUEUE.md` | delegated queue + cursor | "Active: None" while ~30 agents ran during this audit; duplicates the cursor text in DEFERRED_DECISIONS |
| `HANDOFF-2026-08-26/27/29` | each supersedes the previous | `-27` "Parked (15)" lists MCM Helper, OAR, CRD, Light Placer, SPID, TNG, Proteus as parked; all active now; `-29` says older handoffs are "historical evidence only" but nothing marks them so in-file |
| `records/installed-mods.json` | installed truth | Not (F4) |
| Broken references | `docs/OVERNIGHT_REPORT.md` -> `records/overnight-audit-2026-08-23.json` (file is `.jsonl`); `docs/PROTEUS-1.7.99-SMOKE-2026-08-26.md` -> `docs/TEST-MATRIX.md` (absent) | |

Proposed consolidation (not performed):

1. One machine-generated `STATE.md` (from `mod-list`, `plugin-list`, ledger)
   replaces every hand-written "installed / parked / active" sentence; docs
   link to it instead of restating.
2. Merge `AGENT_WORK_QUEUE.md` into `DEFERRED_DECISIONS.md` (one queue, one
   cursor section); or drop both in favour of the GitHub tracker #62 they
   already point at.
3. Stamp `HANDOFF-2026-08-26.md` and `-27.md` with a first-line "SUPERSEDED -
   historical" banner, or move to `docs/archive/`.
4. `BASELINE.md`: strip the runtime status prose from tiers 0-2 (keep the slot
   decisions), pointing at `STATE.md`; fix the three contradictions above.
5. Fix the two broken references.

### F10 - MEDIUM - 34 GB of staging and trash never cleaned

`mod-install` moves only `contentRoot` (`main.cpp:1385`); the
`.mo2-headless-stage-<tx>` parent with the full extraction is left in the
instance root: 155 directories, 19 GB, oldest 2026-08-25. `.mo2-headless-trash`
holds 15 GB with no retention rule. Fix: remove the stage parent on
`tx.commit()` (it is recreatable from the archive) and add a
`trash-prune --older-than` verb; until then a dated `.bak` rename is the
rule-compliant manual cleanup.

### F11 - MEDIUM - Instance binaries are mixed commits and the pin is wrong for the GUI

`mo2-instances\skyrim-se\MO2Headless.exe` = pinned `FEBD3C0A...` (3769ece).
`mo2-instances\skyrim-se\ModOrganizer.exe` = `F27115F4...` =
`mo2-builds\MO2-2.5.2-headless-23de14e2-full\ModOrganizer.exe`, one commit
behind, while `toolchain.json` pins `guiSha256 9CBD793C...` (3769ece). `run`
always launches the sibling in the instance (`main.cpp:1708`), so the
checksum gate in `run-through-mo2.ps1:74-76` verifies a binary that is not the
one mounting the VFS. Fix: copy the 3769ece GUI into the instance or point
`guiPath` at the instance file; add the instance path to the running-process
guard.

### F12 - MEDIUM - #75 LOOT report omission, updated evidence

`loot-report.json` (11:47:34) lists 257 plugins; 14 currently active plugins
are absent: ISC, FNIS, Solitude Docks, NW_Sons_of_Skyrim, XPMSE,
Eli_InigoBloodchillPatch, NW_Companions_Replacer_Light, NW_Steel_Plate_Armors,
Baltimore Weapons, DIS_NordScale, Skyrim Unbound, Lux, Lux - BS Bruma patch,
Water for ENB. Tested and ruled out: masterlist membership (6 of 14 have
entries, 34 of 172 present ones do too), `userlist.yaml` membership (3 of 14),
BSA beside the plugin (none), ESL flag (mixed). The report entry set shows
entries with `messages`, `dirty`, `clean`, `missingMasters` keys all
serialise, so it is not a whole-category drop. The `lootcli-1.8.0-source`
directory contains only `build/`, so the report writer could not be read; the
next step is to run lootcli with `--verbose`-style logging on one omitted
plugin. Posted as a comment on #75.

### F13 - MEDIUM - #91 root cause located

`main.cpp:1397-1412`: on `--replace` the existing entry is `removeAt(index)`
and the new entry is inserted at `entries.size() - priority` with
`priority = entries.size()` (top) unless `--priority` is given, and
`enabled = parser.isSet("enable")` regardless of the old row. Fix in
MO2Headless: when `index >= 0` and no `--priority`, reinsert at `index`; when
no `--enable`/`--disable`, keep the old `enabled`. `install_mod.py` always
passes `--enable`, so the "row disabled" half of #91 comes from direct
controller use. Posted as a comment on #91.

### F14 - MEDIUM - `verify_order.py` over-approximates implicit masters

`audit/verify_order.py:40-50` treats every plugin file in the game `Data`
folder as implicitly loaded. Only the five base masters and `Skyrim.ccc`
entries are; a loose non-CC plugin dropped into `Data` (or a CC plugin removed
from `Skyrim.ccc`) would hide a missing master. No such case exists today
(header scan against `Skyrim.ccc`: 0). It also never checks a master that is
discovered but unstarred, which is the F1 shape. Fix: implicit = base five +
`Skyrim.ccc`; report "master present but inactive" separately.

### F15 - LOW - Tooling details

- `install_mod.py:30-37` `mo2()`: parses the last line of `stdout or stderr`.
  MO2Headless emits error JSON on stderr; if stdout carries anything
  non-JSON (it should not, but `run` embeds child output) the error is
  reported as `{'ok': False, 'raw': ...}` with the real reason truncated to
  400 chars. Parse stdout then stderr, and surface `exitCode`.
- Timeouts: `mo2()` 900 s, LOOT 900 s inside a 1,200 s subprocess, MO2
  `run` kills the child at `--timeout` and the PowerShell wrapper kills the
  tree 15 s later - coherent.
- `modasset.py:14` reads the Nexus API key from
  `crusader-de-tweaker\scripts\nexus\nexus.local.json` - a cross-repo
  hard-coded credential path.
- `modasset.download()` accepts any cached file over 1 KB as complete; no
  size/hash check against the Nexus `size_kb` it already has.
- `launch_triage.py`: regex at :45 matches the observed `skse64.log` line
  shapes (checked against the 2026-08-29 log); the "no version data" line
  for `msdia140.dll` is correctly excluded.
- `plugin_watch.py` writes `records/plugin-watch.json`, which is tracked:
  every poll dirties git.
- `config/loot/userlist.yaml` and the live
  `%LOCALAPPDATA%\LOOT\games\Skyrim Special Edition\userlist.yaml` differ
  only in comments today, but nothing syncs them; a rule edited in the repo is
  not what LootCLI applies until someone copies it.
- Each sort creates ~190 `plugin-enable` processes and journal directories
  (5,107 so far); `snapshot`/`apply` would make it one.
- Read-only controller commands (`status`, `audit`, `plugin-list`) ran clean
  during this audit: `audit` returned `errors: []`, `plugin-list` 272
  discovered / 192 entries / 186 enabled.

### F16 - LOW - Git hygiene

`.gitignore` is deny-by-default (`*` then allowlist), which is why every new
record needs its own `!/records/<name>.md` line (31 added in today's diff).
`git check-ignore` confirms `toolchain.json`, `records/tool-runs/`,
`mods/crf-semantic-patch/work/*.zip`, `*.dds` and `.tmp-*` are all ignored;
`mods/crf-semantic-patch/generator/bin/` is ignored. Nothing in `git status`
is a binary or a credential. Suggest `!/records/*.md` and `!/records/**/*.md`
to end the per-file churn.

Proposed commit grouping for the 70 dirty paths (provenance from `meta.ini`,
handoff, and diff content; verify before committing):

1. **tooling**: `audit/install_mod.py` (sort rewrite + MO2 path),
   `audit/skse_version_data.py`, `audit/plugin_watch.py`,
   `audit/inspect_mod.py`, `records/plugin-watch.json`.
2. **policy docs**: `docs/CURATION_POLICY.md`, `docs/EQUIPMENT_INTAKE_POLICY.md`,
   `docs/TEXTURE_POLICY.md`, `docs/PATCH_INTENTS.md`, `docs/CS_FEATURES.md`,
   `docs/MCM-PERSISTENCE-2026-08-28.md`, `README.md`.
3. **queue and decisions**: `docs/AGENT_WORK_QUEUE.md`,
   `docs/DEFERRED_DECISIONS.md`, `docs/KEEP_REVIEW.md`, `BASELINE.md`,
   `docs/MODPACK-ROADMAP-2026-08-28.md`.
4. **profile state 2026-08-30**: `records/installed-mods.json`,
   `records/restricted-mods.json`, `records/fomod-plans/*.json` (33 files),
   `config/loot/userlist.yaml`, `.gitignore`.
5. **audit records**: the 20 new `records/*.md` files, one commit per topic
   cluster (Solitude/city stack, equipment intakes, sound/blood/texture
   decisions, Varinia, MCM Helper).
6. **CRF semantic patch source**: `mods/crf-semantic-patch/`,
   `records/source-builds/ensrick-crf-semantic-patch.json`.
7. **werewolf totem overlay**: `records/source-builds/ensrick-scoped-werewolf-totem-98175.json`.
8. **vendor integrity + display + water seams**:
   `docs/VENDOR-INTEGRITY-2026-08-29.md`,
   `docs/DISPLAY-UNBOUND-LIGHTING-FIXES-2026-08-28.md`,
   `records/synthesis/water-seams-fix/`.
9. **ecosystem survey**: `docs/ECOSYSTEM-SURVEY-2026-08-30.md`.

## What was checked and found clean

- No duplicate ledger rows by `modName` or `fileId`; the 18 `modId`s with
  several rows are legitimate split installs.
- Every modlist row has a folder and every folder has a row.
- `plugins.txt` order equals the managed part of `loadorder.txt`.
- Every discovered plugin is in `plugins.txt`; no stale entries.
- All masters of active plugins are active or implicit; the only missing
  masters belong to the two deliberately unstarred Lux CC patches.
- No `.esl` file lacks the ESL flag; 147 of 186 active plugins are ESL.
- All four gate-failing DLLs in enabled vendor folders (JContainers64,
  PapyrusUtil, Proteus, skee64) are shadowed by a same-named passing overlay
  at higher priority. Parked DLLs that pass (CS core, SSE Display Tweaks) are
  documented as superseded.
- Archive SHA-256 in the ledger matches the cached download for all 20 mods
  checked.
