# Read-only player observer

`player_observer.py` observes the exact Skyrim1.7.104 build using a held
read-only Windows process handle. It calls no engine function or save writer,
installs no DLL and changes no game configuration. Its purpose is to measure
what happens after controlled input, not infer success from input dispatch.

```powershell
python audit/player_observer.py OBSERVED_GAME_PID --library PATH_TO_VERSIONLIB --samples 2 --interval 0.2
python -m unittest discover -s audit -p test_player_observer.py -v
```

Choose the PID from the owned private test session. The default library path
uses this repository's sibling `mo2-instances/skyrim-se` layout; pass an explicit
path elsewhere. The actual process image is hashed and verified by
`player_layout_audit.verify`, including pinned native sites and address-library
identity. `--engine` may only restate that same resolved image path. Unknown
inputs refuse before pointer interpretation. This supports one exact runtime,
not arbitrary future Bethesda updates or patched executable files.

The report includes position plus raw float bytes, player/cell/world identities,
raw actor-state masks, per-field recheck results, timestamp, process creation
identity and consumed read/byte/sample budgets. Refusals return exit1 and a
structured error. Churn preserves before/after evidence as `DEGRADED`, not a
successful stable sample. Core cell/world data is rechecked as well as pointers.
Each stability flag compares reads within one sample, not positions across
different samples; movement or small settling between samples remains visible
in their separate coordinates and is not silently classified as stationary.
Optional `--candidate` controls/water fields are explicitly unvalidated,
single-read data; they never prove swimming, input success or water height.

Default lifetime limits are16 sample attempts,160 reads,256KiB total and1KiB
per read. Refused attempts consume the sample budget. Finite nonnegative sample
intervals are required. These bound work, **not wall-clock time**: an OS read
can block. Use an external bounded worker for unattended observation. Rechecks
cannot detect changes that revert between reads, guarantee that a first read
was fresh, or produce an atomic snapshot. No health/combat semantics are inferred
from raw state masks. Stable observations alone do not certify gameplay.

Evidence: `docs/PLAYER_OBSERVER_IMPLEMENTATION_REVIEW_2026-09-10.md`,
`docs/USSEP_MISSING_439_SCRIPT_2026-09-10.md`. Initial candidate live readings
matched the independent existing probe and an explicitly bounded saved INITIAL
prefix. Full ACHR parsing remains unsupported for that fixture; prefix agreement
is not whole-save validation. The final canonical adapter also passed a private
live run and real engine-path/read-budget refusal checks. See the review report
for exact evidence. Travel/combat remains open under #267, not automatically
passed by the tool, mock tests or a limited blocked-route attempt.

Original implementation/tests are MIT. Vendor engine/library bytes, private
saves, compiled parser artifacts and raw process reports are not distributed.
