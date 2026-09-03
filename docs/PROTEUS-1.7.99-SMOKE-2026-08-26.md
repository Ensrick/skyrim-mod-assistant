# Proteus 1.7.99 native smoke record

Date: 2026-08-26 18:28-18:31 CDT

## Qualified inputs

- SkyrimSE.exe: 1.7.99.0, SHA-256 `B34E3655489DD655EB12B8221E24F8CE38524ED4E292E07BF3B977CDB488DAAA`
- SKSE: 2.3.0
- Address Library: format 5 `versionlib-1-7-99-0.bin`, SHA-256 `184FCA0C834E0D2523B450D18EA32C9FBF9F6295E88E936712B7360F1FCCC4EC`
- Official Proteus: 3.4.0, Nexus mod 62934 file 497484
- Official `ProteusDLLUtils.pex`: SHA-256 `6A036D98AA8D74C56216EEECA6761CEE5D00A81B0BB3E6BB4709CB8E57F94DB3`
- Fork: `Ensrick/ProjectProteusUtils` commit `324e07cd75196f444f6bafdfa09527d561a3c034`
- Candidate `Proteus.dll`: 766,976 bytes, SHA-256 `316DF6BB9045B34F422087CFC127D314622AB8640EC7AD5CDEE13255D408B41A`

## Deployment

The official `Proteus` MO2 mod supplies `PROTEUS.esp`, Papyrus scripts, source,
and interface assets. `Proteus 1.7.99 Native Overlay - Ensrick` is a separate,
higher-priority mod supplying only `SKSE/Plugins/Proteus.dll` plus a local root
marker. This keeps rollback to the official DLL to one mod toggle.

The disposable profile `Proteus Smoke 1.7.99` was cloned from `Default`.
`PROTEUS.esp` and the overlay were enabled there first. A process launched
inside MO2's VFS hashed the effective DLL and obtained the candidate hash,
proving that the overlay won the conflict.

## Results

The offline verifier passed the DLL exports, all 34 native ABI signatures, C++
registrations, official PSC/PEX contract, exact game executable, and exact
Address Library. A 120-second bounded SKSE launch produced no crash log.
`Proteus.log` reported:

- Proteus 1.1.0 loaded;
- perk functions registered;
- spell functions registered;
- item functions registered;
- actor functions registered;
- utility functions registered;
- form functions registered.

The same layering was then promoted to `Default`; MO2's audit returned no
errors, `PROTEUS.esp` was enabled, and a second VFS hash confirmed the candidate
DLL. RaceMenu already had `bExternalHeads=1`. MCM Helper remains disabled
because Proteus uses SkyUI's MCM API directly and does not list MCM Helper as a
requirement.

## Remaining acceptance work

This is a loader/native-registration pass, not a claim that the full Proteus
feature matrix is complete. Verify MCM registration in a disposable save, then
execute the character-switch, persistence, survival, alternate-start, rollback,
and soak gates in the fork's `docs/TEST-MATRIX.md` before public release.
