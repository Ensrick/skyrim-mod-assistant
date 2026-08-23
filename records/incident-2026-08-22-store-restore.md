# Incident - 2026-08-22 mass-unreview + backup restore

**What happened:** Aug 22 12:30-12:56 the relay applied a runaway flood of
'unreviewed' rows (~48,600 unique ids - effectively a catalogue-wide reset);
relay page-logging stopped at 12:05 the same window. The live decision store
was subsequently restored from the Aug 21 13:16 backup (the v015 export).

**Cost:** every decision made between Aug 21 13:16 and the crash was rolled
back. The relay ledger proves 271 of them (245 keeps / 26 skips); these were
re-queued and re-applied on 2026-08-23 (see decisions-pending -> applied, and
the restore-reconciliation line in the audit). Decisions made manually in the
browser during that window without passing through the relay are NOT in any
ledger and are unrecoverable - they must be re-made on encounter (this is why
already-reviewed mods resurfaced).

**Not touched:** 3 ledger-vs-live mismatches (130669, 33746, 2057 - ledger
said skip, live says keep) were left as-is on the assumption they are
deliberate post-restore overrides; confirm at leisure.

**Hardening recommendations (curator-side):**
1. Batch guard: refuse or require confirmation for any apply batch containing
   more than ~50 'unreviewed' rows - a flood of unreviews is never legitimate.
2. Automated nightly export of the live decision store (the manual Aug 21
   export is the only reason the restore point existed).
