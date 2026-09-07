# Texture resolution policy

Approved 2026-08-26 for the Historical-Mythic Skyrim build. Rebalanced
2026-09-06: the figures are ideals, 4096 is the only hard limit - see "Ideals,
and the one real limit" below, which governs where it and an older sentence
disagree.

## Governing rule

Match the resolution of the asset being replaced by default. A replacement
should not usually increase by more than one conventional resolution step, and
the case for a step is that the additional detail is real, visible at a normal
viewing distance, and proportionate to the asset's UV coverage. No texture
dimension may exceed 4096 pixels.

One conventional step doubles each relevant dimension while preserving aspect
ratio: 256 to 512, 512 to 1024, 1024 to 2048, or 2048 to 4096. Because doubling
both dimensions quadruples pixel count, a permitted step is a ceiling rather
than an automatic preference.

## Ideals, and the one real limit (user, 2026-09-06)

**User directive, verbatim:** *"treat the texture limits less as limits and more
as ideal. The lockpicking interface is pretty large so having high res
locksmithing is normal."*

Everything below except the 4096 ceiling is a **default to justify departing
from, not a gate that refuses**. The figures still say what to pick when nothing
argues otherwise, and the review record below still has to be written when a
build goes above them - the change is that a documented reason now settles it
instead of a cap overriding the reason.

**Screen coverage decides.** The trigger case: `locksmallpiece_snow.dds` in
Security Overhaul SKSE - Lock Variations is 512x2048 and lives under
`textures/interface/objects/lockpicking/`. The lockpicking view fills much of
the screen, so the object is not clutter at the moment it is looked at, and the
1024 figure never applied to it in spirit. Ask where the asset is actually seen
from before applying a number to it.

## Limits

- **4096 pixels on either axis is a hard ceiling** and stays one.
- A texture dedicated to a small clutter object **should** be 1024 pixels or
  less on either axis unless its normal viewing case says otherwise, and an
  interface or close-inspection asset is exactly that exception.
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

Furniture is not small clutter. Chairs, stools, tables, counters, beds, cabinets,
and comparable furnishings are evaluated by screen coverage, UV density, normal
viewing distance, and the source-plus-one-step rule; they are not automatically
subject to the dedicated small-clutter 1024-pixel cap.

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

## Record every downscale as an issue (user, 2026-08-29)

"We can open issues to do downscale patches. We should put issues in for such as
we go." Every time a mod's textures are capped or trimmed into an
`Ensrick - ... Texture Cap` overlay, open a GitHub issue recording the mod, the
measured before/after dimensions, the exact recipe, and the permissions basis.
A ledger `note` alone is not enough - it makes the overlays invisible as a body
of work, so they cannot be reviewed, revisited, or packaged.

Overlays stay local-only and are never committed or redistributed
(`REDISTRIBUTION.md`). The author's own mod folder always stays byte-identical
to the Nexus archive.
