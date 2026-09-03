# Display, Skyrim Unbound, and lighting fixes

Date: 2026-08-28

Status: configuration fixes applied and statically validated; foreground acceptance test pending

No mod was added or removed, and Skyrim was not launched during this work.

## 1. Borderless window and mouse ownership

The active SSE Display Tweaks log already proved that Skyrim was using a 3840x2160
windowed, borderless, flip-model swap chain. The failure was cursor ownership:
`LockCursor=false` had been set explicitly. Windows is configured to scroll an
inactive window under the pointer, so Skyrim's invisible cursor could reach the
second display and scroll a browser while the game still had focus.

Changed the active SSE Display Tweaks configuration to:

```ini
Fullscreen=false
Borderless=true
LockCursor=true
ForceMinimize=false
```

This captures the cursor only while Skyrim owns focus. The Display Tweaks window
hook releases it on focus loss or deactivation, so Alt-Tab or a successful Windows
key focus transfer should immediately free the cursor without minimizing Skyrim.

No Windows `NoWinKeys`/disabled-hotkey policy, Skyrim `bAlwaysActive` setting, or
second mod configuration that suppresses focus loss was found. The source-built
Display Tweaks window hook also does not intercept either Windows key.

If the Windows key itself still fails to transfer focus, that is a separate input
handoff defect. Patch the source-built Display Tweaks fork only after confirming
that behavior with `LockCursor=true`; do not undo cursor capture.

## 2. Skyrim Unbound startup

The installed Skyrim Unbound Reborn 3.0.17 is the current Nexus release. Its
plugin, quest, scripts, SKSE/SkyUI requirements, and starting-room cell are
present. The starting room is not driven by a physical object.

The active configuration explicitly enabled the restored intro-title option.
Changed:

```json
"intro_titles": 0
```

After closing RaceMenu, leave the staging room by either:

1. Press Enter outside any menu and choose **Current Settings** (or a preset), or
2. Open the Skyrim Unbound MCM and select **Begin Your Adventure** on its first page.

The configured hotkey is scan code 28, which is Enter. Auto-opening the MCM was
not enabled because the current Unbound version requires the separate MCM Shortcut
NG mod for that option, and no unrequested dependency was installed.

## 3. Community Shaders exposure

The current Community Shaders runtime log reported that the display supports HDR
but Windows HDR is disabled. The user settings nevertheless forced HDR output,
causing Community Shaders to select an HDR10 PQ/BT.2020 swap chain. Sending that
signal into the current SDR desktop path is consistent with the reported crushed
interiors and blown-out directly lit face.

Changed:

```json
"enableHDR": false,
"hdrAutoDetected": false
```

Advanced Skin's separate character-lighting feature was already disabled, so no
skin or SSS values were changed. Lux and its Community Shaders compatibility
plugin were also left intact. Lux may still be intentionally dark, but it should
only be judged after the HDR mismatch is removed.

## Recovery copies

The exact pre-change files are retained beside their active configurations:

- `SSEDisplayTweaks.ini.pre-fix-20260828-161558.bak`
- `SkyrimUnbound.json.pre-fix-20260828-161558.bak`
- `SettingsUser.json.pre-fix-20260828-161558.bak`

## Foreground acceptance test

1. Focus Skyrim and verify the wheel cannot scroll a browser on the other display.
2. Press the Windows key, then Alt-Tab separately. In both cases, verify that the
   cursor becomes usable outside Skyrim and Skyrim remains running behind the
   foreground window.
3. Start a new game and verify that the restored cart-intro titles no longer flash.
4. Finish RaceMenu, close all menus, press Enter, choose **Current Settings**, and
   verify that the game leaves the Unbound room.
5. Compare the character face, the Unbound room, and a normal interior. Confirm
   that the face is no longer clipped and the interior range is plausible.

If only the final lighting comparison remains too dark, tune Lux/CS lighting as a
separate aesthetic pass rather than compensating for the previous HDR output bug.
