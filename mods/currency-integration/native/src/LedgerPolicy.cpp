#include "LedgerPolicy.h"

#include <limits>

namespace Ensrick::Currency
{
	std::optional<std::uint64_t> SumPhysicalValue(
		const std::span<const FamilyCounts> a_families) noexcept
	{
		std::uint64_t total = 0;
		for (const auto& family : a_families) {
			const auto value = ValueOf(family.counts);
			if (!value || *value > std::numeric_limits<std::uint64_t>::max() - total) {
				return std::nullopt;
			}
			total += *value;
		}
		return total;
	}

	std::optional<std::uint64_t> FreshAdmissionValue(
		const std::uint64_t a_backend,
		const std::uint64_t a_physical) noexcept
	{
		if (a_physical > std::numeric_limits<std::uint64_t>::max() - a_backend) {
			return std::nullopt;
		}
		return a_backend + a_physical;
	}

	std::optional<LedgerPlan> PlanReconciliation(
		const InventorySnapshot& a_snapshot,
		const std::size_t a_activeFamily,
		const ReconcileCause a_cause,
		const bool a_breakOneLargerCoin) noexcept
	{
		if (a_activeFamily >= a_snapshot.physicalFamilies.size()) {
			return std::nullopt;
		}

		const auto physical = SumPhysicalValue(a_snapshot.physicalFamilies);
		if (!physical) {
			return std::nullopt;
		}

		std::uint64_t value = a_snapshot.backend;
		switch (a_cause) {
		case ReconcileCause::migration:
		case ReconcileCause::regionChanged:
			break;
		}

		return LedgerPlan{
			.value = value,
			.backend = value,
			.activeFamily = a_activeFamily,
			.activeCounts = Decompose(value, a_breakOneLargerCoin),
			.backendWonConflict =
				(a_cause == ReconcileCause::migration || a_cause == ReconcileCause::regionChanged) &&
				a_snapshot.backend != *physical,
		};
	}

	namespace
	{
		std::optional<std::uint64_t> ApplyObservedDelta(
			const std::uint64_t a_value,
			const std::uint64_t a_before,
			const std::uint64_t a_after) noexcept
		{
			if (a_after >= a_before) {
				const auto increase = a_after - a_before;
				if (increase > std::numeric_limits<std::uint64_t>::max() - a_value) {
					return std::nullopt;
				}
				return a_value + increase;
			}

			const auto decrease = a_before - a_after;
			if (decrease > a_value) {
				return std::nullopt;
			}
			return a_value - decrease;
		}
	}

	std::optional<LedgerPlan> PlanObservedChanges(
		const LedgerBaseline& a_baseline,
		const std::uint64_t a_currentBackend,
		const std::uint64_t a_currentPhysical,
		const std::size_t a_activeFamily,
		const std::size_t a_familyCount,
		const bool a_breakOneLargerCoin) noexcept
	{
		if (a_activeFamily >= a_familyCount) {
			return std::nullopt;
		}

		auto value = ApplyObservedDelta(a_baseline.value, a_baseline.backend, a_currentBackend);
		if (!value) {
			return std::nullopt;
		}
		value = ApplyObservedDelta(*value, a_baseline.physical, a_currentPhysical);
		if (!value) {
			return std::nullopt;
		}

		return LedgerPlan{
			.value = *value,
			.backend = *value,
			.activeFamily = a_activeFamily,
			.activeCounts = Decompose(*value, a_breakOneLargerCoin),
			.backendWonConflict = false,
		};
	}
}
