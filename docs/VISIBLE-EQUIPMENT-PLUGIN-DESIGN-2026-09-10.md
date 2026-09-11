# EnsrickEquipmentDisplay: the #36 rules layer and Walking Stick staff parity

Proposal for phases 3+ of #269. Date: 2026-09-10. Parent: **#269** (Build our own equipment display framework with dual sheath). Scope owner of the rules: **#36**. Staff visual: **#270**. Superseded: #272 (duplicate of #269, closed), #94 (IED revival, closed), #201 (AllGUD).

**Name.** The framework tree already declares the plugin-name string `EnsrickEquipmentDisplay` (`CMakeLists.txt:55` `NAME "EnsrickEquipmentDisplay"`, `src/main.cpp:43`, `src/Settings.cpp:44` for the ini file name). This document uses that string. NAME_TBD: the user names his mods and may still rename it; the string appears in exactly those three places plus the log and ini file names.

**Ownership.** The framework tree `skyrim-tools-source/EnsrickEquipmentDisplay` (local git, no remote; last commit `662d82f` 2026-09-10 14:53:06 -0500 "Record the phase 2 DLL hash"; commits carry `Claude-Session: https://claude.ai/code/session_017afAzKKUN6pCcCNMm7RbAj`) belongs to the session that opened #269 (GitHub author Ensrick, 2026-09-10T17:19:26Z). Nothing in that tree was edited, built or committed for this document; every reference below is read-only. This is a proposal that the tree's owner applies.

Receipts are file paths with line numbers. Prior-art aliases:

| Alias | Path |
|---|---|
| EED | `skyrim-tools-source/EnsrickEquipmentDisplay/` at `662d82f` (the framework) |
| IED | `skyrim-tools-source/ied-dev/ImmersiveEquipmentDisplays/IED/` (`master` d8e9d33), behaviour and schema reference only |
| SDS | `gh api repos/SlavicPotato/SimpleDualSheath` (`SimpleDualSheath/SDS/`), behaviour reference only |
| OAR-IED | `gh api repos/SlavicPotato/OpenAnimationReplacer-IEDConditionExtensions` (`src/`), behaviour reference only |
| OAR | `skyrim-tools-source/OpenAnimationReplacer-1.7.104/src/` (our 1.7.104 build, 99f140e; Ersh, not excluded) |
| NG | `skyrim-tools-source/CommonLibSSE-NG-6.7.1/include/` (70c1acd, 6.7.1) |
| WS | Walking Stick 1.1.1 (Nexus 120966, file 508070, fetched through the Nexus API; contents in 5.8) |

`docs/EXCLUDED_AUTHORS.md` (SlavicPotato, 2026-09-10, commit 985c074) is binding: IED, SDS and OAR-IED were read for **behaviour and on-disk schema only**; nothing is copied. Section 9 records what was studied and what each finding became.

## 1. Goals: the rules, verbatim from #36

From the #36 comment of 2026-09-02 (user, verbatim as recorded):

> 1. **Weapons need a body slot.** The player can only pick up a weapon if there is a slot on their person for it, and **every weapon in inventory is displayed on the body**. Inventory weapon count == visible weapon count, no hidden carry.
> 2. **One exception: up to 2 daggers in a backpack**, treated as packed/hidden.
> 3. **Quest items are NOT exempt** - reversing the earlier position. Reason, in his words: a quest item stops being a quest item once the quest ends, which would leave the player carrying an item that violates the slot rules with no way to have consented to it.
> 4. **Be aggressively limiting on carry generally.**

From the later 2026-09-02 comment (two tiers):

> | **On the person** | Weapons and worn gear | Every weapon needs a body slot and is **displayed on the body**. Exception: up to 2 daggers packed in a backpack. |
> | **Secondary storage** | Crafting and alchemy materials, in quantity | Exists precisely so material accumulation is possible under aggressive carry limits. **Armor and weaponry capped** - amount TBD. |

From the 2026-09-10 staff rule (user quoted):

> *"I hate staves on the back, so I want walking stick so that if the player has a staff equipped, it is always in hand. The idea for my 'always display equipment mod' is that staves must always be equipped, since you wouldn't strap it to your back. This means it must always either be off-hand or in the primary hand if you have one, otherwise, it goes into the long-term storage. This makes having a staff a commitment to using it, unequipping it moves it into long term storage."*
>
> | A staff has no on-body storage slot | It occupies a hand (off-hand, or primary if no off-hand) or it is not on the person at all |
> | Unequipping a staff | Moves it straight to **secondary (long-term) storage**, not the pack |
>
> **Polearms are excluded from this list** as a category: *"We're not including polearms to keep things more simple and viable."*

#270 (Walking Stick): *"shown only while the staff is actually equipped and not swimming/sitting/riding"*; the mod page's own rule: *"The weapons will only be displayed on the hands when/if: The weapon is actually equipped. Your character is not swimming, sitting, riding or using a furniture."*

Goals of the rules layer, in priority order: G1 every governed inventory weapon displayed at a stable per-class body slot; G2 pickups beyond the slots refused at the source with a HUD line, never a dialog, and reconciled when a path cannot be pre-empted; G3 the two packed daggers; G4 the staff in a hand with WS's placement and animations, and to secondary storage on unequip; G5 log-only, popup-free, derivable state.

## 2. Scope split with #269

#269's own phases (EED `docs/DESIGN.md` "Phases"): 0 it loads; 1 node inventory; 2 dual sheath (left-hand weapon and staves sheathed, **the point at which Simple Dual Sheath comes out**); 3 standard slots (shield on back, bow, ammo, torch); 4 custom displays and conditions; 5 editor. The SSE Display Tweaks replacement is its own track. All of that is out of scope here and only referenced.

This proposal adds four **rules phases R1-R4** (section 13). They depend on phase 2 (the display backbone exists and SDS is gone) and are independent of phases 3-5. Nothing here needs the SDS interface: the framework replaces SDS, so the "SDS handshake" from the original brief is dropped; the only SDS-related code is a one-line startup guard that logs if `SimpleDualSheath.dll` is still loaded (5.6).

Two places where the rules change what phase 2 already does:

- **Staves on the back are not wanted.** Phase 2 displays both staves sheathed on `WeaponStaff` / `WeaponStaffLeft` (EED `src/Display/SlotTable.cpp:44-48`, `DisplayManager.cpp:216-221`, ini `[DualSheath] Staves=1`). Under the staff rule a sheathed staff is carried in the hand instead (R3). Proposal: keep the `Staves` key for the framework's own use but let R3 own staff display, with `Staves` defaulting to 0 once R3 lands.
- **Equipped left-hand weapons occupy a body slot.** The dual-sheath display and the rules-layer display are the same thing seen from two sides: the left-hip sword phase 2 shows is `hip.left.1h` in the roster (5.1). R1 unifies them so one code path decides what hangs where (4.1).

Non-goals: polearms; IED's SKMP interface (5.9); other runtimes; MCM (#39: INI/JSON are the reproducible source of truth); first person (5.7); the secondary-storage system itself (the rules layer needs one `Deposit` entry point, decision D1).

## 3. The framework as it stands (what the rules plug into)

Read from EED at `662d82f`:

| Piece | Facts | Lines |
|---|---|---|
| Entry | `SKSEPluginLoad`: `SKSE::Init`, own log `EnsrickEquipmentDisplay.log` via `logger::log_directory()`, `Settings::Load()`, messaging listener; `OnMessage` handles **only** `kDataLoaded` -> `EED::InstallHooks()` | `src/main.cpp:26-38, 40-70` |
| 3D hook | `Load3DHook<T>` writes vfunc `0x6A` on `RE::Character` and `RE::PlayerCharacter`; thunk calls original, then `SkeletonDump::OnActor3DLoaded`, `WatchGraphs(actor)`, `DisplayManager::OnActor3DLoaded(ref, root)`; every handler is `try/catch(...)` | `src/Hooks.cpp:77-116` |
| Equip sink | `EquipWatcher : BSTEventSink<TESEquipEvent>` -> `DisplayManager::OnEquipChanged(actor)`; registered on `ScriptEventSourceHolder` in `InstallHooks()` | `src/Hooks.cpp:118-147, 149-160` |
| Drawn state | `GraphWatcher : BSTEventSink<BSAnimationGraphEvent>` matching nine tag strings -> `DisplayManager::OnWeaponStateChanged` (listed as risk 1 in `CHANGELOG.md`) | `src/Hooks.cpp:11-62` |
| Display manager | `ActorState { std::array<Attached,2> hands; bool weaponDrawn }` keyed by `FormID`; `Refresh(actor)` computes per hand `wanted = weapon && NodeFor(type,hand) && (hand==Left || type==Staff) && (type!=Staff || settings.staves)`, reuses an attached copy if `attached.item == wantedItem`, else `DetachOurs`, `FindSlotNode` (primary then alternates, logged), `BuildDisplay`, attach with identity transform, `SetAppCulled(drawn)`, `UpdateDownwardPass` | `src/Display/DisplayManager.h:14-46`, `DisplayManager.cpp:196-276` |
| Model source | `BuildDisplay(actor, weapon)`: clone the actor's built biped part when `BipedAnim::objects[i].item == weapon` (inherits texture swap and shaders), else `BSModelDB::Demand` bare then `meshes\`-prefixed, warn when the record carries alternate textures | `DisplayManager.cpp:96-158` |
| Marker | every copy is named `"EED " + "Left"/"Right"`; `IsOurs` / `DetachOurs` recover stale copies by prefix without bookkeeping | `DisplayManager.cpp:12-46` |
| Slot table | constexpr `SlotEntry{type, hand, node, alternates}` from the measured inventory; `NodeFor`, `AlternatesFor`, `WeaponTypeName` | `src/Display/SlotTable.h`, `SlotTable.cpp:11-59` |
| Node inventory | 543 nodes, 71 attach candidates with local translate/scale, measured from XPMSSE's `skeleton.nif` by `tools/skeleton_inventory.py`; the right/left pairs are mirrors (`WeaponSword` x=-11.891, `WeaponSwordLeft` x=+11.892) | `docs/NODE_INVENTORY.md` |
| Settings | `[Log] Level/FlushLevel`, `[DualSheath] Enable/PlayerOnly/Staves`, `[Diagnostics] DumpSkeleton*`; optional ini, defaults always valid, no MessageBox path | `src/Settings.h`, `src/Settings.cpp` |
| Build | CMake + NG 6.7.1 as `extern/CommonLibSSE-NG` symlink, `USE_ADDRESS_LIBRARY` (no runtime ceiling), `/W4` (no `/WX`), presets, `build_1_7_104.cmd`; no CTest, no CI, no source-build receipt, no serialization, no container-change sink, no pickup hooks | `CMakeLists.txt`, `CMakePresets.json`, `CHANGELOG.md` |

Not run in game yet (`CHANGELOG.md` 0.2.0 "Not verified in game"); DLL sha256 `b03a776e24feed796805ee62fdced7f054706d3e516f44ce285081b669d1e205`.

## 4. Integration contract: hook points and data the framework must expose

Each item names the framework file it lands in, what the rules layer calls or provides, and why. The rules layer lives beside the display code (proposed `src/Rules/`), owns its own sinks and hooks, and never touches the `Load3D` thunk, the model builder or the marker scheme.

| # | Framework change | Data / call | Why |
|---|---|---|---|
| H1 | `DisplayManager` generalised from two hands to N slots: `struct DisplayRequest { std::string_view slotId; RE::TESBoundObject* item; std::uint16_t uniqueId; std::string_view node; std::span<const std::string_view> alternates; RE::NiTransform offset; bool cullWhenDrawn; }` and `void Apply(RE::Actor*, std::span<const DisplayRequest>)` that diffs against `ActorState` (now a map `slotId -> Attached`) using the existing attach/detach/cull code; copy names become `"EED " + slotId` | `DisplayManager.h:14-46`, `DisplayManager.cpp:196-276` | the phase-2 policy ("left hand plus staves") and the rules policy ("every slot of the roster") both produce request lists; one applier means one owner of the node tree, which is #269's founding principle (`docs/DESIGN.md` "Why one plugin") |
| H2 | `Refresh(actor)` calls a policy first: `Rules::Policy::Plan(actor) -> std::vector<DisplayRequest>` when `[Rules] Enabled=1`, else the current two-hand plan | `DisplayManager.cpp:196-221` | the three existing entry points (`OnActor3DLoaded`, `OnEquipChanged`, `OnWeaponStateChanged`) keep their signatures; the rules layer only changes what is wanted |
| H3 | `BuildDisplay` unchanged and reachable (`Display/Attach.h`); it already handles the two model sources the rules need | `DisplayManager.cpp:96-158` | unequipped weapons have no biped part, so they take the `BSModelDB::Demand` path; the alternate-texture warning becomes R4's swap application |
| H4 | `SlotTable` becomes the placement table keyed by slot id (section 6): `const SlotDef* Slot(slotId)`, `NodeFor(slotId, WEAPON_TYPE)`, `Alternates(slotId)`, `Offset(slotId)`; `FindSlotNode` takes (node, alternates) | `SlotTable.h`, `SlotTable.cpp:11-59` | the roster (5.1) is the carry limit; it must be one table, not two |
| H5 | `OnMessage` forwards `kPostLoad` (OAR registration must happen there or earlier: OAR `src/API/OpenAnimationReplacerAPI-Conditions.h:95`), `kPostPostLoad` (module presence guards), `kPostLoadGame` and `kNewGame` (rebuild the player's board) | `src/main.cpp:26-38` | today only `kDataLoaded` is dispatched |
| H6 | `InstallHooks()` also installs the rules layer's sinks and hooks: `BSTEventSink<TESContainerChangedEvent>` (`RE/T/TESContainerChangedEvent.h:11-16`), `BSTEventSink<TESFurnitureEvent>` (`RE/T/TESFurnitureEvent.h:12-21`), `SKSE::GetActionEventSource()` (`SKSE/API.h:37`, `ActionEvent::Type::kEndDraw = 8`, `kEndSheathe = 10`), and two `PlayerCharacter` vfunc hooks: `PickUpObject` 0xCC (`RE/A/Actor.h:419`) and `AddObjectToContainer` 0x5A (`RE/A/Actor.h:322`) | `src/Hooks.cpp:149-160` | pickup refusal (5.2) and the drawn-state source SDS used (`SDS Controller.cpp` `ReceiveEvent(const SKSEActionEvent*)`), offered as the fix for `CHANGELOG.md` risk 1: the graph-tag sink stays as fallback |
| H7 | serialization: `SKSE::GetSerializationInterface()->SetUniqueID('EEDR')`, `SetSaveCallback/SetLoadCallback/SetRevertCallback` wired in `SKSEPluginLoad`, bodies in `src/Rules/CoSave.cpp` | `src/main.cpp:40-70`; NG `SKSE/Interfaces.h:94-135` | 5.7 |
| H8 | `Settings` gains `[Rules]`, `[Staff]`, `[Compat]` and `DumpPlacements` (section 7) | `src/Settings.h/.cpp` | |
| H9 | placement hints: `Rules::PlacementHints::Set(actorFormID, gearNodeID, hint)` / `Get(...)` (a read-mostly map under a shared mutex; IED keeps the same thing out of its global lock for exactly this reason, `GearNodeData.h:8`) | new `src/Rules/PlacementHints.h` | the OAR conditions (5.8) read it per frame; the framework's phase 3 shield/bow nodes may `Set` their own hints for OAR parity |
| H10 | `IStorage::Deposit(RE::Actor*, RE::TESBoundObject*, RE::ExtraDataList*, count)` with the ESL stash as the first implementation | new `src/Rules/Storage.h` | 5.5, decision D1 |
| H11 | build conventions: a CTest target for the rule engine, `/WX` on the plugin target, a CI workflow with the NG revision and vcpkg baseline pinned, and a `records/source-builds/` receipt per build | `CMakeLists.txt`, new `.github/workflows/` | the sibling first-party plugins have all four; the retired #272 scaffold (section 14) proved the recipe on this NG revision |

## 5. Rules layer design

### 5.1 Rule engine (pure, no game types)

A header with no `RE::` dependency so a plain executable tests every clause. The retired scaffold carried a working draft with a 52-check test (section 14); the API to lift into `src/Rules/SlotRules.h`:

```cpp
enum class WeaponClass { kOneHanded, kDagger, kTwoHanded, kBow, kCrossbow, kStaff, kPolearm, kOther };
WeaponClass Classify(std::uint32_t engineWeaponType, bool polearmKeyword);  // WEAPON_TYPE 0..9
bool IsGoverned(WeaponClass);              // false for kPolearm (rule 5) and kOther
bool ExemptFromSlotRules(bool isQuest);    // always false (rule 3), pinned by a test
enum class SlotKind { kBody, kHand, kBackpack };
struct SlotDef { std::string_view id; SlotKind kind; std::uint32_t acceptsMask; };
class SlotBoard {                          // one per actor, roster from the placement table
  Verdict CanAccept(WeaponClass) const;    // kAccept | kRefuseNoSlot | kNotGoverned
  std::optional<std::size_t> Place(WeaponClass, Item);  // first free accepting slot, roster order
  std::size_t Remove(Item);
  std::size_t VisibleCount() const;        // kBody + kHand
  std::size_t PackedCount() const;         // kBackpack
  bool Invariant() const;                  // carried == visible + packed && packed <= 2
};
UnequipDestination OnUnequip(WeaponClass); // kStaff -> kStorage, other governed -> kBodySlot
std::optional<Hand> StaffHand(bool leftFree, bool rightFree);  // off-hand first
```

Classes from the engine `WEAPON_TYPE` numbers (`RE/W/WeaponTypes.h`: 1 sword, 3 axe, 4 mace -> `kOneHanded`; 2 -> `kDagger`; 5, 6 -> `kTwoHanded`; 7 -> `kBow`; 9 -> `kCrossbow`; 8 -> `kStaff`; 0 and unknown -> `kOther`); polearms have no engine type and are detected by keyword.

Default roster, in placement order (the order is the policy: body before backpack, off-hand before primary):

| Slot | Kind | Accepts | Skeleton node (measured, EED `docs/NODE_INVENTORY.md`) |
|---|---|---|---|
| `hip.right.1h` | body | one-handed | `WeaponSword` / `WeaponAxe` / `WeaponMace` by type |
| `hip.left.1h` | body | one-handed | `WeaponSwordLeft` / `WeaponAxeLeft` / `WeaponMaceLeft` |
| `hip.right.dagger` | body | dagger | `WeaponDagger` |
| `hip.left.dagger` | body | dagger | `WeaponDaggerLeft` |
| `back.2h` | body | two-handed | `WeaponBack`, `WeaponBackAxeMace` (same transform (12.549, -6.345, 28.651), so one physical slot) |
| `back.bow` | body | bow, crossbow | `WeaponBow`, `WeaponCrossBow` (same transform (-3.558, -10.578, 2.465)) |
| `hand.left` | hand | staff | `NPC L Hand [LHnd]` + WS offset (5.8) |
| `hand.right` | hand | staff | `NPC R Hand [RHnd]` + WS offset |
| `backpack.dagger.1/2` | backpack | dagger | none (hidden) |

Six body slots is the default carry limit for governed weapons. Ankle and back-hip dagger nodes exist on the skeleton and can be added through `placements.user.json`; they are not defaults because rule 4 wants aggressive limits. Equipped weapons hold their body slot too: a sheathed sword is on the hip, so it needs the hip. That is why phase 2's left-hip display and `hip.left.1h` are the same object (section 2).

### 5.2 "Limit = slots": pickup gate and reconcile

| Path into the inventory | Interception | Behaviour |
|---|---|---|
| ground pickup | `PlayerCharacter::PickUpObject` vfunc 0xCC (H6) | `CanAccept` before the engine; `kRefuseNoSlot` -> do not call the original, `RE::SendHUDMessage::ShowHUDMessage("No free slot for <name>")` (`RE/S/SendHUDMessage.h:9`, the HUD queue, not a dialog), one info log line |
| container, corpse, vendor, gift menus | `PlayerCharacter::AddObjectToContainer` vfunc 0x5A with a non-null `a_fromRefr` (H6) | same verdict; the item stays in its source |
| script `AddItem`, quest rewards (no source) | same hook, `a_fromRefr == nullptr` | accepted, then the reconcile step decides (decision D2; interim: route to secondary storage with a HUD line) |
| anything missed | `TESContainerChangedEvent` sink, player as `newContainer`, governed weapon, no free slot | move back to `oldContainer` if it still resolves, else drop at the player's feet (`TESObjectREFR::RemoveItem` with the dropping reason, `RE/T/TESObjectREFR.h:266`); HUD line + log line |

The board is rebuilt from `TESObjectREFR::GetInventory` (`RE/T/TESObjectREFR.h:404`) on `Load3D`, `kPostLoadGame`, `kNewGame` and after every container change, so the verdict never depends on stale bookkeeping.

### 5.3 The two packed daggers

Two `kBackpack` entries accepting only daggers, ordered after the body dagger slots, so daggers pack only when the hips are full; packed daggers get no `DisplayRequest` (hidden) and count toward `CarriedCount` but not `VisibleCount`. R2 ships them unconditionally; gating on a worn backpack item is decision D4.

### 5.4 Quest items

No exemption exists: `CanAccept` has no quest parameter. `InventoryEntryData::IsQuestObject()` (`RE/I/InventoryEntryData.h:56`) is read only to say so in the log line.

### 5.5 Staff: hand, then storage

`hand.left` then `hand.right` accept staves (`StaffHand`: off-hand first, primary if no off-hand, else refused). A staff pickup succeeds only when a hand is free, and the plugin equips it there (`ActorEquipManager`). On `TESEquipEvent` with `equipped == false` for a staff, `OnUnequip == kStorage` -> `IStorage::Deposit` (H10). The first storage implementation is a stash: a container reference in a holding cell from a one-record ESL shipped with the plugin (one CONT, one CELL, one REFR; decision D1), found with `TESDataHandler::LookupForm` (`RE/T/TESDataHandler.h:62`). Equipping a two-handed weapon while a staff is in the off-hand cannot be represented physically; proposal: it unequips the staff (rule 4, "a commitment"), decision D3.

### 5.6 Gates (hand slots only)

State in NG: `ActorState::IsSwimming()` (`RE/A/ActorState.h:202`), `ActorState::GetSitSleepState()` (`ActorState.h:160`; anything but normal covers sitting, sleeping and furniture use; IED diffs the same fields in `Controller/CachedActorData.cpp:251-332`), `Actor::IsOnMount()` (`RE/A/Actor.h:647`). Wake-ups: `TESFurnitureEvent`, `TESEquipEvent`, the action event. Because swimming and mounting have no reliable script event, actors with an active hand display are polled by a re-queued SKSE task every ~250 ms that diffs the four booleans and toggles culling; O(actors with a staff in hand). While gated the published hint (H9) is 0, so WS's replacers stop matching, which is the behaviour the mod page describes. Startup guard: if `GetModuleHandleA("SimpleDualSheath.dll")` is non-null after phase 2 removed it, log one WARN (double display is the framework's concern, not the rules'); no interface call, no ini read.

### 5.7 First person

The player's first-person skeleton (`TESObjectREFR::Get3D(true)`, `RE/T/TESObjectREFR.h:377`) gets nothing: WS attaches the staff to the third-person hand only (`GP_WalkingStick.json` has no 1p entry), and the body is not rendered in first person. `[Display] FirstPersonStaff=1` is an R4 option to also attach to the 1p hand. Camera state, if needed: `RE::PlayerCamera::GetSingleton()->IsInFirstPerson()` (`RE/P/PlayerCamera.h:141`).

### 5.8 Walking Stick parity and the OAR conditions

**What WS 1.1.1 contains** (zip 188,879 bytes): five IED `NodeOverrides` profiles, `SkeletonExtensions/ExtraGearNodes/GP_WalkingStick.json`, and an OAR pack `Walking Stick/` with `Stick on Left Hand`, `Stick on Right Hand`, `Bladestaff` (idle, walk, equip/unequip `.hkx`, one `config.json` each). Only the staff half is adopted (#270).

**The IED half, decoded against IED's parsers** (behaviour only):

| WS file | Content | Meaning | Ours |
|---|---|---|---|
| `GP_WalkingStick.json` `IEDStaffRighHand` | `parent "NPC R Hand [RHnd]"`, `xfrm_mov.pos [-5.0, 4.5, 11.5]`, `rot [2.001106, 0.196279, -0.367237]`, `placement_id 16` | a hand-parented target node with that transform; `placement_id` is parsed as a plain integer and cast without validation (`Parsers/JSONConfigExtraNodeEntryParser.cpp:28`), an opaque number IED only reports | `hand.right` offset, `hint 16` |
| same, `IEDStaffLeftHand` | `parent "NPC L Hand [LHnd]"`, `pos [1.0, 7.0, 12.5]`, `rot [-2.071184, -0.277077, -0.187825]`, `placement_id 16` | idem | `hand.left` offset, `hint 16` |
| `GP - Walking Stick (Staff).json` | for `WeaponStaff` (`WeaponStaffLeft`): placement override to `MOV IEDStaffRighHand` (`...LeftHand`) with five matches | when all pass, re-parent the gear node and publish the hint (`INodeOverride.cpp:1142-1176`); else reset and publish none (`:1215-1244`) | the `gates` list |
| match `type 12`/`13`, `flags 164` | flags low 5 bits = 4 `Type`, bit 5 `kAnd`, bit 7 `kMatchEquipped` (`ConfigNodeOverride.h:63-69, 98-104`); 12 = `ObjectSlot::kStaff`, 13 = `kStaffLeft` (`ConfigData.h:23-24`) | a staff equipped in that hand | `equipped` |
| `bip 17`, `flags 106` | low 5 bits = 10 `Extra`, `kAnd`, bit 6 `kNot`; 17 = `ExtraConditionType::kSwimming` (`ConfigCommon.h:300`) | not swimming | `!swimming` |
| `flags 102` | 6 `Furniture`, `kAnd`, `kNot` | not using furniture | `!furniture` |
| `bip 29`, `flags 106` | `Extra` not; 29 = `kSitting` (`ConfigCommon.h:312`) | not sitting | `!sitting` |
| `flags 112` | 16 `Mounting`, `kAnd`, `kNot` | not mounting or riding | `!mounted` |

Two hand transforms and five gates; nothing else to carry over. Rotation convention: IED-style Euler values, taken verbatim and confirmed visually at R3 (risk R6).

**The OAR half.** WS's configs (`Stick on Left Hand/config.json`, `Stick on Right Hand/config.json`) use `IED_GearNodePlacementHint` with `"Gear node ID"` 12.0 (left) or 11.0 (right) and `"Weapon placement ID"` 16.0, `IED_GearNodeEquippedPlacementHint` with `"Left hand": false` and 16.0, plus stock OAR conditions (`IsEquipped` on `Campfire.esm|250CA` for the Campfire walking stick, gear node 15 / placement 10). Every custom condition carries `"requiredPlugin": "OpenAnimationReplacer-IEDConditionExtensions", "requiredVersion": "1.0.0.0"`. OAR resolves them by string: `IsPluginLoaded(requiredPluginName, requiredVersion)` against the registry keyed by the **name passed to `AddCustomCondition`** (OAR `src/OpenAnimationReplacer.cpp:1054-1067`, checked at `src/Conditions.cpp:97-121`), then `CreateCondition(conditionName)`; component values are read by component name (`src/BaseConditions.cpp:409-437, 499-509, 534-557`).

Design: at `kPostLoad` (H5) the rules layer registers, through `OAR_API::Conditions::AddCustomCondition` (interface V3; the API header says "Copy this file into your own project", `OpenAnimationReplacerAPI-Conditions.h:1-6, 57`), the six condition names OAR-IED defined with identical component names and order and identical numeric semantics: `IED_GearNodePlacementHint` (Gear node ID, Comparison, Weapon placement ID), `IED_GearNodeEquippedPlacementHint` (Left hand, Comparison, Weapon placement ID), `IED_GearNodeParentName`, `IED_HasEquipSlot`, `IED_IsBoundWeaponEquipped`, `IED_PluginOption`; gear node ids follow IED's numbering (`GearNodeID` 1..18, kStaff 11, kStaffLeft 12; OAR-IED `src/API/PluginInterfaceIED.h:27-48`) including its deliberate staff swap for the equipped-weapon lookup (IED `PluginInterface.cpp` `GetGearNodeIDForItem`: `kStaff -> a_leftHand ? kStaff : kStaffLeft`). The hint for 11/12 is the hand slot's `hint` while its gates pass, else 0 (H9).

The only JSON delta is `requiredPlugin`: a converter `tools/oar_requiredplugin_rewrite.py` (R3) rewrites that one string to `EnsrickEquipmentDisplay` in the four WS `config.json` files (4 KB of text; the `.hkx` animations, GiraPomba's work, untouched). Optional and off by default: `[Compat] OarLegacyPluginAlias=1` also registers the factories under the literal name `OpenAnimationReplacer-IEDConditionExtensions` 1.0.1 so unconverted third-party packs parse; the API takes the name as a plain string, so no DLL rename is involved.

### 5.9 IED public API compatibility: the answer

**No.** The consumer resolves the provider by **DLL file name**: `PluginInterfaceBase::query_interface<T>()` calls `GetModuleHandle(T::PLUGIN_DLL)`, `GetProcAddress(handle, "SKMP_GetPluginInterface")`, then checks `GetUniqueID() == T::UNIQUE_ID` (recovered `records/ied-rebuild-feasibility-2026-09-10/recovered-PluginInterfaceBase.h:34-72`), with `PLUGIN_DLL = "ImmersiveEquipmentDisplays.dll"` and `UNIQUE_ID = 0xBD869D3E87EF7D51` (`PluginInterfaceIED.h:9-10`). Parity therefore means naming our DLL `ImmersiveEquipmentDisplays.dll`, exporting his entry point and reproducing a 9-entry vtable (5 base virtuals, then `GetPlacementHintForGearNode`, `GetPlacementHintForEquippedWeapon`, `GetGearNodeParentName`, `GetPluginOption`; reproducible under MSVC's declaration-order vtables and NG's `RE::BSString`). The sole consumer is OAR-IED, by the excluded author and a 2023-08 pre-format-5 build. What Walking Stick actually consumes is the two conditions by name, which 5.8 provides through Ersh's API with a four-file `requiredPlugin` rewrite. So: no SKMP interface, unchanged animation behaviour.

### 5.10 Co-save

`SKSE::SerializationInterface` (H7). Principle: **the co-save is a cache of decisions, not the source of truth.** The board is derivable from the inventory and the placement table, so a missing or rejected co-save costs only which two daggers were packed and per-actor offset overrides, never correctness (the mitigation for the corruption class IED's boost archives carry, `docs/IED-REBUILD-FEASIBILITY-2026-09-10.md` E).

| Tag | v | Payload |
|---|---|---|
| `SLOT` | 1 | `u32 actorCount (<= 4096)`; per actor `u32 formID` (`ResolveFormID`; unresolvable -> skip, log), `u16 entries (<= 64)`; per entry `u8 slotIdLen, char[]`, `u32 itemFormID`, `u16 inventoryUniqueID`, `u8 flags` (bit0 packed) |
| `STOR` | 1 | `u32 stashRefFormID`, `u16 count (<= 256)`; per item `u32 itemFormID`, `u16 uniqueID`, `u32 originalOwner` |
| `OVRD` | 1 | per actor: `u32 formID`, `u16 count`; per: `slotId`, `float pos[3] rot[3] scale` |

Unknown tag -> skip; newer version -> skip and log once; any length or cap violation -> discard the record and rebuild from inventory (WARN). Revert clears everything. R4's CTest round-trips each record through a buffer and fuzzes truncation.

## 6. Placement table

`SKSE/Plugins/EnsrickEquipmentDisplay/placements.json` shipped, `placements.user.json` merged over it by slot id. Whether the framework keeps the constexpr `SlotTable` and loads JSON as an overlay, or moves entirely to JSON, is its owner's call; the schema is the same either way.

```json
{
  "schema": 1,
  "skeleton": { "expect": { "xpmseVersion": 4.81, "nifSha256": "d922d4a6309672c..." } },
  "slots": {
    "hip.right.1h":     { "node": "WeaponSword",  "byType": { "3": "WeaponAxe", "4": "WeaponMace" } },
    "hip.left.1h":      { "node": "WeaponSwordLeft", "byType": { "3": "WeaponAxeLeft", "4": "WeaponMaceLeft" } },
    "hip.right.dagger": { "node": "WeaponDagger" },
    "hip.left.dagger":  { "node": "WeaponDaggerLeft" },
    "back.2h":          { "node": "WeaponBack", "byType": { "6": "WeaponBackAxeMace" } },
    "back.bow":         { "node": "WeaponBow",  "byType": { "9": "WeaponCrossBow" } },
    "hand.right": { "node": "NPC R Hand [RHnd]", "offset": { "pos": [-5.0, 4.5, 11.5], "rot": [2.001106, 0.196279, -0.367237], "scale": 1.0 },
                    "hint": 16, "gates": ["equipped", "!swimming", "!sitting", "!furniture", "!mounted"] },
    "hand.left":  { "node": "NPC L Hand [LHnd]", "offset": { "pos": [1.0, 7.0, 12.5], "rot": [-2.071184, -0.277077, -0.187825], "scale": 1.0 },
                    "hint": 16, "gates": ["equipped", "!swimming", "!sitting", "!furniture", "!mounted"] },
    "backpack.dagger.1": { "hidden": true },
    "backpack.dagger.2": { "hidden": true }
  }
}
```

`byType` keys are engine `WEAPON_TYPE` numbers. Node names are the measured XPMSSE names (EED `docs/NODE_INVENTORY.md`). Style variants (`...FSM`, `...SWP`, `...NMD`, `...OnBack`) stay alternates, logged when used (EED `SlotTable.cpp:11-30`): the bare node follows whatever RaceMenu style the user picked. `skeleton.expect` is checked once per session against the player's tree (`XPMSE` `NiFloatExtraData` on the NPC root's parent, `skeletonID` `NiIntegerExtraData` on the root, the observable fields IED folds into its signature, `SkeletonID.cpp:29-87`); a mismatch is one WARN.

## 7. Configuration additions to `EnsrickEquipmentDisplay.ini`

| Section | Key | Default | Phase |
|---|---|---|---|
| Rules | Enabled, PlayerOnly, EnforcePickup, ReconcileContainerChanges, PackedDaggers | 0 until R2 is verified, 1, 1, 1, 2 | R1/R2 |
| Staff | Enabled, TwoHandedUnequipsStaff | 1, 1 | R3 |
| Compat | OarConditions, OarLegacyPluginAlias | 1, 0 | R3 |
| Display | FirstPersonStaff, ActionEventDrawnState | 0, 1 | R4 / H6 |
| Diagnostics | DumpPlacements | 0 | R1 |

MCM never required (#39); an MCM, if ever built, edits these files.

## 8. Logging and diagnostics

Same log file as the framework. No MessageBox path in rules code; `SKSE::Init` is already the framework's (its `a_log=true` opens NG's default logger before `SetupLog` replaces it, `main.cpp:40-49`; passing `false` would keep a single sink, the owner's call). Startup summary at info: OAR presence and each condition's registration result, SDS guard, player skeleton identity vs `placements.json`, roster. One info line per decision (attach, detach, refusal, reconcile, deposit); per-event lines at trace. `DumpPlacements` writes each slot's resolved node and world transform for the player, beside the existing `DumpSkeleton`. Refusals also produce a HUD line.

## 9. Prior art: studied, not copied

| Behaviour | Where studied | Became |
|---|---|---|
| attach node naming and re-use | IED `Controller/INode.cpp:136-147, 210-243, 302-307` | the framework's marker prefix, extended per slot (H1) |
| clone via `NiCloningProcess` | IED `Controller/ObjectDatabase.cpp:288-297` | the framework's `CreateDeepCopy` path, unchanged |
| scabbard `scb`/`scbLeft` handling | IED `Controller/IObjectManager.cpp:1643-1700` | R4 scabbard split |
| shadow-scene registration after attach | IED `IObjectManager.cpp:1626-1631`, ids at `IObjectManager.h:273-274` | risk R7: id-based port only if phase 2's visual check shows unlit copies |
| extra gear nodes as CME->MOV chains | IED `ExtraNodes.cpp:53-111`; installed `ExtraGearNodes/00200_VanillaGear.json` | placement table with direct offsets, no MOV synthesis |
| skeleton signature | IED `SkeletonID.cpp:12-88` | `skeleton.expect` (6) |
| placement hint publication | IED `INodeOverride.cpp:1142-1176`, `GearNodeData.cpp:9-21` | H9 |
| public API shape | IED `PluginInterface.cpp`; OAR-IED `Conditions.cpp`, `main.cpp` | 5.8, 5.9 |
| gates | IED `CachedActorData.cpp:251-332`; WS preset matches | 5.6 |
| first person | IED `IFirstPersonState.cpp:11-33` | 5.7 |
| events consumed | IED `Controller.h:44-57`; SDS `Controller.h:39-46` | H6 |
| co-save via boost archives | IED `Controller.cpp:5511-5600` | explicitly not replicated; 5.10 |
| SDS engine-object re-parenting by byte patch | SDS `EngineExtensions.h:98-106`, `EngineExtensions.cpp` | rejected; the framework's clone model stands |
| SDS drawn-state source | SDS `Controller.cpp` `SKSEActionEvent` handler | H6 suggestion for risk 1 |

Had the exclusion not applied, the only IED parts free of the missing framework would have been the recovered interface headers and `INode`'s attach logic (~120 lines); everything else pulls `stl::`, `ITaskPool`, `ObjectDatabase` and the author's skse64 patch. Nothing was taken.

## 10. Risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | layout drift | no byte patches, no raw offsets: three vfunc hooks and script/SKSE events through NG 6.7.1 pinned by commit; each hook install logs its resolved address |
| R2 | co-save corruption | derivable state; versioned, length-checked, capped records; unknown records skipped with a log line; round-trip and truncation tests (5.10) |
| R3 | per-frame cost | event-driven; the only poll is per hand-display actor at ~4 Hz; copies created once per (actor, item); a debug counter logs totals and poll cost every 60 s; cap 64 displays per actor |
| R4 | load order / preload | no preload, no `!` prefix; OAR registration at `kPostLoad` is order-independent |
| R5 | double display | one applier (H1); SDS gone at phase 2; startup guard logs if it is back |
| R6 | rotation convention of WS offsets | [unverified] until the R3 in-game comparison; a data edit if wrong |
| R7 | unlit or unshadowed copies | phase 2's visual check; id-based shadow-scene registration as fallback |
| R8 | scripted adds beyond slots | decision D2; never a silent delete |
| R9 | memory growth | copies released on detach and `Load3D`; totals logged; marker sweeps |
| R10 | `MessageBoxA/W` import via NG `report_and_fail` | never called by rules code; PopupGuard intercepts; NG log-only overlay as in the OAR 1.7.104 build (99f140e) is a hardening candidate |
| R11 | two trees | the #272 scaffold is retired (section 14); one tree, one owner |

## 11. Open decisions for the user

- D1 Secondary storage vehicle for the staff rule: plugin-shipped ESL stash (recommended: one CONT, one CELL, one REFR) vs. the future materials tier.
- D2 Scripted adds with no source when slots are full: refuse (may break quest stages), accept and route to storage (recommended), or accept and drop.
- D3 Two-handed equip while a staff is in hand: unequip the staff to storage (recommended) or refuse the two-handed equip.
- D4 Packed daggers: unconditional two slots (R2 default) or gated on a worn backpack item.
- D5 Name (NAME_TBD; currently `EnsrickEquipmentDisplay`) and final phase numbering of R1-R4 inside #269.

## 12. Test plan

1. **Unit (CTest):** `slot_rules` (rule engine, every clause and the invariant; a 52-check draft exists in the retired scaffold); R1 adds `placement_table` (parses the shipped JSON, rejects malformed entries, resolves `byType`); R3 adds `oar_conditions` (component names and order snapshot vs. WS's JSON); R4 adds `cosave_roundtrip` and `cosave_fuzz`. Requires the CTest target from H11.
2. **Static gates:** `py -3 audit/skse_version_data.py <dll>` PASS; `dumpbin -EXPORTS` lists the three SKSE entry points; a grep gate fails the build if `report_and_fail` or `MessageBox` appears in `src/`.
3. **Preflight:** `py -3 audit/preflight.py` exit 0 before any launch.
4. **Verification launch per phase:** install under a claim, harness launch (`audit/launch_verify.py`), main menu under 60 s, save load, startup summary present with zero `[error]`, skse64.log lists the plugin, no new crash log (`feedback_skyrim_launch_verification_mandate`).
5. **User acceptance:** R1: every carried weapon visible on player and one NPC at its slot. R2: seventh governed weapon refused with the HUD line; two daggers packed. R3: staff in the left hand with WS's idle and walk, hidden when swimming, sitting, riding or on furniture, deposited on unequip. R4: save/load keeps packed choice and overrides.
6. **Determinism:** two clean builds byte-identical (`/Brepro`), recorded in the receipt (H11).

## 13. Phases and hours (rules layer only)

| Phase | Content | Exit | Hours |
|---|---|---|---|
| R1 all inventory weapons at their slots | H1-H4, H8, H11; roster and placement table; board rebuilt from inventory; `DisplayRequest` plan for every governed weapon; `DumpPlacements` | launch verification; user sees every carried weapon at a slot; ini `Rules.Enabled` stays 0 by default until R2 | 16-24 |
| R2 limit = slots | H5, H6 (container sink, pickup and add hooks), reconcile, HUD lines, packed daggers | seventh weapon refused; reconcile proven with a scripted add | 12-18 |
| R3 staff rule + Walking Stick parity | hand slots with WS offsets, gates poll, H9 hints, OAR conditions, converter, H10 storage (D1), D3 | staff in hand with WS animations, gated, deposited on unequip | 16-26 |
| R4 co-save + polish | H7 records, revert/load, texture swaps on fresh loads, scabbard split, `FirstPersonStaff`, counters, receipt and package | round-trip verified; determinism receipt; user sign-off | 10-16 |
| **Total** | | | **54-84** |

These sit on top of #269's own phases; the feasibility audit's 64-102 h route-B figure covered display and attach work that #269 phases 0-2 have already spent.

## 14. Retired: the #272 scaffold

While #272 was open, a second tree was committed at `mods/visible-equipment/` (commit `a67fd1c`) with a receipt (`7684dd5`). It is superseded by the framework tree and is **dead**; nothing further will be added to it. Paths to retire:

- `mods/visible-equipment/` (CMakeLists.txt, vcpkg.json, build.ps1, README.md, VisibleEquipment.ini, cmake/version.rc.in, src/PCH.h, src/main.cpp, src/SlotRules.h, tests/SlotRulesTests.cpp)
- `.github/workflows/visible-equipment.yml`
- `records/source-builds/visible-equipment-0.0.1.json`

What in it is worth lifting into the framework tree before deletion: `src/SlotRules.h` + `tests/SlotRulesTests.cpp` (the 5.1 engine and its 52 checks, no game types), and the build recipe the receipt proves on NG 6.7.1 `70c1acd` (`COMPATIBLE_RUNTIMES 1.7.104` -> gate PASS; `/W4 /WX /Brepro` static CRT -> byte-identical rebuilds; CI with the NG revision and vcpkg baseline `ddd0023b` checked out and bootstrapped). The receipt also records one NG quirk the framework will meet at its own gate: `PluginDeclaration::VersionNumber` default-constructs to 1.0.0.0, so unused `compatibleVersions` slots read 1.0.0.0 rather than 0 (`SKSE/Interfaces.h:505-508`); harmless for SKSE's loader.
