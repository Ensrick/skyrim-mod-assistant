# Confirmed BTPS startup crash: repaired, runtime acceptance pending

## Evidence

Latest test: `crash-2026-09-07-15-55-13.log`, Skyrim 1.7.104,
SKSE 2.3.1, uptime 54.986 seconds. A C++ `Xbyak::Error` originates from
`Xbyak::CodeGenerator::opRR` at xbyak.h:2091, through `mov` and
`Hooks::SelectionHook::Hook`, during BTPS's DataLoaded hook installation.
BTPS's log stops immediately after `BTPS applying SelectionHook`.

The previous locally rebuilt 0.8.9 DLL attempts `mov(rcx, eax)`: a 64-bit
destination and 32-bit source. There is no such MOV encoding. Xbyak throws
`ERR_BAD_SIZE_OF_REGISTER`. This is a demonstrated defect, not a suspicion
based on the last mod in a crash stack. RAM pressure is visible, but does not
explain this specific, reproducible assembler exception. No shader/texture
removal or game downgrade is justified by this crash.

## Repair and tests

- Source repair commit: `98d5a5e`, on local BTPS `ensrick/1.7.104`.
- Use `mov(ecx,eax)`: the 32-bit reference handle is passed in ECX, with the
  upper RCX bits cleared. Production emission lives in `SelectionTrampoline.h`
  so the native regression tests the actual emitter, not a handwritten copy.
- Compiled `Hooks.obj` confirms the actual callback stores ECX into the
  4-byte ObjectRefHandle parameter. The callback updates CrosshairPickData
  through FocusManager, so the omitted original native target-store is not
  reintroduced over the mod's chosen target.
- Native test reproduces the OLD exception, then executes ten corrected
  combinations: handles 0/1/7FFFFFFF/80000000/FFFFFFFF, null and non-null
  selected references, deliberately dirty upper input bits, RBX/RCX outputs
  and jump-back. PASS.
- `audit/btps_hook_audit.py` checks actual PE bytes using the installed v5
  Address Library. Selection's seven-byte overwrite at RVA40AE08 and resume
  at40AE0F, stack allocation/alignment, horseback's thirteen-byte skip and
  resume, dismount and crosshair UI call destinations all PASS. This is an
  on-disk check, not proof against runtime detours from other plugins.
- Visual Studio 2022 / MSVC14.44.35207 RelWithDebInfo rebuild PASS. SKSE
  version-data gate PASS. Original compatibility edits remain intact; they
  are not all part of the repair commit. Corresponding source patch is in
  `patches/btps/`. The full compatibility build still needs source publication
  review before external release.

## Installed, reversible scope

MO2 transaction `20260907T211644698Z-12e0891e937e` recoverably replaces only
`Better Third Person Selection 1.7.104 Native Overlay - Ensrick`, retaining
enabled state and priority326. Original Nexus64339/file635566 is untouched.
The package includes the corrected DLL, matching PDB, Apache-2.0 license and
modified-source notice. No vendor assets, settings or gameplay records changed.

Old DLL SHA256:
`125D4F0C500FAC488910364A5C0480B7FE5B19EE86FFCB8F57E038D48F6A0278`.
New installed/winning DLL SHA256:
`FDFD14DF622E9F708133F2D6CEB0F3DA43270179523DCF0595C50C04AC555542`.
New DLL2844160bytes, PE timestamp2026-09-07T21:14:13Z. Winning provider and
absence of an overwrite-folder DLL independently checked. Existing receipt
and only the BTPS ledger row were updated; unrelated dirty work is preserved.
Recovery/log/profile/ledger snapshots are under
`records-work/btps-crash-20260907/before/`; controller retains replaced files.

The first preflight found stale weapon/cloak proofs. Comparison with the last
verified377-input weapon manifest isolated ONLY an adjacent master-order swap:
AHZmoreHUD.esl and Thanedom Assets.esl. Transaction
`20260907T212021778Z-95b1405efbc8` restores moreHUD to priority37, immediately
after Thanedom Assets, matching the recorded vetted order. Both generated
patch gates then PASS without modifying either patch or falsifying manifests.
No mod or plugin was added/removed/enabled/disabled. Cause of that order drift
is not established; do not claim this fixes the process that produced it.

## Acceptance and remaining warnings

Full preflight: zero blockers after restoring the verified order. Warnings
remain: last crash is still the last test, stale game-side plugin-list mirror,
Steam overlay status cannot be verified from disk, five preexisting ledger
gaps (#102), a CRF/Lux Water CELL conflict, and native-currency save restrictions.
The temporary claim warning disappears after release. These are not proven
causes of this exception. Do not silently choose a winner for CELL006439:
dawnguard.esm between Ensrick CRF Semantic Patch and Ensrick Lux Water CS Patch;
inspect desired fields and honor the user's conflict-decision policy.

**No game/UI launch, save edit, or desktop interaction performed.** Keep this
issue open until a user-authorized run completes startup, logs `BTPS finished
applying hooks`, and verifies object selection/activation in first and third
person and horseback. Native tests remove the demonstrated code-generation
failure; they cannot certify the whole modlist stable or rule out later faults.

## Reproduce the headless regression

From the BTPS source directory in an x64 Visual Studio developer shell:

```bat
cl /nologo /EHsc /std:c++20 /O2 /I src /I build\vcpkg_installed\x64-windows-static-md\include tests\selection_trampoline.cpp /Fo:build\selection_trampoline_test.obj /Fe:build\selection_trampoline_test.exe
build\selection_trampoline_test.exe
cmake --build build --config RelWithDebInfo --target BetterThirdPersonSelection --parallel 2
```

Run the Python hook audit with explicit paths to the game EXE and installed
`versionlib-1-7-104-0.bin`. It performs no game writes and starts no UI.
