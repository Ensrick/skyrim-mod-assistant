# Collection workspace

This directory contains reviewed, source-only intent for a future Nexus Mods
Collection. It does not contain a generated Vortex collection, downloaded mod
archives, audio, plugins, or other third-party material.

## Manager boundary

- **Mod Organizer 2** remains the authoritative local profile manager and the
  environment used by headless inspection and patching tools.
- **Vortex** is used as an isolated collection-authoring and consumer-validation
  layer because Nexus Collections are built around Vortex.
- Vortex must use separate staging, downloads, and profile paths. It must not
  discover or adopt the live MO2-managed game state without a reviewed import
  plan.
- Generated Vortex state is private working data and remains ignored.

The installed Vortex 1.13.7 is below the supported collection baseline. The
target is the current stable Vortex 2.5.0 release, pinned from the official
`Nexus-Mods/Vortex` GitHub repository. Its 369,749,984-byte installer has SHA-256
`53CF2EDC3DFC1324FED14E8BF0268EE5C4449378C2960D7F5C1F7B07050B2DC6`,
matches the release manifest's SHA-512, and has a valid Black Tree Gaming Ltd
Authenticode signature. Updating the executable does not itself authorize
Vortex to deploy mods into the live game directory.

## Music framework decision

The selected framework is **Personal Music Framework 1.1**, Nexus SSE mod
134467, FOMOD file 742217. Its hard dependency chain is recorded in
`draft-manifest.json`.

PMF does not ship a soundtrack. Its 356 supplied `.xwm` files are silence
placeholders. Until a rights-cleared soundtrack module is built, the collection
preset installs PMF's required core plugin but selects no playlist option. This
keeps the framework present and inert instead of adding silence to vanilla
playlists.

When music is added later:

1. Verify the source and redistribution rights for every recording.
2. Convert to `.xwm`; do not ship `.wav` as the runtime format.
3. Replace only the PMF slots actually selected by the curated FOMOD preset.
4. Prefer **Add to Vanilla** initially. Use **Replace Vanilla** only for a
   deliberate soundtrack conversion and test every affected music type.
5. Reinstall in a disposable Vortex profile and capture the FOMOD preset into
   the generated collection revision.

## Publication rule

A Nexus Collection references hosted mod files; it does not grant permission to
redistribute those files. PMF must be referenced by its Nexus IDs and may not be
bundled. Any future bundled output is limited to our own material and compatible
tool-generated files whose licenses and source assets permit redistribution.
