# Window Focus Guard

Original, separately distributable SKSE plugin for the modpack's Windows focus
regression (#149). Requires the tested Skyrim SE 1.7.104 runtime. No game memory
hooks, Address Library, ESP, save edits or additional third-party mod dependency.

The official SSE Display Tweaks rendering and Havok fixes stay installed.
Its **LockCursor must be false** when this plugin owns cursor confinement.
Media Keys Fix must retain `DisableWindowsKey=false` and `BackgroundAccess=false`.
No fullscreen, resolution, framerate, physics or lighting settings are changed.

The independent message thread confines to the actual foreground game client.
It releases its own rectangle on foreground loss, minimizes, window destruction,
Win key and Alt-Tab. A desktop-intent latch prevents immediate reclipping while
Start or the task switcher opens. A real foreground return or intentional fresh
click on the game resumes confinement. The keyboard observer always chains all
events and records no key contents. It never forces activation, sends input,
warps the cursor or changes ShowCursor counters. A 16ms watchdog still runs when
the game's main/render thread stalls. No helper process or visible window exists.

ClipCursor has shared state, not an ownership token. We track our last rectangle
and release only if it still matches; a different application's rectangle is not
cleared. A different application using exactly the same rectangle in the tiny
activation race cannot be distinguished by Win32. No absolute zero-race guarantee
is claimed. Hook failure falls back to polling and is logged; timer failure leaves
the cursor free. This intentionally favors desktop access over confinement.

## Build / distribution

Configure CMake with `-DSKSE_SDK_ROOT=<external checkout>` and MSVC x64. Header SHA
is pinned in CMakeLists.txt; public SKSE commit
`71f41da518f964345f0050471ec0232fa3a3afc8` contains the identical header.
The local build used checkout872c2d6 (unpublished headless changes elsewhere);
those changes are not needed or shipped. CI fetches the public header commit.
The SDK remains an external build input.
Build Release and run CTest. Ship only our DLL under `SKSE/Plugins` plus the owned
configuration overlay; never ship the SDK or vendor Display Tweaks DLL.
Original source uses the monorepo LICENSE. Build outputs remain ignored.

## Acceptance (not yet performed)

Host tests check foreground/desktop-intent policy, not actual gameplay. On the
user's next launch, verify logged initialization, Win then click another app on
either display, Alt-Tab both ways, minimize/restore, menus, resolution changes,
shader compilation, game exit and no scroll/input reaching a background browser
after returning. Repeat Win workflows, including dismissing Start without moving
to another app. Keep #149 open until this passes. No automated game launch.

The hook/timer thread has no file I/O: a bounded nonblocking queue sends log
events to a separate logger thread. Ownership release failures retain the lease
for retries, and cached window handles are revalidated by PID/class/owner to
reject recycled HWNDs. Two test groups exercise the actual production policy and
lease implementation, including failed queries/releases and foreground loss
during confinement. These do not claim to simulate the entire Windows desktop.
