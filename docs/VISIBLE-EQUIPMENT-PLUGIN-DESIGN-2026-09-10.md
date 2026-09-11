# Visible-equipment SKSE plugin: design (Phase 1)

Date: 2026-09-10. Tracking issue: **#269** (#272, opened for this phase, was closed as its duplicate at 01:57Z on 2026-09-11 while this spec was being written; #94, IED revival, was closed at the same time). Scope owner: #36. Superseded evaluation: #201 (AllGUD). Related: #270, #39.

**NAME_TBD.** The mod's name is the user's call and is not chosen. This document, the scaffold at `mods/visible-equipment/` and the plugin string `VisibleEquipment` use a placeholder; `CMakeLists.txt` lists every place a rename touches.

Receipts for every claim are file paths with line numbers. Prior-art paths:

| Alias | Path |
|---|---|
| IED | `skyrim-tools-source/ied-dev/ImmersiveEquipmentDisplays/IED/` (`master` d8e9d33) |
| SDS | `gh api repos/SlavicPotato/SimpleDualSheath` (`SimpleDualSheath/SDS/`) |
| OAR-IED | `gh api repos/SlavicPotato/OpenAnimationReplacer-IEDConditionExtensions` (`src/`) |
| OAR | `skyrim-tools-source/OpenAnimationReplacer-1.7.104/src/` (our 1.7.104 build, 99f140e) |
| NG | `skyrim-tools-source/CommonLibSSE-NG-6.7.1/include/` (70c1acd, 6.7.1) |
| EED | `skyrim-tools-source/EnsrickEquipmentDisplay/` (first-party, #269, phases 0-2 written today) |
| WS | Walking Stick 1.1.1 (Nexus 120966, file 508070), fetched via the Nexus API into scratch, contents listed in section 4.4 |

## 0. Two facts that shape this spec

**0.1 A first-party tree already exists.** Issue #269 (opened 17:19Z today) tracks the same plugin under the working name Ensrick Equipment Display Framework, repo `skyrim-tools-source/EnsrickEquipmentDisplay` (commits cb813fb..662d82f, 14:41-14:53 local). It compiles (DLL sha256 `b03a776e24feed796805ee62fdced7f054706d3e516f44ce285081b669d1e205`, CHANGELOG.md), has never run in game, and contains: `Load3D` vfunc hooks and a `TESEquipEvent` sink (`src/Hooks.cpp`), a per-actor `BSAnimationGraphEvent` sink for drawn/sheathed culling, a dual-sheath `DisplayManager` (`src/Display/DisplayManager.cpp`, 278 lines), a slot table (`src/Display/SlotTable.cpp`), a skeleton dumper, and a **measured** XPMSSE node inventory (`docs/NODE_INVENTORY.md`: 543 nodes, 71 attach candidates, read from the winning `skeleton.nif` by `tools/skeleton_inventory.py`). That work is ours and is reused here; milestone M1 below is largely a port of it into `mods/visible-equipment/`. #272 was closed into #269 while this document was being written, so #269 is the single track. Two trees now exist and one has to go: (a) `mods/visible-equipment/` in this repo, which has what the sibling first-party plugins have and the EED tree lacks (`/W4 /WX`, a CTest, a CI workflow with pinned dependencies, a source-build receipt, deny-by-default tracking), or (b) the EED repo, which has the display code and the measured node inventory. Recommendation: (a) is the home, M1 ports EED's phases 0-2 into it, EED's `docs/NODE_INVENTORY.md` and `tools/skeleton_inventory.py` come across unchanged, and the EED repo is archived once the port passes its launch verification. The reverse (adding the rules layer to the EED tree) is workable but would have to recreate the CI, gate and receipt conventions there. Decision D5 in section 10.

**0.2 The author of IED, SDS and OAR-IED is excluded.** `docs/EXCLUDED_AUTHORS.md` (SlavicPotato, 2026-09-10): *"His code is MIT on GitHub, so forking would be permitted. We are not forking... Every replacement below is written from scratch against CommonLibSSE-NG and the game's own structures... No code is copied out of it."* This spec therefore studies IED and SDS for **behaviour and on-disk schema only**. Section 8 answers the "reuse verbatim vs re-derive" question under that rule. It also changes the SDS relationship (section 4.6): SDS is not a long-term partner; it comes out at the end of M1 under exclusion rule 1 ("the function is replaced first, then the mod comes out").

## 1. Goals (verbatim rules from #36)

From the #36 comment of 2026-09-02 (user, verbatim as recorded):

> 1. **Weapons need a body slot.** The player can only pick up a weapon if there is a slot on their person for it, and **every weapon in inventory is displayed on the body**. Inventory weapon count == visible weapon count, no hidden carry.
> 2. **One exception: up to 2 daggers in a backpack**, treated as packed/hidden.
> 3. **Quest items are NOT exempt** - reversing the earlier position. Reason, in his words: a quest item stops being a quest item once the quest ends, which would leave the player carrying an item that violates the slot rules with no way to have consented to it.
> 4. **Be aggressively limiting on carry generally.**

From the #36 comment of 2026-09-02 (later, two tiers):

> | **On the person** | Weapons and worn gear | Every weapon needs a body slot and is **displayed on the body**. Exception: up to 2 daggers packed in a backpack. |
> | **Secondary storage** | Crafting and alchemy materials, in quantity | Exists precisely so material accumulation is possible under aggressive carry limits. **Armor and weaponry capped** - amount TBD. |

From the #36 comment of 2026-09-10 (staff rule, user quoted):

> *"I hate staves on the back, so I want walking stick so that if the player has a staff equipped, it is always in hand. The idea for my 'always display equipment mod' is that staves must always be equipped, since you wouldn't strap it to your back. This means it must always either be off-hand or in the primary hand if you have one, otherwise, it goes into the long-term storage. This makes having a staff a commitment to using it, unequipping it moves it into long term storage."*
>
> | A staff has no on-body storage slot | It occupies a hand (off-hand, or primary if no off-hand) or it is not on the person at all |
> | Unequipping a staff | Moves it straight to **secondary (long-term) storage**, not the pack |
>
> **Polearms are excluded from this list** as a category: *"We're not including polearms to keep things more simple and viable."*

Walking Stick (#270) is the staff-in-hand visual: *"shown only while the staff is actually equipped and not swimming/sitting/riding"*, and the mod page's own rule: *"The weapons will only be displayed on the hands when/if: The weapon is actually equipped. Your character is not swimming, sitting, riding or using a furniture."* (WS description, fetched 2026-09-10).

Goals, in priority order:

1. G1 Display: every governed weapon in the player's inventory is visible on the body, at a stable, per-class body position, on the installed XPMSSE skeleton; equipped-but-sheathed left-hand weapons included (the part SDS does today).
2. G2 Limit: pickups that would exceed the body slots are refused at the source, with a HUD line, never a dialog; a weapon that arrives by a path we could not pre-empt is reconciled (section 4.1).
3. G3 Packed daggers: exactly the exception in rule 2, hidden, counted.
4. G4 Staff: in a hand (off-hand first), carried like a walking stick between casts with WS's placement and animations; unequip sends it to secondary storage.
5. G5 Popup-free, log-only, 1.7.104-exact, deterministic build, CI, receipts.

## 2. Non-goals

- Polearms (rule 5): not governed, no display, no refusal. Bladestaff/polearm presets in WS are not adopted.
- IED's editor, I3DI viewport, physics, custom item displays, conditions engine, effect shaders, lights, NPC outfit logic. None of it is needed for #36.
- Binary compatibility with IED's `SKMP_GetPluginInterface` API (section 4.5 explains why not, and what replaces it).
- Any runtime other than Skyrim SE 1.7.104 (the DLL declares exactly that; section 4.10).
- The secondary-storage system itself (materials tier, armour/weapon cap). This plugin needs a `Deposit(item)` entry point into it (section 5.5); the storage design is #36's own open item.
- First-person display of anything (section 4.8).
- MCM. Configuration is INI + JSON, reproducible per #39 (section 6).

## 3. Architecture overview

```
main.cpp            SKSE entry, log, ini, message listener, sink registration
Rules/SlotRules.h   pure #36 rule engine (no game types; CTest)        [M0 done]
Rules/Placement     JSON placement table -> slot -> skeleton node + offset [M2]
Display/Tracker     per-actor state: slot board, attached copies, hand state [M1]
Display/Attach      model source (biped clone | BSModelDB) -> copy -> attach [M1]
Display/Gates       swimming/sitting/riding/furniture poll for hand slots [M3]
Hooks/Load3D        TESObjectREFR::Load3D vfunc 0x6A (Character, PlayerCharacter) [M1]
Hooks/Pickup        Actor::PickUpObject vfunc 0xCC, AddObjectToContainer 0x5A [M2]
Events              TESEquipEvent, TESContainerChangedEvent, SKSE ActionEvent,
                    TESSwitchRaceCompleteEvent, SKSE NiNodeUpdateEvent, TESFurnitureEvent
Storage/IStorage    staff -> secondary storage deposit (interface + ESL stash) [M3]
OAR/Conditions      IED_* custom conditions registered through OAR's API [M3]
Persist/CoSave      SKSE serialization records (section 4.7) [M4]
Diag/SkeletonDump   node tree dump; Diag/PlacementDump                   [M1]
```

Everything is event-driven; the only polling is the gate check for actors that currently have a hand display (section 4.9).

## 4. Architecture, in detail

### 4.1 Event hooks

| Trigger | Source (NG 6.7.1) | What we do |
|---|---|---|
| Actor 3D created or replaced | `TESObjectREFR::Load3D(bool)` vfunc 0x6A (`RE/T/TESObjectREFR.h:286`, `RE/A/Actor.h:333`), hooked on `RE::Character` and `RE::PlayerCharacter` vtables (EED `src/Hooks.cpp:92-116` does exactly this) | forget the actor's attachment bookkeeping, rebuild displays from inventory. Chosen over `TESObjectLoadedEvent` because cell reload, race swap and RaceMenu preset application create 3D without that event (EED DESIGN.md "Why Load3D"). Belt and braces: `RE::TESSwitchRaceCompleteEvent` and `SKSE::GetNiNodeUpdateEventSource()` (`SKSE/API.h:38`) also trigger a rebuild, which is what SDS subscribes to (SDS `Controller.h:39-46`). |
| Equip / unequip | `RE::TESEquipEvent` {actor, baseObject, originalRefr, uniqueID, equipped} (`RE/T/TESEquipEvent.h:13-17`) via `RE::ScriptEventSourceHolder::AddEventSink<T>` (`RE/S/ScriptEventSourceHolder.h:147`) | re-evaluate hands and sheath displays; staff unequip runs the storage rule (4.9, 5.5) |
| Inventory add / remove | `RE::TESContainerChangedEvent` {oldContainer, newContainer, baseObj, itemCount, reference, uniqueID} (`RE/T/TESContainerChangedEvent.h:11-16`) | re-assign body slots; **reconcile**: a governed weapon that entered the player with no free slot is moved back to `oldContainer` if it is still valid, else dropped at the player's feet (`TESObjectREFR::RemoveItem` with the dropping reason, `RE/T/TESObjectREFR.h:266`), with one HUD line and one log line. This is the safety net for paths the pre-emptive hooks cannot see. |
| Pickup attempt (ground) | `Actor::PickUpObject(TESObjectREFR*, count, arg3, playSound)` vfunc 0xCC (`RE/A/Actor.h:419`), hooked on `PlayerCharacter` | run `SlotBoard::CanAccept` first; on refusal do not call the original, show `RE::SendHUDMessage::ShowHUDMessage("No free slot for <name>")` (`RE/S/SendHUDMessage.h:9`, the top-left HUD queue, not a dialog), log at info |
| Container / vendor / script add | `TESObjectREFR::AddObjectToContainer(TESBoundObject*, ExtraDataList*, count, fromRefr)` vfunc 0x5A (`RE/A/Actor.h:322`) on `PlayerCharacter` | same verdict. When `a_fromRefr` names a container or vendor the item is refused at the source (it stays where it was). When there is no source (a script `AddItem`, quest reward) the item is accepted and routed by the reconcile step; see open decision D2 in section 10. |
| Weapon drawn / sheathed | `SKSE::ActionEvent` `Type::kEndDraw = 8`, `kEndSheathe = 10` (`SKSE/Events.h`) from `SKSE::GetActionEventSource()` (`SKSE/API.h:37`); this is also SDS's source (SDS `Controller.cpp` `ReceiveEvent(const SKSEActionEvent*)`) | cull or show the display copies of the equipped items. EED's phase-2 code matched `BSAnimationGraphEvent` tag strings instead and listed that as its risk #1 (CHANGELOG.md); the SKSE action event is the primary source here, the graph sink stays as a fallback behind an ini switch. |
| Sit / furniture | `RE::TESFurnitureEvent` {actor, targetFurniture, type kEnter/kExit} (`RE/T/TESFurnitureEvent.h:12-21`) | wake the gate check for hand displays |
| Game load / new game / revert | `SKSE::SerializationInterface` callbacks | section 4.7 |
| Message pump | `SKSE::MessagingInterface` `kPostLoad` (OAR condition registration must happen here or earlier: OAR `src/API/OpenAnimationReplacerAPI-Conditions.h:95`), `kPostPostLoad` (SDS presence check), `kDataLoaded` (hooks + sinks), `kPostLoadGame`/`kNewGame` (rebuild player) | |

Every engine-called handler is wrapped in `try { } catch (...) { log }`: an exception unwinding into an engine frame is a crash, a logged line is not (EED `src/Hooks.cpp:49-61`, kept as a house rule).

### 4.2 Node attach model

Two upstream models exist:

- **SDS re-parents the engine's own object.** It patches the biped attach routine at Address Library ids 15569 (SE) / 15746 (AE) at offsets +0x1D1, +0x223, +0x260 and the scabbard get/attach/detach sites (SDS `EngineExtensions.h:98-106`) so the engine's already-built left-hand weapon is parented to the left sheath node instead of hidden, and it moves it between the hand node and the sheath node on draw/sheathe (SDS `Controller.cpp` `ProcessEquippedWeapon`: `FindChildObject(sourceNode, weaponNodeName)` then `AttachToNode(w1, targetNode)`). No clones. It only works for equipped items, because the engine builds 3D only for those, and it requires byte-validated patch sites (`ValidateMemory`, `EngineExtensions.cpp:78-160`).
- **IED clones a model.** `ObjectDatabase::GetModel` loads via its own model database, `CreateClone` runs `NiCloningProcess` `CreateClone` + `ProcessClone` (IED `Controller/ObjectDatabase.cpp:288-297`), the copy goes under an attachment node it creates and names `OBJECT P <parent>` (or `OBJECT R <parent>` in reference mode) with an item root named `OBJECT WEAPON [formid]` (IED `Controller/INode.cpp:136-147, 210-243, 302-307`); the per-item transform lives on the item root (`INode::UpdateObjectTransform`, `INode.cpp:15-70`); scabbard sub-nodes `scb` / `scbLeft` are detached from the copy and re-attached to the target, left-hand items keep `scbLeft` and drop `scb` (IED `Controller/IObjectManager.cpp:1643-1700`); after attach it updates the subtree and registers the object with the shadow scene through two engine calls by Address id (99702/106336 and 99696/106330, `IObjectManager.h:273-274`, called at `IObjectManager.cpp:1626-1631`).

**Ours: the clone model, uniformly, with no engine patches.** Unequipped weapons have no engine 3D, so cloning is the only option for G1; using it for the equipped left hand too keeps one code path and no byte-level patch sites (section 9, R1). Concretely (EED `src/Display/DisplayManager.cpp:96-158, 200-276` is the M1 starting point):

1. Model source, in preference order: (a) if the actor already carries a built copy of the same form (`BipedAnim::objects[i].partClone`, `RE/B/BipedAnim.h:29`, via `Actor::GetBiped(false)`), deep-copy it (`NiObject::CreateDeepCopy`, `RE/N/NiObject.h:83`) so texture swaps and enchantment shaders come along; (b) else `RE::BSModelDB::Demand(path, out, args)` (`RE/B/BSModelDB.h:49`) with the weapon's `TESModel` path, then deep-copy. Texture-swap application on path (b) is M4 polish (IED does it in `ObjectCloningTask::CloneAndApplyTexSwap`, `IObjectManager.cpp:658`).
2. The copy is renamed with a fixed marker prefix (`VEQ ` placeholder) and attached under the slot's skeleton node with `NiNode::AttachChild(copy, true)` and a downward update. The marker is the recovery mechanism: any stale copy can be found and removed by name without the bookkeeping being right (EED `DisplayManager.cpp:12-16`).
3. Transform: `copy->local` = the slot's offset from the placement table (default identity, because the XPMSSE node already carries the right pose for its class); for hand slots the WS offsets (4.4).
4. Drawn state: equipped copies are `SetAppCulled(true)` while drawn and un-culled on sheathe; unequipped copies are always shown. M4 splits scabbard from blade so the scabbard stays visible while drawn, matching what the engine does for the right hand.
5. Lighting: if a fresh copy renders unlit or unshadowed in the M1 visual check, port the two shadow-scene registration calls by Address Library id (an id lookup, not a layout guess); NG exposes `RE::ShadowSceneNode` (`RE/S/ShadowSceneNode.h:21`).
6. Detach: on `Load3D` (new tree), on slot change, on removal, on actor unload; copies are released with their `NiPointer`.

XPMSSE style nodes: the measured inventory shows each attach point duplicated per style (`WeaponSwordLeft`, `WeaponSwordLeftFSM`, `...SWP`, `...NMD`, `...OnBack`, `...LeftHip`; EED `docs/NODE_INVENTORY.md`). We attach to the bare style-independent name; the RaceMenu style system re-parents the `MOV` wrapper, so the bare node follows whatever style the user picked (IED's `NodeMap.cpp:14-58` lists the same names with `kXP32` flags). Alternates are fallbacks only, logged when used (EED `SlotTable.cpp:11-30`).

### 4.3 Placement table

Shipped as `SKSE/Plugins/VisibleEquipment/placements.json`; user overrides in `placements.user.json` (same schema, merged by slot id, later file wins). Rotations are Euler radians in the same order IED's JSON uses so WS's numbers transfer verbatim; the convention is confirmed visually at M3 (section 9, R6).

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
    "hand.right": { "node": "NPC R Hand [RHnd]", "offset": { "pos": [-5.0, 4.5, 11.5], "rot": [2.001106, 0.196279, -0.367237], "scale": 1.0 }, "hint": 16,
                    "gates": ["equipped", "!swimming", "!sitting", "!furniture", "!mounted"] },
    "hand.left":  { "node": "NPC L Hand [LHnd]", "offset": { "pos": [1.0, 7.0, 12.5],  "rot": [-2.071184, -0.277077, -0.187825], "scale": 1.0 }, "hint": 16,
                    "gates": ["equipped", "!swimming", "!sitting", "!furniture", "!mounted"] },
    "backpack.dagger.1": { "hidden": true },
    "backpack.dagger.2": { "hidden": true }
  }
}
```

`byType` keys are the engine `WEAPON_TYPE` numbers (section 5.1). Node names are the measured XPMSSE names (EED `docs/NODE_INVENTORY.md`; the same names appear in IED `NodeMap.cpp:14-58` and SDS's `StringHolder` node constants). `skeleton.expect` is checked once per session against the player's loaded tree: the `XPMSE` `NiFloatExtraData` on the NPC root's parent and the `skeletonID` `NiIntegerExtraData` on the root, which are the observable fields IED folds into its signature (IED `SkeletonID.cpp:29-87`); a mismatch is one WARN line and the table still applies.

### 4.4 Walking Stick's staff preset, re-expressed

WS 1.1.1 contents (zip, 188,879 bytes): five IED `NodeOverrides` profiles, one `ExtraGearNodes/GP_WalkingStick.json`, and an OAR pack `Walking Stick/` with three sub-mods (`Stick on Left Hand`, `Stick on Right Hand`, `Bladestaff`) holding `MT_Idle`, `MT_WalkForward`, equip/unequip `.hkx` files and a `config.json` each. Only the staff half is adopted (#270: polearm and bladestaff presets not adopted).

What the IED side of the preset does, decoded against IED's parsers:

| WS file | Content | Meaning (IED source) | Our equivalent |
|---|---|---|---|
| `GP_WalkingStick.json` entry `IEDStaffRighHand` | `parent: "NPC R Hand [RHnd]"`, `xfrm_mov.pos [-5.0, 4.5, 11.5]`, `rot [2.001106, 0.196279, -0.367237]`, `placement_id: 16`, `valid_mov_child_nodes ["WeaponStaff"]` | create a CME->MOV node chain under the right hand with that transform (IED `ExtraNodes.cpp:53-79`), usable as a target for the `WeaponStaff` gear node; `placement_id` is parsed as a plain integer and cast (`Parsers/JSONConfigExtraNodeEntryParser.cpp:28`), i.e. an opaque number with no meaning inside IED beyond being reported | `hand.right` slot: same parent, same offset, `hint: 16` |
| same, `IEDStaffLeftHand` | `parent: "NPC L Hand [LHnd]"`, `pos [1.0, 7.0, 12.5]`, `rot [-2.071184, -0.277077, -0.187825]`, `placement_id: 16`, child `WeaponStaffLeft` | idem | `hand.left` slot |
| `GP - Walking Stick (Staff).json` | for gear node `WeaponStaff` (and `WeaponStaffLeft`), one placement override `target: "MOV IEDStaffRighHand"` (`...LeftHand`) with five match entries | placement override: when all matches pass, re-parent the gear node to the target MOV and publish `placement_id` as the node's hint (`INodeOverride.cpp:1142-1176` -> `GearNodeData::SetPlacement`); otherwise reset to the default parent and publish `None` (`INodeOverride.cpp:1215-1244`) | the `gates` list on the hand slots |
| match 1: `type 12` / `13`, `flags 164` | flags low 5 bits = 4 = `NodeOverrideConditionType::Type`, bit 5 `kAnd`, bit 7 `kMatchEquipped` (`ConfigNodeOverride.h:63-69, 98-104`); `type` value 12 = `ObjectSlot::kStaff`, 13 = `kStaffLeft` (`ConfigData.h:23-24`) | "a staff is equipped in that hand" | `equipped` |
| match 2: `bip 17`, `flags 106` | low 5 bits = 10 = `Extra`, `kAnd`, bit 6 `kNot`; `bip` 17 = `ExtraConditionType::kSwimming` (`ConfigCommon.h:300`) | NOT swimming | `!swimming` |
| match 3: `flags 102` | low 5 bits = 6 = `Furniture`, `kAnd`, `kNot`, any furniture | NOT using furniture | `!furniture` |
| match 4: `bip 29`, `flags 106` | `Extra` NOT; 29 = `kSitting` (`ConfigCommon.h:312`) | NOT sitting | `!sitting` |
| match 5: `flags 112` | low 5 bits = 16 = `Mounting`, `kAnd`, `kNot` | NOT mounting / riding | `!mounted` |

So the whole IED half of WS is two hand transforms plus five gates; there is nothing else to carry over. The animation half is OAR data (section 4.5).

### 4.5 IED public API compatibility: the answer

**Question.** Can our plugin expose IED's public API (same interface name, version, vtable) so OAR-IED Conditions and Walking Stick's OAR animations work unchanged?

**Answer: technically yes at the ABI level, but it is the wrong target, and it is not what Walking Stick needs.** Evidence:

1. The consumer resolves the provider by **DLL file name**. `PluginInterfaceBase::query_interface<T>()` calls `GetModuleHandle(T::PLUGIN_DLL)` then `GetProcAddress(handle, "SKMP_GetPluginInterface")` and checks `GetUniqueID() == T::UNIQUE_ID` (recovered `records/ied-rebuild-feasibility-2026-09-10/recovered-PluginInterfaceBase.h:34-72`). For IED, `PLUGIN_DLL = "ImmersiveEquipmentDisplays.dll"` and `UNIQUE_ID = 0xBD869D3E87EF7D51` (OAR-IED `src/API/PluginInterfaceIED.h:9-10`). Compatibility therefore requires our DLL to be **named** `ImmersiveEquipmentDisplays.dll`, export `SKMP_GetPluginInterface`, and return an object whose 9-entry vtable matches (5 base virtuals then `GetPlacementHintForGearNode`, `GetPlacementHintForEquippedWeapon`, `GetGearNodeParentName`, `GetPluginOption`, in that order; `PluginInterfaceIED.h:63-73`). The vtable itself is reproducible: MSVC lays virtuals out in declaration order and the by-value `RE::BSString` return uses the same CommonLibSSE-NG type on both sides (the recovered header is CommonLib-typed). Shipping our code under his mod's file name conflicts with the installed-disabled IED folder and with `docs/EXCLUDED_AUTHORS.md`.
2. The only consumer is OAR-IED Conditions, which is by the excluded author (`docs/EXCLUDED_AUTHORS.md`, "remaining GitHub-only projects ... `OpenAnimationReplacer-IEDConditionExtensions`"). It is also a 2023-08 build against a pre-format-5 CommonLibSSE-NG (`xmake-requires.lock`), so it would have to be rebuilt for 1.7.104 as well. Serving that DLL is the thing the exclusion rules out.
3. **What Walking Stick actually consumes is two OAR conditions by name**, not the C++ interface. Its OAR configs (WS `Stick on Left Hand/config.json`, `Stick on Right Hand/config.json`) use `IED_GearNodePlacementHint` with `"Gear node ID" 12.0` (left) or `11.0` (right) and `"Weapon placement ID" 16.0`, `IED_GearNodeEquippedPlacementHint` with `"Left hand": false` and `16.0`, plus stock OAR conditions (`IsEquipped` on `Campfire.esm|250CA` for the Campfire walking stick, gear node 15 / placement 10). Each carries `"requiredPlugin": "OpenAnimationReplacer-IEDConditionExtensions", "requiredVersion": "1.0.0.0"`.
4. OAR resolves those by two lookups, both by string: `OpenAnimationReplacer::IsPluginLoaded(requiredPluginName, requiredVersion)` against the registry keyed by the **name string passed to `AddCustomCondition`** (OAR `src/OpenAnimationReplacer.cpp:1054-1067`, checked at `src/Conditions.cpp:97-121`), then `CreateCondition(conditionName)` from the factory registry. Component values are read by **component name** (`src/BaseConditions.cpp:409-437, 499-509, 534-557`: `"Gear node ID"`, `"Comparison"`, `"Weapon placement ID"`, `"Left hand"`). The provider's own plugin name is only written back when OAR serialises a condition (`BaseConditions.cpp:79`, via `CustomCondition::GetRequiredPluginName()` = `SKSE::PluginDeclaration::GetSingleton()->GetName()`, `OpenAnimationReplacerAPI-Conditions.h` / `ConditionTypes.h:402`).

**Design.** Our plugin registers, through Ersh's public OAR conditions API (`OAR_API::Conditions::AddCustomCondition`, interface V3, at `kPostLoad`; OAR `src/API/OpenAnimationReplacerAPI-Conditions.h:57, 95`; the API header is explicitly "Copy this file into your own project"), the six condition names OAR-IED defined, with identical component names and order and identical numeric semantics: `IED_GearNodePlacementHint`, `IED_GearNodeEquippedPlacementHint`, `IED_GearNodeParentName`, `IED_HasEquipSlot`, `IED_IsBoundWeaponEquipped`, `IED_PluginOption` (OAR-IED `src/Conditions.h`). The placement hint for gear node 11/12 is the `hint` of the hand slot when its gates pass (16), else 0; gear node ids follow IED's numbering (`GearNodeID` 1..18, `PluginInterfaceIED.h:27-48`), and the equipped-weapon lookup mirrors IED's type-to-gear-node mapping including its deliberate staff swap (`PluginInterface.cpp` `GetGearNodeIDForItem`: `kStaff -> a_leftHand ? kStaff : kStaffLeft`). `SDS_IsShieldOnBackEnabled` is registered too, backed by our own shield state once M4 owns the shield.

The one JSON field that differs is `requiredPlugin`. Two options, both cheap:

- **Default: rewrite the data.** A converter (`tools/oar_requiredplugin_rewrite.py`, M3) rewrites `"requiredPlugin": "OpenAnimationReplacer-IEDConditionExtensions"` to our plugin name in the four WS `config.json` files (4 KB of text; the `.hkx` animations, which are GiraPomba's work, are untouched). Honest attribution in OAR's registry, no impersonation.
- **Optional alias, off by default:** `[Compat] OarLegacyPluginAlias=1` additionally registers the same factories under the literal name `OpenAnimationReplacer-IEDConditionExtensions` version 1.0.1, so unconverted third-party IED-OAR packs parse. The API takes the name as a plain string argument, so this needs no DLL rename; it is documented as an alias, not enabled by default.

So: **no** to the SKMP interface; **yes** to unchanged animation behaviour, via OAR's own API plus a four-file rewrite.

### 4.6 Simple Dual Sheath: division of labour and handshake

Facts (installed `mods/Simple Dual Sheath/SKSE/Plugins/SimpleDualSheath.ini`): left scabbards on; `[Sword] [Axe] [Mace] [Dagger] Flags=Player|NPC`; `[Staff] Flags=Player|NPC|Right` (the right-hand staff is shown on the back while sheathed, which is the exact thing the staff rule forbids); `[ShieldOnBack] Flags=FirstPerson` (no `Player`/`NPC` flag, so shield-on-back is off); `[NPC] EquipLeft=false`. SDS owns the *equipped* left-hand weapon and both staves by re-parenting engine objects (4.2). It exposes `SKMP_GetPluginInterface` with `UNIQUE_ID 0x3180B30EFCC0DB62`, `PLUGIN_DLL "SimpleDualSheath.dll"`, virtuals `GetShieldOnBackEnabled(Actor*)`, `RegisterForPlayerShieldOnBackEvent(sink)`, `IsWeaponNodeSharingDisabled()` (`recovered-PluginInterfaceSDS.h`; SDS `PluginInterface.cpp`).

**End state (exclusion rule 1, #269 phase 2):** SDS comes out when our M1 dual-sheath display passes a launch verification and the user's in-game check. After that there is no handshake to maintain.

**Transitional coexistence (M1, while SDS is still enabled):** at `kPostPostLoad` we test `GetModuleHandleA("SimpleDualSheath.dll")`. If present:

- our display of **equipped** items is forced off (`[Display] DualSheath` reported as `auto-off (SDS present)`), so the equipped left-hand weapon and the staves are never double-displayed; we display only *unequipped* inventory weapons (M2) and never on `WeaponStaff`/`WeaponStaffLeft`;
- we read SDS's ini ourselves (`Data/SKSE/Plugins/SimpleDualSheath.ini`, plain text on the VFS) rather than calling his interface: `[Staff] Flags` containing `Player` or `NPC` produces one WARN that the staff rule cannot hold while SDS shows staves on the back; `[ShieldOnBack] Flags` with `Player`/`NPC` reserves the `ShieldBack` node; the absence of a node-sharing key means SDS uses the shared 2H/bow nodes, so our unequipped 2H copies use `WeaponBackAxeMace`/`WeaponCrossBow` only when the slot table says so;
- no call into `SKMP_GetPluginInterface`: module presence plus the ini gives every fact we need, and it keeps the interop surface at zero.

If SDS reappears after removal, the same guard fires and logs; nothing else changes.

### 4.7 Per-actor persistence (co-save)

SKSE serialization (`SKSE::SerializationInterface`: `SetUniqueID`, `OpenRecord`, `WriteRecordData`, `ReadRecordData`, `GetNextRecordInfo`, `ResolveFormID`; NG `SKSE/Interfaces.h:94-135`). Unique id `'VEQP'` (placeholder; part of the rename). Principle: **the co-save is a cache of decisions, not the source of truth.** The slot board is fully derivable from the inventory and the placement table, so a missing or rejected co-save costs the user only (a) which two daggers were packed and (b) per-actor offset overrides; it never costs correctness. That is the mitigation for the corruption class IED's boost archives carry (`docs/IED-REBUILD-FEASIBILITY-2026-09-10.md` E, "Save data").

Records, each self-delimiting, versioned, length-checked, count-capped:

| Tag | v | Payload |
|---|---|---|
| `SLOT` | 1 | `u32 actorCount (<= 4096)`; per actor: `u32 formID` (resolved with `ResolveFormID`; unresolvable -> skip actor, log), `u16 entries (<= 64)`; per entry: `u8 slotIdLen, char[] slotId`, `u32 itemFormID`, `u16 inventoryUniqueID`, `u8 flags` (bit0 packed) |
| `STOR` | 1 | `u32 stashRefFormID`, `u16 count (<= 256)`; per item: `u32 itemFormID`, `u16 uniqueID`, `u32 originalOwnerActor` (staff items moved to storage by the rule) |
| `OVRD` | 1 | per-actor placement offset overrides: `u32 actorFormID`, `u16 count`, per: `slotId`, `float pos[3] rot[3] scale` |

Load: unknown tag -> skip; version newer than ours -> skip record, log once; any length or cap violation -> discard the record and rebuild from inventory (log at WARN). Revert callback clears all state. Save writes only what differs from the derivable default (packed choice, overrides, storage list). CTest (M4) round-trips every record through a memory buffer and fuzzes truncated/oversized payloads.

### 4.8 First person

The player has a second, first-person skeleton (`TESObjectREFR::Get3D(bool a_firstPerson)`, `RE/T/TESObjectREFR.h:377`; IED tracks `node1p`/`node3p` per gear node, `Controller/WeaponNodeEntry.h:22-45`). WS attaches the staff to the third-person hand only (`GP_WalkingStick.json` has no 1p entry), and the body cannot be seen in first person, so: **no first-person attachments in M1-M3**; all copies live on the third-person tree, which the engine does not render in first person. Camera state, if ever needed, is `RE::PlayerCamera::GetSingleton()->IsInFirstPerson()` (`RE/P/PlayerCamera.h:141`); IED additionally honours IFPV through a `TESGlobal` in `IFPVDetector.esl` (`Controller/IFirstPersonState.cpp:11-13`), which is not installed here. M4 offers `[Display] FirstPersonStaff=1` to also attach the staff copy to the 1p hand node for users who want to see the stick in first person.

### 4.9 Swimming / sitting / riding / furniture gates

Only hand slots have gates (4.3). State sources in NG: `ActorState::IsSwimming()` (`RE/A/ActorState.h:202`), `ActorState::GetSitSleepState()` (`ActorState.h:160`; anything but normal counts as sitting or sleeping, which also covers furniture use, the same fields IED diffs in `Controller/CachedActorData.cpp:251-332`), `Actor::IsOnMount()` (`RE/A/Actor.h:647`), plus `TESFurnitureEvent` enter/exit and `TESEquipEvent` as wake-ups. Because the transition into swimming or onto a mount has no reliable script event, actors with an active hand display are polled: a re-queued SKSE task every ~250 ms diffs the four booleans and toggles culling on change. Cost is O(actors with a staff in hand), in practice the player and rarely a follower. While gated, the hint reported to OAR is 0, so WS's idle and walk replacers stop matching, which is the behaviour the mod page describes.

Staff and two hands: equipping a two-handed weapon while a staff is in the off-hand cannot be represented physically; the design treats it as an unequip of the staff (rule 4: "a commitment to using it"), so the staff goes to storage. Flagged as decision D3 in section 10.

### 4.10 Version data and runtime declaration

`add_commonlibsse_plugin(... COMPATIBLE_RUNTIMES 1.7.104)` generates `SKSEPluginInfo(.RuntimeCompatibility = { REL::Version{1,7,104,0} })` (NG `cmake/CommonLibSSE.cmake:127-160`), which packs to `versionIndependence 0`, `compatibleVersions[0] = 0x01070680`, `versionIndependenceEx = kVersionIndependentEx_AddressLibraryV5 | NoStructUse` (NG `SKSE/Interfaces.h:377-378, 422, 500-544`). `audit/skse_version_data.py` reads that as `PASS (explicit compatibleVersions entry for 1.7.104)`, the same verdict the sibling plugins get. REL resolves through the Address Library at run time; NG 6.7.1's `IDDB::load_v5` reads the format-5 file (`src/REL/IDDB.cpp:205-209, 258-302`).

## 5. Slot model

### 5.1 Classes

`WeaponClass` from the engine `WEAPON_TYPE` numbers (`RE/W/WeaponTypes.h`: 0 hand-to-hand, 1 sword, 2 dagger, 3 axe, 4 mace, 5 greatsword, 6 battleaxe/warhammer, 7 bow, 8 staff, 9 crossbow): `kOneHanded` (1,3,4), `kDagger` (2), `kTwoHanded` (5,6), `kBow` (7), `kCrossbow` (9), `kStaff` (8), `kPolearm` (by keyword, rule 5, not governed), `kOther` (0 and anything unmapped, not governed). Implemented and tested: `mods/visible-equipment/src/SlotRules.h` `Classify`, `IsGoverned`.

### 5.2 Body slots, "limit = slots"

The roster is data (4.3); the default is the physical set the measured skeleton offers: `hip.right.1h`, `hip.left.1h`, `hip.right.dagger`, `hip.left.dagger`, `back.2h` (greatsword and battleaxe share one back position: `WeaponBack` and `WeaponBackAxeMace` both sit at (12.549, -6.345, 28.651), EED `NODE_INVENTORY.md`), `back.bow` (bow and crossbow share (-3.558, -10.578, 2.465)). Six body slots is therefore the default carry limit for governed weapons, before the packed daggers. Ankle and back-hip dagger nodes exist on the skeleton and can be added to the roster by the user in `placements.user.json`; they are not in the default because rule 4 asks for aggressive limits.

Enforcement at pickup: `SlotBoard::CanAccept(class)` returns `kAccept`, `kRefuseNoSlot` or `kNotGoverned`; the hooks in 4.1 act on it before the engine adds the item. `Place` takes the first free accepting slot in roster order; `Invariant()` asserts `carried == visible + packed` and `packed <= 2` after every mutation (tests do so). Equipped weapons also hold their body slot: a sheathed sword is on the hip, so it needs the hip.

### 5.3 The two-dagger backpack exception

Two `kBackpack` slots accepting `kDagger` only, ordered after the body dagger slots so daggers pack only when the hips are full; packed daggers get no display copy (hidden) and count toward `CarriedCount` but not `VisibleCount`. M2 ships them unconditionally; whether they should require a worn backpack item is decision D4.

### 5.4 Quest items

No exemption anywhere: `CanAccept` has no quest parameter, and `ExemptFromSlotRules(bool)` exists only so the test can pin the fact (`SlotRulesTests.cpp`, "quest items are not exempt"). Runtime-side, `InventoryEntryData::IsQuestObject()` (`RE/I/InventoryEntryData.h:56`) is read for the log line only.

### 5.5 Staff: hand, then storage

`hand.left` and `hand.right` are slots accepting only `kStaff`, in that order (`StaffHand(leftFree, rightFree)`: off-hand first, primary if no off-hand, else refused). A staff pickup is accepted only if a hand is free; the plugin then equips it there. `OnUnequip(kStaff) == kStorage`: the equip event with `equipped == false` for a staff calls `IStorage::Deposit(actor, form, extraList)`. The initial storage implementation is a stash: a container reference in a holding cell from a one-record ESL that ships with the plugin (decision D1 in section 10), looked up with `TESDataHandler::LookupForm` (`RE/T/TESDataHandler.h:62`). Two equipped staves occupy both hands.

## 6. Configuration surface

INI now, JSON for tables, MCM never required (#39: MCM Helper is disabled on 1.7.104 and the reproducibility rule wants files that can be diffed and replayed; an MCM, if ever built, edits these files).

`SKSE/Plugins/VisibleEquipment.ini` (every key optional; M0 reads `[Log] Level` only):

| Section | Key | Default | Milestone |
|---|---|---|---|
| Log | Level, FlushLevel | info, info (M0 flushes every line) | M0 |
| Rules | Enabled, PlayerOnly, EnforcePickup, ReconcileContainerChanges, PackedDaggers | 0 (M0), 1, 1, 1, 2 | M2 |
| Display | DualSheath (auto-off when SDS is present), NpcDisplay, FirstPersonStaff, GraphEventFallback | 1, 1, 0, 0 | M1/M4 |
| Staff | Enabled, TwoHandedUnequipsStaff | 1, 1 | M3 |
| Compat | OarConditions, OarLegacyPluginAlias | 1, 0 | M3 |
| Diagnostics | DumpSkeleton, DumpSkeletonPlayerOnly, DumpPlacements | 0, 1, 0 | M1 |

`SKSE/Plugins/VisibleEquipment/placements.json` + `placements.user.json` (4.3).

## 7. Logging and diagnostics

- One file: `Documents\My Games\Skyrim Special Edition\SKSE\VisibleEquipment.log` (`SKSE::log::log_directory()`, `SKSE/Logger.h:38`), the path every sibling plugin uses.
- No `MessageBox` path in our code. `SKSE::Init(a_skse, false)` keeps NG from opening its own logger (`src/SKSE/API.cpp:77-99`). NG's `stl::report_and_fail` (a MessageBoxA path) is never called by this module; the DLL still imports `MessageBoxA` through the static library, which PopupGuard (`!PopupGuard.dll`, #255) intercepts at run time. Hardening candidate: the same log-only overlay the OAR 1.7.104 build applied to NG (`skyrim-tools-source/OpenAnimationReplacer-1.7.104` 99f140e, "log-only fatal path"), tracked in section 9.
- Startup summary at info: plugin/version, runtime, address library file, SDS presence and the ini facts read, OAR presence and each condition's registration result, player skeleton identity vs `placements.json` expectation, roster.
- One info line per decision: attach (actor, slot, node, item), detach, refusal (item, class, reason), reconcile (item, where it went), storage deposit. Per-event lines at trace.
- `DumpSkeleton` (EED `src/Display/SkeletonDump.cpp`, ported) writes an actor's real node tree; `DumpPlacements` writes each slot's resolved node and world transform for the player. Both off by default, one file per actor per session.
- Refusals and reconciliations also produce a HUD line (`RE::SendHUDMessage::ShowHUDMessage`), which is the in-game notification queue, not a modal.

## 8. Prior art: what is reused, what is re-derived

Under `docs/EXCLUDED_AUTHORS.md`, **nothing from IED, SDS or OAR-IED is reused verbatim**. Had the policy allowed it, the parts with no dependency on the missing framework would have been the three interface headers (already recovered) and `INode`'s attach and naming logic (`Controller/INode.cpp:119-243`, ~120 lines); everything else in the attach path pulls `stl::`, `ITaskPool`, `ObjectDatabase` and the author's skse64 patch. What was studied, and where it lands here:

| IED / SDS behaviour | Source | Re-derived as |
|---|---|---|
| attachment node naming and re-use (`OBJECT P/R <parent>`, `OBJECT WEAPON [id]`) | IED `INode.cpp:136-147, 210-243, 302-307` | marker-prefixed copy names, single attachment per slot (4.2) |
| clone via `NiCloningProcess` | IED `ObjectDatabase.cpp:288-297` | `NiObject::CreateDeepCopy` (4.2) |
| scabbard `scb`/`scbLeft` handling | IED `IObjectManager.cpp:1643-1700` | M4 scabbard split (4.2 item 4) |
| shadow-scene registration after attach | IED `IObjectManager.cpp:1626-1631`, ids at `IObjectManager.h:273-274` | M1 visual check, id-based port only if needed (4.2 item 5) |
| extra gear nodes as CME->MOV chains with per-skeleton transforms | IED `ExtraNodes.cpp:53-111`; installed `SkeletonExtensions/ExtraGearNodes/00200_VanillaGear.json` | placement table with direct offsets; no CME/MOV synthesis (4.3) |
| skeleton signature | IED `SkeletonID.cpp:12-88` | `XPMSE` version + `skeletonID` extra data + measured NIF hash (4.3) |
| placement hint publication for OAR | IED `INodeOverride.cpp:1142-1176`, `GearNodeData.cpp:9-21` | hand slot `hint` when gates pass (4.4, 4.5) |
| public API shape consumed by OAR-IED | IED `PluginInterface.cpp`; OAR-IED `Conditions.cpp`, `main.cpp` | same condition names through OAR's API (4.5) |
| gates | IED `CachedActorData.cpp:251-332`; WS preset matches | 4.9 |
| first person | IED `IFirstPersonState.cpp:11-33` | 4.8 |
| events consumed | IED `Controller.h:44-57`; SDS `Controller.h:39-46` | 4.1 |
| co-save | IED `Controller.cpp:5511-5600` (boost archives) | explicitly not replicated; 4.7 |
| SDS equipped-object re-parenting via byte patches | SDS `EngineExtensions.h:98-106`, `EngineExtensions.cpp` | rejected; clone model instead (4.2) |
| SDS drawn/sheathed source | SDS `Controller.cpp` `SKSEActionEvent` handler | adopted as the primary source (4.1) |

First-party code that **is** reused (ours): EED `src/Hooks.cpp`, `src/Display/DisplayManager.cpp`, `src/Display/SlotTable.cpp`, `src/Display/SkeletonDump.cpp`, `src/Settings.cpp`, `docs/NODE_INVENTORY.md`, `tools/skeleton_inventory.py` (ported into `mods/visible-equipment/` at M1, adapted to the roster and the action-event source).

## 9. Risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| R1 | Layout drift / wrong offsets | No byte patches and no raw offsets: only vtable hooks (`Load3D` 0x6A, `PickUpObject` 0xCC, `AddObjectToContainer` 0x5A) and script/SKSE events, all through NG 6.7.1 pinned by commit and rejected at configure time if the checkout differs (`CMakeLists.txt`). The DLL declares 1.7.104 only, so a runtime update refuses it instead of loading it. Every hook install logs its resolved address. |
| R2 | Co-save corruption | Derivable state; versioned, length-checked, capped records; unknown/invalid records skipped with a log line; CTest round-trip and truncation fuzz (4.7). |
| R3 | Per-frame cost | Event-driven; the only poll is per hand-display actor at ~4 Hz; copies are created once per (actor, item) and reused; a debug counter logs attach/detach totals and the poll cost every 60 s at debug level; hard cap of 64 displays per actor. |
| R4 | Load order / preload | No preload export, no `!` prefix. OAR registration at `kPostLoad` is order-independent; SDS detection at `kPostPostLoad`; PopupGuard keeps loading first as today (`records/source-builds/popup-guard-0.1.0.json` load-order note). |
| R5 | Double display with SDS during M1 | Coexistence guard forces our equipped-item display off while `SimpleDualSheath.dll` is loaded; SDS ini audit at startup (4.6). |
| R6 | Rotation convention of imported WS offsets | Treated as [unverified] until the M3 in-game comparison; the placement table makes correction a data edit. |
| R7 | Unlit or unshadowed clones | M1 acceptance includes a lighting check; fallback is the id-based shadow-scene registration (4.2). |
| R8 | Scripted `AddItem` / quest rewards exceeding slots | Decision D2; interim behaviour is reconcile-to-storage with a HUD line, never a silent delete. |
| R9 | Memory growth from copies | Copies released on detach and on `Load3D`; totals logged; the marker prefix makes orphan sweeps possible. |
| R10 | `MessageBoxA` import via NG's `report_and_fail` | Never called by us; PopupGuard intercepts; candidate NG log-only overlay (7). |
| R11 | Prior tree divergence (#269) | Consolidate at M1 by porting; keep one tree afterwards (0.1). |

## 10. Open decisions for the user

- D1 Secondary storage vehicle for the staff rule: a plugin-shipped ESL stash container (recommended; one CONT + one CELL + one REFR) vs. hooking into the future materials tier. M3 blocks on this.
- D2 Scripted adds with no source container when slots are full: refuse (may break quest stages that check the item), or accept and route to storage (recommended), or accept and drop.
- D3 Equipping a two-handed weapon while a staff is in hand: unequip the staff to storage (recommended, "commitment") or refuse the two-handed equip.
- D4 Packed daggers: unconditional two slots (M2 default) or gated on a worn backpack item.
- D5 The name (NAME_TBD), and which tree is the home: `mods/visible-equipment/` (recommended, section 0.1) or `skyrim-tools-source/EnsrickEquipmentDisplay`.

## 11. Test plan

1. **Unit (CTest, every build, CI):** `slot_rules` (M0, 50 assertions covering rules 1-5 and the invariant); M2 adds `placement_table` (parses the shipped JSON, rejects malformed entries, resolves `byType`); M3 adds `oar_conditions` (component name/order snapshot vs. WS's config JSON); M4 adds `cosave_roundtrip` and `cosave_fuzz`.
2. **Static gates (headless):** `py -3 audit/skse_version_data.py <dll>` must print `PASS (explicit compatibleVersions entry for 1.7.104)`; `dumpbin /EXPORTS` must list `SKSEPlugin_Load`, `SKSEPlugin_Query`, `SKSEPlugin_Version`; a grep gate in `build.ps1` (M1) fails the build if `report_and_fail` or `MessageBox` appears in `mods/visible-equipment/src`.
3. **Preflight:** `py -3 audit/preflight.py` exit 0 before any launch (profile INIs, load order, claims).
4. **Verification launch (each milestone):** install into the profile under a claim, launch through the harness (`audit/launch_verify.py`), require main menu under 60 s and a save load, `VisibleEquipment.log` startup summary present with zero `[error]`, skse64.log lists the plugin as loaded, no new crash log. Per `feedback_skyrim_launch_verification_mandate`, a milestone without this is not done.
5. **User in-game acceptance (each milestone):** M1: left-hand weapon and staff-free back visible sheathed, hidden drawn, on the player and one NPC; SDS then removed and re-verified. M2: pickup of a seventh governed weapon refused with the HUD line; every carried weapon visible; two daggers packed. M3: staff appears in the left hand with WS's idle/walk, hides when swimming/sitting/riding/on furniture, unequip moves it to the stash. M4: save/load round-trip keeps packed choice and overrides.
6. **Determinism:** two clean build directories produce byte-identical DLLs (`/Brepro`), recorded in the receipt.

## 12. Milestones and hour estimates

| Milestone | Content | Exit criteria | Hours |
|---|---|---|---|
| M0 scaffold (this pass) | spec; `mods/visible-equipment/` with CMake, build.ps1, plugin entry, no-op sinks, `SlotRules.h` + CTest, GHA workflow; receipt | compiles, CTest green, version gate PASS, receipt with `runtimeVerification: UNVERIFIED`; the scaffold DLL's own verification launch is the first M1 task | 6 (5 spent) |
| M1 equipped-but-sheathed display | port EED display manager, slot table, skeleton dump; action-event drawn state; SDS coexistence guard and ini audit; lighting check; placement table loader (read-only use) | launch verification; user sees left-hand weapon sheathed on player and NPC; SDS removed and re-verified | 14-22 |
| M2 all inventory weapons, slots, refusal | slot board wired to inventory and container events; unequipped copies; `PickUpObject` / `AddObjectToContainer` hooks; reconcile; HUD lines; packed daggers | user acceptance items in 11.5 M2 | 24-36 |
| M3 staff rule + Walking Stick parity | hand slots with WS offsets; gates poll; OAR conditions through OAR's API; converter for WS configs; storage deposit (D1) and the 2H interaction (D3) | staff in hand with WS animations; hides under the gates; unequip deposits | 16-26 |
| M4 co-save, SDS end state, polish | serialization records; texture swaps on fresh loads; scabbard split; first-person option; NPC polish; performance counters; Nexus-ready package and docs | save/load round-trip; determinism receipt; user sign-off | 14-22 |
| **Total** | | | **74-112** |

The audit's route-B estimate was 64-102 h; the difference is the OAR condition layer and the pickup enforcement, which the audit did not scope.

## 13. M0 result

See `records/source-builds/visible-equipment-0.0.1.json` for hashes, toolchain, exact commands, test output and the gate verdict. Nothing was installed into the profile; no game was launched.
