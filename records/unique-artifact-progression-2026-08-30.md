# Unique artifact progression audit (2026-08-30)

Tracked by the GitHub issue opened from this audit. No candidate was installed,
enabled, added to Keep, or written into the active MO2 profile.

## Problem boundary

There are three different mechanics hiding behind the phrase "weapons should
level with the player":

1. **Vanilla leveled uniques.** Chillrend, Dragonbane, the Nightingale gear,
   the Pale Blade, the Gauldur weapons, the Shield of Solitude, Miraak's gear,
   and several other rewards exist as several separate base forms. A leveled
   list selects one form when the reward is resolved. The selected object does
   not subsequently level with the player.
2. **Static artifacts.** Most Daedric artifacts are not leveled rewards. They
   have one base form and fixed base/enchantment records. Their problem is
   relative obsolescence, not being stuck on an accidentally low reward tier.
3. **True per-instance progression.** A system may change the temper/health
   value on the exact inventory instance as it is used. That can preserve its
   enchantment and model, but it is not the same as advancing through Bethesda's
   authored reward variants and normally does not scale enchantment magnitude.

These categories must not be patched with the same blind rule. In particular,
an automatic replacer for vanilla leveled reward forms does nothing for
Dawnbreaker, the Mace of Molag Bal, Volendrung, Mehrunes' Razor, or other static
Daedric artifacts.

## Current candidate audit

The Nexus API was used read-only. Candidate archives were downloaded only into
ignored audit storage, SHA-256 checked, and inspected without modifying the
profile.

### Upgrade Leveled Items 4.0 (Nexus 22565, file 749106)

- Current release: 4.0, 2026-05-06.
- Archive SHA-256:
  `C854106E5CF137309A8AB03E23EFE558578EF807B3469B0C4043B67BDBAF5237`.
- [Official page](https://www.nexusmods.com/skyrimspecialedition/mods/22565).
- The archive includes readable Papyrus source but has restrictive
  redistribution/modification permissions. It is source-available, not an
  open-source dependency we can vendor or fork freely.
- The **automatic** choice is an already-ESL-flagged plugin containing one new
  quest with one player alias and no vanilla overrides. Its single script
  registers for SKSE's `StatsMenu` and scans a fixed property list only when the
  perk menu closes. That is a small and bounded Papyrus footprint.
- The **spell** choice is also ESL flagged, but it adds a spell/book and a
  placed reference outside High Hrothgar, with `WRLD` and `CELL` overrides. The
  automatic variant has the cleaner conflict footprint.
- It supports the vanilla/DLC leveled families named on the page and already
  obtained items while they are in the player's inventory.
- Advancement replaces one base form with another via `AddItem`/`RemoveItem`.
  Smithing temper and player-added enchantment data are therefore lost. Charge
  state/favorites/equipment state also require runtime verification. The page
  expressly documents the loss of tempering and player enchantments.
- Because the target is a leveled list, record-overhaul winners that preserve
  the vanilla FormIDs normally carry through. An overhaul which deletes,
  replaces, or collapses those form families needs a patch.
- It does not solve static Daedric artifacts or other one-form uniques.

**Finding:** strongest current narrow utility for Bethesda-authored leveled
reward families. If adopted, use the automatic variant only, patch its fixed
family map after the final artifact stack is chosen, and test replacement
semantics on a disposable save.

### Complete Crafting Overhaul Remastered 2.6.4 (Nexus 28608)

- Current release: 2.6.4, 2026-06-24.
- [Official page](https://www.nexusmods.com/skyrimspecialedition/mods/28608).
- This actively maintained overhaul includes unique-leveled-item upgrading in
  its much larger crafting system.
- It hard-requires USSEP and WACCF, uses SKSE/SkyUI, edits and scripts broad
  crafting behavior, and brings a substantial compatibility surface unrelated
  to this one requirement. It also cannot be packaged inside a collection,
  although compatibility patches are permitted.

**Finding:** valid only if CCOR independently wins the crafting-overhaul
decision. Do not install a broad crafting overhaul solely to solve artifact
progression.

### Signature Equipment 2.2.0 (Nexus 16190, file 288765)

- Last release: 2.2.0, 2022-06-04.
- Archive SHA-256:
  `8F4CDD44A84ABC11AFDDAF3236B73F6798E8460D8FD17113D1510BE71AC1E119`.
- [Official page](https://www.nexusmods.com/skyrimspecialedition/mods/16190).
- The archive includes all four Papyrus sources and the author states open
  permissions, but no standard software license or maintained public source
  repository was identified.
- Its unflagged plugin has eleven new records and can only become ESP-FE after
  compacting FormIDs. That must be a fresh-game/fork decision, not an in-place
  flag change.
- SPID applies a scripted ability broadly. Every relevant hit tracks health;
  delayed updates submit story-manager events; failure retries every 0.5
  seconds until a quest accepts the event. Three quests and follower aliases
  then increase `WornObject` item-health percentage for equipped weapons and
  armor.
- This preserves the actual item form, mesh, texture, and enchantment, and it
  naturally works on mod-added equipment. It modifies instance tempering, so
  conventional grindstone tempering can stack/interact and must be bounded by
  its MCM caps.
- It scales all qualifying gear, not only artifacts. A mundane early-game item
  can become end-game equipment, which undermines the intended equipment and
  loot progression unless the system is redesigned around an explicit artifact
  allowlist.
- It increases physical damage/armor through temper health. It does not make a
  weak fixed artifact enchantment stronger.
- The all-actor hit listener and story-event retry path are a materially larger
  Papyrus/stability surface than a forge recipe or one menu-close inventory
  scan, especially with the planned larger battles.

**Finding:** do not adopt the stock mod for this build. Its instance-preserving
idea is useful, but its global scope, dated event architecture, and inability to
scale enchantments do not match the requirement.

### Leveled Items Level With You 1.03 (Nexus 6657, file 16559)

- Last release: 1.03, 2018-06-18 metadata; main file dates to 2017-01-02.
- Archive SHA-256:
  `5B903DB2861FAF35D91BA04547C30EA8A03F1FD3376688AA85AB8EFF7EFEA98B`.
- [Official page](https://www.nexusmods.com/skyrimspecialedition/mods/6657).
- It replaces an equipped low-tier form with a higher form and optionally
  consumes souls. The page documents restored weapon charge on replacement.
- The archive contains only compiled PEX files, an unflagged plugin with 43 new
  records, one quest alias, and four soul-gem overrides. It has not received a
  modern maintenance release.

**Finding:** superseded for this profile by the narrower, current, ESP-FE
Upgrade Leveled Items 4.0 implementation.

### Reforge Leveled Uniques 1.0.0 (Nexus 14422)

- Last release: 2018-01-04.
- [Official page](https://www.nexusmods.com/skyrimspecialedition/mods/14422).
- Its forge-gated, Arcane-Blacksmith, material-consuming concept closely matches
  the desired fiction.
- The author now labels it unsupported, abandoned, and obsolete, and requires
  permission before modification or asset reuse.

**Finding:** do not adopt or derive files from it. Reimplement the general idea
independently in owned records if that route is selected.

### Artifact overhauls: Artificer and Reliquary of Myth

- [Artificer 1.0.11](https://www.nexusmods.com/skyrimspecialedition/mods/99619)
  was updated 2026-04-27 and is deliberately balanced so top artifacts can
  rival crafted items. It hard-requires Mysticism and Thaumaturgy. Its
  permissions allow credited fixes/modifications, but its complete artifact
  design and two gameplay-overhaul dependencies make it a separate curation
  decision.
- [Reliquary of Myth 4.8.3](https://www.nexusmods.com/skyrimspecialedition/mods/31612)
  was updated 2025-03-27 and similarly tries to make artifacts end-game viable
  through unique, mostly static effects. It is script/record heavy by artifact
  and has a large patch ecosystem; modification permission is restricted.

**Finding:** these solve the static-artifact power floor through deliberate
artifact redesign rather than true player-level scaling. They should be
compared as artifact-overhaul candidates, not silently combined with a global
scaler. Whichever artifact overhaul wins must become the semantic input to any
owned reforging patch.

## Compatibility and save-safety conclusions

- Pure mesh/texture replacers such as Believable Weapons-style remeshes remain
  compatible when they retain the same model paths or win the final `WEAP`
  model field. A progression patch should never copy stale model paths; it must
  forward the final visual winner for every tier.
- Base-form replacement naturally loses instance extras: temper, charge state,
  favorites/equipped state, poisoning, custom names, and player enchantments
  are all acceptance-test targets. Published utilities acknowledge at least
  the temper/enchantment loss.
- An instance-temper solution preserves the form and enchantment but can stack
  with smithing and cannot by itself strengthen a fixed enchantment.
- Quest aliases and active magic effects bake state into saves. Removing a
  scripted scaler mid-save is not an acceptable supported workflow. A
  recipe-only ESP-FE is simpler to add and remove, but converting an artifact
  still permanently changes that inventory instance.
- Duplicate artifacts, follower-held items, museum/display containers, and
  stored items create exploit and coverage questions. Automatic inventory
  scans only see the player inventory; a forge recipe is explicit and avoids
  silently rewriting displays or follower equipment.
- A player-level-only cost is exploitable: the player can wait to a threshold
  and instantly promote every artifact. Reforging should require ownership,
  Arcane Blacksmith (or the final perk-overhaul equivalent), Smithing skill,
  rare material/quest knowledge, and a capped progression table. It must not
  generate sellable duplicate artifacts or refund more resources than it
  consumes.

## Recommended architecture

Use two owned, generated layers after the artifact-overhaul and perk/crafting
decisions are final:

1. **Leveled-reward repair.** Prefer a small ESP-FE, recipe-only implementation
   generated from the final winning vanilla/DLC leveled-item families. Each
   transition consumes the lower form plus documented materials at a forge and
   is gated by the next tier's level and the final Arcane Smithing perk. This is
   the most transparent, lore-friendly, low-script option. Upgrade Leveled
   Items 4.0 automatic is a reasonable temporary comparator, not a redistributable
   implementation base.
2. **Static-artifact balance.** Establish an item-by-item end-game power floor
   in the owned equipment integration patch. Prefer meaningful artifact effects
   and proper tempering/perk support over multiplying every artifact by player
   level. Only artifacts that genuinely need progression should receive owned
   tier forms or conditional effects.

Generate the `COBJ`/override records from a reviewed manifest rather than
hand-authoring them. This keeps the final mesh, keywords, sounds, material,
enchantment, tempering recipe, and artifact-overhaul semantics auditable across
load-order changes. The deliverable can remain ESP-FE if the generated record
count and FormID range are kept within light-plugin limits.

## Decision gates

1. Choose the artifact design winner: vanilla-plus owned balance, Artificer,
   Reliquary of Myth, or another audited contender.
2. Choose explicit forge/reforge progression versus automatic menu-close
   replacement for Bethesda's leveled families. Recommendation: forge/reforge.
3. Decide whether reforging is gated by player level, Smithing skill/perks,
   quest knowledge, rare materials, or a combination. Recommendation: level +
   Smithing/perk + item-specific materials.
4. Decide whether a reforge intentionally strips prior temper/poison/charge and
   warn in the recipe name or confirmation flow, or whether a narrowly scoped
   script must preserve transferable instance state.
5. Define whether followers and stored/displayed artifacts are eligible.
   Recommendation: player-carried items only, through an explicit forge action.

## Acceptance criteria for implementation

- Inventory generated from the final load order distinguishes every leveled
  family from every static unique and records all source/winner FormKeys.
- Owned plugin is ESP-FE, contains no world/cell edits, and vendors no
  third-party assets or scripts.
- Reforge recipes appear only for an owned eligible lower-tier artifact and
  only after all documented level/skill/perk/knowledge/material conditions.
- Exactly one old instance is consumed and one intended higher instance is
  produced; no duplicate, resale, breakdown, or material-refund exploit exists.
- Already-obtained low-tier items work on an existing disposable test save.
- Quest rewards obtained after installation still resolve correctly.
- Every tier forwards the final mesh/model, keywords, sounds, equip type,
  tempering material/perk, enchantment, value, and artifact-overhaul semantics.
- Test and document temper, charge, poison, favorite, hotkey, equipped,
  follower, container/display, renamed-item, and player-enchantment behavior.
- No polling loop, per-frame listener, per-hit global listener, popup, or
  unsolicited notification is introduced.
- Automated xEdit validation reports no ITMs, deleted records, unresolved
  masters, stale visual winners, duplicate recipes, or non-light FormIDs.
- A new game and an existing disposable save both complete the recorded test
  matrix before promotion to the playable baseline.

