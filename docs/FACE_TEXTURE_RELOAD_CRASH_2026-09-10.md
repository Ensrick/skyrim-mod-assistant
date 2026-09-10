# New reload crash: face-customization texture release

Tracker: #268, parent #262. Status: reproduced once, root cause under investigation; no fix
installed and no runtime acceptance claimed.

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
- [ ] Verify acquisition/reference ownership before changing release behavior.
- [ ] Implement any justified fix as separately distributable source/patch.
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
