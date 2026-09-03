# Legacy of Ysgramor installation record

Installed into the MO2 `Default` profile on 2026-08-28 after Skyrim and the
MO2 GUI had exited. Installation, plugin activation, sorting, and audits were
performed through the headless controller without opening desktop windows.

## Selected stack

| Layer | Nexus/file | Version | SHA-256 |
|---|---:|---:|---|
| Legacy of Ysgramor, standard 2K archive | 109963 / 464173 | 1.0 | `B186E6D10F98915490C5B24F06A0196289C15EDBECCA70AF5FA98234F68FD8E8` |
| HIMBO Conversion | 110002 / 464314 | 1.0 | `9D3F10D3BB023B5DD552047E348EE451B19D75F46D36697B8D42E1B3C3BE67F6` |
| RMB SPIDified Core Framework | 63625 / 754890 | 6.3.0 | `59AA7240BC7CACB3C8E29D0FEE8F3B282730A2A054D35D0E9340628E7BE6960D` |
| RMB SPIDified - Legacy of Ysgramor | 140349 / 749746 | 1.2.3 | `80A4F36FF736036AC430D07D59DEE58E48246D94BB724DC1D9043DC185420723` |
| Xtudo RMB-compatible fixes | 111121 / 614646 | 1.9 file | `43070F1A38A92FE18C870068E6688026534204584C5E91B2A7134880F6D34F2B` |
| SkyPatcher AE | 106659 / 796107 | 7.0.3 | `195E5E8CF1EB7517E7D3C9EA581098EB5E5776441F7DBE20C256DC0F896DD38B` |
| SPID official source/payload reference | 36869 / 795621 | 7.3.3 | `B1A2F44F7A55062CF8999D5AE88FBEB4E7A985A371F9BE01A358E8870B24EE71` |

The optional Legacy HD archive was omitted. All 71 textures in the standard
archive are 2K or lower, complying with the list's performance texture policy.

## Deterministic installer choices

RMB Core selections:

- Core definitions and SkyPatcher support.
- Skip followers, following the author's recommendation.
- Skip unique outfits, following the author's recommendation.
- No jailer distribution and no special Galmar, Rikke, Tullius, or Ulfric
  exclusions.

Legacy SPID selections:

- Core.
- Named Companions distribution, Inner Circle only.
- Wuuthrad replacer ESP.
- Skyforge Steel model replacement through SkyPatcher.
- No broad faction distribution, no ESP Skyforge override, and no standalone
  Runic Steel weapons.

The named rules give Kodlak the Ebony set and give Skjor, Vilkas, Farkas, and
Aela the Steel set. Eorlund, Vignar, Brill, Athis, Ria, Njada, and Torvar remain
present as commented examples so their assignments can be reviewed manually.
The direct named rules are unaffected by RMB Core's generic follower exclusion.

SkyPatcher changes only the five vanilla Skyforge Steel weapon model paths, so
their vanilla or later balance records remain authoritative. The separate
Wuuthrad plugin replaces Wuuthrad, its fragments, its associated statics, and
the Shield of Ysgramor appearance. The HIMBO archive includes pre-generated
zeroed meshes and BodySlide sources; no BodySlide run is required for the
current body setup.

## Runtime dependencies

The installed SPID DLL was built locally from
`powerof3/Spell-Perk-Item-Distributor` 7.3.3 source on branch
`ensrick/skyrim-1.7.104`, commit `b580f77`. CommonLibSSE-NG was advanced to
6.7.1 and the SKSE plugin metadata explicitly permits runtime 1.7.104.0.

- DLL version: `7.3.3.104.0`
- DLL SHA-256: `D9CA36FDD3E2A44A624BABF53F19EF8FE62E420BD1F38118683A20E7CBD4850D`
- Build result: Release build succeeded; no upstream unit-test target exists.

The official SPID DLL and PDB were both replaced by the local build outputs;
the installed SPID mod therefore does not contain the Nexus binary. SPID's
source is MIT-licensed. SkyPatcher remains the official AE 7.0.3 binary and is
subject to its Nexus redistribution restrictions.

## Plugin and conflict validation

Winning plugins after all overrides:

- `RMB SPID - Core Definitions.esp`
- `NW_Companions_Replacer_Light.esp` from Xtudo's RMB-compatible fixes
- `RMB SPID - Legacy of Ysgramor.esp` from Xtudo's RMB-compatible fixes
- `RMB SPID - Legacy of Ysgramor - Wuuthrad.esp`

The Xtudo RMB file intentionally removes the two optional standalone records
`NW_ArmorShieldofYsgramor` and `NW_BladeOfYsgramor`; it preserves the selected
vanilla artifact replacer route. Its base plugin has the same record inventory
as RMB's base plugin while forwarding Xtudo's USSEP, Survival, sound, slot,
critical-damage, and race fixes.

The only loose-file conflicts with pre-existing enabled mods are
`textures/cubemaps/metalic_e.dds` and `textures/cubemaps/steel_e.dds` from Sons
of Skyrim. Both pairs are byte-identical. HIMBO intentionally overrides 22 male
armor meshes from the Legacy base layer. No other unexpected loose-file
collision was found.

LOOT 0.29.6 sorted the profile and placed the Core Definitions light master at
priority 15, the base plugin at 54, the distribution plugin at 55, and the
Wuuthrad plugin at 56. The current LootCLI output path removed every enabled
marker while writing the sorted list. This was detected before launch; the
exact 91-plugin pre-sort enabled set was recovered from MO2 transaction
`20260828T175112333Z-271b9269451a`, Wuuthrad was added, and MO2 applied the
92-plugin state atomically in transaction
`20260828T175422694Z-600d6b4b9d89`. Known disabled plugins remained disabled.
LootCLI must not write directly to `plugins.txt` again until marker preservation
is fixed.

Final checks:

- MO2 profile audit: no errors.
- Enabled managed plugins: 92.
- `plugins.txt` SHA-256: `7B2C1C2D261F958A5C43F5D37302B5540CF0D278AD4E4E22E817881FFCBF8776`.
- `loadorder.txt` SHA-256: `8BCB16CFF860D4EF28119910281587B7ACA064CA9BE9236902F7E39F93BB4ED8`.
- No in-game smoke test has yet been performed with this newly installed stack.

## Publication boundary

The public modpack may reproduce the selected options and reference the Nexus
mod/file identifiers. It must not bundle Legacy of Ysgramor, its HIMBO
conversion, either RMB archive, Xtudo's fixes, or the official SkyPatcher
binary. Exact permissions and local policies are recorded in
`records/restricted-mods.json`. The MIT-licensed SPID runtime port may be
published separately with its license and source attribution after in-game
verification.
