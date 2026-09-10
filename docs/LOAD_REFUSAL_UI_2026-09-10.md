# Experimental load-refusal UI — 2026-09-10

Tracking: [#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262).
This is bounded runtime evidence, **not production admission deployment or closure
of the crash/gameplay goal**. The ordinary installed build remains `0438215A`.

## Change and verification boundary

SKSE source `5d99e8dee8fede76b38e2add6e32bb072d052d8b` adds an in-game,
single-OK explanation for experimental early load refusals. Only a copied enum
crosses the queued UI boundary; static bounded text contains no save paths or raw
external reason strings. Native errors after engine entry are not reclassified
as our early refusals. Generation gating and the previous recovery correction
remain in place.

The native message factory at Skyrim 1.7.104 RVA `9625F0` is checked against a
34-byte instruction prefix before calling its verified ABI with a null callback,
flags `0,4,10`, and one null-terminated OK button. Signature mismatch or queue
failure logs failure without a Windows-dialog fallback. `queued=1` alone does
**not** prove display: tests additionally read the actual MessageBox movie's
text, single button, and visible state, then acknowledged it and checked closure.

Experimental DLL SHA256:
`6358C8B1D0DCE100B6A734DCAB783A05683BA6336C3C0DBAFC3ED1BEC86D584D`.
It includes the generation-token follow-up from
[the recovery report](LOAD_ADMISSION_RECOVERY_2026-09-10.md), unlike the older
five-load candidate recorded there. Both SKSE CI runs `34476267044` and
`34476267011` passed. Local coverage includes 109 notice checks, 45 UI cases,
144 experimental wrapper cases, 72 lifecycle checks, and the retained normal
forwarding matrix. Native build and all six probe CTests passed.

## Controlled runtime results

Both runs used muted private QuietWorker desktops, cloned profiles, copied
inputs, and native game-menu input. No interactive desktop input or OS popup
was generated.

| Run | Result | Limits |
| --- | --- | --- |
| Original-copy refusal, 07:17–07:19 CDT | Twice selected Continue on the unchanged Adventurer3 copy. Both rejected before loading for missing `TrueHUD.esl` and `QuickLootIE.esp`. Exact reason appeared in the native one-OK box. Each acknowledgment closed the box; Main menu navigation recovered. Normal Quit at 07:19:53. | Refusal control, not a repaired or migrated campaign. |
| Healthy gameplay, 07:20–07:26 CDT | Continue, generated Save5 Journal reload, and F9 quickload all completed: three successful loads. Temporarily withholding only each generated private co-save produced two early refusals, one Journal and one F9. Both notices displayed and dismissed, with unchanged player position. Restoring each co-save byte-for-byte allowed the same save to load. | Three loads and short observation, not long-play stability. |

After the Journal refusal, closing the menu and a measured move/stop changed
position from `(24862.389,-4551.8213,-2999.7717)` to
`(24842.838,-4354.883,-2997.674)` **before another load**. Thus acknowledgment did
not merely hide a frozen UI. Following the successful F9 load at 07:25:13.849,
the process was responsive and unpaused at 07:26:25.922. Native Quit was accepted
at 07:26:30.163; the controller completed at 07:26:32.324.

All three immutable co-save reads finished with `fault=0` and
`rejected_api_calls=0` (64,729 / 66,329 / 66,329 bytes). Neither early refusal
added a PreLoad event. The isolated crash directory remained empty. Quit's
MenuPilot batch timed out as the game exited; controller completion, archived
logs, and process disappearance were checked separately rather than treating
that timeout as a crash or success oracle.

Private evidence: `records-work/lifetime262-20260910/refusal-ui-original/` and
`refusal-ui-playing/`, including SKSE, LaunchProbe, MenuPilot, currency and
Papyrus logs. These logs/saves are not distributed.

## Preservation and review

The harness verified original saves, source fixture and Default mod/plugin/order
lists unchanged after both runs. Root DLL/PDB and currency/logger restored to
`0438215A` / `A33BF070` / `C8ED83D1` / `0A38C678`; full hashes were independently
checked after the final run. No game/controller remains; the `astra/lifetime262`
claim was released. No new mod or campaign-migration choice was made.

Actual Claude CLI `claude-fable-5-1` reviewed the design read-only: session
`baa0a045-2cc6-41e3-9a38-7a417011f031`, 11 turns, terminal exit 0. Parent verified
native UI queue ordering and corrected the review's reason-source attribution.
The reported $1.34496825 list-cost estimate is not a subscription billing claim.

## Still open

- Deferred native callback ownership, cancellation and consumed-stream resume.
- Remaining pointer-identity assumptions in snapshot/finish paths; the outer
  generation token is not a comprehensive address-reuse proof.
- Supersession after enqueue and arbitrary concurrent native message stacking
  are not proven by these single-request tests.
- Production admission packaging and wider travel/combat/user acceptance.
- Original campaign decisions remain with the user; this work neither restores
  removed plugins nor cleans or migrates the original save.

Keep #262, #267 and #268 open. Do not mistake this notice for protection already
present in the normal, non-admission installed build.
