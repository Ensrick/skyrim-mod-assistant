# Live profile reconciliation — 2026-09-04

Issue: [#102](https://github.com/Ensrick/skyrim-mod-assistant/issues/102)

This is a read-only snapshot. It records the migration debt exposed by
`audit/profile_reconcile.py`; it does not invent ledger provenance and it does
not alter the live MO2 profile.

## Frozen authorities

Captured at `2026-09-04T20:30:23Z`:

| authority | SHA-256 |
|---|---|
| `profiles/Default/modlist.txt` | `754C30FE93EB9BD35D13D115DDE0447E776B80AA14553BCBC35CFDA51B9CDED2` |
| `profiles/Default/plugins.txt` | `912DCB2047092CFCA8DDF7A26FA95392CF0B4333F89E2B9B04E8B084DAF0B5BA` |
| `records/installed-mods.json` | `3594C37EA471599504EB45C564475E1A423EC185B9241D859ADEF7B9CC8FD7AF` |

The snapshot contains 284 physical mod folders, 284 profile rows (257
enabled), 278 ledger rows, and 269 discovered plugins (265 active). The
reconciler reports 18 failures and one explicit archived-row warning.

## Failures

### Eight unledgered physical folders

| physical folder | profile state | known disposition/provenance lead |
|---|---|---|
| `Ensrick - Proteus MCM Indexed Hotkeys` | enabled | owned 0.1.0 package and source/build manifest exist under `skyrim-tools-source/PROTEUS-mcm-hotkeys`; adopt as an owned artifact after exact hash verification |
| `Ensrick - TDP Ulvenwald Wind Calibration (Private Test)` | enabled | owned 0.1.0 test package exists in the TDP wind-calibration worktree; adopt as private test output, not a Nexus mod |
| `FSMP` | disabled | Nexus 57339 archive is present; the existing row named `FSMP (disabled duplicate)` appears to describe this same folder and must be corrected, not duplicated |
| `Immersive Equipment Displays` | disabled | Nexus 62001 archive is present; retain as intentionally parked under #94/#201 until a runtime-compatible build is proven |
| `Nether's Follower Framework - RDO Support` | enabled | component selected from the installed NFF archive (Nexus 55653); record the exact component relationship |
| `Relationship Dialogue Overhaul Lite` | enabled | Nexus 42068 archive and PR #225 installation evidence exist |
| `Skyrim Unbound Reborn - RDO Lite Patch` | enabled | component selected from Nexus 27962 archive; record the parent archive and FOMOD/component choice |
| `Water for ENB - Generated Conflict Patch` | disabled | locally generated 42-byte `Water Seams Fix.esp`; do not adopt as valid output until its purpose and validity are proved under #46/#134 |

### Seven enabled-state mismatches

The ledger says enabled while `modlist.txt` says disabled for:

- `Crafting Recipe Distributor`
- `CS Screen Space GI`
- `CS Skylighting`
- `CS Terrain Blending`
- `CS Terrain Variation`
- `CS Upscaling`
- `CS Wetness Effects`

The live profile is the observed state. The ledger must record `enabled: false`
plus the existing technical reason; these rows must not be silently re-enabled
to make the check pass.

### Two plugin-inventory mismatches

- `Azurite III Darker Nights` physically ships
  `Azurite Weathers III - Darker Nights.esp`, omitted from its ledger row.
- `Proteus` physically ships `PROTEUS.esp`, omitted from its ledger row.

### One stale row

`FSMP (disabled duplicate)` names no physical folder. Evidence indicates it is
the misnamed row for the disabled physical `FSMP` folder. Prove archive and DLL
hash identity, then rename/amend that row in place.

### Non-failure warning

`Azurite III HDR` is a valid disabled row with an existing `archivedTo` target.
It remains recorded as an archived rejection and is not part of the live tree.

## Migration order

1. Reconfirm the three authority hashes before writing. If any changed, rerun
   the read-only snapshot and do not apply this stale plan.
2. Verify each archive, package, source-build record, file ID, installed path,
   plugin inventory and intended enable state.
3. Correct the seven state flags, the two plugin arrays and the FSMP row.
4. Add reviewed rows for the seven genuine missing artifacts. Quarantine or
   remove the 42-byte Water Seams placeholder unless it can be proved valid.
5. Apply or durably queue each required Nexus Keep; locally owned artifacts use
   source-build/distribution records instead.
6. Rerun `profile_reconcile.py`, Keep coverage, package/provenance gates and
   patch-impact review. Zero failures is required before another profile
   mutation or verification launch.
7. Capture the clean post-migration fingerprint and link it from #102.

The migration edits `records/installed-mods.json`, currently coordinated as a
Claude/Fable-owned file. It must be applied in one claimed transaction or
handed off explicitly; parallel edits are not safe.
