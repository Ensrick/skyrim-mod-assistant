# Simple Hunting Overhaul 1.16 adoption and butchering-time audit

Audit date: 2026-08-30

Game/runtime: Skyrim Special Edition 1.7.104.0

MO2 instance/profile: `mo2-instances/skyrim-se` / `Default`

Tracker: [issue #72](https://github.com/Ensrick/skyrim-mod-assistant/issues/72)

Outcome: current SHO, its recommended Papyrus DAK runtime, and its exact Bruma
support are installed; a small owned extension is recommended for time-costed
meat processing, but it has not been implemented

## Executive verdict

[Simple Hunting Overhaul (SHO)](https://www.nexusmods.com/skyrimspecialedition/mods/95943)
1.16 is a good lightweight base for this profile. It uses ordinary corpse
looting, replaces supported animal carcasses after a pelt is taken, advances
time for skinning, raises meat yields, and removes the generic small-treasure
roll that makes gold and gems appear on animals. It has no native DLL and its
plugin is already ESL-flagged.

Its deliberate gap is now proven from the shipped source: taking meat only
adds SHO's `_MeatTracker` token. Time and hunting experience are applied only
when a pelt reaches `GlobalCheck()`. A player can therefore take meat
immediately, and taking meat first can make the carcass non-carryable without
having paid any processing time. No current official SHO addon closes this
gap. Simple Hunterborn 1.1.5 does not close it either; its meat branch only adds
its own tracker and it requires the full Hunterborn stack. Per the user
decision, Hunterborn is Skip and neither it nor any dependent addon was
installed.

The safest repair is a separate, owned ESP-FE plus event-driven Papyrus alias
that charges a carcass once on its first material harvest. It should consume
SHO's public globals/formlists as read-only inputs and place an owned persistent
token on the corpse. It should not replace SHO's vendor script. A native hook
is unnecessary for the first implementation; a small Quick Loot API adapter is
only justified later if the chosen design must block transfer before the item
enters the player's inventory.

## Exact installed inputs

| Input | Exact archive | Integrity and transaction |
|---|---|---|
| Dynamic Activation Key | Nexus file 421305, v1.02, `Dynamic Activation Key-96273-1-02-1693177288.zip` | 2,872 bytes; SHA-256 `28ad717ed88dc0c5ca3b9c01dcf7849a74703e508a5560b21343496606982291`; transaction `20260830T152849272Z-0858430c6b1c` |
| Simple Hunting Overhaul | Nexus file 699215, v1.16, `Simple Hunting Overhaul-95943-1-16-1766050937.7z` | 28,410,984 bytes; SHA-256 `fb6a89ed4874891efacf75c5c9b1c2d2f99da5cee785cd1203a30866be9ce732`; transaction `20260830T152850076Z-dab31c590082` |
| SHO - Beyond Skyrim Bruma Patch | Nexus file 535062, v1.13, `SHO - Beyond Skyrim Bruma Patch-95943-1-13-1724571884.zip` | 967 bytes; SHA-256 `b19236606a323846451579c353437a86d84d55d394ebc5fc3d1ef47bdae7b931`; transaction `20260830T152852491Z-15ed5821eda4` |

All three archives are retained. None contains a FOMOD, so no subjective
installer branch was taken. Installed payloads are byte-identical to their
archives: DAK has 3 vendor files, SHO 347, and the Bruma support 1; there are no
missing, mismatched, or extra vendor files after excluding MO2's `meta.ini`.
No file was copied into the game's `Data` directory and no game was launched.

DAK's page currently reports 1.13 because it added optional native builds,
including file 797511 for Skyrim 1.7.104. The author still explicitly
recommends the Papyrus main file. The native file was published on the audit
date and is described as potentially not working; the stable 1.02 Papyrus
build is therefore the correct non-experimental choice. Its hard requirement,
powerofthree's Papyrus Extender, was already installed and enabled. Adding SKSE
Menu Framework merely to use the optional native DAK build would provide no
benefit here.

The enabled plugin order is:

1. `Dynamic Activation Key.esp`
2. `Simple Hunting Overhaul.esp`
3. `SHO - Bruma Patch.esp`

The corresponding Nexus pages 95943 and 96273 are live Keep decisions.
JaySerpa (Nexus user 5201727) is not Excluded and the curator's effective
author block is false. Hunterborn page 7900 is Skip. Simple Hunterborn page
109288 remains unclassified and was not installed.

## What SHO 1.16 actually changes

SHO contains 356 records: 330 new and 26 overrides, with no deleted records.
The 24 overridden death-item lists cover Vale deer; the three bear variants;
cow; male and female elk; goat; horker; horse; mammoth; sabrecat; skeever;
normal and frost trolls; normal and ice wolves; hare; deer; three mudcrab
variants; and normal and ice foxes.

The shipped `SHO_PlayerAliasScript` registers SHO's ingredient/meat and pelt
formlists. `OnItemAdded` acts only when the source is a dead actor and applies
blacklist, player-horse, and giant gates. The ingredient/meat branch adds
`_MeatTracker` and returns. The pelt branch classifies the actor, calls
`GlobalCheck()`, awards hunting progress, calculates a duration from creature
category, actor scale, `_HuntingXP`, and min/max globals, and advances
`GameHour`. Its fade routine closes only `ContainerMenu`.

SHO also deliberately supplies a loose `ReanimateAshPile.pex` above the base
game. It removes meat and pelts from reanimated animal thralls before ash is
created. The matching source tests `ActorTypeAnimal` twice even though it
retrieves both `ActorTypeAnimal` and `ActorTypeCreature`; non-animal creatures
may therefore miss the cleanup. This is an upstream defect candidate and a
runtime test item, not a reason to edit the vendor file in place.

SHO's three new raw/cooked meat ingestibles use the standard Creation Club
Survival hunger effects: small restoration for raw meats and large restoration
for cooked generic meat. `StarfrostVanillaHunger.esp` overrides those same
magic effects, so SHO meat inherits Starfrost's hunger tuning without an extra
patch.

## Bruma support

The official optional patch is structurally and semantically applicable to the
installed Beyond Skyrim: Bruma 1.6.4 files 775191, 775180, and 775106. Bruma's
1.6.4 creature death-list FormIDs are unchanged and every target referenced by
the patch exists.

The patch is ESL-flagged and contains 9 leveled-item overrides, 1 form-list
override, and 3 armor-addon overrides. Its masters are `Skyrim.esm`,
`BSAssets.esm`, `BSHeartland.esm`, and `Simple Hunting Overhaul.esp`. It
preserves Bruma's unique gray/black fox, wolf, deer, rat, mountain-lion, and
bear pelts, forwards the correct SHO meats, normalizes yields, and removes the
generic `LootSmallTreasure10` entry (`0F961F:Skyrim.esm`). `_BrumaPelts`
forwards the Bruma pelt set and SHO's hare pelt. No current Bruma record loss
was found.

There is no official SHO file for Beyond Reach or Wyrmstooth. Static direct
death-item coverage is partial:

- Beyond Reach has 336 direct-death-item NPC definitions using 48 lists. Of
  those, 36 actors using 14 vanilla bear, cow, deer/elk, goat, rabbit, horse,
  sabrecat, skeever, troll, or wolf lists inherit SHO automatically. Chicken,
  dog, slaughterfish, spider, death-hound, were-creature, and custom lists do
  not.
- Wyrmstooth has 53 direct-death-item NPC definitions using 18 lists. Twelve
  actors using 6 vanilla fox, hare, horse, mudcrab, and skeever lists inherit
  SHO; chicken and other custom lists do not.

Some special actors reuse misleading vanilla races or voices—for example a
Beyond Reach Damned Atronach using `FoxRace` and a Wyrmstooth Mudcrab Merchant.
Blindly extending SHO by race or voice would create false positives. An owned
extension needs explicit allow and exclusion lists plus representative runtime
tests; no speculative Beyond Reach/Wyrmstooth patch was created.

## Survival and Quick Loot behavior

Starfrost hunger updates are registered through game-time callbacks. SHO's
direct `GameHour` advancement should wake that system, while Survival Mode
Improved controls exposure/cold in native code. This is structurally
compatible, but only a disposable runtime test can prove that hunger, cold,
and exhaustion visibly advance at ordinary and critical thresholds during a
processing event.

The installed QuickLoot IE implementation transfers items through the normal
`RemoveItem(..., player)` path, which should still deliver the player alias
`OnItemAdded` event with the corpse as source. Its menu is `LootMenuIE`, not
`ContainerMenu`, so SHO's fade/close routine may leave the Quick Loot window
open or race its refresh. QuickLoot IE exposes a cancellable pre-take API, but
using it would require a small native adapter. The old SHO-linked Quick Loot
patch is hidden/obsolete and explicitly directs users to QuickLoot IE, so it
was not installed.

The exact current profile state matters: the custom QuickLoot IE mod folder is
enabled and its native files are visible, but `QuickLootIE.esp` is currently
not starred in `plugins.txt`. Runtime acceptance must either test that intended
state or first resolve the separate QuickLoot plugin decision; this audit did
not silently enable it.

## Conflicts, links, and order

The managed-file audit parsed 25,164 active files and found no DAK or Bruma
patch collision. SHO wins only two SMIM texture paths,
`textures/smim/clutter/common/rope01_beige.dds` and `rope01_n.dds`; these are
intentional rope assets used by the supplied carcass models. The base-game BSA
override of `ReanimateAshPile.pex` is separately documented above.

The whole-profile record audit parsed 131 active plugins with zero failures.
Only 15 conflict chains involve SHO:

- nine Bruma death lists plus four Bruma patch forwarding/self chains, all
  verified as intended;
- `DLC1DeathItemDeerVale`, where SHO preserves venison and antlers, raises
  venison from one to four, preserves the Vale deer hide, and removes USSEP's
  `LootSmallTreasure10`; and
- `DeathItemHorse`, where SHO preserves horse hide and raises horse meat from
  one to two while removing the same treasure roll.

The two USSEP winners are therefore intentional semantic replacements, not
lost fixes. Link audits found all declared masters present. DAK has no external
links; SHO has 4,185 resolved links across its six masters after exempting only
the engine's canonical non-enumerated `PlayerRef`; and the Bruma patch has 47
resolved links across four masters with no unresolved reference.

LOOT 0.29.6/lootcli 1.8.0 recognizes all three plugins as light and emits no
SHO-specific message. Its only global warning is the already tracked Engine
Fixes Part 2 warning, unrelated to this installation.

## Simple Hunterborn proof and optional mods

Simple Hunterborn 1.1.5 (Nexus file 781645, SHA-256
`56c72efdc9fa1001a5e942b17bf39551299e30b5e93d59df2431fd9a28c01126`)
was downloaded into audit scratch and inspected, not installed. Its FOMOD
requires Hunterborn, SHO, and FormList Manipulator. Its modified
`SHO_PlayerAliasScript` meat branch only adds `_MeatTracker`; it does not call
`GlobalCheck()` or `PassTime()`. It changes harvest-tier globals after pelt
skinning, so it cannot satisfy issue #72's meat-first requirement.

The following SHO recommendations remain optional and unclassified: Carry
Your Carcasses, Immersive Carcass Carrying, Immersive Hunting Animations, and
Skills of the Wild. Carry Your Carcasses is presentation/transport, not
butchering time, and requires IED. Immersive Hunting Animations 2.3.1 requires
OAR and exposes Quick Loot support through its MCM, but it is still a visual
addition rather than the missing mechanic. None was installed or marked Keep.

## Recommended owned extension

Implement an event-driven quest/player-alias ESP-FE as a separate mod:

1. Filter `OnItemAdded` to designated meat and pelt formlists and require a
   dead actor source. Arrows, quest items, equipment, and unrelated inventory
   transfers must never qualify.
2. Put an owned persistent processed token in the source corpse and test it
   before charging. This survives save/load and cell unload and prevents
   reopening, split-stack transfer, and Quick Loot refresh from charging twice.
   Do not reuse `_MeatTracker`: upstream uses it to mean that meat was removed
   and the carcass can no longer be carried, not that processing time was paid.
3. Read SHO's creature trait, scale, hunting XP, and min/max globals to derive
   time, without copying or replacing SHO source. Keep the new classification
   data in owned, extensible allow/exclusion formlists.
4. Ignore an actor that is alive or has been resurrected. Exercise reset,
   respawned-reference, reanimation, pickup/drop, save/reload, and cancelled
   transfer paths explicitly before promotion.
5. Begin with post-transfer Papyrus behavior. It is event-driven, has no
   high-frequency polling, and works with ordinary and Quick Loot transfers.
   Add an optional native adapter using QuickLoot IE's public cancellable
   pre-take event only if the selected UX requires meat to be blocked before
   transfer. Do not hook private executable addresses or build a full native
   hunting replacement.

The cleanest balance is one combined field-dressing charge on the first
material harvest, whether meat or pelt. To prevent SHO from charging the pelt a
second time while retaining its visual transformation, configure SHO's
`_FadeTimePass` to its fade-only value and let the owned extension own the time
charge. This requires a user decision because separate butchering and skinning
charges are also defensible.

## Open user decisions

1. Charge once for combined field dressing, or separately for meat butchering
   and pelt skinning?
2. Automatically charge immediately after the first meat/pelt transfer, or
   block ordinary looting and require an explicit **Butcher** activation?
3. On meat-first processing, use a fade/animation, a quiet time transition, or
   no visual interruption?
4. What are the size/time curve and hunting-XP reward, and should meat
   processing advance SHO's hunting skill?
5. May a processed or partially harvested carcass still be carried?

## Runtime acceptance matrix

- Normal container menu and Quick Loot: meat first, pelt first, partial meat
  stack, take-all, reopen, cancel, drop/pickup, and carry-carcass paths.
- Save/reload and cell unload between first and second harvest; dead actor
  resurrection/reanimation; respawning and reused references.
- Arrows, quest items, ingredients, pelt-only animals, meat-only animals,
  horses/player horse, giants, and blacklisted actors.
- Representative vanilla deer/wolf/bear/fox/skeever; all nine Bruma patched
  lists; covered and uncovered Beyond Reach/Wyrmstooth cases; deliberately
  misleading special actors.
- Starfrost/Survival Mode Improved hunger, cold, and exhaustion at normal and
  near-critical thresholds during processing, including daylight/weather
  progression.
- QuickLoot IE menu refresh/close behavior; keyboard and controller; no modal
  popup, foreground window, forced camera effect, or log spam.
- Reanimation into ash for both `ActorTypeAnimal` and non-animal
  `ActorTypeCreature` cases, specifically testing the upstream duplicate-keyword
  condition.

## Distribution boundary

SHO's permission text asks prospective asset/code users to contact the author,
and its credits identify third-party skinned textures and carcass models. There
is no blanket permission to repack the vendor archive. DAK is likewise an
external dependency. Public packaging must fetch the original Nexus files and
reproduce the tracked installation.

The proposed extension may be distributed as a new Ensrick-owned mod if it
contains only original records/scripts and references SHO forms as a master.
It must not redistribute SHO/DAK files, copy upstream code or assets, or imply
upstream support. If code or art is copied rather than independently authored,
obtain and record permission first.

## Sources

- [Simple Hunting Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/95943)
- [Dynamic Activation Key](https://www.nexusmods.com/skyrimspecialedition/mods/96273)
- [Simple Hunterborn](https://www.nexusmods.com/skyrimspecialedition/mods/109288)
- [Hunterborn SE](https://www.nexusmods.com/skyrimspecialedition/mods/7900)
- [Carry Your Carcasses](https://www.nexusmods.com/skyrimspecialedition/mods/62628)
- [Immersive Hunting Animations](https://www.nexusmods.com/skyrimspecialedition/mods/96961)
