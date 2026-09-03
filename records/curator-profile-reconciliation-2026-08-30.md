# Curator reconciliation to the enabled Default profile

Initial reconciliation completed: 2026-08-30. Current state reverified after
the Better Fur, visual-foundation, and MLO2 adoptions later the same day.

## Result

The Nexus curator now uses the user-defined state model:

- Keep: a Nexus page contributes at least one installed and enabled file to the
  current Default MO2 profile;
- Skip: explicitly rejected by the user; and
- no decision: not installed and not rejected, including deferred, weighted,
  researched, or patch-blocked candidates.

The initial effective Skyrim SE curator state contained **91 Keep** decisions
and **4,527 Skip** decisions. That initial reconciliation against the enabled MO2
profile reports zero inactive Keeps to clear and zero active pages missing
Keep. Representative deferred candidates--Nature of the Wild Lands (63604),
Whiterun Simple 3D Wooden Trellis (178881), Rally's Market Stalls (81282),
Interesting NPCs Party Banter (104014), Scrambled Updates (189511), Orc
Strongholds AIO (150246), Publican's Perch (167277), Samples of Stools (189530),
and Apparel Preview (185334)--all have no decision. Varinia (148853) remains
Keep because it is enabled.

That paragraph describes the initial checkpoint. Nature of the Wild Lands is
no longer deferred; see the later visual-foundation delta below.

## Later Better Fur adoption delta

After the user explicitly kept and installed Better fur - Fine clothes (69240)
and Better fur - Merchant's hat (70589), guarded reconciliation observed both
pages as Unreviewed and queued exactly those two changes. The extension relay
then consumed the batch. A fresh independent plan reports **126 active Nexus
IDs, 126 live Keeps, zero inactive Keeps, and zero active pages missing Keep**.
The current full decision count is **126 Keep** and **4,535 Skip**. Direct
read-only inspection confirms jg1/user 6520144 is absent from the Excluded
author list, as required by Keep protection. The durable machine-readable
snapshot was regenerated after application and now contains an empty change
set.

## Later visual-foundation and MLO2 delta

After exact enabled installation, guarded reconciliation set Skyland AIO
(34179), Nature of the Wild Lands (63604), and the NotWL Solitude Docks patch
(102443) to Keep. Modern Lighting Overhaul 2 (160748) was reconciled by its
separate adoption. Nordic Cut (161936) and Nature of Mild Lands (112765) remain
Unreviewed/no decision because they are not installed. A fresh independent
plan reports **130 active Nexus IDs, 130 live Keeps, zero inactive Keeps, and
zero active pages missing Keep**. Neither curator review cursor moved.

## Guard and reader correction

The first compare-before-write pass revealed that the old read-only
`curator_state.py` decoded only Firefox's compacted `modDecisions` snapshot and
ignored the extension's responsive per-mod journal keys. The relay batch was
accepted, but the stale verifier could not prove the effective result.

The reader was corrected to overlay `nlcModDecision:*` journal values over the
compacted snapshot, including Unreviewed removals. The reconciliation was then
regenerated from that effective state and applied through a second guarded
batch. A final independent plan contains zero changes. This also prevents
future compare-before-write operations from reading stale decision state.

The durable final machine-readable snapshot is
`records/curator-profile-reconciliation-2026-08-30.json`. The reproducible
controller is `nexus-local-curator/scripts/reconcile-installed-keeps.py`.

No mod was installed, disabled, or removed during this curation-only operation.
No deferred item was converted to Skip.
