# Save/load admission — native core, not deployed

Original MIT implementation for [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
This currently builds a static library, read-only CLI and synthetic tests.
There is **no installed SKSE plugin or runtime admission adapter yet**. It
does not repair, clean, migrate, rewrite or certify a saved game.

## Implemented boundary

- Bounded SSE v12 header and plugin-table reader, supporting uncompressed,
  zlib and raw LZ4 bodies (including overlapping matches).
- File and decompressed-body limits256MiB each; checked screenshot arithmetic,
  bounded fields and length/count consistency. World/Papyrus records after
  the plugin table are outside this parser's certification scope.
- Plugin filename validation, strict UTF-8, duplicate detection, ASCII
  case-insensitive name comparison and full/light class preservation. Added
  active plugins are permitted; missing plugins or a changed class refuse.
- Strict whole SKSE co-save envelope and currency ECMK v2 checkpoint parsing.
  Reuses the existing currency source's SaveMarkerPolicy.h recognition and
  balance limits rather than duplicating those constants. No checkpoint,
  duplicate/unknown currency data, different fingerprint or unsupported balances
  refuse. Different backend/physical/value counts can represent pending
  accounting transactions and are NOT arbitrarily forced equal.

The API accepts byte spans and caller-supplied active plugin tables/ledger
fingerprint. Exceptions must be caught by a future engine adapter. The CLI is
an offline harness: its `compare` command treats a second save's table as the
reference, **not** as proof of the currently loaded engine configuration.

## Build and tests

From the repository root:

```text
cmake -S mods/save-load-admission/native -B build-admission
cmake --build build-admission --config Release
ctest --test-dir build-admission -C Release --output-on-failure
```

Dependencies: C++20 toolchain and source-built zlib1.3.2. CMake downloads the
exact upstream source archive with a pinned SHA256; no mod payloads or player
saves are downloaded. See [third-party notices](THIRD_PARTY_NOTICES.md).
Build trees and binaries are excluded from publication.

```text
save_admission_inspect ess SAVE.ess
save_admission_inspect checkpoint SAVE.skse HEX_FINGERPRINT
save_admission_inspect compare SAVE.ess REFERENCE_SAVE.ess
```

Exit0 means parsed/matched at that command's narrow scope;1 reports comparison
differences;2 reports unsupported/malformed/unreadable inputs. Neither0 nor
the word CHECKPOINT certifies Papyrus or gameplay. Metadata strings not used
for policy (player name/location/date/race) are bounded but otherwise opaque.
Plugin names are validated and the CLI never prints player-name metadata.

Local626 synthetic checks cover all compression modes, every truncation of
the minimal complete fixtures, zlib size/checksum/trailing-member failures,
LZ4 bad offsets/lengths/overlap, invalid filenames/UTF-8, changed plugin class,
missing plugins, checkpoint versions/duplicates/truncation/balance limits and
pending accounting observations. Hosted Windows/Linux workflow is included.
This is deterministic regression coverage, not exhaustive fuzzing.

## Remaining work before deployment

1. Adapter must resolve the exact requested ESS/co-save using the engine/MO2
   save-path context, validate basename/path boundaries and capture the actual
   loaded full/light plugin table. A disk profile or reference save is not
   authoritative for an already-running game.
2. Obtain expected currency fingerprint from the initialized, reviewed bridge,
   verify package readiness/identity and paired active companions. Do not
   trust a fingerprint supplied by the save being checked.
3. Preserve file identity between inspection and engine read (read handles,
   sharing/identity checks and tests), handle memory/I/O/parser exceptions,
   and measure latency/memory under the live hook. No file-lock guarantee is
   made by the offline CLI. Non-ASCII case equivalence also needs an explicit
   Windows-compatible policy; current comparison only folds ASCII.
4. Join the proven diagnostic boundary with race-safe native cancellation and
   useful in-game explanation; prevent stale cancellation from affecting a
   subsequent valid request. Do not use a static filename allowlist.
5. Verify Main Menu/Continue/Journal/quickload and relevant nonzero argument
   paths; preserve live character state after rejection, then valid load,
   new save, reload and sustained gameplay. Nothing here authorizes restoring
   removed mods or choosing an Adventurer3 campaign migration.

The existing Python launcher gates remain separate and unchanged. Native
parsing is a prerequisite for ordinary-load enforcement, not its completion.
