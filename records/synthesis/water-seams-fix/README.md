# Water Seams Fix - Water for ENB

This is the reproducible headless configuration for the generated
`Water Seams Fix.esp` conflict-resolution plugin.

- Source: `https://github.com/Oliphantaupe/WaterSeamsFix-WaterForENB`
- Source commit: `0e1b2cd736ba81e85a562177b3dec91cae89e116`
- License: MIT
- Patcher build: local Release build from source, targeting .NET 8
- Main water plugin: `Water for ENB (Shades of Skyrim).esp`
- Base ESM: disabled because the Community Shaders Natural Shades selection
  does not install `Water for ENB.esm`
- Output: `Water Seams Fix.esp`

Run the patcher through MO2's headless VFS so it reads the active `Default`
profile and writes only into the temporary `Water for ENB - Generated Conflict
Patch` target. If the output contains records, enable it after every Water for
ENB plugin and other cell/worldspace conflict winner. Regenerate it whenever the
load order changes. If the result is empty, leave the generated target disabled.

## First validation run

The 2026-08-27 run completed without a window or error and reported zero cells
and zero worldspaces requiring repair after the explicit Water for ENB ordering
was applied. Its 42-byte empty output is parked and disabled; the configuration
is retained so this check can be repeated after future load-order changes.
