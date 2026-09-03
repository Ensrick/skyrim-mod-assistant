# Morning report - 2026-09-03

Everything you raised in your last two messages, plus what ran overnight.
Nothing new was installed except fixes to mods you already have, per your
instruction. Every mod named is a link.

**Game state: working and verified.** Last PASS
`records/launch-verify-20260902-231840.md` - main menu 32.0 s, save loaded
40.4 s, 0 SKSE plugins refused. You can play without touching anything.

---

## 1. What I fixed while you slept - no new mods, our own bytes

Three Ensrick patches, built, installed and covered by that PASS. Commit
`9b62742`.

### Cloaks: fur everywhere, Cloaks of Skyrim nowhere, and guards wearing two

Your report was exactly right and the cause was worse than the first
diagnosis. Entry counts (21 CoS : 115 fur) were the smaller half. The dominant
lever is `chanceNone`: **every Pelts list rolls 0, while the twenty Cloaks of
Skyrim lists roll 25-90** - 2017 numbers from when CoS injected into vanilla
lists directly rather than through RMB's shared graph.

Measured over the real patched graph, a generic NPC's cloak was **1.0% Cloaks
of Skyrim, 54.8% fur**. That is your "I don't ever recall seeing the cloaks of
skyrim", as a number.

**The doubles were a slot collision.** All fourteen outfits RMB injects a guard
cloak list into are Sons of Skyrim overrides that *already* carry a hold cloak.
[Pelts 'o' Plenty](https://www.nexusmods.com/skyrimspecialedition/mods/120726)
sits on biped slot **57**; Sons of Skyrim uses **46**. A guard wears both.
Bandits and faction NPCs never doubled, because their outfits hold no
cloak-slot item - which matches what you saw.

**Now:** 55.0% of covered non-guard NPCs wear no cloak at all, Cloaks of
Skyrim is 23.8% of the rest (20-60% on faction NPCs), and guards wear exactly
one.

Five vendor defects were fixed on the way: a dead `Cloaks - Dawnguard` list
pointer, two "Dark" CoS lists left in fur-only buckets, nine entry-identical
`UNUSED` trimmed lists, and RMB gating both `B5F` *and* its children at 35,
which compounds to 58% cloakless instead of 35%.

**Four dials, each one number in a labelled block** of
`overlays/ensrick-cloak-distribution-balance/.../Ensrick - Cloak Balance.ini`:
guard second-cloak (100), CoS:fur ratio (0 = parity), overall frequency (55),
warm-bucket parity (on).

> **One thing to check in five seconds of play:** the agent could not prove
> from disk that SkyPatcher's *later* `chanceNone` replaces an earlier one -
> file order is proven from the log, the merge rule is not. If it is
> first-write-wins, three of the four dials are no-ops. **The tell is a guard
> still carrying two cloaks.** If you see one, tell me and I will rewrite the
> approach.

### The dragon-priest cloaks now actually place (#187)

RMB's ten unique-cloak directives pointed at `Skyrim.esm` form IDs that do not
exist, so all nine dragon-priest cloaks and Idolaf's never appeared - and those
are the textures the audit measured as base CoS's **best**. Krosis' filter was
also truncated (`767` instead of `100767`). Ours is a new file loading after
his, because
[RMB SPCH](https://www.nexusmods.com/skyrimspecialedition/mods/116030) forbids
editing his. It failed silently because SkyPatcher logs no miss on an npc
`objectsToAdd`.

### Death hound dog meat (#199)

The drop is **vanilla Dawnguard** - `DLC1DeathItemDeathHound` (`00D6F7`),
unoverridden across all 327 plugins. Removed rather than adding a
[Simple Hunting Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/95943)
harvest entry, because SHO's meat branch gates nothing: it adds a tracker and
returns, and time and XP are charged only on a **pelt**, which a death hound
does not have.

---

## 2. Wolves (#42) - analysed, and one finding overturns the plan

### The visual mod you named does not solve it

[FluffWorks](https://www.nexusmods.com/skyrimspecialedition/mods/56361)
measurably does not fix the monster look: it adds 16 fur-shell shapes to the
**vanilla** `wolf.nif` (2 to 18) and ships **no wolf diffuse at all**. The
vanilla head and silhouette survive untouched. The thing you object to is the
shape, and FluffWorks does not change it.

**Suggestion, not installed:**
[Canidae - A Wolf Replacer](https://www.nexusmods.com/skyrimspecialedition/mods/182994)
2.25, core option only. It is the only candidate that changes the shape - 8
`BSTriShape` shapes with proper dismember instances. Distance test against the
vanilla texture each displaces: `wolf_head` x0.90, `icewolf_head` x1.40,
`icewolf_body` x0.97 - with **`blackwolf_body` failing at x0.54**, salvageable
to x0.89 by our resharpen recipe. Two defects, one recipe fix each. Rivals are
worse: Wolves of Skyrim's normal map measures x0.46; Savage Wolves replaces the
skeleton.

### The behaviour fix is a single field

`EncWolf` and `EncBear` are **both** Unaggressive, with identical WarnOrAttack
2000 and Attack 1500. The only difference is **`Warn`: bear 2500, wolf 0.**
Bears warn; wolves go straight to attacking at 1500 units (~21 m). `EncHorker`,
your other example, is Aggressive but only inside 320 units. `EncWolfRed`
inherits from `EncWolf` by template, so one edit covers both, and **no faction
change is needed** - nothing in any faction makes a wolf hostile to you.

### Fewer encounters, bigger packs - both, at once

`LCharWolf` is placed **zero** times, so the leveled list was never the
population. It is **666 placed references** on regional predator actors, each
rolling independently - expect ~535 wolves at level 1. Clustered at 2000 units:
**406 clusters, of which 205 are singletons.**

Retiring only the singletons (Initially Disabled, never deleted) gives **461
refs in 201 clusters, mean pack 2.29, and no lone predator anywhere** - a 31%
cut that *raises* pack size to exactly the 2-3 you asked for. The noise was
never the packs; it was the lone wolves.

The 205 freed positions are already navmeshed and have been handed to **#43**
(Sol's) for the hostile-monster replacement you asked for.

---

## 3. UI and the survival readout

**Nordic UI is not the meta - it is the opposite.** Across the 19 curated lists
in our ecosystem survey, NORDIC UI scores **0/19**; it survives only in one
alpha export. The actual skins are Dear Diary Dark Mode and Untarnished at 7/19
each, Edge UI at 3/19.

**Your floating-healthbar objection does not disqualify TrueHUD.** It is the
mod that adds them and it is 17/19, but the bars are configurable - turn them
off, keep the rest.
[TrueHUD](https://www.nexusmods.com/skyrimspecialedition/mods/62775) 1.1.10 and
[moreHUD](https://www.nexusmods.com/skyrimspecialedition/mods/12688) 5.4.2.0
both **PASS** the corrected version gate.

**Hunger and warmth as bars, no numbers.** The globals are live and
proportional here - hunger 0/120 from Starfrost, cold 55/900 from Survival Mode
Improved. The obvious pick is wrong: iWant Widgets *for Starfrost* reads magic
effects and is invisible below stage 3, and **Survival Control Panel is not the
route at all** - it is a config framework with no meter.

**Recommendation: we author `Ensrick - Survival Meters`** on
[iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457)
1.33 - MIT, **no DLL**, needs only SkyUI - using its native `setMeterPercent`.
Real bars, no numbers, and distributable as our own work. That needs your yes
on adopting iWant Widgets as the framework.

Three candidates **FAIL** the gate and are rebuild-or-skip: Prisma UI, Skyrim
Party Sheet, iWant Widgets NG.

---

## 4. Everything else from yesterday

- **Open Animation Replacer is live** (#140 closed in effect). No rebuild was
  needed - Ersh shipped 3.2.1 on 2026-08-31. The root cause is proven: 3.2.0
  lacked `load_v5`, hit "Unsupported address library format: 5", and **raised a
  modal**; the SKSE plugin loop blocked on a dialog nobody could see. It never
  hung. Own PASS launch.
- **IED is permanently dead** (#94). Source is gone - no release since
  2023-12-10, 51 of 74 headers missing, and Software Heritage holds no copy
  past 2022-02-12. MIT licence, so permission was never the obstacle. **#201**
  proposes [AllGUD](https://www.nexusmods.com/skyrimspecialedition/mods/28833)
  as the only DLL-free route to visible carried gear - which your #36 inventory
  rule cannot ship without. Suggestion only.
- **Block animation (#198): OAR is ruled out, but not everything is.** The
  build's entire OAR payload is Pandora's XPMSE conversion - 164 animations
  across 30 sub-mods, with **no block group**; the only block-named file in the
  whole output is `shd_blockbashsprint.hkx`, which is shield *bash* while
  sprinting. No `mt_behavior.hkx`, `1hm_behavior.hkx` or `shield.hkx` was
  generated either.
  **Correction, caught overnight by a second agent re-deriving it from disk:**
  an earlier version of this line said the hypothesis had "no generated
  behaviour to live in". That was overstated, and it came from a case-sensitive
  search miss. `0_Master.hkx` **is** generated, in both skeletons - 585,136
  bytes third-person and 472,688 first-person - and it is the root graph that
  dispatches block states. So the honest statement is narrower: no OAR
  animation and no block-*specific* generated behaviour can be the cause, but
  **the regenerated master graph is not excluded**. It is a live candidate
  alongside
  [SkyParkour v3](https://www.nexusmods.com/skyrimspecialedition/mods/136980),
  which means an A/B that only toggles SkyParkour will not clear it.
  **This one needs you**, see below.
- **No looting in combat.**
  [No Loot During Combat](https://www.nexusmods.com/skyrimspecialedition/mods/173769)
  is exactly your ask - blocks corpses and chests in combat, ground pickup
  unaffected - but its DLL is stamped 2026-03-01 and **FAILS** the gate.
  [No Loot When Armed](https://www.nexusmods.com/skyrimspecialedition/mods/143253)
  also fails (2025-04-22) and keys off weapon-drawn rather than combat anyway.
  Both are rebuild candidates, not installs.
- **Better Jumping is in and verified** - its own launch, not a shared one.
  Nothing supersedes it; the alternatives are animation layers or a different
  mechanic entirely.
- **Our SKSE gate had a 15-month hole.** Its PE-stamp reject window ended
  2025-05-26, but format 5 support landed 2026-08-21. That is exactly how Smart
  Talk got in and killed your launch. Fixed (`c3da884`); zero new failures
  across all 40 SKSE DLLs in your 232 enabled mods.
- **Inventory design (#36)** captured in both directions: the second inventory
  is back in for crafting and alchemy accumulation, with armour and weaponry
  capped in it; on-person weapons still need a body slot and still display, two
  daggers packed excepted; quest items still not exempt.

---

## 5. Decisions waiting on you

1. **Adopt [Canidae](https://www.nexusmods.com/skyrimspecialedition/mods/182994)
   for wolves?** It is the only mod that fixes the shape. Needs two recipe-class
   repairs from us.
2. **Adopt [iWant Widgets](https://www.nexusmods.com/skyrimspecialedition/mods/36457)
   so we can build your hunger/warmth bars?** MIT, no DLL.
3. **[TrueHUD](https://www.nexusmods.com/skyrimspecialedition/mods/62775) with
   floating bars off?** Or skip it entirely.
4. **Cloak enchantability** - still open from the cloak audit. Both RMB config
   options are omitted until you say; each is one file.
5. **The armour/weapon cap in secondary storage** (#36) - item count, weight
   budget, or slot count. It is load-bearing: without it the second inventory
   becomes the loophole that defeats the design.
6. **Cloak dials** - the four numbers above, if the defaults are not to taste.
7. **[AllGUD](https://www.nexusmods.com/skyrimspecialedition/mods/28833)** (#201)
   - the only path left to visible carried gear.

## 6. One thing only you can do

**#198, the block animation.** No headless instrument here can see whether a
shield is raised. Next time it fails, note: what you were doing (walking,
strafing, sprinting, turning), what was equipped (shield, one-hand, two-hand,
spell), and whether it recovers on releasing and re-pressing block. Three data
points separate a movement-state condition from a weapon-state one, which
decides where to look next.

**And glance at a guard's cloak** - see the warning in section 1.
