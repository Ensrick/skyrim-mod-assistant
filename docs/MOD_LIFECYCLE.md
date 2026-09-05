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

Only `runtime-verified` is a technically complete installation. Until explicit
multi-change batch semantics exist under #235, one lifecycle stays open through
`playtest-accepted` and blocks the next mutation. This prevents a second change
from silently making the first plan's build fingerprint stale. A future batch
controller may share one final fingerprint and disposable test character across
explicitly declared changes; it may not infer a batch after the fact.

## One transaction for every change

The sequence below applies to installs, upgrades, downgrades, removals,
enable/disable operations, FOMOD reselections, generated outputs, owned
patches, INI changes and DLL replacements. Issue #235 is the implementation
master for routing all of those operations through one enforceable controller;
until a mutation type is implemented there, it is unsupported manual work and
must not be represented as lifecycle-complete.

Accordingly, the legacy `install_mod.py --sort` mutation is fail-closed while
#235 is open. LOOT may be run read-only for diagnostics, but applying an order
must eventually create the same before/after, patch-impact, rollback and test
receipts as any other profile change. PR #232's exact enable-state preservation
is necessary but not sufficient by itself.

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

### Nexus install command contract

`install_mod.py` is deliberately a two-pass controller. Both passes require an
issue number. The first pass downloads and installs the exact archive **with the
mod disabled**, inventories the resolved FOMOD payload, computes its full
content fingerprint and owned-artifact impact set, writes a draft beneath
`records/impact-receipts/`, then rolls the MO2 transaction back. It never
overwrites an existing draft or reviewed receipt.

The operator reviews every artifact row, supplies an outcome plus concrete
evidence (and exact hashes for amended/regenerated outputs), and repeats the
same pinned install with `--impact-receipt`. The controller recomputes the
payload and impact topology; any stale fingerprint, policy, artifact set,
issue, parse error or blocked decision rejects the receipt and rolls back. Only
an accepted receipt permits mod/plugin activation, ledger commit, Keep queue
and creation of the fingerprint-bound verification plan.

That receipt also carries the Nexus intake review: durable evidence of the
user's explicit approval, exact-file selection rationale, licence and
redistribution classification, requirements/required-patch review, staged LOOT
evidence, conflict evidence and an empty open-decision list. Research or an
issue number alone is not approval. Every named required patch must actually
exist as one enabled, ledgered MO2 folder before the receipt can pass. A patch
that ships plugins must name the required plugin identities in
`requirements.requiredPlugins`; each must be starred and the effective winning
file must come from that patch folder. A plugin-free patch is treated as an
asset-only requirement and its rationale belongs in the requirements evidence.

Every successful MO2 mutation must return a journal transaction ID. An absent
ID is accepted only when exactly one new committed journal manifest proves the
same operation and supplies it; a friendly response string or filesystem
side-effect is not evidence. An ambiguous unjournaled delta restores captured
profile before-images, quarantines a newly created target instead of deleting
it, re-runs reconciliation, and appends `records/lifecycle-recovery.jsonl`.
Expected failures and unexpected exceptions/interruptions after apply both
roll back in strict last-applied-first order and restore the exact prior ledger
bytes. A
`--replace` operation may not silently change Nexus mod ID; that needs a future
explicit curator migration transaction which can change old Keep to
Unreviewed and new ID to Keep atomically.

Updates are currently refused entirely. Correct update impact needs a retained
before image and an after image so removed records and packed/loose assets enter
the delta; auditing only the replacement folder would fail open. Removal,
enable/disable, FOMOD reselection, order and configuration controllers likewise
remain unsupported until #235 lands their transaction types.

The verification gate scans active `records/test-plans/` in both directions.
An install/update plan must have exactly one ledger binding. Deleting lifecycle
fields from its ledger row, or leaving a managed plan behind with no matching
row, is an invalid orphan and blocks preflight; abandoned plans must be moved to
an explicitly archived evidence location.

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

Disabled owned patches are included in the review set as well: enabling one is
a profile change, and a parked patch must not silently become stale. Policy
modes that depend on `inputs`, `recordTypes` or `assetGlobs` require a non-empty
selector. Overwrite is modeled as the highest-priority provider. Removal
analysis requires a retained before-image manifest/root; an empty directory
after deletion is not evidence about the records or assets which disappeared.
Asset-path matching indexes paths inside BSA archives as well as loose files.
Every referenced source-build record is content-hashed into the frozen audit
signature; a missing, unreadable or edited recipe invalidates the receipt.
Hashes for amended/regenerated output are accepted only from inside that exact
owned artifact's MO2 directory, never from an unrelated file elsewhere.

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
