# Overnight report - 2026-08-23

Running log of the autonomous session; final numbers at the bottom will be
updated before you read this.

## 1. Base setup - COMPLETE

36 mods installed through the MO2 controller, LOOT-sorted, verify clean, every
SKSE dll export-checked. Full list in `records/installed-mods.json`; tiers in
`BASELINE.md`. Since you went to bed: MCM Helper, KID, Base Object Swapper,
Open Animation Replacer, BodySlide, Crafting Recipe Distributor, USSEP 4.3.9,
SSE Engine Fixes 7.0.20 (+ preloader to game root), Bug Fixes SSE, Scrambled
Bugs, CrashLogger 1.25.0, SSE Display Tweaks, Skill Uncapper.

**One manual step remains before first launch: run Pandora once through MO2**
(its `--auto_run` headless mode timed out without output). Only XPMSSE
weapon-style animations depend on it.

## 2. Keep review - COMPLETE

`docs/KEEP_REVIEW.md`. Read its top section first: A-F are the decisions,
everything below is the evidence tables. Headlines:

- 6 keeps are fallout from slots you already decided (AFT, EFF, old HDT-SMP,
  Downgrade Patcher, BnP skin, Tempered Skins) - say the word and they queue.
- 7 NEW slots the Tier-4 table missed: standing stones, religion, vampire
  overhaul (4-way), children policy, dragon package, stagger, the CACO seam.
- 9 hard orphans, most with nuance already resolved (OAR satisfies the DAR
  requirements; the new Uncapper satisfies Adaptive Leveling).
- Verified with file lists overnight: Khajiit/Argonian textures are NOT
  body-locked (CBBE variants ship); Combat Music Fix NG is standalone.

## 3. Undecided sweep - COMPLETE

Skip-only, evidence-cited, live blocklist (20,761 authors), aesthetic and
adult categories untouched per your instruction. Every verdict appended to
`sweep2_audit.jsonl` with rule + evidence; wholesale reversal is one command.

Quality control that ran tonight: two spot-check rounds caught two
false-positive classes (ReShade-presets-for-CS, and content mods with
non-English pages); both classes were guarded in code and all nine affected
verdicts reversed to undecided before they could apply.

## 4. Numbers - final

**Rule sweep: the entire catalogue, 137,746 offsets.** Untouched wholesale per
your instruction: 93k blocked-author entries, 7.6k aesthetic-category mods,
~950 adult-flagged. Verdicts written: **996 rule-based skips**, every one with
evidence in `records/overnight-audit-2026-08-23.jsonl`:

| rule | skips |
|---|---|
| translation / non-English | 486 |
| ENB/ReShade preset (CS decided; CS-compatible presets guarded) | 198 |
| author-declared dead/superseded | 179 |
| Legacy of the Dragonborn exclusive | 72 |
| requires Live Another Life (slot decided: SUR) | 45 |
| VR-only | 29 |
| joke/meme | 7 + 1 parody |

**Deep-read pass (still running): 17,680 survivors read individually so far
(83%), 491 skips** - new skip classes found while you slept: author-marked
OUTDATED/deprecated/superseded pages, patches whose base mod was deleted from
Nexus, wrong-runtime backports (1.5.97-only), guide/modlist/Wabbajack pages that
aren't mods, features folded into Community Shaders 1.4.7, clean-save archives,
downgrade patchers (runtime decided: 1.7.99), and dozens more DV/FR/RU/CHS
translations. Slot harvest grew to **523 candidate entries** in
`docs/SLOT_CANDIDATES.md` - headline finds: NAT.CS III (CS-native weather),
Lux CS + MLO2 + ISL Helper (CS lighting stack), USSEP-Pandora patch 139572,
xVASynth (the Vigilant/Beyond Reach revoice tool), Beyond Reach
dialogue-conditions fix 56542 (fixes your "NPCs won't talk" complaint), the
Vicn delayed-start trio (late-game gating exactly as planned), Equippable
Underwear for NPCs 45277 (rival to our home build), Auto Skeleton Patch 176724
(may remove the Pandora requirement), and Modex 137877 (modern AddItemMenu).

Original first-500 summary: top of the curve clean, 15 skips
(each cited: TDM-conflicting movement mods, Gray Cowl 2017 vs the kept 10th
Anniversary, Sky Sync standalone vs CS core, Trainwreck vs installed
CrashLogger, engine-fix duplicates, Falskaar support stack, QuickLoot RE...).
The top of the curve is clean - its real yield was **167 slot candidates
across 66 slots** in `docs/SLOT_CANDIDATES.md`: Lux, Mysticism, NotWL,
Folkvangr, Skyland, NORDIC UI, Valhalla, SunHelm and the perk trio were never
purged, just undecided.

**Quality control:** two spot-check rounds caught two false-positive classes
early (ReShade-for-CS presets; content mods with non-English pages - iNeed was
nearly lost to that one). Both were guarded in code and all 9 affected
verdicts reversed. One lost-update race on the relay queue was detected
(sweep vs keep-queue writers) and the five affected keeps re-queued post-sweep.

## 5. Queued for the curator (applies when Firefox is up)

1,068 total: 1,011 skips, 35 keeps (every installed mod is now curated as a
keep, including the race-lost five), 9 unreviewed restores. Applies when
Firefox opens.

## 6. Follow-ups surfaced by the requirement cross-check

- **Water for ENB was still "skip" in the curator** despite your verbal
  correction that it supports Community Shaders - a keep is queued to fix the
  record.
- **Project ja-Kha'jay (Khajiit NPC diversity) is skipped**, but the Moonpath
  review praised its Moonpath integration patch. If you want that integration,
  the base needs un-skipping; its patch collection was skipped tonight as a
  companion of a skipped base.
- 18 companion mods (settings loaders, patch collections, addons) were skipped
  because their base mod is skipped - rule `req-skipped` in the audit.
- ConsoleUtilSSE-, old-Uncapper-, and FISS-requiring mods were deliberately NOT
  skipped: those requirements are satisfied by installed successors or are
  soft dependencies.
