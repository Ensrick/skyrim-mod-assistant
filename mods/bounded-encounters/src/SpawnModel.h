#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace BoundedEncounters
{
	enum class Category : std::uint8_t
	{
		General,
		AnimalBeast,
		GiantMammoth,
		Excluded
	};

	[[nodiscard]] std::string ToString(Category a_category);
	[[nodiscard]] Category CategoryFromString(const std::string& a_value);

	struct Curve
	{
		bool enabled{ true };
		double ratePerLevel{ 0.0 };
		std::uint32_t baselineLevel{ 1 };
		double maxMultiplier{ 0.0 };
		std::uint32_t maxExtrasPerSource{ 0 };
		std::uint32_t maxExtrasPerCell{ 0 };
	};

	struct SourceRoll
	{
		std::uint64_t sourceKey{ 0 };
		Category category{ Category::Excluded };
		std::uint32_t extras{ 0 };
		double expectedExtras{ 0.0 };
	};

	struct SpawnPlan
	{
		std::vector<SourceRoll> sources;
		std::uint32_t totalExtras{ 0 };
		double expectedExtras{ 0.0 };
	};

	struct SourceDescriptor
	{
		std::uint64_t sourceKey{ 0 };
		Category category{ Category::Excluded };
	};

	[[nodiscard]] double ExpectedExtrasPerSource(const Curve& a_curve, std::uint32_t a_playerLevel);
	[[nodiscard]] bool PassesNonRespawningExclusion(bool a_actorBaseRespawns) noexcept;
	[[nodiscard]] std::uint64_t MixSeed(std::uint64_t a_seed, std::uint64_t a_value) noexcept;
	[[nodiscard]] std::uint64_t SpawnAdmissionRank(std::uint64_t a_seed, std::uint64_t a_sourceKey) noexcept;
	[[nodiscard]] std::uint64_t SpawnFractionRoll(std::uint64_t a_seed, std::uint64_t a_sourceKey) noexcept;
	[[nodiscard]] SpawnPlan BuildSpawnPlan(
		const std::vector<SourceDescriptor>& a_sources,
		const std::unordered_map<Category, Curve>& a_curves,
		std::uint32_t a_playerLevel,
		std::uint64_t a_seed,
		std::optional<std::uint32_t> a_globalCellCap);
}
