# Achievement-prompt load route — 2026-09-10

Master issue #262 remains open. This resolves one previously unknown deferred
route and adds a current-stack prerequisite check; it does not finish admission.

## Evidence changed the next action

In the pinned Skyrim 1.7.104 executable (MD5
`113faeb71fd8f62b26d0c8627299ab40`), outer load `627DE0` can transfer its
stream into a callback at `627FEE..627FF6`. The prompt string referenced through
`20AE8D0` is the warning about mods disabling achievements, with Yes/No buttons.
The condition calls `1BFA00`, which scans loaded full/light plugin arrays and
checks filename exemptions. It is not a missing-plugin tree, as earlier
provisional notes suggested. Header/local conditions also govern the branch.

The exact address library maps ID441528 to `1BFA00`.
[Engine Fixes' source at b289e3d](https://github.com/aers/EngineFixesSkyrim64/blob/b289e3deae71ce3915bb19c5faeeda8bf6c6a25c/src/patches/enable_achievements.h)
replaces that function with an immediate false return. The installed setting
enables this patch. Therefore, while those bytes remain in effect, this
particular deferred branch is not taken, regardless of the other two conditions.

This is more than source inference:

- The preserved original incident minidump contains `48 31 C0 C3`, followed by
  INT3 padding throughout the reviewed 0x6E-byte function span.
- Private game PID20564 showed the same bytes before and after Continue,
  journal reload and quickload, with stable repeated read-only observations.
- The engine/patch configuration was not changed for those observations.

Historical dump bytes alone are not current-live proof. Repeated live readings
are not proof that some future DLL cannot overwrite the code after observation.

## Controls and source change

Private profile `Astra Load262 Lifetime achievement-route` used the earlier
snapshot candidate8687E032, without the new prerequisite check. Continue,
new-save journal reload and F5/F9 consumed 64729/65384/65275 snapshot bytes,
with zero faults/API rejections. A bounded Auto-Move toggle changed position
from `(24862.389,-4551.8213,-2999.7717)` to
`(24842.912,-4355.6533,-2997.6812)` and stopped; the saved/reloaded position
remained stable. Responsive unpaused at05:27:21, more than81seconds after the
latest post-load. Normal quit05:27:25; no fresh crash or member rejection.

SKSE source `67272e21d9e1b80c21d583f6ab75521cff162e40` now checks the live
five-byte prefix at each experimental Begin, before creating an admission
context or entering native loading. Unknown/unreadable/different bytes refuse
at the already tested early outer boundary. Normal nonexperimental SKSE does
not acquire this restriction. It is a compatibility requirement for the user's
already-approved Engine Fixes configuration, not a new mod or a branch bypass.

Candidate DLL:
`04FE3A5C5F8A9D7A2AD6383FDED295B4C587197A6A7A4B575F82AB74F869B7BD`.
48 actual-source lifecycle/reader checks pass, including absent memory, native
unpatched bytes, every signature-byte mutation, and a reader exception. Full
Windows build passes. These unit checks do not replace engine controls.

Negative runtime control `achievement-negative`: an isolated temporary
overwrite configuration disabled just the achievements setting. Vendor config
was never edited. Actual live code reverted to native `48 83 EC 28 C6...`.
At05:29:43 the new guard refused with `supported=0`; native target was not
entered, no PreLoad/PostLoad/admission context was emitted, and the native
stream was destroyed. Main-menu state and Down/Up navigation recovered.
Normal quit05:30:08. The override was moved out of all live paths into private
evidence; the vendor setting and its hash stayed unchanged.

Positive rebuilt-candidate control **FAILED during quickload**. Continue
completed05:32:22.307 and journal Save5 reload05:32:58.106. Both checked the
supported prefix and consumed the snapshot without errors. F5 created a new
quicksave05:32:59.757; F9 began05:33:01 but crashed05:33:02 before PostLoad.
No snapshot-unbind/currency-completion record exists for that third load.
The third load must not be counted as passed, despite successful input delivery
and two earlier successful routes. A premature progress statement was corrected
immediately after inspecting the fresh crash artifact.

New fault: SkyrimSE+100F207, invalid virtual call in a face-customization
texture-update stack. Community Shaders' Upscaling wrapper appears on the
stack; this does not by itself establish it as the root cause. The signature
differs from the original Papyrus MCM +09C00FC fault. No minidump was enabled
for this run; the detailed text log and exact private save pair are preserved.
Investigation/control comparison is required before blaming the new guard,
the snapshot implementation, Community Shaders, or an unrelated component.

Private crash log SHA-256:
`5CF49CE5A0A1B1DDE9A3F8AF1F2434C3177137D0A3C5DEC28DC1808C5A24FED4`.
Failing quicksave stem:
`Quicksave0_2AF573B9_0_416476656E7475726572_WhiterunWorld_000004_20260910103259_1_1`.
ESS: `54692023CB48CAA906C3C55ACF38A597304E6F86BCB157657003AB04D3E96301`.
Co-save: `752DD9E39C188D7CFB500D0C2B0BE6D76A5F93093811D21690E19BE0A525B364`.

Controller exited0 after the crash; this again demonstrates why its exit code
is not gameplay certification. Harness restored clean SKSE4E3F618B, currency
C8ED83D1 and logger0A38C678, and verified unchanged original/source saves and
Default list hashes. No game/controller remains. The experimental guard is
source-published, not installed as the normal release. Both SKSE CI runs
34466422277/34466422275 succeeded, but cannot override this failed runtime test.

## Limits and review corrections

Actual Fable5.1 participated through the installed CLI. Its previous assertion
that a deferred resume bypasses625FF5 was withdrawn: payload-layout similarity
is not proof of the task dispatcher route. Its suggestion to label inner false
unreachable on the patched stack was rejected. Native inner loading can still
fail for reasons not exhaustively covered by admission.

The later error-callback transfers at628414 and628E24 are distinct and remain
unresolved. This change does not implement cancellation cleanup, promise all
native failure paths are safe, or close the in-game refusal-message gap. No
save cleaning, missing-mod restoration, or campaign migration is performed.

Private tools/evidence live under records-work; no original save, licensed
payload or incident dump is published with this report.
