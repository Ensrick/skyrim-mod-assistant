# MO2Headless deployed build record

Date: 2026-08-28

Status: built from current fork source, regression tested, and deployed

## Provenance

- Repository: `Ensrick/modorganizer`
- Branch: `ensrick/headless-controller`
- Commit: `3769ece0fd4da0f99232be27b68fd51385c95e35`
- Commit subject: `Preserve single Bethesda data roots during staging`
- GitHub Actions run: `33024105521`
- Workflow result: success
- Artifact name: `modorganizer`
- Artifact digest: `SHA256:A6CC72DE595651D751D1A9177D32F2C8E0F4BBC2597365BEB3410BC5D08D045A`

The local rebuild attempt restored and built all 103 vcpkg dependencies but stopped at configuration because this workstation has Qt runtime files, not the Qt development CMake package. The successful GitHub Actions artifact was used instead; it was produced from the exact current fork commit, so installing a large local Qt SDK was unnecessary.

## Executables

| File | SHA-256 |
|---|---|
| `MO2Headless.exe` | `FEBD3C0A505689A41FF3CECF14569017DD9A36071D681AAEE6AC854CE0257A89` |
| `ModOrganizer.exe` | `9CBD793C0759DF7C5AD011C565085F80E08D46CCAAF91C331AD6C43FC87D6003` |

Only the verified headless controller replaced the live portable instance's older controller. The previous executable, SHA-256 `18469B00520CDC6C1924D6A2D5BBC5EF982C3AD3804EDABD9E14B277A52F1921`, remains recoverable under the instance's `backups/headless-controller` directory.

## Regression and deployment checks

1. Initialized a separate disposable portable Skyrim SE instance.
2. Staged a synthetic tree containing `SKSE/Plugins/preserve-root-probe.txt`.
3. Confirmed the installed path retained `SKSE/Plugins`; it was not incorrectly unwrapped to `Plugins`.
4. Ran the disposable-instance audit with no errors.
5. Verified no Skyrim, SKSE loader, Mod Organizer, or headless-controller process was active.
6. Backed up the previous live controller and replaced it with the verified artifact.
7. Verified the deployed executable hash and version.
8. Ran live-instance `status` and `audit`; both passed.

No game process was launched for these checks.
