# Morning checklist - 2026-09-02

Written 2026-09-01 23:20 by the hardening agent for the user and the day
session. Everything below is staged and machine-verified to the launch/load
level (`records/launch-verify-20260901-231117.md`: main menu 31.3 s, save
loaded 43.5 s); nothing was judged visually. Uncommitted per team-lead
instruction - the day session commits.

## What changed overnight (read this before launching by hand)

1. **MO2 now owns the INIs for real.** `profiles/Default/settings.ini` says
   `LocalSettings=true` (it had said false the whole time; the `true` from
   08-31 went into a stray `settings.txt`, now `settings.txt.bak.v20260901-stray`).
   The game reads and writes the PROFILE `skyrim.ini`/`skyrimprefs.ini`
   through usvfs on every MO2 launch. If you change a setting in-game it
   lands in the profile copy, not Documents. `launch_skyrim.ps1` still copies
   profile -> Documents before every launch and prints which applied.
2. **New controller** `MO2Headless 0.2.0` in the instance. LOOT sorts and
   every `run` keep plugin activation by themselves now. If a tool ever
   reports `instance was last mutated by a newer controller build`, you are
   running a stale copy - use `mo2-instances\skyrim-se\MO2Headless.exe`.
3. **Work claim.** Before any install/sort/launch:
   `py -3 audit/claim.py acquire --owner <you> --purpose "..."`; `status`
   shows who holds it; `release` when done. Scripts refuse under someone
   else's claim.
4. **Light Placer is parked again, for a real reason this time**: its DLL
   cannot read the v5 Address Library the 1.7.104 runtime ships
   (`po3_LightPlacer.log`: "Unsupported address library format: 5"). Lux CS's
   LightPlacer JSONs stay inert until a rebuild-forward. OAR and CRD stay
   parked (#140).
5. Launch chain for verification is now DIRECT (`MO2Headless run ->
   headless-run -> skse64_loader`), no Steam URL; the harness variables never
   reach Steam any more (#141). Your own Steam launches are unaffected.
6. **A harness kill now refuses while you are playing** (#164, after the
   23:45 kill of your session). If you open a gameplay menu in a session the
   harness started, `launch_verify` exits 88 (`HUMAN_AT_CONTROLS`), leaves
   the game up and logs to `records/human-at-controls.jsonl`; installs and
   sorts refuse the same way while that game is alive. Agents need
   `--force-kill "<reason>"` and your say-so to override.

## Do in this order

- [ ] `py -3 audit/preflight.py` - expect clean (2-3 warnings, no FAIL).
- [ ] Launch and look (the things the smoke could not judge):
  - [ ] resolution 3840x2160 borderless, no AE upsell prompt (INI ownership)
  - [ ] skin/hair no longer plastic (#144 Advanced Skin + Hair Specular off)
  - [ ] Skyking sign posts no longer shine (#159 env-mask overlay)
  - [ ] window shadow edges softer (#151 fPoissonRadiusScale 8)
  - [ ] player no longer shoves clutter (#150 fMoveLimitMass 0)
  - [ ] 119 fps cap / cursor behaviour per #149; Windows key should now reach
        the desktop: Media Keys Fix SKSE 1.0.2 IS installed and enabled, and its
        log in the 23:11 PASS shows `SetCooperativeLevel ... setting to 0x06`
- [ ] Deploy controller **0.2.1** (downloaded to
      `mo2-builds/headless-core-33589364228-fa8cb528/`, regression 40/40 at
      23:58, NOT deployed because the smoke ran on 0.2.0): copy
      `MO2Headless.exe` (sha256 `C9753382...851B04`) into the instance root
      under the claim with the old one renamed `.bak.v6ed40ae7`, stamp with
      `plugin-disable NoSuch.esp`, re-pin `toolchain.json`, then one
      `launch_verify` PASS. Steps are the deployment table in
      `docs/MO2-HEADLESS-BUILD-2026-09-01.md`.
- [ ] Commit the hardening packages 2 and 3 (working tree; entries are in
      `CHANGELOG.md`): `audit/launch_skyrim.ps1`, `audit/launch_verify.py`,
      `audit/preflight.py`, `audit/preflight_extra.py`, `docs/INI_AND_PROFILE_STATE.md`,
      `docs/MO2-HEADLESS-BUILD-2026-09-01.md`, `records/source-builds/mo2-headless-0.2.0-6ed40ae7.json`,
      `TOOLCHAIN.md`, `records/installed-mods.json` (Light Placer row), this file.
- [ ] #142 Farming: still needs the Creations re-download (blocked by the
      native store per the 22:xx session); the two patch plugins stay off.
- [ ] Decide the 11 unledgered enabled mods (`preflight` WARN, #102) - stub
      rows or `--reconcile`.

## Still discipline, not machine-guaranteed

- Sol's session adopting the claim (the file and `AGENT_WORK_QUEUE.md` say
  how; until then a foreign `plugins.txt`/`modlist.txt` mtime means back off).
- Using the canonical `install_mod.py` (the guard refuses other checkouts,
  but only when that copy is new enough to have the guard).
- Reading `settings.ini`, never `settings.txt`, when checking by hand.
