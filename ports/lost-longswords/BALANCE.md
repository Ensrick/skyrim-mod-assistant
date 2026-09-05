# Lost LongSwords two-handed balance decision

**Historical July baseline, not the current target.** The September 5 user
request supersedes this design with a proposed Speed-1.0 longsword class and
Dragonbone-reference damage 20. See
[the current comparison and approval gates](SEPTEMBER_BALANCE_PROPOSAL.md).
The old values below are still installed pending that review. “DPS” in the
original notes is a `base damage * Speed` index, not measured real-time DPS.

The original two-handed edition's weapon values are deliberately retained for the
surviving swords (12 WEAP records using 11 meshes before the new exclusions).
Its common material tiers were compared against the
installed Skyrim SE master:

- Vanilla greatswords use speed `0.70`, reach `1.30`, and stagger `1.10`.
- These longswords generally use speed `0.80`, reach `1.15`, and stagger `0.90`.
- Their lower damage nearly preserves vanilla greatsword base DPS. Examples:
  iron `13 × 0.80 = 10.4` versus `15 × 0.70 = 10.5`; steel
  `15 × 0.80 = 12.0` versus `17 × 0.70 = 11.9`; ebony
  `20 × 0.80 = 16.0` versus `22 × 0.70 = 15.4`.

This creates a coherent faster/lighter two-handed sword niche without importing the
unrelated one-handed values from the 2024 upload. Dragonbone is removed as requested.
