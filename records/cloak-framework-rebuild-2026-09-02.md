# NPC cloak/hood framework: update sweep, licence status, rebuild attempt

Audit date: 2026-09-02

Runtime: Skyrim Special Edition `1.7.104.0` / SKSE `2.3.1` / Address Library
format 5

Tracker: [issue #95](https://github.com/Ensrick/skyrim-mod-assistant/issues/95)

Prior art: `records/modern-cloak-system-research-2026-08-30.md` (decision 5,
"If no author-updated NPC framework arrives, request permission to port Seasonal
Clothing Framework or commission a clean owned implementation?")

Authorisation: user, 2026-09-02, *"Ok, maybe we can find updates and/or fix
things up ourselves."*

Disposition: **research plus one successful local build. Nothing installed, no
profile mutation, no author contacted, no fork published.** The staged artifact
is deliberately gated behind a licence question that only the author can close.

---

## Verdict in one table

| Framework | Update found? | Rebuildable on 1.7.104? | Distribution class of the rebuild | Verdict |
|---|---|---|---|---|
| Seasonal Clothing Framework 1.0.1 (Nexus 186269, Bottle) | No new Nexus file. **Six unreleased commits on `master`**, including a real feature | **Yes - built, 0 errors, gate PASS** | **local-only** today; becomes **distributable** the moment the author states a licence | **Rebuilt and staged, blocked on licence** |
| WeatherBehaviorNG 2.5.1 (Nexus 175377, Cyrilounay) | No new Nexus file, no new commit. Public source still stops at 2.2.x | **Yes for 2.2.x - built, 0 errors, gate PASS. No for 2.5.1: that source does not exist** | **distributable** by the Nexus grant, but only of 2.2.x | **Built, then rejected: it is a three-release functional downgrade** |

Single recommendation: **stage the Seasonal Clothing Framework rebuild, send the
drafted licence question to Bottle, and hold the install behind his answer.** The
engineering blocker is gone; only the permission question remains, and that is
the user's to send.

---

## 1. Is there an update we missed?

Method: Nexus v1 API, full file list per `NEXUS_API.md` credential resolution
(`GET /games/skyrimspecialedition/mods/{id}/files.json`, every category, not just
`MAIN`), plus `changelogs.json`, plus the GitHub API over each author's public
repository, its branches, tags, releases, forks and Actions runs.

### Seasonal Clothing Framework - Nexus 186269

Mod record: `version 1.0.1`, `updated_timestamp 1784951020` =
`2026-07-25T03:43:40Z`, `status published`. **Three files total, and that is the
whole page:**

| file_id | category | version | uploaded (UTC) | size KB |
|---|---|---|---|---|
| 780441 | OLD_VERSION | 1.0.0 | 2026-07-23T23:43:07 | 18525 |
| 780446 | ARCHIVED | 1 | 2026-07-23T23:47:46 | 0 (example rain-hoods preset) |
| **780931** | **MAIN** | **1.0.1** | **2026-07-25T03:43:40** | 18580 |

No beta, no optional, no update file, no hotfix. `changelogs.json` lists exactly
one entry, `1.0.1 -> ["Clean up json output file", "Clean up the editor a bit"]`.
**No Nexus update exists.**

The repository is a different story. `github.com/InTheBottle/WeatherBehavior`
(named in the mod description as `source`) has `master` at
**`ade391ae90` (2026-07-29T15:18:36Z)** - four days *after* the 1.0.1 upload.
The shipped `WeatherBehavior.dll` carries PE TimeDateStamp `1784947638` =
`2026-07-25 02:47:18Z`, two minutes before commit `c67e8296` ("saving",
02:49:12Z), so the released tree is `c67e8296` or its immediate parent
(which of the two is [unverified] and does not matter here).

Six commits sit on `master` and in no Nexus release:

| commit | date (UTC) | what |
|---|---|---|
| `3e065d1683` | 2026-07-28T04:54:16 | Add CI build support (workflow + CMake) |
| **`01d61007ce`** | **2026-07-28T05:14:30** | **Add configurable season calendar for Four Seasons** (`Config.cpp` +14, `Config.h` +7, `Manager.cpp` +1, `Menu.cpp` +17, `Util.h` +48/-17) |
| `fbac643300` | 2026-07-28T05:17:46 | workflow author name |
| `44fc25d902` | 2026-07-28T06:01:32 | rename the calendar to "monthly", MO2-style CI zip |
| `c2849a3bde` | 2026-07-29T02:53:23 | simplify CI |
| `ade391ae90` | 2026-07-29T15:18:36 | merge PR #1 |

That is one substantive change: pull request
[#1](https://github.com/InTheBottle/WeatherBehavior/pull/1) by `NickStefan`
(merged 2026-07-29, 9 files, +125/-24) adds a `seasonCalendar` key to
`WeatherBehavior.json` with values `"vanilla"` (default, current behaviour) and
`"monthly"`, for
[Four Seasons - Faster Seasons of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/64286).
Verified default in source: `src/Config.h:49`
`std::string seasonCalendar{ std::string(kSeasonCalendarVanilla) }` and
`src/Config.cpp:215` `root.value("seasonCalendar", kSeasonCalendarVanilla)`.

Two things to flag about that PR, both from its own body:

- the author of the PR states *"I did use Cursor to make these changes"* -
  self-declared AI assistance, the same flag the 08-30 record raised against
  Dynamic Armor Variants Extended. It has not been code-reviewed by us.
- the CI workflow it adds is `on: workflow_dispatch` only and has **never been
  run** (`actions/runs` returns an empty list), so there is no CI artifact to
  fetch and no author-built binary newer than 1.0.1.

The single fork, `NickStefan/WeatherBehavior` (pushed 2026-07-29T02:53:50Z), is
the PR branch and is already merged; it contains nothing extra.

Posted-comment hotfixes: none found. The mod has 48 endorsements and 1,447
downloads; there is no pinned hotfix in the description, and the description's
only trailing content is the `source` link.

### WeatherBehaviorNG - Nexus 175377

Mod record: `version 2.5.1`, `updated_timestamp 1778389489` =
`2026-05-10T05:14:49Z`, `status published`. 28 files on the page. The newest is
**file 750568, `MAIN`, 2.5.1, uploaded 2026-05-10T05:14:49Z**; every other file
is `OLD_VERSION` or `ARCHIVED`, and the newest of those is
`749846` (2.5.0, 2026-05-08). `changelogs.json` ends at 2.5.1. **No Nexus update
exists, and there is no optional or update-category file newer than the main
one.**

`github.com/cygrand69-stack/WeatherBehaviorNG` has `main` at
**`4d46c7b0a9` (2026-04-02T06:50:57Z)**, unchanged since the 08-30 record - the
`README.md` at that commit still says *"Version 2.2.0 uses a dynamic runtime
injection system"*. Tags stop at `v2.1.0`; releases stop at `v2.1.0`. There is
**one branch, no fork, no CI.** Every commit is titled "Add files via upload",
so there is no per-change history to review either.

So the public source is **three feature releases behind the shipped binary**.
Everything in 2.3.0 (wig displacement), 2.4.0 (regional snow cloaks, KID wig
management), 2.4.1 (XDistributor/Dynamic NPC Hairstyles wig records, the
body-slot safety check that prevents naked NPCs), 2.5.0 (seasonal gear profiles,
Ennead/Scarves of Skyrim/More Scarves KID patches) and 2.5.1 (custom season month
mapping) exists only as a binary.

### Both binaries, re-verified

Archives are still in the MO2 download cache and hash to the values in the 08-30
record:

```
2dcf786a049efe6ce561206d1d1b85f50b466d464f9ddaed03170e935643a8fd  175377-750568.zip
b61c329c9ab57e14e4c804f1c8f4916d11420f782e8521516e9e1737cd2e02d1  186269-780931.zip
```

| DLL | SHA-256 | PE stamp | `skse_version_data.py` |
|---|---|---|---|
| SCF 1.0.1 `WeatherBehavior.dll` | `A59C48FC6C93AA8C05634CE9E452E2891775454E3777E36BE755F6C3A34E73F6` | 1784947638 = 2026-07-25 02:47:18Z | PASS, `versionIndependence=1`, `versionIndependenceEx=1` (V5 bit NO) |
| WBNG 2.5.1 `WeatherBehaviorNG.dll` | `4FF6A634740D2A46D7DD741C52A0C42C53B12B74A53FD31FB5A0D478E6C1D5B4` | 1778389463 = 2026-05-10 05:04:23Z | PASS, `versionIndependence=1`, `versionIndependenceEx=1` (V5 bit NO) |

Both pass the static gate and both are still unusable, which is exactly the trap
the 08-30 record named. The direct evidence, from a string scan of each DLL:

- both contain CommonLibSSE-NG's fatal string
  `Unsupported address library format: {}`;
- **neither vendor DLL contains a `load_v5` symbol.** The rebuilt DLL does:
  `bool __cdecl REL::IDDB::load_v5(...header_v5_t...)`. That single difference
  is the whole blocker.
- the SCF DLL embeds `D:\Repositories\WeatherBehavior\extern\CommonLibSSE-NG\...`
  build paths, which ties the Nexus binary to the public repository. The WBNG DLL
  embeds no source path at all, so its binary cannot be tied to any public tree.

Upstream fix, dated: `alandtse/CommonLibVR` commit **`7b47c5a8f1`**,
`2026-08-21T08:25:46Z`, *"feat(rel): support AE 1.7.99 address library format 5
(#299)"*, released as `6.4.0` (`e7863a7152`); the declaration flag followed in
**`d8b0acd80b`**, `2026-08-24T04:09:45Z`, *"feat: flag for address library v5
compatibility (#310)"* = `6.7.0`. The `ng` head is `2dde70e8bd`,
`2026-09-02T02:20:23Z`, release **7.1.0**. SCF's submodule is pinned at
`2527ccd474` (`2026-02-15`) - six months before format 5.

---

## 2. Licence status

Re-verified on the live repositories and the live Nexus pages on 2026-09-02.

### Seasonal Clothing Framework

**Repository: no licence.** `GET repos/InTheBottle/WeatherBehavior` returns
`"license": null`; `GET repos/InTheBottle/WeatherBehavior/license` returns
`404 Not Found`. The full tree at `ade391ae90` is nine blobs plus `extern/`,
`includes/`, `src/` - there is no `LICENSE`, `COPYING` or `NOTICE`.

**One new fact the 08-30 record did not have:** `vcpkg.json` at the repository
root declares

```json
"name": "weatherbehavior",
"license": "MIT",
```

That is an SPDX expression the author himself wrote into the project manifest.
It is *evidence of intent*, not a grant: MIT requires that "the above copyright
notice and this permission notice shall be included in all copies", and there is
no copyright notice and no permission notice anywhere in the repository to
include. Treat it as the strongest available argument that the answer to a
licence question will be yes, not as the answer.

**Nexus page: no structured grant.** Mod 186269 uses the free-text mode. Its
entire Permissions block is:

> **Author's instructions**
> please ask i probably wont say no

There is no upload permission row, no modification permission row, no asset-use
row. So Nexus grants us nothing by default, and the author has invited the
question in as many words.

### WeatherBehaviorNG

**Repository: no licence, and never had one.** `"license": null`,
`/license` 404, and `git log --all --diff-filter=A -- "*LICEN*" "*COPYING*"`
over the full clone returns nothing - no licence file has ever existed in the
history.

**Nexus page: a real, structured grant.** Mod 175377, verbatim:

> **Upload permission** - You can upload this file to other sites but you must
> credit me as the creator of the file
> **Modification permission** - You are allowed to modify my files and release
> bug fixes or improve on the features so long as you credit me as the original
> creator
> **Conversion permission** - You are not allowed to convert this file to work on
> other games under any circumstances
> **Asset use permission** - You are allowed to use the assets in this file
> without permission or crediting me
> **Asset use permission in mods/files that are being sold** - You are not
> allowed to use assets from this file in any mods/files that are being sold,
> for money, on Steam Workshop or other platforms
> **Asset use permission in mods/files that earn donation points** - You are
> allowed to earn Donation Points for your mods if they use my assets

So WBNG's *distribution* problem is solved and its *source* problem is not. We
may modify and redistribute the mod with credit; we simply do not have the source
of the version anyone would want.

### Which distribution class each outcome falls into

Using the three classes in `docs/PATCH_INTENTS.md` ("Every fix is a shippable
patch or a reproducible recipe", 2026-09-02) and the eligibility ruling in #160.

| Outcome | Class | Why |
|---|---|---|
| SCF rebuilt DLL, **as things stand today** | **local-only** | Our own compiled bytes, but derived from source carrying no licence. #160 lets a row be classified only if it is an Ensrick overlay/rebuild - this is - but `vendorBytesAllowed` covers permissive licences or a quoted upload permission, and we have neither. It runs on this machine and goes no further. |
| SCF rebuilt DLL **after Bottle confirms MIT** (or any permissive licence) | **distributable** | Then it is exactly the Light Placer shape: permissive upstream with its notice shipped, plus CommonLibSSE-NG under GPL-3.0-or-later with the modding linking exception, corresponding source available. Ships in the Ensrick patch collection with `WeatherBehavior-LICENSE.txt`. |
| SCF rebuilt DLL **as a recipe instead** | **recipe**, but a poor one | An installer could regenerate it from `InTheBottle/WeatherBehavior@ade391ae` + `alandtse/CommonLibVR@2dde70e8` + our two patches. It needs no vendor bytes. But it asks every user to run a 500-target C++ build with vcpkg and VS 2022, which is not a modlist installer step. Viable as a fallback only if the author declines redistribution but not compilation. |
| WBNG rebuilt from public 2.2.x source | **distributable** *(permission-wise)* | The Nexus modification+upload grant with credit covers it, and CommonLibSSE-NG's exception covers the linking. Permission is not the problem here; the missing 2.3.0-2.5.1 features are. |
| WBNG 2.5.1 rebuilt | **impossible** | The 2.5.1 source does not exist publicly. Nothing to build. |
| A clean owned Ensrick framework | **distributable** | Our own code, our own licence, no upstream constraint at all. |

Nothing here authorises redistributing any vendor archive. The vendor mods stay
required downloads from their own pages, per `REDISTRIBUTION.md`.

---

## 3. Can it be rebuilt forward?

### Build 1 - Seasonal Clothing Framework: SUCCESS

Recipe modelled on `records/source-builds/ensrick-light-placer.json`, but simpler:
SCF is already a CommonLibSSE-NG project, so there is no port to po3's fork and
no vcpkg overlay port. The entire fix is *bump the submodule and adapt to one API
change*.

**Source.** `github.com/InTheBottle/WeatherBehavior` at `ade391ae90` (master head,
2026-07-29), cloned to
`C:\Users\danjo\source\repos\skyrim-tools-source\WeatherBehavior-1.7.104`.
Not forked, not pushed - see the licence section.

**Changes, three of them:**

1. `extern/CommonLibSSE-NG`: `2527ccd47479e5bef01b82c0c7b287d435485f6a`
   (2026-02-15, formats 1 and 2 only) ->
   **`2dde70e8bdf9890bbd5e648966c7d2c24e83092f`** (alandtse/CommonLibVR `ng`,
   2026-09-02, release 7.1.0; `src/REL/IDDB.cpp:209` dispatches to `load_v5`).
   The submodule already tracks `branch = ng`, so this is the change the author
   would make himself.
2. `src/Manager.cpp`, two lines - the only compile break in the whole project.
   `BGSBipedObjectForm::GetSlotMask()` now returns
   `REX::EnumSet<BipedObjectSlot, std::uint32_t>` instead of a raw enum
   (`include/RE/B/BGSBipedObjectForm.h:79`), so `static_cast<std::uint32_t>` no
   longer compiles (`error C2440`):

   ```
   -  occupied |= static_cast<std::uint32_t>(wornArmor->GetSlotMask());
   +  occupied |= wornArmor->GetSlotMask().underlying();
   -  const auto mask = static_cast<std::uint32_t>(armor->GetSlotMask());
   +  const auto mask = armor->GetSlotMask().underlying();
   ```

   `REX::EnumSet::underlying()` returns the same `std::uint32_t` the old cast
   produced (`include/REX/REX/EnumSet.h:57`). Semantics unchanged.
3. `patches/commonlibsse-ng-no-modal-fail.patch` against the submodule -
   `include/SKSE/Impl/PCH.h:594`, `stl::report_and_error` -> the
   `REX::W32::MessageBoxW` call removed, the `spdlog critical` line above it and
   the `TerminateProcess` below it kept. Same intent as Light Placer's
   `no-modal-fail.patch`; this project's no-popup rule.
   `CMakeUserPresets.json` adds a `ninja-release` preset because the upstream
   `release` preset asks for generator `Visual Studio 18 2026`, which this
   machine does not have.

**Toolchain.**

| | |
|---|---|
| generator | Ninja (VS 2022 bundled, `Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja`) |
| compiler | MSVC 19.44.35223.0, `VC/Tools/MSVC/14.44.35207` Hostx64/x64, VS 2022 Community |
| vcpkg root | `C:/Users/danjo/source/repos/vcpkg` at `ddd0023b0eee70986e42ed49d9d4afb8098f212e` |
| triplet | `x64-windows-static`, `/MT` |
| flags | upstream preset: `/EHsc /MP /W4 /permissive-`, Release `/O2 /Ob2 /DNDEBUG`, `/Zi` + `/DEBUG /OPT:REF /OPT:ICF` |
| CommonLib options | `Enable Skyrim SE/AE/VR: ON`, `Build Tests: OFF`, `Enable Xbyak: OFF`, patch safety ON |
| priority | BelowNormal |

**Command.**

```
Enter-VsDevShell -VsInstallPath "...\2022\Community" -DevCmdArguments "-arch=x64 -host_arch=x64"
$env:VCPKG_ROOT = "C:/Users/danjo/source/repos/vcpkg"
cmake --preset ninja-release
cmake --build --preset ninja-release
```

**Result: clean build, exit 0, 0 errors, 4 warnings** - `C4099` once and `C5054`
three times, all inside the vendored third-party `includes/SKSEMenuFramework.h`
(the SKSE Menu Framework public header). Zero warnings in the mod's own 1,419
lines. Log:
`skyrim-tools-source/WeatherBehavior-1.7.104/build-logs/build.log`.

**Artifact.**

| file | SHA-256 | bytes |
|---|---|---|
| `WeatherBehavior.dll` | `4037C313E7157E22BD6F552845F3F02CF40B3459CA00923FBBB85C1239B58B67` | 1,056,256 |
| `WeatherBehavior.pdb` | `59901A785605043AAE2C27E7FB6232E698FCAF55F3318F1C1E10B485B808154F` | 27,316,224 |

PE TimeDateStamp `1788376171` = `2026-09-02 19:09:31Z`.

**Gate - `audit/skse_version_data.py`: PASS (version independent).**
`name='WeatherBehavior'`, `author='bottle'`, `pluginVersion 1.0.0.0`,
`versionIndependence=1` (AddressLibraryPostAE), `versionIndependenceEx=1`.

Three honest notes on that gate, because it is necessary and never sufficient:

- the `AddressLibraryV5` declaration bit is **not** set (`viEx=1`, not 3). That
  is not a defect and not something to "fix": the project uses NG's newer
  `SKSEPluginInfo`/`PluginDeclaration` API, whose `StructCompatibility` field
  occupies the same offset (0x304) and whose `Independent` value is 1. SKSE only
  makes a missing V5 bit fatal when the PE stamp falls in
  `[520128000, 1748217600)`; this build stamps 2026-09-02, so it passes on the
  stamp. The vendor 1.0.1 DLL declares the identical `viEx=1` and SKSE admits it
  too - the vendor's problem was never the declaration, it was the linked code.
- the tool also prints sixteen `compatibleVersions` entries of `1.0.0.0`. That is
  an artifact, not a declaration: NG stores `RuntimeCompatibility` as
  `std::array<VersionNumber, 16> _compatibleVersions{}` and `VersionNumber`
  default-constructs with `a_major = 1`, so value-initialising the array yields
  sixteen `0x01000000` words. SKSE ignores the array whenever
  `kVersionIndependent_AddressLibraryPostAE` is set, which it is, and the vendor
  1.0.1 DLL prints the identical sixteen entries.
- what the gate cannot see, and what actually matters, is that the built DLL now
  contains `REL::IDDB::load_v5` and the vendor DLL does not.

**No-popup rule: satisfied.** The rebuilt DLL contains no `MessageBoxA`/
`MessageBoxW` import string at all (the vendor DLL imports both). The only caller
was `stl::report_and_fail`; an address-library failure now writes
`WeatherBehavior.log` and terminates.

**Feature defaults.** One key added versus 1.0.1, from the unreleased PR #1:
`seasonCalendar`, default `"vanilla"` = the 1.0.1 mapping. `enabled=true`,
`onlyOutdoors=true`, `pollSeconds=5` are unchanged (`src/Config.h:43-49`,
`src/Config.cpp:212-215`). So the rebuilt build is behaviour-identical to 1.0.1
out of the box and gains an opt-in setting.

**Dependency reality check.** SCF's two hard requirements are already installed,
enabled, and provably loading on the live 1.7.104 profile - from `skse64.log`
of the 2026-09-02 13:33 session:

```
plugin po3_Tweaks.dll (00000001 powerofthree's Tweaks 01110010) loaded correctly (handle 20)
plugin SKSEMenuFramework.dll (00000001 SKSEMenuFramework 030D0000) loaded correctly (handle 25)
plugin po3_KeywordItemDistributor.dll (00000001 Keyword Item Distributor 04010000) loaded correctly (handle 16)
plugin po3_SpellPerkItemDistributor.dll (00000001 Spell Perk Item Distributor 07000000) loaded correctly (handle 19)
```

Adopting this adds **no new dependency to the build.**

**Staged, not installed.**
`records/source-builds/ensrick-seasonal-clothing-framework/`
(`SKSE/Plugins/WeatherBehavior.dll` + `.pdb`, CommonLibSSE-NG `COPYING` and
`EXCEPTIONS.md`, and a `README-STAGED-NOT-INSTALLED.txt` carrying the licence
hold). The repo is deny-by-default, so those binaries are gitignored -
`git check-ignore` confirms - exactly like the Light Placer staging directory.
Build record: `records/source-builds/ensrick-seasonal-clothing-framework.json`.

**What is NOT verified.** No launch. No hook exercise. No rule created, no NPC
ever equipped anything. Per `docs/CURATION_POLICY.md` "Launch verification is the
definition of done", this build is not done and is not adoptable until a
`launch_verify.py` PASS follows an install - and that install must not happen
until the licence question is answered.

### Build 2 - WeatherBehaviorNG: compiles, and must not be used

Setup, for the record: WBNG has no submodule. Its
`vcpkg-configuration.json` points `commonlibsse-ng` at the colorglass registry
(`gitlab.com/colorglass/vcpkg-colorglass`, baseline
`6fb127f7d425ae3cf3fab0f79005d907c885c0d8`), whose newest
`commonlibsse-ng` is **version-semver 3.7.0**, sourced from
`CharmedBaryon/CommonLibSSE` at `c4ab853d095e81e3390b282d7ba01ab2f24ebf25` - the
original, unmaintained NG. That line has no format-5 support and never will. So
even the "just bump the baseline" route does not exist: the dependency has to be
repointed at `alandtse/CommonLibVR` outright.

Changes made to attempt it, in
`C:\Users\danjo\source\repos\skyrim-tools-source\WeatherBehaviorNG-1.7.104`:

1. `extern/CommonLibSSE-NG` added as a submodule on `alandtse/CommonLibVR` `ng`,
   pinned to `2dde70e8bd` (7.1.0);
2. `CMakeLists.txt`: `find_package(CommonLibSSE CONFIG REQUIRED)` replaced with
   `add_subdirectory(extern/CommonLibSSE-NG ...)` +
   `include(extern/CommonLibSSE-NG/cmake/CommonLibSSE.cmake)` (which is where
   `add_commonlibsse_plugin` lives, at `cmake/CommonLibSSE.cmake:182`), plus the
   static-CRT setting the project was relying on the port for;
3. `vcpkg.json` rewritten to NG 7.1.0's own dependency set,
   `vcpkg-configuration.json` deleted, a `ninja-release` `CMakePresets.json`
   added;
4. `Gearsystem.cpp` lines 466 and 491 - the identical `GetSlotMask()` /
   `REX::EnumSet` break, fixed the identical way (`.underlying()`);
5. the same `patches/commonlibsse-ng-no-modal-fail.patch`, applied cleanly to
   this copy of the submodule.

**Result: it builds. Exit 0, 0 errors, 0 warnings.**

| file | SHA-256 | bytes |
|---|---|---|
| `WeatherBehaviorNG.dll` | `A735D6F1017EE464C172EF23B89E0BAB16038125549119C53EF85E139E1CC2D8` | 954,880 |

PE stamp `1788376768` = `2026-09-02 19:19:28Z`.
`audit/skse_version_data.py`: **PASS (version independent)**,
`name='WeatherBehaviorNG'`, `versionIndependence=1`. It contains
`REL::IDDB::load_v5` and imports no `MessageBox`. On the narrow question the task
asked - *can it be rebuilt forward?* - the answer is yes, and it took the same
two-line fix.

**And it must not be installed, because it is a three-release downgrade of the
mod the user would actually be running.** Two measurements, not opinions:

1. **Keyword pools.** Extracting every `WBNG_*` string from both DLLs:

   | | keywords |
   |---|---|
   | vendor 2.5.1 | 13, including **`WBNG_Wig`** |
   | rebuilt from public source | 12 - `WBNG_Wig` absent |

   The shipped 2.5.1 FOMOD contains six wig KID patches (KS Hairdos SMP, Koralina
   Wig Collection v2, dint999 HairPack02, Vanilla Hair Remake, XDistributor,
   Dynamic NPC Hairstyles). Every one of them tags records with a keyword this
   build would never read, so they would install and do nothing, and hoods would
   stop displacing hair.

2. **Settings.** The 2.2.x `Config.cpp` parses exactly 14 keys across four
   sections - `[General]`, `[Timing]`, `[Combat]`, `[Debug]`. The shipped 2.5.1
   `WeatherBehaviorNG.ini` also ships `[Regional]` (3 keys:
   `bEnableRegionalSnowCloaks`, `iRegionalSnowCloakChancePercent`,
   `bRegionalSnowCloaksStayInCombat`) and `[Seasons]` (14 keys:
   `bEnableSeasonalGearProfiles`, `bUseCustomSeasonMonthMap`,
   `sMonth0Profile`..`sMonth11Profile`). **Seventeen shipped settings would be
   read by nobody**, silently - the parser skips unknown sections rather than
   warning.

Not counted in those two, but also gone: the 2.4.1 safety check that "rejects
unsafe weather accessories that use main body armor slots, helping prevent NPC
outfit stripping / naked NPC issues". Shipping a build without a fix whose
changelog entry names naked NPCs is not a trade worth making.

So this artifact stays in its build tree
(`C:\Users\danjo\source\repos\skyrim-tools-source\WeatherBehaviorNG-1.7.104\build\ninja-release\`)
and is deliberately **not** staged as an MO2 mod root and given no
`records/source-builds/` entry - a staged folder is an invitation to install, and
this one should not be. It is recorded here as proof that the blocker is the
missing 2.5.1 source, not the runtime.

---

## 4. Scope of a clean owned implementation

Only if both routes above stay blocked. Sizing first, because it is the
surprising part: **this is a small program.** SCF is **1,419 lines** of its own
C++ (`Config.cpp` 345, `Manager.cpp` 358, `Menu.cpp` 443, `Main.cpp` 65, plus
headers) on top of a vendored 11,388-line third-party `SKSEMenuFramework.h`
header it did not write. WBNG 2.2.x is **1,163 lines** (`Gearsystem.cpp` 931 is
the whole engine). Neither is a large system; both are one careful person's
month.

### Minimum viable `Ensrick - Weather Gear Framework`

**What it must do.** Everything below is a requirement drawn from observed
behaviour and from this build's constraints - not copied code:

1. **Selection.** Given the loaded actor set, decide which generic humanoid NPCs
   get which accessory, from an explicit allowlist of Editor IDs or keyword
   pools. The choice must be *deterministic per actor* (hash the FormID with the
   rule name) so a crowd looks varied but an individual is stable across a
   reload - both existing frameworks do this and it is the difference between
   "atmosphere" and "flickering".
2. **Conditions.** Weather class (pleasant/cloudy/rainy/snowy), season from the
   in-game month with a configurable month->season map, interior/exterior,
   region, and a per-rule chance. Regional and faction filters are the gap the
   08-30 record identified in SCF's schema and they belong in v1, not v2.
3. **Free-slot discipline.** Compute the occupied biped-slot mask from what the
   actor is *already wearing* and only fill genuinely free slots. Never displace
   existing equipment. Reject any candidate whose slot mask touches a main body
   slot - that is the exact failure WBNG 2.4.1 had to patch (naked NPCs), and it
   is cheaper to have the rule from day one.
4. **Exclusions.** Player, children, creatures, dead, disabled, mannequins,
   prisoners/beggars where configured, and anything a SPID exclusion names.
   Honour SPID (7.3.3), KID (4.1.0) and SkyPatcher (7.0.3) as *inputs*: KID
   supplies the keyword pools, SPID supplies the exclusion vocabulary, SkyPatcher
   supplies owned record edits. The framework never edits an outfit or a vanilla
   record itself.
5. **Ownership and cleanup - the hard part.** Track every item *this* framework
   added, per actor, and remove only those. Serialise that map through SKSE
   co-save (`SKSE::SerializationInterface`), resolve FormIDs on load, and drop
   entries whose source plugin has gone. Clean on: condition clear, cell unload,
   actor death, disable, follower dismissal, transformation, master-switch off,
   and uninstall. This is where a naive implementation leaves cloaks stuck in a
   thousand inventories and poisons a save.
6. **Pacing.** No per-frame work. A sleeping worker that schedules one bounded
   pass on the game thread every N seconds, returning immediately when no rule is
   active. SCF's design here is right and is worth reproducing as a *requirement*.
7. **Configuration.** JSON presets on disk, shareable, hand-editable, plus an
   optional SKSE Menu Framework UI. Presets keyed by Editor ID, not FormID, so
   they survive load-order changes.

**Built on.** CommonLibSSE-NG (`alandtse/CommonLibVR` `ng`, 7.1.0+) with the
`no-modal-fail` patch, `x64-windows-static`, Ninja + MSVC 14.44 - byte for byte
the toolchain that just produced a working DLL in this session, so the build
environment cost is already paid. Optional: SKSE Menu Framework for the UI (its
public header is redistributable and already in the profile).

**Size.** Realistically **1,200-1,800 lines** across selection, condition
evaluation, slot arithmetic, the ownership ledger, serialisation, config I/O and
the menu, plus a JSON schema and a test profile. Call it **two to four focused
days** for someone who already has this toolchain working, of which the
serialisation and cleanup paths are more than half, and then the same
save-safety matrix the 08-30 record already wrote (`## Save and performance
safety`) before it could be trusted on a real save.

### Build vs wait

**Recommendation: neither - ask, then adopt the rebuild.** Writing a fresh
framework is *technically* reasonable and would end all licence questions
permanently, but it spends several days rebuilding something that already exists,
that already has the serialisation and cleanup logic written and shipped, and
that we have now proven compiles and gates clean on this runtime. The blocker was
never capability; it was a submodule pin and one `static_cast`.

Waiting is also not the answer, and the doctrine says so: parking is not a
neutral holding state
(`feedback_never_downgrade_rebuild_forward`, extended 2026-08-30). SCF's page has
not moved since 2026-07-25 and WBNG's since 2026-05-10; neither author has
reacted to the 2026-08-21 format-5 transition in a release.

So the ordering is:

1. **Send Bottle the licence question** (drafted below). His own `vcpkg.json`
   already says MIT and his Nexus instruction is "please ask i probably wont say
   no", so this is a formality with a high prior of success - but it is a
   formality that converts the staged DLL from `local-only` to `distributable`.
2. **Meanwhile the artifact is built and staged.** If the user wants it running
   on this machine before any answer arrives, that is a local install of a local
   build and breaks no permission - but it still needs its own claimed batch and
   its own `launch_verify.py` PASS, and it must not enter the packaged
   collection.
3. **Only if Bottle declines or does not answer** does the clean owned
   implementation become the right spend - and at that point build it against the
   *requirements* above, from the same toolchain, and licence it ourselves.

---

## 5. Drafted author messages - NOT SENT

Per the task constraint, no author has been contacted. These are staged for the
user to send, edit, or discard. Both are for the Nexus "Send a private message"
route on the author's profile, or the mod's Posts tab.

### To `Bottle` - Seasonal Clothing Framework (Nexus 186269)

> Subject: Seasonal Clothing Framework - licence question, and a working 1.7.104 build
>
> Hi Bottle,
>
> Your page says "please ask i probably wont say no", so - asking.
>
> Seasonal Clothing Framework 1.0.1 cannot load on Skyrim 1.7.104. Its
> `extern/CommonLibSSE-NG` submodule is pinned at `2527ccd4` (Feb 2026), and
> Address Library format 5 support only landed in CommonLibSSE-NG on 2026-08-21
> (`7b47c5a8f1`, released 6.4.0). The shipped DLL has no `load_v5`, so it hits
> "Unsupported address library format: 5" on the current runtime.
>
> The fix turned out to be tiny. I bumped the submodule to the current `ng` head
> (7.1.0) and the only compile break in the whole project was
> `BGSBipedObjectForm::GetSlotMask()` now returning `REX::EnumSet<...>` instead
> of a raw enum - two lines in `src/Manager.cpp` become
> `.underlying()` instead of `static_cast<std::uint32_t>`. Clean build after
> that, zero errors, and the resulting DLL passes SKSE's version gate and
> contains `REL::IDDB::load_v5`. I built from `master` (`ade391ae`), so it also
> picks up NickStefan's `seasonCalendar` change, which defaults to "vanilla" and
> changes nothing unless you opt in.
>
> Two things:
>
> 1. Would you rather just do this yourself and push a 1.0.2? Genuinely the
>    better outcome - it is a submodule bump and two lines, and your users would
>    get it through Nexus. I am happy to send the exact diff.
> 2. If you would rather not, may I have a licence on the repository? Your
>    `vcpkg.json` already declares `"license": "MIT"`, but there is no LICENSE
>    file, so I cannot rely on it. Dropping an MIT LICENSE with your copyright
>    line into the repo would settle it - and would let me include the rebuilt
>    DLL, with attribution and your notice, in a private modlist I am putting
>    together. If you prefer it stay off other sites entirely, say so and it
>    stays on my own machine; I will not upload anything either way without your
>    yes.
>
> Either answer is fine. Thanks for releasing the source in the first place -
> it is the only reason this was a two-line fix instead of a dead end.

### To `Cyrilounay` - WeatherBehaviorNG (Nexus 175377)

> Subject: WeatherBehaviorNG - 1.7.104 (format 5), and the source/binary gap
>
> Hi Cyrilounay,
>
> WeatherBehaviorNG 2.5.1 cannot load on Skyrim 1.7.104. The DLL was linked
> 2026-05-10, and CommonLibSSE-NG only gained Address Library format 5 support on
> 2026-08-21 (`alandtse/CommonLibVR` `7b47c5a8f1`, release 6.4.0). Your DLL has no
> `load_v5`, so it fails at "Unsupported address library format: 5". A rebuild
> against the current `ng` branch should be the whole fix.
>
> I confirmed that locally: I built your public source against CommonLibSSE-NG
> 7.1.0 and it compiled with one two-line change (`GetSlotMask()` now returns a
> `REX::EnumSet`, so `static_cast<std::uint32_t>` becomes `.underlying()`). The
> resulting DLL loads format 5. So the runtime is genuinely not the hard part.
>
> The hard part is that `github.com/cygrand69-stack/WeatherBehaviorNG` is still
> at `4d46c7b0` from 2026-04-02, and its README describes 2.2.0. My build has no
> `WBNG_Wig` keyword and no `[Regional]` or `[Seasons]` INI handling, so your own
> wig patches and seventeen of your shipped settings would do nothing - and it is
> missing the 2.4.1 body-slot check that stops naked NPCs. I am not going to
> ship that at your users, so the build stays on my machine.
>
> Also, `vcpkg-configuration.json` points `commonlibsse-ng` at the colorglass
> registry, whose newest version is 3.7.0 from `CharmedBaryon/CommonLibSSE` -
> that line is unmaintained and will never get format 5. The maintained fork is
> `alandtse/CommonLibVR` on branch `ng`.
>
> So: any chance of a 2.5.2 rebuild, or of pushing the current source? Your Nexus
> permissions already allow modification and re-upload with credit, so if the
> source were current I would be glad to do the rebuild and hand you the diff
> rather than fork anything.
>
> Thanks either way - the KID-pool design is the right shape for this problem.

---

## Receipts index

| claim | artifact |
|---|---|
| SCF page has 3 files, newest 780931 (2026-07-25) | Nexus v1 `/mods/186269/files.json` |
| WBNG page has 28 files, newest 750568 (2026-05-10) | Nexus v1 `/mods/175377/files.json` |
| SCF master is 6 commits past the release | GitHub `repos/InTheBottle/WeatherBehavior/commits`, head `ade391ae90` |
| PR #1 adds `seasonCalendar`, AI-assisted, merged 2026-07-29 | GitHub `repos/InTheBottle/WeatherBehavior/pulls/1` |
| SCF CI has never run | GitHub `actions/runs` -> empty |
| WBNG main unchanged since 2026-04-02, README says 2.2.0 | GitHub `repos/cygrand69-stack/WeatherBehaviorNG/commits`, `contents/README.md` |
| Neither repo has a licence | `repos/*/license` -> 404; `git log --all --diff-filter=A -- "*LICEN*"` empty |
| SCF `vcpkg.json` declares MIT | `repos/InTheBottle/WeatherBehavior/contents/vcpkg.json` |
| SCF Nexus permission text | mod page 186269, Permissions and credits |
| WBNG Nexus permission text | mod page 175377, Permissions and credits |
| format 5 landed 2026-08-21 | `alandtse/CommonLibVR` `7b47c5a8f1`, release `e7863a7152` = 6.4.0 |
| V5 declaration flag 2026-08-24 | `alandtse/CommonLibVR` `d8b0acd80b` = 6.7.0 |
| SCF submodule pinned 2026-02-15 | tree at `ade391ae90`, `extern/CommonLibSSE-NG -> 2527ccd474` |
| vendor DLLs lack `load_v5`, rebuild has it | string scan of all three DLLs |
| SCF build clean, 0 errors, 4 vendored-header warnings | `skyrim-tools-source/WeatherBehavior-1.7.104/build-logs/build.log` |
| rebuilt DLL passes the SKSE gate | `audit/skse_version_data.py` on the built DLL |
| rebuilt DLL has no MessageBox import | string scan; vendor DLL imports `MessageBoxA`/`MessageBoxW` |
| SCF's dependencies load on 1.7.104 today | `Documents/My Games/Skyrim Special Edition/SKSE/skse64.log`, 2026-09-02 13:33 |
| colorglass `commonlibsse-ng` tops out at 3.7.0 | `gitlab.com/colorglass/vcpkg-colorglass`, `versions/c-/commonlibsse-ng.json` |
| WBNG 2.2.x builds clean against NG 7.1.0, gate PASS | `skyrim-tools-source/WeatherBehaviorNG-1.7.104/build-logs/build.log` exit 0; `audit/skse_version_data.py` on `WeatherBehaviorNG.dll` sha256 `A735D6F1...` |
| rebuilt WBNG lacks `WBNG_Wig`; vendor 2.5.1 has it | `WBNG_*` string extraction from both DLLs (13 vs 12 keywords) |
| 17 shipped INI settings unreadable by 2.2.x | `Gearsystem.cpp`/`Config.cpp` parse 14 keys in `[General]/[Timing]/[Combat]/[Debug]`; the shipped `WeatherBehaviorNG.ini` also ships `[Regional]` (3) and `[Seasons]` (14) |
