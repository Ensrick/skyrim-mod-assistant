# Patch intents - mods kept for a custom patch, not for a stock install

Mods land here when the user wants the ASSETS or IDEA but the mod as shipped
would not survive the build's existing decisions. Each entry records what the
mod is, why the stock install does not work, and what the user actually intends
to do with it. Without that last part a keep months from now looks like a
mistake and gets reverted.

This is a working queue, not a commitment: nothing here is installed, and an
entry can be dropped once the user decides the payoff is not worth the patch.

Format per entry: what it ships, why stock fails, the intent, and the concrete
patch work that intent implies.

---

## Skyking Guard Shields - Complex Parallax and PBR (189146)

Kept 2026-08-26. v1, released 2026-08-21.

**What it ships.** A from-scratch rebuild of the vanilla hold-guard shields:
new meshes and textures for all nine holds plus the blank/Stormcloak shields,
in Complex Parallax and PBR variants. Replaces vanilla paths under
`meshes\armor\stormcloaks\shield*.nif` (verified from the archive: 39 payload
files, all under `PBR\meshes\armor\stormcloaks\` and its texture tree).

**Why a stock install does nothing.** Sons of Skyrim (68656, installed and
enabled) is the decided guards/Stormcloaks overhaul. It adds 26 new shield
records pointing at its own meshes under
`Meshes\NordWar\SonsOfSkyrim\<Hold>\Shield*.nif` and rewrites the guard outfits
to use them, so the guards you actually see never render the vanilla shield
meshes Skyking replaces. It does override a few vanilla records (Whiterun and
Winterhold guard shields, MS06 quest shields) that keep vanilla paths, so a
handful of Skyking shields would show - a rounding error, not a reason to
install. Second blocker: Complex Parallax and PBR both need Community Shaders,
which is parked with no 1.7.99 build, so the headline feature cannot render
today regardless.

**User intent (2026-08-26).** "If I like them enough, I can find a way to get
those textures/models mixed in with Sons of Skyrim." The shields are wanted as
ART, to be married to the Sons of Skyrim guard system rather than installed
alongside it.

**What that patch would take.** Three routes, cheapest first:

1. *Redirect* - point Sons of Skyrim's shield ARMO/ARMA records at Skyking's
   meshes. Cheapest (a plugin-only patch, no asset work) but it discards Sons
   of Skyrim's per-hold shield designs, which are a large part of why that mod
   was chosen. Only sensible if the user prefers Skyking's shapes outright.
2. *Reskin* - keep Sons of Skyrim's meshes and author PBR/parallax textures for
   them using Skyking's material work as the reference. Preserves both mods'
   intent and is the likely "mixed in" the user means, but it is real texture
   work, not a patch, and it only pays off once Community Shaders is unparked.
3. *Coexist* - install Skyking only for the vanilla shield records Sons of
   Skyrim does not override. Nearly free, but the visible payoff is the few
   shields noted above.

**Gate.** Do not start any of these until Community Shaders ships 1.7.99
support; without it the PBR path is unrenderable and route 2 cannot even be
evaluated on screen. Revisit at CS unpark.

## Master distribution mod (user intent, 2026-08-29)

Standing plan, stated during the keep review: **any weapon or armour mod that
enters this build will need a distribution patch authored in-house**, because
most authors either ship no acquisition path at all or bolt their items onto
crafting menus and leveled lists crudely. Those individual patches are
temporary - they get merged into a **single master mod distributed with the
modlist** whose job is putting modded weapons and armour onto the right NPCs
across the whole load order.

Consequences for this review pass:

- "No in-game acquisition path" is NOT by itself a reason to skip a weapon or
  armour mod. The question is whether the assets and records are worth
  patching.
- Judge those mods on mesh/texture quality, record hygiene (keywords, material
  and impact data - a weapon missing WeaponMaterial/WeaponType keywords is
  invisible to keyword-driven distribution), and balance against the vanilla
  tier it claims.
- Permissions matter more than usual: the master patch is intended to be
  distributed with the modlist.

The mandatory intake schema and decision gates now live in
`docs/EQUIPMENT_INTAKE_POLICY.md`. Codex, Claude, and delegated agents must use
that process for **every** adopted weapon, shield, armor, clothing,
undergarment, or jewelry mod. Installation alone does not close integration:
each added item needs an explicit primary role, balance baseline, acquisition
implementation, permission boundary, patch owner, compatibility audit, and
verification route.

### Baltimore Weapons (29612)

Installed 2026-08-30 as the first full intake example. Billyro's plugin adds
six weapons and two bucklers, all craft-only as shipped. The initial
recommendation is constrained generic distribution—professional mercenaries,
regional raiders, selected veteran/leader archetypes, and future custom enemy
templates—not unique artifacts, creature equipment, or universal bandit-list
injection. Final item roles and balance remain user decisions on [issue
#66](https://github.com/Ensrick/skyrim-mod-assistant/issues/66). Vendor files
remain immutable; any balancing/distribution work belongs in an owned,
preferably ESP-FE patch and the future master distribution system.

## Protected vanilla gear (user constraint, 2026-08-29)

Stated while reviewing the NordwarUA armour family. Armour and weapon mods are
wanted **alongside** vanilla gear, not as wholesale replacers. These vanilla
items are protected and must not be overridden without the user saying so:

| protected | note |
|---|---|
| Iron armor | he likes the vanilla look |
| Iron **helmet** | the ONE exception - he dislikes it and wants it replaced |
| Iron weapons | Believable Weapons already makes these look right to him |
| Steel weapons | same reason |
| Steel Boots | vanilla look preferred |
| Steel Gauntlets | vanilla look preferred |

Undecided, needs a per-mod report before he rules: **Leather, Hide, Padded**.

Practical consequence: for any armour overhaul, prefer the variant that
distributes new armour to NPCs while leaving vanilla ARMO records untouched.
Realistic Armor (36151) ships exactly that split - its `Standalone_ESP` variant
drops the 28 vanilla ARMO overrides and keeps the 91 NPC_ overrides. Where no
such variant exists, the fix is an in-house patch forwarding the vanilla record.

Additive-only mods (Steel Plate Armors 154073, Scale Nord Armor 41118) raise no
protection problem at all; they raise a distribution problem instead, which the
master distribution mod above solves.

### Believable Weapons is the base layer, not the ceiling (user, 2026-08-29)

Clarifying the protected-gear rule above. Believable Weapons owns the **generic**
iron and steel weapon meshes and must not be bypassed there - that is what the
Realistic Armor patch in #57 protects.

It does NOT extend to **unique or named weapons**. The user's words on Legacy of
Ysgramor taking over the five Skyforge Steel weapons: "Skyforge Steel used to
simply be regular Steel-looking, so this is a great change to make it less
generic." Decision: leave that swap in place, no patch.

So the test for a weapon-model override is which layer it lands on. Generic
vanilla tiers stay Believable Weapons; a named or unique weapon getting a
distinct model is an improvement, not a conflict.

Corollary he noted himself: because these overrides move the **mesh path** and
not the texture, texture replacers still layer normally over Believable Weapons.

## Balance and distribution are process, not questions (user, 2026-08-30)

"We open issues for the balancing, and distribution etc. You know this is part
of the process now. Why must I repeat myself."

When an intake audit finds inflated stats, absent leveled-list or NPC placement,
a reverted USSEP record, a missing perk gate, an over-cap texture, or a similar
defect: **open the issue with the evidence and a proposed approach, cross-
reference the master distribution issues, and report that it was tracked.** Do
not put it to the user as a decision.

Questions are reserved for what only he can answer: taste and art direction,
sexual content, which rival wins a contested slot, and whether to accept a real
trade-off or spend money.
