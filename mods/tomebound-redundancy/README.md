# Ensrick - Tomebound Redundancy Patch

A first-party replacement for the third-party "Apocalypse and Tomebound Duplicate
Spells Patch" (Nexus 32231). The user chose to author our own rather than inherit
another author's taste, so every decision below is ours and every one of them is
argued from the records rather than from a mod page.

**What it does.** It removes redundant entries from *distribution only*. Nothing
else. No `SPEL`, `BOOK`, `SCRL` or `WEAP` record is edited, renamed or deleted,
so every spell, tome, scroll and staff named below still exists, still works, and
is still obtainable from the console:

```
help "Conjure Lich" 4
player.additem <formid> 1      or      player.addspell <formid>
```

That is deliberate and matches the behaviour of the third-party patch it
replaces: a spell that loses its shop entry has not been taken away from you, it
has just stopped competing for the same slot on the same merchant's shelf.

## How the two mods actually distribute, and why that matters

Neither mod edits a vanilla leveled list to place its tomes, which is why a naive
"patch the vanilla lists" approach would do nothing at all:

- **Tomebound** ships **69 of its own leveled lists** (`UDLC01LItem*`) which a
  quest script, `UDLC01AddMagicItemsQuest` (`385F60:Tomebound.esp`), injects into
  merchant chests at runtime. Its only five vanilla `LVLI` overrides
  (`LItemSpellTomes00AllSpells` and friends) add no entries of its own.
- **Apocalypse** ships **83 distribution form lists** (`WB_F_LItem*`) which its
  own populate quests copy into the matching vanilla lists. It overrides **zero**
  vanilla leveled lists.

So this patch overrides Tomebound's own `LVLI` records and Apocalypse's own `FLST`
records. Both are unconflicted in the current profile: the only active plugin
mastering Apocalypse is `WeaponBalancePatch.esp`, which holds 3,504 `WEAP` records
and no list of any kind, and the only plugin mastering Tomebound is its own
Immersive Sounds patch, which holds 14 `MGEF` records. Each record here is
therefore a copy of the winning version with entries dropped.

## Decision table

Seventeen distinct items lost their distribution entries, across 30 entry
instances in 22 container records. "Kept" names the twin that survives.

| # | Duplicate pair | Evidence from the records | Kept | Why |
|---|---|---|---|---|
| 1 | **Conjure Lich** — Tomebound `08429A` (Expert `0C44BD`, 366) vs Apocalypse `01236A` (Adept `0C44BC`, 244) | Same display name. Both a lone `SummonCreature`, 60 s, FireAndForget/TargetLocation, summoning an NPC whose Name is literally "Lich" at PcLevelMult 1 | **Apocalypse** | Apocalypse's is rung 3 of a designed five-rung undead ladder (`WB_Con_Undead1`..`Undead5`) whose Master capstone Conjure Nether Lich stays distributed, so pulling rung 3 would leave a hole. Tomebound's is standalone and its Skeleton and Draugr ladders survive intact. The Lich is not a player summon in Morrowind or Oblivion, so the lore-port tiebreak does not apply to either side |
| 2 | **Ice Barrage** — Tomebound `17C4AF` (Adept `0C44C0`, 164) vs **Frost Nova** — Apocalypse `1347EE` (Adept `0C44C0`, 136) | Same perk tier, same area 25, same riders: Slow 50 for 3 s plus a 3 s Paralysis. Tomebound deals 35 in one ring, Apocalypse 30/15/15 in three | **Apocalypse** | One spell entered twice. Apocalypse's tiered rings are the richer implementation and sit inside its Frost ladder. "Barrage" is not a Morrowind or Oblivion spell name, so Tomebound holds no lore claim |
| 3 | **Shock Barrage** — Tomebound `17C4B3` (Adept `0C44C0`, 169) vs **Shock Nova** — Apocalypse `00186D` (Expert `0C44C1`, 375) | Identical signature rider: Disintegrate, magnitude 200, duration 1 s, area 25. Same area, same delivery | **Apocalypse** | Not two spells side by side. This is Apocalypse's Expert capstone undercut by a cheaper copy of itself one tier down, 169 magicka against 375, which would make the Expert spell pointless to ever buy |
| 4 | **Conjure Skeleton Minion** — Tomebound `074F72` (Adept `0C44BB`, 143) vs Creation Club `00085B:ccvsvsse003-necroarts.esl` (Novice `0F2CA7`, 107) | Same display name, both `SummonCreature` 60 s FireAndForget/TargetLocation | **Creation Club** | Base-game Anniversary Edition content the rest of the build assumes, and rung 1 of the Necromantic Grimoire's own skeleton ladder. Patching a Bethesda Creation Club plugin would add a master and a maintenance burden for nothing |
| 5 | **Conjure Skeleton Warlock** — Tomebound `1E6A8D` (Expert `0C44BD`, 351) vs Creation Club `00084E:ccvsvsse003-necroarts.esl` (Expert `0C44BD`, 258) | Same display name **and** the same perk tier. Both `SummonCreature` 60 s FireAndForget/TargetLocation. The strongest duplicate in the set | **Creation Club** | As above: base-game content, part of the Grimoire ladder, the more deeply integrated of the two |
| 6 | **Detonate Lock** — Apocalypse `00AB69` (Expert `0C44B9`, 595) vs Tomebound's **Open Novice/Apprentice/Adept/Expert Lock** (`246DE2`, `246DE3`, `246DE5`, `246DE7`) | Tomebound adds a full four-rank unlocking ladder, Novice (30) to Expert (244). A scan of all 373 Apocalypse spells finds exactly one Unlock rung, `WB_Alt_Unlock4_Spell_DetonateLock`, at Tomebound's top tier | **Tomebound** | The lore-port case: "Open" is the Morrowind and Oblivion Alteration spell and Tomebound ports the whole graded ladder, while Apocalypse's single rung is the generic stand-in. Removing it breaks no ladder because there is no ladder to break |
| 7 | **Dispel Magic** — Apocalypse `00BB25` (Novice Illusion `0F2CA9`, 55) vs **Dispel** — Tomebound `153CA0` (Novice Restoration `0F2CAA`, 47) | Both Novice self-cast dispels at near-identical cost. A scan of all 373 Apocalypse spells finds exactly one Dispel rung, `WB_Ill_Dispel1_Spell_DispelMagic` | **Tomebound** | Dispel is the Morrowind and Oblivion Mysticism spell and Tomebound is the lore-sourced port; Apocalypse's is the generic copy relocated into Illusion. The removed one is better in exactly one respect, a 40-unit area against Tomebound's self-only, recorded here so the call can be revisited |

Each surviving spell keeps its scrolls and staves; each removed spell loses its
matching scroll and, where one existed, its staff, so that the removal does not
leave a scroll on a shelf teaching a spell no merchant sells. That accounts for
the 17 items: 7 tomes, 8 scrolls and 3 staves, once duplicated list membership is
collapsed.

## Claims from the third-party patches that the records do NOT support

Four of the seven changes in Nexus 32231, and most of the premise of "Simple
Tomebound" (Nexus 181265), do not survive a check against the installed plugins.
They were enumerated rather than trusted, and rejected:

- **"Scorching Hands is redundant with Tomebound's Touch spells."** Rejected.
  Scorching Hands (`02388C`) is Concentration/Aimed, Expert, magnitude 80 over an
  area. Tomebound's Burning Touch (`102C00`) and Flame Touch (`13F870`) are
  FireAndForget/TargetActor single hits of 10 and 25 at Novice and Apprentice.
  Different cast type, different tier, an order of magnitude apart.
- **"Tomebound's hindrance tomes duplicate Apocalypse's slow spells."** Rejected.
  A scan of all 373 spells in the installed Apocalypse 10.3.0 finds **no** slow,
  snare or hinder ladder at all. Tomebound's Hinder has no rival and stays.
- **"Apocalypse's disease spells duplicate Tomebound's poisons."** Rejected.
  Apocalypse ships a designed four-rung disease ladder (`WB_Res_Disease2`..
  `Disease5`), all script archetypes with spreading and proc behaviour.
  Tomebound's poisons are plain damage-over-time on Health with a paralysis
  rider. Same theme, different mechanism; removing either deletes real content.
- **"Tomebound's Barrage tomes duplicate Apocalypse's Novas."** Partly rejected.
  True for Ice and Shock. False for **Flame Barrage** (`1815DE`): Apocalypse has
  only two Nova spells, Frost and Shock. Removing all three, as the third-party
  patch does, would leave the fire line with no area burst at that tier, so
  Flame Barrage is kept.
- **"AE and CC content makes Tomebound bloated."** Largely rejected. Of every
  vanilla or Creation Club spell sharing a name with a Tomebound spell, Night Eye
  (Khajiit power and werewolf ability), Poison and Poison Cloak (spider and
  Gloomwraith NPC abilities), Silence (a perk effect and Neloth's scripted
  spell), Waterwalking (a Dragonborn ability), Weakness to Fire (the vampire
  ability line) and Burden (a Ruin's Edge bow enchantment) are abilities, powers,
  perks or enchantments. **None has a spell tome anywhere among the 155 vanilla
  and Creation Club tomes on disk**, so none is obtainable as a player spell and
  none makes Tomebound's version redundant. Only three real collisions exist, all
  with Necromantic Grimoire, and two of them are rows 4 and 5 above.
- **Soul Split** is the third. It is a **name collision only** and both are kept:
  Tomebound's (`03833A`) is Expert, Aimed, draining Health, Magicka and Stamina by
  45 for 30 s plus a Soul Trap; the Creation Club's (`000874`) is Adept,
  TargetActor, one effect for 60 s. Different spells that happen to share a name.
  Removing either would cost real content, so the shared name is recorded for the
  user to decide rather than resolved unilaterally.

## Deliberately out of scope: fast travel

Tomebound's teleport content is **untouched**: the 13 Planewalk destination tomes,
Mark (`36CA4A`) and Recall (`376C50`), and on the Apocalypse side Milestones
(`0A59D5`) and Monarch Mark (`161621`). "Simple Tomebound" strips these for
survival reasons, which is a taste about how the world should be crossed, not a
redundancy. It overlaps the user's undecided travel design, so it is raised as a
question on issue #67 instead of being decided here.

## Build

The `spriggit/` YAML tree is the source of truth and is what gets reviewed; the
plugin is a build artifact and is not committed.

```
pwsh mods/tomebound-redundancy/regenerate.ps1
```

That runs Spriggit 0.41.0 `deserialize` over `spriggit/` and writes
`package/Ensrick - Tomebound Redundancy Patch.esp`. Two consecutive builds are
byte-identical (SHA-256 `D2CBC8EF1D303733537F40BCA35B559D82723F6A1AA5E7BAE32C54CC77D53C5D`,
6,292 bytes), and serializing the built plugin back to YAML reproduces the source
tree with zero differing records.

`build_spriggit.py` regenerates the YAML tree itself from `policy.json` and the
Spriggit serialisations of Tomebound and Apocalypse. It only needs re-running if
either of those mods is updated. It refuses to emit an empty patch and refuses to
empty any list; the smallest list here still holds 2 entries.

## Distribution

Not distributable as-is. The plugin is override-only and carries no assets, but
every record in it is a copy of a Tomebound or Apocalypse record, so it is a
derivative work of both. It is built locally from committed text for this profile
and is not uploaded.
