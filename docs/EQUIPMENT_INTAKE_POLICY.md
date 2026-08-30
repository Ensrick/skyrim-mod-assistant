# Equipment-mod intake policy

This policy applies to every adopted mod that adds a weapon, shield, armor,
clothing item, undergarment, or piece of jewelry. It is mandatory for Codex,
Claude, and delegated agents. A successful MO2 installation is the start of
equipment adoption, not the end.

The policy exists to prevent two common failures: attractive equipment that is
technically installed but can only be reached through the console or a crowded
forge menu, and equipment that is distributed broadly without a deliberate
place in the setting. It also supplies the structured input for the planned
master distribution mod, custom enemy NPCs, and **No Mere Bandits**.

## Required intake record

Every equipment-bearing mod must have a durable audit record and a GitHub
issue, or a clearly named section of an existing equipment-family issue. The
record must include:

1. **Provenance and installation.** Nexus game/mod/file identifiers, author,
   version, source filename, SHA-256, installed MO2 folder, transaction, plugin
   list, selected installer options, dependencies, enabled state, curator
   state, and whether the author had to be removed from Excluded.
2. **Exhaustive item inventory.** Every added item by display name, EditorID,
   FormKey, type, model, equip/body slot, and any alternate variants. Do not
   summarize a multi-item pack as one weapon or one armor set.
3. **One explicit primary role per item.** Choose exactly one:

   - **Unique or named:** belongs to a specific NPC, quest, place, encounter,
     or artifact role and must not enter generic pools.
   - **Generic distributed:** may appear through constrained leveled lists,
     vendors, loot, outfits, SPID, SkyPatcher, or the owned distribution
     system. Record level gates, rarity, eligible archetypes, and exclusions.
   - **Faction, creature, or NPC-specific:** reserved for a named or described
     group such as guards, Companions, Forsworn, Falmer, Draugr, skeletons,
     custom enemies, or one NPC class. Record the exact target allowlist.
   - **Deliberately craft-only:** intentionally learned or made by the player.
     Record why world distribution is unwanted and how the recipe is gated.

   “As shipped” and “intended for the modpack” are separate fields. A vendor's
   forge-only implementation is evidence, not an automatic design decision.
4. **Balance baseline.** Identify the nearest current-load-order comparison and
   record damage or armor, critical damage, speed, reach, stagger, weight,
   value, armor class, warmth where applicable, enchantment, equip slots,
   material/type/vendor keywords, tempering material, crafting costs, perk
   gates, and improvement-perk behavior. Note every deliberate deviation.
5. **Acquisition implementation.** State whether the item uses a quest or
   placement, merchant/loot/leveled distribution, an NPC/outfit assignment,
   the future master distribution system, or a retained crafting recipe.
   Record minimum levels, rarity, enchanted variants, respawn behavior, and
   worldspace or faction limits where relevant.
6. **Compatibility.** Audit asset-path collisions and plugin override chains,
   then check keyword consumers, animation type, first-person and sheathed
   meshes, body/skeleton fit, physics, crafting menus, tempering, enchantment,
   survival warmth/carry systems, NPC outfits, and other active distributors.
7. **Permission boundary.** Quote or summarize the source permission, credit
   any incorporated assets, and state separately what may be used locally,
   committed to GitHub, shipped as an owned patch, or included in a public
   installer. A Nexus dependency does not become redistributable merely
   because an owned patch references it.
8. **Patch ownership.** Vendor archives and installed vendor files remain
   byte-identical and separate. Balancing, distribution, compatibility, and
   recipe changes belong in an Ensrick-owned overlay, preferably ESP-FE when
   technically safe, or in an original declarative distribution configuration.
9. **Verification criteria.** At minimum: resolved masters and links, exact
   target-record assertions, no accidental overrides, compact/light-plugin
   validation where applicable, deterministic regeneration, Spriggit round
   trip for owned plugins, LOOT/order audit, and a disposable runtime route
   covering acquisition, NPC use, loot, crafting/tempering, first/third-person
   visuals, and save continuity.

## Decision and implementation gates

- Installation may proceed when the user explicitly adopts the vendor mod.
- Installation does not authorize a subjective distribution or lore decision.
  Keep those item-role checkboxes open and return them to the user.
- Adoption is not considered integrated until every item has a primary role,
  a balance disposition, and an implemented acquisition path.
- Do not edit a vendor ESP to make it ESL. Compacting changes FormIDs and is a
  migration, not housekeeping. Prefer an owned light overlay; replace a vendor
  plugin only after an explicit, save-aware migration decision.
- Do not solve leveled-list conflicts by making one vendor plugin win. Express
  the chosen semantics in the owned distribution system or an owned patch.
- Never fabricate a navmesh, quest, or placed-reference merge. Escalate those
  cases to exact inspection and runtime/Creation Kit work.

## Master distribution and custom enemies

The future master distribution mod consumes the completed intake records. Its
rules should be allowlist-first, level-gated, and deterministic. Broad keywords
such as “Bandit” are insufficient when an item belongs only to a veteran,
regional group, cultural archetype, dungeon population, or named faction.

Custom enemy NPCs are first-class distribution targets. When **No Mere
Bandits** creates a new enemy archetype, link its equipment issue to the source
item issues rather than copying records or assets. Falmer, Draugr, skeleton,
monster, guard, soldier, outlaw, and roaming-enemy pools remain separate unless
the user deliberately joins them.

The first complete worked example is [Baltimore Weapons issue
#66](https://github.com/Ensrick/skyrim-mod-assistant/issues/66).
