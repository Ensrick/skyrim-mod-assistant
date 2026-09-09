# BTPS 1.7.104 control-map corruption repair

Tracking: [#256](https://github.com/Ensrick/skyrim-mod-assistant/issues/256).
Installed September 9, 2026, 12:23 CDT. Targeted runtime verification passed.

## Finding and correction to the earlier diagnosis

BTPS `Util::GetControlsEnabledPtr` selected a runtime layout using only
`version().patch() > 0x400`. Skyrim **1.7.104** therefore incorrectly selected
offset **0x118**, despite being newer than 1.6.1130. On this executable, 0x118
is the **ControlMap input-context stack count**, not the control flags. The
correct flags offset is **0x120**.

The enabled object-cycle feature binds its modifier to scan code42 (Left Shift).
Its press/release handler clears/sets the mouse-wheel-zoom bit, `1 << 9`.
The faulty release path consequently adds512 to the context count: 1 becomes513
or 3 becomes515. The engine then reads beyond the real context array.

The September7 crash at `SkyrimSE.exe+0CEF4DB` had an ASCII `-Mov` value used
as an array index. Exact disassembly corrects the earlier Fable/root interpretation:

| RVA | Meaning on the reviewed executable |
|---|---|
| CEF45E | Read context count from `[rdi+0x118]` |
| CEF46C | Read context data pointer from `[rdi+0x108]` |
| CEF473 / CEF475 | Decrement count; point RBX at the last context element |
| CEF4D8 | Read context ID from `[rbx]` into RAX |
| CEF4DB | Index ControlMap's context map using that ID; original fault |
| CEF4F1 | Only now read the event's actual device ID from `[r13+8]` |

RDI is **ControlMap**, not BSInputDeviceManager. The caller is indeed input
device polling, but that does not make the faulting index a device enum.
The source write, exact binary layout, deterministic corruption regression and
live corrected-path observation establish a concrete causal repair. We did not
reinstall the faulty binary to deliberately corrupt another running game, nor
claim a time-travel trace of the original crashing session's last writer.

## Implementation and provenance

- Replace patch-number-only comparison with the complete four-component version
  comparison against1.6.1130. Retain the pre1130/non-AE layout branch. Return null
  for a missing singleton so the callers' existing null checks remain effective.
- Keep existing input behavior; no suppression, index clamp, blanket input hook,
  removal of BTPS, or save editing. Future runtime layouts still require review.
- Source commit `c159d8e`, on top of previous selection-trampoline repair98d5a5e,
  in local `skyrim-tools-source/BetterThirdPersonSelection-1.7.104`.
- Complete source delta and native tests: [published patch](../patches/btps/control-map-offset-1.7.104.patch).
  The standalone CI test compiles the exact helper extracted from that patch.
- Build: VS2022/MSVC14.44.35207, CMake **RelWithDebInfo**, existing CommonLibNG
  `70c1acd5261210982bd52f6d4468a082fe04d798`. Util.cpp was rebuilt and DLL relinked.
  An exploratory Release build was not deployed.
- Preserved preexisting uncommitted compatibility changes in the source checkout.
  This receipt is not a claim that the entire checkout is clean/reproducible from
  the single new commit. Publishing all older compatibility deltas remains a
  release gate before distributing the complete binary to users.
- Replaced only our existing overlay **Better Third Person Selection 1.7.104
  Native Overlay - Ensrick**, same enabled state and priority326. Vendor files,
  BTPS settings, meshes and ESP untouched. Included Apache license, PDB and own
  source patch. No third-party mod or Keep decision added.

| Artifact | SHA-256 |
|---|---|
| Deployed DLL, 2,844,160 bytes | `47D6D795D69A060C359F04F598EE77589183EB7B5B35B38C8C07D91698838CC1` |
| Previous overlay DLL | `FDFD14DF622E9F708133F2D6CEB0F3DA43270179523DCF0595C50C04AC555542` |
| Untouched vendor DLL | `CE24158A1AAC15E7984D4280CFF5A71B9FF75290DF8803D7C03C5042454D627C` |
| Local overlay ZIP, 15,903,887 bytes | `6B8E29B636CE31FBE5F819A6B066BE664A40C7B9A36E507B5A5531860A58B86E` |
| Reviewed SkyrimSE.exe | `846EFCCF0C1374D71F892907F46549560F2FCB0A75CB87A3EED438BAA0F1402F` |

Install transaction: `20260909T172355268Z-f6b13f6d00b4`.
Receipt: [build/install record](../records/source-builds/ensrick-btps-controlmap-1.7.104.json).
Private package/evidence root: `records-work/btps-controlmap-20260909/`.

## Verification

1. Native regression reproduces old count3→515. **32,768** production-helper
   version/pointer/memory-isolation cases pass, plus version boundaries and null.
   Only the selected flags field may change during enable/disable.
2. Prior selection-trampoline native ten-case regression still passes.
3. `audit/btps_hook_audit.py` verifies12 exact executable checks, including all
   previous hook spans/call destinations and five context-mapper checks.
4. `audit/read_controlmap_snapshot.ps1` opens the exact hash-guarded executable
   with read/query rights only. It bounds context reads, records process identity,
   and rereads the header to detect change during the snapshot. This is not an
   atomic engine-state capture or a write-attribution debugger.
5. Muted private desktop, disposable profile **Astra BTPS Context Fix**, current
   Default mod/plugin lists. No OS keyboard/focus injection, campaign save edit,
   visible window or audio. MenuPilot sends engine events only.

| Run (CDT) | Observation |
|---|---|
| First, PID16876, 12:24:27–12:31:43 | Loaded admitted fixture; currency admission3 complete12:25:17;22 modifier cycles; responsive; actual quicksave12:27:05; confirmed Quit→Desktop, controller exit0 |
| Hold12:25:58 / release12:26:02 | Count1/capacity10/context0 unchanged; flags `FFFFFDFF` while held, `FFFFFFFF` after release |
| After20 rapid cycles12:26:42 | Count1/capacity10/context0, flags `FFFFFFFF`, stable reread |
| Cold, PID23936, 12:32:16–12:35:49 | Loaded the new quicksave; currency admission3 complete12:33:00; two more modifier cycles; responsive; confirmed Quit→Desktop, controller exit0 |
| Cold hold12:33:35 / release12:33:50 | Count1/capacity10/context0 unchanged; flags `FFFFFDFF` then `FFFFFFFF`; stable reread |

New disposable save:
`Quicksave0_626DC7A8_0_416476656E7475726572_SkyrimUnboundRoom01_000003_20260909172705_1_1.ess`
SHA-256 `CAC5034D4FFB630F81E197FD67FF1E32C1F6AEFF411247B46A5F55FB4BE8114C`.
Plugin and currency checkpoint admission passed before cold load.

No new crash log appeared; latest remains September8 23:26:20. Both exits were
the actual game menu's desktop command, not watchdog termination. MenuPilot's
last input-down exits the process before it can report batch completion; its
five-second reply timeout is not itself a crash or a clean-exit certificate.
Controller exit0, process absence and fresh log review provide the other evidence.

Final check: no owned game/MO2 processes or pending MenuPilot batch remain.
ModOrganizer.ini restored byte-for-byte to SHA-256
`DFE909806CECF03AB08ACA4115C348DC9CF62671E33EE7B80AD600D3EBD8E615`.
The launcher now uses the tested nested-job QuietWorker containment and no
longer kills processes selected merely by game name/start time.

## Remaining acceptance and decisions

- This is targeted input-crash verification in the Unbound starting room, not
  hours of combat/city traversal or whole-modpack certification. Normal fresh-save
  gameplay remains the next acceptance step. #256 retains that soak-test scope.
- September8's separate Papyrus/MCM repeat-load fault remains associated with
  the old save's removed TrueHUD/QuickLoot state. Fresh-character recovery and
  admission checks are verified; the old campaign is **not repaired**. Do not
  automatically clean it or reinstall removed mods. User chooses any migration.
- CRF/Lux CELL conflict, known warning/ledger backlog and gameplay feature issues
  are separate; none were silently decided here.
- Two earlier bounded Fable read-only reviews contributed to the investigation.
  This specific follow-up Fable review exhausted its cost bound with no final
  verdict. Do not label this repair independently approved by Fable.
