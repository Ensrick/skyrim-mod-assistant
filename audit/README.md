# Asset audit

Inspects what a mod actually ships and reports findings. It does not decide
anything: the output is evidence for a keep/skip call, not the call itself.

```
py -3 audit/inspect_mod.py "6369:Cloaks of Skyrim"
py -3 audit/inspect_mod.py "5795:RUSTIC CLUTTER:2K$"     # third field picks a file variant
```

The findings sheet has four parts: what the archive contains, what modern
features it supports, warning signs with the offending file named, and the
community addons that fill the gaps it leaves.

## Files

| file | job |
|---|---|
| `modasset.py` | download, extract, read BSAs (incl. SSE's LZ4-framed entries), parse DDS and NIF headers |
| `esp.py` | plugin parser: ARMO/ARMA equip slots, item classes, masters, ESL flag |
| `vanilla_index.py` | index the game's own BSAs; run once, produces `vanilla_index.json` |
| `inspect_mod.py` | the findings sheet |
| `calibrate_detail.py` | rebuilds the detail-index controls used below |

`vanilla_index.py` must run before upscale detection works. It reads the game
install read-only and takes about 6 minutes for ~180k asset paths.

## What it detects

**Textures** - upscaled vanilla passed off as new work, missing companion
normal maps, normals stored as BC1, flat or diffuse-embossed normals, solid
gloss alpha, absent mipmaps, uncompressed textures, JPEG blocking, resolution
below the vanilla asset being replaced, diffuse/normal resolution mismatch.

**Meshes** - unconverted Oldrim meshes (NIF user version other than 100, using
`NiTriShape` instead of `BSTriShape`), parallax shader flags with no `_p`
texture shipped, triangle budget.

Triangle counts cover static meshes only. Skinned meshes keep geometry in
`NiSkinPartition`, which this does not parse, so they are reported as unread
rather than counted as zero.

**Apparel** - equip slot and item class come from the plugin's ARMO records, so
findings apply only to items where loose cloth is actually visible. A ring is
not asked about physics. For those that qualify, the mesh's bone list decides
what is reported:

| mesh is weighted to | reported as |
|---|---|
| bones outside the vanilla skeleton, no SMP config | rig present but inert without a physics patch |
| the vanilla `Skirt*Bone` chain, no SMP config | canned skirt animation only, no simulation |
| no cloth bones at all | rigid geometry welded to the body |

The vanilla bone set is read from the game's own
`actors/character/character assets/skeleton.nif`, because `SkirtBBone01-03`
look custom but are stock. Absence of a PBR material set is a note, not a
warning, since it only matters under TruePBR.

Contested biped slots (45, 46, 47) are reported too, since two mods on slot 46
cannot be worn together no matter how good either one is.

**Packaging** - `.psd`, `Thumbs.db`, `__MACOSX` and similar junk.

## Calibration

Thresholds are measured against controls, not asserted. The controls are built
by taking vanilla textures and degrading them in known ways
(`calibrate_detail.py`):

| control | detail index |
|---|---|
| hand-authored 2K (RUSTIC Clutter) | 7.33 |
| vanilla, native size | 2.71 |
| vanilla upscaled 2x then sharpened | 1.53 |
| vanilla upscaled 2x | 0.61 |
| vanilla upscaled 4x | 0.25 |

The detail index alone cannot separate a sharpened upscale from real vanilla,
so upscale detection uses correlation against the vanilla asset instead:

| case | correlation to vanilla |
|---|---|
| plain upscale | 0.995+ |
| upscale + sharpen | 0.96 min |
| genuine hand-authored retexture | 0.91 max |

Hence the 0.95 threshold, with roughly 0.05 of margin either side.

An edge-ringing detector for the sharpening case was written and **discarded**:
native vanilla textures ring as hard as sharpened upscales (9.53 vs 12.40), so
it separated nothing. Any metric that fails to separate the controls does not
belong in the report.

## Load-order safety

`verify_order.py` reads each active plugin's TES4 master list and fails when a
master has no provider, is present but inactive, or loads too late. Only the
five official base masters and plugins explicitly listed in `Skyrim.ccc` are
implicit; an arbitrary plugin sitting loose in the physical `Data` directory
is not treated as active. Synthetic regression tests cover those activation
rules and run in the repository's required `validate` check.
