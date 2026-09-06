#include "DenominationMath.h"
#include "LedgerPolicy.h"
#include "LedgerFingerprint.h"
#include "MessagePolicy.h"
#include "SaveMarkerPolicy.h"
#include "SourcePolicy.h"

#include <array>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>

namespace
{
	int failures = 0;

	void Check(const bool a_condition, const char* a_message)
	{
		if (!a_condition) {
			std::cerr << "FAIL: " << a_message << '\n';
			++failures;
		}
	}
}

int main()
{
	using namespace Ensrick::Currency;

	Check(!PostLoadSucceeded(nullptr, 1), "PostLoadGame pointer-value zero must mean failure");
	Check(PostLoadSucceeded(reinterpret_cast<const void*>(static_cast<std::uintptr_t>(1)), 1),
		"PostLoadGame pointer-value one must mean success without dereferencing address 0x1");
	Check(!PostLoadSucceeded(reinterpret_cast<const void*>(static_cast<std::uintptr_t>(1)), sizeof(bool*)),
		"unexpected PostLoadGame payload lengths must fail closed");
	constexpr std::array<RouteDesignCandidate, 3> faceDesigns{
		RouteDesignCandidate{ .familyIndex = 1, .familySalt = 0x4452414B52424541ULL },
		RouteDesignCandidate{ .familyIndex = 2, .familySalt = 0x4452414B524D4F54ULL },
		RouteDesignCandidate{ .familyIndex = 3, .familySalt = 0x4452414B524F574CULL },
	};
	auto reversedDesigns = faceDesigns;
	std::ranges::reverse(reversedDesigns);
	std::array<std::uint64_t, 4> faceSelections{};
	for (std::uint64_t source = 0; source < 100'000; ++source) {
		const auto selectedFamily = SelectRouteDesign(faceDesigns, source);
		Check(selectedFamily && *selectedFamily >= 1 && *selectedFamily <= 3,
			"each source selects exactly one configured ancient face design");
		Check(selectedFamily == SelectRouteDesign(reversedDesigns, source),
			"face selection must be stable and independent of candidate list order");
		if (selectedFamily && *selectedFamily < faceSelections.size()) {
			++faceSelections[*selectedFamily];
		}
		const auto payout = Decompose(source, UseBrokenVariant(source, faceDesigns[0].familySalt, 20));
		Check(ValueOf(payout) == source,
			"face choice must not copy, multiply, or discard the source budget");
	}
	for (std::size_t family = 1; family <= 3; ++family) {
		Check(faceSelections[family] >= 32'500 && faceSelections[family] <= 34'200,
			"equal-weight configured faces must all receive reasonable deterministic coverage");
	}
	Check(SelectRouteDesign(std::span(faceDesigns).first(1), 0) == 1,
		"one-family routes select that family for the player identity zero");
	Check(!SelectRouteDesign({}, 0), "empty face candidates must not invent a family");

	const SaveCheckpoint checkpoint{
		.ledgerFingerprint = 0x123456789ABCDEF0ULL,
		.ledgerValue = 115,
		.observedBackend = 110,
		.observedPhysical = 105,
	};
	Check(IsRecognizedNativeSaveCheckpoint(SaveRecordType, SaveRecordVersion, sizeof(checkpoint), checkpoint),
		"exact native save checkpoint must be accepted");
	Check(!IsRecognizedNativeSaveCheckpoint(SaveRecordType, SaveRecordVersion + 1, sizeof(checkpoint), checkpoint),
		"unknown native save schema versions must be rejected");
	Check(!IsRecognizedNativeSaveCheckpoint(SaveRecordType, SaveRecordVersion, sizeof(checkpoint) - 1, checkpoint),
		"truncated native save checkpoints must be rejected");
	auto oversizedCheckpoint = checkpoint;
	oversizedCheckpoint.observedPhysical = MaximumLedgerValue + 1;
	Check(!IsRecognizedNativeSaveCheckpoint(
		SaveRecordType, SaveRecordVersion, sizeof(oversizedCheckpoint), oversizedCheckpoint),
		"checkpoint counts outside the engine-supported range must be rejected");
	Check(CheckpointMatchesLedger(checkpoint, 0x123456789ABCDEF0ULL),
		"an exact ledger fingerprint must be accepted");
	Check(!CheckpointMatchesLedger(checkpoint, 0x123456789ABCDE00ULL),
		"a changed ledger mapping must invalidate the checkpoint");

	Config fingerprintFixture{
		.owner = "EnsrickCurrencyDenominations",
		.backendForm = FormSpec{ .plugin = "Skyrim.esm", .localID = 0x00000F },
	};
	fingerprintFixture.seed = 0x454E535249434B31ULL;
	fingerprintFixture.routingPrecedence = { "questExceptions", "regionalRoutes", "septimFallback" };
	FamilyConfig fingerprintFamily{
		.id = "septim",
		.displayLabel = "Septims",
		.backendLabel = "Septim value",
		.salt = 0x53657074696DULL,
		.enabled = true,
		.fallback = true,
	};
	fingerprintFamily.denominations = {
		DenominationConfig{ .tier = "copper", .value = 1,
			.form = FormSpec{ .plugin = "Test.esp", .localID = 0x000800 } },
		DenominationConfig{ .tier = "silver", .value = 10,
			.form = FormSpec{ .plugin = "Test.esp", .localID = 0x000801 } },
		DenominationConfig{ .tier = "gold", .value = 100,
			.form = FormSpec{ .plugin = "Test.esp", .localID = 0x000802 } },
	};
	fingerprintFamily.inputAliases = {
		InputAliasConfig{ .tier = "copper", .form = FormSpec{ .plugin = "Test.esp", .localID = 0x000803 } },
	};
	fingerprintFixture.families.push_back(std::move(fingerprintFamily));
	fingerprintFixture.routingRules.push_back(RoutingRuleConfig{
		.id = "test-route",
		.anyKeywords = { FormSpec{ .plugin = "Test.esp", .localID = 0x000900 } },
		.familyIDs = { "septim" },
	});
	Check(ComputeLedgerFingerprint(fingerprintFixture) == 0x0D15619C721A4FAFULL,
		"C++ ledger fingerprint must match the independent Python launch gate");
	const auto originalFingerprint = ComputeLedgerFingerprint(fingerprintFixture);
	auto changedFingerprint = fingerprintFixture;
	changedFingerprint.families[0].denominations[0].tier = "wrong-name";
	Check(ComputeLedgerFingerprint(changedFingerprint) != originalFingerprint,
		"named tiers must be protected by the save fingerprint");
	changedFingerprint = fingerprintFixture;
	changedFingerprint.routingRules[0].anyKeywords[0].localID += 1;
	Check(ComputeLedgerFingerprint(changedFingerprint) != originalFingerprint,
		"regional routing changes must invalidate the previous save fingerprint");
	changedFingerprint = fingerprintFixture;
	changedFingerprint.families[0].salt += 1;
	Check(ComputeLedgerFingerprint(changedFingerprint) != originalFingerprint,
		"face selection salt changes must invalidate the previous save fingerprint");
	changedFingerprint = fingerprintFixture;
	changedFingerprint.families[0].inputAliases[0].form.localID += 1;
	Check(ComputeLedgerFingerprint(changedFingerprint) != originalFingerprint,
		"source alias bindings must be protected by the save fingerprint");
	const auto alias24 = CanonicalCountsWithAliases(24, false, 1);
	Check(alias24 && *alias24 == std::vector<std::int32_t>{ 4, 2, 0, 0 },
		"source alias value must pay into canonical tiers with zero alias output");
	const auto alias124 = CanonicalCountsWithAliases(124, true, 2);
	Check(alias124 && *alias124 == std::vector<std::int32_t>{ 4, 12, 0, 0, 0 },
		"broken output must still clear every source alias without paying twice");
	Check(!CanonicalCountsWithAliases(MaximumLedgerValue + 1, false, 1),
		"source alias normalization must preserve ledger overflow protections");
	Check(!CanonicalCountsWithAliases(24, false, std::numeric_limits<std::size_t>::max()),
		"an overflowing alias layout must fail closed");

	constexpr std::array<std::uint64_t, 13> boundaries{
		0, 1, 9, 10, 11, 19, 20, 99, 100, 109, 110, 199, 200
	};
	for (const auto value : boundaries) {
		for (const bool broken : { false, true }) {
			const auto counts = Decompose(value, broken);
			Check(ValueOf(counts) == value, "boundary decomposition must conserve value");
		}
	}

	for (std::uint64_t value = 0; value <= 1'000'000; ++value) {
		const auto canonical = Decompose(value, false);
		const auto broken = Decompose(value, true);
		Check(ValueOf(canonical) == value, "canonical decomposition must conserve value");
		Check(ValueOf(broken) == value, "broken decomposition must conserve value");
		Check(canonical.copper < 10 && canonical.silver < 10,
			"canonical decomposition must use efficient lower tiers");
		if (value >= 100) {
			Check(broken.gold + 1 == canonical.gold && broken.silver == canonical.silver + 10 &&
				broken.copper == canonical.copper, "broken gold must become exactly ten silver");
		} else if (value >= 10) {
			Check(broken.gold == canonical.gold && broken.silver + 1 == canonical.silver &&
				broken.copper == canonical.copper + 10, "broken silver must become exactly ten copper");
		} else {
			Check(broken == canonical, "values below ten cannot be broken further");
		}
	}

	std::uint32_t selected = 0;
	for (std::uint64_t source = 1; source <= 100'000; ++source) {
		selected += UseBrokenVariant(source, 0x4D656465ULL, 20) ? 1U : 0U;
		Check(UseBrokenVariant(source, 0x4D656465ULL, 20) ==
			UseBrokenVariant(source, 0x4D656465ULL, 20), "selection must be stable");
	}
	Check(selected >= 19'500 && selected <= 20'500,
		"stable hash sample must stay near the configured twenty percent");
	Check(!UseBrokenVariant(1, 1, 0), "zero percent must never select broken");
	Check(UseBrokenVariant(1, 1, 100), "one hundred percent must always select broken");
	Check(Decompose(15, false) != TierCounts{ .copper = 15 },
		"a raw all-copper threshold stack must not satisfy the selected canonical representation");
	Check(Decompose(15, true) == TierCounts{ .copper = 15 },
		"the same threshold stack is idempotent only when its stable source selects broken");

	const TierCounts overflowing{ .copper = 0, .silver = 0,
		.gold = std::numeric_limits<std::uint64_t>::max() };
	Check(!ValueOf(overflowing).has_value(), "overflowing totals must fail closed");
	Check(FreshAdmissionValue(0, 5) == 5,
		"a physical payout before new-game admission must be preserved");
	Check(FreshAdmissionValue(100, 5) == 105,
		"independent backend and physical new-game payouts must both be preserved");
	Check(!FreshAdmissionValue(std::numeric_limits<std::uint64_t>::max(), 1),
		"overflowing fresh-admission inputs must fail closed");

	InventorySnapshot oldSave{
		.backend = 100,
		.physicalFamilies = { FamilyCounts{ TierCounts{ .silver = 4 } }, FamilyCounts{} }
	};
	const auto migration = PlanReconciliation(oldSave, 1, ReconcileCause::migration, false);
	Check(migration && migration->value == 100 && migration->backendWonConflict,
		"migration must preserve the authoritative old-save backend value");
	Check(migration && migration->activeCounts == TierCounts{ .gold = 1 },
		"migration must emit only the active family");

	InventorySnapshot staleAfterFullSpend{
		.backend = 0,
		.physicalFamilies = { FamilyCounts{ TierCounts{ .copper = 4, .silver = 2, .gold = 1 } } }
	};
	const auto spent = PlanReconciliation(staleAfterFullSpend, 0, ReconcileCause::migration, false);
	Check(spent && spent->backend == 0 && spent->activeCounts == TierCounts{} && spent->backendWonConflict,
		"migration must not resurrect a stale physical mirror after a full backend spend");

	InventorySnapshot switchRegion{
		.backend = 248,
		.physicalFamilies = {
			FamilyCounts{ TierCounts{ .copper = 8, .silver = 4, .gold = 2 } }, FamilyCounts{}
		}
	};
	const auto switched = PlanReconciliation(switchRegion, 1, ReconcileCause::regionChanged, true);
	Check(switched && switched->backend == 248 && switched->activeFamily == 1 &&
		switched->activeCounts == TierCounts{ .copper = 8, .silver = 14, .gold = 1 },
		"region change must keep purchasing power and break no more than one gold coin");

	Check(!PlanReconciliation(staleAfterFullSpend, 1, ReconcileCause::migration, false),
		"invalid family indices must fail closed");

	const LedgerBaseline baseline{ .value = 100, .backend = 100, .physical = 100 };
	const auto mixed = PlanObservedChanges(baseline, 110, 105, 0, 1, false);
	Check(mixed && mixed->backend == 115 && mixed->activeCounts ==
		TierCounts{ .copper = 5, .silver = 1, .gold = 1 },
		"same-frame backend reward plus physical pickup must preserve both deltas");
	const LedgerBaseline savedMixed{
		.value = mixed ? mixed->value : 0,
		.backend = 110,
		.physical = 105,
	};
	const auto loadedMixed = PlanObservedChanges(savedMixed, 110, 105, 0, 1, false);
	Check(loadedMixed && loadedMixed->value == 115,
		"a checkpoint must preserve pending mixed observations across save and load");

	const auto pendingPickup = PlanObservedChanges(baseline, 100, 105, 0, 1, false);
	const LedgerBaseline savedPickup{
		.value = pendingPickup ? pendingPickup->value : 0,
		.backend = 100,
		.physical = 105,
	};
	const auto loadedPickup = PlanObservedChanges(savedPickup, 100, 105, 0, 1, false);
	Check(loadedPickup && loadedPickup->value == 105,
		"a pending physical pickup must survive save and load exactly once");

	const auto spentThenSwitch = PlanObservedChanges(baseline, 0, 100, 1, 2, false);
	Check(spentThenSwitch && spentThenSwitch->backend == 0 && spentThenSwitch->activeCounts == TierCounts{},
		"a full spend followed by a region switch must remain zero");
	const LedgerBaseline savedSpend{
		.value = spentThenSwitch ? spentThenSwitch->value : 1,
		.backend = 0,
		.physical = 100,
	};
	const auto loadedSpend = PlanObservedChanges(savedSpend, 0, 100, 1, 2, false);
	Check(loadedSpend && loadedSpend->value == 0,
		"a pending full backend spend must not resurrect after save and load");

	const auto physicalDrop = PlanObservedChanges(baseline, 100, 0, 0, 1, false);
	const LedgerBaseline savedDrop{
		.value = physicalDrop ? physicalDrop->value : 1,
		.backend = 100,
		.physical = 0,
	};
	const auto loadedDrop = PlanObservedChanges(savedDrop, 100, 0, 0, 1, false);
	Check(loadedDrop && loadedDrop->value == 0,
		"a pending full physical drop must not be restored after save and load");

	const auto mixedRemoval = PlanObservedChanges(baseline, 90, 95, 0, 1, false);
	Check(mixedRemoval && mixedRemoval->backend == 85,
		"same-frame backend spend plus physical transfer must preserve both removals");
	Check(!PlanObservedChanges(baseline, 0, 0, 0, 1, false),
		"combined observed removals larger than the ledger must fail closed");

	const LedgerBaseline normalized{ .value = 115, .backend = 115, .physical = 115 };
	const auto delayedSelfEvents = PlanObservedChanges(normalized, 115, 115, 0, 1, false);
	Check(delayedSelfEvents && delayedSelfEvents->value == 115,
		"delayed self-mutation events after baseline advance must not mint money");

	const auto backendToPhysical = PlanObservedChanges(baseline, 0, 200, 0, 1, false);
	Check(backendToPhysical && backendToPhysical->value == 100,
		"an equal backend-to-physical conversion must conserve the ledger");

	const auto physicalToBackend = PlanObservedChanges(baseline, 200, 0, 0, 1, false);
	Check(physicalToBackend && physicalToBackend->value == 100,
		"an equal physical-to-backend conversion must conserve the ledger");

	const LedgerBaseline nearMaximum{
		.value = std::numeric_limits<std::uint64_t>::max(),
		.backend = std::numeric_limits<std::uint64_t>::max(),
		.physical = 0
	};
	Check(!PlanObservedChanges(nearMaximum, std::numeric_limits<std::uint64_t>::max(), 1, 0, 1, false),
		"observed additions that overflow the ledger must fail closed");
	Check(!PlanObservedChanges(baseline, 100, 100, 1, 1, false),
		"invalid observed-change family indices must fail closed");

	if (failures != 0) {
		std::cerr << failures << " native currency test(s) failed\n";
		return 1;
	}
	std::cout << "PASS: denomination conservation, stable distribution, and ledger reconciliation\n";
	return 0;
}
