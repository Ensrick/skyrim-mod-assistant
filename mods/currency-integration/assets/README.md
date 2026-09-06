# User-local denomination asset rebuild

The derived NIF/DDS files are not public redistribution inputs. Build them
from the separately installed, pinned vendor assets with `rebuild.py`.

The schema-2 input manifest covers seventeen non-Septim visual designs:

- Mede, Ulfric, Dram, Oshka, Ohzer, and Varken;
- Drakr Dragon, Moth, Owl, and Whale;
- Gibber Front and Back;
- Mala, Mallari, Nchuark, Sancar, and Bruma Ayleid Mala.

Septim already has three authored inventory meshes and is outside this derived
asset recipe. Every catalogued design produces Copper, Silver, and Gold NIFs.
Most designs use one authored diffuse slot, yielding one NIF and one DDS per
tier. Each Gibber mesh has two authored shapes with different diffuse slots;
both slots are transformed and remapped atomically as `Face0` and `Face10`.
This produces 51 design-tier NIFs and 57 DDS files, 108 files total.

M.I.N.T.'s unified Gibber form (`DE5027:Update.esm`) is an asset alias of the
authored Gibber Front mesh, not an eighteenth non-Septim source design. The
four Drakr NIFs remain separate issue/face designs even though they share an
authored diffuse. No design is silently collapsed onto a generic coin.

The active `C.O.I.N. - Beyond Skyrim Patch.esp` record for
`6028DC:BSAssets.esm` points to nonexistent `Meshes\COIN\Mala.nif`. The recipe
does not reproduce that broken override. Bruma is pinned to its actual authored
source member instead:

`BSAssets - Textures.bsa :: meshes\bscyrodiil\dungeons\ayleidruins\ayleidcoin01.nif`

`inputs.json` pins every logical model/diffuse path, loose or BSA provenance,
member and archive hash, source hash, NIF inspection, and DDS metadata. The
recipe preserves geometry with exact OBJ comparison, converts LE geometry
where required, replaces every catalogued diffuse binding, and preserves all
normal/mask/environment bindings. ImageMagick retains luminance detail while
applying the tier treatment; DirectXTex emits deterministic CPU BC7 output
with complete mip chains and no diffuse larger than 1024 pixels.

`integration-receipt.json` is accepted only after two isolated builds produce
all 108 files byte-identically and the original 0.3.0 36-file tier asset set
remains identical by path, size, and SHA-256. The receipt remains
`runtime-unverified`; it is static build evidence, not gameplay acceptance.

Use a dedicated workspace outside the MO2 instance and repository. Paths shown
here are examples; each executable must have the hash pinned in `inputs.json`.

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

The acquire step reads only current enabled MO2 providers, verifies exact
loose or BSA-member bytes, and writes an untracked private cache. It is
idempotent only when that cache is already exact. It does not use Nexus
credentials or download anything. Each build refuses an existing output and
must match every path, size, and hash in the golden receipt. Cathedral Assets
Optimizer is neither sufficient nor required for this recipe, and users
should not run it over the verified output.
