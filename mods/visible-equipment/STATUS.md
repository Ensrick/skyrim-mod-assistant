# STATUS (2026-09-10): rules-layer staging area, NOT a second plugin

This M0 scaffold (`VisibleEquipment.dll` 0.0.1, receipt `records/source-builds/visible-equipment-0.0.1.json`)
exists to prototype the #36 rules layer: `slot_rules` (CTest, 52 checks), pickup refusal when no body slot
is free, the 2-dagger backpack exception, staff -> long-term storage. The canonical plugin is
`skyrim-tools-source/EnsrickEquipmentDisplay` (#269, name `EnsrickEquipmentDisplay`). At M1 the rules
layer is ported INTO that tree per `docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md` decision D5.
Do not install this DLL; do not develop it as a separate mod. Retire this directory (rename, never delete)
once the port lands.
