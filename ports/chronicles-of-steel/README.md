# Private Chronicles of Steel equipment review

Read `docs/CHRONICLES_OF_STEEL_CONVERSION.md` before use. This is a private review
recipe, **not an installer, finished balance patch, or public port**. It preserves
source archives and cannot activate mods or launch Skyrim.

Requirements: Python 3.11+ with PyYAML 6.0.3, Spriggit 0.41.0, the project's
source-built `nif-port-cli`, `skyrim-record-cli`, BSArch, the exact Finale source
archive and the locally owned Skyrim SE base-game files. Tool paths are explicit;
no credential, API access, GUI, dependency installer or global configuration is
used by these scripts.

## User-side front end

`convert.py` accepts the original downloaded ZIP directly. It validates the exact
archive version, checks local tools, extracts only the four required source
files, and runs preparation plus independent verification. It refuses existing
outputs and game-directory overlap, never enables plugins, and never downloads
or redistributes source assets. `--check-only` performs a read-only preflight.

```powershell
py -3 convert.py --archive "Weapons of War-103289-Final-1591581196.zip" `
  --output "D:/ModConversions/TCOSS-review-001" --toolchain tools.local.json `
  --game-data "D:/SteamLibrary/steamapps/common/Skyrim Special Edition/Data"
```

The local JSON has a `tools` object with `spriggit`, `nifPortCli`,
`skyrimRecordCli`, and `bsarch`; each has a `path` and optional pinned `sha256`.
Relative tool paths resolve beside that JSON. The project's existing
`toolchain.json` works with an explicit `--bsarch <path>` override. Tool hashes
are recorded privately even when a supplied configuration does not pin them.
Use reviewed source-built tools; the script does not install its dependencies.

Allow 8 GiB of free scratch space. Failed runs retain their own outputs and logs
for diagnosis. The resulting `review/mod` is **not a finished modlist component**:
the three missing mip chains, balance, distribution, runtime appearance and
publication permissions remain explicit review gates. This is a portable
prototype entry point, not yet a packaged end-user installer or a general LE
converter. It supports Finale only; Lost LongSwords uses its separate recipe.

Extract the Finale ZIP to an isolated source directory. Supply that directory
(containing its three plugins and TCOSS.bsa) and a new output directory:

```powershell
python prepare-review.py --source <extracted-finale> --output <new-private-output> `
  --spriggit <Spriggit.CLI.exe> --nif-tool <nif-port-cli.exe> `
  --record-tool <skyrim-record-cli.exe> --bsarch <bsarch.exe> `
  --skyrim-master <game-data/Skyrim.esm>

python verify-review.py <new-private-output> --nif-tool <nif-port-cli.exe>
```

`prepare-review.py` checks the input plugin/BSA hashes, extracts the BSA itself,
serializes records strictly, follows equipment dependencies, remaps new forms
into the conventional ESL range, stages only the required asset files under a
private namespace, rebuilds the plugin and checks form links. Opaque Spriggit
byte arrays are preserved as strings, including their leading zeros. Both armor
weight endpoints are required when the source enables weight sliders.

`verify-review.py` separately checks the generated binary, its roundtrip, final
meshes and textures. It reports missing mip chains as open work. A structural
PASS is **not** readiness for installation or release.

Outputs contain vendor-derived data and remain private. They include the mod
payload, complete item inventory, source/roundtrip data and audit reports.
Failed runs deliberately retain their isolated output for diagnosis; do not
point a subsequent run at it. Source snapshots and intermediate copies may be
removed after inspection and reproducibility checks, with the original ZIP/BSA
retained. Do not copy test output into the live game or MO2 profile.
