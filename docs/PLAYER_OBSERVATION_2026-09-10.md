# Player observation and movement acceptance — 2026-09-10

Tracking: #267 (test validity), supporting #262 (actual crash/load/gameplay).
**Both remain open.** No new DLL, plugin, vendor edit or Default change in this
work. The copied-save test ended normally; originals and logger settings were
preserved. Movement was observed, but controlled stopping/dry-land gameplay
was not established. Do not treat this as completion of the crash goal.

## Independent position evidence

`audit/player_layout_audit.py` rejects an unknown executable or address library
before interpreting offsets. Its eight synthetic tests cover identity refusal,
version/format/count/length rejection and bounded reads. All 24 exact-build
checks passed locally; CI runs the synthetic tests, not the private executable.

- Skyrim1.7.104 executable MD5: `113faeb71fd8f62b26d0c8627299ab40`.
- Address-library SHA256: `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`.
- Native SetPosition RVA2F0EF0 compares/assigns reference position at54/58/5C,
  reads parent cell at60, cell interior flag at40, and worldspace at128.
- Address ID403521 resolves the player singleton to3230778; the observed
  player has FormID14 and primary vtable19296C0. Native input code independently
  uses actor-state wordC8; the raw flags are safer evidence than unverified
  Actor health/death virtual calls. No such virtual calls were added.
- Asynchronous memory reads are observations, not atomic engine snapshots.
  The private probe checks form types, singleton stability, finite values and
  repeated position bytes. Changing positions must not be presented as stable.

The independent serialized INITIAL prefix from new-character Save5 was:
`(-65133.664, 96466.03, -13887.649)`, serialized CELL=Tamriel0000003C.
Immediately after this run's cold load, live X/Y/Z agreed exactly. The live
parent cell was000092BC; its worldspace was0000003C. The preceding run's settled
Z differed by about0.35units, so it was not claimed to match bit-for-bit.

The pinned FallrimTools61bb57d full ACHR parser refused this record. The new
original Java consumer keeps default strict refusal and permits only an
explicit `--prefix-only` fallback, labeling the remainder unvalidated. Its
bounded type4 prefix is27bytes; type6 is34bytes. It does not reinterpret opaque
globalData2 as an invented position format, call a writer, or clean a save.
This establishes limited coordinate evidence, not whole-save health.

## Input findings

MenuPilot's existing `input.tap` sends one down packet, waits, then sends one up.
It does not emit continuously held input. Native PlayerControls input entry
7AD900 initializes its movement vector each packet, and the Forward handler
7B380A writes positiveY/clears auto-move. This makes dispatch success inadequate
evidence of walking. The initialization constants are in a non-file-backed
region; a source review's assertion that they are necessarily zero was not
accepted solely from the instruction bytes.

Actual Fable5.1 read-only review completed in session9bfac0cd, with no delegated
writes or agents. Its proposed repeated-dispatch implementation was **not**
deployed: task ordering, cancellation and event lifetime need evidence first.
An existing-event alternative was investigated locally: AutoMove vtable19353D8
slot6 points to7B3130, which toggles data+24 on a nonzero-value/zero-held-duration
press. Its CanProcess compares UserEvents+ C0, named `Auto-Move` by the pinned
header. This supported trying the ordinary toggle, not teleportation or direct
position writes.

## Private runtime test, all times CDT

Profile: `Astra Movement 267 20260910`, cloned from current Default, local muted
settings/saves. Same installed SKSE4E3F618B and MenuPilot1A1D5CEC. Only a copied
Save5 pair was initially present; plugin-presence and currency-checkpoint gates
passed. The controller and game ran on a private QuietWorker desktop that was
never switched to the user's desktop. No minidump was requested.

| Time | Observation | Limit |
| --- | --- | --- |
|03:37:29–03:43:11|Owned controller15556/game30340 ran and exited normally|Controller exit is cleanup, not certification|
|03:38:58.780|Normal Continue completed PostLoad; currency ledger694 admitted|Main-menu query timed out during loading then reported the now-closed menu; not a crash|
|03:39:20.999|Position matched serialized Save5 exactly; state0, autoMove0|No unverified health virtual call|
|03:39:33.357–36.470|Auto-Move toggled on/off, about3.1seconds between down events|Only one movement direction tested|
|03:39:37.648|Position(-64287.477,97004.46,-14122.364), state400, autoMove0|Swimming flag set; this is displacement, not controlled stopping|
|03:39:51.213|Position continued to(-63549.152,97590.48,-14122.364), autoMove0|Water flow/physics versus input handling not isolated|
|03:39:54.045|New Save6 made in this water state|Unsuitable as a healthy walking fixture|
|03:40:11–03:41:03|Life-state observations1 then2; cell changed to929B; repeated automatic reload of Save6|Character death, not a process crash; cause of death not proven|
|03:40:17.911,41.887;03:41:23.298|Three death-triggered PostLoad successes; corresponding currency admissions|Not a substitute for deliberately controlled reload acceptance|
|03:41:37|Native UI `menu.open Journal Menu` used to recover from repeat deaths|Not credited as successful ordinary Journal hotkey behavior while dying|
|03:42:08.867|Selected/confirmed safe Save5 through Journal; PostLoad success|Position returned exactly to saved starting values|
|03:42:28|Shorter auto-move pulse, about0.22seconds between down events|Moved122units initially; later entered water again despite autoMove0|
|03:42:43.905|Save7 captured this second water trial|Also not a healthy fixture; retained as evidence, not default Continue|
|03:43:09.370|Normal Journal→Quit→Desktop confirmation|Final callback timeout expected because the process exited|

No new crash report was produced. No member-bound rejection was found in this
run's SKSE log. Currency's `source-reference-safety-rejected` counters during
death/reload are a different diagnostic, not member-guard failures. Optional
follower-mod lookups still appear in Papyrus; this does not authorize installing
those mods. All raw logs are archived privately per profile before another run.

The waterfront preview and swimming/death sequence mean this fixture is not an
adequate dry-land control. Do not silently blame the Unbound marker, city mods,
physics, survival balance or the input driver. Next movement test should use a
genuinely new character with an explicit dry start, check position/state before
saving, and demonstrate both sustained movement and stopped displacement.

## Preservation and next steps

- Default modlist/plugins/loadorder hashes unchanged by the controller finally.
- Original Adventurer3 ESS/co-save hashes unchanged; no original deleted,
  overwritten, cleaned or migrated. Test Save5 input unchanged as well.
- CrashLogger configuration restored byte-for-byte, SHA256
  `0a38c67861a8bfafd6640eb8d05398060ecf170621eb7fe2df368aeb9a5c58db`.
- No game/controller/Fable job remains; live claim `astra/movement-267` released.
- Save5 SHA256 `77e70fd28e818b0c762cdf9cc88044072f3b456ef6a279c4de5c311883126425`.
  Save6 SHA256 `7472fb343e2c042946878300038b4bbb3e54cf60cb420ee8020a97201199b5e9`.
  Save7 SHA256 `8a2791faf20b7694bebd8e0ca013c7e347d22ca276d68487f840a9245fc37fbe`.

The original member-overrun fix retains its separately documented exact-save
evidence. This run neither invalidates that evidence nor closes the broader
goal. Native load-admission lifecycle/refusal behavior, dry-land gameplay,
Unbound failure recovery, and the original campaign's missing currency
checkpoint decision remain open. No campaign migration decision was made.
