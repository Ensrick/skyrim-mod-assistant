# Fresh-character world-entry failure, September 9

Status: **open; failed world-entry acceptance**, [#263](https://github.com/Ensrick/skyrim-mod-assistant/issues/263), found during #262 controls.

The private, muted `Astra Crash262 Fresh` profile was created from current
Default with an empty local saves directory. PID26696 began at20:37:59 CDT;
New Game was selected and confirmed, character creation completed, and Skyrim
Unbound's MCM `Main > Begin Your Adventure` was selected at20:41:49. No imported
save, character migration, vendor modification, or additional mod was used.

The game remained in `SkyrimUnboundRoom01`, confirmed by the20:42:33 quicksave
header, **not** inferred from process survival or a menu callback.

Papyrus evidence:

-20:41:53: `SkyrimUnboundModuleLocations.SelectLocation`, line1325, calls
  `Find()` on None. Supplied source at that line uses
  `location2 = locTypeList.Find(locationForm) + 1`.
-20:41:55: `TeleportPlayer`, lines1506/1513, cannot move the starting marker
  or player to a None destination; line1514 then calls `GetParentCell()` on None.
-The script nevertheless continues; the quicksave remains in the starting room.

This does not yet establish why location selection produced invalid state.
Check effective PEX/source provenance, initialization, location-list record
winners and location selection inputs. Do not merely suppress the errors or
teleport through the console and call the normal start fixed. The script needs
to preserve a recoverable start when no valid destination exists.

Current Default raw SHA256 before the run:

-modlist.txt: `18f9973e596e94d052b735cd083bf0b138a1558bbc8c31822d4844b1cb3fb0fa`
-plugins.txt: `bafeacc3ed939e6af8b5cf267f0ee0073ff52ed29e419db1f0108680b9904542`

Plugin and currency admission both accepted the new quicksave. Its hash is
`20271824aa6436b8ccace93918423e9d79b2a53d91e659d26ba65e12232abb19`.
It loaded in-session successfully at20:44:36.713, with currency admission4
at20:44:36.841 (ledger198). This is a save/load control, not world-entry success
or recovery of Adventurer3. At20:45:45.355 the game was still unpaused and
responding, 68.642 seconds after load. Normal in-game Quit to Desktop was
confirmed at20:46:50; controller exit0 followed at20:46:52.887. No fresh crash
report appeared, no Skyrim/MO2 processes or pending MenuPilot batch remained.
No cold-restart or world/combat soak success is claimed for this run.

Private logs: `records-work/crash262-current-20260909/fresh-control/` contains
LaunchProbe, MenuPilot, SKSE, currency and Papyrus logs. Default lists were
unchanged byte-for-byte after the run; ModOrganizer.ini was restored to
`7c5fb7fb717a6414a744d9a22e0c29839da7bb46d43228ed6f8fc0f843c42fdd`.
All38 ordinary ESS files remain and the original Adventurer3 input hash remains
`ed8255cd464f8e17ba19aad5f2154549d9bff51ccc5fb8165473fd26fb1ef8f9`.

Acceptance requires a genuinely new character, valid normal MCM destination
selection, successful world entry, no matching selection/teleport errors, and
save/reload at that destination. Exercise both random and explicit choices.
Publish any necessary original patch separately; preserve vendor inputs.

## Static candidate discovered after the run (not yet causal proof)

The supplied `SkyrimUnboundModuleLocations.psc` has a specific invalid-pool path:

-`AfterLoadingAddons`, lines322-325, adds `Hold_Other` to `HoldLists`.
-`SelectLocation`, lines1106-1110, when jail starts are eligible, adds **every
  suitable hold** to both random destination pools, rather than intersecting
  that set with `HoldsWithJail`.
-Read-only record-cli inspection of the installed original plugin finds
  `Hold_Other` (`CD7C88:Skyrim Unbound.esp`) empty. The base `HoldLists` and
  `HoldsWithJail` each contain the same ten real holds; the script then adds
  Other only to HoldLists. Custom imported holds without a crime faction can
  create the same discrepancy (`ImportHold`, lines355-357).
-If random selection returns the empty Other list, it is non-None (bypassing
  the script's missing-location diagnostic) but not a jail hold or member of a
  location category. That predicts a None category and None teleport marker,
  consistent with this run's errors.

Still required: establish winning PEX provenance and relevant record overrides;
reproduce the exact Other-hold selection with bounded diagnostic logging. Do not
claim the run's selected FormID was observed: it was not logged. A prospective
fix should exclude non-jail holds from the jail candidate pool and keep the
  start recoverable when selection is invalid, not remove legitimate Other-area
  locations, choose the user's start, or silently complete the start in the room.

## Candidate implementation and first runtime test

`patches/unbound-jail-pool/prepare.py` now generates a pinned, separate source
patch. It filters jail candidates against HoldsWithJail while leaving ordinary
Other-area starts intact. Bounded log entries identify rejected holds and the
selected destination. No vendor file, persisted variable/property or Default
selection was changed. Author permissions allow credited bug-fix releases:
[Nexus permissions](https://www.nexusmods.com/skyrimspecialedition/mods/27962?tab=description).
The supplied source and installed PEX agree on the faulty branch. A same-
compiler baseline/candidate disassembly comparison changes only SelectLocation;
see the patch README for build/decompiler limitations and source requirements.

Candidate PID22824,20:59:03–21:05:04 CDT, private muted desktop:

-Loaded a copy of the genuine fresh character's **pre-start** Save1, not the
  already-failed start or Adventurer3. PostLoad success20:59:52.123.
-21:01:19: patch explicitly excluded Other (`44CD7C88`) from the jail pool.
-21:01:22: selected real Winterhold jail hold (`44451918`). This is newly
  observed diagnostic evidence; the earlier failed run's selected ID remains
  unknown and must not be retroactively claimed as measured.
-21:01:25.887: saved at WinterholdJail; load menu independently showed The Chill.
-Save3 SHA256 `90b0d0b2be8013396b9565d7d8ad7131eafd6b1926c82add39219eea88fbfabd`;
  plugin and currency admission pass. In-session reload success21:02:49.345;
  currency admission6 at21:02:49.480, ledger8.
-Unpaused responsive ping21:04:05.979, **76.634 seconds after successful load**.
-Normal in-game Quit to Desktop21:05:02; controller exit0 at21:05:04.672.
  No fresh crash file, game/MO2 process or pending MenuPilot batch afterward.
  Private evidence: `records-work/unbound263/runtime-jail/`.

The candidate is **test-only**, source/test profiles `Astra Unbound263 Source`
and `Astra Unbound263 Test`; Default does not enable it. Both Default list hashes
and ModOrganizer.ini were restored/unchanged relative to this run's before-image.
Claude's intervening CLLF installation was present but its plugins inactive;
do not claim the raw lists are identical to the earlier20:37 control.

Five offline transform/policy tests pass, but do not replace runtime evidence.
Remaining: explicit non-jail start, cold reload, stronger deterministic invalid-
selection regression and safe invalid-selection recovery before final adoption.
This narrow progress does not close #262 or the overall crash-recovery goal.

## September10 explicit current-Default control

The vendor (unpatched) explicit City > Solitude path was exercised with a
genuinely new current-Default character. It reached Tamriel near the Solitude
waterfront, saved, reloaded, cold-loaded through Continue, and saved/reloaded
again without the invalid-destination errors. See
[the bounded report](CURRENT_DEFAULT_WORLD_TEST_2026-09-10.md). This is NOT a
test of the random jail branch or generic invalid-start recovery, so #263
remains open and the candidate remains disabled in Default.

Fable5.1 source review identified the required recovery boundary: validate before
QuestScript.PrepareForStart advances stage20, and have all callers honor
failure. A bare return inside TeleportPlayer is too late after stage90/autosave
and disabled controls. Proposed cross-script changes are not applied yet:
review addon-supplied destinations, restore fade/hotkey/menu registration on
every failure path, reset stale FinalTeleportMarker, and retain user's choices.
Do not silently choose another destination or treat same-header readers as
independent native verification. The exact old random selection remains unknown.
