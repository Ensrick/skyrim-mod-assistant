# Weapon balancing standard

Applies to every adopted weapon mod and every regeneration of the owned weapon
balance patch. This extends [equipment intake](EQUIPMENT_INTAKE_POLICY.md), not
permission to install or redistribute an unapproved mod. Implementation and
regressions are tracked in [#239](https://github.com/Ensrick/skyrim-mod-assistant/issues/239);
Lost Longswords curation is tracked in [#237](https://github.com/Ensrick/skyrim-mod-assistant/issues/237).

## Approved baseline and terminology

The September 2026 policy uses Dragonbone as the comparison tier. **Base damage
multiplied by the WEAP speed field is a balance index, not measured damage per
second.** Never label generated index columns simply `DPS` in user reports.

| Class | Dragonbone base damage | Selected WEAP speed | Damage × speed index |
| --- | ---: | ---: | ---: |
| Dagger | 12 | 1.25 | 15 |
| Sword | 15 | 1 | 15 |
| War axe | 16 | 15/16 | 15 |
| Mace | 17 | 15/17 | 15 |
| Greatsword | 25 | 20/25 | 20 |
| Battleaxe | 26 | 20/26 | 20 |
| Warhammer | 28 | 20/28 | 20 |
| Lost Longsword, hypothetical Dragonbone | 20 | 1 | 20 |

Use these class speeds across ordinary material tiers. Do not set every iron,
steel, and Dragonbone weapon to the same index by making weak weapons extremely
fast: material progression is intentional. Exact index equality across weapon
classes is the Dragonbone anchor, not a promise for every tier.

Lost Longswords are an explicit custom category: retained weapons use speed 1
and matching vanilla one-handed sword base damage + 5. Imperial and Stormcloak
variants use the steel baseline. The hypothetical Dragonbone row is a design
anchor only; it does not authorize restoring the excluded model. The generic
speed generator must not reinterpret this category as ordinary greatswords.

## Selection and exceptions

- Resolve records from the current enabled load order and MO2 file winners.
  Exclude the generated output itself when resolving generator inputs.
- Require a recognized weapon-type keyword and a coherent weapon animation
  type. An animation enum alone is not proof of an ordinary player weapon.
- Resolve selector FormKeys against actual record identities in tests. Material
  keywords, especially `WeapMaterialSteel`, are not creature exclusions.
- Default-deny unclassified records. Report them for review; do not silently
  normalize test weapons, invisible attacks, improvised tools, or creature gear.
- Preserve reviewed signature speed exceptions, including Ebony Blade and
  Longhammer. Record exact FormKeys and reasons; unique names alone are not a
  reliable machine selector. New ambiguous exceptions remain decisions.
- Give custom categories explicit per-record or plugin-scoped rules. A newly
  adopted weapon pack cannot be considered balanced merely because the
  generator completed without an exception.

## Field ownership and distribution

The generic patch changes **Speed only**, forwarding every other field from
the current input winner. Intentional damage changes, recipe changes, and
distribution belong to separately reviewed rules/overlays with exact field
assertions. Do not erase enchantments, scripts, critical effects, tempering,
keywords, reach, weight, or other authors' compatibility fixes accidentally.

Compare weight, power-attack stamina use, reach, stagger, enchantment hit rate,
flat damage bonuses, perks, and improvement scaling separately. Speed alone
does not prove stamina efficiency or comprehensive combat balance. Faster
weapons apply per-hit bonuses more frequently, even at equal base indices.

Distribution requires a role and graph audit, not a successful plugin write.
For this longsword integration guards remain excluded. The user's subsequent
approval permits only the Imperial longsword for Imperial soldiers and only the
Stormcloak longsword for Stormcloak soldiers, at a modest native-comparable
share of two-handed choices. Other longswords stay out of military pools.
Shared lists and templates must be traced, not just lists named `Guard`.
Resolve inventory inheritance flags and outfit contents from current winners;
an NPC's raw inventory is not necessarily the inventory it inherits at runtime.
When a desired list also feeds excluded actors, isolate the smallest branch
and redirect only reviewed actor templates. Preserve the remaining equipment
and selection probabilities. Split early compatibility restoration from a
later dependent integration plugin if their master/load-order requirements
conflict; do not falsify masters or copy unrelated records to force one plugin.
Suppress unwanted acquisition paths without deleting or compacting vendor
forms. Existing saved inventories are not automatically purged.

## Generation and installation gates

1. Record generator source/version, policy hash, ordered enabled input plugin
   hashes and their winning paths, output hash, and selection/exclusion counts.
2. Rebuild after any relevant input/order/rule change. The freshness check must
   detect stale inputs, not accept a timestamp or a successful historical run.
   Keep generated-output identity checks separate from the input fingerprint.
3. Test exact Dragonbone anchors, steel inclusion, creature/tool exclusions,
   custom-category precedence, unique exceptions, non-Speed preservation,
   resolved masters/links, and light-plugin safety. Compare deterministic
   regeneration. Preserve original FormIDs; do not compact vendor records.
4. Install through the claimed headless workflow, keeping vendor payloads
   separate. Update the ledger, issue, receipt, and applicable Keep entry.
   Owned patches are not fabricated Nexus mod IDs; Oldrim IDs are not SSE IDs.
5. Check the **final winning fields**, not only the contents of the generated
   patch. Resolve load-order dependencies and downstream overrides explicitly.
   Respect the engine's master-before-regular-plugin ordering: a master-flagged
   USSEP cannot be moved after an ordinary ESP to recover lost fixes. Forward
   reviewed overlap in an owned compatibility layer and preserve later winners.
   Inspect active runtime weapon rules too; a plugin-only winner audit cannot
   prove what SkyPatcher, scripts, perks, or native hooks do after loading.
   Validate runtime configuration selectors/actions against the installed
   parser, not only against the generator's own expected text. Require bounded,
   nonempty selectors unless an all-record operation was explicitly reviewed.
   An ignored unknown selector must never become an accidental catch-all.
6. Keep static verification and runtime verification separate. No surprise
   launch: follow [background testing policy](BACKGROUND-TESTING-POLICY.md).

## Measured cadence and calibration

Skyrim's animation state and transitions affect the time between successful
hits. A record's speed field is a multiplier, not attacks per second. The
two-handed animation multiplier is also not an independently measured hit rate.
Do not multiply an index by it and present the result as real DPS.

A reproducible measurement records game/build and animation configuration,
actor attack-speed modifiers, perspective, attack sequence, target state,
successful hit timestamps, damage, and stamina before/after. Measure sustained
normal attacks and power attacks separately, with documented warm-up and
recovery boundaries. Keep shield, dual-wield, player, and NPC tests distinct.
Control perks, enchantments, buffs, difficulty, regeneration, and target armor;
repeat trials and report the spread. Animation/config changes invalidate timing
calibration even when no WEAP record changed.

Measured throughput is total damage delivered divided by the stated elapsed
combat window. For a relative raw-damage target, a useful reference is the
measured Dragonbone sword hit rate at speed 1: compare ordinary one-handed
weapons to `15 × reference hit rate` and two-handed weapons to
`20 × reference hit rate`. This does not assume the reference hits once a second.

If measured cadence cannot simultaneously honor longsword damage 20, speed 1,
and the desired cross-class throughput, report that conflict with measurements.
Do not silently break the approved anchors or modify animation globals. Ask
which constraint to relax before a new calibration changes the intended feel.

Until those trials exist, the installed policy is **record-index balanced;
actual cadence, power-attack efficiency, and gameplay feel remain unverified**.
