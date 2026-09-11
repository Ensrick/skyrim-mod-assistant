# VisibleEquipment (working name)

First-party SKSE plugin for Skyrim SE 1.7.104 that keeps every carried weapon
visible on the body and enforces the carry rules of issue #36: a weapon can only
be picked up when a body slot is free, up to two daggers may be packed and
hidden, quest items are not exempt, and a staff is either in a hand or in
long-term storage. It replaces Immersive Equipment Displays, which cannot be
rebuilt for this runtime (`docs/IED-REBUILD-FEASIBILITY-2026-09-10.md`).

The name is the user's call and has not been chosen; `NAME_TBD` in
`CMakeLists.txt` lists every place a rename touches.

Design, milestones and the evidence behind each decision:
`docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md`. Tracking issue: #269
(#272 was closed as its duplicate). A first-party phase 0-2 tree also exists
at `skyrim-tools-source/EnsrickEquipmentDisplay`; the spec's section 0.1 says
how the two are meant to merge.

## Status: M0 scaffold, 0.0.1

Loads, logs, counts equip and container-change events, attaches nothing. Not
installed in the profile and not run in game. Build receipt:
`records/source-builds/visible-equipment-0.0.1.json`.

## Build

```
pwsh mods/visible-equipment/build.ps1 `
  -CommonLibRoot C:/Users/danjo/source/repos/skyrim-tools-source/CommonLibSSE-NG-6.7.1 `
  -VcpkgRoot C:/Users/danjo/source/repos/vcpkg `
  -Cmake "C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe" `
  -BuildDirectory records-work/visible-equipment-0.0.1-build/build1
```

Needs Visual Studio 2022 (MSVC 14.44), a CommonLibSSE-NG checkout at the
reviewed revision `70c1acd` (6.7.1) and vcpkg at the manifest baseline. The
script configures, builds Release, runs CTest, and writes a deterministic zip
next to the build. `.github/workflows/visible-equipment.yml` runs the same
script on a hosted runner with both dependencies checked out at their pins.

## Layout

- `src/main.cpp`: SKSE entry point, log, ini, the two no-op sinks.
- `src/SlotRules.h`: the #36 rules as pure C++ with no game types.
- `tests/SlotRulesTests.cpp`: CTest `slot_rules`, one assertion per rule clause.
- `VisibleEquipment.ini`: configuration surface; M0 reads `[Log] Level` only.

## Diagnostics

Log: `Documents\My Games\Skyrim Special Edition\SKSE\VisibleEquipment.log`.
There is no message box path in this module. Failures are log lines.

## Licence

MIT (repository `LICENSE`). Links CommonLibSSE-NG (GPL-3.0-or-later with the
modding and linking exceptions in its `EXCEPTIONS.md`), spdlog and fmt (MIT);
their notices ship in the package.
