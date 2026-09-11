#pragma once

// The carry rules from issue #36, as pure data and functions with no game types,
// so the CTest executable exercises every rule without Skyrim present. The
// design doc (docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md) quotes the
// rules verbatim; the comments here name which one each piece implements.
//
//   R1  every weapon in inventory is displayed on the body, and a weapon can
//       only be picked up if a body slot is free (inventory weapon count ==
//       visible weapon count)
//   R2  exception: up to 2 daggers packed in a backpack, hidden
//   R3  quest items are NOT exempt
//   R4  a staff has no on-body slot: it is in a hand (off-hand, or primary if
//       there is no off-hand) or it goes to secondary storage on unequip
//   R5  polearms are an excluded category (not governed, no support needed)

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace veq::rules
{
	enum class WeaponClass : std::uint8_t
	{
		kOneHanded,  // sword, axe, mace
		kDagger,
		kTwoHanded,  // greatsword, battleaxe, warhammer
		kBow,
		kCrossbow,
		kStaff,
		kPolearm,    // R5: excluded category
		kOther,      // hand to hand, unknown: not governed
	};

	// Numeric values of the engine's WEAPON_TYPE enum (RE/W/WeaponTypes.h:
	// kHandToHandMelee 0, kOneHandSword 1, kOneHandDagger 2, kOneHandAxe 3,
	// kOneHandMace 4, kTwoHandSword 5, kTwoHandAxe 6, kBow 7, kStaff 8,
	// kCrossbow 9). Kept numeric so this header stays free of game headers.
	// Polearms have no engine type; the caller detects them by keyword.
	[[nodiscard]] constexpr WeaponClass Classify(std::uint32_t a_engineWeaponType, bool a_polearmKeyword) noexcept
	{
		if (a_polearmKeyword) {
			return WeaponClass::kPolearm;
		}
		switch (a_engineWeaponType) {
		case 1:
		case 3:
		case 4:
			return WeaponClass::kOneHanded;
		case 2:
			return WeaponClass::kDagger;
		case 5:
		case 6:
			return WeaponClass::kTwoHanded;
		case 7:
			return WeaponClass::kBow;
		case 8:
			return WeaponClass::kStaff;
		case 9:
			return WeaponClass::kCrossbow;
		default:
			return WeaponClass::kOther;
		}
	}

	[[nodiscard]] constexpr bool IsGoverned(WeaponClass a_class) noexcept
	{
		return a_class != WeaponClass::kPolearm && a_class != WeaponClass::kOther;
	}

	// R3, stated as code so a test can pin it: nothing about an item's quest
	// status changes the verdict. There is deliberately no quest parameter on
	// CanAccept; this function exists so the rule is a checked fact, not a gap.
	[[nodiscard]] constexpr bool ExemptFromSlotRules(bool /*a_isQuestItem*/) noexcept
	{
		return false;
	}

	enum class SlotKind : std::uint8_t
	{
		kBody,      // counts as visible on the person
		kHand,      // R4: the staff's only home; counts as visible
		kBackpack,  // R2: packed and hidden; does not count as visible
	};

	[[nodiscard]] constexpr std::uint32_t Bit(WeaponClass a_class) noexcept
	{
		return 1u << static_cast<unsigned>(a_class);
	}

	struct SlotDef
	{
		std::string_view id;       // stable key; the placement table maps it to skeleton nodes
		SlotKind         kind;
		std::uint32_t    accepts;  // bitmask of Bit(WeaponClass)
	};

	// Default roster. Body slots are the physical places the measured XPMSSE
	// skeleton offers (docs/NODE_INVENTORY.md in the phase-1 tree): right and
	// left hip for one-handed weapons, right and left hip for daggers, one back
	// position shared by greatswords and battleaxes/warhammers (WeaponBack and
	// WeaponBackAxeMace sit at the same transform), one back position shared by
	// bow and crossbow (WeaponBow and WeaponCrossBow, same transform). The hands
	// are listed as slots only for the staff rule. The two backpack entries are
	// R2. Order matters: Place() takes the first free accepting slot, so the
	// off-hand precedes the primary hand and body slots precede the backpack.
	inline constexpr std::array<SlotDef, 10> kDefaultRoster{ {
		{ "hip.right.1h", SlotKind::kBody, Bit(WeaponClass::kOneHanded) },
		{ "hip.left.1h", SlotKind::kBody, Bit(WeaponClass::kOneHanded) },
		{ "hip.right.dagger", SlotKind::kBody, Bit(WeaponClass::kDagger) },
		{ "hip.left.dagger", SlotKind::kBody, Bit(WeaponClass::kDagger) },
		{ "back.2h", SlotKind::kBody, Bit(WeaponClass::kTwoHanded) },
		{ "back.bow", SlotKind::kBody, Bit(WeaponClass::kBow) | Bit(WeaponClass::kCrossbow) },
		{ "hand.left", SlotKind::kHand, Bit(WeaponClass::kStaff) },
		{ "hand.right", SlotKind::kHand, Bit(WeaponClass::kStaff) },
		{ "backpack.dagger.1", SlotKind::kBackpack, Bit(WeaponClass::kDagger) },
		{ "backpack.dagger.2", SlotKind::kBackpack, Bit(WeaponClass::kDagger) },
	} };

	[[nodiscard]] constexpr std::span<const SlotDef> DefaultRoster() noexcept
	{
		return kDefaultRoster;
	}

	enum class Verdict : std::uint8_t
	{
		kAccept,        // a free slot accepts this class
		kRefuseNoSlot,  // R1: no free slot, the pickup is refused
		kNotGoverned,   // R5 / kOther: the game's default behaviour applies
	};

	// R4: where an item goes when unequipped. Everything governed stays on the
	// person (its body slot); a staff has no body slot and goes to storage.
	enum class UnequipDestination : std::uint8_t
	{
		kBodySlot,
		kStorage,
		kNotGoverned,
	};

	[[nodiscard]] constexpr UnequipDestination OnUnequip(WeaponClass a_class) noexcept
	{
		if (!IsGoverned(a_class)) {
			return UnequipDestination::kNotGoverned;
		}
		return a_class == WeaponClass::kStaff ? UnequipDestination::kStorage : UnequipDestination::kBodySlot;
	}

	enum class Hand : std::uint8_t
	{
		kLeft,
		kRight,
	};

	// R4: "off-hand, or primary if there is no off-hand".
	[[nodiscard]] constexpr std::optional<Hand> StaffHand(bool a_leftFree, bool a_rightFree) noexcept
	{
		if (a_leftFree) {
			return Hand::kLeft;
		}
		if (a_rightFree) {
			return Hand::kRight;
		}
		return std::nullopt;
	}

	// Occupancy of one actor's roster. Items are opaque tokens (the caller uses
	// a form id or inventory unique id); the board never looks inside them.
	class SlotBoard
	{
	public:
		using Item = std::uint32_t;

		explicit SlotBoard(std::span<const SlotDef> a_roster) :
			_roster(a_roster), _held(a_roster.size(), std::nullopt) {}

		[[nodiscard]] Verdict CanAccept(WeaponClass a_class) const noexcept
		{
			if (!IsGoverned(a_class)) {
				return Verdict::kNotGoverned;
			}
			return FirstFree(a_class).has_value() ? Verdict::kAccept : Verdict::kRefuseNoSlot;
		}

		// Places the item in the first free accepting slot and returns its index,
		// or nullopt when R1 refuses. Ungoverned classes are never placed.
		std::optional<std::size_t> Place(WeaponClass a_class, Item a_item)
		{
			if (!IsGoverned(a_class)) {
				return std::nullopt;
			}
			const auto slot = FirstFree(a_class);
			if (slot) {
				_held[*slot] = a_item;
			}
			return slot;
		}

		// Frees every slot holding the item. Returns how many were freed.
		std::size_t Remove(Item a_item) noexcept
		{
			std::size_t freed = 0;
			for (auto& held : _held) {
				if (held && *held == a_item) {
					held.reset();
					++freed;
				}
			}
			return freed;
		}

		[[nodiscard]] std::optional<std::size_t> SlotOf(Item a_item) const noexcept
		{
			for (std::size_t i = 0; i < _held.size(); ++i) {
				if (_held[i] && *_held[i] == a_item) {
					return i;
				}
			}
			return std::nullopt;
		}

		[[nodiscard]] std::size_t Count(SlotKind a_kind) const noexcept
		{
			std::size_t n = 0;
			for (std::size_t i = 0; i < _held.size(); ++i) {
				if (_held[i] && _roster[i].kind == a_kind) {
					++n;
				}
			}
			return n;
		}

		[[nodiscard]] std::size_t VisibleCount() const noexcept { return Count(SlotKind::kBody) + Count(SlotKind::kHand); }
		[[nodiscard]] std::size_t PackedCount() const noexcept { return Count(SlotKind::kBackpack); }
		[[nodiscard]] std::size_t CarriedCount() const noexcept { return VisibleCount() + PackedCount(); }

		// R1 with the R2 carve-out: everything carried is either visible or one of
		// the packed daggers. Holds by construction; tests assert it after every
		// mutation so a future roster change cannot silently break it.
		[[nodiscard]] bool Invariant() const noexcept
		{
			return CarriedCount() == VisibleCount() + PackedCount() && PackedCount() <= 2;
		}

		[[nodiscard]] const SlotDef& Slot(std::size_t a_index) const noexcept { return _roster[a_index]; }
		[[nodiscard]] std::size_t Size() const noexcept { return _roster.size(); }

	private:
		[[nodiscard]] std::optional<std::size_t> FirstFree(WeaponClass a_class) const noexcept
		{
			const auto bit = Bit(a_class);
			for (std::size_t i = 0; i < _roster.size(); ++i) {
				if ((_roster[i].accepts & bit) != 0 && !_held[i]) {
					return i;
				}
			}
			return std::nullopt;
		}

		std::span<const SlotDef>         _roster;
		std::vector<std::optional<Item>> _held;
	};
}
