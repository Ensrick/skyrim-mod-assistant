# Player-observer implementation review for #267

Status: reviewed design, **not implemented**. Existing private position probes
and independently checked native/serialized layout remain the current evidence.
They are not a finished production observer or representative combat test.

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

Implementation remains queued after the confirmed USSEP package repair under
#157. No new DLL/mod or speculative input patch was installed.
