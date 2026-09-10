# Exact-save Papyrus crash diagnosis — September 10

[#262](https://github.com/Ensrick/skyrim-mod-assistant/issues/262) remains OPEN.
This establishes the failing memory access; it is not a campaign repair or
gameplay acceptance. No production fix was installed during this investigation.

## Evidence chain

The original Adventurer3 autosave was inspected read-only, then copied to a
fresh isolated profile for one muted QuietWorker reproduction. Original files:

- ESS SHA256 `ED8255CD464F8E17BA19AAD5F2154549D9BFF51CCC5FB8165473FD26FB1EF8F9`.
- Co-save SHA256 `E708EC7CE1B7CC384A4E676E2A52A41DCC668BA235D5FD0FD30571AF9E27A1CF`.

The new bounded SKSE inventory reports a nondynamic TrueHUD event handle
`0000FFFFFE051800` for `SKICP_configManagerReady`. The actual September9 crash
log maps saved plugin index `FE051` to missing (`255`), as it should. QuickLoot
is similarly mapped to missing. The SKSE restore implementation skips these
unresolvable registrations. A bad plugin-index remap is therefore not supported
by this evidence.

A source-built, headless FallrimTools consumer then parsed the original ESS:
7,787 script definitions, 76,568 instances, 91 active stacks, three suspended
stacks and 87 pending function messages; no reported truncation/parser failure.
Input hashes remained unchanged. Crucially:

- Saved TrueHUD_MCM instance `0000021f32e54640`, form `FE051800`, has25 variables.
- Saved `_configID` is integer18 at member index5, with matching descriptor.
- Active stack `0002c6a3` already contains `TrueHUD_MCM.OnConfigManagerReady`
  and `MCM_ConfigBase.OnConfigManagerReady`, both owned by that instance.
- A pending message for the same stack is `TrueHUD_MCM.LoadConfig`.

The saved call can resume independently of SKSE's restored event registrations.
Removing an event registration would not remove that already-saved call.

Parser source: [FallrimTools](https://github.com/mdfairch/FallrimTools), Apache-2.0,
pinned `61bb57d895f023617cb55045a4907849fd1ff566`; source-compiled with Java24.
Our consumer calls no save writer or cleaner. Its README documents dependencies
and an upstream array-label display defect that the consumer avoids. Parser
success alone does not certify compatibility with the live game.

## Actual memory capture

Game PID28776, thread4676; the same native stack reproduced after selecting
Continue, accepting the missing-content warning and explicitly choosing the
**current** load order. No removed plugin was restored. Fault occurred at
01:39:59 CDT; CrashLogger's header says01:41:22 after writing the large dump.
Engine1.7.104 MD5 `113faeb71fd8f62b26d0c8627299ab40`.

| Observed field | Value |
| --- | --- |
| Fault | SkyrimSE+09C00FC, array reference-count release |
| CodeTasklet / frame | `204B6A95AD0` / `204B6853C04` |
| Self object | `203B2CFF130` |
| Destination Variable (RDI) | `203B2CFF1B0` |
| Destination index | `(RDI - object - 0x30) / 16 = 5` |
| Self type info | `204B676D800`, name `TrueHUD_MCM` |
| Type parent / metadata pointer | Both null |
| Type state / variable count | Linked-invalid2 / zero |
| Invalid value being released | `20300000001` |

The pinned executable's variable-name lookup at1493090 independently confirms
the type layout: variable count is `(type+0x20 >>8)&0x3FF`, parent is+0x10,
and linked-valid is3. The captured type has count0 and no parent. The resumed
instruction nevertheless addresses member5 using unchecked native arithmetic
at14D59F1–14D5A03. Its failure/default path later treats unrelated memory at that
address as an array and attempts to decrement the invalid pointer.

**This proves a member access outside the receiver's runtime variable layout.**
It does not independently establish the engine heap allocation header/size or
the entire missing-type loader mechanism. The object's saved layout was25
variables; its runtime placeholder is empty. Earlier hypotheses of an index
remap, direct deterministic scalar/array restore mismatch, or a necessary
concurrent writer are no longer needed to explain this observed failure.

Fable5.1 independently traced the native resolver/caller. It corrected its own
earlier intermediate-addref and empty-variable-name interpretations. Parent
checked the actual memory and pinned executable; inference is not substituted
for the dump evidence.

## Preservation, cost and next work

The diagnostic-only CrashLogger setting and log destination were restored
byte-for-byte (SHA256 `0A38C67861A8BFAFD6640EB8D05398060ECF170621EB7FE2DF368AEB9A5C58DB`).
Cleanup was disabled for the private capture, so existing logs/dumps were not
deleted. Original ESS/co-save hashes remained unchanged. No DLL swap, mod
installation, profile load-order change, or save write was performed. The
owned controller exited0 at06:41:27UTC; that exit code means process cleanup,
**not test success**. Game is closed and the profile claim released.

One private dump is17,746,335,113 bytes (~16.5GiB), not uploaded or committed.
Keep this one root-cause artifact; do not create duplicate dumps casually.

- Dump SHA256 `33E759AC5E82217A7D51B28AF1B6049D25E03C7621F19CE6CA03A77B4D040923`.
- Crash log SHA256 `DFED9D19491A7206EC2D186D298A62061E79999CE6A1042E795C203A6784752D`.
- Read-only ESS inventory SHA256 `68CDB0775E8A37A2B64901D122B6D4C1DD4833C840C3355ADF2E0D35A74D2061`.
- Private artifacts: `records-work/mcm-dump-20260910` and
  `records-work/original-papyrus-inventory-20260910-v2.txt`.

Next: validate the resolver's existing failure contract, add a narrowly pinned
bounds check that never dereferences/defaults an invalid destination, and test
the exact copied save plus valid member accesses. No save cleaning, substitute
scripts or reinstated mods. Passing this fault is still not permission to call
the campaign healthy: missing content, currency checkpoint compatibility,
load/save/reload and sustained gameplay acceptance remain separate obligations.

Follow-up contract review: destination resolver14D58F0 returns bool and has
two flag outputs plus a fifth argument (`Variable**`). Its caller14D45C0 skips
all destination reads/defaults when that bool is false and flags are zero.
However, the opcode handler at14CEA60 ignores14D45C0's returned bool, destroys
its temporary source value and continues. **Do not claim a false return aborts
the whole saved script.** Member reads use14D54C0 and need separate inspection;
a write-only check could expose another invalid read. Operand kind7 stores its
encoded member index at+4 (native14A2240); actual member index is encoded-2.
Fable's proposed function-entry detour is a review suggestion, not implemented
or accepted wholesale. A smaller verified call-site hook remains an option.

## Paired guard implemented and tested (subsequent work)

The preceding next-work paragraphs describe the pre-implementation checkpoint.
SKSE source `f81abcc4e0bd8470389ee5f85068dd0aa231484b` now guards BOTH member
reads at14D54C0 and destination resolution at14D58F0. It checks complete inherited
variable counts before the engine calculates a slot. Unknown/unreadable layouts
forward unchanged; known out-of-range accesses use the existing failure return.
No save data, object refcounts or missing script definitions are rewritten.
Both complete prologues are signature-checked before installing whole-instruction
forwarders. Fifty native policy checks and both full-build/Windows-Linux CI pass
(runs34447827157 and34447827098).

Tested candidate SHA256:
`B3E411A66B2F6C7DDB06BD6849FAF440656A76AEE82CD587B06FAC7D6A32A0A4`.

| Test | Actual outcome |
| --- | --- |
| Exact original, cold Continue | Loaded at01:56:58.206 CDT; 3 member reads and1 write rejected, all TrueHUD_MCM with zero runtime variables. |
| Exact original, Journal reload | Loaded at01:59:09.655; same four rejects; responsive after130.7s; normal desktop exit. No save written. |
| Compatible Save7, cold Continue | Loaded at02:03:41.736; currency checkpoint accepted; zero member rejects. |
| New Save8 and Journal reload | New save passed currency gate; reload admitted at02:04:56.002; zero member rejects. |
| F5 quicksave and F9 quickload | New quicksave passed currency gate; reload admitted at02:05:56.979; responsive and normal desktop exit; zero member rejects. |

Each session used a copied input, actual engine menu input on the muted private
desktop, and restored the installed DLL/PDB and CrashLogger configuration after
exit. No new private crash report was generated. Evidence directories:
`records-work/load-request-20260909/automatic-recovery-member-original` and
`automatic-recovery-member-healthy`. Original save hashes remain unchanged.

**Limits:** the old save still receives the correct missing-native-currency-ledger
refusal, and removed TrueHUD native methods still produce handled Papyrus errors.
Passing its previously crashing instruction is NOT old-campaign recovery, save
compatibility, or sustained gameplay certification. Issue262 and the overall
goal remain open. No old-campaign migration has been authorized.

Fable5.1 session`be49bad5-5784-4267-946c-94f92c5aa8a9` reviewed the implementation
read-only. Parent checked its findings against actual memory and disassembly:
its proposed type-name offset+0x18 was wrong (+8 is proven and produces the
correct runtime name), and14D66D0 checks type classification, not handle validity.
Those suggestions were not adopted. No blanket independent approval is claimed.

Source`e843ba3` makes this narrowly scoped guard default-on with SKSE.ini
`[General] EnablePapyrusMemberBoundsCheck=0` as diagnostic opt-out. A fresh release
build with experimental admission linkage disabled passed separate runtime
verification and was installed locally at02:21:44 CDT. Exact receipt:
`records/source-builds/ensrick-skse-member-bounds-1.7.104.json`.

Release DLL SHA256
`4E3F618B6A413B6EA3C38E238EBC607E056EEBFC34ED72073DD46BEEA7BD7184`.
Both CI workflows for exact sourcee843ba3 passed (34448891724,34448891712).

- Original Continue02:14:42.289, Journal reload02:15:29.550, each3 reads/1 write
  rejected on empty TrueHUD_MCM, responsive02:16:17.889; normal exit02:16:25.170.
  Currency refusal on both loads remained intact. No old-save write.
- Compatible fixture with optional load diagnostics OFF: Continue02:18:05.288,
  new Save8 with valid checkpoint, Journal reload02:19:02.357, F5 valid
  quicksave, F9 reload02:19:42.302; all three currency admissions completed.
  Zero member rejects, responsive02:20:53.174, normal exit02:20:59.594.
- Both hooks logged installed/default-enabled in both sessions. Evidence:
  `automatic-recovery-member-release-original` and
  `automatic-recovery-member-release-healthy` under the same private root.
  No new private crash report; CrashLogger configuration byte-restored and
  original ESS/co-save hashes checked unchanged after these runs.
- Permanent deployment changed only our game-root SKSE DLL/PDB after all owned
  game/controller processes ended. PreviousCC2F DLL and matching PDB remain in
  `records-work/load-request-20260909/before`; installed hashes match the tested
  pair. No new Nexus mod, Keep change, vendor asset edit or original save change.

This is empirical repair of the demonstrated member-access fault, with bounded
regression evidence. It does not close issue262 or the user's full crash goal.
The experimental save-admission lifecycle, missing-content decisions and
representative gameplay still require work.

Final normal-profile preflight still reports the SAME four preexisting blockers
documented in `MENUPILOT_STRING_REPAIR_2026-09-09.md`: weapon input order/winner
proof stale and three cloak fingerprint/proof failures. The earlier reconciliation
found FuzzBeed Resources/Thanedom exchanged at115/116 plus four CLLF folders;
this deployment did not reorder or regenerate them. Default lists have write
timestamps from September9, before these tests. Our isolated source also includes
the test-only Unbound jail pool and omits Default's enabled CLLF-CRF folder (its
ESP is inactive). Thus these runs are **not exact-current-Default gameplay proof**.
Do not tell the user to launch based on this report. Existing CRF/Lux CELL warning
and five ledger gaps remain separate tracked work. The root-DLL change warning
is expected and explained by the new exact receipt, not silently baseline-reset.

Subsequent reconciliation: the four stale proof blockers were repaired by
regenerating against the unchanged active plugin bytes/current order. Weapon
ESP/27 sidecars and all240 cloak directives remain byte-identical. Normal
preflight now has zero blockers; no new gameplay test is implied. See
`PATCH_PROOF_RECONCILIATION_2026-09-10.md` for exact transactions and remaining
warnings. This supersedes only the stale-proof status in the preceding paragraph.
