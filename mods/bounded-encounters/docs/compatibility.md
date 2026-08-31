# Runtime compatibility

Compatibility is claimed per exact executable and SKSE build, not by the broad
labels "SE" or "AE." The first public artifact is a test candidate.

## Supported runtime matrix

| Store/runtime | Skyrim executable | SKSE | Address Library | Status |
| --- | --- | --- | --- | --- |
| Steam Skyrim SE/AE | `1.7.104.0` | `2.3.1` | AE database, format 5, matching runtime | Initial target; build and in-game acceptance testing required |

## Explicitly unsupported or unclaimed

| Target | Status |
| --- | --- |
| Skyrim VR | Unsupported; VR is disabled in the build. |
| GOG runtime | Unclaimed until separately built and tested. |
| Microsoft Store/Game Pass runtime | Unclaimed. |
| Older Steam runtimes, including `1.5.97` and `1.6.x` | Unclaimed. |
| Future Steam runtimes | Fail closed until reviewed, built, and tested. |
| SKSE versions other than the matrix entry | Unclaimed. |

"Unclaimed" does not mean known incompatible. It means the project will not
represent that combination as safe without evidence.

## Required runtime dependencies

- SKSE `2.3.1` launched through its loader;
- the Address Library package containing the database for Skyrim `1.7.104.0`;
- the Microsoft Visual C++ runtime required by the release build; and
- the matching Steam Skyrim executable.

The package does not include SKSE, Address Library, the Visual C++ redistributable,
or Bethesda files.

## Pinned build compatibility

The initial target is built against Ensrick's CommonLibSSE-NG
`ensrick/no-modal-errors-v7` fork at commit
`a9d7d4523d5e1abc8b296bd99683b7df11df652f`. That commit has upstream
`v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f` as its direct parent and adds an
opt-in `COMMONLIBSSE_NO_MODAL_ERRORS` failure path. Bounded Encounters enables
that path so CommonLib fatal reporting logs and throws to the plugin boundary
instead of opening a native modal dialog. The submodule pin prevents a later
fork or upstream revision from entering a release implicitly. The vcpkg
registry is independently pinned in `vcpkg-configuration.json`.

CommonLibSSE-NG is GPL-3.0-or-later with its `EXCEPTIONS.md` Modding Exception.
The exception permits this project's original mod code to remain MIT, while the
CommonLib portion remains subject to its GPL and exception terms. Binary
distribution therefore includes those texts and is accompanied by the exact
fork-commit corresponding-source archive. The archive includes the fork patch,
not merely the upstream base.

## Mod compatibility model

Bounded Encounters is a DLL-only runtime multiplier. It does not edit records,
leveled lists, cells, navigation meshes, scripts, or load-order metadata, so it
has no traditional xEdit record conflicts and needs no ESL slot.

It can still interact behaviorally with:

- encounter-zone and leveled-list overhauls;
- mods that spawn, replace, disable, or recycle actors at runtime;
- quest mods with unconventional actors not represented by ordinary aliases;
- population multipliers and increased-spawn mods;
- corpse cleanup, actor persistence, and save-management plugins;
- mods that change hostility or teammate state after a cell loads.

Do not combine it with another general encounter multiplier during initial
testing. Mod-authored references are excluded unless their defining plugin is
explicitly added to `allowedSourcePlugins`. Leave script-driven or self-managed
encounters outside that allowlist and add their plugins to `deniedPlugins` as a
defense-in-depth veto when their forms may also participate in an allowed
encounter.

## Compatibility report requirements

A support claim requires all of the following:

1. exact Skyrim and SKSE versions;
2. Address Library file corresponding to that runtime;
3. clean plugin initialization with no safety-hook failure;
4. new-game and existing-save smoke tests;
5. interior and exterior encounter tests;
6. save, quit, reload, cell-reset, and uninstall-on-disposable-save tests;
7. crash-logger and plugin-log review; and
8. the tested configuration and load order archived with the result.

Use the compatibility-report issue form so results remain reproducible.
