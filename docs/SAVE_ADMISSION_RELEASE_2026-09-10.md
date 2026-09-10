# Save admission release — 10 September 2026

## Status and scope

The always-on guarded SKSE build and its paired currency readiness provider
are installed locally. The exact release candidate passed both original-copy
refusal and healthy save/load controls. The installed-state canary also passed;
do not treat this report as campaign recovery or overall crash closure.
Issues #262, #267 and #268 remain open.

The incompatible Adventurer3 campaign is preserved, not cleaned or migrated.
It references missing TrueHUD.esl and QuickLootIE.esp and lacks the current
currency checkpoint. A controlled refusal prevents loading incompatible data;
it does **not** make that campaign playable. Restoring removed mods, migrating
the campaign, or starting a replacement campaign requires the user's decision.

## Installed pair

- SKSE source: Ensrick/skse64 `16794a70e5ff02f448201e483e39e042fce393b9`.
  Explicit CMake `ENSRICK_SAVE_ADMISSION_RELEASE=ON`; canonical admission source
  pinned at `b2e0387db460fec3680827252e39060121a2acea` in hosted CI.
- Root DLL SHA-256 `F7435705A0959B100B2D25DA9EDA558F9A1D54399F4FC4666DCF9BA181107ACC`;
  PDB `7F99BBEB53F4BDE5DD78C522B039C1376CD25F797EF69FA43A35A509918BFE42`.
- Existing Currency Native Initialization Fix overlay updated to 0.2.3,
  DLL `4DAB6D30FBB116B3E208985C344D2470D4A07C7EAD8A7EB73300F160293FD9AF`.
  Ledger fingerprint `6270B86774F9F4F3`, JSON, ESPs, Papyrus and values unchanged.
- Controller transaction `20260910T134952519Z-3716ce45be94`, existing priority
  346 and enabled state retained. No Nexus adoption or new Keep entry needed.

Request/inner/deferred-lifetime admission is enabled without environment flags.
If the outer hook cannot install, inner enforcement is **not** disabled.
Startup records the missing hook and refuses unadmitted inner loads. Named
outer/inner fault injectors are compiled out of this release. Diagnostic
observers remain opt-in OFF. The member-bounds and texture ownership repairs
remain enabled. Legacy `experimental=1` log labels survive in some messages;
they are not an activation control and must not be interpreted as one.

The currency readiness export is atomic and read-only. It reports no identity
before successful initialization. It does not construct the bridge from an
admission callback. Package builders now derive their version from the
receipt-bound CMake source, not hardcoded 0.2.2 names.

## Build and automated evidence

- Clean release CMake build passed; 4 lifecycle and 6 probe CTest tests passed.
- Actual release policy tests fail if environment activation is consulted;
  the release inner-hook variant verifies that the injector is ignored while
  an empty admission still refuses loading.
- SKSE CI runs 34484051133, 34484051106, 34484051054 and 34484050952 passed.
  Canonical packaging commit d9150f7 CI 34484423486 passed.
- Currency native build: 205 initialization/export checks, 100000 concurrent
  publications, 9 form checks, 131072 quest-state cases, denomination tests,
  and 18-family/27-invalid configuration contracts passed.
- Gate/packaging Python tests: 22 passed after invoking from the required
  `audit` import root. The initial root-level invocation was an import failure,
  not a passing test run.
- Two release ZIPs were byte-identical, SHA-256
  `193D13D07D8FD47C4E6BC0019A942F1828CC6623E4BA7E4625E75AC0A297AE94`.
  All 41 installed payload files match the reviewed archive receipt.
  This is not a claim of two independent native builds. An unnecessary Python
  bytecode-cache entry is present in the source bundle; exclude caches in a
  future packaging cleanup. It is not an additional game runtime component.

## Actual release-candidate tests (local CDT)

All activation, rejection, texture-override and observer environment switches
were removed. Tests used muted private desktops, isolated copied saves and a
no-popup/no-cleanup private crash logger. No desktop input was injected.

| Run | Observed result |
| --- | --- |
| release-original, 08:40:20–08:42:13 | Exact original copy refused for missing plugins before PreLoad/native entry. Native MessageBox explained the refusal. OK acknowledged; Down/Up main-menu navigation worked. Native Quit 08:42:11.733, controller exit 0. |
| release-playing, 08:42:32–08:47:08 | Four successful loads: Continue 08:43:32.662, generated Save5 Journal reload 08:45:10.492, F9 08:45:16.740 and 08:45:31.542. All immutable readers fault=0/rejected API calls=0; currency admissions 3/6/9/12 completed. |

For the healthy run, temporarily withholding **only the generated private
Save5 co-save** caused the expected refusal at 08:44:08, not another PreLoad.
The in-game explanation was visible and acknowledged. The exact co-save was
restored in `finally`, SHA-256
`22E6F668A879D97F06F9BE58C4D2F94E7F28745484461A750ECC9681888CB5F6`.
The same save then loaded successfully. Guarded read-only position samples
were unchanged across refusal; paired Auto-Move input subsequently changed
position and returned to idle. This is narrow movement evidence, not combat
or full Actor ABI certification. Final unpaused ping was 90.573 seconds after
the final successful PostLoad. Native Quit 08:47:06.618; controller exit 0.
No new logs appeared in the protected crash directory.

Earlier actual native deferred-callback cancellation/resume and injected
pre-target inner-false tests are documented separately in
[Deferred load lifetime](DEFERRED_LOAD_LIFETIME_2026-09-10.md). Injecting a
pre-target refusal is not equivalent to a genuine partially executed native
load failure. Do not extend its conclusions to that untested branch.

## Deployment and preservation

### Installed-state canary: completed

The normal installed pair was tested without swapping binaries, a candidate
gate exception, autoload or activation/observer flags. Controller 22124 ran
09:00:59.490–09:06:07.095 CDT; game PID 36340. Private profile:
`Astra Load262 Installed Release 20260910`, refreshed from Default.

- Continue succeeded at 09:02:09.713; two F5/F9 cycles succeeded at
  09:02:28.190 and 09:02:42.917. Both cycles verified the complete live 147-byte
  texture-repair signature on repeated read.
- Paired Auto-Move at 09:04:05 changed the guarded candidate position from
  `(24862.389, -4551.821, -2999.7717)` to
  `(24842.932, -4355.782, -2997.6826)`, returning to idle.
- A new private Save5 was created through the native Journal. Its checkpoint
  passed the normal currency gate; the observed fileNum=5 was selected and
  reloaded at 09:04:53.612. Subsequent position remained at the saved moved
  location. Four snapshots consumed 64729/65384/65384/66329 bytes exactly,
  with fault=0 and rejected API calls=0. Admissions 3/6/9/12 completed, ledger11.
- The last unpaused ping at 09:06:00.208 was **66.596 seconds** after the final
  successful load. This is a bounded smoke, not sustained travel/combat.
- Native Quit Accept was delivered at 09:06:04.697; controller exited 0 at
  09:06:07.095. The Quit command's batch acknowledgement timed out because
  the game exited; this was not counted as a gameplay test failure or ignored
  without checking the controller. No game or controller remained.
- All installed root/41 overlay payload files, original save/co-save, source
  fixture and Default profile hashes remained unchanged. Normal logger was
  restored byte-exact. Protected crash directory contained zero files.

Private evidence: `records-work/admission-release-20260910/installed-canary/`.

Root DLL/PDB were recoverably backed up; the controller retained the previous
currency overlay in transaction trash. The deployment script's final raw
modlist hash assertion caught a controller-only first-line comment change
(`Mod Organizer` to `MO2Headless`). A read-only diff confirmed no order or
enablement changes. The controller header version was archived and the exact
original modlist restored from its transaction backup.

Default modlist SHA-256 remains
`A19834B77608342C63123E5ABA2BBCA9A9A5FC200BBD69AB06EE1E49F8EA71BE`.
Ledger verification: 345 rows, 392 discovered plugins, 0 problems. Preflight:
0 blockers; reports the authorized root DLL update and existing warnings
about overlay verification, five missing ledger rows, our live claim, resolver
ordering and old-save currency restrictions. None was suppressed. Weapon and
cloak freshness gates passed without regenerating their outputs. Existing
conflict reports and unrelated dirty files were not changed.

Private evidence lives under `records-work/admission-release-20260910` and
`records-work/lifetime262-20260910/release-{original,playing}`. Originals and
the 17.7 GB causal dump are retained. No conversation history was removed.

## Licensing and remaining work

### Independent log review and limits

Actual Claude Fable 5.1 CLI session
`be3a35e2-7fd8-4749-8703-8494f2d63b29` completed a read-only four-log review
(16 turns, no subagents or edits). It confirmed the expected refusal and all
four successful snapshot/currency sequences. The parent rejected its claims
that USSEP no longer ships the missing scripts, that the alias issues are
necessarily baked into the save, and that particular quests are demonstrably
degraded: those conclusions require package/record inspection and were not
established by the cited logs.

Specifically, `release-playing/Papyrus.0.log` records missing
`ussepretroactive439script` and Retro439 linkage failures at 08:43:07, before
the 08:43:25 save-load sequence. HLIOMQ1/Remi/Redcap and AnvilDen alias binding
errors also recur. Track these under existing #157, not a duplicate issue.
Do not infer provider ownership from a script prefix alone; map active full
plugin indexes and winning PEX/BSA providers before proposing a repair.
No causal connection to a native crash was demonstrated by this review.

Earlier Fable release-policy review session
`1bb9bf01-a6ad-4ebc-b9b9-42c97d55e1fb` completed read-only (19 turns);
implementation and verification were performed by the parent. Both CLI jobs
are terminal. These were actual requested Fable runs, not Codex substitutes
or input into the user's PowerShell window.

Currency's combined DLL is GPL-3.0-or-later with CommonLib exceptions and
bundled corresponding source; original adapter code being MIT does not make
the combined DLL MIT. SKSE retains upstream terms. No public binary release
or vendor asset redistribution was performed.

Continue representative travel/combat and failure-path diagnostics under #267. Keep the
user's campaign decision explicit; do not close #262 or the overall goal on
the strength of a controlled refusal and healthy-fixture smoke alone.
