# Expressive faces: current suitability review

Reviewed 2026-09-06. Research only: nothing installed, downloaded, added to Keep,
or changed in the live profile. Versions below are those displayed by the
author's current Nexus pages, not independently audited archive versions.

## Recommendation

**Recommend considering both Expressive Facial Animation editions.** They suit
the intended restrained, vanilla-compatible presentation. Expressive Facegen
Morphs is also useful, but its full package is a character-creation decision,
not a prerequisite for installing the two animation packages. No authoritative
deprecation or general-purpose successor was found in this bounded review.
Old asset-release dates do not themselves establish obsolescence; neither does
popularity establish compatibility with every face.

| Component | Current listed version / update | Distinct job |
|---|---|---|
| [Expressive Facegen Morphs SE](https://www.nexusmods.com/skyrimspecialedition/mods/35785) | 1.0 / 2020-07-19 | Player character-creation deformation and additional RaceMenu sliders. |
| [Expressive Facial Animation — Female](https://www.nexusmods.com/skyrimspecialedition/mods/19181) | 1.7 / 2019-12-07 | Female expression morph replacements for compatible player and NPC heads. |
| [Expressive Facial Animation — Male](https://www.nexusmods.com/skyrimspecialedition/mods/19532) | 1.21 / 2019-12-08 | Male counterpart; its latest fix corrects upper-lip beard deformation. |

## Actual installed context

Read-only evidence: `profiles/Default/modlist.txt` in the canonical MO2 instance
and `records/installed-mods.json`. RaceMenu and its Ensrick 1.7.104 native overlay,
CBBE, HIMBO, Reverie, SkySight Skins, VHR SMP and its NPC package are enabled.
The private VHR compatibility overlay deliberately retains 29 USSEP FaceGen
winners and fixes three VHR XML references. The current setup also contains
custom followers and new-land NPCs with their own assets.

No enabled or ledgered Expressive package, High Poly Head, broad Nordic
Faces/Bijin/Pandorable replacement, or Mfg Fix was identified. Six standard
head/mouth NIF/TRI paths had no loose mod provider; this limited check is **not**
a complete BSA or custom-head audit. The existing ecosystem survey groups
Expressive Morphs/Animation among common choices; its combined count should
not be represented as a fresh, separately verified count for each package.

## Morphs versus expressions

EFM's main package changes how existing slider values shape a face. Back up
presets/sculpts; use it for new or EFM-authored characters. The optional
RaceMenu-plugin-only package adds sliders without replacing the underlying
creation morphs. EFM does not automatically rebuild existing NPC FaceGen.
Its included mouth mesh and texture are a matched pair; its female head also
adjusts UVs, so makeup and competing mouth/head files need inspection.
The author targets vanilla topology, not arbitrary high-poly meshes.
[EFM author documentation](https://www.nexusmods.com/skyrimspecialedition/mods/35785)

EFA changes the shapes used while speaking, blinking, and expressing emotions;
it does not schedule more emotions. Existing NPCs can benefit when their heads
reference the compatible expression assets. Alternate topology or private TRI
paths require their own compatible route. The author warns that strongly
receding jaws can still expose teeth, and RaceMenu's expression sliders do not
preview these EFA files. Fair Skin is tied to an optional teeth choice, not a
reason to replace our approved skin textures.
[Female edition documentation](https://www.nexusmods.com/skyrimspecialedition/mods/19181)

For our setup, preserving the VHR/USSEP FaceGen winners is preferable to
regenerating all NPC faces merely to add expressions. This is an integration
recommendation, not a claim that every installed follower's topology was
inspected. Test male beards, female mouths, elves and representative followers
in actual dialogue. The male author likewise describes EFA as asset replacement
with conversation-driven control, not a new expression scheduler.
[Male edition documentation](https://www.nexusmods.com/skyrimspecialedition/mods/19532)

## Newer alternatives are not automatic replacements

- [Conditional Expressions Extended](https://www.nexusmods.com/skyrimspecialedition/mods/91438)
  2.2.1, updated 2026-08-07, adds condition-driven expression control and nearby
  NPC support. It complements EFA's shapes rather than replacing their role.
  Its additional behaviors and dependencies are a separate owner decision.
- [Mfg Fix NG](https://www.nexusmods.com/skyrimspecialedition/mods/133568)
  1.0.9, updated 2026-05-11, provides native expression functions/transitions.
  It is not an EFA asset successor. Its shipped DLL compatibility with our
  1.7.104 runtime has **not** been verified here; do not infer it from “NG.”
- [Waifu Expression Redux](https://www.nexusmods.com/skyrimspecialedition/mods/70691)
  1.11, updated 2022-09-12, is a genuine competing female expression set, with
  deliberately stronger expressions and vanilla/HPH variants. That is a style
  alternative, not evidence EFA is obsolete. My recommendation favors EFA for
  this project's restrained aesthetic; no objective quality ranking is claimed.

## Approval and installation gates

The open choice is full EFM for future character creation versus its optional
slider-only route for preserving existing looks. This matters to multiple
Proteus characters as well as the current player. Do not silently choose for
the owner. EFA-only is a separate viable scope.

If approved: inspect exact archives, resolve mesh/TRI/teeth winners explicitly,
retain immutable vendors, and verify faces in a disposable test character.
Asset-based operation suggests low overhead and no behavior-generation job;
that is an architectural expectation, not a measured FPS or 1.7.104 gameplay
result. Do not automatically install High Poly Head or an expression controller.

Niroku's permissions prohibit redistributing or modifying the EFM/EFA morph
files; package references/download instructions, not copied TRI assets or a
purported open-source fork. EFM separately permits generated NPC FaceGen and
presets under its stated conditions.
[EFM permissions](https://www.nexusmods.com/skyrimspecialedition/mods/35785),
[EFA permissions](https://www.nexusmods.com/skyrimspecialedition/mods/19532).
