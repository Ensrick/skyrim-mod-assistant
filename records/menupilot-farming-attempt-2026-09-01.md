# Farming (ccvsvsse004) re-download attempt via MenuPilot - 2026-09-01, launches 1+2

Goal (#142 last item): restore `Data\ccvsvsse004-beafarmer.bsa` through the
game's own Creations flow, headlessly. Outcome: NOT achieved; the store is a
native UI the pilot cannot read, and the two engine-side shortcuts tried
either did nothing (first-run INI flag) or crashed (ExternalInterface invoke).
Build state after the session is identical to before it (INIs restored to
their pre-edit SHA256, .bak pair untouched, patch plugins unchanged).

Expected artifact when it is done: `ccvsvsse004-beafarmer.bsa` = 18,261,078 B
(`%LOCALAPPDATA%\Skyrim Special Edition\ContentCatalog.txt`: Farming
FilesSize 18,746,124 = bsa + 485,046-B esl; catalog Timestamp 1788296287 =
the 08-31 22:04 re-acquisition).

## Launch 1 (18:17:04, `launch_verify.py --no-autoload --leave-running`, MENU-ONLY t+48.8s)

Logs: `records/tool-runs/menupilot-20260901-launch1-creations-store.log`,
`launchprobe-20260901-launch1-creations-store.log`, `records/launch-verify-20260901-181756.md`.

| pilot step | result |
|---|---|
| `menu.list`, `menu.query Main Menu` | 39 menus, `Interface/StartMenu.swf`, `Mod Manager Menu` registered but closed (never opened by the engine in either launch) |
| dump `MainList.EntriesA` | `$CONTINUE $NEW $LOAD $CREATIONS $CREDITS $QUIT`; CREATIONS index 5 at list position 3 |
| `input.tap Down` x3 (code 208) | `iSelectedIndex` 1,2,3; `selectedEntry.text=$CREATIONS` (first ever exercise of input.tap: works) |
| `input.tap Accept` (28) | LaunchProbe +123869ms `Login Menu` open, +124122ms `Marketplace Menu` open, Login closed; `strCurrentState` stays `Main` |
| `menu.query Marketplace Menu` + dump | `swf=Interface/CreditsMenu.swf`, 77 credits-only members. Native store; no tiles/buttons reflected |
| exe string table (`SkyrimSE.exe`) | `MarketplaceMenu::InputHandler`, `MarketplaceCategoryConfiguration.json`, `MarketplaceTextures.bsa`, `CreationsOptionDownloadAllCC`, `CreationsSurePromptDeleteAll`, `UI_DialogDownloadCC`, `DownloadAll::uiCallback`; no CEF/webview DLL in the process |
| `input.tap Cancel` (15, Tab) | store closed (+371377ms MENU_CLOSE), `strCurrentState=Main`, selection back to 0 |
| Down x5 -> `$QUIT`, Accept | `strCurrentState=MainConfirm`, text "Quit to desktop?  Any unsaved progress will be lost." |
| Accept | clean exit, no crash log |

## Launch 2 (18:27:04, same flags, `bUpsellOwned=0` in profile AND Documents SkyrimPrefs.ini, MENU-ONLY t+31.6s)

Logs: `menupilot-20260901-launch2-upsell-downloadall.log`,
`launchprobe-20260901-launch2-upsell-downloadall.log`,
`crash-2026-09-01-18-43-46-externalinterface-invoke.log` (all in `records/tool-runs/`).

| time | step | result |
|---|---|---|
| 18:27:36-18:33:08 | idle at main menu, poll Data every 10s | no `ccvsvsse004-beafarmer.bsa`, no file newer than 1 min in Data; `_Sky10UpSell._visible=false` (AE owned), `DLCPanel.warningText="Loading Add-Ons"`, `LoadingContentMessage._visible=true`, `NewContentText=" "` throughout; no MessageBoxMenu |
| 18:34:50-18:35:49 | CREATIONS -> store (Login Menu again), 60s inside | nothing written |
| 18:35:51-18:38:58 | Cancel, 3 min at main menu | nothing written; panel text unchanged |
| 18:40 | Down x3 from a non-reset selection landed on `$QUIT`; readback guard refused Accept | (why every Accept is preceded by a text readback) |
| 18:41 | Up x2 -> CREATIONS, Accept, `input.tap` O (code 24, empty user event) | store open; no Scaleform menu opened, `MessageBoxMenu` closed. Native options list state unknowable -> no further input |
| 18:42 | Cancel; dump `Menu_mc.codeObj` | same 13 login callbacks as `_root.CodeObj`; no `DownloadAll` |
| 18:43:46 | `gfx.invoke _global.flash.external.ExternalInterface.call ["OpenCreditsMenu"]` (plumbing test for the FxDelegate route, harmless target) | CRASH: AV `SkyrimSE.exe+117AB19` `cmp [r8+rdx*1], r15b` reading 0x0; stack `MenuPilot.dll+4FA5` (main.cpp:570 `view->Invoke`) -> GFx -> engine. Game gone; both launches spent |

## Cleanup done

- `bUpsellOwned` restored to 1 in both INIs; SHA256 prefixes match pre-edit
  (profile `cf485eb88b91`, Documents `a5ddefc0aa4b`). `preflight.py` clean
  (8 warnings, none from this work except the archived INI snapshot).
- Note: `preflight_extra` reported this session that MO2 reads
  `profile/settings.ini` (`LocalSettings=false`), so the game most likely read
  the Documents INI; editing both copies is what made the flag take effect.
- MO2 dead, no pending `commands.jsonl`, Steam shut down and restarted from a
  shell with no `SKYRIM_LAUNCH_PROBE_*` / `SKSE_AUTOMATION_SILENT_UI` (#141).
- Claim `farming-store` released.

## What would make it headless next time

1. A MenuPilot op that resolves the main menu's `FxDelegateHandler` callback
   by name (`DownloadAll`) and calls it natively with proper `FxDelegateArgs`
   - the engine's own "download all owned CC" routine, main-menu context.
2. Or: reproduce the full 08-31 reset-INI state (`uiMarketplaceUpdatedHash=0`
   plus `bUpsellOwned=0`) and watch whether the engine re-syncs unattended.
3. Or the human path, ~30s: main menu -> CREATIONS -> O -> "Download all
   owned Creation Club Creations" -> confirm -> quit via menu.
