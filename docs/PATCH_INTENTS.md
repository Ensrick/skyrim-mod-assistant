# Patch intents - mods kept for a custom patch, not for a stock install

Mods land here when the user wants the ASSETS or IDEA but the mod as shipped
would not survive the build's existing decisions. Each entry records what the
mod is, why the stock install does not work, and what the user actually intends
to do with it. Without that last part a keep months from now looks like a
mistake and gets reverted.

This is a working queue, not a commitment: nothing here is installed, and an
entry can be dropped once the user decides the payoff is not worth the patch.

Format per entry: what it ships, why stock fails, the intent, and the concrete
patch work that intent implies.

---

## Skyking Guard Shields - Complex Parallax and PBR (189146)

Kept 2026-08-26. v1, released 2026-08-21.

**What it ships.** A from-scratch rebuild of the vanilla hold-guard shields:
new meshes and textures for all nine holds plus the blank/Stormcloak shields,
in Complex Parallax and PBR variants. Replaces vanilla paths under
`meshes\armor\stormcloaks\shield*.nif` (verified from the archive: 39 payload
files, all under `PBR\meshes\armor\stormcloaks\` and its texture tree).

**Why a stock install does nothing.** Sons of Skyrim (68656, installed and
enabled) is the decided guards/Stormcloaks overhaul. It adds 26 new shield
records pointing at its own meshes under
`Meshes\NordWar\SonsOfSkyrim\<Hold>\Shield*.nif` and rewrites the guard outfits
to use them, so the guards you actually see never render the vanilla shield
meshes Skyking replaces. It does override a few vanilla records (Whiterun and
Winterhold guard shields, MS06 quest shields) that keep vanilla paths, so a
handful of Skyking shields would show - a rounding error, not a reason to
install. Second blocker: Complex Parallax and PBR both need Community Shaders,
which is parked with no 1.7.99 build, so the headline feature cannot render
today regardless.

**User intent (2026-08-26).** "If I like them enough, I can find a way to get
those textures/models mixed in with Sons of Skyrim." The shields are wanted as
ART, to be married to the Sons of Skyrim guard system rather than installed
alongside it.

**What that patch would take.** Three routes, cheapest first:

1. *Redirect* - point Sons of Skyrim's shield ARMO/ARMA records at Skyking's
   meshes. Cheapest (a plugin-only patch, no asset work) but it discards Sons
   of Skyrim's per-hold shield designs, which are a large part of why that mod
   was chosen. Only sensible if the user prefers Skyking's shapes outright.
2. *Reskin* - keep Sons of Skyrim's meshes and author PBR/parallax textures for
   them using Skyking's material work as the reference. Preserves both mods'
   intent and is the likely "mixed in" the user means, but it is real texture
   work, not a patch, and it only pays off once Community Shaders is unparked.
3. *Coexist* - install Skyking only for the vanilla shield records Sons of
   Skyrim does not override. Nearly free, but the visible payoff is the few
   shields noted above.

**Gate.** Do not start any of these until Community Shaders ships 1.7.99
support; without it the PBR path is unrenderable and route 2 cannot even be
evaluated on screen. Revisit at CS unpark.
