# NotWL + Ulvenwald controlled tree diversity — 2026-08-30

Status: installed, enabled, statically verified; foreground acceptance pending
on issue #29.

## Decision and architecture

The selected route follows Tree Diversity Project's documented **NotWL base +
Ulvenwald swap** design:

1. full Nature of the Wild Lands 3.14 remains the sole placement authority;
2. Traverse the Ulvenwald 3.3.2 is enabled only as a lowest-priority asset
   dependency and `Ulvenwald.esp` is deliberately disabled;
3. Tree Diversity Project 1.0.1 supplies an ESL-flagged tree-record library and
   one Base Object Swapper configuration;
4. only the existing NotWL patch family remains active;
5. no vanilla dummy, Seasons files, Ulvenwald placement patch, or second city /
   worldspace placement ecosystem is active.

This captures the useful part of Invicta's mixed-tree direction without copying
its private patch or adopting its much larger bespoke forest stack.

## Exact immutable inputs

| Nexus source | Exact file | Version | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| Ulvenwald `57874` | `444742` | 3.3.2 | 1,101,626,726 | `6FD168C2F063A3C8DD4D3D5B8D1BC5D596B76721F3364542ACA80056DB0A7379` |
| Tree Diversity Project `155974` | `680001` | 1.0.1 | 2,436,474 | `606224ADE3AEE68444C681453712635DC45C4E66456D06E35EC7509F38185FCD` |

The deterministic selections are:

- `records/fomod-plans/57874-ulvenwald-3.3.2-assets.json`: required main
  meshes/textures/plugin plus the author's **No Seasons** autumn aspen choice;
- `records/fomod-plans/155974-tree-diversity-project-notwl-ulvenwald.json`:
  required TDP plugin plus `NOTWL base + Ulvenwald swap` only.

Neither vendor payload was edited. Ulvenwald's page forbids reupload and
requires permission for modification or asset reuse, so it is a required
external download. TDP is also retained as an immutable external dependency.
Publication policy is recorded in `records/restricted-mods.json`.

## Transactions and ordering

| Operation | Transaction |
|---|---|
| Install Ulvenwald assets | `20260830T233143674Z-ac84df658c57` |
| Disable `Ulvenwald.esp` | `20260830T233218061Z-14436378f8c2` |
| Initial below-NotWL placement | `20260830T233218219Z-153453fa307c` |
| Install TDP | `20260830T233240809Z-0f5adaaba3ef` |
| Group TDP above the NotWL asset stack | `20260830T233434734Z-e4d0c188568e` |
| Tighten Ulvenwald to lowest asset priority | `20260830T233734606Z-de8c9e4579f7` |

The final left-pane relationship is Ulvenwald at priority 0, full NotWL and its
patches above it, the NotWL texture cap above the vendor tree stack, and TDP's
small plugin/config mod above those. Priority 0 is deliberate: Ulvenwald's two
shared SMIM meshes lose to SMIM, preventing unrelated `milllogpile.nif` and
`tundradriftwood01.nif` changes. All assets actually selected by TDP use paths
that still resolve to the intended tree providers.

After LOOT, `Ulvenwald.esp` is disabled at discoverable plugin priority 35,
`Nature of the Wild Lands.esp` is enabled at 36, and
`Tree_Diversity_Project.esp` is enabled at 145. The deliberate-disabled state
is stored in `records/installed-mods.json`, so ledger verification and future
sorts treat it as policy rather than an error.

## Static record and asset proof

`Tree_Diversity_Project.esp` is already ESL-flagged. It has five vanilla/DLC
masters and 515 new records: 27 `STAT` and 488 `TREE`. It contains zero
overrides, placed references, cells, worldspaces, navmeshes, scripts, quests, or
deleted records. It is therefore a model library, not a second placement mod.

The selected BOS INI has 14 active swap lines targeting 13 unique TDP records:
three sycamores, two ash, one swamp tree, two mother-oak variants, four pines,
and one willow used by two NotWL sources. Every target EDID exists in the TDP
plugin. Provider resolution after the final left-pane ordering is:

- 12 selected models from Ulvenwald;
- 1 selected willow model from NotWL;
- 39 unique referenced DDS paths, 33 from Ulvenwald and 6 from NotWL;
- zero missing selected models and zero missing referenced textures.

A full enabled loose-file scan covered 37,918 files and 2,083 shared paths. The
tree stack adds no order-sensitive code/config collision. After lowering
Ulvenwald, the only Ulvenwald collision family is two meshes intentionally won
by SMIM. The NotWL texture-cap overlay remains the intended one-texture winner.

## Verification

- LOOT exit 0; all 201 previously active plugins restored.
- MO2Headless audit: `errors: []`.
- Ledger: 198 mods, 284 discoverable plugins, 0 problems.
- Master/order audit: 201 active plugins, `CLEAN`.
- `Ulvenwald.esp`: discovered and disabled.
- `Tree_Diversity_Project.esp`: discovered and enabled.
- Nexus curator: 137 active Nexus IDs, 137 Keep decisions, zero inactive Keeps
  and zero active pages missing Keep. This also protects Wigfrid09 and
  knightradiant2 from Excluded status without moving either review cursor.
- No game, MO2 GUI, CK, visible tool, or popup was launched.

The physical game `Data` tree retained the same 237-file count. Its aggregate
size changed by 214 bytes during the headless-tool pass; no mod payload was
copied there, and the durable installation transactions target only the MO2
instance. `Data/Engine.log` is the sole volatile log in that directory and is
excluded from publication and mod-payload accounting.

## Remaining foreground acceptance and rollback

Issue #29 remains open for a user-owned disposable/new-game route through
Falkreath, Riften, Morthal, Whiterun tundra, Bruma, Tundra Homestead, Lux Via,
Grand Solitude, and Solitude Docks. Measure average/1% low frame time and VRAM;
inspect wind, alpha/shadow artifacts, clipping, nav routes, and near-to-LOD
transitions. Final TexGen/DynDOLOD stays deferred until grass and exterior
worldspace decisions are frozen.

Rollback is independent and transaction-backed: disable TDP to remove only the
swaps; disable the Ulvenwald asset mod after TDP is off; keep full NotWL and its
existing patch family. Do not enable `Ulvenwald.esp` as a rollback step because
that would introduce a second placement authority and require a different patch
ecosystem.
