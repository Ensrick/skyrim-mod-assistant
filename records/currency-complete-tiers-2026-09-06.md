# Complete regional currency tiers — 2026-09-06

Parent: #207. Denomination acceptance: #217. Transaction/exception acceptance: #209.

## Outcome

Currency integration **0.4.0 is installed and statically verified, not gameplay-verified**.
The former single-denomination/ancient exemptions contradicted the user's requirement
and have been removed. Every supported design has copper, silver and gold worth
exactly **1 / 10 / 100**: 18 designs, 54 canonical physical forms and one recognized
Gibber input alias. This includes the four Drakr faces, two Gibber faces, Mala,
Mallari, Nchuark, Sancar and Bruma's separate authored Ayleid design.

The original mods remain untouched. The changes live in an owned package with two
ESL-flagged plugins, native accounting, narrow script/configuration overrides and
user-local generated coin assets. No new third-party mod was adopted.

## Distribution contract

- Eligible generic dead NPCs, safe respawning containers and supported purses use
  80% efficient change and 20% breaking one larger coin into the next tier.
  Value 24 normally yields two silver and four copper; the alternative is one
  silver and fourteen copper. A 100-value payout normally yields one gold coin.
- Loose authored vanilla coins retain the approved 75% copper / 20% silver / 5%
  gold distribution. Existing physical coins preserve their value tier during
  regional swapping, including after being dropped.
- Fourteen cultural/region routes cover modern and ancient locations. Bruma's
  own Ayleid model is preserved. Locations without an established route retain
  Septims; no bespoke Beyond Reach or Wyrmstooth currency was invented.
- Unique/quest/vendor/follower actors and protected or ambiguous storage remain
  excluded from unsafe inventory rewriting. This is not a coin-design exemption.
- Names explicitly identify the metal; recognition does not depend on color.
  WiZkiD's Ancient Imperial Septim artwork remains part of the Septim assets.

## Verified evidence

- Two reproducible native, main-plugin, companion, Papyrus and original archive
  builds; 108 reproducible tier assets. Main: 1,772 records / 12 masters.
  Companion: 405 records / 5 masters. No unresolved record links.
- Independent exact whole-purse probability and binary audits; 42 purse bases.
- 136 Python regression tests, native checks and passing Windows CI for
  `0aa6e4a` and final ordering correction `a79d2d5`.
- Final ZIP: **201 files, 33,320,658 bytes**, SHA-256
  `AC738CCA9AD67ECFAC109B7A85D73C979985F8BBC3311A7015D165C3C4F8F86A`.
- Final installation and effective MO2 file winners: **201/201 exact matches**.
  All 55 physical plugin-record winners pass across 350 runtime plugins.
- Two same-path ECE overrides remove 14 competing legacy physical-coin writes.
  All 55 physical forms now have exactly one correct SkyPatcher writer, without
  relying on directory iteration order. Hidden accounting and four plural-name
  effects are retained. The archive-only correction added two files and changed
  none of the original 199 entries.
- Weapon refresh preserves the exact ESP and 27 translations. Cloak refresh
  preserves all 240 directives and proves 569 mesh winners / 35 configurations.
- Controller audit, installed-ledger plugins, load order, fresh-character
  admission and Keep coverage pass. **195 installed Nexus identities / 195 Keeps**.
- Full preflight: zero blockers, eight documented warnings. The new helper must
  be synchronized to game-side Plugins.txt by the sanctioned launcher on the
  next authorized launch. Five preexisting enabled-mod ledger omissions remain
  #102 work; snapshot, Steam-overlay, save-backup and save-admission notices are
  not a gameplay PASS. No game was launched.

Final currency transaction: `20260906T175635745Z-6c53c4cf09b2`.
Weapon refresh: `20260906T174820592Z-0fdb94f225b8`.
Cloak refresh: `20260906T175856840Z-a7633843ec76`.
Exact hashes and rollback provenance are in the three current source-build receipts.
The four preexisting conflict reports are preserved and excluded from this work.

## Decisions deliberately left open

1. Keep the existing automatic conversion of the carried wallet when changing
   regions, or preserve foreign coins until an explicit exchange?
2. Keep the existing regional merchant buy/sell perks? These are separate from
   the exact 1/10/100 accounting values and were not rebalanced here.
3. Raise the fifteen new helper purse budgets? Current small 2–28, medium 5–42
   and large 10–70 budgets cannot contain a 100-value gold coin. Other authored
   purse budgets and loose coins are not capped by these helpers.

Standalone publication also needs complete prerequisite documentation, portable
provenance paths and alignment of the cosmetic native-version log string. Private
coin NIF/DDS/ESP/PEX/ZIP outputs were not uploaded; eligible source and local-build
recipes are published separately with their actual licenses.

## Remaining acceptance

**Use a fresh character. Do not load 0.3.0 or earlier currency saves, and do not
clean or delete co-save data to bypass admission. Existing saves are untouched.**

- [x] Complete and independently audit the two-plugin/three-tier package.
- [x] Reversibly install, update ledger/receipts and refresh dependent proofs.
- [ ] Verify each region and metal visually in the game.
- [ ] Test corpse, container and purse contents before first opening, including Quick Loot.
- [ ] Test pickup/drop/storage and barter, training, bounty, horse and exchange services.
- [ ] Prove save/reload conservation and capture logs before closing #207/#209/#217.
