# Contributing

Changes must preserve the following invariants:

1. Generated actors never become multiplication sources.
2. Exclusion wins over every category or allow rule.
3. Invalid or ambiguous configuration disables the affected behavior.
4. No build step deploys into Skyrim or a mod manager.
5. Runtime-facing work includes deterministic pure-logic tests and structured
   logging.
6. Hook or engine assumptions include evidence and a supported-runtime gate.

Run `tools/build.bat` before opening a pull request. Do not commit Bethesda
files, Nexus archives, Address Library databases, game logs, saves, or build
outputs.
