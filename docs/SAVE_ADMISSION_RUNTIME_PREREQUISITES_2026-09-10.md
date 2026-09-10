# Runtime admission prerequisites — September 10, 2026 UTC

[#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) remains OPEN.
Source-only work; installed currency0.2.2, root SKSE and MenuPilot unchanged.
No game, save cleaning, campaign migration or profile mutation this batch.

## Currency identity ABI candidate0.2.3

`EnsrickCurrency_GetAdmissionFingerprintV1()` is a C-exported, no-argument,
noexcept function returning uint64_t. Zero means no successful initialization
has published identity. Nonzero is the resolved ledger fingerprint, NOT a
statement about current character admission, complete package correctness or
save health. It does not normalize inventory, admit a save or register hooks.

The getter reads a constant-initialized module atomic; it never constructs or
accesses the Bridge singleton. Release/acquire publication occurs only after
configuration parsing/resolution, optional QuickLoot initialization, event
sink registration and the success log. All failure paths before that point
leave the initial zero. Successful duplicate initialization preserves the
existing publication without re-running setup. Revert intentionally preserves
configuration identity while invalidating character-specific admission.

This addresses the observed early `_initialized.exchange(true)` guard: that
flag is set before initialization completes and is not a safe readiness API.
Existing initialization control flow and gameplay/currency rules are otherwise
unchanged. A consumer must check the expected export and reviewed module/
package identity, not silently accept missing ABI or a zero fingerprint.

Tests compile the ACTUAL Bridge::Initialize and export bodies against mocked
collaborators. They inject standard/nonstandard exceptions at five stages,
false configuration/QuickLoot results, retry success and duplicate calls, and
assert no early publication. Local205 checks plus100000 concurrent atomic
publications pass. These do not prove engine initialization or cross-DLL usage.

Full plugin build uses new private output C:/b/ccapi, retaining old C:/b/ccfix
and all original deployment archives. Build recipe now runs the identity test
before emitting its source/config-frozen receipt. Exact binary/export and
final build/CI evidence follows; no candidate is installed merely because
its getter compiles.

Full build finished successfully, with all4 CTest targets passing and the
separate configuration executable accepting18 families/rejecting27 invalid
contracts. Existing131072 quest-state combinations and nine lookup cases
pass too. Source/config remained frozen throughout the build; CommonLib
remains clean at90a64a4d65ce659a139137c968f42151bb6ecec9.

- Candidate DLL1034240 bytes, SHA256 `4DAB6D30FBB116B3E208985C344D2470D4A07C7EAD8A7EB73300F160293FD9AF`.
- Private receipt C:/b/ccapi/native-build-receipt.json, SHA256 `77AEF56E6B7F48586A605DF32D07BFABFF6F8119A72023CB505C143C73ED92B6`.
- Export table names the exact ABI at RVA5350. Read-only disassembly shows
  `mov rax,[rip+F0079]; nop; ret`, reading aligned zero-initialized storage
  atRVA F53D0. No call, allocation, Bridge construction or UI operation exists
  in that compiled getter. An initial assertion expected no intervening NOP;
  inspecting the instructions corrected that inspector assumption, not code.
- Installed0.2.2 DLL still SHA256 `C8ED83D13E0EEFC0353A20D4C7C40438CD2DF31596B15979994BBB501074007E`.

The candidate binary and build receipt remain private and uninstalled.
Public source/patches retain the existing combined CommonLib licensing rules;
do not label the linked DLL all-MIT. No engine invocation of this export has
occurred, so readiness across actual DataLoaded/reload is still unverified.

## Windows paired input lease

New WindowsSavePairLease opens the absolute ESS path and corresponding .skse
read-only with FILE_SHARE_READ, holds both handles, bounds each input to256MiB,
and checks file identity/size/write-time during the read. Constructor failure
releases any opened handle. No cache, save rewrite or content conversion.

Local18 synthetic Windows checks pass: existing read handles remain usable;
additional reads work; ordinary writer and delete handles fail with sharing
violation for both files; different/null/invalid handles do not match; existing
writer/missing co-save/relative path refuse; partial construction releases the
first file. Fixtures were created in a new temporary directory and only those
exact synthetic files were removed. No player files were involved.

The pinned SKSE common source IFileStream::Open uses GENERIC_READ and
FILE_SHARE_READ, compatible with this proposed lease mode. This source check
is not actual engine-stream compatibility proof. The adapter must establish
the real ESS handle/path and USVFS behavior. MatchesHandle can compare a
borrowed engine handle, but we do not yet know/use that handle in a hook.
Preexisting writable mappings and privileged mutations are outside ordinary
sharing protection. Pair correctness and lifetime still need engine tests.

## Outstanding

- Join the parser, identity ABI and lease into the actual early-load hook.
- Validate real loaded plugins and reviewed paired currency components.
- Provide useful in-game refusal reasons and race-safe cancellation.
- Test normal Continue/Journal/quickload paths, live-character preservation,
  admitted load/new save/reload and sustained gameplay.
- Continue the actual Adventurer3 MCM failure diagnosis; do not treat denied
  loading as recovered campaign data or silently choose a new campaign.
