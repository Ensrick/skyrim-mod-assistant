# CK first: solve it the way a modder would, or say you cannot

**User directive, 2026-09-03:** *"how can I trust you aren't circumventing the
most practical methods of implementation via the CK with scripts for no good
reason? Write those rules, make sure you use the CK wiki first before trying to
write a script... writing entire C# programs to make files best managed by hand
isn't necessary."*

This exists because the assistant defaulted to code for problems the Creation
Kit solves declaratively, and kept doing it because a precedent existed. Two
concrete failures triggered it:

- Asked how to grant a bonus for wearing a full armour set, an earlier session
  advised a Papyrus `ReferenceAlias` script with SKSE `GetWornForm` calls on
  every equip event. The engine answer is **one condition**:
  `WornApparelHasKeywordCount( <keyword> ) == 4`. Two people said so before the
  assistant verified it. Record:
  `records/matching-set-perk-mechanism-2026-09-03.md`.
- `Ensrick Wolf Territorial Patch` is **830 lines of C# across 7 files** that
  emit a **3,959-byte plugin changing three numbers on nine records**. The whole
  change is four lines of YAML the project can already round-trip.

## The rules

### 1. Consult the Creation Kit wiki before writing anything

`https://ck.uesp.net/wiki/` is the reference. Before proposing a script, a
generator, or a patch, look up whether the engine already exposes a condition
function, keyword, entry point, form flag or record field that does the job.
**Name the wiki page in the record.** "I could not find a native mechanism" is
a claim that needs a receipt like any other.

Condition functions in particular are the thing most often reinvented in
Papyrus. If the question is "how do I detect X", assume a condition function
exists until the wiki says otherwise.

### 2. State the CK-native answer first, before touching a tool

Write down what an experienced modder would do in the Creation Kit for this
problem, in one or two sentences. If that answer is "one condition", "one
keyword", "one field", or "one leveled-list entry", then that is the change -
implement exactly that and stop.

### 3. If the deliverable is a file, produce the file - not a program that
produces the file

Most CK work ends in a plugin. A plugin can be authored directly:

- **spriggit YAML** round-trips a plugin to readable text and back. Editing
  `AIData: Warn: 2500` in a 131-line YAML *is* the patch.
- **xEdit** for inspection and one-off record edits.
- **SkyPatcher / KID / SPID configs** for distribution and keyword work - a
  text line, no plugin at all.

A `.NET` generator is a build system. Do not build a build system to change a
number.

### 4. Escalate to code only when the work is genuinely generative

Code earns its place when the output cannot reasonably be written by hand:

- the selection is **by rule over many records** - the wolf encounter thinning
  chooses 191 references by clustering 622 at a 2000-unit radius;
- the decision needs **measurement first** - the cloak distribution work had to
  compute a probability across 24 leveled lists before it knew what to write;
- the patch must **regenerate when upstream changes**, and the rule, not the
  result, is the thing worth keeping.

Three records with a changed field is none of those.

### 5. If it is CK-only, say so and stop

The assistant cannot drive the Creation Kit - it is a GUI, this project runs
headless, and auto-launching GUI applications is forbidden. Work that is
genuinely CK-only:

**navmesh, cell and worldspace layout, dialogue trees, facegen export, and
anything that must be seen before it is committed to.**

For those: say plainly that it is the user's to do, give a click-path of three
steps or fewer, and do **not** substitute an approximation in code. Telling the
user "I cannot do this one" is the correct output.

### 6. One generator, many policies - never one project per patch

Where generation is justified, it goes in a **single shared generator driven by
per-patch policy files**. As of 2026-09-03 there are five separate .NET
projects in `mods/` that are near-duplicates of each other; one left a 304 MB
NuGet cache that broke a commit. That is the shape to stop making.

### 7. Justify the weight in the record

Every generated artifact's `records/source-builds/*.json` states **why code
rather than hand-authoring**, in one sentence, against rule 4. A record that
cannot answer it is a patch that should be converted.

## Why this is a trust rule, not a style rule

The user is building a list to share. A modder who wants to check or adjust an
Ensrick patch should be able to open it in xEdit like any other plugin. If the
answer is "install .NET 9 and read C#", the patch is effectively opaque, and
opacity is the opposite of what a shared list needs.

Related: `docs/PATCH_INTENTS.md` (distribution classes),
`docs/CURATION_POLICY.md`, memory `feedback-ck-first-before-scripting`.
