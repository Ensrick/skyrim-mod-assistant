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

**Meshes** - unconverted LE-format meshes, parallax shader flags with no `_p`
texture shipped, triangle budget.

**Apparel** - no physics data at all, or CBPC-only rather than HDT-SMP.
Absence of a PBR material set is reported as a note, not a warning, since it
only matters under TruePBR.

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
