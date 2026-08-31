## Bounded Encounters summary

Describe the behavior and why this is the smallest safe change.

## Safety impact

- [ ] Generated actors still cannot become multiplication sources.
- [ ] Exclusions still win over classification and allow behavior.
- [ ] No authored reference is modified, moved, deleted, or persisted.
- [ ] Save/lifecycle assumptions are unchanged or covered by targeted evidence.
- [ ] Unsupported runtimes and invalid configuration fail closed.
- [ ] No code path adds modal UI, deployment, telemetry, or network access.

## Verification

Include commands and concrete results, not only "tests pass."

```text
cd mods/bounded-encounters
tools/build.bat
```

## Compatibility and release notes

Document schema/runtime changes, save implications, and whether a disposable
save is required. Confirm source, notices, manifest, SBOM, and corresponding
source remain complete.
