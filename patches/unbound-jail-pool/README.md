# Skyrim Unbound Reborn: jail candidate pool repair (candidate)

Tracking: [#263](https://github.com/Ensrick/skyrim-mod-assistant/issues/263).
**Enabled only in isolated test profiles, not Default.** One random jail start
and in-session reload passed; additional acceptance remains open. This does
not fix the old-save crash #262.

Original mod: **chinagreenelvis / lilebonymace**,
[Skyrim Unbound Reborn](https://www.nexusmods.com/skyrimspecialedition/mods/27962).
The author's Nexus permissions, checked September9,2026, allow credited
modification and bug-fix releases. Derivatives retain those permissions; do not
represent the author's work as original Ensrick work or relicense it as MIT.
Only our small source transformer is stored here; it requires the user's own
exact source and creates a separate output. Never overwrite the vendor mod.

The installed PEX SHA256 is
`af579568fc1e629127739cf5032f209204c21083249c030426ec5d448e19292a`.
Champollion1.3.2 decompilation confirms the source's all-holds jail-pool inserts
and `AfterLoadingAddons` insertion of Other. The source SHA is pinned in the
generator. Other remains eligible for ordinary non-jail starts; only its
incorrect admission as a jail is removed. No properties or persisted variables,
quest stages, locations, inventories or player preferences are changed.

Run `python prepare.py <vendor-psc> <separate-output-psc>` followed by Caprica
with Skyrim/SKSE/PapyrusUtil/Unbound/SkyUI source imports. Preserve dependencies
as read-only inputs. Output creation is exclusive; reuse is rejected.

Local candidate build: Caprica0.3.0, SHA256
`d28cddd7e476709c0daa473ad558e783c00ca8e1b0de407ddba839c55e9a3630`;
`--game skyrim --ignorecwd --enable-ck-optimizations=0` and both
`--allow-unknown-events=true --skyrim-allow-unknown-events-on-non-native-class=true`.
This compiler binds both option names to the same variable; the legacy option's
false default overwrites the new alias otherwise. W7000 for the vendor's
existing OnAdventureBegun mod-event handler is expected, not a new event.
Use absolute input/output paths (relative slash paths are treated as namespaces).

`python -m unittest discover -s patches/unbound-jail-pool -p test_prepare.py -v`
checks source gating, edit scope/uniqueness, newline handling, and a small-set
policy model. **These do not execute the PEX or prove an in-game repair.**

Required next verification: explicit non-jail location start, cold reload and
stronger deterministic invalid-selection regression. Invalid selection recovery is still a separate open
hardening item; this candidate does not add a generic safe-failure path.

September9 evidence: same-compiler disassembly has32 functions before/after,
with only SelectLocation changed; nonempty variable/property tables match
exactly (24093/29644 characters). Champollion disassembled both builds but could
not decompile either rebuild's unchanged ImportHold function (orphaned node).
That decompiler limitation is disclosed, not treated as proof of invalid PEX.
The installed vendor PEX decompiled successfully for source-logic comparison.
The candidate loaded and ran its selection in-game; see the report below.

Candidate PEX SHA256:
`4d738f3a514a2f50ff7dfa13d2595bd6968010ba2d62fee6c43bf84518ac8cc0`.
It is staged as `Ensrick - Unbound Jail Pool TEST ONLY`, with no plugin and no
Default activation. [Runtime details](../../docs/UNBOUND_START_FAILURE_2026-09-09.md).
