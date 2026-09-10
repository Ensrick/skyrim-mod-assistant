# Save admission: native failure ownership and recovery

Status: experimental source correction and bounded runtime regression PASS.
Issue #262 and overall crash/gameplay acceptance remain OPEN. Normal installed
SKSE does **not** link experimental admission; this report is not deployment
approval or a campaign migration decision.

## Correction and regression evidence

SKSE commit `d3b0ee915280dcd1d34e7524e1d17267b6d0373d` removes the assignment
which enabled our deferred `CancelLoading` recovery whenever the native outer
load target returned false. Native false is not equivalent to our early veto:
the target can transfer its stream to an error callback before returning.
Only a deliberate rejection before entering that target now enables our UI
recovery. The native failure notifier and ownership/result forwarding remain.

The old forwarding tests compiled out `ENSRICK_EXPERIMENTAL_SAVE_ADMISSION`.
A second executable now compiles that branch from the actual production source,
with mocked admission/engine services. Its 144 combinations cover enabled/off,
accept/refuse, configured veto, native true/false, retained/transferred/unknown
stream ownership and three recovery modes. Before the source fix it failed at
the recovery-eligibility assertion; after the fix all 144 pass. Assertions now
report stderr/exit1 instead of becoming unhandled exceptions. The original
1,572,864 forwarding cases and UI/installation/Windows snapshot tests also pass.
Both CI runs 34473620839 and 34473620871 passed. Full experimental Windows DLL
build succeeded; neither mocks nor compilation prove native callback behavior.

Test DLL SHA-256:
`E6E2F916AB1A656C48C368BBE2C0ACFB4199E131C3622ADBCFDA69A78BC6F1A9`.

## Native callback findings

Read-only inspection uses pinned executable MD5
`113faeb71fd8f62b26d0c8627299ab40`. No native error branch was bypassed.

- Late transfer at628414 installs vtable190B068: destructor62E0A0,
  callback62CD70. This is the same callback type used by the earlier achievement
  prompt; disabling that prompt does not remove its later error-list use.
- Transfer at628E24 installs vtable190B0C8: destructor62DFC0, callback62C500.
  Destructor62DFC0 destroys a remaining nonnull stream through its virtual
  destructor with flags1, like62E0A0.
- Both callback types can transfer their stream through task constructor62B950.
  The second callback can do so on both branches of its initial button test;
  treating one arbitrary button as harmless cancellation is not justified.
- Constructor62B950 calls632B30 with typeD0000010, which is stored at task+0C;
  ownership moves to task+18 and callback+10 becomes null. This is more than
  merely similar payload layouts: dispatcher625B90 explicitly compares
  task+0C toD0000010 at625DA3 and branches at625DA9 to625FD1, the path containing
  our outer request call625FF5. The callbacks submit negative-type tasks via
  the manager+3B8 queue; the dispatcher obtains tasks through that queue's
  virtual pop. This establishes the native type/routing association, not that
  every possible queued task necessarily reaches dispatch without alteration.
- A resumed consumed stream is not a fresh snapshot: `Begin` currently requires
  position0 and undecompressed data. Supporting legitimate deferred resumes
  needs explicit lifecycle handling; silently treating them as fresh inputs
  or skipping validation is not acceptable.

Private disassemblies remain under records-work. No executable bytes, licensed
payloads, original saves or private dumps are included in this report.

## Runtime regression, 06:53–06:57 CDT

Owned Skyrim PID34736/controller36132 ran on the muted private desktop, using
profile `Astra Load262 Lifetime native-recovery`. Input fixture was a copy of
the exact previously failed texture quicksave54692023/co752DD9E3. Texture fix
was explicitly enabled; admission used the test currency export bridge.

1. Continue loaded at06:54:34.708.
2. Three fresh F5/F9 pairs completed; fourth total successful load was
   06:55:32.083. Each cycle rechecked the full147-byte live texture repair.
3. Native Journal created private Save1 at06:56:01. Its co-save66329bytes was
   temporarily moved out of that isolated profile, with byte-exact restoration
   in a finally block. Original source saves were never moved or changed.
4. Journal load of that Save1 refused with status6/Win32=2 before engine entry.
   No additional PreLoad/PostLoad occurred for this refusal. Native stream
   destruction followed. The recovery delegate correctly did not send Main
   Menu cancellation while Journal was open. The character position remained
   `(24862.389, -4551.821, -2999.7712)` and Journal remained available.
5. Co-save restored SHA-256
   `0AAFF85C8E800229A9566328D50E32F63305CF9E88A0F01A7AA9D8E6CA2DB0D2`.
   Loading the same Journal entry then completed at06:57:05.827: five successful
   loads total. Measured movement06:57:32–35 ended at
   `(24842.986, -4356.2266, -2997.6868)` with auto-move off, life-state0,
   no swimming and controls unblocked.
   All five immutable co-save snapshots consumed their complete buffers with
   fault0 and zero rejected API calls (64960/65384/66014/66329/66329bytes).
6. Normal native Quit to Desktop accepted06:57:46.890. Controller ended0 at
   06:57:49.127; no fresh crash artifacts. The Quit command's own response
   timed out because the game exited; terminal/log evidence establishes exit.

Startup's first read-only menu query was submitted before Main Menu existed
and timed out in the client. Its eventual completed read was checked before
the subsequent request. No load/accept input was blindly repeated.

Harness verified original/fixture/Default hashes unchanged and restored root
DLL0438215A/PDBA33BF070, currencyC8ED83D1 and logger0A38C678. No game/controller
remains. The successful refusal was an **early missing-co-save veto**, not an
induced native-false/deferred callback. No runtime claim is made for that latter
path, long gameplay, original Adventurer3 migration, or complete crash closure.

## Independent Fable review and unresolved gates

Actual Claude Fable5.1 CLI session4f945a49-193b-46b7-9fac-029690e34ca7 completed
19 read-only turns; no edits, permission denials or subagents. It independently
identified the native-false recovery defect. Its suggestion to gate recovery
on an inner-refusal flag was not adopted: even an inner refusal can return
through the outer callback-creation paths, so that flag is not terminal proof.

Review corrections: derived scalar159D3E0 calls common base159D290, **not**
nondeleting159D320. Healthy destructors normally observe pending0 because
inner `Finish` already released the context; expected matched1 is not a valid
healthy-test assertion. Unobserved destruction/ABA risk cannot be dismissed as
merely a stuck lease. Bridge release is source-visible noexcept/delete, and
WindowsReadLease closes its handle; it is not an unknown currency-DLL release
API. No speculative destructor release has been installed.

Remaining work: generation-aware terminal ownership/cancellation, verified
deferred resume policy, actual native failure controls, useful in-game refusal
reason, clean production integration/package, and broader save/load/gameplay
acceptance. Preserve fail-closed behavior and record user decisions rather than
restoring removed mods, cleaning saves or choosing a campaign migration.
