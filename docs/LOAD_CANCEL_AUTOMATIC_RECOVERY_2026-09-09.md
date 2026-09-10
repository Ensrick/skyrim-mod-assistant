# Automatic rejected-load recovery — September 9, 2026

Parent [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) stays
OPEN. This extends the [manual native cancellation evidence](LOAD_CANCEL_NATIVE_RECOVERY_2026-09-09.md).
It does not repair Adventurer3, deploy admission rules, or certify gameplay.

## Negative control and corrected runtime result

Immediate-message candidate SHA256
`7FE220568A965318309F3544E90BFD69582A62835E472C5D4D3A914ECEF363E0`
called the original failure notifier then queued CancelLoading immediately.
In isolated PID29544 rejection and native input-flag clearing worked, but the
movie remained CharacterSelection. Normal Cancel input was needed to return
to Main. Controller exited normally23:10:33.623 CDT. **Partial failure**, not
automatic recovery success. Private evidence: `records-work/load-request-20260909/automatic-recovery/`.

Deferred candidate SHA256
`16FA95D2DB9702264E395C9A8E4796C426BEFAF7A782246BEEA5ED576EB78EF5`
schedules a UI delegate after native failure notification. Existing SKSE
UIManager::ProcessCommands drains native events before delegates; the delegate
queues CancelLoading for the next native pass, using the engine factory,
reference-counted string setter and Main Menu kUpdate handler. No raw menu
reset, flag write, manual diagnostic cancel, Back input or movie recovery
invocation was used in this corrected test.

PID31576/controller31124 ran on the muted private desktop with a dedicated
**Astra Load262 Auto Recovery deferred** profile. Autoload was disabled; only
an exact copied Adventurer3 Autosave3 pair was available. Main Menu opened
23:12:31.894 CDT,34.445 seconds after probe attachment.

| Test | Actual evidence |
| --- | --- |
| Baseline | Engine Down selects New; Up returns to Continue |
| First confirmed Continue | Exact `.ess`, reject=1, target not entered; generation1 recovery; Main23:13:22.591; normal Down/Up work |
| Second confirmed Continue | Same rejection, generation2; Main23:13:58.982; normal Down/Up work |
| Native state after both | MainMenu+6D/global3258201=0/0; MenuControls+83/remap82 and DirectionHandler+29=0; registered handler=1, count9; bounded reread stable |
| Exit | Normal Down/Accept selects Quit and confirms exact desktop prompt; controller exit0 at23:14:10.772 CDT |

Neither rejection emitted SKSE pre/post-load messages. LaunchProbe records
spinner open/close, not a successful world load. The final MenuPilot batch
timed out because Quit terminated its process; normal controller exit0 is
the terminal evidence. Latest crash remained the real20:12:50 report.

Private evidence: `records-work/load-request-20260909/automatic-recovery-deferred/`:

- skse64.log SHA256 `144B8EDFC1F9AD406BE34A11535A865E9084E3565E9DB60EF9FE087F1CE9A2BF`
- menupilot.log SHA256 `F6B057B6A0D681181E0C1706734DE37952620F6C77B1BB037D4CB26B2E50ABFA`
- LaunchProbe.log SHA256 `4D5002564E6155E3CF8E254D3915AB7E2A7358EB3DC2883755C8A890F1B5BEB1`

## Published source and later installation hardening

Source [d8943a1](https://github.com/Ensrick/skse64/commit/d8943a1fe8dcf444836583e6d57250c3caf5f31c)
adds paired failure handling at625FFE to the diagnostic request hook625FF5.
Both original call sites are byte-checked when recovery is requested. Only
our deliberate rejection sets the thread-local, one-use recovery eligibility.
Original failure handling always runs first. Deferred tasks skip superseded
generations and queue only for Main Menu without Journal.

After runtime testing, installation was hardened: check trampoline capacity
before either edit; failure wrapper before request interception; check return
values and avoid a false success log. A failure wrapper left without a request
wrapper only forwards native failure. This is not an atomic patch transaction;
SafeWriteBuf returns void, so OS write-error handling is not established.

Final local build SHA256
`D01E1C2A0F29F9936B20488D00BD62DF15BA631F62733F1D457DCA2E16A9E2A0`.
This exact post-hardening binary is **not runtime-tested or installed**.
Local full DLL build and extracted-production tests pass:

- 1,572,864 request forwarding/rejection/failure-order/one-use cases.
- 35 UI factory/eligibility/string-release/deferred-generation cases.
- 48 paired-installation capacity/order/failure cases.
- Rebuilt existing inner-load argument regression:2,048 cases.

Mocks do not prove engine ABI, preservation or code-write atomicity. Hosted
Windows/Linux request-probe run34436908793 and load-argument run34436908784
PASS at this revision. Full build34436908858 subsequently PASS, completed
2026-09-10 04:24:15 UTC. No Fable verdict is claimed for this change.

## Restored state

Both wrappers finished. Root SKSE DLL `CC2F98A4` and PDB `45279100` are restored.
Permanent MenuPilot remains `1A1D5CEC`; manual cancel support was not installed
for these tests. No game/controller remains. Claim astra/load262-auto-recovery
released after verification. Default lists and ModOrganizer.ini match their
before-images. Original Autosave3 ESS `ED8255CD...F8F9` and co-save
`E708EC7C...A1CF` match the full hashes in the preceding report. All38 ordinary
ESS remain. Disposable pairs were moved to evidence/input-copies after exit;
originals were not moved or edited. No vendor changes, removed mod restoration,
save cleaning, campaign migration, or Keep decisions occurred.

## Required next gates

1. Test exact final candidate through Journal rejection and subsequent valid
   load/new save/reload. Main-menu recovery is not character preservation.
2. Resolve stale cancellation window: a generation check before enqueue does
   not establish safety if a newer request starts before message consumption.
   Need serialization evidence or a guard before production acceptance.
3. Implement actual requested-save plugin/currency admission, bounded parsing,
   file identity and useful in-game refusal feedback. Exact-name diagnostic
   rejection is NOT ordinary-load protection; none is deployed yet.
4. Verify quickload/other relevant routes and sustained gameplay explicitly.
5. Continue original Adventurer3/Papyrus diagnosis. Missing saved MCM state is
   documented; the corrupting writer is not proved. Recovery versus a new
   campaign remains an owner decision; rejection is not save repair.

Separate stale weapon/cloak proof drift #253 remains; this test did not reorder
or regenerate the configuration to hide it. Full crash-repair goal stays active.
