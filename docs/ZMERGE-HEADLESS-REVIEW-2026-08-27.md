# zMerge Headless source-build review

Date: 2026-08-27 (America/Chicago)

## Decision

Use `Ensrick/zedit` branch `ensrick/headless-zmerge` at commit
`fd8df93a0ac47f529d6f144e61f6741700f4bd97` as the conditional merge builder.
Do not adopt a merge merely to reduce plugin count; the current profile does not
need one. Install MergeMapper only if a reviewed zMerge output is actually
adopted and dependent runtime FormIDs need translation.

## Current-state research

The current upstream zEdit/zMerge release is 0.6.7 from 2022. zMerge remains the
merge producer; MergeMapper consumes zMerge maps at game runtime and does not
replace the producer. Skyrim SE's ESL ecosystem has superseded routine merging
for many lists, but not the specialized merge workflow itself.

## Worker architecture

The fork preserves the upstream Angular/XEditLib merge engine inside a hidden,
muted Electron renderer. Production packages cannot launch the legacy UI. They
create no visible window, taskbar entry, focus target, sound, or dialog; GPU use,
HTTP/HTTPS, child windows, and non-file navigation are disabled. Internally this
is still an Electron renderer, not a pure console rewrite. The distinction is
recorded because Electron 12 is end-of-life.

The versioned JSON contract supports:

- `inventory`: read MO2-visible load order and active state;
- `validate`: resolve the source/master closure and load it without output; and
- `build`: require `BUILD_MERGE_OUTPUT` and write to a folder outside Data.

The worker refuses core/Creation Club sources, duplicate sources, unsafe Windows
names, output in or around game Data, unowned replacement folders, and merge
filenames already visible in the VFS. It hard-disables plugin and mod disabling.
Every completed build returns relative path, byte size, and SHA-256 for each
output file.

## Defects found and corrected

- Upstream `mergeBuilder.buildMerges` did not expose completion or failure, so a
  controller could not know when a build had actually finished.
- `mergeIntegrationService.sortModFolders` constructed but did not return its
  result.
- Validation cleanup assumed that the GUI progress logger was initialized.
- Build finalization assumed that the desktop merge-status view model existed.
- Startup/crash paths used modal dialogs or renderer alerts.
- A native module omitted `/EHsc`, despite using C++ exceptions.
- Pinning only the Electron EXE would not pin application code; the toolchain now
  validates `app.asar` and native companions too.

## Verification evidence

- 7/7 JSON contract tests passed.
- Gulp production source build passed.
- `diskusage`, `xelib`, and `registry-js` rebuilt from pinned source for Electron
  12 with Visual Studio 2022 and Python 3.
- The one-command packaging recipe passed and produced a self-describing manifest
  plus a 96,934,758-byte ZIP with SHA-256
  `6F61932986F24E09EA2836BE5753179A8266AC8241774D4C5668E949E3ABD9A4`.
- Bare packaged launch exited 2 silently; all sampled window handles were zero.
- Real MO2 `Default` profile inventory returned 168 load-order entries and 162
  active entries, exit 0, with zero window handles.
- Validation of `Starfrost.esp` plus `StarfrostVanillaHunger.esp` loaded their
  nine-plugin master closure, returned zero mutations, and created no output.
- A disposable external build returned exit 0 and inventoried 51 output files,
  including a 116,369-byte merged ESP. Plugin/mod disabling remained false.
- Pre/post load-order and active-plugin membership were identical, and the
  disposable merge was not visible in the MO2 VFS.

## Residual risk and roadmap

Electron 12 and the historical Angular dependency graph contain known advisories.
The worker blocks networking and loads trusted local files only, which narrows
but does not erase that risk. The long-term master issue is to extract the merge
pipeline from Angular/Electron onto a maintained runtime while retaining exact
fixture parity. Until then, manifests and mod inputs are trusted-local only and
the tool must not be exposed as a service.
