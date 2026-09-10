# Excluded authors

Authors whose mods this build does not install. The list is the **user's alone**
to write: no review, audit, filter or agent may add a name, and no reviewer may
skip a mod for any reason on its own initiative. A reviewer's only job here is
to *recognise* an excluded author on a mod page and say so.

An exclusion is a distribution preference for this one build. It is not a claim
about the author's conduct, quality, or permissions, and nothing in this file
belongs in a public list, an issue, a mod description, or a message to anyone
outside this repo.

## The list

| Author | Since | Stated as |
|---|---|---|
| Elianora | 2026-09-06 | "I don't trust or use anything from Elianora" |
| Brenandvalidor | 2026-09-08 | "The author has no idea what they're doing... I already excluded the author" |
| SlavicPotato | 2026-09-10 | "Let's exclude this author, make a framework that includes our own simple dual sheath, and make our own display tweaks as well" |

## What an exclusion means in practice

1. **Nothing by that author is installed.** A mod already installed comes out,
   and its function is replaced first if the build depends on it.
2. **Reviews flag, they do not decide.** When a batch contains a mod by an
   excluded author, the review says so and stops there. The verdict is the
   user's, as with every other Keep or Skip.
3. **A replacement is built rather than borrowed** when the excluded mod was
   fixing something real. Prefer a forward of the game's own records over
   re-authoring: see `mods/inigo-bloodchill-landscape/` for the worked example.
4. **Creation Club content is out of scope.** Anniversary Edition ships 74 CC
   items, several of the `ccEEJSSE*` homes among them, as Bethesda-published
   files in the game folder. They are not Nexus mods, they cannot be removed
   without breaking AE, and a CC requirement is never treated as a blocker
   (memory `reference_skyrim_full_anniversary_edition`). Bloodchill Cavern
   (`ccEEJSSE005-Cave.esm`) stays installed; only the Nexus patch came out.

## Audit

`records/installed-mods.json` rows carrying a Nexus `modId` were checked
against the Nexus API `author` and `uploaded_by` fields on 2026-09-06:
**230 rows looked up, 0 lookups failed, 0 matches** after the removal below.
Re-run that check after any bulk install.

Brenandvalidor was excluded 2026-09-08 after the user inspected MMAT - More Merchants And Traders (190647) and found the plugin declares **every AE plugin as a master**, plus masters for mods it does not use - the signature of experimenting in the Creation Kit and uploading the result. Nothing by that author is or was installed. The mod's *idea* is wanted and is tracked separately as an open slot; the exclusion is about this author's work, not about merchants.

## SlavicPotato, 2026-09-10

Excluded while surveying the equipment-display slot.

**Two of his mods are installed and enabled, and one of them is load-bearing.**
Correcting a wrong first reading: an initial ledger check reported zero matches
because it queried a `title` field that `records/installed-mods.json` does not
have (the key is `modName`). The real result:

| Ledger row | Nexus | Enabled | What it does here |
|---|---|---|---|
| Simple Dual Sheath 1.5.9 | 50049 | yes | `SKSE/Plugins/SimpleDualSheath.dll` + ini. Left-hand weapon and staves visible while sheathed. |
| SSE Display Tweaks Official 0.5.25 | 34705 | yes | `SKSE/Plugins/SSEDisplayTweaks.dll` + ini. Owns borderless, the 119 fps limit, Havok fixed-step decoupling, WindowFocusGuard. |
| SSE Display Tweaks 0.5.16 | 34705 | no | Retained rollback only; superseded 2026-08-30. |
| Ensrick - SSE Display Tweaks Configuration | ours | yes | `SSEDisplayTweaks_Custom.ini`, our settings overlay. Depends on the DLL above. |

So exclusion rule 1 applies in its strict form: **the function is replaced
first, then the mod comes out.** Neither is pulled on the day of the exclusion.
Display Tweaks in particular carries the display configuration the whole build
launches with (issue #149), and yanking it before a replacement exists would
break launches for no gain. Both stay enabled until their replacement passes a
launch verification, and the removal is the last step of each build, not the
first.

**The exclusion is not the end of the subject.** The user wants the
*functionality*, built here: *"make a framework that includes our own simple
dual sheath, and make our own display tweaks as well... We need to be ready to
make our own version of everything he has. If possible, try to do a better
job."* That is scenario 4 of the runtime doctrine
(`docs/RUNTIME_COMPATIBILITY_DOCTRINE.md`), chosen deliberately rather than
forced by a runtime break.

His code is MIT on GitHub, so forking would be permitted. We are not forking.
An exclusion means his work does not ship in this build, and a fork ships his
work under a new name. Every replacement below is written from scratch against
CommonLibSSE-NG and the game's own structures. The upstream clone taken earlier
in this session is parked at
`skyrim-tools-source/_reference-ied-dev-DO-NOT-FORK/` and is kept only so the
*observable behaviour* and the *on-disk config schema* can be matched for user
migration. No code is copied out of it.

### What he authors, and where each one stands

| Nexus | Mod | Our replacement | Status |
|---|---|---|---|
| [62001](https://www.nexusmods.com/skyrimspecialedition/mods/62001) | Immersive Equipment Displays | Ensrick Equipment Display Framework | building, #269 |
| [50049](https://www.nexusmods.com/skyrimspecialedition/mods/50049) | Simple Dual Sheath | folded into the framework above as a built-in slot set | building, #269. **Installed** - comes out when the framework shows left-hand weapons. |
| [34705](https://www.nexusmods.com/skyrimspecialedition/mods/34705) | SSE Display Tweaks | Ensrick Display Tweaks | queued, next after #269. **Installed and load-bearing** - do not remove before parity. |

The remaining GitHub-only projects (`EquipEnchantmentFix`, `UnlimitedFastTravel`,
`SSMT_Fix`, `skee64-memleak-patch`, `OpenAnimationReplacer-IEDConditionExtensions`,
`ImmersiveEquipmentMeshGen`) have not been reviewed yet. Enumerated from the
GitHub API on 2026-09-10: 19 public repos, of which 14 are his own work and 5
are forks of upstream libraries (bullet3, imgui, nifly, reactphysics3d,
CommonLibSSE).

There is prior art on the Display Tweaks half. In August we already built
`Ensrick/SSEDisplayTweaks` branch `ensrick/1.7.99-format5` @2981fe3 as an
emergency 1.7.99 build: 26 of 26 patch sites byte-verified against the exe,
MessageBox paths converted to log-only, and the BranchTrampoline
Destroy-ownership bug fixed. That fork is a fork and does not ship under this
exclusion, but the work proves every patch site is already located and
understood, which is most of the difficulty of rewriting it.

**Folding SDS into the framework is itself the first improvement.** Upstream
ships the two as separate DLLs whose scopes overlap, and running both requires
switching features off in one of them to stop double-attachment. One DLL owns
the node tree here, so there is nothing to reconcile.

## Removals made under this list

| Date | Mod | Nexus | Replaced by |
|---|---|---|---|
| 2026-09-06 | Inigo - Bloodchill Manor Patch | [58317](https://www.nexusmods.com/skyrimspecialedition/mods/58317) | `Ensrick - Inigo Bloodchill Landscape Forward` (`mods/inigo-bloodchill-landscape/`) |

Recoverable trash for that removal:
`mo2-instances/skyrim-se/.mo2-headless-trash/20260906T195320022Z-44a3cd70f0f4-Inigo - Bloodchill Manor Patch`.
The downloaded archive `downloads/58317-240839.7z` was left in place as install
provenance; delete it only on request.
