# Asset audit

Inspects what a mod actually ships and reports findings. It does not decide
anything: the output is evidence for a keep/skip call, not the call itself.

Launch tooling lives here too - see [Launching](#launching) below.

```
py -3 audit/inspect_mod.py "6369:Cloaks of Skyrim"
py -3 audit/inspect_mod.py "5795:RUSTIC CLUTTER:2K$"     # third field picks a file variant
```

The findings sheet has four parts: what the archive contains, what modern
features it supports, warning signs with the offending file named, and the
community addons that fill the gaps it leaves.

## Files

| file | job |
|---|---|
| `modasset.py` | download, extract, read BSAs (incl. SSE's LZ4-framed entries), parse DDS and NIF headers |
| `esp.py` | plugin parser: ARMO/ARMA equip slots, item classes, masters, ESL flag |
| `vanilla_index.py` | index the game's own BSAs; run once, produces `vanilla_index.json` |
| `inspect_mod.py` | the findings sheet |
| `mip_retention.py` | distance detail: high-frequency energy per stored mip, vs vanilla at matched pixel size; `--resharpen` regenerates a sharpened chain (recipe form) |
| `calibrate_detail.py` | rebuilds the detail-index controls used below |

`vanilla_index.py` must run before upscale detection works. It reads the game
install read-only and takes about 6 minutes for ~180k asset paths.

## What it detects

**Textures** - upscaled vanilla passed off as new work, missing companion
normal maps, normals stored as BC1, flat or diffuse-embossed normals, solid
gloss alpha, absent mipmaps, uncompressed textures, JPEG blocking, resolution
below the vanilla asset being replaced, diffuse/normal resolution mismatch.

**Distance detail** (CURATION_POLICY "Textures are judged at distance") - up
to 12 sampled diffuse/normal/specular maps >= 1024 px have their stored mip
chain decoded (`mip_retention.py`, texconv) and the RMS Laplacian energy of
mips 512-128 px compared with the vanilla texture at the same pixel size.
A replacer under 70% of vanilla there is flagged `soft-at-distance`; the
note line carries the median ratio. `--mip=0` skips the check (it is the
slow part), `--mip=N` changes the sample. Needs `vanilla_index.json` for the
vs-vanilla half; without it only self-retention (mip 3 / mip 0) is recorded
in the JSON. Stand-alone use:

```
py -3 audit/mip_retention.py <mod.dds> [vanilla.dds] [--json]
py -3 audit/mip_retention.py <mod.dds> --resharpen out.dds --unsharp 1.0 --radius 1.0
```

**Meshes** - unconverted Oldrim meshes (NIF user version other than 100, using
`NiTriShape` instead of `BSTriShape`), parallax shader flags with no `_p`
texture shipped, triangle budget.

Triangle counts cover static meshes only. Skinned meshes keep geometry in
`NiSkinPartition`, which this does not parse, so they are reported as unread
rather than counted as zero.

**Apparel** - equip slot and item class come from the plugin's ARMO records, so
findings apply only to items where loose cloth is actually visible. A ring is
not asked about physics. For those that qualify, the mesh's bone list decides
what is reported:

| mesh is weighted to | reported as |
|---|---|
| bones outside the vanilla skeleton, no SMP config | rig present but inert without a physics patch |
| the vanilla `Skirt*Bone` chain, no SMP config | canned skirt animation only, no simulation |
| no cloth bones at all | rigid geometry welded to the body |

The vanilla bone set is read from the game's own
`actors/character/character assets/skeleton.nif`, because `SkirtBBone01-03`
look custom but are stock. Absence of a PBR material set is a note, not a
warning, since it only matters under TruePBR.

Contested biped slots (45, 46, 47) are reported too, since two mods on slot 46
cannot be worn together no matter how good either one is.

**Packaging** - `.psd`, `Thumbs.db`, `__MACOSX` and similar junk.

## Launching

Three consecutive broken launches in two days were all caused by state nobody
looked at, and the third ended with the user watching a 2.5-minute stall unable
to tell loading from dead. The launch path is now four gates in a fixed order,
with one command that runs them:

```
py -3 audit/launch_session.py
```

| file | job |
|---|---|
| `preflight.py` | everything that must be true BEFORE the user is told to launch. Non-zero exit = do not tell them to launch |
| `launch_watch.py` | samples the live process and names its state every few seconds |
| `launch_verify.py` | the automated pass/fail run: launches, times the menu, loads a save |
| `launch_triage.py` | reads the SKSE logs afterwards and reports every plugin that failed |
| `threaddump.py` | groups a CrashLogger thread dump and says what the process was doing |
| `claim.py` | the instance work claim: one owner mutates the profile at a time (#103). `acquire` / `renew` / `release` / `check` / `status` |
| `preflight_extra.py` | the 2026-09-01 gates: DLL depth (a `.dll` under `Plugins/` not `SKSE/Plugins/` in an enabled mod = FAIL), ledger gap (#102), watched-config snapshots (`watched_configs.json` -> `records/config-history/`), saves mirror (`records/save-backups/`, newest 5), the real profile `settings.ini`, the claim |
| `feature_defaults_diff.py` | source builds: diff shipped defaults against upstream's for the build record (#144) |
| `human_presence.py` | #164: is a person playing in the harness's session? Gameplay menus opened after AUTOLOAD_SETTLED with no MenuPilot command within 2 s = yes. `launch_verify.kill` then refuses (exit 88, `--force-kill "reason"` overrides) and `install_mod` refuses an install/sort under that game; `--selftest` replays the 23:41 (human) and 23:11 (clean) fixtures in `audit/fixtures/` |
| `launch_skyrim.ps1` | the sanctioned launcher: claim check, harness-env scrub before the Steam cycle (#141), profile-INI sync over Documents (#143), `-Direct` spawn through `MO2Headless run` |

### Work claim: `claim.py`

```
set SKYRIM_CLAIM_OWNER=<you>                # once per session; scripts pick it up
py -3 audit/claim.py acquire --owner <you> --purpose "install X" --ttl 30
py -3 audit/claim.py status
py -3 audit/claim.py release --owner <you>
```

`install_mod.py` (install, `--sort`), `launch_verify.py` and `launch_skyrim.ps1`
acquire or check it themselves and stop with exit 75 when another owner holds
it. A claim past its TTL is stale and is taken over with a logged warning
(`records/claim-log.jsonl`). `install_mod.py` additionally refuses to mutate the
profile from any checkout but the canonical one (`--i-know-what-im-doing`
overrides, #105).

### Verification: `launch_verify.py`

User criterion: *"With each change we must successfully launch the game and load
the save"* and *"It must reach the main menu in under 60 seconds or it's a
failure."*

```
py -3 audit/launch_verify.py --dry-run     # rehearse: plan + blockers, no launch
py -3 audit/launch_verify.py               # the real pass/fail run
py -3 audit/launch_verify.py --selftest    # replay timelines through the rules
```

PASS requires **both** a real main menu within 60 s of process start **and** a
save actually loaded. Exit 0 PASS, 1 otherwise; a record lands in
`records/launch-verify-*.md` either way, with the timing breakdown
(process start -> kDataLoaded -> main menu -> save loaded).

It is the only file here that launches the game and the only one that kills it;
the user authorized both for verification runs specifically. `--leave-running`
turns the kill off. `launch_session.py --verify` is the same thing.

**It refuses to certify a PASS without LaunchProbe.** The cheap main-menu
signals lie: on both hung launches of 2026-08-31, CommunityShaders'
`InitializeMenuIcons` and SkyParkour's log fired at about T+56s and the game
never became playable. A signal that fires during the failure it is meant to
exclude cannot gate a PASS. LaunchProbe is a micro SKSE plugin built for this
(source `skyrim-tools-source/LaunchProbe`, artifact staged at
`records/source-builds/launch-probe/`, record
`records/source-builds/ensrick-launch-probe.json`) that logs, timestamped:

| probe event | means |
|---|---|
| `MAIN_MENU_OPEN` / `MAIN_MENU_ALREADY_OPEN` | the game's own `MenuOpenCloseEvent` for `RE::MainMenu::MENU_NAME` |
| `SKSE_MESSAGE name="kDataLoaded"` etc. | each SKSE messaging phase |
| `SKSE_MESSAGE name="kPostLoadGame" success=1` | a save finished loading |

It also drives the load: with `SKYRIM_LAUNCH_PROBE_AUTOLOAD=<save base name>` set
it calls `BGSSaveLoadManager::Load` once the main menu is up. The env var must be
set before Steam restarts, because the chain is Steam -> MO2 -> SKSE ->
SkyrimSE and each link inherits its parent's environment; `launch_verify.py`
handles that. Unset, the plugin only logs, so it is inert during normal play.

ConsoleUtilSSE was considered for the save load and rejected: it executes
console commands from Papyrus, and Papyrus is not running at the main menu.

`launch_session.py` runs preflight, waits for the game (**it never launches it**
- autonomous launches are not allowed), watches, triages, and analyses any
thread dump taken during the session. Exit code is the first step that failed:
1 preflight, 2 hang, 3 died before menu, 4 never started, 5 refused plugins.

**preflight** checks INI ownership (`LocalSettings=true`) and the deliberate
keys, plugin state via `install_mod --verify` and `verify_order`, whether the
last launch died mid-plugin-load or crashed after init, whether a headless MO2
writer is running (#103), whether Steam is wedged with a phantom Running flag,
and whether the game-side `%LOCALAPPDATA%` `Plugins.txt` still matches the
profile. It skips the MO2-driven checks when the game is already running rather
than driving MO2Headless alongside a live session.

**launch_watch** answers one question continuously: is this progressing?

| state | what it means |
|---|---|
| `loading` | memory climbing or an SKSE-side log still being written |
| `shaders` | shader cache growing - CPU pegged with flat memory is CORRECT here |
| `at-menu` | LaunchProbe saw the real main menu open |
| `stalled` | nothing advancing, not yet long enough to call |
| `stalled-unconfirmed` | nothing advancing, window still pumping, and no authoritative menu signal - a real menu and a wedge are indistinguishable from outside |
| `hung-spin` | burning CPU, nothing advancing |
| `hung-idle` | no CPU and nothing advancing - a lock, not slow work |
| `died` | process gone; names any crash log newer than `skse64.log` |

Separating `shaders` from `hung-spin` is the point: a first launch after a
shader-affecting change pegs a core with memory flat for minutes, which is the
most hang-shaped thing this build does that is not a hang.

Progress is movement between consecutive samples, never recency. Judging it by
"a log was written in the last minute" reports `progressing` forty seconds into
a hang, because one stale burst keeps satisfying the window. Sizes are compared
with `!=` rather than `>`, because SKSE truncates `skse64.log` at startup and a
`>` test scores the refill as a stall until it passes the old session's size.

`stalled-unconfirmed` exists because honesty demanded it: without LaunchProbe,
"sitting at a real main menu" and "wedged with a message loop still turning"
produce identical readings, and the 2026-08-31 hang was the second one with a
responsive window. The watcher says it cannot tell instead of guessing.

On a hang it prints the verdict with its evidence, captures per-thread CPU
attributed to the owning module, writes `records/launch-watch-<timestamp>.md`,
and tells the user to press Ctrl+Shift+F12. **It never kills the game**, and it
does not press the hotkey either: CrashLogger polls `GetAsyncKeyState` (no
`RegisterHotKey`, no window hook, no event or pipe trigger in the DLL), so a
synthetic trigger would mean injecting global keystrokes and hoping the poll
catches them - delivery depends on the foreground window and fails silently
against an elevated game.

Sampling is native Win32 via ctypes (`GetProcessTimes`,
`GetProcessMemoryInfo`, `SendMessageTimeout`), not a `pwsh` child per tick.
Responsiveness is a modifier, never a verdict: a loading Skyrim is legitimately
unresponsive, and a main thread parked in `GetMessage` answers promptly while
rendering nothing - which is exactly what the 2026-08-31 hang looked like.

`py -3 audit/launch_watch.py --selftest` exercises every branch of the state
machine and both disk scanners without a game running.

## Calibration

Thresholds are measured against controls, not asserted. The controls are built
by taking vanilla textures and degrading them in known ways
(`calibrate_detail.py`):

| control | detail index |
|---|---|
| hand-authored 2K (RUSTIC Clutter) | 7.33 |
| vanilla, native size | 2.71 |
| vanilla upscaled 2x then sharpened | 1.53 |
| vanilla upscaled 2x | 0.61 |
| vanilla upscaled 4x | 0.25 |

The detail index alone cannot separate a sharpened upscale from real vanilla,
so upscale detection uses correlation against the vanilla asset instead:

| case | correlation to vanilla |
|---|---|
| plain upscale | 0.995+ |
| upscale + sharpen | 0.96 min |
| genuine hand-authored retexture | 0.91 max |

Hence the 0.95 threshold, with roughly 0.05 of margin either side.

An edge-ringing detector for the sharpening case was written and **discarded**:
native vanilla textures ring as hard as sharpened upscales (9.53 vs 12.40), so
it separated nothing. Any metric that fails to separate the controls does not
belong in the report.

## Load-order safety

`verify_order.py` reads each active plugin's TES4 master list and fails when a
master has no provider, is present but inactive, or loads too late. Only the
five official base masters and plugins explicitly listed in `Skyrim.ccc` are
implicit; an arbitrary plugin sitting loose in the physical `Data` directory
is not treated as active. Synthetic regression tests cover those activation
rules and run in the repository's required `validate` check.
