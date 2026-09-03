# Believable Weapons retexture compatibility audit

Audited headlessly on 2026-08-29 against the current official files. Nothing
was installed, no game or mod-manager UI was launched, and no curator state was
changed.

## Decision

[Silver Armor and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/89109)
works with Believable Weapons' silver sword and silver greatsword meshes. No
mesh patch is needed for their blade or hilt. Use Xavbio's current 2K silver
weapon textures directly and let them overwrite the vanilla silver DDS paths.

The only separate aesthetic decision is the scabbard. Believable Weapons uses
the **steel** scabbard texture set on its silver sword and optional greatsword
scabbard, so the scabbard will follow the eventual steel retexture rather than
Xavbio's silver sword textures. That is intentional path separation, not a UV
or missing-texture defect. Do not create an Ensrick silver compatibility patch
for this combination.

## Why a retexture may or may not fit a replacement mesh

The NIF, not the DDS, supplies the geometry, vertex UV coordinates, texture
paths, tangents/normals, shader type, cubemap and material flags. A retexture is
patch-free only when all of the following remain true:

- the winning NIF reads the paths the retexture replaces;
- the new mesh preserves the texture's atlas semantics, not merely its filename;
- its normal/specular/environment maps match the winning tangent basis and
  shader/material configuration; and
- first-person, third-person, left-hand, ground/load-screen and scabbard variants
  are either covered or intentionally independent.

Scaling or reshaping a blade does not inherently break a retexture: UVs can move
with the vertices. A mesh made for a newly rearranged atlas does break a vanilla
texture even when the filenames match. Two mesh replacers also do not blend;
the later NIF wholly replaces the earlier NIF unless someone makes an integrated
mesh.

Believable Weapons' author describes the base mod as a mesh-only reshaper that
uses the original texture paths and supports texture replacers. The installer
nevertheless includes special mesh choices for known material/path exceptions:
aMidianBorn Skyforge, Frankly Imperial, Frankly Dawnguard, HD Reflective Ebony,
Light Refracting Glass, Outlandish Stalhrim, Refracting Stalhrim, dual sheath and
greatsword scabbards. Those options are the authoritative choice for those
combinations.

## Silver 89109: archive and NIF proof

The current Nexus version is `2.1.1`, updated 2026-07-18. The separately
published `Silver Swords Retexture` file 775704 contains exactly three assets:

- `textures\weapons\silver\silversword.dds`
- `textures\weapons\silver\silversword_n.dds`
- `textures\weapons\silver\silversword_m.dds`

It contains no NIF or plugin. All four relevant Believable Weapons v1.5 base
NIFs consume those exact three paths. The silver-textured shapes retain the
same shader and material state as Bethesda's extracted SE meshes: shader type
1, flags `0x82400381/0x8001`, environment mapping at `0.5`, specular enabled at
strength `1`, glossiness `80`, and an identity UV transform. Every vertex has a
finite, nonzero normal and tangent.

The following comparison uses quantized UV-coordinate multisets. High overlap
is expected rather than byte identity because Believable Weapons changes the
geometry and adds a small number of vertices. The unchanged atlas bounds plus
93-98% multiset overlap show preservation of the vanilla silver atlas rather
than a remap.

| Mesh | Vanilla UV coverage found in BW | BW UV coverage found in vanilla | UV Jaccard | UV bounds identical |
|---|---:|---:|---:|---|
| Third-person silver sword | 99.22% | 98.29% | 97.54% | Yes |
| First-person silver sword | 99.44% | 98.33% | 97.79% | Yes |
| Third-person silver greatsword | 96.88% | 96.23% | 93.34% | Yes |
| First-person silver greatsword | 97.32% | 95.63% | 93.17% | Yes |

The third-person atlas bounds are
`0.002592,0.001492..0.991699,0.996582`; first-person uses
`0.002304,0.001492..0.991699,0.996582`. The corresponding vanilla and
Believable shapes agree exactly.

The 1H Believable silver sword's scabbard reads
`textures\weapons\steel\steelscabbards.dds`, `_n.dds`, and `_m.dds`; the
optional Believable greatsword-scabbard NIF uses the same steel set. Xavbio's
optional LeanWolf silver-scabbard choice targets LeanWolf's custom mesh and is
not the correct choice for Believable Weapons.

## Compatibility matrix

The status distinguishes byte/structure inspection performed in this audit
from compatibility inferred from a current texture-only contract or an
author-provided option.

| Retexture or mesh suite | Current version | Status with Believable Weapons | Required treatment |
|---|---:|---|---|
| [Silver Armor and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/89109) | 2.1.1 | **Verified compatible** for vanilla silver sword/greatsword blade and hilt | No patch. Do not select the LeanWolf scabbard option. Steel textures govern BW scabbards. |
| [Project Clarity - Vanilla Weapon Textures Redone](https://www.nexusmods.com/skyrimspecialedition/mods/36222) | 2.0 | Compatible by texture-only vanilla-path contract | No patch for the ordinary weapon DDS payload. |
| [Project Clarity AIO](https://www.nexusmods.com/skyrimspecialedition/mods/45306) | 3.2 | Compatible for its vanilla-path weapon textures | No BW patch for texture-only paths; audit any independently selected mesh extras separately. |
| [aMidianBorn Book of Silence SE](https://www.nexusmods.com/skyrimspecialedition/mods/35382) | 1.9.1 | Standard vanilla-path weapon textures fit; custom Skyforge treatment is an exception | Select `aMidianBorn Skyforge weapons` in the BW FOMOD where applicable. |
| [aMidianBorn Content Addon](https://www.nexusmods.com/skyrimspecialedition/mods/35390) | 3.1.9 | Custom variants/scabbards are not a generic texture-only case | Use the addon's current Believable Weapons and greatsword-scabbard choices; do not synthesize a second patch. |
| [RUSTIC ARMOR and WEAPONS SE](https://www.nexusmods.com/skyrimspecialedition/mods/19666) | 3.0 | Ordinary vanilla-path texture payload should fit, but this archive was not asset-audited here | Permit DDS conflicts; re-audit any optional NIFs before enabling them over BW. |
| [Daedric Armors and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/84151) | 2.0.1 | Base vanilla-path textures fit the BW contract | Do not install a LeanWolf custom-sheath mesh over BW. Audit non-vanilla consistency options separately. |
| [Iron Armors and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/84978) | 2.1.1 | Texture-only selection fits; cubemap/mesh features require the matching mesh choice | Select the Believable Weapons option wherever the current FOMOD offers a weapon/cubemap mesh. |
| [Steel Armors and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/85445) | 2.1.2 | Texture-only paths fit; material/cubemap and Nordic Carved variants are mesh-sensitive | Select the Believable Weapons weapon/scabbard choices in its FOMOD. This pack will also control BW silver scabbard appearance. |
| [Glass Armors and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/87580) | 2.2.1 | Mesh-sensitive because its glass material/cubemap presentation is part of the result | Use the current Believable Weapons mesh option, not vanilla or LeanWolf. |
| [Ebony Armors and Weapons Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/83654) | 2.1.2 | Supported by its Believable Weapons installer choice | Select Believable Weapons. Do **not** add the optional `Vanilla Ebony Weapons Meshes - Greatsword Fix`; the author explicitly excludes the BW option. |
| [Saints and Seducers Retexture SE](https://www.nexusmods.com/skyrimspecialedition/mods/151116) | 1.1.0 | Base CC set needs matching integrated meshes for BW's reshapes and special artifacts | Use its BW choices plus the current patch collection where the selected Sword of Jyggalag/Nerveshatter texture addons require it. |
| [Iron Weapons Retexture](https://www.nexusmods.com/skyrimspecialedition/mods/50377) | 1.1 | **Verified incompatible without its patch** | Install the author's `Believable Weapons Patch` after both. It deliberately remaps BW UVs. |
| [Cathedral - Armory](https://www.nexusmods.com/skyrimspecialedition/mods/20199) | 3.21 | Mesh/material suite; not safely combined by overwrite alone | Use [Cathedral Armory Believable Weapons Patch](https://www.nexusmods.com/skyrimspecialedition/mods/46199) after both. |
| [Cathedral Armory for CC](https://www.nexusmods.com/skyrimspecialedition/mods/85977) | 1.3.4 | Only the explicitly patched CC subset is established | Use its current BW patch option. The official file description declares Draugr and Saints/Seducers coverage; do not infer coverage for every CC weapon. |
| Frankly Imperial, Frankly Dawnguard, Reflective Ebony, Refracting Glass/Stalhrim, Outlandish Stalhrim | current selected upstream file | Known special material/path cases | Use Believable Weapons' own named FOMOD alternative; do not use the plain base mesh. |
| [ElSopa - Iron Weapons Redone SE](https://www.nexusmods.com/skyrimspecialedition/mods/52605) | 1.2 | Mutually exclusive mesh replacement for the same iron weapon NIFs | Choose ElSopa or BW for each path. [CL's integrated alternative](https://www.nexusmods.com/skyrimspecialedition/mods/118250) is a separate replacer, not an overlay for BW. |
| LeanWolf's Better-Shaped Weapons | current selected upstream file | Mutually exclusive on every shared NIF path | Choose the winning mesh per weapon and use that mesh family's texture/scabbard options. |

### Iron 50377 verification

The official patch archive was compared directly with BW v1.5. It is not a
no-op: the iron longsword and war-axe weapon shapes have zero quantized UV
overlap with the unpatched BW shapes; battleaxe overlap is roughly 20-29%,
warhammer roughly 27-69%, and mace roughly 64-88%, depending on view. The
scabbard shapes remain unchanged. This agrees with the author's file note that
the patch alters BW UVs to fit the new iron atlas. A texture overwrite without
that patch will visibly mis-map the weapons.

## Current upstream patch coverage

[Believable Weapons and Better Shaped Bows Patches](https://www.nexusmods.com/skyrimspecialedition/mods/167575)
v1.0, updated 2025-12-20, was downloaded and enumerated. Its Believable Weapons
payload covers:

- Artificer - Xavbio Texture Addon variants: Pale Blade, Imperial arming sword,
  Prelate mace, Red Eagle, silver-ebony weapons, Sword of Solitude and white
  Nord Hero weapons;
- Xavbio's Sword of Jyggalag; and
- Amber Refossilized Nerveshatter.

Its other groups cover Better-Shaped Bows and Kinda Believable Ghosts of the
Tribunal. It does not contain a patch for vanilla silver sword/greatsword
textures, consistent with the structural result that none is required.

## Ensrick-owned overlay policy

Prefer the upstream installer option or current upstream patch in every row
above. Do not copy vendor NIFs or DDS files into an Ensrick mod merely to freeze
conflict order.

Create a public Ensrick compatibility overlay only when a chosen combination
lacks upstream support and all source permissions explicitly allow the derived
mesh to be redistributed. Such an overlay should contain only the minimum
edited NIF/configuration, name exact required versions, retain provenance and
credits, and never repackage the texture suite. If any source permission is
unclear or restrictive, the synthesis must remain local-only and be recorded as
a restricted/private runtime dependency. A Nexus page's `modder's resource`
label applies only to the specifically labelled resource file, not automatically
to the complete mod.

No owned overlay is justified for Silver 89109 now. A new silver-coloured
scabbard would be an optional art-direction mod, not a compatibility fix, and
should wait until the steel texture suite is selected and evaluated in game.

## Provenance and limitations

| Archive | Nexus file | SHA-256 |
|---|---:|---|
| Believable Weapons v1.5 | 260562 | `C9F93A3F0690A8A601B1CE5BED83236021520132BFB32BB9D397838DC2FFB470` |
| Silver Swords Retexture (2K) | 775704 | `244C90D4B589C452AE58D19DF2FD00586215C7CB6BAD497C17063F8808E9CE9C` |
| Iron Weapons Retexture - Believable Weapons Patch | 205558 | `3808CEBE868504C61F29CD202CF9A82554791CC797241ABEBB3F212AD7A62989` |
| Believable Weapons and Better Shaped Bows Patches v1.0 | 700122 | `48723310CEC25EC427334FC2F674E90B4F0B3A8026C8823DED484AC781C3DA96` |

Bethesda silver meshes were read directly from the installed
`Skyrim - Meshes1.bsa`; no game asset was copied into this repository. The NIF
comparison used the owned source checkout of `nifly` and examined texture slots,
shape/triangle/UV counts, quantized UV overlap, UV bounds, normal/tangent health,
shader type and flags, environment mapping, specular/gloss and UV transforms.

Consequential uncertainty remains limited to appearance under the final lighting
stack. This was a structural compatibility audit, not an in-game render test.
The silver blade/hilt mapping is strongly established, but the eventual steel
scabbard colour and cubemap response should receive a visual spot-check once the
steel retexture and Community Shaders material stack are final. Large FOMOD
suites change over time; their exact selected file map must be captured and
re-audited at installation rather than relying on this matrix alone.
