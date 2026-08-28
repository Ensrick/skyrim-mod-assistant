# Skyrim 1.7.104 native-runtime rebuild record

Date: 2026-08-28

Runtime target: `SkyrimSE.exe` 1.7.104.0

Status: Proteus native loader gate passed; ConsoleUtil and Proteus gameplay tests still pending

This record covers only the locally rebuilt SKSE native components needed to test Proteus. It is not permission to redistribute binaries, source, or mod assets.

## Installed overlays

| Component | Local overlay | SHA-256 | MO2 priority |
|---|---|---|---:|
| Proteus | `Proteus 1.7.104 Native Overlay - Ensrick` | `D2FA06B2D269E682F07D432356FD02D64ED84F70BE34652010F36E9EB3FAC50B` | 106 |
| JContainers | `JContainers 1.7.104 Native Overlay - Ensrick` | `F58CF37728A54552B08A2E3C4C6C2CF2F63955F3FA59B03640C60F129DF701B5` | 107 |
| PapyrusUtil | `PapyrusUtil 1.7.104 Native Overlay - Ensrick` | `0D5648E2415E1F48248D14774F19DC0DBFDF2A733D5149BB0F1E9CEF04CA2953` | 108 |
| RaceMenu / SKEE | `RaceMenu 1.7.104 Native Overlay - Ensrick` | `7290EAFD4116E742AA7477D34BF137ABBEFED936CD44E67FDC829F2E36925ED1` | 109 |
| ConsoleUtil | `ConsoleUtilSSE 1.7.104 Native Overlay - Ensrick` | `7775AA6E70C7608317ADF28D27B09673EA9C8DE98902CE16E08CF5986958722D` | 110 |

The overlays contain the replacement native DLL only and deliberately load after the corresponding base mod. Their installed path is `SKSE/Plugins/<dll>`. The base mods remain responsible for scripts, interface files, configuration, and other assets.

## Source provenance

| Component | Local source directory | Branch | Starting revision | Upstream |
|---|---|---|---|---|
| Proteus | `skyrim-tools-source/ProjectProteusUtils-1.7.104` | `ensrick/1.7.104` | `324e07cd75196f444f6bafdfa09527d561a3c034` | `Nightfallstorm/ProjectProteusUtils` |
| JContainers | `skyrim-tools-source/JContainers-1.7.104` | `ensrick/1.7.104` | `90db5e29183a0a36b992e9cb010860640e47a14c` | `ryobg/JContainers` |
| PapyrusUtil | `skyrim-tools-source/PapyrusUtil-1.7.104` | `ensrick/1.7.104` | `01ac25db3969a09822c2d5d9de830bc567417f9e` | `eeveelo/PapyrusUtil` |
| RaceMenu / SKEE | `skyrim-tools-source/RaceMenu-1.7.104` | `ensrick/1.7.104` | `748ca80c30ada6dba54528aa1a5a11db96870afd` | `expired6978/SKSE64Plugins` |
| ConsoleUtil | `skyrim-tools-source/ConsoleUtilSSE-NG-1.7.104` | `ensrick/1.7.104` | `fd89858` | `VersuchDrei/ConsoleUtilSSE` |

The first four working trees contain local compatibility changes and build output. Their hashes identify starting revisions, not a claim that the installed binaries can be reproduced from unmodified checkouts. ConsoleUtil is the first component in this set whose changes are committed to a public fork and whose installed DLL comes from a successful clean CI run. The other local changes must still be cleaned, reviewed, committed where legally permitted, and built by reproducible automation before any public release.

## Verification evidence

- Proteus verification suite: 37 tests passed and the release verifier passed.
- The MO2 profile audit passed after the first four overlays were installed,
  and passed again after the ConsoleUtil overlay was added.
- A bounded 120-second SKSE run checked 21 native plug-ins and refused zero.
- SKSE logged all four replacement DLLs as loaded correctly.
- Proteus identified itself as local build `1.1.0.104` and registered Perk, Spell, Item, Actor, Utility, and Form native groups.
- JContainers and PapyrusUtil initialized for Skyrim 1.7.104.0 and registered their functions.
- No new crash log was produced during the bounded run.
- ConsoleUtil's clean CI run `33208154245` passed its build, file-version,
  export, non-modal logging, and source-compliant packaging gates. Its overlay
  was then installed transactionally and the MO2 audit passed. It has not been
  loaded in-game since installation.

This proves loading and native registration only. It does not prove Proteus MCM registration, character creation, character switching, save/reload persistence, inventory isolation, appearance restoration, follower behavior, or global quest-state behavior.

## Licensing and publication gate

- Proteus source contains a GPL-3.0 license. Any distributed derivative must satisfy that license and include corresponding source; this does not automatically grant rights to unrelated packaged mod assets.
- JContainers source contains the MIT license and its copyright notice must be retained.
- ConsoleUtil source is GPL-3.0-or-later with explicit modding/linking exceptions; its CI artifact includes the Papyrus source, symbols, license, exceptions, and dependency notices.
- No clear top-level license was found in the inspected PapyrusUtil or RaceMenu/SKSE64Plugins source trees. Their rebuilt binaries and local changes remain private until their licensing and third-party dependencies are reviewed.
- None of these DLLs may be bundled into a public mod pack merely because they function locally.

## Remaining acceptance test

On the next user-authorized foreground game run:

1. Confirm Proteus and QuickLoot are visible and functional.
2. Confirm `ConsoleUtilSSE.log` contains no VM type-ID failures.
3. Let MCM registration settle and confirm the Proteus menu.
4. Use a disposable save to create and switch a character.
5. Save, reload, and switch again.
6. Verify inventory, appearance, perks/spells, location, followers, and shared quest state.
