#pragma once

#include "DenominationMath.h"

#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace Ensrick::Currency
{
	struct FamilyCounts
	{
		TierCounts counts;
	};

	struct InventorySnapshot
	{
		std::uint64_t backend{ 0 };
		std::vector<FamilyCounts> physicalFamilies;
	};

	enum class ReconcileCause
	{
		migration,
		regionChanged
	};

	struct LedgerPlan
	{
		std::uint64_t value{ 0 };
		std::uint64_t backend{ 0 };
		std::size_t activeFamily{ 0 };
		TierCounts activeCounts;
		bool backendWonConflict{ false };
	};

	struct LedgerBaseline
	{
		std::uint64_t value{ 0 };
		std::uint64_t backend{ 0 };
		std::uint64_t physical{ 0 };
	};

	[[nodiscard]] std::optional<std::uint64_t> SumPhysicalValue(
		std::span<const FamilyCounts> a_families) noexcept;

	// New-game admission has no prior mirror. Backend and recognized physical
	// currency received before the asynchronous owner callback are independent
	// value and must both survive the first normalization.
	[[nodiscard]] std::optional<std::uint64_t> FreshAdmissionValue(
		std::uint64_t a_backend,
		std::uint64_t a_physical) noexcept;

	// On migration or a regional switch, hidden Gold001 is authoritative even
	// when it is zero. Treating a stale physical mirror as spendable after the
	// backend was fully consumed would mint money on load or region change.
	[[nodiscard]] std::optional<LedgerPlan> PlanReconciliation(
		const InventorySnapshot& a_snapshot,
		std::size_t a_activeFamily,
		ReconcileCause a_cause,
		bool a_breakOneLargerCoin) noexcept;

	// Compute both deltas from a post-reconciliation baseline. This preserves a
	// backend reward and a physical pickup that occur in the same task batch,
	// and it also makes delayed events from our own normalization harmless: once
	// the baseline is advanced, the observed deltas are both zero.
	[[nodiscard]] std::optional<LedgerPlan> PlanObservedChanges(
		const LedgerBaseline& a_baseline,
		std::uint64_t a_currentBackend,
		std::uint64_t a_currentPhysical,
		std::size_t a_activeFamily,
		std::size_t a_familyCount,
		bool a_breakOneLargerCoin) noexcept;
}
