# Five-minute smoke test - 2026-08-31

Everything below landed since the last launch. Ordered cheapest-first; stop
anywhere. Launch through Steam as usual; afterwards run
`py -3 audit/launch_triage.py --max-age-min 30` regardless of how it felt.

## Main menu / immediately on load
1. **Map (ACMOS)**: open the world map - fog gone, full rotation, markers not
   clumped. Bruma/Wyrmstooth/Beyond Reach get real maps; Moonpath/Gray Cowl/
   Vigilant intentionally keep the old style until DynDOLOD roads (#81).
2. **Sound (AOS+ISC)**: draw/sheathe a weapon, cast a spell, open/close a door -
   should sound noticeably richer than vanilla.
3. **MCM sanity**: Collectibles Helper MCM exists (toggle marker classes);
   VioLens present; SkyParkour settings under the SKSE Menu Framework UI.

## Your character
4. **Hair (VHR + FSMP)**: pick or wear any vanilla hairstyle - remade model,
   sways in wind and when you spin the camera. No stretching = physics good.
5. **Climbing (SkyParkour + headless Pandora output)**: jump at a ledge or
   low wall - climb should trigger; sprint-sneak = slide/roll. If nothing
   animates, #128's generation is suspect: say so, do not troubleshoot in-game.
6. **Bloodskal Blade** (`player.additem xx01a578` not needed - COC or console
   `help bloodskal`): constant red glow, NO heartbeat pulse, no drifting embers.

## The world (Whiterun + a road out of town)
7. **Mountains (ERM)**: look at any mountain face - rounder, eroded shapes.
   Distant mountains should MATCH near ones (LOD add-on).
8. **Companions (Ysgramor via SPID, finally live)**: walk into Jorrvaskr -
   Kodlak/Skjor/Vilkas in ebony/steel Ysgramor sets, Farkas/Aela simpler sets,
   NOT vanilla wolf armor. Skyforge Steel weapons look distinct.
9. **Underlayers (SPID live)**: kill or pickpocket-strip any bandit - period
   underwear beneath, not the "garbo" default. Full nudity still possible via
   TNG when its unpark lands.
10. **Guards (Sons of Skyrim)** still correct after today's mesh churn.
11. **NPC hair**: most NPCs remade (VHR NPCs file); USSEP/CRF-touched NPCs and
    NPC-overhaul faces keep their own look - that is by design.

## If time allows
12. **Inigo**: Riften jail, cell next to the exit. Recruit; he runs his own
    system - do NOT import him into NFF's management.
13. **Fires**: unchanged for now - Embers XD is a pending decision (#123).
14. **Warhammers/Vikings/Quicksilver/Lunar/Scale Nord**: craft-only until the
    master distribution mod; forge categories Steel/Advanced show them.

Report anything off as plain observations; every system above has an issue or
ledger trail, so "hair did not move" is enough for me to act on.
