# Active vendor-integrity audit — 2026-08-29

## Policy

An author-supplied mod is immutable input. An official update may replace it
transactionally with another verified official archive, but a local DLL,
configuration change, generated patch, or bug fix must never be written into
the vendor mod directory. Local work is installed as a separate, explicitly
named Ensrick MO2 mod with its own source, manifest, version, hashes, license
review, and rollback boundary.

Public packaging follows the same separation. Restricted vendor files remain
author-hosted external downloads. Ensrick outputs are distributable only after
their inputs and licenses pass review.

## Violations found in the active profile

| Vendor mod | In-place local state | Effective state now | Required normalization |
|---|---|---|---|
| JContainers SE | Patched `JContainers64.dll` plus an as-released backup | The separate 1.7.104 native overlay wins the DLL conflict | Reinstall the exact pristine vendor archive; retain only the separate native overlay. |
| RaceMenu | Self-built `skee64.dll`, two backup DLL/INI files, and edited `skee64.ini` | The separate 1.7.104 native overlay wins the DLL; the edited vendor INI remains effective | Reinstall pristine RaceMenu; retain the native DLL overlay and create a minimal, separate Ensrick configuration overlay. |
| SKSE Menu Framework | Self-built DLL and official DLL backup in the vendor directory | The self-built DLL is effective | Prefer the current official 3.14.1 build if it passes 1.7.104 qualification; otherwise move the local LGPL-2.1 build into a separate native overlay, then reinstall the pristine vendor package. |
| SSE Display Tweaks | Self-built DLL, edited INI, and two vendor-directory backups | Both local files are effective | Move the MIT-licensed DLL build and the minimal display configuration into separate Ensrick overlays; reinstall pristine 0.5.16 below them. |
| The New Gentleman | Self-built DLL and official DLL backup in the vendor directory | The self-built DLL is effective | Qualify official 4.2.6 first; if a local build remains necessary, install it as a separate MIT-licensed overlay and reinstall the pristine vendor package. |
| Skyrim Unbound Reborn | Edited JSON configuration and a timestamped backup in the vendor directory | The edited JSON is effective | Reinstall the pristine vendor package and reproduce only the intended settings in a separate Ensrick configuration mod or a reviewed MCM-settings artifact. |

Debug symbols shipped as part of an author's package are not, by themselves,
evidence of mutation. Custom mods already isolated by name, such as the
Community Shaders AIO source build and QuickLoot IE Ensrick build, are not
vendor-directory violations; their licensing and release readiness are tracked
separately.

## Transactional remediation gate

For each row above:

1. Record the current effective custom file hashes.
2. Build a separate overlay containing only the necessary local delta.
3. Re-download or recover the exact official archive and verify its checksum.
4. Reinstall the official archive transactionally into the vendor mod.
5. Verify that the effective VFS hashes are unchanged where behavior must be
   preserved and that no `.bak`, local marker, or custom binary remains in the
   vendor directory.
6. Run the MO2 profile audit, master audit, ledger verification, and DLL-provider
   audit without launching Skyrim.

No content-record winner will be changed as part of this normalization. Any
record-level compatibility decision remains subject to user approval and, when
approved, belongs in a separate ESL-flagged patch wherever technically safe.
