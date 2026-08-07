# Contributing

Contributions should preserve the repository's source-only, fail-closed design.

Before opening a pull request:

1. Do not add game files, downloaded mods, third-party binaries, generated
   plugins, archives, logs, deployment manifests, or local build output.
2. Do not weaken the deny-by-default `.gitignore` without documenting and
   reviewing the newly exposed paths.
3. Keep executable paths and local hashes in the ignored `toolchain.json`; only
   generic examples belong in `toolchain.example.json`.
4. Parse every changed PowerShell file and JSON document locally.
5. Document destructive behavior and provide a non-mutating preview before
   proposing any game-file maintenance command.

By contributing, you agree that your contribution is licensed under the MIT
License in this repository.
