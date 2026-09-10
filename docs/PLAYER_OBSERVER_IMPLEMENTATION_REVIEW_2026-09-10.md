# Player-observer implementation review for #267

Status: **candidate implemented and live-smoke-tested**, not promoted to the
canonical toolset. Existing independently checked native/serialized layout
remains the authority. This is not representative combat acceptance.

Actual Fable5.1 CLI session65216fa7-4b68-4b8b-8c71-4729a7d4915f completed a
bounded seven-turn read-only review of the existing layout auditor, tests,
ControlMap reader, private player probe and player/dry-ground reports. No
delegated writes, subagents, process interaction or native calls occurred.

Recommended implementation is an original read-only Python module with an
injectable reader, held process handle, finite sample/read budget, structured
refusals and bounded streaming. Reuse `player_layout_audit.verify` and its
exact engine/library/native byte evidence; do not accept merely a version
string or unverified CommonLib vtable call.

Required tests before use: unknown input identities; invalid/null/noncanonical
pointers; partial/unreadable reads; changed process identity; singleton/player/
cell churn; nonfinite coordinates; sampling limits; meaningful preservation of
unstable/degraded evidence. Report positions and cell/world identities with
raw supported actor-state masks, not unverified health/combat flags. Controls
and water-height offsets remain explicitly candidate data until independently
validated. Compare successful live samples with the existing pinned observer
and saved INITIAL prefix before relying on this tool for travel tests.

Parent corrections to the proposal:

- A read-count/byte budget does not guarantee a hard wall-clock deadline for
  a blocking operating-system read. Do not promise that guarantee without a
  bounded worker/process design and actual timeout tests.
- Re-reading pointers detects some churn but cannot guarantee that a prior
  asynchronous dereference was never stale. ReadProcessMemory must fail safely;
  samples remain asynchronous observations, never atomic engine snapshots.
- Do not treat arbitrary unstable samples as rigorous displacement lower
  bounds or treat life-state changes alone as combat acceptance. Test claims
  require coherent before/after identity/cell/position and corroborated actions.
- Do not retire the existing generic ControlMap diagnostics merely because a
  new player observer exists. They serve different purposes.

## Candidate implementation, September 10

Actual Fable5.1 CLI session93417b2f-27e4-4e5d-b919-3080858be151 delivered only
`records-work/player-observer-fable-20260910/`: original observer, adversarial
tests and handoff. No live settings/mods/saves or canonical source were changed
by Fable. First root-run suite:32 PASS. Parent identified missing ctypes
GetModuleInformation signatures and an engine-override identity gap; Fable
fixed them and added finite-interval/path/churn tests. Actual second suite:
35 PASS, not the handoff's estimate36. Both delegated CLI jobs completed.

With the root-confirmed private game11120, two stable samples at14:51:24–25Z
matched the existing independent probe's position, cell1A276, world1A26F and
raw actor state0. Native Auto-Move start/stop produced coherent changed
positions in before/after JSON, with the independent probe subsequently
observing auto-move0 and zero input vectors. See the USSEP repair dossier for
bounded gameplay and preservation evidence. ReadProcessMemory only; no engine
calls or process memory writes, and no DLL/mod installed.

Before promotion: review the entire adversarial suite and live adapter,
strengthen/relabel stability checks for dereferenced cell/world data (currently
the player cell pointer is rechecked, not every nested field), compare a fresh
saved INITIAL prefix, test deployed CLI failure paths, and integrate canonical
documentation/tests. Retain candidate controls/water labels and the explicit
non-atomic/no-hard-deadline limitations. Do not replace these with another
general paper review or call this completion of #267 travel/combat acceptance.
