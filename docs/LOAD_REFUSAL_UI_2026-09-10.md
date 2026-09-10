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

## Follow-up: inner ownership and reentry (07:46 CDT)

Source `fb2495b18e4358559383983c8926864fa53fc83c` replaces separate pointer-only
inner checks/snapshot lookup with one atomic, single-consumer acquisition of a
generation token and owned immutable bytes. Inner Finish now requires that
token. A rejected entry no longer closes an already prepared reader or clears
the outer invocation's save name. These are local ownership/reentry fixes, not
proof of allocation identity before acquisition or support for deferred resume.

Actual-source tests now pass **92 lifecycle checks and 103 inner-hook checks**.
A stale-inner cleanup regression failed the original pointer-only Finish.
Reinserting the original unconditional ClosePreparedLoad into the generated
inner-hook test produced a separate failure; regenerating from the corrected
source passed. Both same-generation reentry and another generation facing an
occupied reader are covered. The native reader/callback objects remain mocks.
All six request-probe CTests and the full experimental build also passed.
GitHub runs `34478155047`, `34478155023`, and `34478154972` all passed.

Actual Fable review session `ac314814-7d25-49b7-9416-7e8f6f2ba946` completed
read-only, 11 turns, exit 0. It identified the occupied-reader cleanup defect and
recommended single-consumer acquisition; parent applied and tested those fixes.
No additional agent remains running.

Runtime candidate SHA256:
`295DEBF32A6FB556D77B0773F68F66A934787BE7006AA52B1438408C2183F512`.
Private profile `Astra Load262 Lifetime inner-token`, PID7596, controller29008,
07:41:59–07:46:22 CDT. Continue, two F5/F9 cycles, a restored quickload, and a
new Journal Save5 reload yielded five successful loads at 07:43:05.503,
07:43:32.023, 07:43:47.310, 07:44:48.607 and 07:45:25.349. All five snapshots
were fully read, fault0/rejected0: 64,729 /65,384 /65,384 /65,384 /65,699 bytes.

Withholding only the generated quicksave co-save caused status6 before PreLoad.
The visible single-OK notice dismissed; player position was unchanged. The
co-save restored byte-exact (`6154AA5A1CEB15157FDABEF04E669BAB8DFC3BEDD6B05F1326AA649264D6A5A4`).
Before retry, measured movement changed position from
`(24862.389,-4551.821,-2999.7708)` to `(24843.03,-4356.7227,-2997.6917)`, with
auto-move off, no swimming/death, and controls unblocked afterward. Retrying
the same quicksave succeeded. Later Journal Save5 also reloaded successfully.
Last unpaused response was 07:46:15.261, about 50 seconds after the final load;
native Quit was accepted at 07:46:20.264. This is not a sustained-gameplay claim.

This follow-up used the normal CrashLogger configuration, **not** the earlier
isolated crash directory; minidumps and auto-open/upload remained off. No new
default-directory crash log appeared. Its existing retention setting was not
changed for this run; future crash-provoking tests should explicitly install
a no-cleanup private logger configuration before launch. Logs are archived in
`records-work/lifetime262-20260910/inner-token/`.

Original saves, source fixture and Default lists remain byte-identical. Normal
`0438215A` /`A33BF070` /`C8ED83D1` /`0A38C678` restored and independently
verified; no game/controller remains and claim released. Save5's package gate
correctly refused while the experimental currency DLL was temporarily present,
then passed after the normal reviewed DLL was restored. No policy was bypassed.
The experimental candidate is not installed for ordinary play. #262 stays open.
