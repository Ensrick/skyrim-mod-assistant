# "Ask Claude" review standard

**User directive, 2026-09-04:** *"When I use the 'Ask Claude' button on the app,
I want you to thoroughly investigate against our survey and see if the mods are
superseded, etc."*

## How a batch arrives

The button fires the extension's `relay-review` action, which POSTs the mods
visible on the current Nexus listing page to the loopback relay. The relay
writes them to:

```
%TEMP%\nlc-relay\page-latest.json     {url, mods[], reportedAt, receivedAt}
```

Each entry carries `modId`, `sourceUrl`, `author {username, userId}` and the
current `decision` (empty when unreviewed).

**The relay is a Scheduled Task, not a session job.** `NexusCurationRelay`
runs `scripts/curation-relay.py` with a logon trigger, a 5-minute watchdog and
restart on failure; `scripts/relay-ensure.ps1` registers and starts it. It died
silently at least six times while it was a background job of one Claude Code
session or an ad hoc process, which is why it no longer is.

Ensure it, from any session:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\danjo\source\repos\nexus-local-curator\scripts\relay-ensure.ps1
```

Pull the batch:

```
py -3 C:\Users\danjo\source\repos\nexus-local-curator\scripts\relay-batch.py
```

Any Claude Code session answers a batch by invoking `/ask-claude`, which runs
both one-liners, applies the rules below, and queues skips through
`scripts/queue-decisions.py`. Architecture, failure history and one-liners:
`nexus-local-curator/scripts/RELAY.md`.

The pipeline is not tied to Claude. `nexus-local-curator/scripts/ASSISTANT_PROMPT.md`
carries this standard's binding subset and the reply format for any model.
An agentic tool with a shell follows that file directly; a chat-only assistant
gets the brief from `relay-batch.py --out --clip` and its reply's `verdicts`
block is queued by `scripts/apply-verdicts.py --clipboard`. The button label
says Claude; the relay does not care who answers.

Check `reportedAt` against the current time before reviewing. A stale
`page-latest.json` looks exactly like a fresh one. `relay-batch.py` prints a
`WARNING: STALE batch` line past 60 minutes; a batch older than the user's
request means the click never reached the relay - ask for another click.

*Revised 2026-09-04 evening: user asked for the relay to be easy to attach to
any open Claude conversation. Revised 2026-09-05: made assistant-neutral so
any model can be swapped in.*

## What this is not

**This is not a filter pass.** Established 2026-08-23 and it still holds: no
exclusion-list screening, no skip-class heuristics, no scripts that decide.
Every mod on the page gets an individual judgement.

**Filters reject; they never select.** A hard filter can produce a skip. Nothing
produces a Keep except adoption: approval, audit, install, verify.

## Per-mod evaluation

Six questions, in this order. Rule 0 from `docs/CK_FIRST_DOCTRINE.md` applies
throughout: look at what already exists before forming a view.

1. **What does it actually do?** From the page description and, when it matters,
   the archive contents. Never from the title. Titles mislead - "Supports
   Skyrim VR", LOTD keyword-stuffing, and "CBBE 3BA" have each caused a wrong
   call here before.
2. **Is it current, and is it superseded?** Version, last-updated date, and
   whether a newer mod does the same job better. Supersession is the specific
   thing the user asked for. Check both directions: does this supersede
   something we run, and does something supersede it?
3. **What does the survey say?** `docs/ECOSYSTEM-SURVEY-2026-08-30.md` covers 19
   curated lists across 22 slots. Report the count where the slot exists.
   **State plainly when the survey has no slot for it** - a zero means "not
   covered" as often as "rejected", and conflating those has already produced
   one wrong answer in this project. Adoption counts measure a curator's suite
   commitment and slot budget, not fitness for this build; an additive mod's
   count is not comparable to a slot-filler's.
4. **Does it fit the build?** Against `BASELINE.md` decided slots, current
   Keeps, `SLOT_CANDIDATES.md`, and the pillars: Proteus multi-character,
   Community Shaders, CBBE Curvy + Reverie / HIMBO + SkySight, FSMP cloth-only,
   Skyrim Unbound, grounded survival.
5. **What would it cost?** Record surface and conflicts against the live load
   order, DLL version gate where applicable (PE stamp against 2026-08-21 per
   `audit/skse_version_data.py`), dependencies, and whether it forces a slot
   decision not yet made.
6. **Verdict:** `skip` / `unreviewed, worth a look` / `unreviewed, needs his
   call` - with the evidence attached. **Never a Keep from a review.**

## Skip authority

Claude may skip only for: **broken, dead, superseded**, or one of the standing
hard filters - new races, VR-exclusive, top/bottom armour separation, MCO /
BFCO / SkySA / SCAR dependency, Valhalla Combat dependency, Animated Armoury
dependency, OStim dependency, LotD-only purpose, 3BA/BHUNP/UNP-only bodies,
body-jiggle physics, glossy/flawless skin art direction. Parody and meme mods
fail the earnestness bar and are Claude's call.

**Everything else is the user's.** Sexual or skimpy content is never a reason to
skip - flag it and leave it undecided. Author-level exclusion is his alone.

## Report format

Terse, skip-first, evidence attached. For each mod: name with a **markdown Nexus
link**, version and date, one line on what it is, the verdict, and the receipt
that supports it. No background essays. Mods needing his decision go in a short
separate list at the end so they are not buried among the skips.

Related: `docs/CURATION_POLICY.md`, `docs/CK_FIRST_DOCTRINE.md`,
memory `feedback-curator-workflow-fast-verdicts` and
`feedback-curation-judge-each-mod-no-script`.
