# ECE coin-purse probability audit and owned override policy

**Audit date:** 2026-09-03

**Runtime:** Skyrim `1.7.104.0`

**Status:** the exact three-record purse repair is installed in Ensrick
Regional Currency Integration v0.2.4. Static record, arithmetic, link,
deterministic-build, and save-load smoke gates pass. A post-v0.2.4 full-profile
conflict snapshot plus runtime harvest, frequency, reset, transfer, and
duplication checks remain open under #211.

**Scope:** the three ordinary vanilla coin-purse leveled lists overridden by
Exchange Currency Enhanced (ECE) 4.1.1. Thieves Guild purses and loose placed
coins are deliberately out of scope.

**Tracking:** master [#207](https://github.com/Ensrick/skyrim-mod-assistant/issues/207);
implementation child [#211](https://github.com/Ensrick/skyrim-mod-assistant/issues/211).

## Verdict

ECE 4.1.1 has a reproducible Small-purse data defect and an incoherent payout
curve:

- `CoinPurseGoldSmall [LVLI:0D790B]` calls
  `LootGoldChange10Gold [LVLI:000954]` twice and never calls
  `LootGoldChange10Silver [LVLI:000955]`.
- Medium and Large each call the Gold and Silver helpers once, which makes the
  second Small Gold entry overwhelmingly likely to be a copy/paste mistake.
- The duplicate gives Small a 19% chance of at least one 100-value gold coin,
  a 1% chance of two, no chance of silver, a mean payout of 28.75, and a
  maximum of 221. Medium's mean is only 29.00 and its maximum is 182; Large's
  maximum is 196. Small can therefore out-pay both larger tiers.
- Replacing only the second Gold helper with Silver would repair the apparent
  typo, but Small would still average 22.50 versus vanilla's 10.75. That is not
  the pack's desired mean-neutral widening.

The pack-owned v0.2.4 integration ESPFE now overrides the three purse lists
after ECE. Each purse makes one uniform selection among 16 direct `Gold001`
value budgets. The implemented lists below preserve each vanilla mean exactly,
widen both tails in a controlled way, preserve Small < Medium < Large
progression, and let ECE's existing inventory synchronization physicalize the
result as weighted denominations.

## Audited artifacts

| Artifact | Identity |
|---|---|
| ECE archive | Nexus mod 141884, file 758183, version 4.1.1; SHA-256 `01e1c2b543ae0364fb493735f440021f93b3514b388af4e4cf34653235cd76b6` |
| ECE plugin | `exchangeCurrency_enhanced.esp`; SHA-256 `3DAAF50FB3FBA43644B7AB7E47987350F5F486F9E5D8D0A92E606E6CFF893592` |
| Vanilla master | Local Skyrim 1.7.104 `Skyrim.esm` |

The 4.1.1 archive contains one common copy of
`00 Main/exchangeCurrency_enhanced.esp`; the defect is not produced by a FOMOD
branch. ECE was serialized with Spriggit 0.41.0 and the relevant vanilla LVLI
subrecords were decoded independently from the local master. The original
probability audit changed no live-profile file; the later v0.2.4 implementation
was installed through the normal transactional path.

## Exact records and entries

### Vanilla helper lists

`LootGoldChange [LVLI:037C2B in Skyrim.esm]` has 10% Chance None and nine
equal level-1 `Gold001 [MISC:00000F]` entries with counts 1 through 9. Its
flags are Calculate From All Levels <= Player and Calculate Each Item In Count.
One invocation is therefore exactly uniform over values 0 through 9, with
mean 4.5.

`LootGoldChange25 [LVLI:04F78D in Skyrim.esm]` has 75% Chance None and nine
equal level-1 `Gold001` entries with counts 1 through 9, with the same flags.
Its payout is 0 with probability 3/4 and each value 1 through 9 with
probability 1/36, for mean 1.25.

### Vanilla purse lists

All three use `Use All` and Chance None 0.

| Purse | Record | Exact entries | Exact value formula | Range | Mean |
|---|---|---|---|---:|---:|
| Small | `CoinPurseGoldSmall [LVLI:0D790B]` | `Gold001 x5`, `037C2B x1`, `04F78D x1` | `5 + A + B` | 5–23 | 10.75 |
| Medium | `CoinPurseGoldMedium [LVLI:0D8E7D]` | `Gold001 x10`, `037C2B x2`, `04F78D x1` | `10 + A1 + A2 + B` | 10–37 | 20.25 |
| Large | `CoinPurseGoldLarge [LVLI:0D8E7E]` | `Gold001 x20`, `037C2B x3`, `04F78D x1` | `20 + A1 + A2 + A3 + B` | 20–56 | 34.75 |

Here each `A` is an independent `037C2B` roll and `B` is the `04F78D` roll.

### ECE denomination helpers

| Helper | Record | Chance None | Entries | Exact payout | Mean |
|---|---|---:|---|---|---:|
| Gold 10% | `LootGoldChange10Gold [LVLI:000954 in exchangeCurrency_enhanced.esp]` | 90% | `Gold003 [MISC:000824] x1` | 0 at 90%; 100 at 10% | 10.00 |
| Silver 10% | `LootGoldChange10Silver [LVLI:000955 in exchangeCurrency_enhanced.esp]` | 90% | `Gold002 [MISC:000823] x1`, `Gold002 x2` | 0 at 90%; 25 at 5%; 50 at 5% | 3.75 |
| Gold 25% | `LootGoldChange25Gold [LVLI:000956 in exchangeCurrency_enhanced.esp]` | 75% | `Gold003 x1`, `Gold003 x2` | 0 at 75%; 100 at 12.5%; 200 at 12.5% | 37.50 |
| Silver 25% | `LootGoldChange25Silver [LVLI:000957 in exchangeCurrency_enhanced.esp]` | 75% | `Gold002 x1`, `x2`, `x3`, `x4` | 0 at 75%; 25/50/75/100 each at 6.25% | 15.625 |

The two 25% helpers, `000956` and `000957`, have no reference anywhere else
inside the audited ECE main plugin. None of the three purse overrides uses
them.

ECE and its active SkyPatcher configuration assign:

| Item | Record | Value | Weight |
|---|---|---:|---:|
| hidden accounting tender | `Gold001 [MISC:00000F in Skyrim.esm]` | 1 | 0 |
| Copper Septim | `gold004 [MISC:000B6D in exchangeCurrency_enhanced.esp]` | 1 | 0.01 |
| Silver Septim | `Gold002 [MISC:000823 in exchangeCurrency_enhanced.esp]` | 25 | 0.02 |
| Gold Septim | `Gold003 [MISC:000824 in exchangeCurrency_enhanced.esp]` | 100 | 0.03 |

`Gold001` is intentionally the invisible value-one backend. ECE's inventory
script decomposes newly added backend value into physical copper, silver, and
gold and synchronizes the backend total to their combined value. That makes a
direct `Gold001` value budget the least coupled source representation, subject
to the runtime gate below.

### ECE purse overrides

All three use `Use All` and Chance None 0.

| Purse | Exact ECE entries | Exact value formula | Range/support | Mean | Change from vanilla |
|---|---|---|---|---:|---:|
| Small `0D790B` | `Gold001 x3`, `037C2B x1`, `04F78D x1`, `000954 x1`, `000954 x1` | `3 + A + B + G1 + G2` | 3–21, 103–121, 203–221 | 28.75 | +167.44% |
| Medium `0D8E7D` | `Gold001 x5`, `037C2B x2`, `04F78D x1`, `000954 x1`, `000955 x1` | `5 + A1 + A2 + B + G + S` | 5–82 and 105–182 | 29.00 | +43.21% |
| Large `0D8E7E` | `Gold001 x10`, `037C2B x3`, `04F78D x1`, `000954 x1`, `000955 x1` | `10 + A1 + A2 + A3 + B + G + S` | 10–96 and 110–196 | 38.50 | +10.79% |

`G` is 0 with probability 0.9 and 100 with probability 0.1. `S` is 0 with
probability 0.9 and 25 or 50 with probability 0.05 each. The two Small `G`
rolls are independent, so their combined jackpot count is binomial:

- no Gold: 81%;
- exactly one Gold: 18%;
- two Gold: 1%.

The medians are only 10, 16, and 26 for ECE Small, Medium, and Large,
respectively, compared with vanilla medians 11, 20, and 35. Typical ECE purses
are poorer; rare denomination jackpots inflate their means. The probabilities
of exceeding the corresponding vanilla maximum are 19%, 17.68%, and 15.0295%.

### Exact probability representation

The following probability-generating functions completely specify every
possible payout and its exact probability; the coefficient of `z^v` is the
probability of value `v`:

```text
A(z) = (1 + z + ... + z^9) / 10
B(z) = 3/4 + (z + z^2 + ... + z^9) / 36
G(z) = 9/10 + z^100 / 10
S(z) = 9/10 + z^25 / 20 + z^50 / 20

Vanilla Small  = z^5  A(z)   B(z)
Vanilla Medium = z^10 A(z)^2 B(z)
Vanilla Large  = z^20 A(z)^3 B(z)

ECE Small      = z^3  A(z)   B(z) G(z)^2
ECE Medium     = z^5  A(z)^2 B(z) G(z) S(z)
ECE Large      = z^10 A(z)^3 B(z) G(z) S(z)
```

This is preferable to rounding a long decimal probability table and makes the
duplicate Small jackpot explicit.

## Implemented owned override

`Ensrick Currency Integration Patch.esp` v0.2.4 incorporates the purse work in
the unified 45-record ESPFE loaded after `exchangeCurrency_enhanced.esp`. The
purse portion overrides exactly three existing records, creates no purse forms,
contains no vendor asset, and leaves all shared helper lists unchanged.

For each override:

- Chance None: 0;
- clear `Use All`;
- one level-1 entry is selected per activation;
- 16 equally weighted entries, all referencing
  `Gold001 [MISC:00000F in Skyrim.esm]`;
- the entry's count is the complete purse value budget.

| Override | Sixteen entry counts, each probability 6.25% | Range | Exact mean |
|---|---|---:|---:|
| Small `0D790B` | `2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 22, 28` | 2–28 | 172/16 = 10.75 |
| Medium `0D8E7D` | `5, 8, 10, 12, 14, 16, 18, 19, 20, 21, 22, 24, 27, 30, 36, 42` | 5–42 | 324/16 = 20.25 |
| Large `0D8E7E` | `10, 14, 18, 22, 26, 29, 31, 33, 35, 36, 38, 41, 45, 50, 58, 70` | 10–70 | 556/16 = 34.75 |

This deliberately makes the result deterministic after one ordinary leveled-
list choice: there are no nested Chance None rolls and no denomination-valued
jackpot helpers. The resulting standard deviations are approximately 6.8511,
9.6792, and 15.3806. All means remain exactly vanilla while the ranges widen
from 5–23/10–37/20–56 to 2–28/5–42/10–70.

The three purse records are overrides of Skyrim forms and require no FormID
compaction. They are part of the larger integration plugin, whose nine exact
masters are derived from all 45 serialized records and links. Explicit LOOT
metadata keeps that ESPFE after ECE and every other record source.

Do not override the three purse flora records:

- `CoinPurseSmall [FLOR:0D790C]` -> `0D790B`;
- `CoinPurseMedium [FLOR:0D8E7F]` -> `0D8E7D`;
- `CoinPurseLarge [FLOR:0D8E80]` -> `0D8E7E`.

Do not alter `LootGoldChange [037C2B]`, `LootGoldChange25 [04F78D]`, or ECE's
four denomination helpers; other records may use them. Do not alter the
separate Thieves Guild purse lists `0D8E87`, `0D8E88`, and `0D8E89` without a
separate decision.

### Fallback only if physicalization fails

First verify that harvesting each FLOR causes ECE to decompose the selected
`Gold001` budget immediately. If direct backend value remains visible, is
lost, or is synchronized twice, do not ship this design. The fallback is one
parent selection list per tier pointing to 16 pack-owned `Use All` outcome
lists made from budget-balanced physical denominations. That fallback is much
more complex, creates 51 new records, and must prove it cannot double-credit
ECE's accounting script; it is not the preferred implementation.

## Validation matrix

| Gate | Test | Pass condition |
|---|---|---|
| Static identity | Resolve `0D790B`, `0D8E7D`, `0D8E7E`, and `00000F` against the final load order | All four resolve to the audited Skyrim records; no new FormID and no missing master |
| Static data | Inspect the three winning LVLI records in xEdit/Spriggit | Chance None 0, no Use All, exactly 16 level-1 `Gold001` entries, counts exactly as specified |
| Arithmetic | Enumerate all 16 entries per tier | Sums 172/324/556; means 10.75/20.25/34.75; ranges 2–28/5–42/10–70 |
| Conflict | Regenerate winning-record conflicts after all economy mods | Owned patch wins only these three LVLIs; every unrelated field and all later intentional changes are reviewed and forwarded |
| Runtime physicalization | Activate at least 100 purses of each size in a disposable test save and inspect inventory before/after | Exactly one selected value budget per purse; no visible hidden `Gold001`; physical denominations total that budget; weight matches resulting coins |
| Runtime bounds | Log total value from every activation | Every Small/Medium/Large result belongs to its exact 16-count set; no 100/200-value helper jackpot survives |
| Runtime frequency | Run a seeded or sufficiently large automated sample | Each of the 16 outcomes is approximately 6.25%; no tier or entry is unreachable |
| Persistence | Save/load, cell reset, rapid activation, inventory transfer, and currency exchange | No duplicate conversion, lost value, stale backend balance, or repeated harvest |
| Regression | Test loose placed coins, ordinary containers, merchants, and Thieves Guild purses | Existing regional loose-coin rules and ECE physicalization remain intact; TG purses remain unchanged |
| Plugin quality | Check for errors and inspect header/masters/flags | ESP-FE flag present; no new records to compact; only required masters; no deleted/navmesh/ITM contamination |

The v0.2.4 generator/auditor satisfies the static identity, data, arithmetic,
and plugin-quality rows. The retained whole-profile conflict snapshot predates
v0.2.4, so the conflict row remains open until that snapshot is regenerated.
The five runtime rows also remain acceptance work; the save-load smoke proves
only that the installed records and scripts load without a currency-specific
error.

## Vendor-report draft

> ECE 4.1.1's `CoinPurseGoldSmall [LVLI:0D790B]` contains
> `LootGoldChange10Gold [LVLI:000954]` twice and no
> `LootGoldChange10Silver [LVLI:000955]`, while Medium and Large each contain
> one of both. With the current 1/25/100 values this gives Small a mean of
> 28.75, a 19% chance of at least one gold coin, a 1% two-gold result, and a
> maximum of 221; Medium averages 29.00 and tops out at 182. Was the second
> Small `000954` intended to be `000955`?

No indexed existing report of this exact duplicate was found during the audit;
that is not proof that no private, deleted, or unindexed report exists. The
pack-owned mean-neutral override remains useful even if the vendor corrects
the typo, because a one-entry correction alone would leave Small's mean at
22.50.

## Sources

Local plugin/master/config/script inspection is the primary evidence for every
record, entry, flag, value, weight, and probability above.

- [Exchange Currency Enhanced](https://www.nexusmods.com/skyrimspecialedition/mods/141884)
- [Creation Kit Wiki: LeveledItem](https://ck.uesp.net/wiki/LeveledItem)
