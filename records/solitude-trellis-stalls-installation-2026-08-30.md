# Solitude, trellis, stalls, and owned-patch installation

Date: 2026-08-30  
Profile: MO2 `Default` / Skyrim SE 1.7.99  
Issues: [#47](https://github.com/Ensrick/skyrim-mod-assistant/issues/47), [#71](https://github.com/Ensrick/skyrim-mod-assistant/issues/71)

## Outcome

The approved Whiterun trellis, Rally market stalls, Grand Solitude, Solitude
Docks, separated Snazzy Solitude interiors, SFCO3 furniture layer, and exact
active-profile official patches are installed and enabled. Two owned
compatibility patches are installed as separate MO2 mods. No game was launched,
no visible program was opened, and the real game `Data` tree remained byte- and
file-count identical to the pre-install baseline (236 files,
20,732,350,348 bytes; latest write 2026-08-27 19:54:03Z).

## Exact vendor inputs

| MO2 mod | Nexus/file | Version | SHA-256 | Transaction |
|---|---:|---:|---|---|
| Whiterun Simple 3D Wooden Trellis - AIO | 178881/752331 | 1 | `bc707c3834fa3efbe5de5af3956c8a43cf16b9189c6ee9608375c66255ece59e` | `20260830T161307671Z-ead1abf659a3` |
| Rally's Market Stalls Animated - 2K | 81282/466020 | 1.3 | `9a1ca93b63885fa0a20e83a373e9306d00e23bcd92f35ab6079e3636369d1294` | `20260830T161400941Z-b380b3f853e6` |
| Rally's Market Stalls Animated - Hotfix | 81282/632767 | 1.3 | `8d95dc9ce55f1d2e2efdfa2aebaa4586a881984bdc2ac531704d2b489483383c` | `20260830T161417341Z-0e53dd8016a7` |
| Grand Solitude | 157506/796423 | 1.3.1 | `6dd495804fae532727571b0b47e87c675e2b6b57d86d6248cbb74cbf43fe7eee` | `20260830T161425126Z-5d6db5fa54b2` |
| Solitude Docks Updated | 33777/511162 | 3.2c | `22b955384335cb253625075b88865eb0e62f5404d26da48eb3d0a581c7b21581` | `20260830T161449894Z-ec7d87472bd6` |
| Grand Solitude Patch Collection | 157450/797296 | 1.5 | `fe58c5aca1025688ae74ba54df312135ee8715792ac3fd49b6a3febfc0e64233` | `20260830T161528235Z-a8f5ecdd379b` |
| Snazzy Location Resources | 147670/785915 | 2.40 | `a55505844ec6d439f6c89149ded890f520875a77144a58f108d2d7717489ac74` | `20260830T161540780Z-2d6b86ae2c8d` |
| Snazzy Solitude - Separated Houses | 147618/760311 | 2.3 | `8d09b5e7bada85424b01ec19e407381b7112fec1e94a426f8acf5b1970fc6470` | `20260830T161644824Z-e98da6c18edf` |
| Snazzy Interiors patches | 91604/786655 | 2.8 | `d1cda0e5f3426cdcd68b161ec922c1a3b75a6576558bdb5319552d9ae3dc5889` | `20260830T161655745Z-38df2d490838` |
| SFCO3 - BOS | 113045/783076 | 3.50 | `50bffcdbfc292080a2eef47f88ffc3840333b3d8017cab6c019a5bf84e2c5de3` | `20260830T161707126Z-5b10bd003d4d` |
| SFCO3 patches | 114482/797290 | 1.22 | `c88db8fb91b8d5209601ef43bb502f3b823fbd29e4f65d547dcd201f152d0e32` | `20260830T161755498Z-1e97e8703423` |
| Lux Patch Hub | 113002/695703 | 7.1 | `90a71f107383b46eb9a7d1927037e96046de6a5f2d110af96c147e0729490fc4` | `20260830T161824749Z-a18abc89d632` |
| Lux - Solitude Docks | 113002/742497 | 7.1 | `543f35bc3943247d54a9eba2cea3a9ad88304d2508c2cc868d6445db847bbf4e` | `20260830T161851743Z-16e5a9c0468d` |
| Lux Orbis patch hub | 114169/695720 | 4.7 | `48bc06968b2cdd8e3505ce0d080136a623c2d5c5c14183b50230cb8d71a487cb` | `20260830T161905627Z-66ba4441a1dd` |
| Lux Orbis - Grand Solitude | 114169/796261 | 4.6 | `351aff3ee64679f258541bfd602456a39c7d987c54fcc069957d443625ccabec` | `20260830T161923095Z-6c65930f0d88` |
| Lux Orbis - Solitude Docks Updated | 114169/742495 | 4.7 | `d271c5a094938c30204972868d00d50ef94e7a8c4dacab04bc62459eec9affdb` | `20260830T161931116Z-8d3c1f4fb736` |

Deterministic FOMOD plans are stored under `records/fomod-plans`. Rally uses
2K dark wood, 3D trellis, and the animated BOS add-on. Grand uses the main
files and SMIM rotor. Snazzy uses its shared resources and four separated house
plugins. SFCO3 uses required resources, default/desaturated assets, and Addons.

The Grand patch collection includes current applicable CC, 3DNPC, CRF, Lux Via,
and official Grand+Docks terrain patches. The Snazzy collection includes the
applicable Lux, USSEP, Gray Cowl, and Fishing patches. SFCO3 includes current
Grand, Docks, separated-Snazzy, CRF, 3DNPC, Gray Cowl, Vigilant, and Wyrmstooth
configs. Lux/Lux Orbis include the exact active-profile Grand, Docks, CRF,
3DNPC, and Wyrmstooth patches. AI Overhaul is absent, so no AI patch was added.
The known payload-mismatched Lux Orbis file 796263 was explicitly omitted.

## Owned outputs

- `Ensrick - General Compatibility Patch`, priority 187 at install, plugin
  SHA-256 `F9E93B4983D8326BA898622DA93AAAB7A8A486C2164FF4223C18097E72A5B6ED`;
  transactions `20260830T164449040Z-ec5e6b03c204` and
  `20260830T164449400Z-8c6611f1a4bc`. It contains exactly 12 WRLD and 2 CELL
  overrides. Two current-profile generations were byte-identical; 374 selected
  fields and 61 links were checked with zero unresolved links; Spriggit's
  checked round trip passed.
- `Ensrick - CRF Semantic Patch`, priority 188 at install, plugin SHA-256
  `D3EA7952099EF73AC30B1C9BF4094A3886065FC781568FAA1F05AA3D0F8A257C`;
  transactions `20260830T164449478Z-b0e04f73b959` and
  `20260830T164449919Z-97bfa0c64a42`. It contains five semantic overrides and
  one required DIAL parent anchor, no new forms, and 1,601 checked links with
  zero unresolved. Two generations were byte-identical and the Spriggit tree
  round trip matched exactly.

The CRF patch restores Dark Chasm XLCN, Whiterun's three CRF ACPR entries and
ACEC block, Herebane/Kilkreath add/removals, Dushnikh's removal, and Tasius's
`GetDead` condition while preserving Skyrim Unbound's global. The genuinely
ambiguous Hall of the Dead XLCN (`0DD216`) is deliberately omitted and Lux
remains its winner.

## Final validation and rollback

Final LOOT places the general and CRF patches at lines 191 and 192, after every
reviewed input. The exact six pre-existing disabled plugins remained disabled.
MO2 master/link audit returned zero errors; order audit reports 186 active and
272 discoverable plugins, clean; ledger reports 173 vendor mods and zero
problems; the full conflict scan parsed all 186 active plugins, 27,119 shared
chains, and zero failures. Each owned target is confirmed to end in its owned
patch; Hall of the Dead still ends in Lux by design.

Every vendor install is individually recoverable through its transaction ID.
The two owned mods can be disabled or rolled back independently without
touching vendor directories. Vendor archives are treated as non-redistributable
inputs unless their page grants explicit permission; a future public installer
must download them from Nexus rather than embed them. The CRF output remains
private until CRF compatibility-patch permission is documented.

Nexus Keep reconciliation queued all 124 active Nexus pages as Keep and clears
five inactive pages back to unreviewed; the guarded browser relay applies those
decisions when the extension is available.
