# Texture cleanup ownership audit and execution observation

Parent #262; native texture fault #268. This supplements the chronological
[reload report](FACE_TEXTURE_RELOAD_CRASH_2026-09-10.md). It supports a narrow
native correction, not certification of the entire modpack or old campaign.

## Ownership findings

Pinned Skyrim1.7.104 executable MD5 `113faeb71fd8f62b26d0c8627299ab40`.
Read-only scan found65 functions containing a candidate count-store at+20;
five also had nearby28-byte renderer-wrapper allocation. Instruction listings
were then inspected. This heuristic is **not** an exhaustive indirect-dataflow
proof; omitted SIB stores/outlined constructors remain a stated limitation.

| Creator RVA | Owned fields on the reviewed path | Acquisition evidence |
| --- | --- | --- |
| 100D990 | resource+0, SRV+10 | CreateTexture2D output stored directly; CreateSRV output goes directly to+10; no extra AddRef |
| 100DD60 | SRV+10 only | Creates one SRV over existing renderer resource; resource/UAV fields remain null |
| 100DE60 | resource+0, optional SRV+10 | Direct factory outputs, wrapper count1; previously reviewed face/atlas factory |
| 100E080 | SRV+10 only | 1029E70 returns created SRV; direct store; no second persistent reference |
| 100E980 | resource+0 and SRV+10 | 1029E70 creates SRV; subsequent10299F0 creates a separate resource into+0; one owned reference to each |

10299F0 routes to D3D CreateTexture1D/2D/3D with caller output pointer directly.
1029E70 uses it for a temporary resource, creates one SRV, then releases the
temporary resource reference once at1029FA6. A resource field and the SRV's
underlying resource need not be identical: the model now covers both cases.
64 exact-instruction model cases pass, using the source header's bytes and
comparing its147-byte signature to the pinned executable.

Wrapper sharing helper100F180 increments **wrapper count+20 only**. The renderer
thunk1582710 forwards to cleanup100F190. Direct cleanup calls include face
43CB54 and atlas11B2356/11B3116/11B31C6. Independent actual Fable5.1 inspection
of the atlas factory/reset/destruction listings found one cleanup per stored
wrapper, no added wrapper reference or extra COM ownership in those paths.
Its possible unrelated atlas-failure leaks are unverified leads, not fixes
implemented as part of this work. Separate shader objects in that subsystem
are released once before their storage is freed.

Read-only CS source inspection found its extra texture bindings borrowing
resource-view pointers; no rendererTexture field-reassignment/allocation match
in the searched source. This is not an exhaustive audit of all installed DLLs.
No evidence was found that the duplicate cleanup triplet compensates for two
references intentionally owned by these wrappers. External holders' references
would not authorize this wrapper to release them.

## Optional observation, not a refcount oracle

Source `00b2619cd975ad4bbccee3c2bca7d42265ae0a9e` adds a separate opt-in face
call-site observer. Both CI runs34471101599/34471101607 passed. It verifies
the cleanup's full body and call43CB54 before replacing that five-byte call
with a checked relay. The native operation executes once, outside diagnostic
exception handling; no wrapper read occurs after it returns. No COM method,
AddRef or Release is invoked by the observer itself.

Logs sample calls1–8 and later powers of2. Sampled before-count1 is **not** an
atomic proof of which native refcount branch subsequently ran. A proposed
additional before-count accumulator was rejected as a final-branch oracle
for the same reason. Matched before/returned records establish actual cleanup
invocation and return for those samples, which the earlier patch-byte-only
verification could not show. Other cleanup callers are not instrumented.

## Clean observed test

Candidate BF92B81622D155E80DEA0B3B436AF3B6CB2F3F5672AF8C93412AADFC9FF1718F,
clean non-admission build, opt-in repair and observer on. Private profile
`Astra Load262 Lifetime texture-clean-probe`, PID35120/controller5180, exact
failed quicksave/co-save copied as starting input. Seven successful loads:
Continue, five F5/F9 pairs, and new Save1 journal reload; last success
06:26:55.910. All five F9 full cleanup readbacks matched. Eight sampled cleanup
invocations had readable before-count1 and matched returned records.

Unpaused movement/jump input06:28:21–24 changed player position from
(24862.389,-4551.821,-2999.7715) to(24842.88,-4355.2036,-2997.677); auto-move
returned0, candidate life state0/swimmingfalse. Normal Quit06:28:30.055;
harness completed06:28:32.282. No new private crash log. Root4E3/currencyC8ED/
logger restored and source saves/Default hashes unchanged. This is bounded
movement/reload coverage, not travel/combat or a GPU-memory leak test.

## Narrow release decision

Five reviewed native creation paths, factory-output ownership, the atlas
callers,64 exact-code model cases and the observed clean runtime support
removing duplicate releases as a native defect correction. This does **not**
prove a measured live crash-rate reduction: the earlier unpatched control
also passed. #268 and the overall #262 goal therefore stay open for broader
acceptance rather than being silently closed by this repair.

Source19d34bbbd054369c5fa89a480953a0b40d38d393 makes only the narrow repair
default-on, with SKSE.ini `[General] EnableTextureDuplicateReleaseFix=0` opt-out
and strict diagnostic environment override. Full167 signature/branch/policy
checks pass. Observer remains opt-in/off normally. The normal-build canary
and deployment result are recorded in the source-build receipt and main
reload report; do not infer deployment from this decision alone.

All source changes are in our fork; no vendor texture/mesh, SkyrimSE.exe,
original save or load-order list was edited. SKSE's upstream license remains
applicable, not MIT; no public binary release has been made.
