# Texture resolution policy

Approved 2026-08-26 for the Historical-Mythic Skyrim build.

## Governing rule

Match the resolution of the asset being replaced by default. A replacement may
increase by no more than one conventional resolution step when the additional
detail is real, visible at a normal viewing distance, and proportionate to the
asset's UV coverage. No texture dimension may exceed 4096 pixels.

One conventional step doubles each relevant dimension while preserving aspect
ratio: 256 to 512, 512 to 1024, 1024 to 2048, or 2048 to 4096. Because doubling
both dimensions quadruples pixel count, a permitted step is a ceiling rather
than an automatic preference.

## Mandatory limits

- A texture dedicated to a small clutter object is capped at 1024 pixels on
  either axis, even when a larger download is available.
- Every DDS image is capped at 4096 pixels on either axis. This includes color,
  normal, material, mask, glow, cubemap-face, interface, and generated texture
  assets.
- Rectangular textures retain their aspect ratio. A 2048 by 4096 atlas is not
  equivalent in pixel count or memory cost to a 4096 by 4096 image, although
  both are often marketed as "4K."
- Companion maps are evaluated independently. A low-resolution mask does not
  become 4K merely because the color map is 4K, and a normal or material map
  should not exceed its useful source detail without recorded evidence.
- Resolution alone is not evidence of quality. Pure resampling, including an
  AI upscale without recovered or newly authored detail, does not justify a
  step upward.

## Interpretation

"Source" means the winning asset at the same virtual path before the proposed
replacement: normally Bethesda/Creation Club data, or the required upstream
mod when evaluating an add-on. We compare width and height from the DDS header,
not the file name or download-page label.

When a mod introduces a genuinely new texture path, use the closest shipped or
already-approved analogue with comparable screen coverage, UV layout, and use.
The resolution selected by a new asset's author is evidence to inspect, not an
automatic baseline that bypasses these limits.

A shared atlas is classified by everything represented in its UV space rather
than by the physical size of one constituent object. Tiling architecture and
landscape materials are judged by texel density and repeat scale, not by the
total size of the wall or terrain on which they appear.

Small clutter means a dedicated asset for an ordinarily minor, non-hero object
with a small normal-gameplay screen footprint. First-person equipment,
readable surfaces, and atlases shared by many objects are not automatically
small clutter, but they remain subject to the source-plus-one-step and 4096
limits.

## Review record

For every accepted upward step, record:

1. source and proposed dimensions for each affected map;
2. whether the texture is dedicated, shared, tiled, or an atlas;
3. the normal closest viewing case that exposes additional detail;
4. compression format and approximate mip-chain VRAM cost;
5. why the source-resolution option was insufficient.

When evidence is inconclusive, select the source-resolution option. Downscale a
download locally only when its permissions allow modification; otherwise choose
an author-provided compliant file or omit the asset. Redistribution remains
subject to the permissions ledger regardless of whether a private downscale is
technically possible.
