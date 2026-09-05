# Farming Creation payload recovery — 2026-09-04

Issue: [#142](https://github.com/Ensrick/skyrim-mod-assistant/issues/142)

## Finding

The complete official Farming BSA already existed in the MO2 `overwrite`
directory. It was written on 2026-09-01 while Skyrim's Creations downloader was
running through MO2. The physical game `Data` directory had no live BSA and
retained only a truncated backup.

| artifact | bytes | SHA-256 |
|---|---:|---|
| recovered `overwrite\ccvsvsse004-beafarmer.bsa` | 18,261,078 | `CBA7DC555FD2636DA3B6BCD6EB95C041B1241F6ED85C820238D4B550C872E3CE` |
| live `Data\ccVSVSSE004-BeAFarmer.esl` | 485,046 | `3CFF6FEAB109B434D1EC9C85F2ED996FDC73302BF3173388300170BA19B3FF9D` |
| parked truncated BSA | 4,194,256 | `0BA23E5C3D9613F3456EFAB1F9AC85024F3248FE672FC58CF6A365669C55957E` |

The BSA and ESL total 18,746,124 bytes, exactly the `FilesSize` recorded for
Farming in `%LOCALAPPDATA%\Skyrim Special Edition\ContentCatalog.txt`
(Creation ID `CSV2_6e6062c2-1c8d-47b0-891e-ef1171cca870`, version
`1663102599.3`). The truncated file is byte-for-byte the first 4,194,256 bytes
of the intact BSA. Both advertise BSA version 105, 10 folders and 182 files;
the old file is an interrupted write, not a different valid release.

After recovery, the live BSA was also parsed and every indexed entry was fully
decoded through the project's v103/104/105 BSA reader. All 182 entries decoded
successfully (18,252,308 uncompressed bytes); there were zero empty results,
decompression failures, or declared-size mismatches. This tests the whole
archive rather than trusting only its header and outer SHA-256.

All 466 retained MO2 archives were searched. None contains the official BSA or
ESL. `659-595607.7z` is the SMIM Farming Creation Club visual patch: three NIF
meshes only. It presupposes the official payload and cannot restore it.

## Guarded repair

With Skyrim, Mod Organizer and MO2Headless absent and the shared claim held by
`sol-lifecycle-20260904`, the intact recovered BSA was copied to:

`C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data\ccvsvsse004-beafarmer.bsa`

The operation refused to overwrite an existing target. Post-copy verification
returned 18,261,078 bytes and the expected SHA-256. The recovered overwrite
source and truncated `.bak` were intentionally retained until runtime
acceptance, so rollback and byte comparison remain possible. The claim was
released immediately afterwards.

## Remaining acceptance

Run a fresh-character initialization and save/load round trip, then confirm the
previous load-phase corruption signature does not recur. Only after that pass
should the duplicate recovered source be removed from `overwrite`; retain the
truncated file only as long as issue #142 needs forensic evidence.

Authoritative recovery guidance: Bethesda Support describes the Creations
library “Download All” path; SKSE identifies 1.7.104 as the current Steam
runtime. Bethesda's August update notes do not list a Farming content removal.

## Sources checked

- [Bethesda Support: download all owned Creation Club content](https://help.bethesda.net/app/answers/detail/a_id/54457/)
- [Bethesda: Skyrim Update — August 20, 2026](https://elderscrolls.bethesda.net/en-US/news/skyrim-update-august-20)
- [SKSE: current Steam AE runtime 1.7.104](https://skse.silverlock.org/)
- [Nexus guide: downloading Creation Club content files](https://www.nexusmods.com/skyrimspecialedition/articles/6649)

These pages establish the supported recovery path and current runtime. The
decisive Farming diagnosis is local byte evidence: exact catalog size, matching
ESL, BSA header counts and the truncated file being an exact prefix of the
complete payload.
