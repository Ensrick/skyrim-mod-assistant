# Block animation intermittently fails while moving: what the build can and cannot explain

Investigation date: 2026-09-02 (late evening).

Runtime: Skyrim SE `1.7.104.0` / SKSE `2.3.1`. MO2 instance `mo2-instances\skyrim-se`,
profile `Default`, 243 active plugins.

Tracker: [#198](https://github.com/Ensrick/skyrim-mod-assistant/issues/198).
Touches [#140](https://github.com/Ensrick/skyrim-mod-assistant/issues/140) (OAR
unparked) and [#148](https://github.com/Ensrick/skyrim-mod-assistant/issues/148)
(the `fnis_aa` Papyrus gap).

**Disposition: static analysis only. The root cause is NOT found, and it cannot
be found without the user at the controls.** Nothing was installed, disabled,
reordered or configured for #198. The one launch performed today was the
verification launch for the #200/#187/#199 batch
(`records/launch-verify-20260902-231840.md`); its logs are used here as evidence,
but no launch was made for #198 and no block behaviour was exercised.

---

## 0. Two corrections to my own first pass

Both were reported to the team lead before this record existed and are corrected
here rather than quietly fixed.

1. **I said "Pandora did not regenerate the block or movement behaviour graph."
   That was wrong.** Pandora regenerates `0_Master.hkx`, the root graph that
   carries the block state machine. My first sweep used
   `find -path "*behavior*"` (lower case), which matched the two
   `magic*behavior.hkx` *filenames* and missed the `Behaviors\` directory, whose
   capital B did not match. Section 3 has the real inventory. The conclusion in
   section 2 (about OAR) is independent of this and stands.
2. **#148's `fnis_aa` signature is gone from this session's Papyrus log.**
   Section 5. That was not true when #198 was filed and it changes what row 6
   of the matrix means.

## 1. The baseline changed under this issue

#198 was observed with `Open Animation Replacer` **disabled**. It is now
**enabled** at modlist line 240, upgraded 3.2.0 -> 3.2.1, launch-verified in
`records/launch-verify-20260902-223914.md` (#140). Any retest therefore runs on
a profile that has a working animation framework for the first time, which is a
different baseline from every earlier attempt at this issue.

The team lead's first question was whether that changes #198 at all. It does
not, and the reason is specific rather than general.

## 2. Why OAR being live cannot explain the symptom

`OpenAnimationReplacer.log`, both launches today:

```
Directory cache complete: 1 OAR directories, 0 legacy directories, 164 animation hashes
```

**One** OAR directory. The build's entire OAR payload is Pandora's XPMSE
FNIS-AA conversion under
`Pandora Output - Ensrick\meshes\actors\character\animations\OpenAnimationReplacer\XPMSE\`:
**164 animations in 32 sub-mods**, across 16 FNIS-AA groups -

```
xpe_1hmeqp  xpe_2hmeqp  xpe_2hweqp  xpe_axeeqp  xpe_maceqp  xpe_dageqp
xpe_bowatk  xpe_boweqp  xpe_bowidle
xpe_magatk  xpe_magcastmt  xpe_magcon  xpe_magidle  xpe_magmt
xpe_sprint  xpe_shout
```

equip, unequip, bow, magic, sprint, shout. **There is no block group.** Across
all 164 files exactly one is block-related: `xpe_sprint_1\shd_blockbashsprint.hkx`
- shield **bash while sprinting**, not "raise shield while moving" - and its
`config.json` gates the whole sub-mod on a graph variable:

```json
{ "name": "xpe_sprint_1", "priority": 2147483618,
  "conditions": [ { "condition": "CompareValues",
    "Value A": { "graphVariable": "FNISaa_sprint", "graphVariableType": "Int" },
    "Comparison": "==", "Value B": { "value": 1 } } ] }
```

`EVG Conditional Idles`, the only other mod on disk carrying an OAR tree, is
**disabled** (modlist line 11, `-`), which is why the log counts one directory
and not two.

All 164 HKX are normally sized (smallest 9,296 bytes); none is a stub or a
zero-byte placeholder.

**Conclusion: turning OAR on adds no block animation to this build, and turning
it off removes none.** The single exception is sprint-bash, which section 5
makes newly reachable.

## 3. What Pandora actually generated

Complete output inventory, `Pandora Output - Ensrick`:

| generated | not generated (vanilla BSA is used) |
|---|---|
| `meshes\actors\character\Behaviors\0_Master.hkx` (585,136 B) | `Behaviors\BlockBehavior.hkx` |
| `Behaviors\magicbehavior.hkx` | `Behaviors\BashBehavior.hkx` |
| `Behaviors\magicmountedbehavior.hkx` | `Behaviors\mt_behavior.hkx` |
| `Characters\DefaultMale.hkx` | `Behaviors\1hm_behavior.hkx`, `shield.hkx` |
| `Characters Female\DefaultFemale.hkx` | |
| `_1stperson\Behaviors\0_Master.hkx`, `_1stperson\Characters\FirstPerson.hkx` | |
| `meshes\animationdatasinglefile.txt`, `animationsetdatasinglefile.txt` | |

So the **master** graph is Pandora's, and the block **sub-graph** is vanilla.
Rebuilding the master is what every behaviour engine does - FNIS, Nemesis and
Pandora all have to, in order to inject new states - so this is expected, not a
defect on its face.

The block wiring is present and intact in the generated master. String table,
`0_Master.hkx`:

```
iWantBlock   iWantBlock == 0   iWantBlock == 1   iBlockState   IsBlocking
IsBlockHit   IsBlockHit == 0   IsBlockHit == 1   BlockBFR      Bash_State
blockStart  blockStop  blockStartOut  blockStopOut  blockAnticipateStart/Stop
blockHitStart/Stop  blockUp  blockDown  blockLeft  blockRight
BlockStartBlendTransition   BlockBashSprint   Shd_BlockIdle   Shd_BlockIdle_1stP
Behaviors\BlockBehavior.hkx   Behaviors\BashBehavior.hkx
```

65 block/bash strings in total, including the shield-block sound events. Nothing
is obviously missing, and the merged animation data carries the expected
`1HM_BlockBash`, `2HM_BlockBash`, `2HW_BlockBash`, `Bow_BlockBash*`,
`2GS_BlockBash` set plus `BlockIdle` / `BlockHit` clips.

**The interesting part is what Pandora put IN that master.** Exactly one
third-party mod appears in the whole 2,949-string table -
`Pandora_Engine\ActiveMods.json` lists `sppffp` and `sppftp` and nothing else,
and the injected content is:

```
graph variables : SkyParkour  SkyParkourGrabVariant  SkyParkourLedge
                  SkyParkourOngoing  SkyParkourSliding  SkyParkourSpeedMult
                  SkyParkourState  SkyParkourStepLeg
states          : SkyParkour_Slide  SkyParkour_SlideStop
sub-behaviour   : behaviors\skyparkour_behavior.hkx
```

**SkyParkour is the only mod sharing the master graph with the block state
machine.**

## 4. The runtime surface

[SkyParkour v3](https://www.nexusmods.com/skyrimspecialedition/mods/117414) is
also the only mod in the build that hooks player input and the animation graph.
`SkyParkourNG.log`, this session:

```
[info] 'SkyParkourNG 3.6.3' by Tsptds / Skyrim '1-7-104-0'
[info] Installed Hooks: |Input|
[info] Installed Hooks: |AnimEvent|
[info] Installed Hooks: |NotifyGraph|
[info] Installed Hooks: |Camera|
[info] Installed Hooks: |GraphManager|
[info] Post Load Graph: Adventurer3
[info] Havok channel SkyParkourSpeedMult bound to Adventurer3
[info] Parkour: < ON >   Slide & Roll: < ON >
```

Live config, `overwrite\SKSE\Plugins\SkyParkourNG.ini`:

```
bEnableMod = true      iAutoParkour = 1     fInputDelay = 0.0
bSmartSteps = true     bSmartVault = true   bSmartClimb = true
bEnableCrouchSlide = true   bEnableAdvancedSlide = true   bEnableLandRolling = true
```

`iAutoParkour = 1` with all three `bSmart*` on means the mod decides for itself,
from movement state, when to take the graph. That is a component whose stated job
is to intercept movement input and push graph events **while the player is
moving** - which is the exact condition in the report.

The rest of the animation stack is thin and none of it touches block:
`Better Jumping SE`, `3rd Person Camera Stagger Remover`, `XPMSSE`,
`Dyn FNIS AA functions`, `Pandora Behaviour Engine`.

## 5. #148 has changed state, and it changes what sprint-block means

`Dyn FNIS AA functions` is enabled. In `Papyrus.0.log` from tonight's launch
(2026-09-02 23:18) the three signatures #148 is about -
`Static function GetInstallationCRC / GetGroupBaseValue / SetAnimGroupEX not
found on object fnis_aa` - appear **zero times**. #148 recorded 312 / 16 / 18 of
them in a single session. One different unresolved binding remains, on a
different script:

```
error: Native static function GetFlags could find no matching static function
       on linked type FNIS. Function will not be bound.
```

Scope this carefully: it is **one session**, and the 2026-09-01 logs #148 quoted
have rotated out of `Logs\Script\`, so I could not diff them directly - only
observe that the signature is absent now. Reported on #148 as an observation,
not as a closure.

**Why it matters here.** `xpe_sprint_1` - the sub-mod holding
`shd_blockbashsprint.hkx` - only applies when `FNISaa_sprint == 1`, and that
variable is set by XPMSE Papyrus through `fnis_aa.SetAnimGroupEX`. While those
calls aborted, the sub-mod could never apply and vanilla sprint-bash always
played. With the API resolving and OAR live, **sprint-bash is a state that has
newly become replaceable in this build**, and it is the only block-adjacent one.

## 5a. The regenerated master graph, diffed against vanilla

Added 2026-09-02 late, after `oar-ied-rebuild` correctly pushed back that
section 3 leaves the regenerated master unexcluded and that a SkyParkour-only
A/B would not clear it. That objection was right, so the master was measured
rather than argued about.

Vanilla `meshes\actors\character\behaviors\0_master.hkx` extracted from
`Skyrim - Animations.bsa` with `tools\xEdit\BSArch64.exe` (read-only, into a
scratch directory outside `mods\`; nothing in the build was touched) and its
string table diffed against Pandora's.

| | vanilla | Pandora | delta |
|---|---:|---:|---:|
| bytes | 580,896 | 585,136 | +4,240 |
| distinct strings | 2,891 | 2,949 | +58 |
| **block/bash strings** | **83** | **83** | **0** |

**Block/bash strings added: none. Removed: none.** The 61 strings Pandora adds
are, in full: 22 `FNISaa_*` / `FNISaa_*_crc` graph variables plus
`FNIS_XPMSE_Behavior` and `Behaviors\FNIS_XPMSE_Behavior.hkx` (the XPMSE
alternate-animation plumbing), 17 `SkyParkour*` variables, states and
`behaviors\skyparkour_behavior.hkx`, `SPPF`, `PN_StateInfo`, the two Pandora
markers `bIsPandoraGenerated` / `bIsPandoraLocked`, and 4 binary byte-runs that
are not text. The 3 "removed" entries (`D{?o`, `UUU?`, `www?`) are float and
padding patterns, not strings.

**What this does and does not prove.** It proves the regeneration adds no block
state, event, variable or animation reference, and drops none - the block
vocabulary of the master graph is unchanged. It does **not** prove the block
state machine's *wiring* is unchanged: a string diff cannot see re-pointed state
IDs, altered transition priorities or changed blend times, because those are
node data, not names.

**The practical consequence is that the two candidates collapse into one.**
Everything Pandora put into the master is SkyParkour or XPMSE FNIS-AA naming.
There is no third party in there and no "Pandora regeneration per se" content to
blame. So if the master graph is implicated at all, it is implicated *through
SkyParkour* - note in particular `SkyParkour_Interrupt`, `SkyParkour_Recovery`,
`SkyParkour_Start`/`_Stop` and `SkyParkour_TransitionStart`/`_End`, which are
wired into the same state machine the block states live in and are exactly the
shape of thing that could interrupt a block mid-movement.

That is why section 7 now has a two-step ladder instead of one toggle: step 1
tests SkyParkour's runtime hooks, step 2 tests SkyParkour's injected graph
states. Together they do clear the master.

## 6. Verdict

**Not root-caused, and not reproducible without the user at the controls.** I
cannot press block while moving; nothing in a headless launch exercises a block
state, and I did not launch over a live session (#164). What static analysis
settled is narrower and worth having:

- **OAR is ruled out** as an explanation for the symptom as reported (section 2),
  with the single sprint-bash exception in section 5.
- **The Pandora hypothesis in #198's body is not supported as written.** The
  block sub-graph is vanilla; the master is regenerated, which is normal; and
  the regeneration measurably changes nothing block-shaped (section 5a).
- **SkyParkour is the named hypothesis**, now on three grounds: it is the only
  runtime hook on input and the graph manager (section 4); it is the only
  third-party content in the generated master graph (section 3); and everything
  that regeneration added is its own or XPMSE's, so there is no separate
  "Pandora broke the master" candidate left to hold (section 5a). **Still
  unproven** - a string diff cannot see state wiring, and nothing here has been
  exercised in play.

## 7. What the user should do, and what to watch

Cheapest instrument available. Same cell, same enemy, hold block through the
whole movement each time. Record two things per row: does the shield come up
**at all**, and does it come up **late**.

| # | movement | loadout | watch for |
|---|---|---|---|
| 1 | standing still | sword + shield | control - should always work |
| 2 | walking forward | sword + shield | |
| 3 | running forward | sword + shield | |
| 4 | strafing left / right | sword + shield | |
| 5 | running backward | sword + shield | |
| 6 | **sprinting** | sword + shield | see below - this row is special |
| 7 | running forward | one-hand, no shield | does the weapon-block pose play |
| 8 | running forward | two-hand | |
| 9 | running forward | dual-wield | control - cannot block at all |
| 10 | during a jump / on landing | sword + shield | |
| 11 | **immediately after a vault, step-up or slide** | sword + shield | the row I expect to fail if SkyParkour is the cause |

Then the A/B ladder. Two steps, because step 1 alone does not clear the
regenerated master graph - SkyParkour's states stay in `0_Master.hkx` whatever
its ini says.

**Step 1 - the runtime hooks.** In
`mo2-instances\skyrim-se\overwrite\SKSE\Plugins\SkyParkourNG.ini` set:

```
bEnableMod = false
```

(or, to keep parkour on the key and only disable the automatic path,
`iAutoParkour = 0` plus `bSmartSteps`, `bSmartVault`, `bSmartClimb` all `false`).
Rerun rows 2-6 and 11. This kills `|Input| |AnimEvent| |NotifyGraph| |Camera|
|GraphManager|` while leaving the injected graph states in place.

**Step 2 - the injected graph states, only if step 1 does not fix it.** Re-run
Pandora with SkyParkour deselected (`tools\run-pandora.cmd`), which produces a
master with the FNIS-AA variables but no `SkyParkour_Interrupt`,
`SkyParkour_Recovery` or `SkyParkour_Transition*`. Rerun the same rows.

Do **not** simply disable the `Pandora Output - Ensrick` mod as the test. That
strips the 22 `FNISaa_*` variables XPMSE needs as well, leaves the SkyParkour
DLL hooking a graph whose states no longer exist, and perturbs far more than the
question asks. Step 2 is the controlled version of the same test.

Reading the ladder:

- **Shield behaves after step 1** -> SkyParkour's runtime hooks, and the fix is
  a config line, not a mod. Nothing needs installing.
- **Still broken after step 1, fixed after step 2** -> SkyParkour's injected
  graph states, and the fix is a Pandora re-run without it, or dropping the mod.
- **Broken after step 2 as well** -> neither SkyParkour nor the regenerated
  master. That exhausts everything static analysis named, and the next step is a
  crash-free bisect of the rest of the load order rather than more reading.
- **Row 6 is the only failing row** -> that is the sprint-bash state from
  section 5, and it belongs to #148, not to SkyParkour.
- **Rows 7 and 8 fail too** -> the fault is not shield-specific, which points at
  the movement graph rather than at anything block-shaped.
- **Nothing reproduces** -> it may have been an artefact of the pre-#140 profile,
  in which case say so and close it.

Restore the ini afterwards either way; it lives in `overwrite`, so it is not
tracked and a wrong value there is invisible to the audit gates.
