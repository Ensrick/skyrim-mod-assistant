# Current-Default world-entry and save/load controls, September 10

**Narrow acceptance passed; overall #262 remains open.** These runs use current
Default's installed content, not the Unbound jail-pool test override used by
earlier controls. No new mod, plugin activation, campaign migration or vendor
edit was made. Installed SKSE remains the clean default-on member guard
e843ba3 / DLL `4E3F618B6A413B6EA3C38E238EBC607E056EEBFC34ED72073DD46BEEA7BD7184`.
Experimental native load admission remains unlinked and uninstalled.

## Exact scope and observations

Both profiles were cloned/refreshed from Default and used private local saves,
local INIs with master volume zero, and the never-focused QuietWorker desktop.
MenuPilot drove the game's own normal menus; no Windows keyboard/cursor input,
console teleport, save cleaning, or original-campaign write was used.

| Run | Observed result (CDT) |
| --- | --- |
| Fresh `Astra Default World 20260910`, game21392/controller23172 | New Game confirmed02:59:46; normal character creation finished03:00:48. MCM Starting Location > City > Solitude selected and committed03:04:18; Begin Your Adventure03:05:00. |
| World entry | Save3 at03:05:15 has Tamriel rather than SkyrimUnboundRoom01; embedded screenshot shows the Solitude waterfront. This is an explicit non-jail start, not random-start acceptance. |
| In-session load/save | Save3 selected by file number3, confirmed in normal Journal Load; PostLoad success03:06:02.695, currency admission4 at03:06:03.008, ledger694. New manual Save4 at03:06:41. |
| F5/F9 | Quicksave03:07:06; exact co-save gate passed. F9 PostLoad success03:07:24.478. Normal Quit to Desktop03:07:41; controller exit0 at03:07:43.823. |
| Cold `Astra Default World Cold 20260910`, game33032/controller32104 | Only a copy of new Save4 supplied. Its plugin and currency gates passed. Normal Continue confirmed03:10:02; PostLoad success03:10:16.082, currency admission3 at03:10:17.227. |
| Cold-session save/reload | New Save5 at03:11:38, currency checkpoint admitted; normal Journal Load file5, PostLoad success03:12:14.822; currency admission6 at03:12:14.989, ledger694. |
| Sustained observation | Responsive unpaused ping03:17:38.910, 324.088 seconds after that reload; HUD reported100% health03:14:53.771. Normal Quit to Desktop03:17:43; controller exit0 at03:17:45.593. Not combat/travel certification. |

Both logs confirm both member-guard hooks installed/default enabled, with **zero
rejected accesses**. No new crash report was created in the isolated crash
directory. No matching Unbound SelectLocation/TeleportPlayer None-destination
error was observed. This does not imply every warning or mod is healthy.

The Quit helper's last input batch times out because the game exits during its
callback. Actual normal-quit confirmation, process disappearance, controller
exit0, and wrapper restoration establish cleanup; that timeout is not a crash.

## Test-driver limitation discovered, not hidden

Tracked separately in [#267](https://github.com/Ensrick/skyrim-mod-assistant/issues/267).

`input.tap` reports dispatch success, not movement. A read-only candidate player
layout probe sampled position before/after a two-second Forward dispatch in the
cold session. Both samples returned `[-65133.664, 96466.03, -13887.999]`, cell
`000092BC`, world`0000003C`, player form`00000014`; identity and repeated-read
checks passed. The source's position is `OBJ_REFR+0x14`, hence player+0x54,
**not** player+0x40. Address-library ID403521 resolves singleton RVA3230778;
observed player vtable RVA19296C0. Native field/semantic confirmation is still
required before promoting this probe to an authoritative test tool.

No meaningful travel is proved. The cause of the unchanged reading remains
unresolved: input delivery/continuous-hold behavior, collision, or observation
layout must be distinguished. Do not call a sent button event successful
gameplay, or conclude that the user's physical movement controls are broken.

The screenshot's low waterfront viewpoint initially suggested a water arrival.
That is only a visual hypothesis. Candidate swimming=false and cell water
height=FLT_MAX are not independent proof; the latter may be a sentinel. Check
the actual marker, cell/world water data and native actor fields before moving
the start marker or changing the city overhaul.

## Remaining log triage / acceptance

- #263 random jail-pool and invalid-start recovery remain test-only/open. The
  explicit Solitude path does not repair or test the invalid random branch.
- WeaponRackTriggerSCRIPT reference`2E009307` reports missing WRackActivator on
  cell attach03:05:15. Resolve its originating/winning plugin and linked refs;
  no delete, disable or replacement was applied.
- FNIS.GetFlags native static binding warning needs effective script/native
  provenance review. Nearby Campfire optional-mod warning text is not proof
  that this separate binding warning is harmless. Do not install FNIS merely
  to silence a log line.
- Other missing-file probes occur in optional compatibility detection, including
  Lucien/Campfire. They do not by themselves authorize installing those mods.
- Original Adventurer3 still lacks the currency checkpoint and retains removed
  content. Its demonstrated crash repair is separate from campaign admission.
- Native normal-load admission lifecycle/refusal remains unfinished; broader
  verified movement, travel, combat and multi-cell testing remain required.

## Preserved evidence and identities

Private logs and embedded preview images:
`records-work/current-default-world-20260910/`, with separate per-profile log
folders. Original saves were not copied into either test profile. Exact original
ESS/co-save hashes were checked before/after both runs and remain unchanged.
No diagnostic dump was requested or duplicated. Logger settings were restored
byte-for-byte to SHA256
`0A38C67861A8BFAFD6640EB8D05398060ECF170621EB7FE2DF368AEB9A5C58DB`.

Default lists checked unchanged before/after each launch:

- modlist: `A19834B77608342C63123E5ABA2BBCA9A9A5FC200BBD69AB06EE1E49F8EA71BE`
- plugins: `AFD114200F6D5B4E6EE6A1FD7E7A8934FD2F76B64BE40D581CE3533E233A5F9B`
- loadorder: `212EC959768726B1F8B6234470AE434A7E4BEC393094565F1AEE0468E59138A2`

New test ESS SHA256:

- Save3: `20C0ED9B90F51191CE9D9D0DB8A0AEA75A5C9EAB97263BF0624C6A58582704F9`
- Save4 and its cold copy: `FE9AB3997E5A091A7E2B621FE52437EC34FD53B92CEBAD183EED46A2A13DC0BA`
- Quicksave: `1CACBB90FF68BFCAD3ACB8718F113ABEBE02625EBC8FB46066DB2BFBCF615A2E`
- Cold Save5: `77E70FD28E818B0C762CDF9CC88044072F3B456EF6A279C4DE5C311883126425`

Actual Fable5.1 CLI session9bfac0cd-5752-47d3-b14c-528d1643a04d completed two
bounded read-only reviews (Unbound recovery and player observation). Parent
checked the recommendations rather than applying them blindly. In particular,
two readers derived from the same CommonLib header are **not independent ABI
validation**, and the existing ControlMap script uses pinned native RVAs rather
than resolving library IDs itself. No Fable job or game/controller remains.
