# Active runtime issues — 2026-08-28

These are observed faults, not permission to change settings or launch Skyrim
during an active user test. Diagnose them headlessly first and ask before a new
game launch.

## P0 — Proteus native component is not working

**Observed:** Proteus features and MCM are absent. The current SKSE session log
rejected `Proteus.dll` on Skyrim 1.7.104. It also rejected
`JContainers64.dll`, `PapyrusUtil.dll`, and RaceMenu's `skee64.dll`; those are
part of the dependency path Proteus needs for a meaningful functional test.

**Prior evidence is insufficient:** the 1.7.99 native-overlay smoke test proved
that six native function groups could register on that older runtime. It did
not prove end-to-end character creation, switching, persistence, or 1.7.104
compatibility.

**Next acceptance gate:** every required native dependency loads on 1.7.104;
the Proteus log registers its functions without loader errors; its MCM appears;
then a disposable save passes create, switch, save/reload, and inventory/state
isolation tests.

## P0 — Secondary-sized image nested inside the primary display

**Observed:** after Community Shaders finished compiling, Skyrim still rendered
a screen-sized image inside the game window. The nested image appears to be
2560×1440, matching the secondary monitor, while the primary monitor and
configured game output are 3840×2160. The problem therefore is not explained by
an unfinished shader compilation.

**Known configuration evidence:** Windows reports the 3840×2160 display as
primary and the 2560×1440 display to its left. `SkyrimPrefs.ini` requests
3840×2160 borderless windowed output, and the SSE Display Tweaks log also
records a 3840×2160 request.

**Next acceptance gate:** identify which component owns the incorrectly sized
render target or viewport; verify Windows DPI/scaling, window placement,
swap-chain dimensions, Community Shaders/upscaling state, and Display Tweaks
overrides; then confirm true 3840×2160 borderless output on the primary display
with clean Alt-Tab and cursor release behavior.

## Investigation order

1. Repair the rejected Proteus dependency chain without launching the game.
2. Audit the effective display, scaling, and shader configuration plus the
   latest logs without changing the user's live test.
3. Prepare one bounded validation launch covering both issues, but run it only
   with explicit user approval.
