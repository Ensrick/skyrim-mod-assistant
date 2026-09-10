# USSEP 4.3.9 missing-script investigation

Status: official corrected package installed; dependent generated patches
refreshed. Fresh-character update completion is observed, but the pre-update
copied save retains an invalid updater object. This advances #157 and the current setup's
script health; it does not establish a cause or closure for native crash #262.

## Evidence

The September 10 release-playing log reports the missing
`ussepretroactive439script`, Retro439 linkage and type failures at 08:43:07,
before its 08:43:25 load sequence. The installed USSEP/readme and ledger identify
4.3.9, Nexus mod266/file792961. Installed main BSA and ESP are byte-identical
to the retained downloaded archive; this is not evidence of a local edit.

| Input | SHA-256 |
| --- | --- |
| Original 4.3.9 archive | `63f68b23343b81ba6eed3f987c87e27d5d8f3f2ad1d7a47c32f436e4000a3cfd` |
| Installed/main archive BSA | `716ec370a439782ba5d27742f64f1d65694a4dc54cbdf6d5075ec1ad814951f0` |
| Installed/archive ESP | `7d7cea13683eff2c1c766f5c266441d98fd6e99081815c3f098cf0e54752bd04` |
| Downloaded 4.3.9c archive | `008f594d90650a27d36dae93f205681cfa4114a674ff55e26b1128666fcb4fb4` |

The 4.3.9 BSA has 6608 entries. Its 438 and version-tracking scripts explicitly
reference the missing 439 class. A targeted scan of 181 highest-priority
top-level BSA providers from enabled folders/Data, plus matching loose files,
found no supplier of the 439 PEX. There were zero archive-index errors. This
scan identifies potential archive providers; it does not by itself certify
the engine's archive activation/order.

The [official changelog](https://www.afkmods.com/index.php?/topic/10216-relz-unofficial-skyrim-special-edition-patch/)
identifies the missing 4.3.9 update script as bug37035, corrected in 4.3.9c on
September5. Nexus's authenticated API confirmed main file800977, version4.3.9c,
uploaded2026-09-05T22:22:09Z; the [current file page](https://www.nexusmods.com/skyrimspecialedition/mods/266?tab=files)
agrees. No secret or signed download URL was recorded in Git.

The downloaded correction contains the previously absent PEX (1279 bytes,
SHA256 `cda5d9d564b786d3df17db7ab19b5507c0df6c1e5576b778f16a83815f6950b6`)
and its PSC (856 bytes,
`fbf76bd7e90d4819d01dda8f79f74dd1e559db8fc4014e78e6bcb76babef9922`).
Those are the only script/source byte differences between the main BSAs.
Inspection of the supplied source shows the normal chargen-stage guard,
conditional Pinewatch correction, version tracking and quest stop. This is
the upstream implementation, not an invented empty class to suppress errors.

## Update scope and compatibility review

The update is **not a script-only archive**. Exact uncompressed record-payload,
semantic-flag and form-version comparison found:

- 59383 old versus59381 new records, including TES4.
- No newly added records.
- Two removed override records: `10C5FE:Skyrim.esm` / SteelGlovesArgAA and
  `10C5FF:Skyrim.esm` / SteelGlovesKhaAA. These are removed USSEP overrides,
  not deletion of Skyrim's originating records.
- Changed TES4 header and `105900:unofficial skyrim special edition patch.esp`
  / Help_USSEP message. Editor-control bytes/group metadata were excluded from
  this comparison; no broader semantic-equivalence claim is made.

Current record inventories for all304 starred profile plugins found only USSEP
writing those three FormKeys, with zero inventory failures. This is the managed
starred set, not all384 loaded base/Creation/light plugins. Both originating
ArmorAddons exist in Skyrim.esm, with the expected Argonian/Khajiit races,
Hands/Forearms slots and first/third-person steel gauntlet paths. The old September7 broad
conflict report is stale and was not used as proof of current winners.

Main-BSA differences also include seven mesh paths (four changed, three
removed), consistent with the intervening official regression-fix changelog,
and333 changed FUZ containers. Do not describe the update as byte-identical
audio or only the missing script. An initial voice check wrongly expected
RIFF/WAVE; these files use RIFF/XWMA. The diagnostic now accepts that actual
container type. No decoded-audio/voice-quality equivalence has been established.
The texture BSA is byte-identical, SHA256
`d45e6e26fcf83c0a5bb1bacd7dc2d0c1b071853ae6fc0538f62b1d8b84e8ba74`.
Effective loose mesh winners remain SMIM (Solitude light post), Rally's Market
Stalls Animated (market stall), Unofficial Material Fix (patio corner), and
Assorted Mesh Fixes (Gray Quarter door and mounted wolf). Both removed sigil
stone paths remain supplied by Skyrim - Meshes0.bsa. No replacement priority
was changed and no new overhaul choice was made.

## Required implementation and verification

1. Update the existing approved USSEP mod to the exact official4.3.9c package,
   under a live instance claim and with recoverable old package/profile state.
   Preserve plugin order; do not substitute a local empty script or clean saves.
2. Recheck effective mesh and ArmorAddon winners. Raise an actual discretionary
   conflict decision if found; do not silently select another overhaul.
3. Regenerate/reverify affected weapon-balance and cloak reservation metadata
   through their normal source-driven workflows. Their fingerprints include
   plugins/archives; do not waive freshness by editing stored input hashes.
4. Verify installation ledger and actual Keep coverage for the already-approved
   Nexus mod266, not merely a queued browser update. Retain private/vendor
   payloads outside Git and document the official update rather than publishing
   modified USSEP assets as our own work.
5. Use a private copied current fixture to test startup, normal load, expected
   439 completion/linkage behavior, save/reload and normal exit. Preserve all
   original campaign inputs. Absence of one warning is insufficient; inspect
   the tracking script's positive progress and fresh failure diagnostics.
6. Keep other #157 bindings and broad #262/#267 acceptance open. This correction
   does not grant approval for original-campaign migration or removed mods.

Private staging and read-only comparison script:
`records-work/ussep439c-20260910/`. The comparison's OLD path describes the
pre-install live folder; rerunning after installation requires pointing it at
the preserved old package, not treating the updated live folder as 4.3.9.
Downloaded archives remain in managed downloads; prior installed folders are
recoverable through the controller transaction journal.

## September 10 installation and static verification

- Official USSEP transaction `20260910T142918438Z-8d2da5624533`, enabled at
  unchanged priority15. Main BSA SHA256
  `4c589b14a6843c341a572a5d25ea47296f046ae25885778c571caef05e6275de`;
  ESP `c496e65927a75a6209bf0db58ffe62047f5fbf03063a399c6e2ff1ced98548a5`.
- Default modlist/plugins/loadorder remained byte-exact after each replacement.
  Only the controller's known comment-header normalization was restored, after
  exact body comparison. No plugin activation/order or user save changes.
- Weapon source-driven repeat build and semantic only-Speed comparison passed;
  all4225 final target/preserve rows passed. The 3504-record ESP and27 localized
  sidecars remain byte-identical; new input metadata was generated, not waived.
  Replacement transaction `20260910T143824618Z-7061c29e61f0`, priority246.
- Cloak reservation regenerated after that replacement: 240 unchanged rules,
  576 paths,569 present meshes,7 existing absence sentinels, zero parse errors
  or reserved-slot hits,40 winning runtime configurations. No new physics or
  distribution behavior. Transaction `20260910T143931305Z-8a0a9933875b`, priority295.
- Live Keep coverage:235 installed Nexus IDs and235 Keeps, no missing/extra/
  skipped-installed IDs. First-party artifacts have no invented Nexus IDs.
- Preflight: zero blockers; five existing warnings remain (Steam overlay cannot
  be verified on disk, five unledgered enabled folders under #102, this work
  claim, CRF/resolver CELL006439 difference, old-save currency restriction).
  This is not comprehensive gameplay certification or a waiver of those issues.

Runtime acceptance is recorded below after both private sessions ended and
preservation checks finished. #157 remains open for other
bindings; #262/#267 and the original-campaign decision remain open.

## Runtime contrast: existing copy versus genuine New Game

The controlled copied-save run used the normal installed F7435705 SKSE and
4DAB6D30 currency pair, not test activation flags. Controller25060/game31944
ran09:41:14–09:45:02 CDT and exited0 after normal Journal Quit. Continue,
Journal Save5 and Journal reload succeeded, but the actual Papyrus log twice
reported `ussepretroactive438script.Process()` on an invalid object, at09:42:33
and09:44:07. There was no positive439 completion. Therefore the update is
**not proven to repair already-retained broken updater state**. Do not clean
that save, reset quests or claim it repaired merely because it loads.

For comparison, private profile `Astra USSEP439c Fresh 20260910` started with
an empty local-saves directory and genuine New Game. At09:46:43, Papyrus logged
both `USSEP 4.3.8 Retroactive Updates Complete` and
`USSEP 4.3.9 Retroactive Updates Complete`. Vendor Unbound's MCM selected
City→Whiterun (`$SU_City7`) and Begin Your Adventure. The MCM list dialog keeps
its chosen active entry until Exit/Cancel closes it; Accept alone did not
close it. One premature page read was undefined; state was reobserved before
continuing, not treated as a mod failure or forced with console commands.

Fresh Save4 and Save5 loaded successfully at09:52:10.919 and09:53:34.179.
The bounded co-save readers consumed exactly62204/64527 bytes with fault0 and
rejected_api_calls0; currency admissions4/7 completed with ledger623. The
438/439 binding/call failure did not recur in that fresh session. Native
Auto-Move start/stop moved the character from approximately
(24876.596,-4695.499,-3003.046) to(24827.049,-4225.86,-2996.447), within the
same Whiterun cell1A276/world1A26F. An independent read-only probe observed
auto-move0 and zero input vectors afterward. This is bounded movement evidence,
not combat, broad travel or an atomic physics snapshot.

Fresh Save5 ESS SHA256
`0032479db0599e3a7ed53851d2c6c81c7f72d5e957d6158fa19d177fdbe9aabc`;
co-save `316b4f160010a9da7597997a761f81da5241478d0209151ee3e63d22722106eb`.
It is a disposable test fixture, **not a silently chosen replacement campaign**.
Raw logs remain private in `records-work/ussep439c-20260910/runtime-canary/`
and `runtime-fresh/`. Original Adventurer3 and prior fixture inputs are retained.

The fresh controller24936/game11120 ran09:45:16–09:54:46.851 CDT and exited0
after normal Quit. The final unpaused ping at09:54:40.076 is65.897 seconds
after the final PostLoad. Both sessions preserved the pinned original saves,
prior fixture, Default lists/INIs, root DLL/PDB and all41 currency-overlay
files. CrashLogger was restored byte-exact; protected crash directory remains
empty. No owned game/controller remains. These bounded passes do not establish
an overall crash rate or resolve the original-campaign admission decision.

Fable5.1 CLI session93417b2f-27e4-4e5d-b919-3080858be151 separately implemented
a read-only observer candidate in private staging. Root's first run passed32
mocked tests; after review corrections to ctypes signatures, engine-path
validation and intervals, the actual second suite passed35 tests (not the
estimated36 in the handoff). Live samples matched the existing independent
probe's coordinates/cell/world/raw state and detected the measured movement.
It remains a candidate, not a new installed DLL or a combat acceptance oracle.

## Other provider findings

The targeted archive scan maps `HLIOMQ1Script` to Remiel's `HLIORemi.bsa` and
`AnvilDencheckjusticar` to Moonpath's `moonpath.bsa`. The preceding Fable log-only
review's Beyond Reach/Bruma attribution was not supported. Provider identity
alone does not explain their alias-base-type mismatches; inspect actual PEX
base types and current quest/alias bindings separately under #157.
