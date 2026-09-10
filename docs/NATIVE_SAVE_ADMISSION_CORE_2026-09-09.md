# Native admission reader evidence — September 9, 2026

[#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) OPEN.
Implemented [original native core](../mods/save-load-admission/README.md) for
the ordinary-load admission gap. Static library/CLI/tests only; **no runtime
adapter or installed load rejection policy**. No game launch this batch.

## Exact-input and corpus evidence

Read-only native-versus-Python comparison covered all38 ordinary ESS files
plus the admitted isolated Save7, and all39 paired SKSE co-saves. Native ESS
metadata and ordered full/light plugin names match audit/save_plugin_gate.py
on every input. All39 real saves use compression2/LZ4; compression0 and1 are
covered by synthetic fixtures, not claimed as real-game samples.

Currency acceptance and successful checkpoint values match
audit/currency_save_gate.py for fingerprint `6270B86774F9F4F3`. Only admitted
Save7 matches the current checkpoint; the38 ordinary saves do not. A missing
or incompatible checkpoint is not evidence of age, Papyrus corruption or
permission to migrate. Every ESS and co-save SHA256 was rechecked after reads
and remained unchanged. Private harness: records-work/check-native-save-corpus.py.

Exact Adventurer3 Autosave3 has77 full and301 light plugins, ESS SHA256
`ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
Native `compare` against the admitted Save7 table reports precisely:

```text
missing plugin: TrueHUD.esl
missing plugin: QuickLootIE.esp
```

This comparison uses another save as a reference, NOT a runtime snapshot.
Admitted Save7 has77 full and307 light plugins, SHA256
`2C281D826882059055880286E55CBEE31E800B4D760EAC0D6993DD1364161167`.
No original was rewritten, moved, cleaned, or passed to an engine load.

## Implementation verification

Native626 synthetic checks pass locally. Coverage includes all3 compression
modes, overlapping LZ4, every truncation of minimal complete fixtures,
deflate checksum/output/trailing-byte checks, bounded counts/screenshot
arithmetic, filename UTF-8/path safety/duplicates, missing and changed-class
plugins, co-save envelope and currency checkpoint identity/limits. Pending
currency observations need not be equal and are preserved as valid.

Final local inspection executable SHA256:
`A716E98972B46B381A156E8D84BC98E51A9435DBB590982214F80DB41635781D`.
Both pre-UTF8 and final post-UTF8 builds passed the39-pair corpus comparison.
Build dependency zlib1.3.2 is compiled from the upstream SHA256-pinned archive,
not a legacy library found in another mod. Its provenance/license notice is
included. No vendor DLL, game save, mod asset or build output is published.

Hosted Windows/Linux regression and Linux ASan/UBSan workflow added. Its
actual results must be checked after publication; local tests are not hosted
CI or engine verification. First hosted run34437906874 failed at dependency
download: zlib.net returned bytes with SHA256 f5921a86..., not the pinned
release. The correct1502830-byte archive is present locally. Switched to the
upstream GitHub release asset357391855 as preferred mirror; its API digest
matches the SAME expected hash. Hash verification was not relaxed. The cause
of the differing hosted response is not established; no foreign bytes built.

## Still required

The next adapter must use the exact engine-resolved filename, real loaded
plugin table and initialized currency bridge identity. It must hold/check
paired input identity through engine use, catch errors at the ABI boundary,
and use race-safe rejection/cancellation with a useful in-game explanation.
Ordinary load routes and post-rejection character preservation still require
actual engine tests. Non-ASCII case equivalence needs Windows-compatible
handling; current byte-preserving comparison folds ASCII only.

No disk profile mutation claim was needed or held; existing installed root
SKSE/MenuPilot and Default profile stayed untouched. Other assistants' dirty
files remain excluded. This prerequisite does not fix the original MCM crash,
settle the campaign-recovery choice or complete the larger goal.
