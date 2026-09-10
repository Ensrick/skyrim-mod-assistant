# Why a mod was skipped

**User directive, 2026-09-09:** *"Record skips I tell you to skip and tell you
why I skipped it. It may turn out I do want that mod later, but for now, I don't
think so."*

The curator store is binary by design: `keep` or `skip`, no defer. That is
deliberate and it works - 234 keeps against 4,773 skips. What it cannot hold is
**why**, so a skip that was really "not yet, and here is what would change my
mind" becomes indistinguishable from "no, never." This file is that missing
half. The decision still goes into the curator; only the reason lives here.

`skip-reasons.jsonl` is the machine-readable log, one JSON object per line:

| Field | Meaning |
|---|---|
| `modId`, `title`, `author` | the mod |
| `date` | when the call was made |
| `status` | `skip` (the curator holds the authoritative decision) |
| `reason` | the user's own words, not a paraphrase |
| `revisitWhen` | the condition that would reopen it, or `null` if there is none |
| `relatedMods` | ids this skip depends on - a patch's bases, a framework, a rival |
| `issue` | the slot issue tracking it, when the decision belongs to a slot |
| `note` | anything measured that a future reviewer would otherwise redo |

## How to use it

**On a skip:** ask nothing extra, but write down whatever reason the user gave,
verbatim. A skip with no stated reason gets `reason: null` and that is fine -
most skips are genuinely "no."

**When adopting a mod:** query `relatedMods` for its id. Anything skipped
*because* that mod was absent comes straight back. This is the whole point - a
patch skipped for a base you did not have is retrievable the moment you take
the base.

**When a slot gets reviewed:** query `issue`, or `revisitWhen`, for the
candidates already seen and set aside.

**A `revisitWhen` of `null` on a "maybe later" skip is the smell.** If nothing
would reopen it, it is not deferred, it is closed - and pretending otherwise is
how a queue stops draining.

## Query

```
py -3 -c "import json,io;[print(f\"{r['modId']:>7} {r['title'][:40]:<40} {r['reason'][:70]}\") for r in map(json.loads, io.open('records/skip-reasons.jsonl', encoding='utf-8'))]"
```
