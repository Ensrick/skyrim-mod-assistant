# Private Chronicles of Steel equipment review

Read `docs/CHRONICLES_OF_STEEL_CONVERSION.md` before use. This is a private review
recipe, **not an installer, finished balance patch, or public port**. It preserves
source archives and cannot activate mods or launch Skyrim.

Requirements: Python 3.11+ with PyYAML 6.0.3, Spriggit 0.41.0, the project's
source-built `nif-port-cli`, `skyrim-record-cli`, BSArch, the exact Finale source
archive and the locally owned Skyrim SE base-game files. Tool paths are explicit;
no credential, API access, GUI, dependency installer or global configuration is
used by these scripts.

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
