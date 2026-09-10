# Experimental in-game load admission — September 10

Issue [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) remains **open**.
The original Adventurer3 campaign is not repaired. No original save, removed
mod, vendor asset, or normal-profile load order was changed by this work.

## Implemented

The native parser now has an original C ABI, consumable by the older SKSE
build without exporting C++20 containers or exceptions across the boundary.
It validates the actual ESS snapshot, running full/light plugin names, live
currency fingerprint, and the leased co-save's checkpoint. It returns typed,
bounded reasons and explicit lease ownership. It does not certify all save
contents or gameplay. The component links statically; no extra plugin DLL.

Fable 5.1 drafted the ABI in a separate headless, read-only session. Parent
reviewed/applied it, enforced reserved fields and corrected a test that
mistook the phrase `size/ABI` for a leaked filesystem path. All 1,518 ABI
checks, the 626 parser checks, and 18 Windows lease checks pass locally.
The ABI tests also compile and call a real C consumer translation unit.

The SKSE fork has a development-only source-directory option and an opt-in
runtime adapter. It snapshots the engine's buffered ESS before decompression,
reads the actual plugin arrays, and queries the currency DLL's versioned V1
identity export. Before the inner load it preopens SKSE's actual co-save
reader, compares its file identity to the held lease, and consumes that same
handle through the existing serialization callbacks. It does not reopen the
co-save by pathname after the comparison.

Currency 0.2.3 was tested temporarily, not permanently installed. The isolated
launcher accepts an explicit source-bound candidate build only for dedicated
`Astra Load262 ...` profiles with local saves enabled. It checks the candidate
binary, source inputs, pinned dependency, runtime and unchanged configuration;
all other winning files still must match the normal release receipt. The
normal release receipt is unchanged. Ten candidate tests plus existing gate
and CLI tests pass (34 total).

## In-game evidence

All tests used muted private desktops, engine MenuPilot input, and copied or
new disposable saves. No Windows focus switching or interactive PowerShell
control was used.

| Test | Evidence | Result |
|---|---|---|
| Currency API dependency | Game 27368 / controller 9016; root candidate `0FAF77B0...` | Export returned `6270B86774F9F4F3`; copied Save7 loaded; new Save8 checkpoint accepted and normal reload succeeded; exit 0 at 05:49:24 UTC |
| Actual incompatible-save policy | Game 24112 / controller 23596; guard candidate `8949DD34...` | Status 5: missing `TrueHUD.esl` and `QuickLootIE.esp`; no filename rejection configured; engine target not entered; Main recovered, native navigation worked; exit 0 at 06:00:03 UTC |
| Accepted load, save/reload and F9 | Game 30616 / controller 33872; same guard candidate | Save7, new Save8, and Quicksave0 all admitted; all three actual co-save handles matched; three leases released; currency admission completed; exit 0 at 06:05:33 UTC |

After Save8 reload, a non-writing `Open/ReadWrite` handle to that exact test
co-save succeeded while the game was running. Its hash stayed
`F882945068A1A46FBF0D9031A1CEBDFBA36763344807275E90745440352BF019`.
This independently checks that the completed load did not leave the file
locked. No bytes were written through that handle.

Private evidence directories are under
`records-work/load-request-20260909/automatic-recovery-` with suffixes
`healthy-currency-api`, `guard-bad`, and `guard-healthy`. Their SKSE log hashes:

- API: `D60B8206E5900DF033DFD0328414ECD665C8BBF951EDD63C7DE3FA5C9D64A6A8`
- Refusal: `BEBDFF4B65F8432184B99C177DA4CFA537B3381BAAD87D569746439738FE0890`
- Accepted loads: `F8913D9AD944FA706135FB81E2EC305F7617192488132BD199D35259846551C2`

Full tested guard DLL hash:
`8949DD340E461B47F01999EE1DA0803F80DA19C910CCC264BE628F3F3A298892`.
All wrappers restored installed root `CC2F98A4...` and currency `C8ED83D1...`.
MenuPilot remained `1A1D5CEC...`. The original failing ESS still hashes to
`ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
Quit input batches time out as the game exits; controller exit 0 is independent
evidence, not a fabricated completed MenuPilot batch. These are bounded
load/save tests, not extended representative gameplay.

## Review findings and deployment blockers

Fable's separate actual-source review caught a retained lease after a native
pre-inner failure. Parent inspected the pinned caller: 625FFA–626024 destroys
the caller's remaining nonnull stream regardless of the result; 627FF2 clears
that pointer when transferring ownership to a callback. The adapter now
releases when the caller retains its terminal stream, but retains ownership
for deferred/unknown transfers. Basename continuity was also added. The raw
buffer cannot simply be compared again at the inner hook: the native outer
target legitimately decompresses it first.

These follow-up changes build and have 25 actual-source lifecycle checks.
Their DLL `0FA75F29E01FC2BCED9351DEAABD81071F98A2FA7D8FE85EA690713F0D251FFD`
has **not** had a subsequent in-game run. Do not attribute the preceding
runtime evidence to that changed build.

Still required before normal-profile installation:

1. Observe deferred callback cancellation/destruction so a retained lease
   cannot outlive an abandoned request; exclude stream-address reuse.
2. Resolve the late inner-hook refusal path. Returning false there skips
   native cleanup, as previously documented; this fallback is unverified.
3. Close the queued `CancelLoading` consumption race and provide a useful
   in-game refusal message. Current reasons are logged, not user-facing.
4. Mixed rejected/accepted loads while preserving an already-live character;
   unsupported routes, initialization failure, and post-review runtime tests.
5. Pin/package corresponding admission and zlib sources for reproducible
   distribution, with SKSE and dependency terms retained. No public binary
   release or all-MIT SKSE claim is made. The dev source path is not a release.

The existing SKSE target already uses static CRT; the generated projects
confirm `/MT` for SKSE, the bridge, and zlib. The bridge alone uses C++20;
SKSE was not globally migrated to that language standard.

## Original Papyrus crash — separate investigation

Fable reviewed the actual crash and parent checked the pinned executable.
The immediate fault is an array-reference release of pointer 2, reached from
`VMValue::Destroy` through `SetArray` while resetting a variable to its default
value after a failed script assignment. This identifies the failing operation,
not the writer of the invalid value.

The suggested missing-plugin index-remapping defect was not supported by
source: missing names map to `0xFF`, and restored registrations whose handles
fail resolution are skipped. The actual registration handle still needs
inspection; dynamic/base-game handles are not ruled out. A missing-script
stub/variable-layout hypothesis remains speculative. Absence of direct VM
API use in another DLL cannot rule out arbitrary memory corruption.

No save cleaning, removal of registrations, restored mods, or campaign
migration was performed. Next root-cause work must identify the relevant
saved registration and trace the first invalid variable state rather than
assuming missing scripts alone explain the native crash.
