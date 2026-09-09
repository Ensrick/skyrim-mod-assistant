# Currency admission repair during crash #256 verification

This is a prerequisite repair for a valid crash-test save, not evidence that
currency caused the old save's Papyrus crash. Default gameplay payloads remain
unchanged during candidate testing. No third-party adoption or Keep changes.

## Confirmed defects

1. `ResolveForm<T>` used pinned CommonLib's `LookupForm<T>`, which compares the
   exact `T::FORMTYPE`. `TESForm` and `TESBoundObject` have `FormType::None`, so
   even `Gold001` (MISC) failed resolution. Native 0.2.1 now resolves untyped and
   performs the checked, inheritance-aware `As<T>` cast. Concrete wrong types
   and nulls still fail closed.
2. Pinned `TESQuest::IsRunning()` evaluates `!IsStopping() && !promoteTask`.
   A fully stopped, non-promoting quest therefore reports running. The first
   candidate exposed the next false rejection: `FE081B63` / local `000B63` in
   `exchangeCurrency_enhanced.esp`. Native 0.2.2 uses `IsEnabled()` to decide
   whether to stop, then requires `IsStopped()` **and no promotion task** for
   admission. Stage-waiting, active, unknown and promoting quests remain denied.

Both defects were independently confirmed by read-only Fable 5 reviews against
the actual pinned CommonLib checkout, commit
`90a64a4d65ce659a139137c968f42151bb6ecec9`. No CommonLib/vendor files were edited.
No delay/retry loop was added: waiting cannot repair the erroneous predicate.
If an actual pending quest later prevents admission, record its state and
investigate; do not weaken the single-owner requirement.

## Evidence

- Build root `C:/b/ccfix`; VS2022 x64 static runtime, pinned clean CommonLib.
- Native policy/conservation tests PASS; strict 18-family configuration test
  and 27 negative contracts PASS; nine lookup checks PASS.
- Quest-state tests exhaust 131,072 flag/promotion combinations plus null.
  These mock tests prove our adapter logic, not engine memory layouts.
- Native 0.2.1 DLL SHA256:
  `360FBA9804EC3ED7751469A4FD399C96D20E5DE4815E0E756F62E412C1D291CB`.
  Actual runtime resolves all 18 families / 55 physical forms, then rejects the
  stopped quest. That fresh save is NOT admitted. Clean in-game desktop quit
  returned controller exit 0 at 07:38:18 UTC; no crash.
- Native 0.2.2 DLL SHA256:
  `C8ED83D13E0EEFC0353A20D4C7C40438CD2DF31596B15979994BBB501074007E`.
  Actual runtime initializes all 18/55 forms and logs
  `admission 1 complete: family=septim ledger=0` at 02:40:04 CDT.
- Fresh character completed through actual RaceMenu controls; Unbound saved
  `Save1_626DC7A8_0_416476656E7475726572_SkyrimUnboundRoom01_000001_20260909074059_1_1.ess`.
  Exact candidate DLL/config/two-plugin winner check and co-save checkpoint
  admission PASS. Unpaused runtime ping PASS. Clean in-game desktop quit
  returned controller exit 0 at 07:42:08 UTC.
- Cold reload of that exact admitted save succeeds at 02:43:17 CDT;
  `admission 3 complete: family=septim ledger=0`. Responsive unpaused pings at
  02:44:05, 02:44:38 and 02:45:57; no new crash log. Clean in-game desktop quit
  returns controller exit0 at 07:46:58 UTC. This does not test combat, nonzero
  wallet transactions or the original September7 input-pool fault.

Local evidence lives under `records-work/crash256-20260909/`:
`currency-candidate`, `currency021-fresh`, `currency022-candidate`,
`currency022-fresh`, `currency022-cold`. These include native source/build receipts, original
candidate ZIPs, and per-session currency/Papyrus/SKSE/LaunchProbe/MenuPilot logs.
Original user saves have not been cleaned, overwritten or deleted.

## Deployment boundary

The receipt-bound candidates are separate first-party test overlays, enabled
only in `Astra Currency Candidate Source` and the corresponding isolated test
profiles. They are NOT enabled in Default. Profile-local saves and muted audio
are mandatory. The launcher now optionally clones an explicitly named source
profile while still refusing to overwrite Default or the source profile.

The candidate gate receipt copies only the four exact winning-file hashes from
the 0.4.0 contract, replacing the DLL hash. It does not inherit the historical
release's runtime/installation claims. The base release receipt remains
historical; the gate now selects the explicit native0.2.2 hotfix receipt.
Denominations, distribution, config, ESPs, Papyrus and assets are
byte-identical to the existing release. Corresponding native source and the
CommonLib GPL-plus-exceptions notices accompany the candidate DLL.

## Final separate-patch deployment

`Ensrick - Currency Native Initialization Fix` installed into Default at
priority346, transaction `20260909T074740372Z-24829af68b5b`.
All38 installed files match the reviewed ZIP, two archive runs are identical,
the Default winning DLL is the same tested C8ED83D1 binary, and the exact
admitted save passes under Default currency winners. Test-only overlays remain
disabled in Default. The source bundle has its own accurate overlay notices;
no vendor models/textures/ESP/Papyrus files were packaged. Native0.2.2 itself
was built once; do not confuse repeat archive creation with two DLL rebuilds.

Receipt: `records/source-builds/currency-integration-0.4.0-native-0.2.2.json`.
Ledger includes the first-party patch; no Nexus Keep identity is necessary.
Twenty co-save tests and eleven save/plugin-table tests PASS. Ledger plugin
verification reports zero problems. MO2 configuration restored byte-exactly
(SHA256 DFE90980...D8E615); no remaining test game or controller process.

Still required: dependent freshness repair and wider gameplay tests. Targeted
checks still reject the pre-existing weapon proof (383 inputs vs376, changed
providers/order/binary inventory, weapon output not uniquely final) and cloak
proof (plugins, enabled mods, BSA metadata and profile fingerprint differ).
The native overlay also changes the cloak enabled-mod fingerprint; that check
must be refreshed honestly, not bypassed. Whole-pack launch clearance is NOT
granted. The old full currency regeneration pipeline still describes release
0.4.0; this additive native hotfix uses its own receipt-bound packaging recipe.
The old `TrueHUD`/`QuickLoot` save incompatibility and original September 7
input-pool crash remain distinct findings in `CRASH256_DIAGNOSIS_2026-09-09.md`.
