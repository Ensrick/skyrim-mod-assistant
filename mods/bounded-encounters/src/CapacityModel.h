#pragma once

#include <cstdint>

namespace BoundedEncounters
{
	inline constexpr std::uint32_t MaxSpawnsPerEvaluation = 8;

	struct PopulationCapacity
	{
		std::uint32_t additionalCellCap{ 0 };
		std::uint32_t hostileCellCap{ 0 };
		std::uint32_t existingCellHostiles{ 0 };
		std::uint32_t globalActiveOwnedCap{ 0 };
		std::uint32_t existingActiveOwned{ 0 };
		std::uint32_t remainingHostileCapacity{ 0 };
		std::uint32_t remainingActiveOwnedCapacity{ 0 };
		std::uint32_t perEvaluationCap{ 0 };
		std::uint32_t effectiveAdditionalCap{ 0 };
	};

	[[nodiscard]] PopulationCapacity ComputePopulationCapacity(
		std::uint32_t a_additionalCellCap,
		std::uint32_t a_hostileCellCap,
		std::uint32_t a_existingCellHostiles,
		std::uint32_t a_globalActiveOwnedCap,
		std::uint32_t a_existingActiveOwned,
		std::uint32_t a_perEvaluationCap = MaxSpawnsPerEvaluation) noexcept;
}
