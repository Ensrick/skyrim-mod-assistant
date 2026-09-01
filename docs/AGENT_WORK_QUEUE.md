# Agent work queue

Durable queue for delegated Skyrim work. This file records assignments so work
does not disappear when all concurrency slots are occupied. It is not authority
to install dependencies or change Keep/Skip decisions that the user has not
approved.

## Active

- None. All delegated audits and the Varinia fragment repair are complete.

## Pending - authorized

- None. Previously queued work has completed or is active above.

## Keep-review coordination

- Codex owns the **top-down** pass: newest `addedAt` first, using the preserved
  2026-08-26 curator export as the stable baseline. The current cursor has
  advanced through Nexus SSE **69240**; the next entry is **72351** (`Forest
  Cat`). Nexus SSE 70589 (`Better fur - Merchant's hat`) was also explicitly
  kept and installed out of order and is already decided when the cursor reaches it. Publican's
  Perch plus Samples of Stools (189530),
  Morthal Swamp Bald Cypress (189488), Katana - Yoto Hatamonba (187162), and
  Interesting NPCs Party Banter (104014) were passed to agents without Keep/Skip
  decisions; Additional Companions Members (144315) and Additional Thieves Guild
  Members (144351) were skipped.
- Claude owns the opposite, oldest-first end. Both assistants must record every
  decision by game-domain plus Nexus mod ID in `docs/KEEP_REVIEW.md` before
  moving their cursor.
- Claude's ascending cursor opened 2026-08-29 at the oldest keep, Nexus SSE
  **62271** (`addedAt` 2026-07-26T19:00:40Z). Ordering is `addedAt` ascending
  over the same frozen 2026-08-26 export (1,307 SSE keeps, 1,235 of them not
  yet installed). Decisions land in `docs/KEEP_REVIEW.md` section 8 under
  dated sub-headings; the cursor line below is the resume point.
- Claude cursor: **not yet advanced** - first tranche (oldest 100) under
  review.
- Before presenting or acting on a mod, check the decision ledger for the ID.
  If the other assistant already recorded it, skip past it. If two recorded
  decisions disagree, stop and return the conflict to the user; neither wins by
  recency or position.
- Mods the user adds while either pass is running belong to a separate new-items
  intake. They do not move either frozen cursor and therefore cannot silently
  cause overlap.

## Standing state checks - both assistants

INIs and profile settings are build state, not user preference. Before and after
every launch, and after any Steam update or vanilla-launcher run, verify the
deliberate keys in `docs/INI_AND_PROFILE_STATE.md` and that the profile still has
`LocalSettings=true`. The game silently reset them on 2026-08-31 (#98). The same
applies to the other silent-state failures already on file: plugin enable markers
after any LOOT sort (#73, #100), SKSE DLL staging depth (#103), and ledger
coverage (#102).

## Changelog rule - both assistants

`CHANGELOG.md` at the repo root traces every change to its source (user
directive 2026-08-31). Before moving on from any change - install, removal,
park/unpark, INI key, generated overlay, tool change - write its entry with a
named source. No batch is done until a verification launch passes (main menu
in under 60 seconds AND the save loads); entries stay `UNVERIFIED` until then.
A `FAILED` launch means the unverified pile gets bisected before anything else
lands. Full policy: "Changelog discipline" in `docs/CURATION_POLICY.md`.

## Dispatch rule

Dispatch the oldest authorized pending item when an agent slot becomes free.
Never displace an active assignment merely to shorten this queue. External mod
archives remain vendor inputs and are never committed to the public repository.
Every completed research assignment must be added to `docs/DEFERRED_DECISIONS.md`
and surfaced to the user as a decision packet before another non-queued research
assignment is started.

## Recently completed

- Orc Strongholds AIO (150246) exact archive/patch audit. Hold pending a user
  decision on its replacement-main dependency model and authorization for a
  disposable DA06/pathing test; nothing was installed.
- Grand Solitude + Solitude Docks Updated + selective Snazzy cell/module
  matrix. Exact compatible layering and patch boundaries are documented;
  nothing was installed.
- Varinia 1.1.0 six-fragment correction and 3DNPC overlap audit. The omission
  is a packaging / generated-source defect; a private six-PEX overlay passed
  strict compilation, decompilation, normalized sibling-bytecode comparison,
  and headless profile audits. The 17 shared 3DNPC chains need no compatibility
  ESL. Vendor files remain immutable and the derivative overlay is not
  distributable without author consent. Full record:
  `records/varinia-private-fragment-fix-2026-08-30.md`.
- Publican's Perch and Samples of Stools exact archive audit. Current releases
  are Hold pending author fixes or a separately approved owned repair.
- Interesting NPCs and Party Banter health/quality audit. Both are Hold pending
  city architecture and, for Party Banter, an audio-quality decision.
- Katana - Yoto Hatamonba competing-port, provenance, mesh, balance, and
  named-NPC fit audit. Hold / conditional Keep; nothing installed.
- Current tree-overhaul comparison and Morthal Bald Cypress audit. The later
  user decision supersedes its provisional composition: full NotWL 3.14 is
  installed; Nordic Cut is rejected from this stack and Mild Lands is not
  installed. Cypress remains a conditional future decision.
- Scrambled Updates audit. Nexus 1.1.0 is Hold because SKSE 2.3.1 rejects its
  target legacy DLLs before preload and the available mutation/modal approach
  violates project policy.
- Apparel Preview source port and runtime 1.7.104 validation; activation remains
  blocked on a separately approved player-camera companion.
- City/interior overhaul landscape and Grand Solitude comparison.
- Intrusive camera-space hit-effect candidate research, documented on GitHub
  issue #52; implementation is not authorized merely by that research.
- Believable Weapons retexture compatibility audit. Xavbio Silver Armor and
  Weapons Retexture SE 2.1.1 is directly compatible; no patch is needed.
