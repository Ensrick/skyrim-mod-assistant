# Mod lifecycle and change control

This is the normative process for every change to the Skyrim build. It binds
the lead session, Claude, Codex and delegated agents. A mod being visible in
MO2 is not proof that an installation is complete.

The user owns taste and adoption decisions. Automation owns bookkeeping,
compatibility evidence, repeatable tests and diagnostics. No assistant may add
an optional mod merely because it would help a test. A dependency explicitly
required by an already-approved mod may be adopted, but it follows this same
process and receives its own Keep.

## Authorities and invariants

Four representations describe the live build and must agree:

1. the physical directories under the MO2 `mods` directory;
2. the profile's `modlist.txt` enable state;
3. the profile's `plugins.txt` discovery and activation state;
4. `records/installed-mods.json` provenance and intent.

The Nexus curator is a fifth authority for user intent:

- **Keep** means the mod is physically present in the live MO2 instance,
  whether enabled or deliberately parked;
- **Skip** means it is not present in the live instance;
- **unreviewed** means deferred, under investigation or awaiting a decision.

An installed Nexus mod without a live Keep or durable pending-Keep operation is
an incomplete transaction. A Keep with no installed mod and an installed Skip
are curation defects. Locally authored artifacts have no Nexus Keep; their
source-build and distribution records are mandatory instead.

Run `py -3 audit/profile_reconcile.py` to compare the four build authorities.
Any failure blocks another mutation and blocks launch. `--adoption-plan`
prints facts for missing ledger rows without editing the ledger or inventing
provenance.

## State machine

Every mod or owned artifact moves through these states:

`proposed -> user-approved -> staged -> applied/unverified -> static-verified -> runtime-verified -> playtest-accepted`

`Skip` moves directly from proposed/deferred to rejected. Disablement is not
removal: a parked mod remains installed, remains Keep and has
`enabled: false` plus a reason. Removal archives or deletes the physical mod,
removes its live ledger state and clears its Keep only after rollback evidence
has been retained.

Only `runtime-verified` is a technically complete installation. Subjective
acceptance can remain open without blocking unrelated work, provided its issue
is labelled `status:needs-test`.

## One transaction for every change

The sequence below applies to installs, upgrades, downgrades, removals,
enable/disable operations, FOMOD reselections, generated outputs, owned
patches, INI changes and DLL replacements.

1. **Declare scope.** Read the shared coordination board, name the exact target
   and acquire the MO2 profile claim before any live write. Never mutate from a
   stale worktree.
2. **Freeze the before state.** Record modlist/plugins/ledger hashes, active
   plugin set and target archive or artifact hashes. A moving profile invalidates
   the plan.
3. **Prove provenance.** Pin the source page/repository, mod ID, file ID,
   version, archive SHA-256, permissions and immutable vendor payload. Secret
   tokens and licensed archives never enter Git.
4. **Inspect before applying.** Inventory plugins, DLLs, scripts, BSAs, record
   types, masters, assets, FOMOD choices, texture-policy exceptions and author
   requirements. Follow `docs/CK_FIRST_DOCTRINE.md`.
5. **Review patch impact.** Produce the mandatory impact receipt described
   below. Resolve required official/community patches and owned-patch updates
   before activation. An unresolved taste or architecture choice blocks the
   transaction and returns to the user.
6. **Apply through the canonical controller.** Nexus installs use the canonical
   `audit/install_mod.py`; local artifacts use an owned, deterministic package
   and source-build record. Direct MO2Headless calls are diagnostic primitives,
   not an accepted install path.
7. **Commit all postconditions atomically.** Physical folder, profile state,
   plugin intent, ledger row, Keep/pending Keep, FOMOD plan, patch receipt,
   changelog and test state are one logical operation. Failure of the Keep
   queue or ledger write makes the whole operation incomplete.
8. **Run static gates.** At minimum: profile reconciliation, Keep coverage,
   missing/late masters, LOOT messages, DLL placement/version checks,
   provenance/package verification, owned-patch freshness and unexpected
   conflict deltas.
9. **Run the test contract.** `docs/TESTING_POLICY.md` defines the disposable
   new-character and save/load stages. Capture logs and a build fingerprint.
10. **Close or leave explicit debt.** Link the verification record from the
    changelog and issue. Pending subjective observations remain an issue, not
    an undocumented memory. Release the profile claim.

A failed transaction is never hidden by carrying on. Restore the before state
through the MO2 journal or finish the missing postcondition, then reconcile
again.

## Patch-impact receipt

Every profile change examines every owned patch which could depend on the
changed files. “It has no new masters” is not enough: a generated balance patch
can need regeneration when a newly added plugin introduces records without
ever becoming its master.

Each owned artifact's `records/source-builds/*.json` record must declare an
`impactPolicy`:

```json
{
  "impactPolicy": {
    "mode": "declared-inputs | record-types | full-profile | asset-paths | manual",
    "inputs": ["Mod name", "Plugin.esp"],
    "recordTypes": ["WEAP"],
    "assetGlobs": ["meshes/weapons/**"],
    "onRemoval": "regenerate",
    "rationale": "one sentence explaining the dependency boundary"
  }
}
```

The per-change receipt lists each candidate patch and exactly one outcome:

- `regenerated` — new deterministic output and hashes;
- `amended` — a reviewed patch/config change;
- `verified-current` — evidence shows the existing output still covers the
  changed inputs;
- `not-affected` — evidence names the disjoint records/assets/rules;
- `blocked-decision` — the user must choose between real alternatives.

Missing `impactPolicy` is maintenance debt and forces manual review; it never
means “not affected.” Generated outputs tied to the whole load order (weapon
normalization, leveled-list synthesis, conflict forwards, Pandora, BodySlide,
xLODGen/TexGen/DynDOLOD) are stale after a relevant input or ordering change
until regenerated or explicitly proved unchanged.

## Change receipt minimum

The durable receipt for a completed transaction records:

- operation ID, UTC time, owner and linked issue;
- before/after profile fingerprints;
- target mod/artifact identity and exact file hashes;
- expected and observed mod/plugin deltas;
- Keep status and ledger row identity;
- patch-impact outcomes and evidence;
- static gate results;
- required test class, fresh-character ID and verification record;
- rollback transaction/archive location;
- distributability: `distributable`, reproducible `recipe`, or `local-only`.

The receipt contains no private key and no third-party archive. Vendor files
remain immutable; all fixes ship as separate owned patches or reproducible
local recipes.

## Current migration rule

This policy is fail-closed for all new work. Existing gaps found by
`profile_reconcile.py` are migrated under issue #102 as one bounded
reconciliation: verify provenance, repair rows and explicit disabled intent,
then capture a clean baseline. A generated stub is an investigation aid, not a
finished ledger row.

Archive identity is not yet proof of the extracted payload: a FOMOD selection
or later in-place edit can produce a different folder while retaining the same
download hash. Issue #233 tracks normalized installed-payload manifests and an
automated vendor-drift gate. Until that gate lands, every changed or adopted
folder needs a full file/hash manifest in its change receipt; unexplained
third-party-folder drift blocks acceptance and is repaired by reinstalling the
vendor payload plus a separate owned patch.
