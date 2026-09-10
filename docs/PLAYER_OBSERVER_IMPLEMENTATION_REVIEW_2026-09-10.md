# Player-observer implementation review for #267

Status: **canonical read-only observer implemented and live-tested**, with
41 adversarial tests and a CI step. Existing independently checked native/
serialized layout remains the authority. This is not travel/combat acceptance.

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

## Final implementation and acceptance

Fable's third bounded refinement (same session,11 turns, no running job left)
added same-address cell/world header/flag/world-pointer rechecks and preserved
changed nested data as DEGRADED evidence. The sample budget now spans an
Observer lifetime, including refused sample attempts. Root reviewed the code
and tests, corrected canonical relative paths and refused non-integer/boolean
sample counts, and promoted original source to `audit/player_observer.py`,
`audit/test_player_observer.py` and `audit/player-observer.md`. All41 tests pass.
The Windows workflow now runs the suite. No in-process code was installed.

The original Java consumer, recompiled against pinned FallrimTools source,
independently read fresh Save4's27-byte INITIAL prefix: cell/world1A26F and
position(24876.596,-4695.499,-3003.0457), matching the earlier observer/probe.
It explicitly reported fullAchrParsed=false, prefixOnlyMode=true and unchanged
input bytes. This is limited coordinate agreement, not whole-save health.

Final canonical live adapter: owned private game29728, profile
`Astra Observer267 Final 20260910`, copied post-USSEP Save5, normal F743/4DAB
runtime pair. CLI engine override to an unrelated source file returned
`engine-path-mismatch`; zero read budget returned `budget-exhausted` with
reads0/bytes0. An absent PID returned a structured OpenProcess refusal. Real
samples before movement and after Save6 reload succeeded with16 bounded reads
for two samples, all core stability checks true. Candidate controls/water
remained off in the canonical report; independent legacy probe observed
auto-move0 and zero vectors after input stopped.

**The attempted adjacent-cell route did not pass.** Before position was about
(24826.992,-4226.014,-2996.457); after the native Auto-Move start/stop pair it
was about(24817.338,-4215.558,-2996.350), still cell1A276/world1A26F. The new
Save6 embedded preview visibly shows a large tree directly ahead. This is
consistent with obstructed movement, not proof of the collider or a broken
input handler. No cell crossing or combat certification is claimed. Do not
silently disable trees, teleport, change collision or install a movement mod
to make this test pass; select/observe a valid route in subsequent work.

Raw JSON, refusal reports, save preview and runtime logs remain private under
`records-work/observer267-final-20260910/`. Retain the explicitly asynchronous,
non-atomic/no-hard-deadline limitations. Recheck flags describe within-sample
consistency, not an assertion that different samples have identical positions.
#267 travel/combat and overall #262 remain open.

Final controller24892/game29728 ran10:03:15.079–10:09:25.971 CDT and exited0
after native Journal Quit. PostLoad successes were10:04:23.027 and10:08:09.056;
final unpaused ping10:09:18.801 was69.745 seconds after the latter. All pinned
original/fixture/Default/root/41overlay checks passed, normal logger restored,
no protected crash report or owned game/controller remained. Combined local
layout/observer suite:49 PASS (8 layout+41 observer). This completes the bounded
observer implementation checks, not the remaining travel/combat criterion.
