# Adventurer3 recovery requires approval

September10, 2026. #262 remains OPEN; the crash goal is not accomplished.
Safe load refusal is installed, but refusal is not recovery of the campaign.

## Read-only census of preserved saves

The current Default plugin list and installed currency package were pinned
before inspection and rechecked afterward. No save was loaded, rewritten,
cleaned, or selected as a replacement campaign.

| Ordinary character saves | Count | Plugin-presence pass | Currency-checkpoint pass |
| --- | ---: | ---: | ---: |
| Adventurer | 10 | 0 | 0 |
| Adventurer2 | 4 | 0 | 0 |
| Adventurer3 | 18 | 0 | 0 |
| Test | 6 | 6 | 0 |

All38 ESS/co-save pairs still match the September9 22:33 backup byte-for-byte.
All five repository backup directories were also inspected:
`20260907-204255`, `20260907-210119`, `20260908-223519`, `20260909-020354`,
`20260909-223317`. Their190 ESS/co-save pairs contain three additional unique
pair variants, all Adventurer3, beyond the ordinary-save census. **No ordinary
or backup pair passed current admission.** This covers the named local sets,
not every storage device, cloud backup, or file that might exist elsewhere.

Every inspected pair lacks the required native currency v2 checkpoint. This
is not proof that the saves are corrupt or simply too old: failed historical
bridge initialization/serialization can also leave a checkpoint absent.
The four latest ordinary Adventurer3 saves, including the reported crash input,
also reference removed TrueHUD.esl and QuickLootIE.esp. The older fourteen
reference Eli_InigoBloodchillPatch.esp, BowOfShadowsFix.esp and QuickLootIE.esp.
The three additional backup variants have one of those same missing sets.

Original failing ESS remains `ED8255CD...BF1EF8F9`, co-save
`E708EC7C...E27A1CF`; both full hashes were rechecked. All files and current
installation inputs were unchanged during both censuses. Admission proves
only the named compatibility conditions, not Papyrus integrity or gameplay.

## Decision needed before actual campaign recovery

Authorize a **separate-copy recovery attempt** that can restore the removed
dependencies appropriate to the selected save and explicitly migrate its
currency state. The original saves stay immutable. Restoration compatibility,
currency accounting, saved script state, repeated loads and representative
gameplay would still need verification; approval would authorize an attempt,
not guarantee recovery. It would not authorize arbitrary save cleaning,
deleting script instances or resetting quests.

Alternatively, the user may explicitly choose a fresh replacement campaign.
The existing disposable fresh-character fixtures are not silently being made
the user's campaign. That choice does not retroactively repair Adventurer3.

The same permission boundary was recorded in the preceding two goal turns
(`TRAVEL_INPUT_LIMITATION_2026-09-10.md`, commit899f0b7;
`MOUSE_LOOK_EXPERIMENT_2026-09-10.md`, commitsc24b836/3235c46) and persists in
this third turn. Those turns made bounded test progress but did not grant
restoration/migration authority. The preserved-save census now rules out an
admissible candidate in the available original/backup sets. Further controller
experiments on a different character do not resolve this decision. Do not
continue such experiments as a substitute for repairing the actual failing
input, or mark #262 complete based on their success.

Private audit reports remain under records-work, SHA256:
ordinary census `11BDF448EF8146FC6B5111BFF08B0C0BA2B9356E3D482087FFE58F91E4BD5D88`;
backup census `2FC0032A834FDDDB604801B0FB620544760F58232717E49CD347FE529B481348`.
No game/controller, delegated agent or instance claim was needed for this work.
Latest current-head CI34497749708 and earlier CI34497726093 both passed;
neither run certifies recovery of the original campaign.
