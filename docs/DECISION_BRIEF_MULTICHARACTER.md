# Decision brief - the multi-character pillar (Proteus vs the one rival found)

Your core design - several characters sharing one world, main quest and
dragons as late-game - is built on **Proteus**. The full deep-read of all
21,356 sweep survivors surfaced exactly ONE direct rival to that mechanism:

**Multiple Characters of Skyrim (186444)** - "Play as multiple characters in
the same save! Each will have their own level, perks, spells, powers,
diseases, crime, appearance, inventory and marriage." Updated 2026-08-04,
low endorsement count (young mod).

## Honest comparison, without launching anything

- **Proteus** (decided): mature framework, years of hardening, wheel/spell UI,
  known behavior with SPID/appearance mods, and the whole build was planned
  around it. Known frictions you've already accepted: it swaps within a save
  via its own bookkeeping, and heavy scripted swaps deserve save hygiene.
- **MCoS** (186444): single-save per-character bookkeeping including crime and
  marriage - the exact feature axis Proteus is weakest on paper. But it is
  young, small-audience, and untested against a 1,500+ mod load. The author
  admits "there might be some things I'm missing."

## Recommendation shape (not a decision)

Stay on Proteus - it is a pillar, not a slot, and nothing found overnight
justifies re-architecting. Treat MCoS as the documented fallback: if Proteus's
swap bookkeeping fights the final load order during shakedown, this page is
the one alternative worth an isolated-profile trial. Watching its comment
section for a few months costs nothing.

Supporting cast already harvested for the pillar (complementary, not rivals):
Save It Name It 170714 (named saves per character), Delete Saves 96261
(multi-character save rotation), Skyrim Fitting System 187128 (visual gear
independent of equipped - pairs with the Underwear.dll underlayer design).
