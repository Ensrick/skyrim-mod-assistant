# Ensrick Inigo Bloodchill Landscape Forward

Builds `Ensrick Inigo Bloodchill Landscape Forward.esp`: an ESL-flagged,
4-record, 0-new-form patch that restores Dawnguard's landscape and navmesh in
cell `008FC4` after `Inigo.esp` reverts them, which is what buries the Creation
Club Bloodchill Cavern entrance.

Full evidence, measurements and the trade-off:
`records/inigo-bloodchill-landscape-forward-2026-09-06.md`. Why it exists at
all rather than the Nexus patch: `docs/EXCLUDED_AUTHORS.md`.

## Build

```
py -3 mods/inigo-bloodchill-landscape/build.py [--out <mod folder>]
```

Standard library only, no .NET, no generator project - per
`docs/CK_FIRST_DOCTRINE.md`, the change is a record copy, so the tool is a
record copier. It reads `Dawnguard.esm`, `Inigo.esp` and the current WRLD
Tamriel winner straight from disk and writes the plugin; two runs are
byte-identical (`287c43a7...4e7ca`, 20,300 bytes).

Verify after building:

```
skyrim-record-cli plugin-info "<out>/Ensrick Inigo Bloodchill Landscape Forward.esp"
Spriggit.CLI.exe serialize --InputPath "<esp>" --OutputPath <dir> \
  --GameRelease SkyrimSE --PackageName Spriggit.Yaml.Skyrim --PackageVersion 0.41.0 \
  --Check --ErrorOnUnknown
```

## Load order

Requires `Inigo.esp` (declared master, so the engine enforces the order) and
`Dawnguard.esm`. It does **not** require `ccEEJSSE005-Cave.esm`: without the
Creation Club home the patch simply restores Bethesda's terrain, which is
correct either way.

Re-run the build if `Ensrick General Compatibility Patch.esp` (#47) is
regenerated - this plugin carries a byte copy of that patch's WRLD Tamriel
record so its structural parent stays a no-op wherever it sorts.

## Distribution

Distributable. The payload is one ESP holding four override records, each a
byte copy of a record already on disk (`Dawnguard.esm` for the landscape and
navmesh; the load order's own records for the two structural parents), plus a
single master-index remap. No assets, and no third-party author's authored
content.
