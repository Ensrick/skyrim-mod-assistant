# Desktop focus repair — issue149

Status: installed candidate, **UNVERIFIED on the real desktop/in game**. No
assistant game launch, visible helper, dialog or audio occurred.

## Evidence and scope

Latest playtest logs show actual3840x2160 borderless flip-model output and
Media Keys Fix `DisableWindowsKey=false`, `BackgroundAccess=false`. Simply
restating borderless or changing resolution does not address the reproduction.

Installed official SSE Display Tweaks0.5.25 SHA
`DF7F352A3F13736709C5F9D265EBF311D9D77D373A9A1B8CBE2AEE7FDD8BA9F4`
has a callback at RVA2C440: loads the supplied HWND, calls GetWindowRect at
2C45B and ClipCursor at2C46A without a foreground check. A separate activation
callback compares GetFocus; the installed DLL does not import GetForegroundWindow.
The [public upstream window.cpp](https://github.com/SlavicPotato/SSEDisplayTweaks/blob/master/SSETweaks/window.cpp)
registers unconditional confinement on window sizing/position changes as well
as focus acquisition. The public source is older than0.5.25, so its exact callback
registration is supporting evidence, not claimed a source-identical build.
This establishes a credible reclip path, not a runtime trace proving it caused
every inaccessible-window occurrence.

Win32 explicitly describes the cursor as shared state and requires releasing
confinement before another application takes control:
[ClipCursor](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-clipcursor).

## Installed correction

- Separate original WindowFocusGuard0.1.0, sourcec091e917; no game-memory patches,
  ESP, save edits or replacement official rendering DLL.
- Owned Display Tweaks `LockCursor=false` paired with our guard. All other INI
  values unchanged: fullscreenfalse/borderlesstrue,119FPS and HavokMaximum0.
- Actual foreground PID/class/owner identity required for confinement. Windows
  key and AltTab release a desktop-intent latch; no forced focus, keyboard
  suppression, cursor warping or ShowCursor-counter manipulation.
- Independent16ms watchdog and foreground event listener; input observer always
  chains. A separate logger thread consumes a bounded nonblocking queue.
- Clip query/release failures retain ownership for retry. A different rectangle
  is never cleared. Win32 has no ownership token, so an identical-rectangle race
  with another program cannot be distinguished and is explicitly not guaranteed.

Independent review corrected three defects before installation: synchronous
file I/O on the hook thread, dropping ownership after a failed clip query, and
trusting a recycled HWND without rechecking process/class. Two native test
groups use the real production policy/lease; six pairing gate tests reject
overwriting DLLs, competing cursor owners, disabled guard and background input.

## Verification / recovery

Deterministic clean rebuild, `/W4 /WX`, exact runtime metadata, installed hashes,
zero-error MO2 audit and focused focus/cloak/weapon freshness gates pass.
The cloak reservation was regenerated only because its strict fingerprint
includes all enabled mods; all240 rules/meshes and349 plugins are unchanged.

Receipts: `records/source-builds/window-focus-guard-0.1.0.json`,
`records/source-builds/conditional-arrow-embedding-0.3.4.json` and refreshed
`records/source-builds/ensrick-full-cloak-exclusivity.json`.

Real acceptance still required: repeated Windows→click another app on either
monitor; AltTab both ways; minimize/restore; Start dismissed without changing
apps; gameplay/menu/shader stalls; browser scroll isolated on returning; clean
game exit. Do not close149 or call the desktop problem solved before this passes.
Rollback is paired: restore previous Display Tweaks config and remove/disable
WindowFocusGuard together under the claim, then refresh the cloak fingerprint.
