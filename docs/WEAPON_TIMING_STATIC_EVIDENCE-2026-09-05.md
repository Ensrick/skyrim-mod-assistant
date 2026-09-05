# Static weapon-timing evidence (2026-09-05)

Status: reproducible offline baseline. This is **not** a measurement of attacks
per second, successful impacts, damage, or DPS.

## Provenance and current asset resolution

- Source archive: `Skyrim - Animations.bsa`, SHA-256
  `F2E1BF18F6498D637998808A06ECF17220D17D123ECEDDBB796ECED8B68DC68A`.
- Read-only extraction: `tools/xEdit/BSArch64.exe` (BSArch 0.9c), SHA-256
  `5A8F1FD36ADB183FCF3EEC04E092F61F2AFA5E9A869AB181F81BD65A55E5B267`.
- Scratch root:
  `work/weapon-timing-static-20260905/meshes/actors/character`.
- Parser: local `HKX2E.dll`, SHA-256
  `3531833D7A7225B9427B94934DEEC8599F5C71D983C5CA26854A8DBDEC37BA20`,
  from `pandora-behaviour-engine` commit
  `6adf04b218cf4361f775e6e74e2b0e87a29efa44`.
- A case-insensitive scan of all loose HKX files below the installed MO2 mods
  found four attack-name matches. All four are XPMSE/OAR copies of
  `mlh_1hm_attackforward[Intro].hkx`, the magic-left-hand branch, not an
  ordinary sword, greatsword, battleaxe, or warhammer attack.
- The project's pure-Python BSA indexer successfully read all 77 BSAs below
  the installed mods directory: zero archive entries matched a 1HM/2HM/2HW
  attack name. Pandora Output overrides `0_Master.hkx` and magic behaviors but
  does not ship `1hm_behavior.hkx`.

On the inspected filesystem, the ordinary 1HM/2HM/2HW attack clips and the
`1hm_behavior.hkx` subgraph therefore resolve to the vanilla files. This does
not exclude runtime graph variables, perks, actor values, or a future OAR
condition changing playback.

## Reusable analyzer

`audit/weapon_timing.py` is read-only. It:

1. deserializes third- and first-person attack HKXs;
2. records file hashes, source durations, and embedded annotations;
3. serializes each `1hm_behavior.hkx` to XML in memory;
4. resolves `hkbClipGenerator` trigger event IDs through the behavior event
   string table; and
5. optionally projects source-local times through caller-supplied effective
   rate scalars.

Example:

```powershell
py -3.13 audit\weapon_timing.py `
  --character-root work\weapon-timing-static-20260905\meshes\actors\character `
  --rate onehand=1.0 `
  --rate greatsword_current=1.2 `
  --rate longsword_proposed=1.5
```

Validation performed:

- `py -3.13 -m py_compile audit/weapon_timing.py`: pass.
- `py -3.13 -m unittest audit/test_weapon_timing.py -v`: 5 tests pass,
  including non-finite/duplicate rate rejection and referenced-event-table
  resolution/fail-closed ambiguity handling.
- Full JSON generation and parse: pass.
- Default selection: 27 clips in each perspective and 34 matching behavior
  clip-generator nodes in each behavior file.
- `git diff --check -- audit/weapon_timing.py`: pass.

The JSON embeds interpretation limits. In particular, `HitFrame` and
`weaponSwing` are event **names**; neither proves collision, successful damage,
nor the time at which another attack is accepted.

## Static findings

All matching behavior clip generators have `playbackSpeed = 1.0`. Selected
source animation durations are:

| Perspective | Clip | Source duration (s) | Embedded annotations |
|---|---|---:|---|
| Third person | `1hm_attackright.hkx` | 1.300000 | none |
| Third person | `1hm_attackpower.hkx` | 1.366667 | none |
| Third person | `2hm_attackright.hkx` | 2.000000 | none |
| Third person | `2hm_attackpower.hkx` | 2.166667 | none |
| Third person | `2hw_attackright.hkx` | 2.000000 | none |
| Third person | `2hw_attackpower.hkx` | 2.000000 | none |
| First person | `1hm_attackright.hkx` | 1.466667 | `AttackWinStart` 0.833333; `AttackWinEnd` 1.466667 |
| First person | `2hm_attackright.hkx` | 2.000000 | none |
| First person | `2hw_attackright.hkx` | 2.000000 | none |

The first- and third-person behavior files expose the same selected trigger
values. Important standing-right and standing-power nodes are below; times are
unscaled source-local seconds exactly as stored in the graph.

| Graph node | Generator setup | `weaponSwing` | `HitFrame` | `AttackWinStart`–`AttackWinEnd` |
|---|---|---:|---:|---:|
| `1HM_AttackRight` | `startTime=0.333333` | 0.333 | 0.367 | 0.867–1.267 |
| `2HM_AttackRight` | `cropStart=0.333333` | 0.100 | 0.200 | 0.433–0.800 |
| `2HM_AttackRightNPC` | full clip | 0.700 | 0.800 | 1.133–2.000 |
| `2HW_AttackRightNPC` | full clip | 0.700 | 0.800 | 1.133–2.000 |
| `1HM_AttackPower_Intro` | full clip | 0.500 | 0.600 | 1.000–1.366667 |
| `2HM_AttackPower_Intro` | `startTime=0.333333` | 0.900 | 1.000 | 1.400–2.000 |
| `2HW_AttackPower_Intro` | `startTime=0.333333` | 0.900 | 1.000 | 1.400–2.000 |

The normal-attack intro nodes separately mark `InitiateWinBegin` at 0.233 and
`InitiateWinEnd` at 0.333. The analyzer intentionally does not add these times
to continuation-node times: proving the active state sequence and transition
semantics requires runtime observation. Likewise, the `NPC` suffix and absence
of that suffix are useful graph labels, not proof of which branch the current
player actually selected during a given attack.

The evidence is nevertheless decisive on one point: identical WEAP `Speed`
values cannot prove identical 1H and 2H cadence. They select different clips,
different graph nodes, and different trigger windows.

## What the approved speed change means

With the established reference-rate model:

- a one-handed sword at WEAP Speed 1.0 has reference rate `1.0`;
- a current global-patch greatsword at Speed 0.8 has two-handed reference rate
  `0.8 * 1.5 = 1.2`; and
- a proposed longsword at Speed 1.0 has two-handed reference rate
  `1.0 * 1.5 = 1.5`.

Changing 0.8 to 1.0 therefore raises that weapon's effective animation-rate
scalar by **25%** (`1.5 / 1.2`) and projects every affected source-local
interval to **80%** of its former duration. That is a reliable scalar
comparison. It is not a claim of 1.5 attacks/second, 1H-identical swing time,
or real DPS.

## Existing telemetry and launch feasibility

- `audit/launch_skyrim_isolated.ps1` does use a GUID-named Windows desktop via
  `CreateDesktop`, assigns the child to `WinSta0\\<name>`, hides its window,
  sets `SKSE_AUTOMATION_SILENT_UI=1`, and forces zero master volume in a
  dedicated `Codex Smoke - Muted` profile.
- It is not acceptance-grade isolation as written. It copies Documents INIs
  rather than a canonical isolated source, does not force `LocalSaves=true`,
  writes global `%LOCALAPPDATA%/Skyrim Special Edition/Plugins.txt`, identifies
  cleanup targets by process name plus start time rather than proven ancestry,
  and maps watchdog/controller timeout codes to success without proving a save
  loaded.
- `audit/launch_verify.py` can prove main-menu and save-load events through
  LaunchProbe, but it currently invokes the interactive-desktop launcher.
- LaunchProbe records menu/load lifecycle only. MenuPilot can automate UI but
  cannot execute an in-game console command or synthesize a gameplay attack.
- There is no installed telemetry path that timestamps repeated attack graph
  events and confirms impacts. No game was launched for this audit.

## Minimum remaining runtime protocol

Do not build a general SKSE framework for this. A future narrow, disposable
probe is sufficient once the isolated-launch gaps are fixed:

1. Subscribe to the player's `BSAnimationGraphEvent` source and timestamp at
   least `attackStart`, `weaponSwing`, `HitFrame`, `AttackWinStart`,
   `AttackWinEnd`, and `attackStop` with a monotonic clock. Treat these as graph
   events only.
2. Timestamp the injected attack input separately. To prove damage, also log a
   target hit/health change; do not promote `HitFrame` to an impact receipt.
3. For every sample, log equipped FormID, animation type, WEAP Speed, effective
   attack-speed actor value/graph scalar, perspective, stamina before/after,
   weapon reach, weight, enchantment state, relevant perks, and whether the
   actor is player or NPC.
4. In one controlled save and fixed stance, collect at least 20 normal attacks
   and 20 power attacks for: a 1H sword at Speed 1.0, a global-patch
   greatsword at Speed 0.8, and the proposed two-handed longsword at Speed 1.0.
5. Report medians and spread for input-to-`weaponSwing`, input-to-`HitFrame`,
   inter-`HitFrame`, accepted-input/recovery interval, stamina cost, and actual
   successful-hit damage. Keep misses separate.

Only that last controlled run can supply actual cadence and real DPS. Until
then, damage multiplied by the reference-rate scalar is a balancing index, not
a literal damage-per-second measurement.
