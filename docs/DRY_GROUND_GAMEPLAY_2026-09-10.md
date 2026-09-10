# Dry-ground gameplay control — September 10

**Bounded pass, not completion of #262.** A genuinely new character on current
Default successfully entered Whiterun, moved and stopped twice, saved/reloaded
through Journal and F5/F9, jumped and landed, and quit normally. No new crash
report, member-guard rejection or observed dying/swimming state. #267 still
needs a production-quality observation tool and travel/combat coverage.

This follows the inconclusive waterfront tests in
[PLAYER_OBSERVATION_2026-09-10.md](PLAYER_OBSERVATION_2026-09-10.md). The new
dry-land result isolates successful stopping without changing the input DLL.
It does **not** retroactively prove the cause of the earlier water drift/death.

## Controlled inputs and preservation

- Private profile `Astra Dry Ground 267 20260910`, refreshed from current
  Default, muted local settings/local saves. No copied old campaign or test
  jail-pool patch. Vendor Skyrim Unbound MCM explicitly selected City→Whiterun
  (`$SU_City7`), then Begin Your Adventure. Default gameplay settings unchanged.
- Original engine/native MenuPilot inputs only. No OS focus switching, console
  teleport, coordinate writes, god mode, save cleaning or new mods/DLLs.
- Installed SKSE SHA256 `4e3f618b6a413b6ea3c38e238ebc607e056eebfc34ed72073dd46beea7bd7184`.
  Runtime log confirms `installed_read=1 installed_write=1` for the paired
  Papyrus guard. MenuPilot and currency were unchanged existing builds.
- Owned controller24760/game32664; private desktop never displayed. Controller
  ran 03:51:39.542–04:00:07.887 CDT and exited0 after normal Quit confirmation.
  Its exit is cleanup evidence; actual gameplay evidence is below.
- Original Adventurer3 pair/Default lists unchanged by final hash checks.
  CrashLogger restored exactly, SHA256
  `0a38c67861a8bfafd6640eb8d05398060ecf170621eb7fe2df368aeb9a5c58db`.
  No game/controller or owned Fable process remains; claim `astra/dry267` released.

## Measured behavior

All times CDT. Live coordinates use the independently native/serialized-checked
layout from the preceding report. Read-only asynchronous snapshots retain
identity and repeated-position checks. No unverified health virtual call.

| Action | Evidence |
|---|---|
|World entry|Whiterun Save3 at03:55:03.967; embedded preview shows dry city ground. Live cell1A276/world1A26F, state0; initial position(24876.596,-4695.499,-3003.0457).|
|First move/stop|Auto-Move down events03:55:45.754/46.141. At48.284, position(24862.389,-4551.8223,-2999.7712); identical at50.847 with autoMove0/state0. Approximately144units horizontal displacement followed by a measured stop.|
|Journal save/load|New Save4 at03:56:10.215; currency checkpoint admitted before selecting file4/confirming Load. PostLoad success03:56:45.598; currency admission4/ledger11 at46.070. Position returned within0.002units of saved coordinates.|
|Second move/stop|After reload, Auto-Move down events03:57:18.808/19.915. At22.051, position(24842.395,-4349.93,-2997.6267); identical at24.573, autoMove0/state0. Approximately203units horizontal displacement; no collision-free speed claim.|
|Quicksave/quickload|F5 new Quicksave0 at03:57:35.924; its checkpoint gate passed. F9 PreLoad53.241/PostLoad55.023, currency admission7/ledger11 at55.196. Returned to the second stopped position within0.005units.|
|Jump/landing|Jump down03:58:23.742. Z rose from-2997.6262 to-2930.1235 at24.083; returned to-2997.6267 at26.127, X/Y unchanged.|
|Settled operation|At03:59:39.334, same landed coordinates/state0; unpaused ping39.481. About104seconds after latest reload, including jump/landing. Continued responsive to normal Quit at52.266.|

The first MCM page query ran too early and returned undefined, so the guarded
driver stopped rather than proceeding with an unverified selection. After
observing the actual selected Unbound mod/page, normal native navigation
succeeded. This is a test-driver timing issue, not proof of an Unbound failure.
Final Quit batch timed out because the game exited; it is not marked completed.

The saved Save4 INITIAL prefix independently equals the first stopped position,
serialized CELL=WhiterunWorld1A26F. Full FallrimTools ACHR parsing remains
unsupported for the fixture; the explicit bounded prefix-only result is not a
whole-save certificate. Input bytes unchanged after inspection.

Private Save4 SHA256: `6c18d93232493c965b68e36b875fa5632274002ccf05cd6fed3a962eebae2509`.
Private Quicksave0 SHA256: `691d35a00265309da40a413909b77e04ab9e2a5b043ba819f713253757e30099`.
Raw logs, snapshots and save preview remain in private per-profile evidence,
not in the public mod or repository. Save1/2 are pre-world staging saves, not
preferred healthy Continue fixtures; Save4/Quicksave0 are the relevant controls.

## Remaining work

This validates limited ordinary character movement and save/load on current
Default. It does not validate combat, broad travel/cell transitions, hours of
play, original campaign currency migration, or the experimental load-admission
adapter. The original member-overrun fix has its separate exact-failing-save
proof; #262 remains open until the broader requirements are satisfied.

Actual Fable5.1 session2a8fe176 completed a read-only admission lifetime review
alongside this run. Its proposed dual-destructor observer is **not applied**:
parent flagged exception containment, bounded logging, complete trampoline
budget and precise ABI/coverage requirements. No speculative cleanup hook or
lease-release behavior was installed to make these tests pass.
