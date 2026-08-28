# ConsoleUtilSSE 1.7.104 rebuild record

Date: 2026-08-28

Runtime target: `SkyrimSE.exe` 1.7.104.0

Status: clean CI build installed as an MO2 overlay; runtime acceptance pending

## Why the official DLL is not yet sufficient

The installed Nexus release is ConsoleUtilSSE NG 1.6.1 (mod 76649, file
793316). It loads under SKSE, but the current runtime log records two failures
to resolve VM class type 61. Source inspection maps those messages to
registration of `GetSelectedReference` and `SetSelectedReference`, the two
native functions that exchange `TESObjectREFR` values with Papyrus.

This matters to Proteus. Its scripts call `SetSelectedReference` before several
console-driven actor operations, so a successful SKSE loader message alone is
not an adequate acceptance test.

The official 1.6.1 source predates CommonLibSSE-NG commit
`68ae73e1cb99cdf81cd406918531d0570fe1e332`, which corrected the AE 1.7.99+
layout shift in `SkyrimVM` and `PlayerCharacter`. The local rebuild uses a
newer pinned CommonLib revision containing that correction.

## Source provenance

- Fork: `Ensrick/ConsoleUtilSSE`
- Branch: `ensrick/1.7.104`
- Upstream: `VersuchDrei/ConsoleUtilSSE`
- Upstream base: `fd89858`
- Current rebuild commit: `ad5e6e529341c8b730a0255ec9cb68fb4fe5eb59`
- CommonLibSSE-NG pin: `70c1acd5261210982bd52f6d4468a082fe04d798`
- Declared DLL file version: `1.6.1.104`

## Local changes

- Require the exact audited CommonLib revision by default. A deliberately
  named CMake override is required to build against any other revision.
- Rebuild for the 1.7.104 runtime while preserving the official Papyrus API.
- Replace the logging initialization's modal fatal-report path with a caught,
  logged plug-in load failure. A logging failure must not create an error box
  on the user's desktop.
- Add a clean GitHub Actions build with current official action releases.
- Verify file version and the three SKSE exports before publishing an artifact.
- Upload the DLL, symbols, Papyrus sources, license, exceptions, and dependency
  license notices together.

## Verification completed

- The release build completes locally against the exact CommonLib pin.
- The DLL reports file version `1.6.1.104`.
- `SKSEPlugin_Load`, `SKSEPlugin_Query`, and `SKSEPlugin_Version` are exported.
- The logging source contains no `report_and_fail` modal path.
- The local release DLL SHA-256 is
  `E4D31AC54DBD54474A0E482017339DCAB6620846EFB91C94F811CD56A2B20A97`.
- A negative configuration test using a deliberately wrong CommonLib revision
  fails as designed.
- GitHub Actions run `33208154245` passed at rebuild commit `ad5e6e5`.
- Its source-compliant artifact digest is
  `sha256:102e36ebe3055940d9e53b4c79aed6d1e49039f02738ab81d5927c47f1c5da4a`.
- The CI-built DLL SHA-256 is
  `7775AA6E70C7608317ADF28D27B09673EA9C8DE98902CE16E08CF5986958722D`.
- The CI DLL reports file version `1.6.1.104`, exports all three required SKSE
  entry points, and imports only standard Windows/DirectX libraries.

The clean hosted artifact is installed as
`ConsoleUtilSSE 1.7.104 Native Overlay - Ensrick` at MO2 priority 110. It was
admitted transactionally as `20260828T204303046Z-84343993f71e`, after a
successful dry run, and the post-install profile audit passed. The overlay
replaces only `SKSE/Plugins/ConsoleUtilSSE.dll`; the official mod remains
installed underneath it and continues to provide every other file. No copy of
the DLL exists in Skyrim's physical `Data` directory.

## Runtime acceptance gate

On the next user-authorized foreground launch:

1. Confirm the rebuilt DLL loads under SKSE 2.3.0 and Skyrim 1.7.104.
2. Confirm `ConsoleUtilSSE.log` no longer contains `Failed to get vm type id`.
3. Exercise a harmless selected-reference read/write path.
4. Confirm Proteus operations that use `SetSelectedReference` behave normally.
5. Preserve the foreground game's normal audio and display behavior; no
   autonomous background launch is authorized for this check.

## License and publication

The fork retains the upstream GPL-3.0-or-later license, its explicit modding and
linking exceptions, and bundled third-party license notices. Any distributed
binary must be accompanied by the corresponding source and required notices.
This source license does not grant redistribution rights to unrelated Nexus
packages or assets.
