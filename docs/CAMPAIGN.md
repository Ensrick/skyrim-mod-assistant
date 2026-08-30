# Campaign design - four protagonists, one world

Your stated plan, mapped against what Proteus 3.4.0 and Skyrim Unbound Reborn
verifiably do (Proteus claims quoted from its page 2026-08; SUR from our
install record). Nothing here is queued without your say-so except the Bruma
install and its curator keep.

## Your four requirements vs reality

**1. "Alternate between protagonists at will without inconsistencies" - YES,
with one structural caveat.** Proteus swaps characters in the same save in
<30s, each with own appearance/perks/spells/items/stats. The caveat, straight
from its page: a character "will retain all quest progression, faction ranks,
relationships, and discovered locations" - the WORLD is shared. Quests,
faction status, and world flags belong to the save, not the character. Your
plan already survives this because each protagonist owns a disjoint questline
(DB+Daedric / Thieves Guild / MQ+Dawnguard / College). Swap discipline that
keeps it clean:
- Finish or park a questline at a quiet point before swapping.
- Save + reload after a swap (page: player name display needs it).
- Never hand inventory to a spawned copy of another character (spawns reset).
- Physics hair on swap is the known crash-sensitive path. FSMP 4.1.1 AVX and
  Vanilla Hair Remake SMP are now installed; the legacy SMP-NPC Crash Fix is
  intentionally absent because FSMP 3.0+ integrated its correction and the
  only public DLL targets Skyrim 1.6.x, not this build's 1.7.104. A foreground
  Proteus swap/hair reset smoke remains required on #27.
  (Proteus is active as of 2026-08-26: the official 3.4.0 scripts/plugin run
  with the source-built Ensrick 1.7.99 native overlay. Native registration has
  passed; extended multi-character persistence testing remains mandatory.)

**2. "Each new protagonist goes through the alternate start" - PARTLY, with a
better substitute.** The alt-start scenario (SUR, installed) runs once per
save, for character #1 only; Proteus's New Character function explicitly
creates people mid-save. The substitute found in the harvest: **Why I Came to
Skyrim (167166)** - 40 origin quests designed to run alongside any alt-start -
plus its addon **(167957)** that opens the Book of Origins ANYTIME, ANYWHERE.
Flow per new protagonist: create via Proteus at a fitting location, open the
Book, pick their origin. The Khajiit literally gets created at the Cyrodiil
border/Bruma gate (Bruma installing now) - "arrived from Cyrodiil" for real.

**3. "Choose whether they are Dragonborn" - YES at save level, PROBABLY per
character.** SUR's core feature (per our baseline note) is non-Dragonborn
characters - shout learning and soul absorption controlled by the mod. TO
VERIFY in its MCM: whether Dragonborn status can be flipped mid-save. If yes,
flipping it on swap = per-character Dragonborn, done. If no, fallback
discipline: non-DB characters simply avoid dragon kills (and with SUR the
main quest/dragons don't even start until triggered - see timeline below).

**4. "Have them kill each other" - YES, as staged theater.** Proteus can
"summon player characters as permanent followers" (an NPC copy of any stored
character) and its NPC module can set any NPC killable. A death scene = play
the survivor, spawn the victim's copy, set killable, fight it out. Then
retire the dead character in Proteus permanently. Their corpse-loot, if any,
you hand over manually.

## The four arcs, with mechanical notes

| protagonist | questlines owned | notes |
|---|---|---|
| **The villain** - Nord vampire, maybe DB | Dark Brotherhood, evil Daedric quests | The vampire-overhaul 4-way (Sacrosanct/Sacrilege/Sanguinaire/Bloodlines, all in keeps) now has a decision driver: pick the one with the best PLAYER-villain vampire arc. His "no main plots" wish is trivially satisfied - just never trigger them as him. |
| **The Khajiit thief** + Inigo | Thieves Guild complete | Created at the Bruma border (origin: fleeing a Cyrodiil bounty via Book of Origins). Dies to the villain in a staged duel; retire him after. Inigo persists in the world - he binds to whoever the player is, so his later travels with the sorceress work natively. |
| **The hero** - Nord Dragonborn | Main quest, Dawnguard | Kills the villain during Dawnguard (staged duel, then retire the villain). Triggers the MQ - which, under SUR, is when dragons START existing. |
| **The sorceress** - elf (Dunmer?) | College of Winterhold | Travels with Inigo and (pre-death) the Khajiit. Non-DB. |

## Timeline consequence worth exploiting

With SUR, dragons and the main quest are dormant until deliberately started.
So the natural act structure: Act I villain rises and Khajiit's TG career in a
dragonless Skyrim -> Act II the hero triggers the MQ (dragons return, fits the
dragons-as-late-game pillar) -> Act III Dawnguard and the two staged deaths.
The College arc floats freely.

## Action items opened by this design

1. DONE: Beyond Skyrim Bruma (Assets + Bruma + DLC Integration, v1.6.4)
   installed via headless MO2 (3 ledger entries); curator keep queued (10917).
2. Install when you green-light: Why I Came to Skyrim (167166) + Book addon
   (167957); Proteus companions it recommends that we lack: RemoveAllItems
   Freeze Fix (NFF, FSMP, and the VHR SMP hair baseline are already installed;
   do not add the obsolete SMP-NPC Crash Fix alongside FSMP 4.1.1).
3. Verify in-game later: SUR MCM - mid-save Dragonborn toggle, dragon-start
   timing options.
4. Slot decisions this design now DRIVES: vampire 4-way (villain arc lens),
   alternate-death handling for the staged kills (Proteus ships an optional
   alternate death system - evaluate during shakedown).
