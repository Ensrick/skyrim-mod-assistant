# User-local denomination asset rebuild

The derived NIF/DDS files are not public redistribution inputs. Build them
from the separately installed, pinned vendor assets with `rebuild.py`.

`recipe.py` is the unchanged historical transform whose SHA-256 is
`C85B16567AC9E120417E18FB29ACDA6F2775256CA6F0FD69775679102A0F2FE9`.
`inputs.json` pins the twelve vendor inputs and three tool executables; its
SHA-256 is
`54DEADDCDB88E49D4EB33FD2FFF7C963E6A895B6294407613992108381A8306A`.
`integration-receipt.json` records the 36 byte-identical golden outputs from
two isolated builds and remains bound to that historical recipe. The portable
driver supplies local paths and does not rewrite or repin any of those files.
The reviewed `rebuild.py` SHA-256 is
`84BEB276277D1C1068E7B1564525A41A0AD4D5A459AE5FDD6DE08142CEC4064B`.

Use a dedicated workspace outside the MO2 instance. Paths shown here are
examples; each executable must have the hash pinned in `inputs.json`.

```powershell
$common = @(
  '--instance-root', 'D:/Modding/MO2/SkyrimSE',
  '--profile', 'Default',
  '--repo-root', 'D:/src/skyrim-mod-assistant',
  '--workspace', 'D:/build/ensrick-currency-assets',
  '--nif-tool', 'D:/tools/nif-port-cli.exe',
  '--magick', 'C:/Program Files/ImageMagick/magick.exe',
  '--texconv', 'D:/tools/texconv.exe'
)
py -3 ./mods/currency-integration/assets/rebuild.py --verify-environment @common
py -3 ./mods/currency-integration/assets/rebuild.py --acquire-inputs @common
py -3 ./mods/currency-integration/assets/rebuild.py --build build-a @common
py -3 ./mods/currency-integration/assets/rebuild.py --build build-b @common
```

The acquire step reads only the current enabled MO2 providers, verifies exact
loose or BSA-member bytes, and writes an untracked private cache. It is
idempotent only when that cache is already exact. It does not use Nexus
credentials or download anything. Each build refuses an existing output and
must match all 36 hashes and sizes in the golden receipt; therefore the two
successful example builds are also byte-identical to one another.
