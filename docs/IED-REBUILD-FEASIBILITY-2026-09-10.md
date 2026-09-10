# IED rebuild feasibility for Skyrim SE 1.7.104

Date: 2026-09-10. Read-only audit; nothing installed, no game launch, MO2 profile untouched.
Scope: can Immersive Equipment Displays (Nexus 62001, SlavicPotato, MIT, last release 1.7.4 on 2023-12-10) be rebuilt for runtime 1.7.104 / Address Library format 5, and what would it cost. Refs #94, #201, #36.

Receipts: `records/ied-rebuild-feasibility-2026-09-10/` (header lists, symbol tables, compile census, recovered headers, per-iteration MSBuild error lists).

## Symptom

`SlavicPotato/ied-dev` (`master` `d8e9d33`, 2026-03-05) compiles only against the author's private `sse-build-resources` tree, which sits as a sibling directory on every include path and is force-included through `ext/ICommon.h`. `SlavicPotato/sse-build-resources` is 404. The only public copy (`clayne`, 2022-02-12) plus our own additions (`Ensrick/sse-build-resources` `ensrick/1.7.99-format5`, 59 `ext/*.h`) covers the framework as it was when IED was at 1.3.x. IED has grown against a framework nobody but the author has.

## Evidence

### A. The exact gap (counted from source, tolerant `#\s*include` regex)

| IED revision | distinct `ext/*.h` includes | missing from our fork |
|---|---|---|
| `7e240fd` 2022-02-13 (contemporary with the clayne mirror) | 26 | 1 (`str_conv.h`, which we already re-added) |
| `origin/1.6` 2022-11-27 | 48 | 23 |
| `3f014c3` = release 1.7.4, 2023-12-10 | 71 | 48 |
| `origin/1.7` 2023-08-06 | 69 | 46 |
| `master d8e9d33` 2026-03-05 (target) | 75 (74 unconditional + `stl_allocator_mi.h` under `IED_USE_MIMALLOC_*`) | **52** |

Plus two vendored-skse64 headers IED includes that the 2022 patched skse64 tree does not have: `skse64/BipedObject.h`, `skse64/GameAudio.h` (the latter is listed in the mirror's `.vcxproj.filters` but the file was never in the mirror). Direct-include gap: **54 files**. Transitive includes inside those 54 are unknowable without the files; the shipped 1.7.4 DLL's assert strings name two more (`ext\BSTask.h`, `ext\BranchTrampoline.h`) that no IED source includes directly, so the real file count is higher.

Full lists: `missing-ext-headers.txt`, `missing-skse64-headers.txt`, `missing-header-includers.tsv` (which IED file pulls each one; 44 of the 52 come in only through `pch.h`).

### B. What IED actually uses from the missing headers

`engine-symbol-usage.txt` and `stl-tokens-not-in-fork.txt` hold the greps. Summary by class:

**B1. `stl_*` container/utility layer (14 headers).** 65 distinct `stl::` tokens used by IED; **42 are undefined in our fork** (grep) and the compiler census (section D) raises that to **44 missing `stl::` members**: `lock_guard` (215 uses), `smart_ptr` (60) + `intrusive_ref_counted`/`make_smart[_for_overwrite]`, `cache_aligned` (44), `boost_vector` (30) + `boost_unordered_map` + `boost_container_allocator`, `traced_exception`/`report_and_fail` (30), `make_array`, `flat_set`/`flat_map`, `read_/write_lock_guard`, `shared_mutex`, `recursive_mutex`, `fast_spin_lock`, `flag_bf`, `array_size_v`, `strnicmp`, `container_init_wrapper`, `type_hash`, `tolower_ascii`, `fnv1a_64`, `hash_string`, `L1_CACHE_LINE_SIZE`, `ston`, `forward_list`, `split_string`, `is_equal`, `ftz_daz_ctl_scoped`, `fmod`/`fmod_1`, `fixed_string_less_equal_ptr`, `validate_memory_with_report_and_fail`, `mi_allocator`, `hasher`/`fnv_hasher`/`fnv_variant`, `cts`, `container_allocator`, `clamped_num_cast`, `charproc_toupper_l1s`, `wstr_to_str`, and the plain aliases `stl::vector/list/map/set/unordered_map/queue`. `stl::fixed_string` itself exists in our `StringCache.h` (731 uses) but the 2023 version gained `make_tuple`, `make_hash`, `compute_hash`, `less_str`. All of this is thin wrapping over STL/boost; none of it touches game memory.

**B2. SKSE plumbing (7 headers).** `SKSEMessagingHandler` (`GetSingleton().AddSink/Setup`), `SKSESerializationEventHandler` (`GetDispatcher<SKSESerializationEvent>().AddSink`, event types `kSave/kRevert`), `SKSEMessagingEvents.h`, `SKSESerializationEvents.h`, `ISerializationBase` (base class of `Controller`), `IDebugLog.h` (no direct use), `ILUID.h` (`luid_tag`/`ILUID` - **4,430 census errors**, the single most pervasive symbol; it is a locally-unique-id mixin every config object carries). Dispatcher-over-SKSE-interface code; reconstructable from usage.

**B3. Plugin interface (3 headers).** `PluginInterfaceBase.h`, `PluginInterfaceSDS.h`, `SDSPlayerShieldOnBackSwitchEvent.h`. **Recovered** - see C.

**B4. Engine-structure headers (30 of the 52 plus the 2 skse64 ones).** The `RE::` classes IED touches, with the members it uses: `TES` (`sky`, `worldSpace`, `interiorCell`), `Sky` (`currentGameHour`, `currentRoom`, `skyColor`, `currentClimate`, `currentWeather`, `lastWeather`, `currentWeatherPct`, `clouds`, `GetSunPosition`, `GetCurrentWeatherHalfPct`), `Clouds`, `TESClimate` (`timing`), `ShadowSceneNode` (`sunLight`, `shadowDirLight`, `CreateAndAddLight`, `QueueAddLight`, `UnkQueueBSLight`), `BSLight` (`light`, `pointLight`, `fade`, `diffuse`), `BSShaderPropertyLightData` (`lights`), `ImageSpaceManager` (`data.baseData.hdr.sunlightScale`), `BGSLensFlare`, `Calendar` (`GetDayOfWeek`, `Day` enum, `gameHour`, `GetYear/GetMonth/GetDay/GetDaysPassed/GetTimescale`), `GarbageCollector` (`QueueBehaviorGraph`, `QueueForm`), `BackgroundProcessThread` (`QueueTask`, `m_list`), `BSThread` (base of `ActorProcessorTask`), `IOTask` (base of 3 loader tasks), `BSAnimationGraphManager`/`BSAnimationUpdateData`/`WeaponAnimationGraphManagerHolder` (`Create()`, `GetSequenceByName`), `hkaSkeleton` (`name`), `ShaderReferenceEffect` (hooked at `Resume`+0x84), `ConcreteFormFactory` (`IFormFactory::GetConcreteFormFactoryByType<BGSOutfit>()`), `InteriorData` (`lightingTemplateInheritanceFlags`), `RefrInteraction`, `LightCreateParams`, `BSString`, `D3D11Backup` (`D3D11StateBackupImpl`), `MemoryValidation`, `INIConfReader` (one INI reader use), `IOTask`, `compiletime-strings`.

Cross-check against CommonLibSSE-NG 6.7.1 (`skyrim-tools-source/CommonLibSSE-NG-6.7.1`): **22 of the 24 class layouts exist there** with the same member names IED uses (`TES::sky`, `Sky::currentRoom/currentGameHour/skyColor/clouds`, `Calendar::GetDayOfWeek`, `ImageSpaceData::sunlightScale`, `hkaSkeleton::name`, `IFormFactory::GetConcreteFormFactoryByType`, `TESClimate::timing`, `BSShaderPropertyLightData::lights`, ...). Missing in NG: `BackgroundProcessThread` (RTTI/VTABLE ids only, no layout), and the author's own function wrappers (`Sky::GetSunPosition`, `GetCurrentWeatherHalfPct`, `ShadowSceneNode::QueueAddLight/UnkQueueBSLight/CreateAndAddLight`, `WeaponAnimationGraphManagerHolder::Create`, `GarbageCollector::QueueBehaviorGraph/QueueForm`, `Calendar::Day` enum) which are engine functions resolved by Address Library id. So the layouts are not lost knowledge; they are in a different type system (`RE::NiPointer`/`RE::BSFixedString` vs the skse64 `NiPointer`/`BSFixedString` IED is written against) and would have to be transplanted member by member.

### C. Survivor hunt - exhaustive, with receipts

| Source | Result |
|---|---|
| All 19 `SlavicPotato` repos (`gh api users/SlavicPotato/repos`) - tree scan of every default branch | no `ext/`, no `.gitmodules`, no `vcpkg.json`, no `sse-build-resources` vendored anywhere (`slavicpotato-repo-tree-scan.txt`). `SimpleDualSheath` last push 2023-05-22; the 2026 SDS source is not public. |
| Deleted submodule SHAs | none exist: IED, SDS, SSEDisplayTweaks, CBPSSE never used a submodule (`git log --all -- .gitmodules` empty; the `.sln` references `..\sse-build-resources\sse-build-resources.vcxproj` by relative path). |
| GitHub fork network of `clayne/sse-build-resources` | 5 forks: `renngar`, `rethesda` (2022-02-12), `pcbeard` (2021-02-21), `Ensrick` (ours), **`schlosserleo` pushed 2026-08-27** - a third party porting the same 2022 base to 1.7.99/SKSE 2.3.0 for SSEDisplayTweaks; 88 files, identical `ext/` set, **none of the 52** (`schlosserleo-fork-ext-list.txt`). Useful ally for the SSEDisplayTweaks family, useless for IED. |
| `gh api search/repositories?q=sse-build-resources` | only `clayne`. |
| GitHub code search for distinctive names (`stl_flat_map.h`, `stl_csr.h`, `stl_fixed_string.h`, `compiletime-strings.h`, `D3D11Backup.h`, `BackgroundProcessThread.h`, `INIConfReader.h`, `stl_boost_serialization_containers`, `BipedObject.h skse64`, `SKSEMessagingHandler.h`, `ISKSEBase`, `SKMP_GetPluginInterface`) | every hit is `SlavicPotato/ied-dev` itself or another SlavicPotato consumer that `#include`s the name (SSMT_Fix 2023-04, EquipEnchantmentFix/UnlimitedFastTravel 2022-10, skee64-memleak-patch 2022-06). No copy of the headers anywhere on GitHub. |
| Software Heritage | origin `github.com/SlavicPotato/sse-build-resources` **never archived** (`NotFoundExc`). Origin search lists 5 forks: `clayne`/`rethesda`/`renngar` share snapshot `56549d7a2617` (2022-02-12 tree), `pcbeard` `22388b6f0a85` (2021-02-21), `Enesore` listed but "no visit" and 404 on GitHub. |
| Wayback Machine (CDX) | 55 captures of `github.com/SlavicPotato/sse-build-resources*`, **all 2020-11-25**; zero for `raw.githubusercontent.com` or `codeload` (`wayback-cdx-sse-build-resources.txt`). |
| Nexus 62001 files (API) | 48 files, all binary zips 1.3-2.2 MB, no source, no PDB, no optional files. Newest 450464/450465 = 1.7.4, 2023-12-10. |
| Nexus 50049 files (API) | 30 files, all binary; 1.5.8 and 1.5.9 both 2026-08-29 ("Support for 1.7.x", "Remove development leftovers"). No source zip. |
| SDS 1.5.9 DLL strings (`mods/Simple Dual Sheath/SKSE/Plugins/SimpleDualSheath.dll`) | PE stamp 2026-08-29 20:24:35 UTC, linker 14.44, Rich header MSVC 14.44.35207/35224 (VS 2022 17.14). PDB path `x:\repos\SimpleDualSheath\x64\Release MT Post 629 143\`. Assert paths: `X:\repos\sse-build-resources\ext/BSTList.h`, `ext\BranchTrampoline.h`, `skse64\skse64\skse64\GameExtraData.h`, boost from triplet `x64-windows-rel-static-143`. **The framework is alive on the author's machine in 2026 and still diverging** (`BranchTrampoline.h` moved into `ext/`). |
| IED 1.7.4 DLL strings | linker 14.38, assert paths `ext/BSTSmartPointer.h`, `ext\BSTask.h`, `ext\BranchTrampoline.h` - the last two are not in the 2022 mirror and not direct IED includes (transitive growth). |
| `SlavicPotato/OpenAnimationReplacer-IEDConditionExtensions` (2023-08-19) | **carries `src/API/PluginInterfaceBase.h`, `PluginInterfaceSDS.h` (with `SDSPlayerShieldOnBackSwitchEvent`), `PluginInterfaceIED.h`** - the author's own copies, CommonLib-typed (`RE::Actor*`). Recovered into `records/.../recovered-*.h`. Licence of that repo is GPL-3.0 with the modding/linking exceptions; the same interface is in `SlavicPotato/SimpleDualSheath` `SDS/PluginInterface.h` (`recovered-SDS-PluginInterface.h`). |

**Recovered: 3 of 54 (the plugin-interface trio). Reconstruct: 51.**

### D. Build attempt (scratch worktree, compile-only)

Setup: `git worktree add --detach C:\Users\danjo\source\repos\_ied_feas_scratch master` (ied-dev `d8e9d33`) with the staged branch's working-tree `.vcxproj` (which only rewires include/lib paths to vcpkg, forces `common/IPrefix.h`, and turns `ConformanceMode` off); scratch copy of our framework fork plus junctions to `imgui`/`assimp`/`xbyak` and a copy of `bullet3/src`; `SolutionDir` pointed at that tree; `/t:ClCompile`, config `Release MT Post 629 143`, VS 2022 17.14 (MSVC 14.44.35207), vcpkg static boost 1.92 / assimp / DirectXTK / tbb already present. 54 empty `#pragma once` stubs for the missing files. MSBuild iterations (`msbuild-iteration-N-errors.txt`):

1. `wrl/def.h`: `NTDDI_VERSION` undefined -> added `/D_WIN32_WINNT=0x0A00 /DNTDDI_VERSION=0x0A000000`. `NiTransform::noinit_arg_t` undeclared -> **skse64 patch drift**: the 2023 tree added `noinit_arg_t` constructors to `NiPoint3`/`NiTransform`; patched into the scratch copy. bullet3 `btVector3`/`btMatrix3x3`/`btQuaternion`: 50 `__m128` operator errors.
2. (mis-run, stubs path mangled)
3. Overlaying bullet headers by include order fails (`btScalar.h` relative includes) -> switched to a full `bullet3/src` copy with the author's `sp-edits` branch headers (`SlavicPotato/bullet3` `sp-edits` `76ae9dbd`, 2 commits touching exactly `btVector3.h`/`btMatrix3x3.h`/`btQuaternion.h`/`btQuadWord.h`/`btTransform.h`...).
4. bullet errors unchanged with `sp-edits`. Cause: IED's vcxproj defines `BT_NO_SIMD_OPERATOR_OVERLOADS`, so bullet needs `__m128` operators from elsewhere; DirectXMath's live in `namespace DirectX` and nothing in IED or our framework opens it before the bullet includes. The author's 2023 `common/IPrefix.h` or `ext/` evidently does. Scratch shim `stubs/skmp_shim.h` (force-included, `using DirectX::operator*` etc.) cleared all 50 (`scratch-skmp_shim.h`).
5. `/permissive-` (the author's real setting) breaks the **2022 framework** in 111 places (`stl::underlying`, qualified member names, two-phase lookup) - confirms why the staged branch had turned conformance off; kept `/permissive`.
6. `version.h` includes bare `<skse_version.h>`; 2022 layout only has `skse64_common/skse_version.h` -> shim.
7. `pch.h:160` `IPluginInfo<stl::fixed_string>`: **`IPluginInfo` became a class template** in the 2023 framework; ours is a class -> alias shim.
8. **`pch.cpp` compiles** (169 MB pch). First real TU `Common/VectorMath.cpp` fails on `NiMatrix33::GetColMM`, `NiPoint3::GetMM` (more skse64-patch drift).

Full census (direct `cl.exe /MP /Yu"pch.h"` over all 409 non-pch sources with the same flags; `compile-census-2026-09-10.txt`):

| metric | value |
|---|---|
| translation units | 410 (409 + pch) |
| compiled clean (`.obj` produced) | **27** (pch + 26 leaf UI/input/D3D files) |
| failed | 382 |
| unique error lines | 32,852 across 210 files |
| top codes | C2039 6,895 · C2061 3,813 · C2614 2,368 · C3615 2,314 · C3861 2,253 · C2064 2,075 · C2065 1,717 |

Most-hit missing symbols (each is one reconstruction item; the count is C2039 "not a member" lines, i.e. how much of IED depends on it): `luid_tag`/`ILUID` 4,430 (C2065/C3861) · `stl::boost_vector` 897 · `stl::flat_set` 700 · `stl::boost_container_allocator` 597 · `RE::Sky` 482 · `IED::Data::configFormSet_t::contains` 392 (cascade from `flat_set`) · `stl::smart_ptr` 391 · `stl::unordered_map` 385 · `stl::map` 242 · `stl::boost_unordered_map` 214 · `stl::vector` 210 · `stl::fixed_string_less_equal_ptr` 205 · `stl::intrusive_ref_counted` 201 · `NiMatrix33::init_angle_extrinsic` 161 · `NiMatrix33::SetEulerAnglesExtrinsic` / `SetEulerAnglesIntrinsic` 159 each · `stl::list` 159 · `stl::flag_bf` 107 · `stl::flat_map` 67 · `stl::fixed_string::make_tuple/make_hash` 66 · `RE::WeaponAnimationGraphManagerHolderPtr` 37.

**New finding the earlier passes did not have: the 23 "present" `ext` headers and the vendored skse64 patch have drifted too.** Members IED uses that our 2022-based copies lack (census, non-`stl`, non-IED): `NiMatrix33::init_angle_extrinsic/SetEulerAnglesExtrinsic/SetEulerAnglesIntrinsic/GetColMM`, `NiPoint3::GetMM`, `NiPoint3/NiTransform::noinit_arg_t`, `Events::ThreadSafeEventDispatcher`, `RE::TESWeather` (our reconstructed `TESWeather.h` shape), `TESObjectCELL::CellCoords`, `Actor::GetBiped1/GetSkin/GetCurrentLocation/IsPlayerTeammate/GetActorBase/GetActorValue`, `TESNPC::GetShield/Body/Head/HairBipedObject`, `TESRace::Data::bodyObject`, `TESObjectWEAP::Flag/Flag2/firstPersonModelObject`, `NiAVObject::AsNode`, `IAL::Address<>::get`, `StringCache::Ref::empty`, `Game::g_frameTimer`, `Game::IsAnyMenuOpen`, `hook::check_dst5`, `SKSEPluginVersionData::kVersionIndependentEx_None`, `RE::BSTArray`, `RE::BSSimpleList`, `RE::ModelLoadParams/ModelEntryAuto` (`Model.h`), `IPluginInfo` template, `skse_version.h` location, the `__m128` operator source, `ActiveEffect::Flag`, `RE::ACTOR_VALUE_MODIFIER`. Roughly **40 more surfaces** beyond the 54 files. Third-party drift as well: `ImGui::SeparatorText`, `ImGuiStyle::SeparatorText*` need imgui >= 1.89.5; the author's `SlavicPotato/imgui` fork on GitHub is 1.86 WIP (2021-12-10) and the local `imgui/deployment/a/imgui.vcxproj` IED references is untracked (previous session's reconstruction), so the author's real imgui is private too.

Nothing from the scratch build was deployed. The worktree `_ied_feas_scratch` can be removed with `git worktree remove`.

### E. Runtime hazards, measured

- **Address Library format 5.** IED's bundled `ext/versiondb.h` `Load()` calls `Load(2, ...)`; our fork already carries `LoadV5` (commit `0cb94dc`: format-5 header 4x`int` version, 64-byte module name, `ptrSize`, `dataFormat`, `offsetCount`, dense `uint32` array indexed by id). No further change needed there.
- **IED's own address ids against `versionlib-1-7-104-0.bin`** (format 5, 565,759 slots): IED uses 76 `IAL::Address<T>(se, ae)` sites, 75 distinct pairs; 15 are SE-only (`ae = 0`); **all 60 AE ids exist in the 1.7.104 library**; the framework's own 130 pairs also all exist (`ied-address-ids-se-ae.txt`, `framework-address-ids-se-ae.txt`). Presence proves the id is mapped, not that the hooked bytes still match; IED validates hook sites at install (`IAL::HasBadQuery`, `hook::check_dst5`) and a validation failure returns false from `SKSEPlugin_Load`, which is exactly the crash precondition below.
- **Shared-pool `VirtualFree`.** IED requests both branch and local trampolines (`skse.h`: `kTrampoline`, `TrampolineID::kBranch/kLocal`). With the 2022 `ISKSE.h:229-238` path (`AllocateFromBranchPool/LocalPool` then `BranchTrampoline::SetBase`), a `Load` failure after `CreateTrampolines` lets the static destructor `VirtualFree` SKSE's pool (`records/upstream-issues/sse-build-resources-trampoline-setbase-free.md`). Our fork's `a63a917` (`m_owned`) closes that for any rebuild done on our fork. The shipped 1.7.4 DLL was built against `ext\BranchTrampoline.h` (a 2023 rewrite we do not have), so whether the official binary has the same defect is [unverified]; the withdrawn overlay stays withdrawn regardless.
- **Save data.** IED serialises with boost::serialization (`SKSE_ENABLE_BOOST_SERIALIZATION`) through the missing `stl_boost_serialization_containers.h` and `ISerializationBase`; a reconstruction that changes any container's archive layout silently invalidates or corrupts every IED co-save. This is the corruption-class risk, not a compile risk.

## Findings per header class

| class | files | recovered | reconstruct from | risk |
|---|---|---|---|---|
| plugin interface | 3 | 3 | - | none |
| `stl_*` utilities | 14 (+ drift in `StringCache.h`, `stl_containers.h`, `Events.h`) | 0 | IED usage; boost/STL underneath (44 members) | low; serialization-layout risk for `stl_boost_serialization_containers.h` |
| SKSE plumbing + LUID | 7 | 0 | IED usage + SKSE `PluginAPI.h` | low-medium (`ILUID` is pervasive; its persistence semantics must be inferred) |
| engine structures | 30 (+2 skse64) | 0 | CommonLibSSE-NG layouts transplanted into skse64 types; ~8 engine functions need address ids + signatures we do not have (`BackgroundProcessThread::QueueTask`, `Sky::GetSunPosition`, `GetCurrentWeatherHalfPct`, `ShadowSceneNode::CreateAndAddLight/QueueAddLight/UnkQueueBSLight`, `WeaponAnimationGraphManagerHolder::Create`, `GarbageCollector::QueueBehaviorGraph/QueueForm`) | **high**: an off-by-one field is memory corruption, not a compile error |
| skse64 patch + present-header drift | ~40 members | 0 | IED usage; most are accessors/math, ~10 need offsets/ids (`Actor::GetBiped1/GetSkin/GetCurrentLocation`, `TESObjectCELL::CellCoords`, `TESRace::Data::bodyObject`, `TESObjectWEAP::firstPersonModelObject`) | medium-high |
| third-party forks | imgui (private >= 1.89.5 fork + `deployment/a` project), bullet3 `sp-edits` (recoverable), `__m128` operator source | bullet3 | imgui: re-port IED's UI to upstream imgui | medium |

## Estimate

Hours are expert-engineer estimates, not measurements. IED is 143,765 lines in 1,011 files (410 TUs); the framework fork is 19,949 lines of `ext/`.

**Route A - revive IED on our reconstructed framework**

| step | hours |
|---|---|
| `stl_*` layer, 44 members + `fixed_string` extensions + `Events.h` dispatcher drift | 24-40 |
| `ILUID`/`luid_tag` + SKSE messaging/serialization handlers + `ISerializationBase` | 12-20 |
| plugin interface (recovered, retype to skse64) | 1-2 |
| skse64-patch and present-header drift (~40 members; ~10 need ids/offsets) | 24-48 |
| 30 engine headers transplanted from CommonLibSSE-NG, member-by-member | 60-110 |
| ~8 engine functions without a public signature/id (RE work in a disassembler against 1.7.104) | 24-60 |
| imgui >= 1.89.5 re-port of IED's UI, bullet3 `sp-edits`, project files | 8-16 |
| link, address/hook validation on 1.7.104, first stable in-game run, co-save round-trip | 24-48 |
| **total to a first playable build** | **180-340** |

Plus an open-ended tail: every layout guess that is wrong shows up as a crash or a corrupted co-save in play, not at compile time; and the result is a permanent private fork of a 144k-line codebase whose author keeps building against a framework we will never see (SDS 1.5.9 proves the tree is still moving in 2026). A cheaper checkpoint exists - about 40 hours gets the `stl_*`/LUID/SKSE layers done and leaves only the engine layer - but it does not change the end state.

**Route B - own plugin for #36 on CommonLibSSE-NG**

Scope is what #36 needs, not what IED offers: attach each carried weapon (and the Walking Stick staff-in-hand rule) to the XPMSSE skeleton nodes Simple Dual Sheath does not already cover, per actor, driven by inventory/equip events, with a JSON placement table and co-save of per-actor overrides; no ImGui editor, no I3DI viewport, no bullet physics, no conditions engine. CommonLibSSE-NG 6.7.1 (2026-08-26) has `IDDB::load_v5` and this repo already ships 1.7.104 natives on it (BTPS, CNO, CDF in `records/source-builds/`).

| step | hours |
|---|---|
| skeleton/node attach + detach on equip/unequip/inventory events (the part SDS does for the left hand) | 20-30 |
| placement table (node, transform per weapon type; XPMSSE style-fitting), Walking Stick staff rule | 12-20 |
| per-actor persistence (SKSE co-save) + reload | 8-12 |
| NPC coverage, loading-screen/cell-change robustness, SDS interface handshake (`SKMP_GetPluginInterface`, recovered header) | 12-20 |
| in-game verification passes | 12-20 |
| **total to a first playable build** | **64-102** |

## Recommendation: Route B

1. Route A's cost is dominated by re-deriving a private framework that is still changing; the 1.7.4 binary already names two headers we would not even know to write, and SDS 1.5.9 shows the tree kept moving into 2026. We would be maintaining a guess forever.
2. The failure mode of route A is the one the user's rules forbid tolerating: silent memory-layout errors and co-save corruption in a live modlist. Compile success proves nothing here.
3. #36 needs a fraction of IED's surface. Route B lands on a maintained, format-5-capable library the repo already builds on, stays on the modern stack, and can be published and upstreamed. It is also the only route that does not depend on the author.
4. Route A is not dead, it is the author's to unblock: IED is MIT and the interface headers are already public; a request to SlavicPotato to publish `ext/` (or a 1.7.x IED build) converts route A from 180-340 hours of guessing into a few days of porting. That ask is the user's to send (#94 unpark trigger unchanged).

Decision needed on #94: approve route B as the #36 foundation (new scoped issue), keep #94 held pending the author, and close #201's AllGUD evaluation as superseded or keep it as the DLL-free fallback.
