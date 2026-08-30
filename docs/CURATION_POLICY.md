# Nexus curation state policy

Effective 2026-08-30, the three practical states are:

- **Keep**: at least one file from that Nexus mod page is installed and enabled
  in the current `Default` MO2 profile. Keep is the active load-order list, not
  a wishlist or candidate shortlist.
- **Skip**: the user has explicitly rejected the mod for the current modpack.
- **Unreviewed**: the mod is not installed and has not been rejected. It may be
  weighted, deferred, under investigation, awaiting dependencies, awaiting a
  patch, or simply not reviewed yet.

Research and a favorable recommendation do not create a Keep entry. The normal
adoption sequence is explicit user approval, archive/licence audit, headless
installation and enablement, verification, and only then Keep plus removal of
the selected mod's author from Excluded. If an installed mod is disabled or
removed, clear Keep back to Unreviewed unless the user separately chooses Skip.

For a mod that adds weapons, shields, armor, clothing, undergarments, or
jewelry, adoption also opens a mandatory item-by-item integration record under
`docs/EQUIPMENT_INTAKE_POLICY.md`. Keep still means the approved vendor mod is
installed and enabled; it does not imply that unresolved balance, lore role,
or distribution choices were silently decided.

The live curator is reconciled against enabled MO2 state with
`nexus-local-curator/scripts/reconcile-installed-keeps.py`. Its queued mutation
uses compare-before-write guards and maps inactive Keeps to Unreviewed, never
to Skip.
