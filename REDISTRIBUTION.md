# Redistribution Policy

The MIT License applies only to the original scripts and documentation committed
to this repository. It does not relicense any game, tool, or mod content used by
a local workflow.

## Never committed

- Bethesda game masters, archives, executables, Creation Club content, or saves
- Nexus or other mod archives and their extracted files
- Third-party executables, libraries, or source snapshots
- Generated ESP/ESL/ESM files unless every input and output right is separately
  verified
- NIF, DDS, animation, audio, or other third-party assets
- MO2/Vortex profiles, deployment manifests, download metadata, and logs
- Private build directories, test worlds, backups, and crash reports
- `toolchain.json`, which contains machine-specific paths and executable hashes

## Restricted local recipes

The Lost LongSwords documents and scripts describe transformations and validation
checks only. The source archive, converted assets, and generated plugin are not
distributed. The authoritative local policy is recorded in
`records/restricted-mods.json`.

Referencing a third-party project, filename, identifier, or checksum is factual
provenance and does not grant permission to redistribute its content.

## Required-but-non-bundled dependencies

The project distinguishes a mod-pack requirement from a file that may be placed
inside a public release:

- An author-hosted mod with restrictive permissions can remain a required
  external download. The installer or collection may identify the exact page,
  file, version, and checksum, but must acquire it from the authorized source.
- The current tree blend follows that model: Ulvenwald 3.3.2 and Tree Diversity
  Project 1.0.1 remain immutable Nexus-fetched dependencies. A public installer
  may reproduce the recorded FOMOD choices and disable `Ulvenwald.esp`; it may
  not bundle either vendor archive or extracted tree assets.
- The current grass stack follows the same model: Freak's Floral Fields 3.2.3,
  Freak's Floral Solstheim 1.0.1, Freak's Floral Veil 1.0, and DrJacopo's 3D
  Grass Library 16.53 remain immutable Nexus-fetched dependencies. The
  installer may reproduce the recorded mappings and locally extract FFF's
  lower-tier `Twigs_Freak.dds` to enforce the 4096-axis cap, but must not bundle
  that DDS or any vendor payload.
- A locally rebuilt binary or generated asset that has no established right of
  redistribution is a **publication blocker** when the active profile cannot run
  without that exact private artifact.
- Original Ensrick patches and binaries are published as separate mods only
  after their inputs, license, source, build recipe, and notices pass review.
- Optional experiments and inactive files are not runtime blockers and must not
  be presented as required dependencies.

The current blocker inventory is machine-readable in
`records/private-runtime-dependencies.json`. Restricted author-hosted downloads
remain in `records/restricted-mods.json`.
