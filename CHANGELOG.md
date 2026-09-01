# Change log

**User directive (2026-08-31, verbatim):** "now we're keeping a changelog so we
can trace every change back to its source. With each change we must
successfully launch the game and load the save." Launch criterion, verbatim:
"It must reach the main menu in under 60 seconds or it's a failure."

Every entry carries:

- **What** changed - mod installed/removed/parked/unparked, INI key, tool
  change, generated patch or overlay, or a decision that changes build state.
- **Source** - who or what caused it: the user's words, the issue number, the
  agent/session, or the research record that justified it.
- **Verification** - `VERIFIED <date>` (main menu in under 60 seconds AND the
  save loaded), `UNVERIFIED`, or `FAILED <evidence>`.

Newest first. Times are local (UTC-5); `installedUtc` stamps in
`records/installed-mods.json` are UTC. Rules for landing new entries:
"Changelog discipline" in `docs/CURATION_POLICY.md`.

> **STATE WARNING (2026-08-31).** Everything between the 2026-08-29 17:23
> checkpoint launch and the 2026-08-31 22:00 launch wave - roughly 40 change
> batches covering 111 ledger rows plus INI, tool, and overlay changes - is
> **UNVERIFIED**, and the three 2026-08-31 launch failures sit directly on top
> of that unverified pile. That is exactly why this changelog now exists.
> Nothing else lands until the failures are bisected.

---

## 2026-09-01 17:26 - LaunchProbe kPostLoadGame AV fixed (the 17:12/17:25 crashes)

- **What:** LaunchProbe dereferenced kPostLoadGame's data as `bool*`; this
  SKSE build passes the success bool BY VALUE in the pointer slot, so the
  FIRST successful save load after the #142 fix AV'd at LaunchProbe.dll+2C51
  (17:12:51 and 17:25:41; failed loads pass null and never crashed, which is
  why every earlier run survived). Guard added (values <0x10000 are the flag),
  rebuilt, redeployed to mods/LaunchProbe + staged copy, committed
  (skyrim-tools-source/LaunchProbe 12ce92e, includes the previously
  uncommitted _wfsopen tail-sharing change). New DLL sha256 47cfbe47...b210.
- **Source:** menupilot agent; crash-2026-09-01-17-25-41.log call stack
  (Dispatch_Message -> LoadGame_Hook), records/launch-verify-20260901-172546.md.
- **Verification:** VERIFIED 2026-09-01 17:28 - launch PASS, main menu 31.2s,
  save loaded 35.7s, kPostLoadGame success=1 logged cleanly
  (records/launch-verify-20260901-172851.md).

## 2026-09-01 17:23 - MenuPilot installed: headless in-game menu control

- **What:** new MO2 mod `MenuPilot` (SKSE, source
  skyrim-tools-source/MenuPilot commit 93e5afa, gate PASS): file-driven
  bridge - assistant writes SKSE/MenuPilot/commands.jsonl, plugin consumes it
  exactly once and drives menus (kShow/kHide), Scaleform
  (Invoke/GetVariable/dump) and engine-layer input (ButtonEvent via
  BSInputDeviceManager) on the main thread, logging every step. Inert without
  a command file; panic op; no popups. Driver audit/menupilot.py; docs
  docs/MENUPILOT.md; record records/source-builds/ensrick-menu-pilot.json.
  Purpose: user order - drive game menus without the user clicking; first
  target the Creations store re-download of Farming (#142). Discovery so far:
  runtime registers no "Creation Club Menu"; "Marketplace Menu" = credits
  movie; store surfaces must be driven from the main-menu context
  (records/menupilot-cc-discovery-2026-09-01.log).
- **Source:** user order via team lead 2026-09-01; issue #142 remaining action.
- **Verification:** VERIFIED 2026-09-01 17:28-17:33 - installed for the PASS
  launch above; in-game round-trip proven (Journal open/query/close, 39-menu
  enumeration, Scaleform dumps). input.tap not yet exercised.

## 2026-09-01 ~07:40-07:52 - #142 ROOT CAUSE: truncated ccvsvsse004-beafarmer.bsa; hang fixed

- **What (diagnosis, zero launches):** captured the live 07:35 hang specimen
  from outside with the new `audit/spindump.py` (all-thread RIP sampling +
  handle resolution + minidump). The 3 spinning threads: an engine IO worker
  in an unbounded ReadFile retry loop on handle 0x85C =
  `Data\ccvsvsse004-beafarmer.bsa` (real Steam path, outside the VFS), file
  position pinned 544,816 bytes PAST the 4,194,256-byte EOF; the other two are
  poll loops (Sleep-loop worker + PeekMessage main-thread pump) waiting on it.
  The BSA is truncated at exactly 4MB-48: Steam content_log + mtimes show the
  game process re-downloaded CC content 22:04:31-53 on 08-31 (first-run
  `bUpsellOwned=0` state from the INI reset) and the run-2 kill at 22:04:30
  truncated the last file mid-write. Not in any Steam depot (only the 4
  free-AE creations are), so `steam://validate/489830` ran clean in 25s and
  could not repair it. Full evidence: `records/hang-rootcause-2026-09-01.md`.
- **What (fix):** renamed `ccvsvsse004-beafarmer.bsa/.esl` to
  `.bak.v20260831-truncated`; disabled the two dependent patch plugins via
  MO2Headless (`Lux - Farmer patch.esp`, transaction
  20260901T125112069Z; `Landscape and Water Fixes - Patch - Farming.esp`,
  20260901T125112329Z) and marked both `disabledPlugins` in the ledger with
  re-enable instructions. Preflight clean (224 active plugins).
- **What (confirmation launch 07:52):** kDataLoaded t+24.6s, MAIN MENU
  t+25.2s - the hang is gone after 11 consecutive failures. Save load
  reports success=-1 as expected: the 08-29 save references the parked
  `ccvsvsse004-beafarmer.esl`. Full PASS is blocked until the Farming
  creation is re-downloaded. Record `records/launch-verify-20260901-075219.md`.
- **Pending user action:** in-game Creations menu -> re-download "Farming"
  (restores canonical bsa+esl), then re-enable both patch plugins, clear the
  two ledger `disabledPlugins` entries, delete the `.bak.v20260831-truncated`
  files, and run a full launch_verify PASS. `ccbgssse068-bloodfall.*` /
  `ccbgssse069-contest.*` were rewritten in the same window and survived data
  load; a re-download of those two is cheap insurance at the same time.
- **Source:** #142 phase-2 investigation (machine/VFS agent, user out of
  loop).
- **Verification:** hang fix VERIFIED 2026-09-01 07:52 (main menu 25.2s);
  save-load half FAILED by design until Farming is restored.

---

## 2026-09-01 - #142 bisect rounds 3 + verdict: ALL content exonerated, build restored

- **What (round 3, launch 07:28):** parked the final content slice - 28
  weapons/armor/gameplay smalls plus the 3 generated non-ledger mods (Pandora
  Output - Ensrick regenerated 08-30 19:15, Ensrick - General Compatibility
  Patch, Ensrick - Scoped Werewolf Totem Skull). At that point EVERY mod
  installed or regenerated after the 2026-08-29 17:23 good launch was parked
  (91 active plugins) alongside the 8-DLL wave. The game STILL hung:
  identical signature, hang onset t+16s, exactly 3 SkyrimSE.exe-entry threads
  spinning at 100 percent each, working set flat at 1810MB, skse64.log
  stopping after the last translations line, kDataLoaded never dispatched,
  LaunchProbe seeing only Loading/Mist/Fader/LoadWaitSpinner menus. Records
  launch-verify-20260901-072617.md (round 2) and -072845.md (round 3).
- **Verdict:** the post-08-29 install wave - native DLLs (launch 5) and all
  ~99 content/generated mods (rounds 1-3) - is EXONERATED wholesale. The
  spin-hang plateau (1879/1815/1810MB at 149/106/91 plugins) is nearly
  content-independent. Suspect space is now usvfs/MO2 overlay, Steam overlay,
  profile-level state (plugin order, archives), or machine-side change
  (driver/OS) - a different investigation per the campaign rails; stopped at
  4 launches of the 8 budgeted.
- **What (restore):** applied the pre-campaign baseline snapshot (MO2Headless
  transaction 20260901T122948673Z-7f1c30834ecd): all bisect parks reversed,
  226 active plugins, the 13-mod DLL wave still parked as directed,
  LaunchProbe still installed. Ledger rounds reversed; ~41 ledger notes the
  round tooling had clobbered were restored from git HEAD (notes on the 6
  rows newer than the last ledger commit had none to restore).
  verify_order CLEAN, install_mod --verify 0 problems, preflight clean.
- **Source:** #142 autonomous bisect campaign (team-lead directive, user
  out of loop).
- **Verification:** FAILED x3 as designed evidence (rounds 1-3); final
  restored state UNVERIFIED (no launch can pass until the residual cause is
  found).

## 2026-09-01 - #142 bisect rounds 1-2: content halves

- **What (round 1, launch 07:23):** with the facegen/NPC + city-stack half
  parked (entry below), the game STILL hung - same signature, new location:
  skse64.log stops after the last translation line (now Skyrim Unbound, nwsFF
  parked), no kDataLoaded, LaunchProbe saw only loading-screen menus, ~3 cores
  spinning with working set flat at 1879MB t+38..60s. Record
  records/launch-verify-20260901-072310.md. That half (39 mods, incl. every
  facegen carrier) is EXONERATED as sole culprit; left parked for now.
  (The 07:19 attempt aborted at t+9s: LaunchProbe held its log deny-all
  sharing; probe rebuilt with _SH_DENYWR, launch_watch.probe_events hardened.
  No bisect signal - not counted as a round.)
- **What (round 2):** additionally parked 30 mods - the record/payload-heavy
  half: USMP, SLaWF (15 plugins), ACMOS x2, sound stack (ISC, AOS x2), fix
  floor (UMF, VSM, AMF + Ensrick port, Navigator), Skyland AIO, NotWL family,
  MLO2 x2, ERM x3, Ulvenwald x2, grass stack x6, Ensrick Lux Water CS Patch.
  MO2Headless apply transaction 20260901T122434359Z-19ea1febe33e. 106 active
  plugins; verify_order CLEAN, install_mod --verify 0 problems. Still active
  from the post-08-29 wave: weapons/armor + small-gameplay mods only.
- **Source:** #142 autonomous bisect campaign.
- **Verification:** PENDING - next launch: menu = culprit in round-2's 30;
  hang = culprit among the ~25 weapons/gameplay smalls or outside the ledger.

## 2026-09-01 - #142 bisect round 1: facegen/NPC + city-stack half parked

- **What:** parked 39 mod folders (3DNPC + 6 addons/patches, Cutting Room
  Floor + CRF Semantic Patch, INIGO + 2 patches, Varinia + dialogue fix,
  Nether's Follower Framework, Skyking x4, Whiterun Trellis, Rally's Market
  Stalls x2, Grand Solitude x2, Solitude Docks + NotWL docks patch, Snazzy x4,
  SFCO3 patches, Lux/Lux Orbis patch hubs x5, Collectibles Helper x2, CC Bow
  of Shadows fix) and unstarred 2 cross-half patch plugins (3DNPCNavFix.esp,
  NotWL-CuttingRoomFloor.esp) so Navigator and SLaWF stay active. Applied as
  MO2Headless `apply` transaction 20260901T121850734Z-ff9bf0e8b786 from
  snapshot-derived state; baseline snapshot retained by the bisect agent.
  149 active plugins; verify_order CLEAN, install_mod --verify 0 problems.
- **Source:** #142 autonomous bisect campaign (launch 5 exonerated the DLL
  wave; crash evidence is a facegendata path string - this half contains every
  candidate mod shipping facegen payloads: 3DNPC, CRF, Inigo, Varinia, Grand
  Solitude, Snazzy Solitude, Solitude Docks).
- **Verification:** PENDING - next launch decides. Menu reached = culprit in
  this half; hang = culprit in the landscape/fix-floor/sound/weapons half.

## 2026-09-01 - #142 instrumentation: LaunchProbe installed

- **What:** LaunchProbe 2026-09-01 installed as MO2 mod (priority 225,
  transaction 20260901T121454337Z-a0ba87af72df, ledger row added, sha256
  167051c7eb2cafe5...). One SKSE DLL logging MenuOpenClose + every SKSE
  message with timestamps to SKSE/LaunchProbe.log - the authoritative
  kDataLoaded/MainMenu pass-fail signal launch_verify.py requires.
- **Source:** #142 bisect campaign; built by the watchdog agent from
  C:/Users/danjo/source/repos/skyrim-tools-source/LaunchProbe, staged at
  records/source-builds/launch-probe/, SKSE-gate PASS.
- **Verification:** PENDING - validated implicitly by the round-1 launch (if
  it malfunctions it gets removed and the campaign falls back to the
  skse64.log translations-line criterion).

## 2026-09-01 - #142 corruption bisect: eight-DLL wave parked

- **What:** parked 13 mod folders (FSMP AVX-512, VHR SMP + NPCs + Ensrick facegen
  overlay, Community Shaders AIO source build, SSE Display Tweaks Official +
  Ensrick config overlay, SkyParkour v3 SPPF + Pandora cache, Simple Dual
  Sheath, MCM Helper, Sound Record Distributor, QuickLoot IE rebuild) and
  unstarred their 5 plugins. Content mods untouched. 226 active plugins.
- **Source:** docs/CRASH-2026-08-31-DEEP-DIVE.md + issue #142 - heap corruption
  during menu-phase load (facegendata path string over pointer data, engine
  code, job thread); this is the recommended single test that splits the
  hypothesis space. Wave = every new/replaced native DLL since the last
  VERIFIED launch (2026-08-29 17:23).
- **Verification:** PENDING - next launch is the test. Clean = corruption is in
  the wave, bisect in 2-3 launches. Hung/crashed = all new native code
  exonerated in one shot.

## 2026-08-31

### Verification launch wave, 22:00-22:47 - FAILED, three distinct signatures

- **What:** repeated attempts to launch and load the save. MO2 usvfs logs show
  six game sessions between 22:02 and 22:47
  (`mo2-instances/skyrim-se/logs/usvfs-2026-09-01_03-02-52` through
  `_03-47-19`). No attempt loaded the save.
  1. **FAILED - OAR load hang:** Open Animation Replacer 3.2.0 passes the SKSE
     timestamp gate, then hangs inside its own load with a popup; every SKSE
     plugin after it in load order never loads. Evidence: skse64.log
     2026-08-31 22:00, `threaddump-2026-08-31-22-13-15.log`, issue #140.
  2. **FAILED - INI first-run reset:** game came up 1920x1080 windowed on the
     4K panel with the AE upsell prompt; Skyrim had rewritten SkyrimPrefs.ini
     because MO2 was not managing INIs (`LocalSettings=false`). Evidence:
     `SkyrimPrefs.ini.bak.v20260901-firstrun-reset` (22:07), issue #98,
     `docs/INI_AND_PROFILE_STATE.md`.
  3. **FAILED - access violation at 85s uptime:** EXCEPTION_ACCESS_VIOLATION at
     SkyrimSE.exe+0E128B2 (JobListManager::ServingThread on stack). Evidence:
     `crash-2026-08-31-22-42-16.log`.
- **Source:** user-directed verification launches.
- **Verification:** FAILED (all three signatures above). The whole 08-29 to
  08-31 pile below is suspect until bisected.

### Mitigations during the launch wave

- **What:** Open Animation Replacer re-parked (ledger transaction
  `20260901T030136569Z`, verify_order clean at 231). Gate-pass alone is now
  known to be necessary-not-sufficient for unparks.
  **Source:** issue #140 (also invalidates the gate-only unpark basis of
  #83/#84/#85).
  **Verification:** UNVERIFIED (a later launch with OAR parked still crashed).
- **What:** SkyrimPrefs.ini restored from the `.base` snapshot;
  `LocalSettings=true` set in `profiles/Default/settings.txt`; deliberate-key
  table and before/after-launch checks written down.
  **Source:** issue #98; user directive "Since AI is managing MO2 I want you
  and Sol to never forget a single thing like ini files";
  `docs/INI_AND_PROFILE_STATE.md`.
  **Verification:** UNVERIFIED.

### Installs and repo work earlier on 08-31

- **What:** Skyrim Landscape and Water Fixes v10.6 installed, 15 plugins
  (19:29; ledger 2026-09-01T00:29Z).
  **Source:** fix-floor/survey lineage (`docs/ECOSYSTEM-SURVEY-2026-08-30.md`,
  issue #107 family); fomod plan `records/fomod-plans/26138-slawf.json`. **No
  issue or user line names this install specifically - source partially
  inferred (process hole).**
  **Verification:** UNVERIFIED.
- **What:** Bounded Encounters observe-only alpha: repo-side plugin project,
  commits 2dbea66..85de98f on main, tag `bounded-encounters/v0.1.0-alpha.1`,
  PRs #135/#136/#137 merged, #138/#139 open. Not installed into the profile;
  no game-state change.
  **Source:** design issue #133; user direction on bounded scaling.
  **Verification:** n/a (not in profile).
- **What:** `docs/NEW-LANDS-SURVEY-2026-08-31.md` added (research only).
  **Source:** research-newlands agent.
  **Verification:** n/a (no state change).

---

## 2026-08-30 late evening, 21:58-23:46 - grass and fix-floor wave

- **What:** smoke-test plan for the whole 08-30/31 wave
  (`docs/SMOKE-TEST-2026-08-31.md`, commit 3f434c7).
  **Source:** session docs work following the install wave.
  **Verification:** n/a (doc).
- **What:** grass stack installed: DrJacopo's 3D Grass Library meshes, Freak's
  Floral Fields 3.2.3 Realistic Regional Mix (7 plugins) + Ensrick texture
  cap, Freak's Floral Solstheim, Freak's Floral Veil, Landscape Fixes For
  Grass Mods. Commits 4347647, 60be49c.
  **Source:** issue #112 (empty grass slot);
  `records/freaks-floral-fields-3.2.3-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** DLL-free fix floor installed: Unofficial Material Fix 1.18.0,
  Vanilla Script MicroOptimizations, Assorted Mesh Fixes 0.139.3 + Ensrick SE
  mesh port, Navigator navmesh fixes (4 plugins), USMP 2.6.8b.
  **Source:** issue #107 (fix-floor batch from survey);
  `docs/ECOSYSTEM-SURVEY-2026-08-30.md`; USMP install opened #134 (Lux Water
  CS patch must be regenerated).
  **Verification:** UNVERIFIED.
- **What:** issues #130-#134 opened (Fuz Ro D-oh gate failure, deflate64
  install failure, verify false-positive on disabled plugins, bounded-scaling
  design, Lux Water CS regen).
  **Source:** session triage during the wave.
  **Verification:** n/a (tracking).

## 2026-08-30 evening, 16:22-18:32 - landscape, lighting, hair, movement

- **What:** base texture/landscape foundation: Skyland AIO 1K + full Nature of
  the Wild Lands 3.14 + active-profile patches + Solitude Docks patch +
  Ensrick texture cap. Commit 0aca55b.
  **Source:** user decision closing issue #88 (base texture and landscape
  stack); `records/skyland-notwl-foundation-install-2026-08-30.md`; follow-up
  tracking #119, #120.
  **Verification:** UNVERIFIED.
- **What:** Modern Lighting Overhaul 2 (MLO2) 5.4.1 + Ensrick foundation
  config adopted as the Lux lighting foundation. Commit 01387c8.
  **Source:** `records/mlo2-5.4.1-2026-08-30.md`; smoke test tracked as #121.
  **Verification:** UNVERIFIED.
- **What:** Vanilla Hair Remake SMP + NPCs file + Ensrick NPC compatibility
  overlay + FSMP 4.1.1 (hair physics dependency). Commit f526268.
  **Source:** research-hair agent;
  `records/vanilla-hair-remake-smp-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** ERM - Enhanced Rocks and Mountains 1.1.2 + Fix and Addon 6.4 +
  DynDOLOD add-on; layered-landscape decision recorded (commit 36306a2).
  **Source:** issue #122 (mountain/rock slot); conflict finding filed as #127
  (ERM outranks Lux on 28 ice-cave meshes).
  **Verification:** UNVERIFIED.
- **What:** SkyParkour v3 3.6.3 + Pandora animation cache; Pandora headless
  fork built and run so SkyParkour behaviors generate (`run-pandora.cmd`,
  commit 1a855dc).
  **Source:** issues #128 (closed by the Pandora run), #129 opened for
  Animation Queue Fix; fork-pandora / push-pandora agents.
  **Verification:** UNVERIFIED.
- **What:** controlled tree blend: Traverse the Ulvenwald 3.3.2 assets + Tree
  Diversity Project (NotWL base, Ulvenwald mix). Commit d5451ff.
  **Source:** `records/notwl-ulvenwald-tree-diversity-2026-08-30.md`; tree
  decision lineage in
  `records/tree-overhaul-and-morthal-cypress-audit-2026-08-29.md`.
  **Verification:** UNVERIFIED.
- **What:** issues #119-#129 opened (texture-cap overlay tracking, mip chains,
  MLO2 smoke test, mountain slot, fire/spell/creature adoption decisions,
  Eldergleam clusters, ERM/Lux ranking, Pandora, AQF rebuild).
  **Source:** survey-ecosystem + session triage.
  **Verification:** n/a (tracking).

## 2026-08-30 afternoon, 12:17-14:53 - reconciliation and clothing

- **What:** ledger re-registration of three pre-existing source builds:
  Community Shaders AIO 1.7.99 source build, Ensrick Lux Water CS Patch,
  QuickLoot IE Ensrick 1.7.99 (all stamped 17:17:26Z in the same second).
  Commit 668c4b9 "Record current installed foundation state".
  **Source:** ledger reconciliation (#102). **The stamps are registration
  time, not change time - no transaction trail for the underlying files
  (process hole).**
  **Verification:** UNVERIFIED (builds predate the checkpoint but their ledger
  rows are new).
- **What:** Better Fur - Fine Clothes + Merchant's Hat + Ensrick CBBE-HIMBO
  refit.
  **Source:** user explicitly kept Nexus 69240 and 70589
  (`docs/AGENT_WORK_QUEUE.md` keep-review coordination);
  `records/better-fur-jg1-adoption-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** Ensrick - Collectibles Helper USSEP Forward overlay plugin
  generated and installed.
  **Source:** issue #92 (forward USSEP over Collectibles Helper on twelve
  records).
  **Verification:** UNVERIFIED.
- **What:** issues #106-#118 opened (Solitude confirmation, fix floor,
  ISC-SRDified, survey outliers, DLL-gate batch, UI layer, grass slot, perk
  slot, CoMAP, Synthesis/PGPatcher chain, per-city plan, waterfalls,
  gitignore/records visibility).
  **Source:** survey-ecosystem + survey-standards digests
  (`docs/ECOSYSTEM-SURVEY-2026-08-30.md`,
  `docs/STANDARDS-DIGEST-2026-08-30.md`).
  **Verification:** n/a (tracking).

## 2026-08-30 midday, 14:52 commit wave - process audit and tooling

- **What:** eleven commits (fc4835e..cb40cf2): snapshot-driven LOOT sort +
  SKSE gate checker tooling, curation-state policy, equipment intake policy,
  profile-state ledger docs, LOOT rules, research records, werewolf-totem
  overlay recipe, CRF semantic patch source, vendor-integrity/display/water
  records, ecosystem survey + standards digest, process-audit findings F0-F16.
  **Source:** audit-process agent (`docs/PROCESS-AUDIT-2026-08-30.md`);
  findings filed as issues #97-#105.
  **Verification:** n/a (docs/tools; no profile change).

## 2026-08-30 morning, 09:44-11:19 - Solitude, sound, map, companions

- **What:** Cutting Room Floor 3.1.26 + CRF semantic patch (spriggit source,
  commit 19875a9) + Interesting NPCs CRF patch.
  **Source:**
  `records/cutting-room-floor-3.1.26-compatibility-audit-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** INIGO 2.4C + Bloodchill Manor patch + Official Patch SE.
  **Source:** `records/inigo-1461-2026-08-30.md`; mesh-format caveat filed as
  issue #77.
  **Verification:** UNVERIFIED.
- **What:** Baltimore Weapons; Vikings Weaponry SE + Ensrick mesh port +
  texture cap.
  **Source:** `records/baltimore-weapons-29612-2026-08-30.md`,
  `records/vikings-weaponry-14409-2026-08-30.md` (keep-review equipment
  intake).
  **Verification:** UNVERIFIED.
- **What:** Simple Hunting Overhaul 1.16 + Bruma patch + Dynamic Activation
  Key (dependency).
  **Source:** `records/simple-hunting-overhaul-95943-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** world map: A Clear Map of Skyrim and Other Worlds 4.0 (4 plugins)
  + Water for ENB patch.
  **Source:** research-worldmap agent; `records/acmos-56367-2026-08-30.md`;
  known limitations filed as #81 (LOD32 at DynDOLOD time) and #82 (water
  patch sort order, currently inert).
  **Verification:** UNVERIFIED.
- **What:** sound stack: Sound Record Distributor, Immersive Sounds
  Compendium 3.0, Audio Overhaul for Skyrim SE 4.1.3, AOS-ISC integration.
  **Source:** research-sound agent; `records/sound-stack-2026-08-30.md`;
  USSEP-reversion caveat filed as #89, ISC-SRDified follow-up as #108.
  **Verification:** UNVERIFIED.
- **What:** MCM Helper 1.6.3 installed (unparked on gate pass).
  **Source:** issue #83; `records/mcm-helper-1.6.3-2026-08-30.md`. Gate-only
  basis invalidated later by #140; needs launch re-validation.
  **Verification:** UNVERIFIED.
- **What:** unparks on gate pass alone: Open Animation Replacer (#84),
  Crafting Recipe Distributor (#85).
  **Source:** issues #84, #85 (both closed on the gate result). OAR was
  re-parked 2026-08-31 after #140; CRD still needs launch re-validation.
  **Verification:** OAR FAILED (#140); CRD UNVERIFIED.
- **What:** Simple Dual Sheath 1.5.9 installed.
  **Source:** issue #78 (closed - provenance decision); audit-dualsheath
  agent.
  **Verification:** UNVERIFIED.
- **What:** Scale Nord Armor + Ensrick texture cap + Bloodskal static-glow
  overlay.
  **Source:** compare-41118 agent; distribution follow-up filed as #96.
  **Verification:** UNVERIFIED.
- **What:** Solitude city stack: Whiterun 3D Trellis AIO, Rally's Market
  Stalls + hotfix, Grand Solitude + patch collection, CC Bow of Shadows fix,
  Solitude Docks Updated, Snazzy Location Resources, Snazzy Solitude
  Separated Houses + patch collection, SFCO3-BOS + patch collection, Lux
  Patch Hub + Solitude Docks patch, Lux Orbis patch hubs, Collectibles
  Helper.
  **Source:** issue #106 (Solitude stack as the city decision);
  `records/solitude-city-interior-cell-matrix-2026-08-30.md`,
  `records/solitude-trellis-stalls-installation-2026-08-30.md`,
  `records/city-interior-layering-direction-2026-08-30.md` (commit 30c4679).
  **Verification:** UNVERIFIED.
- **What:** issues #77-#96 opened (Inigo meshes, dual sheath, Light Placer
  re-check, water effects, ACMOS, unparks, artifacts design, SKSE rebuilds,
  texture/blood/landscape decisions, mod-install --replace defect, USSEP
  forwards, Steel Plate textures, IED block, cloak tracking, Scale Nord
  distribution).
  **Source:** morning audit + intake sessions (audit-* / research-* agents).
  **Verification:** n/a (tracking).

---

## 2026-08-29 evening, 17:40-23:36 - keep-review equipment wave

- **What:** commit 2809071 "docs: track new Skyrim playtest requirements".
  **Source:** user playtest feedback after the 17:23 session.
  **Verification:** n/a (doc).
- **What:** keep-review ascending pass installs (Claude cursor opened at the
  oldest keep, Nexus 62271): One-handed warhammers (install-62271), Steel
  Plate Armors + HD textures (install-154073; 4K body-texture question filed
  as #93), Lunar Guard Armor (install-75349), Sagittarius Real Bows
  (install-109490), Bloodskal Blade 4 + No Glow variant (disabled) + Ensrick
  texture cap (install-120399), Akatosh's Talon + Chitin Bow
  (install-121553-162825), Quicksilver's Sword Pack + Ensrick texture cap.
  **Source:** `docs/AGENT_WORK_QUEUE.md` keep-review coordination + the named
  install agents; per-mod records in `records/`.
  **Verification:** UNVERIFIED.
- **What:** Ring of Khajiit replacer installed.
  **Source:** `docs/KEEP_REVIEW.md` decision ledger. **Thinnest trail of the
  wave - no dedicated record file (process hole).**
  **Verification:** UNVERIFIED.
- **What:** Skyking Signs + Unique Signs + Bruma patch + Interesting NPCs
  patch.
  **Source:** `records/skyking-signs-2026-08-29.md`.
  **Verification:** UNVERIFIED.
- **What:** High Poly 3D Wolf Skull werewolf totem replacer installed
  DISABLED pending the overlay build.
  **Source:** overlay recipe committed as 8d51193.
  **Verification:** UNVERIFIED (disabled; inert by design).
- **What:** Varinia companion 1.1.0 + Ensrick six-PEX dialogue fragment fix
  overlay.
  **Source:** `records/varinia-148853-2026-08-29.md`,
  `records/varinia-private-fragment-fix-2026-08-30.md` (commit 5cec4ce);
  upstream report drafted.
  **Verification:** UNVERIFIED.
- **What:** SSE Display Tweaks migrated to official 0.5.25 + Ensrick
  configuration overlay (borderless/fullscreen mirror, LockCursor=true - the
  LockCursor choice is Sol's and contradicts an earlier user complaint; ask
  before flipping, per `docs/INI_AND_PROFILE_STATE.md`).
  **Source:**
  `records/sse-display-tweaks-official-migration-2026-08-30.md`.
  **Verification:** UNVERIFIED.
- **What:** screen-effect QoL trio: Disable Screen Blood, No More Blur on
  Hit, 3rd Person Camera Stagger Remover.
  **Source:** `records/blood-visuals-audit-2026-08-30.md` lineage; the larger
  blood-system decision remains open as #90.
  **Verification:** UNVERIFIED.
- **What:** Interesting NPCs 4.5 + 4.54 update + ILS freeze fix + Abandoned
  Prison combat fix + Cat and Mouse script fix + Survival Mode patch +
  Nether's Follower Framework 2.8.6b.
  **Source:**
  `records/hit-effects-and-interesting-npcs-install-2026-08-30.md`; health
  audit `records/interesting-npcs-party-banter-health-2026-08-29.md`.
  **Verification:** UNVERIFIED.

---

## 2026-08-29 17:23 - checkpoint launch (last known good)

- **What:** launch of the pre-wave profile: main menu reached, save loaded.
  Earlier failure that afternoon (`crash-2026-08-29-16-46-11.log`) was
  resolved before this launch; a play session followed (saves written 18:40).
- **Source:** user session.
- **Verification:** VERIFIED 2026-08-29. **This is the baseline every entry
  above stacks onto. Nothing after this line has been verified.**

---

## Backfill notes - process holes found during reconstruction

1. `mo2-instances/skyrim-se/.mo2-headless-journal/` does not exist; actor
   attribution for ledger transactions comes only from timestamps and agent
   names, not a journal.
2. Three ledger rows (CS AIO build, Lux Water CS patch, QuickLootIE) carry a
   same-second registration stamp, not a true change time.
3. The SLaWF v10.6 install has a fomod plan but no issue or user line naming
   it; its source is inferred from the #107 survey batch.
4. Ring of Khajiit has a Keep decision but no per-mod record file.
5. Launch attempts were not first-class events anywhere; the three 08-31
   failure signatures had to be reconstructed from skse64.log, a threaddump,
   a crash log, usvfs logs, and issue text. This changelog's Verification
   field is the fix.
6. `records/installed-mods.json` and several docs sit modified/untracked in
   the working tree; ledger state and git state can drift (issue #118 is the
   standing example).
