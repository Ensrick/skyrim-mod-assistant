# Currency denomination repair — 2026-09-06

Status: currency 0.3.0 installed; static checks and dependent patch refreshes
passed. Transaction `20260906T063118626Z-c71bb2e136f9` preserved
priority 274, enabled state, every mod/plugin entry and their order. Only the
controller's modlist header comment changed. All 105 installed files match the
reviewed archive, and all 73 runtime payload files checked are effective winners.
Weapon metadata transaction `20260906T063900070Z-4ab34e480a6e` preserves the
exact weapon ESP and all 27 translations. Cloak proof transaction
`20260906T064200560Z-1dcaca3ea8b2` preserves all 240 directives and confirms 569
parsed mesh winners, no slot 58 partition hits and 35 winning SkyPatcher files.
No game was launched. Runtime acceptance is **UNVERIFIED**.

## Requested behavior and actual implementation

The previous ECE payout handlers replaced backend money with an equal count
of copper. The replacement retires those transaction owners and uses one
native ledger bridge, with an ESL-flagged companion patch and exact winning
distribution/configuration overrides. Vendor mod folders and user saves are
not edited.

All modern denomination families use copper 1, silver 10 and gold 100. An
eligible source uses efficient change 80% of the time; the other 20% breaks
at most one larger coin. Both variants preserve the original value:

| Value | Usual contents | Less-efficient alternative |
| ---: | --- | --- |
| 24 | 2 silver, 4 copper | 1 silver, 14 copper |
| 100 | 1 gold | 10 silver |
| 124 | 1 gold, 2 silver, 4 copper | 12 silver, 4 copper |

The seed is stable per source/family, so reopening a container is not a new
roll. Ordinary dead generic NPCs, safe respawning containers and explicitly
supported purses are covered. Unique/quest/merchant/follower actors, player
storage and unsafe or ambiguous sources are deliberately excluded. This is
not a claim that every inventory in every mod is rewritten.

Mede, Ulfric, Dram, Oshka and Ohzer receive explicit Copper/Silver/Gold names
and distinct 1K-or-smaller tier diffuses, preserving their meshes' geometry
and other texture bindings. Dormant Varken assets also exist but its route
remains disabled pending a region decision. Ancient coin routes remain
distinct. Canonical Drakr and Sancar retain singleton tender treatment.
Wyrmstooth and Beyond Reach retain the current Septim fallback; this does not
invent new regional currencies for them.

Loose placed coin keeps the approved 75/20/5 tier roll and regional mapping.
Changing silver from 25 to 10 changes that roll's mean value from 10.75 to
7.75; it does not change the authorized probabilities. Septim weights remain
0.06/0.07/0.13, and regional weights are retained rather than newly certified
as physically realistic.

Gold001 is the hidden purchasing-power backend. Physical coins remain
droppable/storable and weighted, but cannot be sold through ordinary barter
to create a second payment for the same money. Pickup/drop/storage and
backend spending are reconciled, including pending transactions at save time.

## Save boundary

**Start a fresh character for currency 0.3.0. Do not load a pre-0.3.0 save
with this package.** Old Papyrus instances cannot be proved retired merely
by stopping their quests. The previous package must remain paired with old
saves for rollback; no cleaning, deletion or migration of those saves occurs.

New admitted saves carry an exact ECDN/ECMK v2 checkpoint with configuration
fingerprint `EC66DF8F57CF4726`. The launcher rejects absent, malformed, old,
duplicate or mismatched checkpoints, and verifies the active companion ESP
plus winning DLL/JSON/ESP hashes against the trusted release receipt.
Thirteen synthetic gate tests and public Check run 34015591583 passed at
`52dfe2e`. A menu-only launch is never a loaded-save PASS. Manual loading through
Skyrim's menu cannot be prevented by this external check.

## Verification and distribution

Native DLL and configuration have passed independent review and two identical
clean builds; native DLL SHA-256 is
`3866DD5FC35C8223C24A34379C464444C114A2BAD9A17A4D9EF3905802F50CF8`.
All 36 private tier-asset hashes and sizes match independent builds. Full
package proof includes exact record/VMAD/parent-dialogue scope, master/link
checks, script compilation, semantic serialization roundtrip and archive
reproducibility. An application-boundary error handler returns failures in
captured STDERR rather than leaving unhandled audit exceptions to Windows.

Original source, credited permitted M.I.N.T. script changes and user-local
asset recipes belong in the public project. The local generated archive is
**not publicly redistributable as a whole**: the coin designs remain licensed
vendor derivatives. The native DLL's linked CommonLib terms and corresponding
source are documented separately; the complete package is not all MIT.

Still owed in game: initial admission; mixed corpse/purse contents before
normal and Quick Loot display; regional countertop coins; pickup/drop/storage;
shopping/training/horse purchase/bank exchanges; save/reload with pending
transfers. Record telemetry for each case. Do not close issues 207/209/217 or
claim economic correctness from build tests alone.
