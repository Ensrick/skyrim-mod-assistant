# Bruma iron helmet floats after decapitation — #242

## Diagnosis

The human/elf Cyrodiil iron helmet has a concrete dismember-partition mismatch.
The minimal modder-native repair is to change `INV.00` →
`BSDismemberSkinInstance` → partition 0 → Body Part from **31 to 131** in its
NIF, leaving the equipment records alone. This is a mesh metadata repair, not
an equipment-slot migration or an animation replacement.

The September 6 audit inspected all 348 active plugins. The Bruma base armor
`30001F:BSHeartland.esm` (`CYRArmorIronHelmet`) and 24 enchanted variants link
to the same three ArmorAddons. No active plugin overrides those declarations.

| ArmorAddon | Worn mesh under `meshes/bscyrodiil/armor/iron/` | Current partition | Action |
|---|---|---:|---|
| `083C16:BSHeartland.esm` human/elf, both sexes | `cyrironhelmet.nif` |31|131|
| `083C17:BSHeartland.esm` Khajiit, both sexes | `cyrironhelmet_khaj.nif` |131|None|
| `083C18:BSHeartland.esm` Argonian, both sexes | `cyrironhelmet_arg.nif` |131|None|

All three currently resolve to **Beyond Skyrim - Bruma / BSHeartland -
Textures.bsa**, despite that archive's name. There is no loose mesh winner.
The armor mask is 4098 (hair/circlet); human and Khajiit addon masks are 8194
(hair/ears), and the Argonian mask is 2 (hair). These match vanilla iron armor
records. All six vanilla iron helmet meshes use partition131. Bruma's own two
beast variants also use131, making them particularly close controls.

The human mesh has one shape, `INV.00`, with one dismember partition, flags257,
and the single bone `NPC Head [Head]`. The recipe preserves all of these except
the Body Part enum. It does not modify the ground/inventory mesh.

This is strong static evidence for the reported symptom, not a claim that the
decapitation has already been reproduced and passed in-game.

## Original user-local recipe

`repair_bruma_iron_helmet.ps1` reads the winning mesh through the existing
HousecarlCore asset resolver. It accepts only this exact source SHA256:

`892AED580ACF254840E026CC0BA1919D29594C65E3448D69EE9290F16AC4968F`

In that 99,651-byte asset, block2 is a 28-byte BSDismemberSkinInstance beginning
at560. The one bone count is at572, one partition count at580, flags257 at584,
and Body Part ushort31 at586. The recipe changes **only byte586** to131; the
high byte remains zero. All other99,650 bytes are compared unchanged. Before
and after decoding with NifService independently confirms the requested enum
change and identical other exposed semantics. Exact byte equality outside the
field also protects geometry, weights, textures and opaque data the semantic
inspector does not expose.

Output mesh SHA256:
`AC0A5D396756ECCBC7577945E5DBFEDC74BD0F40A28A0D0DAEAD3376AD02CCD8`

```powershell
pwsh -NoProfile -File audit/repair_bruma_iron_helmet.ps1 `
  -Instance '<MO2 instance>' -GameData '<Skyrim Special Edition/Data>' `
  -ToolBin '<houseCARL>/src/housecarl-generator/bin/Release/net9.0' `
  -Output '<new empty directory outside the instance/game/tool directories>'
```

Run from the repository root with PowerShell7 capable of loading .NET9.
HouseCARL source: [Ensrick/houseCARL](https://github.com/Ensrick/houseCARL),
commit `6386941e6ebaf84b5bf10decfa60c99af5847e44`; build its generator project
with .NET9 (`dotnet build src/housecarl-generator/housecarl-generator.csproj -c Release`).
The project uses Nifly1.1.0. Actual parser binary hashes are included in the
local output receipt. No source tool was modified for this repair.

The command refuses a different input hash, an unresolved winner, unexpected
mesh semantics, any unrelated byte/semantic change, an existing output, or an
output inside live/tool directories. It resolves reparse-path components before
the output boundary check. It cannot be rerun over its own already-winning
patched mesh: disable that owned overlay for a reviewed rebuild, or retain the
prior valid package. Do not weaken the input hash to accommodate an unknown
update.

Two independent builds produced the same user-local ZIP SHA256:
`9D2E60BDA215CD25FCBE5708660BE68F37107B8ECA0678046EF44404AC224E91`.
PowerShell AST parsing passed. Live-instance output, game-Data output and
existing-output negative tests all refused before writing.

## Rights and verification boundary

The recipe and report are original MIT source. The generated NIF remains a
modified third-party asset: **the generated ZIP is user-local and must not be
uploaded or included as vendor bytes in the public modlist** without permission.
The collection can distribute this original recipe and have each user generate
the overlay from their own required Bruma download. Vendor archives remain
untouched; the overlay contains one NIF and its owned receipt, no ESP or DLL.

After a fresh game process, test a disposable humanoid NPC wearing the ordinary
Cyrodiil iron helmet, then an enchanted version. Repeat for male and female
humans/elves. A decapitation should not leave the helmet at the old head position.
Verify ordinary equip/render behavior, inventory/ground appearance, and no change
to Khajiit/Argonian variants. Previously instantiated dead actor geometry is not
the appropriate test of a replaced disk asset. Gameplay acceptance remains open
on [#242](https://github.com/Ensrick/skyrim-mod-assistant/issues/242).

## Sources and tooling observation

- Vanilla `Skyrim.esm` iron helmet records and six original worn NIFs were the
  initial reference, followed by Bruma's matching beast-race variants.
- The [Niftools format specification](https://raw.githubusercontent.com/niftools/nifxml/develop/nif.xml)
  defines separate31 and131 enum values and the ushort Body Part field;131 is
  explicitly a Skyrim hair-slot helmet/hood partition. Its enum should not be
  mistaken for a131 equipment slot in an ESP.
- The [CK ArmorAddon page](https://ck.uesp.net/wiki/ArmorAddon) and Biped Object
  page were requested but returned403 in this environment. No claim of having
  read blocked content is made; installed vanilla and same-mod examples are the
  primary operational evidence.
- A modder's [published before/after account](https://forums.nexusmods.com/topic/13500212-floating-headwear-following-decapitation-help-requested/)
  documents the same symptom resolved by selecting the appropriate100-series
  dismember partition for another headwear model. This corroborates the mechanism,
  not a Bruma-specific upstream fix. No already-published Bruma iron helmet fix
  was verified in the search.

The existing NifService.Set writer correctly refused to emit output for this
particular file: normalization moved the BSDismember block from2 to4, while its
changed-block guard expected2. The guard was not weakened. The hash-pinned
single-byte recipe avoids normalization entirely and verifies stronger whole-file
preservation. That tool's block-index tracking is a separate maintenance finding,
not justification to bundle a new runtime dependency.
