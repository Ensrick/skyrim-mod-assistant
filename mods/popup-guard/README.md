# Popup Guard

Original, separately distributable SKSE plugin for the modpack's hidden-dialog
hang (#255). Requires the tested Skyrim SE 1.7.104 runtime. No game memory
hooks, Address Library, ESP, save edits or additional third-party mod dependency.
The only third-party code is MinHook 1.3.4 (BSD-2-Clause, statically linked,
license shipped as `LICENSE-MinHook.txt`).

Standing rule: no popups, ever; failures go to log files. On 2026-09-07 a
plugin's `stl::report_and_fail` parked the main thread in `MessageBoxW` behind
the borderless 4K game window; 52 enabled SKSE DLLs import `MessageBoxA/W` or
`FatalAppExitW`, so per-fork patching does not scale. This plugin installs
in-process inline hooks on the exported user32 entry points `MessageBoxA`,
`MessageBoxW`, `MessageBoxExA`, `MessageBoxExW`, `MessageBoxTimeoutA`,
`MessageBoxTimeoutW`, `MessageBoxIndirectA`, `MessageBoxIndirectW` and the
kernel32 entry points `FatalAppExitA`, `FatalAppExitW`. Every hooked call writes
one line (local time, API, calling module plus offset, flags, caption, text with
control characters escaped) to `Documents\My Games\Skyrim Special Edition\SKSE\
PopupGuard.log` and returns `IDOK` at once with no window. `FatalAppExit` logs,
then `TerminateProcess(1)`. `report_and_fail` therefore proceeds straight to its
own `TerminateProcess` and leaves a log line instead of a hidden modal loop.

The logger never blocks on anything but its own `WriteFile`: one SRW lock, one
unbuffered write per line, captions bounded to 256 escaped bytes, text to 2048,
one line to 4096, at most 1000 lines per session (then a final notice and
silence). A thread-local guard makes re-entry impossible even in theory. The
hooks never call the original functions, so no user32 dialog code runs.

`SKSE/Plugins/PopupGuard.ini` `Enabled=false` installs nothing and logs that.

## Load order and attach timing

SKSE iterates `SKSE/Plugins/*.dll` with `FindFirstFile` and, for plugins that
export `SKSEPlugin_Preload`, calls `LoadLibrary` during its preinit hook (before
the game's global initializers), then loads every other plugin in the same
enumeration order during `SKSEPlugin_Load`. The plugin therefore:

- is named `!PopupGuard.dll`: `!` (0x21) sorts before every digit and letter in
  NTFS enumeration (verified on this machine with `FindFirstFile` against the
  64 distinct installed plugin file names; `_PopupGuard.dll` would sort last)
  and MO2's virtual listing is name ordered too (`skse64.log` "checking plugin"
  lines of the 2026-09-07 launch are strictly case-insensitive alphabetical);
- exports `SKSEPlugin_Preload`, so it is mapped before any Load-phase plugin's
  DllMain even if a future name sorts earlier; only another preload plugin
  sorting before `!` could raise an unguarded dialog (EngineFixes is the only
  other preload plugin installed and sorts after);
- installs the hooks in `DllMain(DLL_PROCESS_ATTACH)`. Under the loader lock it
  touches only kernel32/ntdll (INI read via `CreateFileW`, `GetProcAddress` on
  already-loaded user32/kernel32) and MinHook, whose thread freeze and
  trampolines use its own private heap and `VirtualAlloc`; no shell32, COM,
  CRT file I/O, `LoadLibrary` or thread creation happens there. The Documents
  log needs `SHGetKnownFolderPath`, so it opens at the first SKSE entry point
  (`SKSEPlugin_Preload`, main thread, outside the loader lock); attach-time
  lines are buffered (16 x 512 bytes) and flushed then. In SKSE's flow nothing
  runs between our `LoadLibrary` and our `SKSEPlugin_Preload`.
- pins itself (`GET_MODULE_HANDLE_EX_FLAG_PIN`) at the first SKSE entry point:
  inline hooks must never outlive their code. A plain `LoadLibrary`/`FreeLibrary`
  pair without SKSE (the host tests) still unhooks on detach.

The installed SKSE build's own `SKSE_AUTOMATION_SILENT_UI` import redirection
applies only to automation launches and only to each plugin's own import table;
this guard covers user launches and every call path through the exported
functions. Both can coexist.

## Attribution and the funnel probe

The calling module comes from the hook's return address (`RtlPcToFileHeader`
plus `GetModuleFileNameW`), so it names the nearest frame that actually pushed
one. A wrapper compiled into a tail jump (`return MessageBoxW(...)` under /O2)
leaves no frame and is attributed to its own caller; CommonLibSSE-NG's
`report_and_fail` calls `MessageBoxW` then `TerminateProcess`, so it is a real
call and is attributed to the plugin DLL. The offset in the record locates the
call site for a disassembler either way.

On this machine (user32.dll 6.2.26100.9278) the probe found `MessageBoxA` and
`MessageBoxExA` calling `MessageBoxTimeoutA`, and `MessageBoxW` and
`MessageBoxExW` calling `MessageBoxTimeoutW`, with no direct edge from
`MessageBoxTimeoutA` or either `MessageBoxIndirect` variant to
`MessageBoxTimeoutW` within their first 96 bytes. A single `MessageBoxTimeoutW`
hook would therefore not provably cover the ANSI and Indirect paths; hooking
every export makes the behaviour independent of user32 internals. Because the
first hook to fire answers without calling the original, one call yields
exactly one record.

## Not covered

Dialogs from other processes (`skse64_loader.exe`, Windows Error Reporting),
comctl32 `TaskDialog`, custom dialog windows, and hangs that never call one of
the hooked entry points. Callers that inspect the answer see `IDOK` even for
`MB_YESNO` prompts (documented, logged; the flags are in the record).

## Build / distribution

Configure CMake with `-DSKSE_SDK_ROOT=<external checkout>` (header SHA pinned in
CMakeLists.txt; public SKSE commit `71f41da518f964345f0050471ec0232fa3a3afc8`
carries the identical header), the vcpkg toolchain file and triplet
`x64-windows-static` (`vcpkg.json` pins MinHook 1.3.4 at baseline
`ddd0023b`). `build.ps1` configures, builds Release, runs CTest and writes a
deterministic zip. Ship only `SKSE/Plugins/!PopupGuard.dll`,
`SKSE/Plugins/PopupGuard.ini`, this README, the monorepo LICENSE and
`LICENSE-MinHook.txt`; never ship the SDK. Build outputs remain ignored.

## Tests (host, CTest)

- `line_policy`: escaping, per-field truncation with visible markers, capacity
  bounds, opt-out INI parsing, 1000-line budget.
- `process_wide_hooks`: installs the production hooks in the test process,
  calls all ten entry points (`MessageBoxTimeout*` via `GetProcAddress`), asserts
  `IDOK` in under 50 ms with no window on the calling thread, loads a helper DLL
  whose own code calls `MessageBoxW` and checks the log names
  `PopupHelperDll.dll`, spawns a child that calls `FatalAppExitW` and checks
  exit code 1 plus its log line, then removes the hooks and verifies the
  user32 prologue is byte-identical again. It also prints an empirical funnel
  probe (direct call/jmp edges between the MessageBox exports of the loaded
  user32) before hooking; the guard hooks every export regardless.
- `plugin_dll_attach`: loads the real `!PopupGuard.dll` with plain
  `LoadLibrary`, proves DllMain installed the hook, checks the exported
  `SKSEPlugin_Version` (exact 1.7.104, no address library, no struct use) and
  the `SKSEPlugin_Preload`/`SKSEPlugin_Load` exports, proves an `Enabled=false`
  INI copy patches nothing, and that `FreeLibrary` restores user32.

## Acceptance (not yet performed)

Host tests prove the hook mechanics, not the game. On the user's next launch
verify `PopupGuard.log` shows the hook table, `preload phase` and `load phase`
lines, that `skse64.log` lists `checking plugin !PopupGuard.dll` first and
`preloading plugin "PopupGuard"` before EngineFixes, and that the game reaches
the main menu and loads a save. No automated game launch.
