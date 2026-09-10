# New reload crash: face-customization texture release

Tracker: #268, parent #262. Status: opt-in repair has passed two isolated
tests totalling19 successful loads; broader acceptance remains open.
Nothing newly deployed to the normal playing configuration.

## Reproduction evidence

Private `Astra Load262 Lifetime achievement-positive`, Skyrim1.7.104, snapshot/
admission candidate04FE3A5, normal approved Engine Fixes configuration. Continue
and new Save5 journal reload succeeded. F5 generated a quicksave, then F9
crashed at05:33:02 before PostLoad or co-save consumption completed.

Fault: SkyrimSE+100F207, a virtual call through an invalid pointer. The native
face-customization updater+043CB59 and Community Shaders Upscaling thunk are on
the stack. This differs from the original Papyrus member-write crash+09C00FC.
Presence of Community Shaders in the stack is not attribution of root cause.

Exact private quicksave ESS/co-save and crash-log hashes are in
[the admission control report](ACHIEVEMENT_LOAD_GATE_2026-09-10.md). Both files
remain in the private profile; originals, source fixture, vendor content and
Default lists were verified unchanged. Normal SKSE/currency/logger restored;
all game/controller processes terminated. Controller exit0 did not mean a pass.

## Concrete native lead

Read-only inspection of the pinned executable found renderer-texture cleanup
100F190 decrementing a wrapper reference count. On the final reference it
invokes virtual slot2 on fields+10,+0,+8, then repeats+0,+8,+10 without clearing
those fields. The crash is at the second call for+10. CommonLib's matching
28-byte layout identifies these as resource, UAV and shader-resource-view
pointers. Microsoft documents that [COM Release frees an object at reference
count zero](https://learn.microsoft.com/en-us/windows/win32/api/unknwn/nf-unknwn-iunknown-release).

The reviewed creation path100DE60 stores the created texture directly in+0,
initializes wrapper count1, and passes+10 directly as the shader-resource-view
creation output. No persistent second view-reference acquisition is visible
on this path. 100EF50's temporary GetResource reference is released separately.
This is a specific duplicate-release hypothesis, stronger than inferring an
unspecified race from the stack. It still needs ownership/ABI validation and a
controlled experiment before a patch is justified.

## Verification and repair gates

- [x] Preserve the exact failed save pair, logs and candidate identity.
- [x] Restore the normal stack and confirm no live test override remains.
- [x] Distinguish this signature from the original MCM crash.
- [x] Reproduce the ownership failure with bounded exact-code/COM modelling.
- [ ] Compare the same input under an admission-disabled control; a failure
  there would show admission is not necessary, not prove it never affects timing.
- [x] Verify reference ownership on face-texture and DDS creation paths before
  changing release behavior; exhaustive other-path audit remains a limitation.
- [x] Implement opt-in, separately distributable source repair with exact-byte
  rejection and checked startup write; normal configuration remains unchanged.
- [ ] Repeat cold and in-session load/save/reload and sustained gameplay with
  fresh crash-log checks. Do not count input delivery or controller exit as success.

Actual Fable5.1 is reviewing source/ownership. Parent is validating claims
against the executable; no speculative exception filter, null guard or visual
feature removal is being treated as a solution.

## Offline exact-code experiment

Unicorn2.1.4, installed only in a private diagnostic dependency directory,
executed the actual pinned cleanup bytes against synthetic COM objects and
bounded mapped memory. Sixteen scenarios cover wrapper counts1/2, an optional
UAV, and zero/one external texture reference. The unmodified final-release
path faults on duplicate virtual dispatch; with one external texture reference
and no UAV it faults at the exact observed100F207 site. A hypothetical jump
over the second triplet avoids the invalid calls, frees the wrapper once and
preserves the modelled external reference. Nonfinal wrapper decrements remain
unchanged. No real game code or process memory was patched by this experiment.

This establishes a failing exact-instruction sequence under the modelled
ownership, not all live D3D ownership or a finished game fix. Other creation
paths and any legitimate extra references owned by the wrapper still require
audit. References owned by unrelated holders would not authorize this wrapper
to release them; raw COM reference counts alone cannot establish ownership.

## Opt-in implementation and first live test

SKSE fork commit `aef6fcb`, candidate DLL SHA256
`D2B87965C54C6268F309CB546F0820344DDEF46C22EBBA5FE48CAFB54B4B4424`.
`SKSE_AUTOMATION_TEXTURE_RELEASE_FIX=1` replaces exactly three bytes at100F1DE
with EB2B90, jumping to100F20B. It requires the entire147-byte original function
to match. The branch retains the first release triplet, wrapper reference
decrement, free and native unwind. It does not swallow faults or adjust CS
visual settings. Source/tests are published in Ensrick/skse64;156 signature/
branch checks and16 exact-code emulation cases pass locally.

The model was subsequently expanded to32 cases, including a wrapper without
its own resource field (DDS-style SRV ownership). All32 pass the expected
original-fault/patched-success and nonfinal-reference assertions. The patch
bytes and full original signature are read from the actual source header and
compared to the pinned executable, avoiding an independently invented patch
in the emulator. Both source CI runs34468813475 and34468813418 passed.

The additional DDS path100E080 stores its returned SRV directly at wrapper+10
(100E203), while +0/+8 remain null; no second AddRef appears on that path.
Actual Fable5.1 performed a seven-turn read-only implementation review. Parent
corrected its claim about initialization order: InstallPlugins/LoadComplete
occur **before** this patch's Install in SKSE64_Initialize, not afterward.
Independent bounded read-only memory checks also verified all147 patched bytes
after initialization and each tested F9, not merely the startup log.

First positive test, `Astra Load262 Lifetime texture-fixed-exact`:

- Private muted desktop, PID32524/controller35956; normal explicit admission
  enabled, and copied **exact failed** quicksave/co-save as starting input.
- Continue PostLoad success05:55:32.669; new Save1 journal reload05:56:27.739.
- Five F5/F9 pairs: each has a fresh kSaveGame and successful kPostLoadGame.
  Last success05:57:33.307. All seven snapshot reads unbound with fault0 and
  rejected API calls0. Each F9 was followed by full live patch readback.
- After more than a minute of unpaused operation, bounded native movement and
  jump input05:58:31–34; player position changed from(24862.389,-4551.821,
  -2999.7712) to(24842.883,-4355.4175,-2997.6792). Auto-move returned0,
  candidate life state0, swimmingfalse. This is not travel/combat coverage.
- Normal Quit05:58:53; harness finished05:58:55.307. No new private crash log.
  Root/currency/logger and original/fixture/Default hashes restored unchanged.
- Process private bytes grew from11,544,576,000 after cycle1 to11,616,550,912
  after cycle5. Five cycles do not establish a GPU-leak trend or absence.

This is a passed scoped regression test, **not** a100% stability claim or issue
closure. Fix-disabled/admission-disabled control is next; intermittent failure
rates and a fix-alone control still need comparison. Private receipts/logs are
under records-work/lifetime262-20260910/texture-fixed-exact; no saves or vendor
assets are published.

### Extended unpatched control

`Astra Load262 Lifetime texture-off-admission-off`, PID35536/controller11440,
used the same candidate with **both** opt-ins off and the normal currency DLL.
The exact original147-byte cleanup function was independently read and
verified before Continue and after every F9. No admission/snapshot runtime
events appeared. Starting from a copy of the same failed quicksave, Continue,
ten F5/F9 pairs, and an intervening new Save1 journal reload all succeeded:
12 PostLoad successes total, last06:04:05.649.
Normal Quit06:04:44.849; harness restored root/currency/logger and preserved
original/fixture/Default hashes at06:04:47.102. No new private crash log.

The original fault did **not** reproduce in this bounded control. This does
not exonerate native duplicate-release code or establish admission as cause.
It also means the positive run cannot demonstrate a measured live reduction
in crash rate. Process private bytes rose from11,608,576,000 after its first
F9 to12,042,919,936 after its tenth; this is not a comparable GPU leak metric
or evidence that either configuration has a leak.

### Fix-alone control

`Astra Load262 Lifetime texture-fixed-admission-off`, PID13212/controller35516,
same failed-input copy, normal currency, texture fix on and admission off:
Continue, ten F5/F9 pairs and an intervening new Save1 journal reload all
succeeded. Last of12 successful PostLoad events06:10:06.560. Full147-byte
patched signature matched before loading and after each F9; no admission/
snapshot events. Normal Quit06:10:44.823, harness finished06:10:47.044, no new
private crash log, original/fixture/Default preserved and normal binaries/
logger restored. Private bytes11,501,428,736 after first F9 and11,671,461,888
after tenth; no GPU-leak conclusion from those numbers.

All three new runs total31 successful loads,19 with the fix. This is not
31 independent attempts to reproduce the original crash: repeated loads in
the same three processes are correlated. The original failing admission-on
run began from healthy Save4 and used the previous build; it is historical
evidence, not a perfectly matched fourth factorial-control cell.

### Release status and next bounded work

A clean build without experimental admission code also compiled successfully:
SHA256 `A776C5C5832A957571C0DADF7BEC9F9894A6F9A0048291927964C6A0C6C7F3FB`,
same source aef6fcb, opt-in still required. **Not installed or runtime-tested.**
Normal root remains4E3F618B. Both new Fable reviews have finished; no assistant
game/controller remains and the live mutation claim is released.

The independent release-readiness review supports an opt-in repair but holds
normal enabling for broader ownership and gameplay coverage. Its proposed
AddRef/Release count probe is **not accepted** as an ownership test: reference
counts include unrelated holders, and a count >=2 does not prove this wrapper
owns two references. No mutable COM probing was performed. The useful next
steps are audited creation/ownership provenance and a non-mutating observation
of cleanup execution, followed by clean-build and NPC-dense runtime coverage.
Source correction, live crash attribution, and whole-game acceptance remain
separate claims. No extra mods, visual-policy choices, save cleaning or
campaign migration were authorized or performed.
