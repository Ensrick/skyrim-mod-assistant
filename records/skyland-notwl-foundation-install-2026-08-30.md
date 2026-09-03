# Skyland AIO + full Nature of the Wild Lands foundation install

Date: 2026-08-30
Profile: MO2 `Default`
Result: **installed, enabled, sorted, and statically verified**

## User decision implemented

- Skyland AIO is the broad architecture/landscape base.
- Full Nature of the Wild Lands is the tree overhaul.
- Nordic Cut is rejected from this stack and is not installed, enabled, Keep,
  a plugin master, or a selected patch path.
- Nature of Mild Lands is not authorized or installed.
- Vanaheimr, grass, Skyland LODs, Skyland complex parallax, Bits and Bobs, and
  all other visual candidates were outside this transaction.

All work used headless MO2. No visible MO2/game UI or Skyrim launch occurred,
and nothing was copied into physical game `Data`.

## Exact archives and transactions

| Installed mod | Nexus/version/file | Archive SHA-256 | Transaction |
|---|---|---|---|
| Skyland AIO 1K | 34179 / 4.32 / `443516` | `490F02EC34487FA9CFFD76E9CCFB69A2C17AD5207A2416CC6B1AAD027D15D734` | `20260830T212020229Z-7f65325a83d6` |
| Nature of the Wild Lands | 63604 / 3.14 / `661793` | `86B83A9A3B26D5A54DBB3EA40C4E638B18E7BE4BA47F880FEA6779ECB011054A` | `20260830T212334766Z-a04d527c7c35` |
| NotWL active-profile patches | 63604 / 3.10 / `613478` | `F9D60425DDF14C73D353E6B47BC676573DF4088C4F6AA2D28D04FA159B157880` | `20260830T212423153Z-3df90b4f4b11` |
| Grand Solitude Patch Collection | 157450 / 1.5 / `797296` | `FE58C5ACA1025688AE74BA54DF312135EE8715792AC3FD49B6A3FEBFC0E64233` | `20260830T212433508Z-056f5c588b19` |
| NotWL – Solitude Docks Patch | 102443 / 1 / `433438` | `6BFB0D45E3481D100F5BEBFB2C02C75B6D322F2FC9266BC59E08F7D48CE85A29` | `20260830T212515599Z-583f2ea6fb87` |
| Ensrick NotWL Texture Cap | local / 2026-08-30 | `C86C89277B4DFADB7FF62451CB0B953007D956208B8BDEE2295154D44D118D2E` | `20260830T212604894Z-45c3cdc85532` |

The NotWL archive contains malformed empty-name entries that Windows `tar`
rejects. Its already-audited exact extraction was mapped into a clean selected
staging tree, then installed with MO2Headless `mod-stage`. Selected vendor
files were copied byte-for-byte; the installed NotWL vendor folder was not
edited. The policy texture is a separate later overlay.

## Exact FOMOD choices

Durable plans:

- `records/fomod-plans/34179-skyland-aio-1k-4.32.json`
- `records/fomod-plans/63604-nature-of-the-wild-lands-3.14.json`
- `records/fomod-plans/63604-nature-of-the-wild-lands-active-patches-3.10.json`
- `records/fomod-plans/157450-grand-solitude-patches.json`

Skyland selects full landscapes, Blended Roads compatibility, its SMIM patch,
grey vanilla mountains, grey farmhouse/town textures, and broad vanilla/DLC
city, architecture, fort, ruin, dungeon, ship, shack, tent, and window
coverage. It omits dirt roads, road signs, lit signs, sign addons, lanterns,
water colour/textures, night sky, and pre-generated LOD.

NotWL selects the full main plugin/assets, shipped DynDOLOD rules and hybrid
LOD meshes, and the ENB Light nirnroot mesh. It omits autumn textures, Seasons,
tree animation, and PBR. It uses the ordinary main textures and full placements,
not Nordic Cut or Mild Lands.

## Patch and master audit

Only patches whose exact masters are active were selected:

| Plugin | Exact functional scope |
|---|---|
| `Nature of the Wild Lands - Bruma.esp` | Bruma tree/grass/TXST/placed/CELL/WRLD integration; 30 records. |
| `Nature of the Wild Lands - CC Tundra Homestead.esp` | Skyrim, Update, Tundra Homestead, NotWL; 25 records. |
| `Nature of the Wild Lands - CuttingRoomFloor.esp` | Skyrim, Update, NotWL, CRF; 23 records. |
| `Nature of the Wild Lands - Lux Via.esp` | Skyrim, Lux Via, NotWL; 12 records. |
| `Grand Solitude - Nature of the Wild Lands patch.esp` | Skyrim, Update, USSEP, NotWL, Grand Solitude; 28 records. |
| `Shadow's NotWL - Solitude Docks Patch.esp` | Skyrim, Update, NotWL; 27 records. |

The Docks patch is the normal full-placement main, not its aesthetic/performance
lite alternative. All 19 NotWL-owned FormIDs it targets still exist in 3.14.
The active Snazzy Solitude modules are interior/separated-house layers, so no
named Snazzy tree patch applies. Water for ENB has no tree-placement plugin
requirement. Beyond Reach and Wyrmstooth do not share these Tamriel placement
records. No Nordic Cut plugin or Nordic-specific compatibility plugin was
installed.

LOOT places `Nature of the Wild Lands.esp` at active plugin position 36,
before Lux Orbis, Lux, Water for ENB, and the owned semantic outputs. Tree
placement patches win their narrow target records; later specialized plugins
retain CELL/WRLD lighting, water, and map semantics. The two post-sort WRLD
reversion candidates involving NotWL are desirable later winners: the existing
Bruma compatibility output restores the English world name over a Russian
string in the vendor Bruma patch, and Lux's 3DNPC patch restores the larger
Bloated Man's Grotto world bound.

## Loose-file and texture audit

The selected Skyland payload contains 1,845 DDS and 141 NIF files:

- 44 DDS at or below 512, 1,609 at or below 1K, 182 at or below 2K, and
  10 at or below 4K; none exceeds 4096;
- 1,026 BC7, 675 BC1, 143 BC3, and one uncompressed map;
- eight world-space maps at 256 or larger have only one mip level; their
  runtime/permission follow-up is issue #120. Vendor files were not altered.

The NotWL vendor payload contains 413 DDS and 1,082 NIF files:

- 18 DDS at or below 512, 125 at or below 1K, 208 at or below 2K, 61 at or
  below 4K, and one 8192-square map;
- 392 BC7, 12 BC1, and 9 BC3; every map has a mip chain;
- `textures/true forest/log/log01.dds` is the sole policy violation:
  8192×8192 BC7, 14 mips, 89,478,660 bytes.

The local-only cap overlay converts that one map to 4096×4096 BC7, 13 mips,
22,369,796 bytes with:

`texconv -w 4096 -h 4096 -f BC7_UNORM -m 0 -y -nologo`

Two clean generations were byte-identical at SHA-256
`C86C89277B4DFADB7FF62451CB0B953007D956208B8BDEE2295154D44D118D2E`.
Issue #119 tracks the mandatory downscale record and permissions boundary.

Post-install loose-file inventory found 35,254 active files, 1,890 collisions,
and no new critical collision:

- Skyland wins 74 DDS and 15 NIF intended overlaps with SMIM;
- Water for ENB remains the only active provider of
  `textures/water/defaultwater.dds` and `textures/water/riverflow.dds`;
- no selected Skyland sign option overwrites Skyking Signs/Unique Signs;
- Lux Orbis wins its Solitude bridge mesh and Lux wins its three Solitude
  window-glow paths;
- NotWL's only loose collision is `log01.dds`, correctly won by the cap
  overlay.

## Verification and physical-Data proof

- LOOT sort: exit 0; 198 previously active plugins restored.
- Ledger verification: 185 mods at the visual-foundation checkpoint, 280
  discoverable plugins, 0 problems.
- `audit/verify_order.py`: 198 active plugins, `CLEAN`.
- MO2Headless `audit --profile Default`: `errors: []`.
- Full record inventory: 198 plugins parsed, 0 failures.
- NotWL-related winning records after sort: base and exact placement patches
  retain their intended reference changes; later Lux/Water/owned semantic
  layers retain functional headers. No additional owned ESP-FE was required.
- Physical `Data` before and after: 236 files, 20,732,350,348 bytes, exact
  sorted path/size/mtime-ns manifest SHA-256
  `AEF6D486A20E539004FA18E3975DB5C42898A94EACBFCC63044D1F5E75A58338`.
  It is unchanged.

## Curation, issues, and rollback

Live curator reconciliation completed through the guarded relay:

- Skyland AIO 34179: Keep;
- Nature of the Wild Lands 63604: Keep;
- NotWL – Solitude Docks Patch 102443: Keep;
- Nordic Cut 161936: Unreviewed/no decision;
- Nature of Mild Lands 112765: Unreviewed/no decision.

Keeping the installed mods protects their authors from Excluded status without
moving either review cursor. Base-decision issue #88 is closed. Tree runtime
acceptance remains on #29. The NotWL texture cap is #119, the eight Skyland
no-mip maps are #120, and systemic texture-cap work remains on #64/#101.

Rollback is profile-local and does not touch game `Data`: disable the three
NotWL patch mods, the texture-cap overlay, NotWL, and Skyland in reverse
priority order, then restore the prior `plugins.txt`/order transaction
snapshot. Do not delete vendor downloads or copy their payloads into `Data`.
