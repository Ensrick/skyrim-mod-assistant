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

## Removals made under this list

| Date | Mod | Nexus | Replaced by |
|---|---|---|---|
| 2026-09-06 | Inigo - Bloodchill Manor Patch | [58317](https://www.nexusmods.com/skyrimspecialedition/mods/58317) | `Ensrick - Inigo Bloodchill Landscape Forward` (`mods/inigo-bloodchill-landscape/`) |

Recoverable trash for that removal:
`mo2-instances/skyrim-se/.mo2-headless-trash/20260906T195320022Z-44a3cd70f0f4-Inigo - Bloodchill Manor Patch`.
The downloaded archive `downloads/58317-240839.7z` was left in place as install
provenance; delete it only on request.
