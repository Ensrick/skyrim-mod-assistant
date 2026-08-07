# Optional hip scabbard and draw/sheathe integration

Use the modern OAR/IED route. Do not install the old DAR-era Two Handed Katanas
package as the foundation for this setup; the generated plugin already performs
the record and keyword work.

## Dependencies to install separately

These assets are not bundled:

1. Open Animation Replacer 3.1.6 or newer
2. Immersive Equipment Displays 1.7.4 or newer
3. Open Animation Replacer - IED Conditions
4. Weapon Styles - Draw-Sheathe animations for IED 3.0.1 or newer

The last mod supplies a dedicated two-handed-on-hip equip/unequip animation. It
uses IED's selected placement so it does not require an MCO/BFCO combat overhaul.

## Katana-only IED rule

The generated plugin adds `KWA_WeapTypeKatana2H` as FormID
`000800:KatanaTwoHandedPatch.esp`.

After all four dependencies are installed:

1. Open IED in game (Backspace by default).
2. Open `View > Gear Nodes` and choose the Actor/player scope for the first test.
3. Enable `Placement`, expand the two-handed sword entry, and add a placement
   override rather than changing the base placement.
4. In the override condition, select the katana keyword
   `KWA_WeapTypeKatana2H`. Enable the equipped/displayed applicability used by
   the current IED UI.
5. Select Weapon Styles' `Two handed on hip` placement (enable unrestricted
   placement if IED requests it).
6. Put this override above the generic two-handed placement, save it as an IED
   preset, and test draw, sheathe, sprint, sneak, first person, and third person.

Using an override is important: changing the base two-handed placement would put
every greatsword on the hip. The keyword lets the rule follow every katana found
by the patcher, including later mod-added weapons.

Do not create a guessed JSON preset before the exact installed IED/Weapon Styles
versions are available. Export the verified in-game preset once, then we can
version and deploy that exact file headlessly.
