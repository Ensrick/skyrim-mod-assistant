# Cloak layer audit: what to install, and what we have to fix ourselves

Audit date: 2026-09-02

Runtime: Skyrim SE `1.7.104.0` / SKSE `2.3.1` / Address Library format 5.
MO2 instance `mo2-instances\skyrim-se`, profile `Default` (220 enabled mods,
238 active plugins).

Tracker: [issue #95](https://github.com/Ensrick/skyrim-mod-assistant/issues/95).
Companion record, same day, covering the NPC weather-framework half of #95:
`records/cloak-framework-rebuild-2026-09-02.md`. This record covers the asset,
record and distribution half only.

Supersedes the asset half of
`records/modern-cloak-system-research-2026-08-30.md`, which ranked candidates on
page copy rather than on measurement. Three of that record's conclusions are
reversed below.

**Disposition: audit only.** Nothing was installed, no profile file was
touched, no curator state changed, and the game was never launched. Archives
were fetched to the MO2 download/audit cache and extracted to `downloads\x*`
outside `mods\`.

**2026-09-02 addendum.** Section 7 adds ElSopa's Cloaks Of Skyrim Retextured
`42558`, brought by the user after the first pass. It changes the asset
recommendation and forces a mesh decision; the executive answer, the distance
table, the recommended stack and the fix-up list below are updated for it. The
user also settled the fur bake-off in the same message: **Pelts 'o' Plenty wins,
Winter Is Coming is out** (*"I don't like the fake fur from winter is coming"*).

---

## Shortlist: only the user can settle these

Everything else in this record is decided by evidence. These are taste, or a
trade-off he owns. Item 2 is already settled and kept for the record.

1. **Which Cloaks of Skyrim families do you actually want?** The 120 cloaks
   split three ways (full editor-ID lists in "Item inventory" below):
   **57 generic** colour/burlap/linen variants, **40 hold and faction**
   (per-hold guard heraldry, Stormcloak, Imperial, Thalmor, Forsworn,
   Greybeard, College, Necromancer), **23 unique/named** (9 dragon-priest
   cloaks, Vaermina, Red Eagle, Himir's Hide, the Dwemer ceremonial pair, and
   the enchanted Health/Resist pairs). Note before you answer: **Sons of Skyrim,
   already installed, ships eleven of the hold cloaks itself** on the same slot
   46 (measured below). So the hold group is a *civilian* and *variety*
   argument, not a "guards have no cloaks" one. The 23 unique cloaks and the 57
   generic variants have no substitute anywhere.
2. **SETTLED 2026-09-02 by the user: Pelts 'o' Plenty `120726`.** His words:
   *"I don't like the fake fur from winter is coming. Pelts o Plenty is vastly
   superior."* Winter Is Coming `4933` and its RMB SPCH patch `116029` are OUT
   of the plan; the measured hf x0.94 vs x0.75 gap did not decide it, taste did,
   which is what this shortlist item existed for. Consequence for the fix-up
   queue: Pelts ships 54 of 96 textures with **no mip chain at all**, so #188
   (mip regeneration) now has to cover Pelts as well as the 19 CoS textures.
   Original bake-off text follows.

   ~~**Bake-off, fur slot: Winter Is Coming vs Pelts 'o' Plenty.**~~ Measured at
   distance these are the two best assets in the whole audit and they are close
   (hf x0.94 vs x0.75, tone x1.01 vs x1.07 - both beat base Cloaks of Skyrim).
   WIC is 2016 hand-painted fur at 2K with a clean BC1 chain; Pelts is 2026, 4K,
   over 100 pieces, ships SMP, and is the only one with hoods - but 54 of its
   96 textures ship with **no mip chain at all**. Different looks, not different
   quality tiers. Pick by eye.
3. **Bake-off, ordinary cloth cloak: Bocksten vs Cloaks of Skyrim's plain
   cloaks.** Bocksten is the better *mesh* (a real SMP cloth rig - 4 of its 5
   NIFs reference `CloakSMP.xml` - nine dyed colours, a clean 38-record plugin)
   and the worse *texture* (hf x0.40 median, the softest cloth in the audit
   apart from the PBR pack; `cloak_blk_d.dds` is x0.24). CoS's plain 1K capes
   measure x0.51-x0.60, roughly 40% more detail at distance than Bocksten's
   median and more than twice its worst. Better drape, or better fabric?
4. **Do generic cloaks stay enchantable?** RMB SPCH ships a one-line optional
   config that adds `MagicDisallowEnchanting` to all 122. Base CoS makes every
   cloak an enchantable free slot-46 enchantment.
5. **Physics on other people's cloaks, or only yours?** FSMP in this build is
   capped at 5 simultaneous skeletons (receipt below) and those 5 are already
   contested by Vanilla Hair Remake SMP. Cloaks on NPCs will sometimes win that
   contest and freeze someone's hair instead. Cheap to try, cheap to revert.
6. **ElSopa's textures, or Artesian's physics, until the port lands?** New with
   section 7. ElSopa's mesh update and Artesian replace 381 of the same NIFs and
   cannot both apply: whichever loads later wins outright. ElSopa is a x1.16
   median improvement on the 2017 textures at play distance and a much larger
   one up close (64 normal maps against base CoS's 8); Artesian is the only
   thing that makes the cloaks move at all. The owned NIF port
   ([#193](https://github.com/Ensrick/skyrim-mod-assistant/issues/193)) gives
   both and is the recommendation; this only asks what to run in the meantime.
   The 36 dragon-priest meshes are unaffected either way - neither mod touches
   them.

Not a user decision, tracked as work: everything in "Fix-up jobs" below.

---

## Executive answer

**Install:** Cloaks of Skyrim `6369` as the **mesh source**, its textures
superseded by **ElSopa - Cloaks Of Skyrim Retextured `42558` at the 2k tier**
(file `170809`) **plus its Mesh Update 1.2** (file `263634` - mandatory, not
optional: the 2020 MAIN archives ship 394 Oldrim-format meshes and the update is
their Special Edition conversion). Drive the records with
**RMB SPCH - Cloaks of Skyrim `116030` 1.5.3**, backed by
**RMB SPIDified - Core Framework `63625`** and
**RMB SPIDified - Sons of Skyrim `83340`** - the second is not optional here,
because Sons of Skyrim already owns eleven slot-46 hold cloaks and RMB's shared
configs are what merge the two populations into one roll instead of a slot
fight. Add **More Scarves `149259` 1.4.0** for hooded capes, the only candidate
shipping Dynamic Armor Variants configs wired to Helmet Toggle 2, and
**Pelts 'o' Plenty `120726` 4.3.1** for fur (settled by the user 2026-09-02).

**Physics needs one owned step.** **Artesian Cloaks `17416`** remains the only
source of a real cloth rig for these cloaks - all 391 of its NIFs are direct
path replacers carrying `HDT TailBone*` chains where base CoS has
`SkirtBBone01-03`. But ElSopa's 394 meshes replace **381 of those same files**,
carry no SMP string, and are what bind his renamed textures. The two are
mutually exclusive as shipped. The fix is an owned NIF texture-path port
([#193](https://github.com/Ensrick/skyrim-mod-assistant/issues/193)); until it
exists the build picks **ElSopa textures without physics** or **Artesian physics
with 2017 textures** - shortlist item 6.

**Do not install:** Cloaks of Skyrim HD SSE PBR `178993` (measurably the worst
asset in the audit, beaten by a 2020 mod at a fifth of the disk cost, and
unrenderable in this build regardless); `Cloaks.esp` in any of its eight
variants; `Cloaks_SMP_Patch.esp`; the ElSopa **4k** tier (2,130 MB for a measured
x0.99, and the only tier with mip-less files); Winter Is Coming `4933` and
RMB SPCH - Winter is Coming `116029` (settled by the user 2026-09-02).

**We have to fix ourselves:** the Artesian/ElSopa NIF port, the 1 remaining
no-mip and 8 uncompressed base CoS textures plus Pelts' 54, the missing warmth
tier, RMB SPCH's ten broken unique-cloak assignments, and the whole distribution
layer for Bocksten and More Scarves. Seven jobs, classed in "Fix-up jobs" below.

---

## The measurement that decides most of this

`docs/CURATION_POLICY.md`, "Textures are judged at distance": a texture is
sampled at mip 0 only when the camera is close; at play distance the GPU reads
the 512-128 px band, and a replacer whose detail lives only in mip 0 reads matte
there.

None of these mods replaces a vanilla asset (`inspect_mod` reports 0 of N for
every one of them), so the inspector's vs-vanilla half cannot run. Instead each
candidate's cloth **diffuse** maps were compared at **matched pixel size**
against three vanilla clothing torso diffuses -
`clothes/beggarclothes/torsom_d.dds`, `clothes/farmclothes02/m/farmcloth02body1024.dds`,
`clothes/merchantclothes/torsof_d.dds` (all 2048 px, 11 mips). Ten diffuse maps
per mod, deterministic sample (`random.seed(11)`), median of the per-file
medians. Script: `audit/mip_retention.py` driven by
`records-work/cloak-audit-2026-09-02/dist_compare2.py`, output
`distance-detail.txt`.

**This comparison is cross-asset and therefore advisory.** A vanilla torso
diffuse packs a whole outfit into one map; a cloak diffuse is mostly one fabric
panel, so every cloak scores low in absolute terms. The **ranking between the
six** is the usable signal, because all six are the same kind of asset.

| Mod | Released | median hf | median tone | n |
|---|---|---:|---:|---:|
| Winter Is Coming `4933` | 2016 | **x0.94** | x1.01 | 10 |
| ElSopa CoS Retextured `42558` (see §7) | 2020 | x0.75-0.80 | x0.67-0.76 | 10 |
| Pelts 'o' Plenty `120726` | 2026 | x0.75 | **x1.07** | 10 |
| **Cloaks of Skyrim `6369`** | **2017** | **x0.72** | x0.76 | 10 |
| More Scarves `149259` | 2026 | x0.46 | x0.58 | 10 |
| Bocksten Cloak `138180` | 2025 | x0.40 | x0.33 | 10 |
| Cloaks of Skyrim HD SSE PBR `178993` | 2026 | **x0.31** | x0.27 | 10 |

The two oldest mods in the audit hold the most detail at play distance, and the
newest "HD PBR" package - which exists specifically to modernise Cloaks of
Skyrim - reads **2.3x softer than the 2017 originals it replaces**. That is the
"looks nice zoomed in, loses all texture zoomed out" failure named in the
curation policy, measured.

Where a file ships with no mip chain the number describes a texconv-regenerated
chain, i.e. the asset's potential, not what the game currently samples. Those
rows are marked in `records-work/cloak-audit-2026-09-02/distance-detail.txt`.

---

## Exact artifacts

Downloaded to `mo2-instances\skyrim-se\downloads`, extracted to sibling `x*`
directories. Not installed, not enabled, not staged into `mods\`.

| Candidate | Nexus | File | Bytes | SHA-256 |
|---|---|---|---:|---|
| Cloaks of Skyrim 1.2.1 | 6369 | `6369-18422.rar` | 79,305,564 | `03ef0b317a28bab42eb226c774e3fda1b3a522f14b0d6c38a53bc2a32d5cbab9` |
| RMB SPCH - Cloaks of Skyrim 1.5.3 | 116030 | `116030-749413.zip` | 30,552 | `6b7e6d867f4a2438cb10d8045119671e8d1af0bba71b8f95436f10cf15037e88` |
| RMB SPCH - Winter is Coming 1.4.6 | 116029 | `116029-749936.zip` | 35,483 | `bcace2e1ca5b2a17bff3cb460ee6898ca44099b969e94d9206a49e76868b560f` |
| Artesian Cloaks FOMOD 1.3.0 | 17416 | `17416-58843.7z` | 8,901,645 | `77ee81e57f6a5dfa792dca2682115d807baef49f8e06dafcd1f78010c0f338b3` |
| More Scarves 1.4.0 | 149259 | `149259-723968.7z` | 100,246,502 | `9b909da46bae6f083c4e28a9f81c02609ea8e3b0adf78b56452467bb98cc2c35` |
| Bocksten Cloak 1.1 | 138180 | `138180-612148.7z` | 25,408,378 | `d9e75694e48292060f3dfaeb1ff0a75524580ba3514321f0aeba4e5026037708` |
| Pelts 'o' Plenty 4.3.1 (Gear) | 120726 | `120726-704702.zip` | 740,094,589 | `cd48e207533666c39bb99e5cdebc2a7c2db9252484006de9dbfa5e225495e1a1` |
| Winter Is Coming 2.4 | 4933 | `4933-10466.7z` | 65,526,547 | `e549cfff4b8f4877fb66c025354663972a28a338ed270d06f2dd82cd659e5d78` |
| Cloaks of Skyrim HD SSE PBR 1 | 178993 | `178993-747777.zip` | 595,781,482 | `7b364084878f21d26a8249d6d4c4096c031620149b229abd970b65c6a15e29a1` |
| ElSopa CoS Retextured 4k | 42558 | `42558-170807.7z` | 724,105,987 | `3dba5aa51cc91933a23ab751ac841055ef91df4d14aca42f754fdfe33cafbd95` |
| **ElSopa CoS Retextured 2k** | 42558 | `42558-170809.7z` | 200,405,187 | `5200f9ea5e4a9d64b05df3e72fc90c53d1e9e78ed650e48e4ee57629fc9d6cab` |
| ElSopa CoS Retextured 1k | 42558 | `42558-170810.7z` | 55,647,330 | `d9578236cdd4d380cd51672bed5d8a9667d40c4614a7af63d6339a8704624575` |
| ElSopa CoS Retextured 512 | 42558 | `42558-170811.7z` | 15,619,648 | `b7cab5046c97c5936f3a077a8a4a36c585f19fdffe21d153347404627fecc489` |
| **ElSopa Mesh Update 1.2** | 42558 | `42558-263634.7z` | 332,180 | `df8822b5fcba8120e0cb52629b8183287d21c50928f93f6fb017dc56a1c251f6` |
| CoS Retextured Female Mesh Patch 1.0.0 | 85932 | `85932-363920.7z` | 52,165 | `2e2a264fe4134a2d0feb9fbd82a790cb610b3ad06b54df7d2ccec4718b12a898` |

**Artesian Cloaks of Skyrim is Nexus `17416`**, not 115097 - that id resolves to
`Immersive Equipping Animations (PTBR)` (Granhadd, v2.02, 2024-03-26), a
different mod. Author Zeridian/Rosent, v1.4.0, page last updated
**2020-11-27**. Its MAIN v1.4.0 file (`171756`) patches *Cloaks of Skyrim
Retextured*, not base CoS; the base-CoS payload is inside the v1.3.0 FOMOD
(`58843`, 2018-07-02), which is what was audited.

**Cloaks of Skyrim HD SSE PBR is Nexus `178993`** (Julio005, v1, 2026-05-02,
13 endorsements). Its sibling `178836` "Cloaks of Skyrim SSE PBR" is a
different package whose own summary says it is "upscaled and refined 2K
textures based directly on the original 1K textures".

---

## 1. Cloaks of Skyrim 6369 v1.2.1 - what is actually dated

Author Nikinoodles and Nazenn, uploaded by Nazenn, **last updated 2017-01-19**,
100,712 endorsements. Eight plugin variants ship
(`Cloaks.esp`, `Cloaks - No Imperial.esp`, `Cloaks - Player Only.esp`, each with
a Dawnguard companion, plus two USSEP patches).

### Record surface (`skyrim-record-cli plugin-info` / `records`)

`Cloaks.esp` carries **536 records: 400 new and 136 overrides of vanilla.**

| | new | overrides vanilla |
|---|---:|---:|
| ArmorAddon | 111 | - |
| Armor | 120 | - |
| PlacedObject (REFR) | 111 | 2 |
| LeveledItem | 19 | 5 |
| ConstructibleObject | 36 | - |
| Book / Furniture / Keyword | 3 | - |
| **Cell** | - | **68** |
| **Outfit** | - | **47** |
| **Npc** | - | **10** |
| **Worldspace** | - | **4** |

The 47 outfit overrides are the problem, not the age. They include
`GuardWhiterunOutfit`, `GuardOutfitRift`, `GuardPaleOutfit`,
`GuardFalkreathOutfit`, `GuardWinterholdOutfit`, `ReachHoldGuardOutfit`,
`ArmorHaafingarAllOutfit`, `ArmorStormcloakOutfitNoHelmet`,
`CWSoldierImperialSoldierOutfit`, `ArmorCompanionsOutfitNoHelmet` - and the
10 NPC overrides are every dragon priest plus Idolaf Battle-Born.

Cross-referenced against the live 238-plugin order
(`records/active-record-conflicts.json`, captured 2026-09-02T18:07:46Z, plus a
direct `skyrim-record-cli records` sweep of all 238 providers):

- **24 of the 62** Outfit/Npc/LeveledItem overrides are **already written** by a
  live plugin. **16 by `NW_Sons_of_Skyrim.esp`**, 7 by USSEP, 4 by
  `cutting room floor.esp`, 1 by `Unofficial Skyrim Modders Patch.esp`,
  1 by `arnima.esm`.
- **76 of the 136** total overrides are already in a live chain, contested by
  USSEP (67), `Lux.esp` (60), `SFCO3-BOS - Addons.esp` (29),
  `Navigator-NavFixes.esl` (29), `3DNPC.esp` (27) and 20 others, mostly on the
  68 CELL records.

Installing `Cloaks.esp` means a guard-outfit fight with Sons of Skyrim on
sixteen records - the exact class of conflict
`docs/PATCH_INTENTS.md` "Protected vanilla gear" exists to prevent.

### Texture defects, named

137 DDS, 128 diffuse, **8 normal maps**, 1 env mask. Resolutions:
127 at 1024, 5 at 512, 4 at 256, 1 at 2048. Formats: BC1 75, **uncompressed 46**,
BC3 10, **BC2 6**.

1. **19 textures ship with no mip chain at all** (`mips=1`, 1024x1024,
   uncompressed). Every one is a named or faction cloak - i.e. exactly the
   assets that justify the mod:

   `Capes/CapeWhiterun`, `CapeSolitude`, `CapeRiften`, `CapeTalos`,
   `CapeRedEagle`, `CapeMossyWrap`, `CapeComp`, `cloakmdawnstar`,
   `cloakmhjaalmarch`, `cloakmgreyfox`, `cloakfurcrow`, `cloakhimirhide`,
   `cloaknecro`, `sagecloakblue2`, `sagecloakcrimson2`, `sagecloakdawnstar`,
   `sagecloakgreen2`, `sagecloakmarkarth`, `sagecloakthalmor3`.

   With no stored chain the GPU has only mip 0, which is what shimmers in
   motion and what the user is describing when he says a cloak "loses all
   texture" as he backs away.
2. **46 textures shipped uncompressed** rather than BC-compressed, about
   **204 MB of VRAM for no visual gain** (e.g. `cloakdwemerpurple.dds`).
3. **123 of 128 diffuse maps ship with no matching normal map.** The cloth has
   no authored bump detail at all; it is lit as a flat surface (e.g.
   `Clothes/cloaksofskyrim/cape_d.dds`).
4. **6 textures stored as BC2**, a format with no modern use.
   `collareddaedric.dds` (2048 BC2) is the single worst CoS file measured:
   hf x0.24 at distance.
5. **3 sampled textures show JPEG blocking** (compressed source):
   `capes/capeflover2.dds`, grid ratio 1.37.
6. One normal map stored as BC1 (`spinning wheel/clutter/iron01_n.dds`).

Measured per-file, the *named* cloaks are the good ones and the *plain* ones
are the weak ones - the opposite of what "the mod has aged" suggests:

| file | px | fmt | hf vs vanilla cloth |
|---|---:|---|---:|
| `DPKrosis.dds` | 1024 | BC1 | x2.38 |
| `DPVokun.dds` | 1024 | BC1 | x1.93 |
| `cloakmhjarvo.dds` | 1024 | BC1 | x1.28 |
| `DPHevnoraak.dds` | 1024 | BC1 | x1.13 |
| `cloakmashlander.dds` | 1024 | BC1 | x0.83 |
| `CapeSolitude.dds` | 1024 | uncompressed, no mips | x0.60 |
| `CapeFblue.dds` | 1024 | BC1 | x0.57 |
| `CapeSilverhand.dds` | 1024 | BC1 | x0.57 |
| `cloakscale.dds` | 1024 | BC1 | x0.51 |
| `collareddaedric.dds` | 2048 | BC2 | x0.24 |

### The mesh defect is the real ageing

All 366 equippable cloak records point at meshes weighted to the **vanilla skirt
bone chain**. Receipt - `meshes/clothes/cloaksofskyrim/cloakburblackm_0.nif`
bone list:

```
NPC Spine1 [Spn1]   NPC Spine2 [Spn2]   NPC L/R Clavicle   NPC L/R Pauldron
NPC L/R UpperArm    NPC L/R UpperarmTwist1/2
SkirtBBone01   SkirtBBone02   SkirtBBone03
```

`SkirtBBone01-03` are stock skeleton bones driven by the canned skirt animation.
No HDT-SMP config ships anywhere in the archive. **The cloaks do not simulate,
do not respond to wind, and do not respond to movement.** That, not the texture
resolution, is what reads as 2017.

One mesh is still unconverted Oldrim format (NIF user version 34, `NiTriShape`
rather than `BSTriShape`): `meshes/clothes/cloaksofskyrim/cloakmblack2.nif`.

### Slots

Slot 46 (chest/cloak) on all 366; **slot 40 (tail) on 339**, which hides
Khajiit and Argonian tails while a cloak is worn.

### Item inventory (120 ARMO, for the shortlist question)

- **Generic, 57:** CloakBlack/Blue/Brown/Crimson/Green/Grey/White plus Burlap
  and Linen variants of each, CloakShort* equivalents, CloakAshlander1/2,
  CloakBurned, CloakCrow, CloakDaedric, CloakDwemer(Alt), CloakGreyFox,
  CloakHjarvoBlanket, CloakHuntersFolly, CloakKvatch, CloakNorthPaladin,
  CloakNya, CloakScale, CloakShortLover, CloakShortMossy, CloakShortSilverhand,
  CloakWarmSands, CloakWildHunt, CloakTest.
- **Hold and faction, 40:** per-hold cloak + linen + short variants for
  Dawnstar, Falkreath, Hjaalmarch, Markarth, Riften, Solitude, Whiterun,
  Winterhold, plus CloakFallWinterhold, CloakForsworn(Alt), CloakGreybeard,
  CloakImperialGold/Silver, CloakNecro(Alt), CloakShortCollege,
  CloakShortImperial, CloakShortStormcloak, CloakStormcloak(Linen),
  CloakThalmor/Alt/AltEnch.
- **Unique and named, 23:** CloakDragonPriest, CloakDPHevnoraak, DPKrosis,
  DPMorokei, DPNahkriin, DPOtar, DPRahgot, DPVokun, DPVolsung, CloakVaermina,
  CloakShortRedEagle, CloakHimirHide, CloakDwemerCeremonial,
  CloakDwemerPurple(Alt), and the four enchanted pairs
  CloakBrownHealth01/02, CloakBlackResist01/02 with Linen twins.

Balance baseline: **all 120 weigh 1.0 and have ArmorRating 0**; values are 20
(79 items), 50 (18), 100 (4), 200 (11), 250 (4), 300 (2), 400 (2). Keywords are
`ClothingNecklace`, `ArmorClothing`, `ArmorMaterialLeather` or
`ArmorMaterialHide`, and `08F95B` - **no Survival warmth keyword on any record**
(the mod predates Survival Mode by a year).

### Permissions - the grid is empty, the description is not

The Nexus permission widget says only "See the description for more details on
permissions and credits." The description's `:: Permissions ::` block reads, in
full:

> "If you just wish to use one of the cloak meshes for an armour/clothing/
> companion mod, then go ahead. You have permission to use the resources for
> anything along those lines. Please make a comment in the comments section
> letting me know you have done this.
>
> The is also open permissions for any sort of compatibility patch you may want
> to do between this and another file, but again, please do let me know.
>
> For anything else including use of multiple cloak designs or using more files
> etc please toss me a message first via a PM on the Nexus and I'll get back to
> me ASAP."

So, plainly:

- **A compatibility/distribution patch that ships no CoS bytes is explicitly
  permitted** ("open permissions for any sort of compatibility patch"), with a
  courtesy comment. That is `distributable`.
- **Shipping fixed CoS textures or meshes is not covered.** Single-mesh reuse is
  granted; "use of multiple cloak designs or using more files" needs a PM first.
  A 19-file or 46-file texture repair is squarely "more files", so it is
  `recipe` unless the user PMs Nazenn and gets a broader grant.
- Third-party content is inside: the credits name **Backsteppo and Zenl** for
  the cloak meshes, **Shadowtroop** for the high-collared cloak, **Stroti** for
  the spinning wheel, and **Hemingwey** for textures. Any asset shipping must
  clear them too, which is a second reason to keep asset work as a recipe.

The mod is **not** as restrictive as the task assumed - the patch we most want
to ship is the part that is explicitly allowed.

---

## 2. RMB SPCH - Cloaks of Skyrim 116030 v1.5.3 - claim verified, two defects found

RowanMaBoot, v1.5.3, **2026-05-06**, 523 endorsements. 30 KB.

### The claim is true, and the receipt is decisive

`Cloaks - RMB SPCH.esp` is ESL-flagged, masters `Skyrim.esm` + `Update.esm`
only, and carries **294 records, every one of them new and zero overrides**:

| | new records |
|---|---:|
| Armor | 122 |
| ArmorAddon | 113 |
| ConstructibleObject | 36 |
| LeveledItem | 20 |
| Book / Furniture / Keyword | 3 |

Against base `Cloaks.esp`'s 136 vanilla overrides, RMB SPCH writes **none**.
All 68 cell edits, 113 placed references, 4 worldspace records, 47 outfit
overrides and 10 NPC overrides are gone. Distribution moves to SkyPatcher
configs that inject at runtime:

```
SKSE/Plugins/SkyPatcher/leveledList/Cloaks - CoS/Cloaks - RMB SPCH.esp.ini
SKSE/Plugins/SkyPatcher/npc/Cloaks - CoS/Cloaks - RMB SPCH.esp.ini
SKSE/Plugins/SkyPatcher/armor/Cloaks - CoS/Tweaks - *.ini            (optional)
```

Because it masters neither `Cloaks.esp` nor anything else, and re-declares the
same item set under its own form IDs, **RMB SPCH replaces the base plugin rather
than patching it**: you install Cloaks of Skyrim for its `meshes\` and
`textures\` and never activate any of its eight ESPs. Receipt that it still
needs the CoS asset tree - the plugin's own bytes carry **253 model paths**,
almost all under `clothes\cloaksofskyrim\`:

```
clothes\cloaksofskyrim\Cape_go.nif
clothes\cloaksofskyrim\Capeashlander_go.nif
clothes\cloaksofskyrim\Capeblue_go.nif   ...
```

**Hard dependency:** the leveled-list config injects into
`RMB SPID - Core Definitions.esp` form IDs, so
[RMB SPIDified - Core Framework `63625`](https://www.nexusmods.com/skyrimspecialedition/mods/63625)
v6.3.0 (2026-05-21) is required. The `00 Shared` folder also ships configs
targeting `RMB SPID - Sons of Skyrim.esp` and
`RMB SPID - NordwarUA GAR - Outfits.esp`; those are inert unless
[RMB SPIDified - Sons of Skyrim `83340`](https://www.nexusmods.com/skyrimspecialedition/mods/83340)
is installed, and Sons of Skyrim **is** in this build, so adopting that patch is
how the hold cloaks reach the guards we actually see.

### Defect 1: the ten unique cloaks are never placed

`SKSE/Plugins/SkyPatcher/npc/Cloaks - CoS/Cloaks - RMB SPCH.esp.ini` has ten
directives. Every one names the wrong plugin for the item:

```
filterByNpcs=Skyrim.esm|13BB2:objectsToAdd=Skyrim.esm|D6B    ; Idolaf / CloakCrimson
filterByNpcs=Skyrim.esm|23A93:objectsToAdd=Skyrim.esm|8EF    ; Dragon Priest
... 8 more, all objectsToAdd=Skyrim.esm|<id>
```

The comments say the item ids are `CloakCrimson` `D6B`, `CloakDragonPriest`
`8EF`, `CloakDPVokun` `8FF` and so on - which are form IDs **in
`Cloaks - RMB SPCH.esp`**, not in `Skyrim.esm`. The leveled-list ini in the same
package gets this right (`addToLLs=Cloaks - RMB SPCH.esp|809~1~1`); the NPC ini
does not. Verified against the game's own master:

```
skyrim-record-cli record-fields Skyrim.esm 0008EF:Skyrim.esm  -> Record not found
skyrim-record-cli record-fields Skyrim.esm 000D6B:Skyrim.esm  -> Record not found
skyrim-record-cli record-fields Skyrim.esm 013BB2:Skyrim.esm  -> Npc IdolafBattleBorn   (control, resolves)
```

The NPC filters resolve; the items do not exist. Every one of the nine
dragon-priest cloaks and Idolaf's crimson cloak is a no-op.

### Defect 2: Krosis' filter is truncated

The last line reads `filterByNpcs=Skyrim.esm|767`, while the comment above it
says `100767 >> dunShearpointKrosisDragonPriest`. `000767:Skyrim.esm` does not
exist; `100767:Skyrim.esm` resolves to Krosis. So that line fails on both halves.

### Warmth: partly fixed, and not to the target

`01 Tweaks - Generic` (an optional FOMOD group; there is a "Does not include the
generic tweaks config" alternative) applies, to every slot-46 item in the
plugin:

```
keywordsToAdd    = Update.esm|2ED8 , Skyrim.esm|A8657
keywordsToRemove = Skyrim.esm|6BBDD , 6BBDB , 10CD0A
bipedSlotsToRemove = 10        ; biped slot 40, the tail slot
weight = 2.0
pickUpSound / putDownSound = ITMClothingUp/DownSD
```

Resolved: `Update.esm|2ED8` = **`Survival_ArmorCold`**, `Skyrim.esm|A8657` =
**`ClothingBody`**; removed are `ArmorMaterialHide`, `ArmorMaterialLeather` and
`ClothingNecklace`. The author's own comment is honest about it: *"Add
SurvivalCold - provides some coverage but not much"*.

What this means against the installed survival stack:

- `Starfrost_KID.ini` already reads
  `Keyword = MAG_SurvivalArmorCold|Armor|ArmorClothing`, and **all 120 CoS
  cloaks carry `ArmorClothing`**, so Starfrost tags every one of them as its
  coldest clothing tier with or without RMB's tweak.
- Starfrost's warmth budget is slot-based:
  `fSurvWarmBodyBonus = 60`, `fSurvWarmHeadBonus = 30` (GMSTs in
  `Starfrost.esp`, read directly). A slot-46 cloak is not one of the four
  warmth slots, which is why RMB adds **`ClothingBody`** alongside the survival
  keyword - it is trying to make a cloak register as a body-slot warmth item.
- Neither route reaches the 25/35/50 tiers issue #95 targets. **[unverified]:**
  whether `ClothingBody` on a slot-46 item is honoured by Starfrost 2.0.0 +
  Survival Mode Improved 1.7.0 can only be settled in-game; the calculation
  lives in `SurvivalModeImproved.dll`, not in its shipped Papyrus sources.
  Tracked as its own job.

The tail fix is real and worth having: `bipedSlotsToRemove=10` clears the slot-40
flag that base CoS sets on 339 of its 366 items.

**Permissions (grid):** Upload "not allowed under any circumstances";
Modification "must get permission"; Asset use "must get permission"; assets are
the author's own or free-to-use resources. So RMB SPCH is a **required
download**, never a bundled file, and our corrections to its configs must be
authored as our own files rather than as edits of his.

`RMB SPCH - Winter is Coming 116029` v1.4.6 (2026-05-08) is the same design for
WIC: ESL-flagged `Winter is Coming Cloaks - RMB SPCH.esp`, 183 new cloak/hood
records, SkyPatcher armor+leveledList configs **plus** a SPID distribution file
(`0_rmb_wic_cloaks_distr.ini`), same permission grid.

---

## 3. Artesian Cloaks 17416 - take the meshes, drop the plugin

FOMOD v1.3.0 (`58843`, 2018-07-02); the page's newest file is a 2020 patch for a
different retexture mod. **Page last updated 2020-11-27** - it is older than
Cloaks of Skyrim's own last update is young.

### What it ships for Cloaks of Skyrim

- **391 replacement NIFs**, and every one of them is a **direct path replacer**
  of a base CoS mesh: 391 of 391 Artesian paths already exist in `6369`,
  0 are new. They overwrite `meshes/clothes/cloaksofskyrim/...` in place.
- Two HDT-SMP configs at `SKSE/Plugins/hdtSkinnedMeshConfigs/cape.xml`
  (39 bones, 14 generic constraints, 4 per-triangle shapes) and `cloak.xml`
  (42 bones, 17 constraints, 4 per-triangle shapes).
- `Cloaks_SMP_Patch.esp`, ESL-flagged, 217 records (113 ARMO + 104 ARMA),
  masters `Skyrim.esm`, **`Cloaks.esp`**, **`Cloaks - Dawnguard.esp`**.

The rig change is exactly the fix base CoS needs. Same file, before and after:

| | base `6369` | Artesian `17416` |
|---|---|---|
| `cloakburblackm_0.nif` bones | `SkirtBBone01-03` + torso | `HDT TailBone01-05.x` chains |
| physics config | none | `SKSE\Plugins\hdtSkinnedMeshConfigs\cloak.xml` |

### The architectural conflict, and the way through it

`Cloaks_SMP_Patch.esp` masters `Cloaks.esp`. RMB SPCH *replaces* `Cloaks.esp`.
As shipped, **Artesian and RMB SPCH are mutually exclusive.**

They do not have to be. Because all 391 Artesian meshes are path replacers, the
SMP rig arrives through the **asset tree alone**: install Artesian's
`Meshes\` + the two `hdtSkinnedMeshConfigs` XMLs above Cloaks of Skyrim, and do
not install `Cloaks_SMP_Patch.esp` at all. RMB SPCH's own ARMA records point at
the same Data-relative paths, so they pick up the SMP meshes automatically.

**[unverified]:** the 217-record ESP presumably also fixes ArmorAddon
sex/weight-slider assignments that the mesh swap alone will not carry. Whether
anything is lost by dropping it needs a first-person and third-person look
in-game. Tracked.

### Mesh defects found

- **82 of 391 NIFs carry a misspelled physics path**,
  `HTD-SMP\Clothes\cloaksofskyrim\cloak.xml` (`HTD`, not `HDT`). Each of those
  files *also* carries the valid
  `SKSE\Plugins\hdtSkinnedMeshConfigs\cloak.xml` string, so whether those 82
  cloaks simulate depends on which string FSMP resolves first. Not proven
  broken; needs an in-game check.
- Neither `HDT-SMP\Clothes\cloaksofskyrim\cape.xml` nor `...\cloak.xml` exists
  anywhere in the archive - 307 NIFs point at a path that ships no file.
- One NIF has **no** physics string at all; one carries three
  (both `cape.xml` and `cloak.xml`).
- **78 CoS meshes have no Artesian counterpart** and stay unsimulated: all 36
  dragon-priest meshes, the 6 `holds` meshes, the 3 spinning-wheel meshes, the
  `*_go` ground/inventory objects, and `cloakdaedric[fm]_0/1`.

### Performance: the bounded-density policy is already in the runtime

Artesian's page warning ("can impact FPS depending on... the number of NPCs in
your loaded cells wearing physics-enabled clothing") was written in 2018 against
the original hdtSMP64. FSMP 4.1.1's live config in this build already bounds it:

`mods\FSMP - Faster HDT-SMP\SKSE\Plugins\hdtSkinnedMeshConfigs\configs.json`

```json
"maximumActiveSkeletons": 5,     "autoAdjustMaxSkeletons": true,
"budgetMs": 3.0,                 "minCullingDistance": 500.0,
"disable1stPersonViewPhysics": true,
"skipDeadActors": false,         "minScreenSizePercent": 0.0,
"solver": { "numIterations": 16, "min-fps": 60, "maxSubSteps": 4 },
"wind":   { "enabled": true, "windStrength": 2.0, "distanceForMaxWind": 2000.0 }
```

So the answer to "what would a bounded actor-density policy look like" is: **it
is a runtime-config policy, not a distribution policy.** At most 5 skeletons
simulate at once, auto-adjusted down against a 3 ms/frame budget, and nothing
past 500 units simulates at all. Handing cloaks to 100% of a city crowd does not
cost 100 skeletons; it costs the same 5, chosen by proximity. Consequences:

1. **The real contention is with hair, not with crowd size.** `Vanilla Hair
   Remake SMP` and `Vanilla Hair Remake SMP - NPCs` are enabled and consume the
   same 5 slots. Cloaked NPCs will sometimes take a slot from a haired NPC.
   That, not frametime, is the visible symptom to watch for.
2. `disable1stPersonViewPhysics: true` already neutralises the first-person
   instability the More Scarves page warns about.
3. `skipDeadActors: false` keeps corpses simulating - measurably wasteful once
   bandits wear cloaks. Worth flipping; tracked.
4. `minScreenSizePercent: 0.0` disables the screen-size cull entirely. A small
   non-zero value is the cheapest further bound if 1% lows regress.

**Permissions (grid):** Upload "not allowed under any circumstances";
Modification "must get permission"; Asset use "not allowed under any
circumstances"; and "Some assets in this file belong to other authors". Artesian
is a **required download only** - not one byte can ship, and a fixed-`HTD-SMP`
mesh set cannot be distributed even as our own work without Zeridian's
permission. Any repair is `recipe` at best.

---

## 4. Cloaks of Skyrim HD SSE PBR 178993 - resolved: it still blocks, and it is also worse

Two independent blockers, either one sufficient.

### Blocker 1: nothing in this build can render it

The 568 MB payload is 579 DDS under `textures/pbr/clothes/cloaksofskyrim/` plus
**38 JSON files under `PBRNifPatcher/`**. `PBRNifPatcher` is a **ParallaxGen**
input directory: the JSONs describe how ParallaxGen should rewrite each NIF's
shader type and texture slots to the PBR path.

- **ParallaxGen is not installed** (no match anywhere in
  `mo2-instances\skyrim-se\mods`).
- Without that pass, the CoS NIFs keep their vanilla shader and never reference
  `textures/pbr/...`. The whole package is inert - 568 MB of files nothing loads.
- Community Shaders **is** present and does carry the feature
  (`Community Shaders AIO - 1.7.99 Source Build\Shaders\Features\TruePBR.ini`,
  `Shaders\Common\PBR.hlsli`), so the renderer is not the blocker; the missing
  NIF-patching step is.
- And it collides with route 3: ParallaxGen rewrites the same
  `meshes\clothes\cloaksofskyrim\*.nif` files that Artesian replaces to get SMP.
  Ordering that correctly (Artesian meshes in, ParallaxGen run over them, SMP
  strings preserved) is a real integration project, not an install.

### Blocker 2: it is the worst asset in the audit

| | base CoS 6369 | CoS HD SSE PBR 178993 |
|---|---:|---:|
| median hf at 512-128 px | **x0.72** | **x0.31** |
| median tone | x0.76 | x0.27 |

Worst individual files: `cloakburnt.dds` **x0.04**, `sagecloakcrimson2.dds`
**x0.05**, `sagecloakgreen.dds` **x0.07**, `CapeFgrey.dds` (4096 px) **x0.20**.
`inspect_mod` independently flags 11 of 29 sampled textures as "far less detail
than their stored size suggests", 15 with JPEG blocking, 7 normals embossed from
the diffuse (X/Y correlation 0.86), and **120 of 125 texture sets with a normal
map at half the diffuse's resolution** (2048 diffuse / 1024 normal).

This is an upscale of a 2019 upscale: `178993` is a PBR conversion of
*Cloaks of Skyrim HD SSE* `29258` (2019), which is itself a HD pass over the
2017 originals. Each step added pixels and removed information.

**Verdict: skip, and it does not become viable if ParallaxGen is later adopted.**
The integration reports are the smaller problem.

**Permissions (grid):** Upload no; Modification "must get permission"; Asset use
"must get permission"; "Some assets in this file belong to other authors" - and
`29258`, its source, carries the same restrictive grid. Nothing derived from
either can ship.

---

## 5. More Scarves 149259 v1.4.0 and Bocksten 138180 v1.1

### More Scarves 1.4.0 (devInTheDetails, 2026-02-21, 5,524 endorsements)

`moe-scarves.esl`: **56 records, 54 new** (12 ARMO, 25 ARMA, 12 COBJ, 5 TXST)
and **2 overrides** - `ccPlaceholder13Interior01` and `ccPlaceholder12Interior01`
from `Update.esm`. Those are empty Creation Club placeholder cells that get
touched whenever an author saves in the CK; harmless, but they are dirty edits
and belong in the cleaning note.

12 items: 3 hooded capes (`cloak/cape` class), 9 scarves/gaiter. Slots: 45 neck
on all 12, plus 31 hair / 42 circlet / 43 long-hair on the three hooded capes.

**The inspector's "no HDT-SMP config ships" finding is a false negative** - its
detector only looks in `SKSE/Plugins/hdtSkinnedMeshConfigs/`. More Scarves puts
its configs beside the meshes:

```
meshes/clothes/moe-scarves/xml/hooded.xml
meshes/clothes/moe-scarves/xml/scarves.xml
```

and **221 of its 243 NIFs reference one of them** by NiStringExtraData
(161 -> `hooded.xml`, 60 -> `scarves.xml`). The physics is real.

**It is the only candidate in this audit with first-class hood support.**
The `__loweredHood` FOMOD option ships
`SKSE/Plugins/DynamicArmorVariants/moe-scarves.json` with three variants -
`LoweredHoods`, `HT_LoweredHoodsHairOnlyPlayer`, `HT_LoweredHoodsPlayer` -
each `linkTo`-ing a Helmet Toggle 2 state (`HT_HiddenHelmetPlayer`,
`HT_HiddenHelmetHairOnlyPlayer`) with `overrideHead: showAll` and a
`replaceByForm` map from the three raised capes to their three lowered forms.
The matching KID rule is one line:

```
Keyword = HT_ArmorHood|Armor|_MOE_cape001AM,_MOE_cape002gAM,_MOE_cape002rAM
```

Body routes shipped: `_3BA`, `_BHUNP`, `_HIMBO`, `_VanillaF`, `_VanillaM`
(47/47/47/47/46 NIFs) plus BodySlide slider sets (84 `.osd`, 5 `.osp`). This
build has **CBBE + HIMBO + BodySlide**, no 3BA/BHUNP/OBody, so the correct
route is `_HIMBO` for male, `_VanillaF` for female, **then a BodySlide build
against the installed CBBE Curvy preset** - not a raw copy. It passes the hard
filter (a HIMBO option exists and BodySlide data ships).

Texture side is the weak half: 23 DDS, 21 at 2048; **12 of 12 diffuse maps have
no matching normal**; 4 sampled normals are embossed from the diffuse (X/Y
correlation 0.9); 4 show JPEG blocking; and at distance it lands at
**hf x0.46** - third from bottom. `scarf001a_d.dds` is x0.38, `scarf002_d.dds`
(4096 px!) is x0.34.

**Permissions (grid): the most permissive in the audit.** Upload "can upload to
other sites but you must credit me"; Modification "allowed to modify my files
and release bug fixes or improve on the features so long as you credit me";
Asset use "without permission as long as you credit me"; all assets are the
author's or free-to-use. No sale, DP allowed. A More Scarves refit or texture
fix can be **distributable** with credit.

### Bocksten Cloak 1.1 (OperatorCactus, 2025-03-31, 1,010 endorsements)

`BoxtonCloak.esp`, ESL-flagged: **38 records, all new, zero overrides**
(10 ARMO, 10 ARMA, 9 COBJ, 9 TXST). Slot 46 only - no tail-slot flag, so no
beast-race problem. 5 NIFs, 4 of them referencing
`meshes\clothing\boxton\CloakSMP.xml`. 16 DDS, 14 at 2048.

It is the cleanest plugin in the audit and the softest cloth texture. Distance:
**hf x0.40 median**, `cloak_blk_d.dds` x0.24, `cloak_red_d.dds` x0.33,
`cloak_ylw_d.dds` x0.32; only `cloak_wht_d.dds` (x0.80) is respectable.
10 of 10 diffuse maps ship with no normal map.

Nine crafting recipes and **no distribution whatsoever** - no leveled list, no
NPC, no vendor. Per `docs/PATCH_INTENTS.md` that is not a reason to skip it; it
is a job for the master distribution mod.

**Permissions (grid):** Upload "not allowed under any circumstances";
Modification "must get permission"; Asset use "**allowed without permission as
long as you credit me**". So: required download, our record/config patch is
fine, and a credited asset derivative is allowed but re-uploading his files is
not. A refit or retexture we author is `distributable` with credit; his original
archive is a fetch.

---

## 6. Pelts 'o' Plenty 4.3.1 vs Winter Is Coming - the fur slot

| | Winter Is Coming `4933` | Pelts 'o' Plenty `120726` |
|---|---|---|
| Author / updated | Nivea, **2017-01-19** | qIp, **2026-01-05** |
| Endorsements | 32,435 | 2,031 |
| Plugin | `1nivWICCloaks.esp`, **not** ESL, 900 records | `Pelt Cloaks.esp`, **ESL-flagged**, 120 items |
| Record surface | 183 ARMO, 300 ARMA, 244 COBJ, **118 LVLI**, 16 OTFT, 32 TXST | 119 cloak + 1 body armour |
| Slots | 46 chest (63), 31 hair (120), 42 circlet (96), 40 tail (63) | **57 misc** (109), 31 hair (10), 32 body (1) |
| Physics | **none** - skirt-bone rig, no SMP config | **HDT-SMP** (`meshes/clothes/furpeltcloak/lem_cloak_smp.xml`) |
| Textures | 46 DDS, 31 at 2048, BC1 31 / uncompressed 12 | 96 DDS, 42 at **4096**, BC7 89 |
| **Distance (median hf)** | **x0.94** | **x0.75** |
| Distance (median tone) | x1.01 | **x1.07** |
| Mip defects | 12 uncompressed normals (~64 MB VRAM) | **54 of 96 ship with no mip chain** |
| Other defects | 34/34 diffuse with no normal map | 83/83 diffuse with no normal map; 2 embossed normals; 9 JPEG-blocked; 2.17 M triangles across 11 static meshes |
| Distribution as shipped | 118 leveled-list edits + 16 outfit overrides | none in the audited MAIN file; separate SPID add-on (`653164`) |
| Modern patch | RMB SPCH `116029` 1.4.6 (2026-05-08), 183 new records, zero overrides, SkyPatcher + SPID | RMB SPCH - Pelts o Plenty `179354` exists (57 endorsements) |
| Permissions | **hostile**: "This mod is NOT to be used without my permission... Recolors... Using any meshes and textures from my mod". Compatibility patches explicitly fine **provided they contain no meshes or textures** | "**Do what thou wilt, but throw some credit my way.** Check the credits so you can properly attribute too." |

Reading:

- **On assets they are genuinely close and the choice is taste.** WIC's
  hand-painted 2K fur holds slightly more high-frequency detail at distance;
  Pelts' 4K fur holds slightly more tonal variation. Both beat base Cloaks of
  Skyrim and both beat every cloth candidate. The prior record's "prefer Pelts
  because it is newer" is not supported by measurement.
- **On engineering Pelts wins clearly**: ESL, SMP out of the box, hoods, no
  vanilla overrides, 4K, and permissions that let us fix and ship anything as
  long as we credit.
- **On engineering WIC loses badly**: a non-ESL 900-record plugin with 118
  leveled-list and 16 outfit overrides (its `1nivWICCloaks.esp` would need RMB
  SPCH `116029` to be usable at all), no physics, and the most restrictive
  permission text in the audit - it forbids even recolours, so a texture fix is
  not merely `recipe`, it is **not permitted at all** without Nivea's consent.
- **Slot 57 is Pelts' one real risk.** Nothing about slot 46 covers it, so any
  warmth or Helmet-Toggle rule written for cloaks needs an explicit slot-57
  arm. Note also that Pelts uses slot 31 (hair) on 10 hoods, which collides
  with More Scarves' hooded capes and with Helmet Toggle.
- **`Pelts 'o' Plenty - Fur Pelt Cloaks - Survival Fix` `164077`** exists and is
  the obvious first thing to check before we author warmth ourselves.

**Recommendation: Pelts 'o' Plenty**, unless the user prefers WIC's look on
sight. The permission difference alone decides it if the visuals are a wash: we
can repair and ship Pelts' work with credit, and we can ship nothing of Nivea's.

---

## 7. ElSopa - Cloaks Of Skyrim Retextured SE 42558 v1.2 (added 2026-09-02)

Brought by the user: *"I think this looks really good."* This is the direct test
of section 1's finding that the pixels were fine and the rig was what aged.

ElSopa, created 2020-11-19, **page last updated 2022-02-12**, 16,758
endorsements, 3.35 M downloads. Page claim: *"Cloaks Of Skyrim Retextured From
Scratch. From 4k To Vanilla Size. NO UPSCALING."* Requires Cloaks of Skyrim;
file credits "Nikinoodles and Nazenn".

### Verdict

**It goes in the stack, at the 2k tier, and it forces one architectural change:
the meshes.** It is not another mip-0 beauty - it beats base Cloaks of Skyrim at
play distance and by a much larger margin up close. But it renames every texture
and binds them through its own 394 meshes, which collide head-on with Artesian's
391. Section 3's "install Artesian meshes, drop its ESP" survives only with an
owned NIF texture-path port on top.

### The measurement, against the textures it actually replaces

This is a **true replacer comparison**, not the cross-asset one used for the
other six candidates. ElSopa renamed the whole set, so filename matching fails;
the binding is the mesh. For one NIF path, base CoS's `BSShaderTextureSet` names
texture A and ElSopa's names texture B, so A and B are the same surface on the
same UVs. That yields **104 distinct base-to-ElSopa diffuse pairs** across the
394 shared meshes (`records-work/cloak-audit-2026-09-02/elsopa_pairs.py`,
output `elsopa-vs-base-pairs.txt`).

| tier | median hf vs the base texture it replaces | median tone | files below x1.00 | n |
|---|---:|---:|---:|---:|
| 1k `170810` | **x1.18** | x1.05 | 42 | 104 |
| 2k `170809` | **x1.16** | x1.05 | 42 | 104 |
| 4k `170807` | **x1.18** | x1.04 | 40 | 104 |

So at play distance ElSopa is a **16-18% median improvement over base Cloaks of
Skyrim** - real, but modest, and **40 of 104 files are actually softer than the
2017 originals** at that range. Best and worst of the sampled pairs:

| base file | ElSopa file | 2k hf |
|---|---|---:|
| `cloakburnt.dds` | `cloakburnt.dds` | **x2.34** |
| `cloaknecro.dds` (uncompressed) | `cloaknecroalt.dds` | x2.25 |
| `sagecloakblack2.dds` | `cloakblackburlap.dds` | x1.79 |
| `cloakmhjarvo.dds` | `worncloakhjarvo.dds` | x1.79 |
| `cloakmstormcloakblue.dds` (BC2) | `worncloakstormcloak.dds` | x1.58 |
| `sagecloakwhite2.dds` | `cloakwhiteburlap.dds` | **x0.31** |
| `cloaknyartuk.dds` | `cloakzelda.dds` | x0.40 |
| `cloakwildhunt2.dds` | `cloakwild.dds` | x0.56 |

Placed in the section-3 table, same method as the other six (10 sampled diffuse
maps vs the same three vanilla clothing torso diffuses,
`elsopa-vs-vanilla.txt`): ElSopa measures **hf x0.75 (2k) / x0.79 (1k) / x0.80
(4k)**. The three medians are on different random file samples, so the spread is
sampling noise, not a tier effect - the matched-pair table above is the
controlled test. Rounded into the ranking:

| Mod | median hf vs vanilla cloth |
|---|---:|
| Winter Is Coming `4933` | x0.94 |
| **ElSopa CoS Retextured `42558`** | **x0.75-0.80** |
| Pelts 'o' Plenty `120726` | x0.75 |
| base Cloaks of Skyrim `6369` | x0.72 |
| More Scarves `149259` | x0.46 |
| Bocksten `138180` | x0.40 |
| CoS HD SSE PBR `178993` | x0.31 |

It is nothing like the PBR pack. Where `178993` collapsed to x0.31 with 11 of 29
files flagged soft-for-their-size, ElSopa's 2k tier flags 4 of 31 and carries a
**detail index of 3.55 against base CoS's 1.96** - nearly double the real texture
information per pixel at twice the resolution. The "NO UPSCALING" claim holds for
the set as a whole. Named exceptions, from `inspect_mod`:
`cloakthalmorb.dds` (2048 px, detail 0.22), `cloaknyartuk.dds` (0.91, and the one
file in the set showing JPEG blocking, grid ratio 1.36),
`cloakdwemerpurplerough.dds` (1.23), and 2 normals embossed from the diffuse
(`cloakburnt_n.dds`, X/Y correlation 0.93).

Up close the gap is much wider than the distance number suggests, and that is
where the user's "looks really good" comes from: base CoS ships **8** normal maps
for 128 diffuse maps; ElSopa ships **64** for 103.

### Tier: 2k

`docs/CURATION_POLICY.md` judges at distance, and the tiers are indistinguishable
there. Measured directly against each other at every shared pixel size
(`elsopa-tier-compare.txt`, `tier_hi.py`):

| comparison | median ratio | n |
|---|---:|---:|
| 4k / 2k at 512, 256, 128 px | x0.99, x0.99, x0.99 | 10-14 |
| 2k / 1k at 512, 256, 128 px | x0.99, x0.99, x1.00 | 10-14 |
| 1k / 512 at 512, 256, 128 px | x0.99, x0.98, x0.99 | 10-14 |
| **4k at 2048 px / 2k's own 2048 px top mip** | **x0.99** | 10 |
| **2k at 1024 px / 1k's own 1024 px top mip** | **x1.01** | 10 |

Every tier is a clean resample of one authored source; none adds information at
any size another tier also stores. (The measurement cannot see detail existing
only above a smaller tier's top mip, so it does not prove the 4096 px level is
empty - it proves nothing below it differs.)

What the tiers do differ in is footprint, measured on disk:

| tier | file | textures | on disk |
|---|---|---:|---:|
| 512 | `170811` | 172 | **34 MB** |
| 1k | `170810` | 172 | **138 MB** |
| 2k | `170809` | 172 | **538 MB** |
| 4k | `170807` | 172 | **2,130 MB** |
| *(base CoS for scale)* | `18422` | 137 | 271 MB |

Applying the build's source-plus-one-step rule: the surface being textured is a
2011 cloak on a **1024 px** UV (127 of base CoS's 137 textures are 1024), so one
doubling puts the ceiling at **2048**. **Take the 2k tier, file `170809`.** The
4k tier is 4x the VRAM for a measured x0.99, and it is also the only tier with
defects - **3 of its 172 files ship with no mip chain at all**
(`CloakWarmSands.dds`, `Cloak_Fall_g.dds`, `WornCloakHunter.dds`), which the 1k
and 2k tiers do not have. If VRAM is ever tight the 1k tier is a free swap: it is
identical in the play band and costs 138 MB.

### Does it retire #188? Mostly, yes

| | 1k tier | 2k tier | 4k tier |
|---|---:|---:|---:|
| textures with a full mip chain | **172/172** | **172/172** | 169/172 |
| textures with no chain at all | 0 | 0 | 3 |
| formats | BC1 107, BC3 64, uncompressed 1 | same | same |

The single uncompressed file in every tier is `worncloakgreyfox_g.dds`, a glow
mask (~5 MB).

Coverage against issue #188, computed by walking which base CoS textures are
still referenced by a mesh after ElSopa's mesh update lands
(`coverage.py`):

- ElSopa replaces **394 of base CoS's 469 meshes**, leaving **75**.
- Of base CoS's **137** textures, **101 are retired** - no surviving mesh
  references them - and **36 stay live**.
- **18 of #188's 19 no-mip textures are retired.** The survivor is
  `capes/capetalos.dds`.
- **38 of #188's 46 uncompressed textures are retired.** The 8 survivors are
  `capes/capetalos.dds`, `cloakmblue/mbrown/mgreen/mred/mwhite.dds`,
  `sagecloak_n.dds`, `sagecloakvaermina.dds`.

So #188 shrinks from 19 + 46 to **1 + 8** for the Cloaks of Skyrim half. Pelts 'o'
Plenty's 54 mip-less textures are untouched by this and remain the bulk of that
issue.

### Coverage: what it leaves on base assets

104 of base CoS's 128 cloak diffuse maps are replaced. The **27 it does not
touch**, from `elsopa-vs-base-pairs.txt`:

`dpblack, dpblack2, dpblue, dpbrown, dpgreen, dpgrey, dphevnoraak, dpkrosis,
dpmorokei, dpnahkriin, dpotar, dprahgot, dpvokun, dpvolsung, dragonpriest,
capeflover2, capetalos, cloakdwemerpurplerough, cloakforsworn2, cloaktornbrown,
cloakwildhunt, collaredbrown, sagecloakmythic`, plus the two spinning-wheel
clutter maps.

**The 15 dragon-priest textures and all 36 dragon-priest meshes are covered by
neither ElSopa nor Artesian.** They keep base CoS's 2017 assets and skirt-bone
rig whatever else is installed. That is a benign outcome: section 1 measured
those as base CoS's *best* files (`dpkrosis` x2.38, `dpvokun` x1.93,
`dphevnoraak` x1.13 against vanilla cloth).

Three-way mesh coverage of the 469 base meshes: both ElSopa and Artesian **381**;
ElSopa only **13**; Artesian only **10**; **neither 65** (36 dragon-priest, 3
spinning-wheel, 16 `*_go` inventory models, 10 others).

### The mesh update is not optional, and it is the collision

`Cloaks Of Skyrim Retextured Mesh Update 1.2` (file `263634`, 324 KB, 2022-02-12)
is not a refinement. Read directly from the NIF headers (`nif_ver.py`):

| set | nifs | NIF user version 2 | shape blocks |
|---|---:|---|---|
| base CoS `6369` | 469 | 468x **100**, 1x 34 | BSTriShape 499 |
| **ElSopa 2k MAIN `170809`** | **394** | **394x 83** | **NiTriShape 394 + NiTriShapeData 394** |
| **ElSopa mesh update `263634`** | **394** | **394x 100** | **BSTriShape 394** |
| Artesian `17416` | 391 | 391x **100** | BSTriShape 1238 |

The 2020 MAIN archives ship **394 Oldrim-format meshes**. The 2022 update is the
Special Edition conversion of exactly those 394 files. **Installing a MAIN
archive without the update leaves 394 LE meshes in an SSE build.**

And the meshes are load-bearing, not cosmetic: **all 394 ElSopa meshes reference
texture paths base CoS never used** - 141 distinct new paths such as
`capes/cape_n.dds`, `capes/capelinen_black.dds`, `cloakburlap_n.dds`,
`worncloakleather_n.dds`. Example, `capes/capefblack_0.nif`:

```
base CoS : capes/capef_n.dds        capes/capefblack.dds
Artesian : capes/capef_n.dds        capes/capefblack.dds
ElSopa   : capes/cape_n.dds         capes/capeblack.dds
```

His texture set is self-contained and fully mesh-bound: of the 169 texture paths
his meshes reference, **169 resolve inside his own archive and 0 fall back to
base CoS** (`dangling.py`); only 3 shipped textures go unreferenced. **Without
ElSopa's meshes, none of his 172 textures is ever sampled.**

Hence the collision, stated exactly:

- ElSopa's mesh update replaces **381 of Artesian's 391** SMP meshes.
- **None of ElSopa's 394 meshes carries any HDT-SMP string** - same as base CoS.
- Artesian's 381 meshes point at base CoS texture names, so they cannot show
  ElSopa's textures.

They are mutually exclusive as shipped. Whichever loads later wins outright:
ElSopa above Artesian = ElSopa's textures, **no physics on 381 cloaks**;
Artesian above ElSopa = physics, **2017 textures** and ElSopa's 538 MB inert.

The community female-mesh patch
[85932](https://www.nexusmods.com/skyrimspecialedition/mods/85932) (Grausam,
2023-02-27, 883 endorsements, 48 NIFs, sha256 `2e2a264f...12a898`) is a third
layer on the same files - all 48 exist in base CoS and Artesian, 46 in ElSopa's
update - and it uses ElSopa's texture names (`worncloakdawnstar.dds`,
`worncloakleather_n.dds`), user version 100, no SMP string. It belongs to the
ElSopa branch, not the Artesian one.

### Permissions

The strictest grid in the audit after Artesian and Winter Is Coming:

> Other user's assets: "Some assets in this file belong to other authors."
> Upload: "You are not allowed to upload this file to other sites under any
> circumstances." Modification: "You must get permission from me before you are
> allowed to modify my files to improve it." Conversion: not allowed.
> Asset use: "You must get permission from me before you are allowed to use any
> of the assets in this file." No sale, no donation points.

File credits name Nikinoodles and Nazenn, because the mesh update redistributes
394 Cloaks of Skyrim meshes.

Consequences: **required download, never a bundled file.** No ElSopa byte can
ship. A fix-up is `recipe` at best - regenerated locally from the user's own
download - and the NIF port below embeds Artesian geometry as well, whose grid is
"Asset use: not allowed under any circumstances", so that output is `recipe` and
cannot become `distributable` without two separate permissions.

### Consequences for the rest of this record

1. **Section 1 stands, with a qualifier.** Base CoS's textures are not the
   problem the mod's age suggests, and the rig is - but a from-scratch 2020
   retexture does beat them, by x1.16 median at distance and much more up close.
   "Fine" was right relative to modern *cloth* mods; it was not a ceiling.
2. **Section 3's Artesian route needs the port.** "Install Artesian's meshes,
   drop its ESP" is still correct, and now needs a texture-path rewrite on those
   meshes to point at ElSopa's names.
3. **Section 4 is unaffected.** CoS HD SSE PBR `178993` stays rejected and is now
   also beaten by a 2020 mod at a fifth of the disk cost.
4. **Issue #188 shrinks** to 1 no-mip and 8 uncompressed base CoS files, plus
   Pelts 'o' Plenty's 54.

---

## Slot contention against the live load order

Every one of the 238 active plugins was swept for ARMO records flagged on biped
slots 45, 46 and 57 (`record-selected-fields-by-type <plugin> Armor
EditorID,BodyTemplate`, `FirstPersonFlags` bit test; script
`records-work/cloak-audit-2026-09-02/slot_scan.py`, output `slot-contention.txt`).

| slot | wanted by | live ARMO records | live plugins |
|---:|---|---:|---|
| 45 | More Scarves | **2** | USSEP 1, `BSHeartland.esm` 1 |
| 46 | Cloaks of Skyrim, Bocksten | **20** | `NW_Sons_of_Skyrim.esp` **14**, `Campfire.esm` 4, `DIS_NordScale.esp` 2 |
| 57 | Pelts 'o' Plenty | **3** | `Inigo.esp` 3 (`MrDragonfly*`) |

Slot 45 and slot 57 are effectively free. Slot 46 is not, and the detail
matters more than the count:

**Sons of Skyrim already ships eleven hold cloaks on slot 46** -
`0_Dawnstar_Cloak`, `0_Falkreath_Cloak`, `0_Markarth_Cloak`, `0_Morthal_Cloak`,
`0_Riften_Cloak`, `0_Solitude_Cloak`, `0_Whiterun_Cloak`,
`0_Whiterun_Cloak_Ligth`, `0_Winterhold_Cloak`, `0_Windhelm_Cloak` (+ a
pauldron variant), `0_Officer_Cloak` (Stormcloak Officer) - plus two brown fur
collars. Campfire adds four `Travel Cloak` variants (burlap/linen/fur/hide) and
Scale Nord Armor two fur collars.

So the hold-heraldry argument for Cloaks of Skyrim is **already half-satisfied
on guards** by an installed, modern, better-integrated mod. What Sons of Skyrim
does not cover, and nothing else does, is the 23 unique/named cloaks, the 57
generic colour and fabric variants, and hold cloaks on **civilians** rather than
guards.

This is exactly the case RMB SPCH's `00 Shared` configs were written for. They
inject CoS's per-hold sublists into Sons of Skyrim's own cloak lists:

```
filterByLLs=RMB SPID - Sons of Skyrim.esp|842 : addToLLs=RMB SPID - Core Definitions.esp|B6C~1~1
                (RMB_SoS_ListCloakGuardEastmarch)          (RMB_Sublist_CLO_GuardEastmarch)
```

A guard then rolls either a Sons of Skyrim cloak or a Cloaks of Skyrim cloak
from one list, instead of two mods fighting for slot 46. **That only works if
[RMB SPIDified - Sons of Skyrim `83340`](https://www.nexusmods.com/skyrimspecialedition/mods/83340)
is installed** - without it the shared configs target a plugin that does not
exist and are inert.

Campfire's four travel cloaks and the two fur-collar sets are ordinary slot-46
rivals: only one slot-46 item can be worn, which is a wear-time choice, not a
load-order conflict.

## Recommended stack

| Layer | Mod | Why |
|---|---|---|
| Physics runtime | FSMP 4.1.1 (installed) | Already bounded at 5 skeletons / 3 ms / 500 units |
| Cloak base assets | Cloaks of Skyrim `6369` **meshes + textures only**, no ESP | The only source of hold heraldry and named cloaks; still the sole asset for the 36 dragon-priest meshes and 15 dragon-priest textures, which nothing else covers |
| Cloak textures | **ElSopa `42558` 2k tier (file `170809`) + Mesh Update 1.2 (file `263634`)** | x1.16 median over the base textures it replaces at play distance, 64 normal maps against base CoS's 8, full mip chains on 172/172. The mesh update is mandatory: the MAIN archives ship Oldrim-format meshes |
| Cloak physics | Artesian `17416` FOMOD, **meshes + `hdtSkinnedMeshConfigs` XMLs only**, `Cloaks_SMP_Patch.esp` discarded | 391 direct path replacers convert the skirt-bone rig to an SMP rig without needing `Cloaks.esp`. **Collides with the ElSopa mesh update on 381 files - needs #193, or a temporary either/or** |
| Cloak records | RMB SPCH `116030` 1.5.3 | 294 new records, **zero** vanilla overrides; replaces the 136-override 2017 plugin outright |
| Distribution backbone | RMB SPIDified - Core Framework `63625` 6.3.0 | Hard dependency of the above |
| Guard integration | RMB SPIDified - Sons of Skyrim `83340` | Sons of Skyrim owns the guard outfits **and eleven slot-46 hold cloaks** in this build; RMB's `00 Shared` configs merge the two cloak pools into one roll and are inert without it |
| Hooded capes | More Scarves `149259` 1.4.0 (`_HIMBO` + `_VanillaF` + `__loweredHood`, BodySlide-built) | Only candidate shipping DAV variants wired to Helmet Toggle 2 |
| Ordinary cloth cloak | Bocksten `138180` 1.1 | Cleanest plugin in the audit; best drape - subject to the bake-off |
| Fur | Pelts 'o' Plenty `120726` 4.3.1 (+ `179354` SkyPatcher patch, + `164077` survival fix) | **Settled by the user 2026-09-02.** ESL, SMP, hoods, permissive |
| Optional | CoS Retextured Female Mesh Patch `85932` | 48 female hold-cloak meshes using ElSopa's texture names; belongs to the ElSopa branch, not the Artesian one |
| **Rejected** | CoS HD SSE PBR `178993`, ElSopa **4k** tier `170807`, `Cloaks.esp` (all 8 variants), `Cloaks_SMP_Patch.esp`, Winter Is Coming `4933` + `116029` | Measured, record-surface or user grounds above |

Load-order note, in order: Cloaks of Skyrim `6369` -> ElSopa 2k `170809` ->
ElSopa Mesh Update `263634` -> (female mesh patch `85932`) -> **either** Artesian
`17416` meshes **or** the #193 ported set, never both raw. RMB SPCH's plugin
needs `RMB SPID - Core Definitions.esp` before it.

Footprint of the texture decision, measured on disk: base CoS 271 MB (137 files,
inflated by 46 uncompressed) plus ElSopa 2k 538 MB (172 files). The rejected 4k
tier is 2,130 MB; the 1k tier is 138 MB and measures identically in the play
band, so it is the free fallback if VRAM ever binds.

---

## Fix-up jobs, by distribution class

Classes per `docs/PATCH_INTENTS.md` "Every fix is a shippable patch or a
reproducible recipe".

| # | Issue and job | Class | Basis |
|---|---|---|---|
| 1 | [#187](https://github.com/Ensrick/skyrim-mod-assistant/issues/187) **Ensrick - Cloaks of Skyrim Unique Placement** - our own SkyPatcher `npc/` config replacing RMB SPCH's ten broken directives with correct `Cloaks - RMB SPCH.esp\|<id>` references, and Krosis' `100767`. | **distributable** | Our bytes. CoS grants "open permissions for any sort of compatibility patch"; RMB SPCH forbids modifying his files, so this is a new file that loads after his, never an edit. |
| 2 | [#189](https://github.com/Ensrick/skyrim-mod-assistant/issues/189) **Ensrick - Cloaks of Skyrim Warmth Tiers** - SkyPatcher `armor/` config assigning the 25/35/50 tiers of #95 across the 122 records by family, replacing the single `Survival_ArmorCold` blanket. | **distributable** | Same basis as #1. Gated on measuring whether slot 46 + `ClothingBody` even registers under Starfrost 2.0.0 (job 6). |
| 3 | [#188](https://github.com/Ensrick/skyrim-mod-assistant/issues/188) **Mip and format repair** - regenerate mip chains and BC-compress. Scope shrank when ElSopa entered: adopting `42558` retires 18 of the 19 no-mip and 38 of the 46 uncompressed CoS textures, leaving `capes/capetalos.dds` plus `cloakmblue/mbrown/mgreen/mred/mwhite`, `sagecloak_n`, `sagecloakvaermina`. **Pelts 'o' Plenty's 54 mip-less textures are now the bulk of this job.** | **recipe** | CoS grants single-mesh reuse and patches, but "use of multiple cloak designs or using more files etc" needs a PM to Nazenn; Pelts grants credited use ("Do what thou wilt, but throw some credit my way"), so the Pelts half could be distributable with credit. Regenerate locally; ship the texconv command list. |
| 4 | [#190](https://github.com/Ensrick/skyrim-mod-assistant/issues/190) **Artesian `HTD-SMP` path repair** - rewrite the misspelled NiStringExtraData in the 82 affected NIFs, only if the in-game check (job 6) shows those cloaks inert. | **recipe** | Artesian: Upload no, Modification "must get permission", Asset use "not allowed under any circumstances". Nothing of Zeridian's may ship. Regenerate from the user's own copy; even then, ask before publishing the recipe. |
| 5 | [#192](https://github.com/Ensrick/skyrim-mod-assistant/issues/192) **Ensrick - Cloak Distribution** (folds into the master distribution mod, #53/#96 pattern) - SkyPatcher/SPID rules giving Bocksten's 10 colours and More Scarves' 12 items an acquisition path; both ship crafting recipes and nothing else. | **distributable** | Our bytes. Bocksten: asset use allowed with credit; More Scarves: modification and upload allowed with credit. |
| 6 | [#191](https://github.com/Ensrick/skyrim-mod-assistant/issues/191) **FSMP config tuning for a cloaked crowd** - `skipDeadActors: true`, a non-zero `minScreenSizePercent`, and a decision on whether cloaks or hair win the 5-skeleton budget. | **distributable** | Our own config file, same class as `Ensrick - MLO2 Foundation Config`. |
| 7 | [#193](https://github.com/Ensrick/skyrim-mod-assistant/issues/193) **Ensrick - Artesian ElSopa Texture Port** - rewrite `BSShaderTextureSet` strings in Artesian's 381 shared NIFs to ElSopa's renamed paths, from the 104 base-to-ElSopa diffuse pairs already derived from the two mesh sets. Per-shape, not per-file: Artesian averages ~3 `BSTriShape` per NIF against ElSopa's 1. Delivers SMP physics and ElSopa's textures at once, which no shipped combination does. | **recipe** | Output embeds Artesian geometry. `17416` asset use is "not allowed under any circumstances"; `42558` is "must get permission". No bytes ship; the installer regenerates from the user's own downloads, like the Lost LongSwords model in `REDISTRIBUTION.md`. Cannot become distributable without two separate grants. |

Nothing in this list is `local-only`.

---

## Receipts

Every script and raw output quoted above is staged at
`records-work/cloak-audit-2026-09-02/` (local-only, not tracked):

| file | what it is |
|---|---|
| `inspect-*.txt` | `inspect_mod` findings sheets for all eight asset mods, including `inspect-42558-2k.txt` / `-4k.txt` |
| `distance-detail.txt` | the cross-asset mip measurement behind the six-mod ranking |
| `elsopa-vs-base-pairs.txt` | ElSopa against the base CoS texture it replaces, 104 matched pairs, all three tiers |
| `elsopa-vs-vanilla.txt` | ElSopa placed in the same table as the other candidates |
| `elsopa-tier-compare.txt` | tier-versus-tier at every shared pixel size |
| `slot-contention.txt`, `outfit-contention.txt` | the live-load-order sweeps |
| `cos-records.jsonl`, `cos-armor.jsonl`, `rmb-armor.jsonl` | record CLI dumps |
| `elsopa_pairs.py`, `tier_compare.py`, `tier_hi.py`, `coverage.py`, `mesh_overlap.py`, `nif_ver.py`, `texpaths.py`, `dangling.py`, `femalepatch.py`, `dist_compare2.py`, `slot_scan.py`, `scan_outfits.py` | the scripts that produced them |

## What was NOT verified

- **No launch.** Every runtime claim below is owed a foreground test:
  whether ElSopa's mesh update and Artesian actually behave as the file analysis
  says when one overwrites the other;
  whether slot-46 + `ClothingBody` produces warmth under Starfrost 2.0.0 +
  SMI 1.7.0; whether FSMP resolves the valid path in the 82 `HTD-SMP` NIFs;
  whether dropping `Cloaks_SMP_Patch.esp` loses anything; how the 5-skeleton
  budget behaves with hair and cloaks competing; first-person and clipping
  behaviour of More Scarves' slot-45 capes over armour.
- **More Scarves' crafting-recipe costs** were not expanded; the record CLI does
  not resolve container entries, so the prior record's "extreme cotton/flower
  counts" claim stays **[unverified]**.
- **ElSopa tier ceiling.** The matched-size comparison cannot see detail that
  exists only above a smaller tier's top mip, so "4k adds nothing" is proven for
  every size the tiers share (2048 down to 128) and **not** proven for the 4096
  px level itself. The tier call rests on the play-band tie plus the 4x VRAM
  cost, not on a claim that the 4096 level is empty.
- **Nexus permission text** was read from each mod's own public page. The
  quotes above are verbatim from the "Permissions and credits" block or, for
  `6369`, from the description section it points to.
