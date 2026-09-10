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
