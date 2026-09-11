#include "SlotRules.h"

#include <cstdio>
#include <cstdlib>

int main()
{
	using namespace veq::rules;
	int checks = 0;
	const auto check = [&](bool a_condition, const char* a_what) {
		++checks;
		if (!a_condition) {
			std::fprintf(stderr, "FAIL %d: %s\n", checks, a_what);
			std::exit(1);
		}
	};

	// Engine type mapping (numeric WEAPON_TYPE values, see SlotRules.h).
	check(Classify(1, false) == WeaponClass::kOneHanded, "sword is one-handed");
	check(Classify(3, false) == WeaponClass::kOneHanded, "axe is one-handed");
	check(Classify(4, false) == WeaponClass::kOneHanded, "mace is one-handed");
	check(Classify(2, false) == WeaponClass::kDagger, "dagger");
	check(Classify(5, false) == WeaponClass::kTwoHanded, "greatsword is two-handed");
	check(Classify(6, false) == WeaponClass::kTwoHanded, "battleaxe is two-handed");
	check(Classify(7, false) == WeaponClass::kBow, "bow");
	check(Classify(9, false) == WeaponClass::kCrossbow, "crossbow");
	check(Classify(8, false) == WeaponClass::kStaff, "staff");
	check(Classify(0, false) == WeaponClass::kOther, "hand to hand is other");
	check(Classify(5, true) == WeaponClass::kPolearm, "polearm keyword wins over the engine type");

	// R5: polearms and hand-to-hand are not governed; the game's default applies.
	SlotBoard board{ DefaultRoster() };
	check(board.CanAccept(WeaponClass::kPolearm) == Verdict::kNotGoverned, "polearm not governed");
	check(board.CanAccept(WeaponClass::kOther) == Verdict::kNotGoverned, "other not governed");
	check(!board.Place(WeaponClass::kPolearm, 0x900).has_value(), "polearm never placed");
	check(OnUnequip(WeaponClass::kPolearm) == UnequipDestination::kNotGoverned, "polearm unequip not governed");

	// R1: one-handed weapons take the two hip slots, the third is refused.
	check(board.CanAccept(WeaponClass::kOneHanded) == Verdict::kAccept, "first sword accepted");
	check(board.Place(WeaponClass::kOneHanded, 0x101).has_value(), "first sword placed");
	check(board.Place(WeaponClass::kOneHanded, 0x102).has_value(), "second sword placed");
	check(board.CanAccept(WeaponClass::kOneHanded) == Verdict::kRefuseNoSlot, "third sword refused");
	check(!board.Place(WeaponClass::kOneHanded, 0x103).has_value(), "third sword not placed");
	check(board.VisibleCount() == 2 && board.Invariant(), "two visible, invariant holds");

	// A full hip does not block other classes: they have their own slots.
	check(board.CanAccept(WeaponClass::kTwoHanded) == Verdict::kAccept, "greatsword accepted with hips full");
	check(board.Place(WeaponClass::kTwoHanded, 0x201).has_value(), "greatsword placed");
	check(board.CanAccept(WeaponClass::kTwoHanded) == Verdict::kRefuseNoSlot, "second two-handed refused");

	// Bow and crossbow share the one back position.
	check(board.Place(WeaponClass::kBow, 0x301).has_value(), "bow placed");
	check(board.CanAccept(WeaponClass::kCrossbow) == Verdict::kRefuseNoSlot, "crossbow refused while a bow is on the back");
	check(board.Remove(0x301) == 1, "bow removed");
	check(board.Place(WeaponClass::kCrossbow, 0x302).has_value(), "crossbow placed after the bow left");

	// R2: two dagger slots on the body, then two packed in the backpack, hidden.
	const auto d1 = board.Place(WeaponClass::kDagger, 0x401);
	const auto d2 = board.Place(WeaponClass::kDagger, 0x402);
	check(d1 && d2 && board.Slot(*d1).kind == SlotKind::kBody && board.Slot(*d2).kind == SlotKind::kBody, "first two daggers on the body");
	const auto d3 = board.Place(WeaponClass::kDagger, 0x403);
	const auto d4 = board.Place(WeaponClass::kDagger, 0x404);
	check(d3 && d4 && board.Slot(*d3).kind == SlotKind::kBackpack && board.Slot(*d4).kind == SlotKind::kBackpack, "daggers three and four are packed");
	check(board.PackedCount() == 2, "two packed daggers");
	check(board.CanAccept(WeaponClass::kDagger) == Verdict::kRefuseNoSlot, "fifth dagger refused");
	check(board.Invariant(), "invariant with packed daggers");
	check(board.CarriedCount() == board.VisibleCount() + 2, "carried equals visible plus the two packed");

	// R3: quest status is not a parameter of the verdict.
	check(!ExemptFromSlotRules(true) && !ExemptFromSlotRules(false), "quest items are not exempt");
	check(board.CanAccept(WeaponClass::kDagger) == Verdict::kRefuseNoSlot, "a quest dagger is refused like any other when full");

	// R4: staves live in a hand, off-hand first, then primary, then refused.
	check(StaffHand(true, true) == Hand::kLeft, "off-hand preferred");
	check(StaffHand(false, true) == Hand::kRight, "primary when no off-hand");
	check(!StaffHand(false, false).has_value(), "no hand, no staff");
	const auto s1 = board.Place(WeaponClass::kStaff, 0x501);
	check(s1 && board.Slot(*s1).id == "hand.left", "first staff in the left hand");
	const auto s2 = board.Place(WeaponClass::kStaff, 0x502);
	check(s2 && board.Slot(*s2).id == "hand.right", "second staff in the right hand");
	check(board.CanAccept(WeaponClass::kStaff) == Verdict::kRefuseNoSlot, "third staff refused");
	check(OnUnequip(WeaponClass::kStaff) == UnequipDestination::kStorage, "unequipped staff goes to storage");
	check(OnUnequip(WeaponClass::kOneHanded) == UnequipDestination::kBodySlot, "unequipped sword stays on the body");
	check(OnUnequip(WeaponClass::kDagger) == UnequipDestination::kBodySlot, "unequipped dagger stays on the body");
	check(board.Invariant(), "invariant with staves in hand");

	// Removal frees exactly the item's slot and the class is accepted again.
	check(board.SlotOf(0x102).has_value(), "second sword located");
	check(board.Remove(0x102) == 1, "second sword removed");
	check(!board.SlotOf(0x102).has_value(), "second sword gone");
	check(board.CanAccept(WeaponClass::kOneHanded) == Verdict::kAccept, "hip free again");
	check(board.Remove(0x999) == 0, "unknown item frees nothing");
	check(board.Invariant(), "invariant after removals");

	std::printf("slot_rules: %d checks passed\n", checks);
	return 0;
}
