# USSEP 4.3.9 missing-script investigation

Status: upstream defect confirmed; official corrected package downloaded and
inspected, **not installed yet**. This advances #157 and the current setup's
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
starred set, not all384 loaded base/Creation/light plugins. Resolve the base
ArmorAddons before finalizing update evidence; the old September7 broad
conflict report is stale and was not used as proof of current winners.

Main-BSA differences also include seven mesh paths (four changed, three
removed), consistent with the intervening official regression-fix changelog,
and333 changed FUZ containers. Do not describe the update as byte-identical
audio or only the missing script. An initial voice check wrongly expected
RIFF/WAVE; these files use RIFF/XWMA. The diagnostic now accepts that actual
container type. No decoded-audio/voice-quality equivalence has been established.
The texture BSA is byte-identical, SHA256
`d45e6e26fcf83c0a5bb1bacd7dc2d0c1b071853ae6fc0538f62b1d8b84e8ba74`.
Effective winning mesh providers still need final checks.

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
`records-work/ussep439c-20260910/`. No live profile/mod/INI/Keep state changed in
this investigation. Downloaded archive remains in the managed downloads folder.

## Other provider findings

The targeted archive scan maps `HLIOMQ1Script` to Remiel's `HLIORemi.bsa` and
`AnvilDencheckjusticar` to Moonpath's `moonpath.bsa`. The preceding Fable log-only
review's Beyond Reach/Bruma attribution was not supported. Provider identity
alone does not explain their alias-base-type mismatches; inspect actual PEX
base types and current quest/alias bindings separately under #157.
