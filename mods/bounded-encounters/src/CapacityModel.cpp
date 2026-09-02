#include "CapacityModel.h"

#include <algorithm>

namespace BoundedEncounters
{
	namespace
	{
		[[nodiscard]] constexpr std::uint32_t SaturatingSubtract(
			const std::uint32_t a_cap,
			const std::uint32_t a_existing) noexcept
		{
			return a_existing >= a_cap ? 0U : a_cap - a_existing;
		}
	}

	PopulationCapacity ComputePopulationCapacity(
		const std::uint32_t a_additionalCellCap,
		const std::uint32_t a_hostileCellCap,
		const std::uint32_t a_existingCellHostiles,
		const std::uint32_t a_globalActiveOwnedCap,
		const std::uint32_t a_existingActiveOwned,
		const std::uint32_t a_perEvaluationCap) noexcept
	{
		PopulationCapacity capacity{
			.additionalCellCap = a_additionalCellCap,
			.hostileCellCap = a_hostileCellCap,
			.existingCellHostiles = a_existingCellHostiles,
			.globalActiveOwnedCap = a_globalActiveOwnedCap,
			.existingActiveOwned = a_existingActiveOwned,
			.remainingHostileCapacity = SaturatingSubtract(a_hostileCellCap, a_existingCellHostiles),
			.remainingActiveOwnedCapacity = SaturatingSubtract(a_globalActiveOwnedCap, a_existingActiveOwned),
			.perEvaluationCap = a_perEvaluationCap
		};
		capacity.effectiveAdditionalCap = std::min({
			capacity.additionalCellCap,
			capacity.remainingHostileCapacity,
			capacity.remainingActiveOwnedCapacity,
			capacity.perEvaluationCap });
		return capacity;
	}
}
