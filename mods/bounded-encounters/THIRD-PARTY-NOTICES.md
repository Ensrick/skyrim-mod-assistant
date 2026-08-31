# Third-party notices

Bounded Encounters links against or uses the following build dependencies:

- Ensrick's CommonLibSSE-NG no-modal-errors fork (commit
  `a9d7d4523d5e1abc8b296bd99683b7df11df652f`), based directly on upstream
  `v7.0.0` commit `8b032fa992750d654d6d38a33731714d8b86be1f`, GNU General
  Public License version 3 or later with the unchanged upstream
  `EXCEPTIONS.md` Modding Exception. Upstream is maintained by alandtse and
  contributors; the opt-in no-modal-errors change is maintained by Ensrick.
- Skyrim Script Extender, copyright its respective authors; distributed under
  the terms in the SKSE source package.
- DirectXMath, MIT License, Microsoft Corporation.
- DirectX Tool Kit, MIT License, Microsoft Corporation.
- {fmt}, MIT License, Victor Zverovich and contributors.
- nlohmann/json, MIT License, by Niels Lohmann and contributors.
- rapidcsv, BSD 3-Clause License, Kristofer Berggren.
- SimpleIni, MIT License, Brodie Thiesfield.
- spdlog, MIT License, by Gabi Melman and contributors.
- Xbyak, BSD 3-Clause License, MITSUNARI Shigeo.

The binary archive retains the exact vcpkg-provided copyright/license text for
each direct build dependency under `licenses/vcpkg/`.

The implementation is original. Dynamic Enemy Spawns SKSE 3.1 was inspected as
prior art while evaluating cell-load timing, transient-reference lifecycle,
and known save-persistence hazards. No source from that package is included in
this module.

## CommonLibSSE-NG source and exception

The release DLL statically links CommonLibSSE-NG. The Modding Exception permits
the original Bounded Encounters code to remain under MIT, but it does not remove
the GPL obligations for the CommonLibSSE-NG portion of the combined binary.

Every binary package is accompanied by a deterministic archive named
`BoundedEncounters-<version>-CommonLibSSE-NG-a9d7d452-source.zip`. It contains
the tracked corresponding source at the actual fork build commit, `COPYING`,
`EXCEPTIONS.md`, and a SHA-256 manifest. The same GitHub release must retain
that archive and its hash for as long as it distributes the binary. Review the
[immutable fork build commit](https://github.com/Ensrick/CommonLibSSE-NG/tree/a9d7d4523d5e1abc8b296bd99683b7df11df652f)
and its [immutable upstream base](https://github.com/alandtse/CommonLibSSE-NG/tree/8b032fa992750d654d6d38a33731714d8b86be1f).

The binary archive includes verbatim copies of CommonLibSSE-NG's `COPYING` and
`EXCEPTIONS.md`. Refer to those files for the controlling terms.
