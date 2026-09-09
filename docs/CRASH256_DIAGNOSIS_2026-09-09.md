# September 8 repeat-load crash: evidence and recovery boundary

Owner: Astra, with an independent read-only Claude Fable 5 review.
Tracking: [#256](https://github.com/Ensrick/skyrim-mod-assistant/issues/256),
[fresh-character automation #227](https://github.com/Ensrick/skyrim-mod-assistant/issues/227).

## Outcome

The current mod configuration successfully initialized a genuinely new character,
saved it, reloaded it in-session, and loaded that same save after a cold restart.
No further mods were removed, reinstalled, upgraded or enabled. Default modlist
and plugin-list hashes are unchanged. This is a demonstrated recovery path for
the repeat-load failure, **not a repair of the old campaign save or proof that
every crash and gameplay problem is solved**.

The immediate September 8 failures strongly implicate saved Papyrus/MCM state
left behind after mod removal. The earlier September 7 `-Move` failure is a
different top-of-stack signature and remains unresolved under #256. Do not
close that issue or call the entire configuration production-ready.

## What changed the diagnosis

- Ten of eleven September 8 crash logs contain the same live R13
  `BSScript::Internal::CodeTasklet` at `SKI_ConfigBase.OnConfigManagerReady`,
  `SKI_ConfigBase.psc:289`, called through `MCM_ConfigBase.psc:64`.
- Those ten also contain `[None].TrueHUD_MCM.OnConfigManagerReady` and invalid
  assignment messages. TrueHUD and QuickLoot DLLs are absent from those runs.
- The latest crash, `crash-2026-09-08-23-26-20.log`, faults at
  `SkyrimSE.exe+148EF80`, `mov eax,[rdi+0x28]`, with RDI=1 (read address 0x29).
  Address-library ID 104253 is `RE::BSScript::Object::DecRef`, as mapped in the
  installed CommonLibNG source at
  `skyrim-tools-source/BetterThirdPersonSelection-1.7.104/external/CommonLibNG/src/RE/O/Object.cpp`.
  It is not a Havok function. Behavior-graph names in scanned stack memory are
  not proof that an animation DLL caused this crash.
- The corresponding LaunchProbe log loads the **September 8 01:56 Adventurer3
  autosave**, not a fresh game. The first load reports failure, a second reports
  success at 23:26:19.505, and the process crashes less than one second later.
- Its Papyrus log reports missing `TrueHUD_MCM`, invalid saved type information,
  missing `LoadConfig`, and the `[None]` MCM chain. The save's serialized plugin
  table still contains **TrueHUD.esl and QuickLootIE.esp**, both currently absent.
- New-game logs have successful MCM registration without that removed-TrueHUD
  failure chain. An independent Fable review reached the same leading hypothesis.

This is strong converging evidence, not a controlled demonstration that TrueHUD
alone is the original corrupting writer. Restoring removed mods, deleting saved
script instances, or bypassing the faulting instruction would not be justified
by this evidence. No such changes were made.

## Runtime observations (America/Chicago, September 9)

All runs used an off-screen Windows desktop, master volume zero, and the separate
MO2 profile `Astra Crash256 - New Game` with `LocalSaves=true`. The game received
engine/Scaleform commands through MenuPilot; no OS keystrokes, focus switching,
UAC interaction or Steam restart was used.

| Run | Positive evidence | Scope |
|---|---|---|
| Fresh 01, PID 44940 | New Game confirmed; `kNewGame` 01:46:01; successful MCM registration; RaceMenu opened | Initialization observation only; character creation not finished before watchdog |
| Fresh 02, PID 48608 | `kNewGame` 01:52:16; character creation finished; `kSaveGame` 01:53:48; unpaused 01:54:05; manual in-session reload `kPostLoadGame success=1` 01:57:51; still unpaused 02:00:44 | New game + save + in-session reload; more than 170 seconds beyond successful reload |
| Cold 03, PID 35040 | Main menu 02:02:51, successful load of exact Fresh 02 save 02:02:55; unpaused 02:03:26, 02:04:12 and 02:05:22; watchdog ends run 02:07:08 | Cold save-load diagnostic, not a currency/gameplay acceptance certificate |

The main menus appeared roughly 47, 42 and 41 seconds after process creation,
respectively. The later load in Fresh 02 was deliberately selected manually;
it was not a slow automatic boot/load attempt. The test character stayed in the
Skyrim Unbound starting room, not a dungeon or combat encounter. Bounded timeout
termination is not a clean-exit test and is not counted as one.

An initial isolated attempt never started Skyrim: MO2 waited on an advisory
about elevated Steam. That is a failed launch, not a successful alive timeout.
The tested remedy uses MO2's existing **No / Continue without elevation** choice
temporarily, restoring `ModOrganizer.ini` afterward. It never grants elevation.

### Saved evidence (private, not distributable save payloads)

`records-work/crash256-20260909/` contains pre-change crash/Papyrus/SKSE logs,
profile lists, configuration backup, and separate per-run log snapshots. The
disposable `.ess` and `.skse` pair remains only in the isolated profile's `saves`.
The game named it `Adventurer`; the attempted UI text-field rename did not alter
the engine's saved name. Its separate path and exact filename identify it:

`Save1_0E3A786B_0_416476656E7475726572_SkyrimUnboundRoom01_000002_20260909065348_1_1.ess`

| Artifact | SHA-256 |
|---|---|
| Original failing autosave | `ed8255cd464f8e17ba19aad5f2154549d9bff51ccc5fb8165473fd26fb1ef8f9` |
| Disposable fresh save | `657d57c98b6495f57a7672b2f059ab6c0088f21eb23a352d4fb598389c2a36ce` |
| Unchanged Default modlist | `d688858ad8d748598ebd524361220674af91dbd2f0994bf3dd1600ee01d01f76` |
| Unchanged Default plugins | `be8dd98553339edffc0b1fa624a53a102659c9c0460219e700c80670f82ff95c` |

## Repairs to the testing process

1. `audit/save_plugin_gate.py` independently reads SSE version-12 `.ess` headers
   and full/light plugin tables, including uncompressed, zlib and raw LZ4 saves.
   It checks active MO2 plugins and engine-forced official content from the
   installed `Skyrim.ccc`. It has no save-writing operation or network access.
2. `launch_verify.py` now refuses automatic loading of a save containing removed
   plugins, before launching. It also reads **settings.ini**, not the nonexistent
   settings.txt, to honor profile-local saves. A passing plugin-table check does
   not certify Papyrus health, script-only removals, DLL state or currency state.
3. The isolated launcher now uses canonical profile INIs, enforces local saves,
   handles CRLF audio settings correctly, clears inherited autoload commands,
   refuses pending MenuPilot batches and existing game/MO2 processes, requires
   an already-held claim, and restores temporary MO2/global plugin configuration.
   Explicit cold loads are confined to its test profile and checked for missing
   plugins. It no longer maps controller timeouts to a success exit code.
4. MenuPilot refuses to queue commands when Skyrim is no longer running, rather
   than trusting a stale log. This is a basic admission guard, not full per-PID
   session binding; commands still require explicit review after a mid-batch exit.
5. Eleven synthetic parser/gate tests, one no-game MenuPilot test and the ten
   existing launch-verifier self-tests pass. These fixtures contain no vendor
   assets or player saves.

The isolated runner remains a diagnostic primitive, not the complete #227
state machine. Do not infer acceptance from its exit code, a main menu, or an
open character-creation screen. Fresh-game selection, confirmation and runtime
evidence were explicitly inspected during this investigation. General
`launch_verify.py` still has an interactive launch route; it was **not** used to
launch overnight. Only its self-tests and dry-run path were exercised.

Format references, not copied implementation: FallrimTools
[Header](https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/Header.java),
[ESS](https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/ESS.java),
[PluginInfo](https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/PluginInfo.java).

## Remaining gates and decisions

- **Campaign choice:** start a new character under the current set, or separately
  investigate migration/restoration for Adventurer3. The original files are
  untouched. Do not press Continue into that old save expecting this investigation
  to have healed it. No automatic save cleaning is approved by this report.
- **#256 original crash:** September 7 `+0CEF4DB`, ASCII `-Mov` used as an index,
  is not proven fixed by avoiding the newer removed-script failure. It needs
  representative-world testing with an admitted current-build character.
  Its caller ID 68617 maps to `BSInputDeviceManager::PollInputDevices`; do not
  conflate this input-processing signature with the newer Papyrus tasklet crash.
- **#239 / cloak receipts:** preflight reports 383 current inputs versus 376 in
  the weapon manifest, resolver ordering drift, and stale cloak fingerprints.
  Keep these gates red until the existing approved patches are refreshed and
  reverified; do not install more mods as a workaround.
- **Currency admission #217:** even the genuinely new starter save above lacks
  the v2 checkpoint expected by `currency_save_gate`. Thus "predates the ledger"
  is not a reliable age diagnosis by itself. The cold load was a plugin-admitted
  diagnostic, not a currency-approved play save. The native log explains why:
  at 02:02:50 initialization fails resolving the accounting backend
  `00000F:Skyrim.esm` as the required form type, and the bridge remains inactive.
  This is a concrete runtime failure, not a reason to weaken the checkpoint gate.
  Diagnose `Bridge.cpp` / `ResolveForm<TESBoundObject>` and its runtime bindings.
- **#157:** several missing-class/binding warnings persist before and during
  genuine new-game initialization (USSEP retro439, Bruma classes, HLIO aliases).
  They cannot all be explained as old-save residue. Optional-follower probes are
  not reasons to install those followers. No causation of this crash is established.
- **#102:** five enabled mods lack ledger entries in current preflight. Keep/ledger
  reconciliation remains necessary; no Keep decisions were changed overnight.

There is no whole-modpack launch clearance from this report. It establishes a
working fresh-game/load path and prevents a known invalid automated test input.
The remaining gates above must be resolved before broad gameplay acceptance.

Final isolation check: no Skyrim/MO2 test processes remain, no pending MenuPilot
batch remains, and `ModOrganizer.ini` matches its pre-test SHA-256
`dfe909806cecf03ab08aca4115c348dc9cf62671e33ee7b80ad600d3ebd8e615`.
Original saves were not changed. The existing general preflight also made its
normal 178 MiB save-backup snapshot; no conversations or user data were deleted.

## Second Fable review: original input crash

A separate bounded read-only Fable 5 CLI run reviewed the September 7 log and
MenuPilot's actual event creation/dispatch. No supported native patch was found.
The invalid index is consistent with accessing the input manager's devices array
using string bytes instead of an input-device enumeration. The decoded event
address is in engine static storage, whereas MenuPilot creates heap events.
MenuPilot dispatches synchronously on an SKSE task and intentionally does not
free its synthetic event; no demonstrated use-after-free was found there.

No September 7 consumed-command archive is present, although archives from
surrounding dates remain. That supports automation having been idle, but archive
absence is not absolute proof (files might have been removed). We do not adopt
the stronger claim that any DLL is conclusively exonerated by this alone.

Comparing the September 7 Crash Logger **SKSE PLUGINS** section against the
successful September 9 cold run's SKSE **loaded correctly** entries gives exactly
two removals and no additions: **TrueHUD.dll and QuickLootIE.dll**. This is a
filename-set comparison, not binary-hash equivalence or proof of guilt. Do not
reenable either just to experiment on the user's campaign. Capture a new sample
if the original input signature recurs under the admitted current configuration.

The currency gate's misleading save-age wording was subsequently corrected in
commit `690685d`, without weakening admission. Its twenty tests pass. The actual
currency bridge initialization defect remains open under #217.
