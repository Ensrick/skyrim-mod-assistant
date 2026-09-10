# Travel acceptance remains incomplete

September 10, 2026, 10:25 CDT. Parent #262; test capability #267.

The existing menu controller cannot yet substantiate representative navigated
gameplay. A successful input callback or clean exit is not a travel/combat pass.
No further identical load-only test is justified as evidence for that criterion.

## Bounded input experiment

Private, muted profile `Astra Travel267 Route 20260910` copied the post-USSEP
fresh-character Save5 (`0032479D` ESS / `316B4F16` co-save). Normal installed
SKSE `F7435705` and currency `4DAB6D30` were used without swaps, autoload,
activation flags, or additional mods. Controller38608 / game37152 ran
10:20:19.427–10:22:55.222 CDT, ending through normal Journal Quit, exit0.

Continue completed at10:21:28.600. At10:21:48.963 the guarded read-only observer
reported player14 at `(24826.994140625, -4226.01171875, -2996.45556640625)`,
cell1A276 / world1A26F. Two distinct probes followed:

- One `Strafe Right` keyboard event, code32, down/up separated by400ms.
- Twenty-four `Strafe Right` down/up pairs, each separated by10ms.

Both batches completed without a reported dispatch failure. Both subsequent
observations returned **byte-identical position**, same cell/world, and stable
core rereads. Neither moved the actor. This is measured failure of these two
input recipes, not proof that normal user keyboard controls are broken, nor a
complete causal diagnosis of frame timing versus collision.

Final unpaused ping10:22:48.244 was79.644 seconds after the load. The protected
crash directory remained empty. Original campaign, source fixture, Default
files, root DLL/PDB and all41 currency overlay files passed preservation checks;
normal logger restored. No new save was generated and no save was cleaned.
No owned game/controller remains; claim `astra/travel267` released.

## Actual Fable review and source boundary

Actual CLI model `claude-fable-5-1`, session
`86a3337d-1c79-431b-a9fe-9bfa06d3cadc`, completed a read-only review in35 turns,
117.684 seconds. No permission denials, writes or subordinate agents. Its
reported list-price accounting is not a claim about subscription billing.

Root checked the relevant source: MenuPilot `src/main.cpp` sends only a
ButtonEvent down and up; its sleep does not emit held events each frame.
CommonLib6.7.1 `UserEvents.h` identifies `Strafe Right`; the existing dispatcher
does not construct MouseMoveEvent or ThumbstickEvent. `MouseMoveEvent.h` defines
X/Y deltas, while the existing tool offers no camera-look operation. The review
therefore cannot supply a supported rotate-then-Auto-Move recipe.

CommonLib declarations alone do not prove native frame timing or object
lifetime. Do not add speculative vtable calls, direct position writes, unsafe
queue insertion, collision bypass, or a new movement mod merely to pass this
test. A future native-input extension needs a bounded contract, exact-runtime
verification, ownership/lifetime review, isolated candidate deployment and
observed direction/displacement before promotion. This has **not** been built
or installed by this experiment.

## Remaining acceptance and user decisions

- #267: genuine navigated travel/cell transition and appropriate combat evidence
  remain unverified. A teleport would not verify locomotion.
- #262: original Adventurer3 is preserved and safely refused, **not recovered**.
  Restoring removed TrueHUD/QuickLootIE, cleaning/migrating saved state, or
  selecting a replacement campaign requires the user's decision. No such
  permission is inferred from overnight testing authorization.
- #157: other script-binding diagnostics remain. Missing optional-integration
  plugin probes are not by themselves evidence that those mods must be installed.

Private raw logs and observer reports remain under
`records-work/travel267-route-20260910/`. The overall goal and issues remain open.
