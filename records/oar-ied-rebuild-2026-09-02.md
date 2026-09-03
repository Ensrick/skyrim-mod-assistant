# Open Animation Replacer and Immersive Equipment Displays: update sweep, licence, rebuild attempt

Audit date: 2026-09-02

Runtime: Skyrim Special Edition `1.7.104.0` / SKSE `2.3.1` / Address Library
format 5

Trackers: [#140](https://github.com/Ensrick/skyrim-mod-assistant/issues/140)
(OAR passes SKSE gate then hangs at load),
[#94](https://github.com/Ensrick/skyrim-mod-assistant/issues/94) (IED blocked on
deleted framework; overlay was unsafe)

Prior art: `records/source-builds/ensrick-light-placer.json` and
`records/cloak-framework-rebuild-2026-09-02.md` - the two worked rebuild-forward
precedents on this runtime.

Authorisation: user, 2026-09-02, *"That right now is a major priority"*, on the
two parked native mods; *"I also don't seem to have IED working"*.

Disposition: **OAR unparked on an author release and launch-verified. IED
remains blocked - the blocker in #94 was re-tested from scratch and it still
holds; nothing was installed for it.**

---

## Verdict in one table

| Mod | Author update we missed? | Rebuild needed? | Distribution class | Verdict |
|---|---|---|---|---|
| [Open Animation Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/92109) 3.2.0 -> **3.2.1** (Nexus 92109, Ersh) | **Yes - 3.2.1, uploaded 2026-08-31, changelog "Updated to support runtime 1.7.99+"** | **No.** The author already did it: 3.2.1 repins CommonLibSSE-NG past the format-5 commit | **none - vendor row.** Unmodified third-party release, so no `distribution:` field per the `docs/PATCH_INTENTS.md` eligibility ruling | **Installed, enabled, launch PASS** |
| [Immersive Equipment Displays](https://www.nexusmods.com/skyrimspecialedition/mods/62001) 1.7.4 (Nexus 62001, SlavicPotato) | **No.** Newest file is still 1.7.4, 2023-12-10. 16 unreleased commits sit on `master` (to 2026-03-05) but cannot be built | **Yes, and it is still impossible** - 51 reverse-engineered `ext/` headers have no public copy anywhere, Software Heritage included | n/a - nothing was produced | **BLOCKED, unchanged. Stays parked** |

Single recommendation: **OAR is available now. IED needs an author release; do
not spend more engineering on it** - the missing input is 51 headers of the
author's private reverse-engineering work, not a build problem we can solve.

---

## What is finished, and what needs the user's decision

**Finished, nothing to decide.**

- [Open Animation Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/92109)
  3.2.1 installed, enabled at modlist line 240, launch-verified. It is a mod
  already in the build being fixed, which is the exception the user named
  ("Get any requisite mods you need to fix the issues with the mods we currently
  have"), so the 2026-09-02 no-new-vendor-mods constraint does not bite here.
- [Immersive Equipment Displays](https://www.nexusmods.com/skyrimspecialedition/mods/62001)
  investigated to a dead end. **Nothing was installed and no new vendor
  dependency was needed**, so nothing was staged for approval either.
- #140 and #94 commented with the evidence. Neither was closed.

**Needs the user's decision - three items, none urgent, none blocking play.**

1. **Does he want gear display at all?** IED cannot be fixed by us (section 2).
   The only DLL-free route is
   [AllGUD](https://www.nexusmods.com/skyrimspecialedition/mods/28833) - a **new
   vendor mod**, therefore *suggested, not installed*, per the 2026-09-02
   constraint. It is a real install project (an xEdit mesh-generation pass over
   the whole installed gear set) and was last updated 2020-03-22, so it wants
   its own scoped issue rather than a quiet adoption. Meanwhile
   [Simple Dual Sheath](https://www.nexusmods.com/skyrimspecialedition/mods/50049)
   1.5.9 is already enabled and verified and covers the visible part.
2. **Should we ask SlavicPotato to publish `ext/`?** That is the one cheap move
   left on #94 and it is an outward contact, so it is the user's to send, not
   mine. IED itself is already MIT; only the private build framework is in
   question.
3. **Close or keep #140?** It is fixed and launch-verified, but I was told to
   close nothing. It is his call.

**Explicitly NOT claimed:** that any animation replacer works in game. OAR's own
log reports `1 OAR directories` - the plugin's own, because no replacer mod is
installed. The framework loads; per-animation behaviour is untested, and #198
(block animation) is a separate retest owned by `own-patch-fixes`.

---

## Every DLL touched this pass: PE stamp and `load_v5`

The gate's PE-stamp reject window was corrected today to end **2026-08-21**
(commit `c3da884`, "Fix the SKSE gate reject window: 2025-05-26 -> 2026-08-21
(#197)", 22:35:31) after Smart Talk passed the old window and aborted the SKSE
load. Every row below was produced **after** that fix, by the corrected gate.

`load_v5` is read from the DLL's own string table (the C++ symbol names for
`REL::IDDB::load_v5` / `header_v5_t`), which is the receipt the flags cannot
give: a plugin can declare the V5 bit without having the reader, which is
exactly what the withdrawn IED overlay did.

| DLL | version | PE stamp | UTC | viEx / V5 bit | compatibleVersions | **`load_v5` in binary** | gate verdict |
|---|---|---|---|---|---|---|---|
| `OpenAnimationReplacer.dll` (parked 3.2.0) | 3.2.0.0 | 1785103405 | 2026-07-26 22:03:25 | 1 / **NO** | 1.6.1170.0 | **absent** | FAIL |
| **`OpenAnimationReplacer.dll` (installed 3.2.1)** | **3.2.1.0** | **1788193253** | **2026-08-31 16:20:53** | **3 / YES** | **1.7.99.0** | **present** | **PASS** |
| `ImmersiveEquipmentDisplays.dll` (parked 1.7.4, untouched) | 0.1.112.4 | 1702213004 | 2023-12-10 12:56:44 | 0 / **NO** | 1.6.318.0, 1.6.323.0 | **absent** | FAIL |

Only one DLL entered the build: OAR 3.2.1. The other two rows are diagnostic
reads of binaries that were already on disk; neither was modified, and the IED
row is the reason it stays parked.

---

## The discriminator, stated once

`audit/skse_version_data.py` PASS is necessary and never sufficient. What
separates a DLL that loads from one that kills the load on 1.7.104 is whether
its CommonLib was built after **`alandtse/CommonLibSSE-NG` `7b47c5a8f`,
2026-08-21T08:25:46Z, "feat(rel): support AE 1.7.99 address library format 5
(#299)"** - the commit that added `REL::IDDB::load_v5`. (The repository is the
one formerly named `alandtse/CommonLibVR`; GitHub redirects the old path, so
both names appear across our records and refer to the same commit.) Before it, CommonLib's
`IDDB::load_file` reads the `versionlib-1-7-104-0.bin` header, sees format 5,
and bails.

That is checkable in the shipped binary without building anything: the exported
C++ symbol names for `REL::IDDB::load_v5` and `header_v5_t` sit in the DLL's
string table when the reader is present, and are absent when it is not. Every
DLL in this record was checked that way, not inferred from the PE stamp.

---

## 1. [Open Animation Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/92109) (Nexus 92109, Ersh)

### 1.1 Diagnosis of the #140 failure - it was never OAR's own code

#140 recorded the symptom (SKSE logs `loading plugin "OpenAnimationReplacer"`,
never returns, a popup appears, and the 14 plugins behind it never load) but
attributed it to "fails inside its own load". The mechanism is narrower, and it
is the [Light Placer](https://www.nexusmods.com/skyrimspecialedition/mods/127557) failure exactly.

`OpenAnimationReplacer.dll` 3.2.0, PE stamp `1785103405` = 2026-07-26
22:03:25Z, pins `extern/CommonLibSSE` to
**`alandtse/CommonLibVR@539d4ce50` (2025-04-12)** - sixteen months before the
format-5 commit. Confirmed against the binaries themselves:

| symbol string present in the DLL | 3.2.0 (parked) | 3.2.1 (installed) |
|---|---|---|
| `Unsupported address library format: {}` | yes | yes |
| `bool __cdecl REL::IDDB::load_v2(...)` | no (inlined) | yes |
| **`bool __cdecl REL::IDDB::load_v5(..., class REL::IDDB::header_v5_t, ...)`** | **absent** | **present** |
| `REL::IDDB::istream_t::istream_t(...)` | absent | present |
| imports `MessageBoxW` | yes | yes |

So 3.2.0 reaches `IDDB::load_file`, finds the format-5 versionlib, has no v5
reader, formats `Unsupported address library format: 5`, and raises the modal
its `MessageBoxW` import provides. On an interactive launch that modal is the
"popup" #140 describes, and the SKSE plugin loop blocks behind it forever -
which is why the 14 later plugins never load and why no crash log is written.
Nothing hangs in the mathematical sense; the process is waiting on a message box.

The gate now catches this on its own. Re-run today against the parked 3.2.0
binary:

```
  PE stamp: 1785103405 (2026-07-26 22:03:25Z)
  name='OpenAnimationReplacer' pluginVersion=50462720 (3.2.0.0) author='Ersh'
  versionIndependence=1 versionIndependenceEx=1 (V5 bit=NO)
  compatibleVersions=['1.6.1170.0'] raw=['0x1064920']
  VERDICT: FAIL: incompatible with current version of the game
           [addrlib-v5 flag missing AND stamp inside reject window]
```

#140 recorded a PASS for this same file. The binary did not change - the gate
did: the 2026-09-02 fix for #197 (`CHANGELOG.md`, "Fix the SKSE gate that let
Smart Talk through", commit `c3da884`, 22:35:31, four minutes before the gate
runs below) raised the PE-stamp reject window's upper bound from
2025-05-26 to **2026-08-21**, the format-5 date. OAR 3.2.0's 2026-07-26 stamp
sits inside the corrected window and outside the old one, so it was always going
to fail and the old gate could not see it.

### 1.2 The update sweep found the fix already shipped

Method: Nexus v1 API, full file list (every category, not just `MAIN`) plus
`changelogs.json`, plus the GitHub API over `ersh1/OpenAnimationReplacer`.

Nexus mod record: `version 3.2.1`, `updated_timestamp` = **2026-08-31T16:32:18Z**,
`status published`. 34 files on the page; the only `MAIN` one is new:

| file_id | category | version | uploaded (UTC) | size KB |
|---|---|---|---|---|
| 781784 | OLD_VERSION | 3.2.0 | 2026-07-26T22:20:38Z | 8064 (**what was installed**) |
| **798222** | **MAIN** | **3.2.1** | **2026-08-31T16:32:18Z** | **8094** |

`changelogs.json` for 3.2.1, verbatim, first line first:

> `Updated to support runtime 1.7.99+`
> `(API) Updated the UI API.`
> `(API) UI: Added OpenMenu(), CloseMenu(), ToggleMenu(), IsMenuOpen(), SetSuppressMenuHotkey()`

The repository says the same thing in code. `ersh1/OpenAnimationReplacer` `main`
is at `f4e7688` (2026-08-31T16:02:46Z, clang-format only); the substantive
commit is **`4d8c0f1b0` "Version 3.2.1" (2026-08-31T18:01:34+02:00)**, and its
diff to `.gitmodules` is the whole story:

```
 [submodule "extern/CommonLibSSE"]
 	path = extern/CommonLibSSE
-	url = https://github.com/alandtse/CommonLibVR.git
-	branch = ng
+	url = https://github.com/alandtse/CommonLibSSE-NG.git
```

with the pointer moving `539d4ce50` (2025-04-12) -> **`fd60ebdfe`
(2026-08-29T05:49:23Z)**, eight days past the format-5 commit.

**This is the author's own rebuild-forward, published the day before the user
asked for one.** Building our own fork would have produced a strictly worse
artifact: the same fix, minus the API additions, plus a fork to maintain.

### 1.3 Licence and distribution class

`COPYING` is GPL-3.0 with `EXCEPTIONS` carrying the standard SKSE modding
exception (linking permission for Modding Libraries, corresponding source
required). That would have governed a fork.

It does not apply here, because **nothing was forked**. Under the eligibility
ruling in `docs/PATCH_INTENTS.md` ("An unmodified third-party release, GPL or
not [...] is a vendor row and a required download from its own source"), OAR
3.2.1 carries **no `distribution:` classification at all**. Its ledger row
records source, file id and archive SHA-256, like any Nexus mod.

The two files a previous attempt staged under
`records/source-builds/ensrick-open-animation-replacer/`
(`OpenAnimationReplacer-COPYING.txt`, `-EXCEPTIONS.txt`) are the licence capture
for a fork that no longer needs to exist. They are untracked and were left in
place. There is no `records/source-builds/*.json` for OAR because **no build was
performed**.

### 1.4 Install and launch

Installed with `py -3 audit/install_mod.py 92109 "Open Animation Replacer"
--file 798222 --replace` under claim `claude/oar-ied-rebuild`, transaction
`20260903T033733283Z-de1db0b97e86`. Archive `92109-798222.7z`, 8288609 bytes,
sha256 `970cb6c34045ee6a5ba7a5f0c598a8e398d0973cc81a9a6ee5dd303329907de8`. It
replaces 3.2.0 in place, so the mod keeps modlist line 240 and is now `+`.
Active plugin count is unchanged at 243 - OAR ships a DLL and a PDB, no ESP.
Modlist backed up to `profiles/Default/modlist.txt.bak.v20260902-pre-oar321`.

Gate on the installed binary:

```
  PE stamp: 1788193253 (2026-08-31 16:20:53Z)
  name='OpenAnimationReplacer' pluginVersion=50462736 (3.2.1.0) author='Ersh'
  versionIndependence=1 versionIndependenceEx=3 (V5 bit=YES)
  compatibleVersions=['1.7.99.0'] raw=['0x1070630']
  VERDICT: PASS (version independent)
```

PE stamp 2026-08-31, ten days after the format-5 commit; `versionIndependenceEx`
1 -> 3 (the AddressLibraryV5 bit); `compatibleVersions` 1.6.1170.0 -> 1.7.99.0.
And, the receipt the flags cannot give, `REL::IDDB::load_v5` is in the binary.

**Launch: PASS** - `records/launch-verify-20260902-223914.md`, its own run, not
shared with anything else. Main menu **37.4 s**, save loaded **46.1 s**, 243
active plugins, **36 SKSE plugins checked, 0 refused**.

`skse64.log`:

```
checking plugin OpenAnimationReplacer.dll
loading plugin "OpenAnimationReplacer"
automation silent UI: redirected 1 modal import(s) for OpenAnimationReplacer.dll
plugin OpenAnimationReplacer.dll (00000001 OpenAnimationReplacer 03020010) loaded correctly (handle 16)
```

`OpenAnimationReplacer.log` - the file #140 never got to write:

```
[22:38:25.689] OpenAnimationReplacer v3-2-1-0
[22:38:25.690] Reading .ini... ...ini not found, creating a new one ...success
[22:38:26.029] Initializing condition and function factories...
[22:38:26.029] Condition and function factories initialized.
[22:38:52.298] Directory cache complete: 1 OAR directories, 0 legacy directories,
               164 animation hashes (3880ms)
[22:39:01.153] Finished parsing data\meshes for replacer mods...  Total: 15ms
```

No `Unsupported address library format` line. The one warning, `Failed to
dispatch message to MergeMapper`, is the same benign line five other plugins log
this session (MergeMapper is not installed).

Two honest caveats. The `automation silent UI` line means the harness redirected
the `MessageBoxW` import for this DLL, as it does for every plugin; that changed
nothing here, because the plugin never took the failure path. And the run
covered load, ini creation, factory init, the 164-hash directory cache and a
save load. **Correction, 2026-09-03:** an earlier version of this record read
that line as "no replacer animation was played, because none is installed
(`1 OAR directories`, the plugin's own)". That was wrong. The one OAR directory
is real payload - `Pandora Output - Ensrick`'s XPMSE FNIS-AA conversion at
`meshes/actors/character/animations/OpenAnimationReplacer/XPMSE`, **30 sub-mod
directories and exactly 164 `.hkx`**, which is precisely the `164 animation
hashes` the log reports. So OAR loaded, parsed and hashed a genuine replacer set.
What remains untested is whether any of those animations *plays* in game; the
launch never left the load path.

### 1.5 What this unblocks

Directly: OAR itself, and any OAR-format animation replacer the user adds.

**#198 (block animation): OAR being live rules OAR out rather than implicating
it.** `own-patch-fixes` reached that conclusion first; I re-derived it from the
files rather than accepting it, and two of its three legs hold:

- **Holds.** The whole OAR payload is Pandora's XPMSE conversion: 30 sub-mods,
  164 `.hkx`, and the group names are equip/unequip, bow, magic, shout, sprint.
  **There is no block group.** The only block-named file in the entire Pandora
  output is `xpe_sprint_1/shd_blockbashsprint.hkx` - shield *bash while
  sprinting*, gated on `graphVariable FNISaa_sprint == 1`.
- **Holds.** No `mt_behavior.hkx`, `1hm_behavior.hkx` or `shield.hkx` was
  generated; the only regenerated per-subgraph behaviours are `magicbehavior.hkx`
  and `magicmountedbehavior.hkx`.
- **Did NOT hold.** The claim that Pandora shipped no `0_master.hkx` was wrong.
  **`0_Master.hkx` is present and regenerated in both skeletons** -
  `meshes/actors/character/Behaviors/0_Master.hkx` (585,136 bytes) and
  `meshes/actors/character/_1stperson/Behaviors/0_Master.hkx` (472,688 bytes).
  A case-sensitive search for `0_master.hkx` misses it. `own-patch-fixes` had
  independently caught the case-sensitivity miss and corrected it in commit
  `2642391` before my flag arrived; what my flag added was the consequence, that
  a regenerated master left the hypothesis alive.

**Resolved the same night, by measurement.** `own-patch-fixes` extracted vanilla
`0_master.hkx` from `Skyrim - Animations.bsa` (read-only, into a scratch dir
outside `mods\`) and diffed the string tables against Pandora's:

| | vanilla | Pandora | delta |
|---|---:|---:|---:|
| bytes | 580,896 | 585,136 | +4,240 |
| distinct strings | 2,891 | 2,949 | +58 |
| **block/bash strings** | **83** | **83** | **0** |

Zero block or bash strings added or removed. The 61 additions are entirely
SkyParkour states and variables, XPMSE/FNIS-AA variables plus
`FNIS_XPMSE_Behavior.hkx`, and Pandora's own markers.

The honest limit, which that agent stated itself: a string diff proves the
regeneration adds and drops no block state, event, variable or animation
reference, but **cannot see re-pointed state IDs, transition priorities or blend
times**, which are node data rather than names. So the master is **narrowed, not
formally excluded**.

The useful consequence is that my two candidates collapse into one: everything
Pandora put in that master belongs to SkyParkour or XPMSE, so if the master is
implicated at all it is implicated *through SkyParkour*. The row survives as a
two-step ladder rather than a single toggle - disable SkyParkour's runtime hooks
first, and only if that fails, re-run Pandora with SkyParkour deselected to get
a master without the injected states. Simply disabling `Pandora Output - Ensrick`
is **not** the test: it also strips the 22 `FNISaa_*` variables XPMSE needs.
Detail in `records/block-animation-198-2026-09-02.md` section 5a.

[#148](https://github.com/Ensrick/skyrim-mod-assistant/issues/148)
(XPMSE weapon-style Papyrus calls aborting against Pandora's `fnis_aa` stub) now
has a live route - OAR conditional animations are the modern replacement for
FNIS alternate-animation draw/sheathe styles - but **that is a route, not a fix,
and #148 is not addressed by this change.** Note the coupling
`own-patch-fixes` flagged: `xpe_sprint_1` is the one group whose OAR condition
reads `FNISaa_sprint` through the `fnis_aa` API, so if sprint-block is the only
failing row in that matrix it lands in #148's territory.

---

## 2. [Immersive Equipment Displays](https://www.nexusmods.com/skyrimspecialedition/mods/62001) (Nexus 62001, SlavicPotato)

### 2.1 Update sweep: no author release in two years and nine months

Nexus mod record: `version 1.7.4`, `updated_timestamp` **2023-12-10T13:02:53Z**.
Every category listed; 40 files, and the two newest are the only `MAIN` ones:

| file_id | category | version | uploaded (UTC) | variant |
|---|---|---|---|---|
| 450464 | MAIN | 1.7.4 | 2023-12-10T13:02:23Z | for 1.5.39 - 1.6.353 |
| **450465** | **MAIN** | **1.7.4** | **2023-12-10T13:02:53Z** | for 1.6.629 and newer (**installed**) |

No beta, no optional, no update file, no hotfix. Newest changelog entry is
`1.7.4 -> ["Updated for game version 1.6.629", ...]`.

`github.com/SlavicPotato/ied-dev` is a different story, and it is worth being
precise about, because it is why the block is frustrating rather than final.
`master` is at **`d8e9d33` (2026-03-05T21:57:42+01:00)** - the author is still
working. **16 commits** post-date the 1.7.4 upload (`git rev-list --count
--since=2023-12-10T13:02:53Z origin/master`), including real features: NPC mount
tracking, conditional variable fixes, an inventory mode for variables. There are **no releases, no GitHub Actions workflows and no
submodules** on the repo. Nothing there is buildable by anyone but the author.

### 2.2 The blocker, re-tested from scratch, still holds

`ImmersiveEquipmentDisplays.vcxproj` expects a **sibling directory**,
`$(SolutionDir)..\sse-build-resources\`, on the include path of every
configuration, and force-includes `ext/ICommon.h`. It is not a submodule, so the
project does not even record which revision it wants.

`SlavicPotato/sse-build-resources` is **404**. What is public:

| source | state | `ext/*.h` |
|---|---|---|
| `clayne/sse-build-resources` | last push **2022-02-12**, the only GitHub copy | 52 |
| `rethesda/`, `renngar/` (Software Heritage only) | identical snapshot `56549d7a2617` to clayne | 52 |
| `pcbeard/` (Software Heritage only) | snapshot `22388b6f0a85` -> revision `3f24c03ce`, **2021-02-21** - *older* | fewer |
| **`Ensrick/sse-build-resources`** `ensrick/1.7.99-format5` | our own fork of clayne, +6 headers | **58** |

The current `ied-dev` tree `#include`s **74** distinct `ext/*.h`. Against our
own already-extended fork, **51 are missing** - which independently reproduces
the number in #94 from a clean count:

- **37 reverse-engineered game/engine headers**: `TES.h`, `Sky.h`, `Clouds.h`,
  `TESClimate.h`, `ShadowSceneNode.h`, `ShaderReferenceEffect.h`,
  `ImageSpaceManager.h`, `BSLight.h`, `BGSLensFlare.h`,
  `BSShaderPropertyLightData.h`, `BSAnimationGraphManager.h`,
  `BSAnimationUpdateData.h`, `WeaponAnimationGraphManagerHolder.h`,
  `hkaSkeleton.h`, `InteriorData.h`, `RefrInteraction.h`, `Calendar.h`,
  `ConcreteFormFactory.h`, `GarbageCollector.h`, `D3D11Backup.h`,
  `LightCreateParams.h`, `MemoryValidation.h`, `BackgroundProcessThread.h`,
  `BSThread.h`, `BSString.h`, `IDebugLog.h`, `ILUID.h`, `INIConfReader.h`,
  `IOTask.h`, `ISerializationBase.h`, `PluginInterfaceBase.h`,
  `PluginInterfaceSDS.h`, `SDSPlayerShieldOnBackSwitchEvent.h`,
  `SKSEMessagingEvents.h`, `SKSEMessagingHandler.h`,
  `SKSESerializationEventHandler.h`, `SKSESerializationEvents.h`
- **14 `stl_*.h` container/utility headers** the author's serialization and
  config layers are written against: `stl_flat_map.h`, `stl_flat_set.h`,
  `stl_fixed_string.h`, `stl_csr.h`, `stl_smart_pointer.h`, `stl_mutex.h`,
  `stl_queue.h`, `stl_error.h`, `stl_typeid.h`, `stl_comparison.h`,
  `stl_str_conv.h`, `stl_str_helpers.h`, `stl_allocator_mi.h`,
  `stl_boost_serialization_containers.h`

New evidence this pass, beyond what #94 had: **Software Heritage was searched
and it does not have the repository either.** `SlavicPotato/sse-build-resources`
was never archived (`NotFoundExc` on the origin), and all four archived forks
resolve to snapshots at or before 2022-02-12. A GitHub code/name search returns
only clayne. There is no copy left to find.

The first group is the hard one. Those are the author's own layouts for game
structures at specific runtime offsets. Reconstructing them means redoing the
reverse-engineering, and a field that is off by one produces memory corruption,
not a compile error. That is not work to attempt against a modlist the user is
playing.

### 2.3 Why the previous overlay attempt was unsafe, and why it stays refused

The withdrawn `IED 1.7.99 Compatibility Overlay` (sha256 `A5857D9F...A8A6`) set
`kVersionIndependentEx_AddressLibraryV5` on the 1.7.4 DLL. That bit is a
**declaration to SKSE's loader**, not an implementation. Setting it moves the
failure later and makes it worse:

1. SKSE's version gate stops refusing the plugin, so `SKSEPlugin_Load` runs.
2. Inside, IED's `ext/ISKSE.h` calls `CreateTrampolines`, which takes a slice of
   SKSE's shared 64 KB branch pool via `AllocateFromBranchPool` and wraps it in a
   `BranchTrampoline` with `SetBase`.
3. Its bundled `ext/versiondb.h` `Load()` calls `Load(2, ...)` and returns false
   on a format-5 file - so the load fails, *after* step 2.
4. SKSE calls `FreeLibrary` on the failed plugin
   (skse64 `PluginManager.cpp:204`). The static `BranchTrampoline`'s destructor
   runs `VirtualFree(m_base, 0, MEM_RELEASE)` on a slice **it does not own**.
   Windows page-rounds the address: a slice in the pool's first 4 KB page frees
   **SKSE's entire shared pool**.
5. SKSE then writes its own core hooks into freed memory and takes an access
   violation in `BranchTrampoline::Write5Branch_Internal` during `Hooks_*_Commit`,
   about a second in.

Full analysis and the field crash log:
`records/upstream-issues/sse-build-resources-trampoline-setbase-free.md`
(`crash-2026-08-25-20-36-52.log`, write AV at pool+0x6D0).

So the overlay does not trade "IED might not work" against "IED works". It
trades a clean refusal against **taking SKSE itself down and corrupting a
process the user is playing in**. It stays withdrawn; `ports/ied-1.7.99/README.md`
is already marked so.

Gate on the installed 1.7.4 DLL, for the record:

```
  PE stamp: 1702213004 (2023-12-10 12:56:44Z)
  name='ImmersiveEquipmentDisplays' pluginVersion=67332 (0.1.112.4) author='SlavicPotato'
  versionIndependence=5 versionIndependenceEx=0 (V5 bit=NO)
  compatibleVersions=['1.6.318.0', '1.6.323.0']
  VERDICT: FAIL: incompatible with current version of the game
```

`load_v5` absent; imports `MessageBoxA`. **IED stays disabled at modlist line
165, untouched by this pass. It has never been active in this build, and the
user's report that it is not working is correct.**

### 2.4 Licence, and what a rebuild would have been classed as

`LICENSE` is **MIT, Copyright (c) 2022 SlavicPotato** - so an Ensrick rebuild
would have been squarely permitted, and under `docs/PATCH_INTENTS.md` it would
have been **distributable** (our own bytes, MIT notice shipped, corresponding
source in a public fork), exactly like the [Light Placer](https://www.nexusmods.com/skyrimspecialedition/mods/127557) rebuild. The licence is
not the obstacle. The missing headers are.

### 2.5 The alternative, scoped - not installed

Nothing here half-works, so nothing was installed.

**Already in the build and verified.** [Simple Dual Sheath](https://www.nexusmods.com/skyrimspecialedition/mods/50049) 1.5.9
(Nexus 50049, enabled) covers the part of IED's job most players notice: unequipped left-hand
weapon, shield and staff visibility on the back and hip. It is by the same
author, and unlike IED it got a 2026-08-29 "Support for 1.7.x" release. What it
does **not** do is IED's actual distinguishing feature: arbitrary user-placed
displays of *any* item on *any* skeleton node, per-actor, with the in-game
editor - bags, tools, torches, potions, custom gear, NPC displays.

**The only DLL-free route to that.**
[All Geared Up Derivative SE - AllGUD](https://www.nexusmods.com/skyrimspecialedition/mods/28833) (Nexus 28833, Kriffin, 1.5.6). It is Papyrus + skeleton + xEdit-generated
display meshes with **no SKSE plugin of its own**, so no address-library
question arises and the 1.7.104 runtime is irrelevant to it. Two honest marks
against it: last updated **2020-03-22**, which is a red flag under
`reference_skyrim_ecosystem_currency_filter`; and it requires a mesh-generation
pass over the installed weapon and armour set, which against this build's ~259
mods is a real install project, not a drop-in. **Recommend evaluating it as its
own scoped piece of work if the user wants gear display, rather than bolting it
on now.**

**What is not an alternative:** waiting quietly. The author is committing but has
not released in 2 years 9 months, and the unpark trigger is outside our control.

### 2.6 Unpark trigger for #94

Any one of: (a) SlavicPotato uploads an IED build against a format-5 CommonLib;
(b) `sse-build-resources` reappears publicly at a 2023-or-later revision;
(c) the author publishes `ext/` in any form. Nothing else changes the answer,
and (c) is worth an ask if the user wants to send one - the licence on IED
itself is already MIT, so only the framework is in question.

---

## Files touched

- `records/installed-mods.json` - OAR row 3.2.0 -> 3.2.1
- `mo2-instances/skyrim-se/mods/Open Animation Replacer/` - replaced in place
- `mo2-instances/skyrim-se/profiles/Default/modlist.txt` - line 240 `-` -> `+`
  (backup `modlist.txt.bak.v20260902-pre-oar321`)
- `CHANGELOG.md`, this record
- Nothing under `records/source-builds/` - **no build was performed for either
  mod**, so no source-build JSON is owed
