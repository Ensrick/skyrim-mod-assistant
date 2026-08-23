# Incident - 2026-08-23 MO2Headless install-plan path collapse

**Symptom:** MO2Headless mod-install does not honor --install-plan destination
subpaths and auto-collapses single-child source folder chains. Files land at
mod root instead of the mapped destination.

**Blast radius found:** 11 of 40 installed mods had SKSE plugin payloads at
`Plugins/` instead of `SKSE/Plugins/` (Engine Fixes, Bug Fixes, Scrambled
Bugs, Crash Logger, Display Tweaks, OAR, BOS, SPID, KID, Crafting Recipe
Distributor, Address Library). None of those DLLs would have loaded in-game -
the base skeleton's engine-fix layer was effectively OFF. Also bit the SKSE
scripts deploy twice before diagnosis (transactions 20260823T204151650Z,
20260823T204304467Z).

**Fix applied:** moved `Plugins/` -> `SKSE/Plugins/` inside each affected mod
directory (filesystem move; mod names, plugins.txt, and ledger unchanged).
Re-audit: zero misplaced DLLs; anomaly scan of all top-level layouts clean
(remaining oddities are benign readme/tool folders). SKSE 2.3.0 scripts were
separately repacked and installed correctly the same day.

**Follow-up:** upstream repo Ensrick/modorganizer has issues disabled - bug
recorded here instead. Until the controller is fixed: after ANY mod-install,
verify payload paths (the dll-location audit in this incident is the check);
prefer repacked archives with final layouts over install-plan destination
mapping.
