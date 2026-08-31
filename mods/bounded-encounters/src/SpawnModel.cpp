#include "SpawnModel.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace BoundedEncounters
{
	std::string ToString(const Category a_category)
	{
		switch (a_category) {
		case Category::General:
			return "general";
		case Category::AnimalBeast:
			return "animalBeast";
		case Category::GiantMammoth:
			return "giantMammoth";
		case Category::Excluded:
			return "excluded";
		}
		return "excluded";
	}

	Category CategoryFromString(const std::string& a_value)
	{
		if (a_value == "general") {
			return Category::General;
		}
		if (a_value == "animalBeast") {
			return Category::AnimalBeast;
		}
		if (a_value == "giantMammoth") {
			return Category::GiantMammoth;
		}
		if (a_value == "excluded") {
			return Category::Excluded;
		}
		throw std::invalid_argument("unknown category: " + a_value);
	}

	double ExpectedExtrasPerSource(const Curve& a_curve, const std::uint32_t a_playerLevel)
	{
		if (!a_curve.enabled || a_curve.ratePerLevel <= 0.0 || a_playerLevel <= a_curve.baselineLevel) {
			return 0.0;
		}

		const auto progress = static_cast<double>(a_playerLevel - a_curve.baselineLevel);
		double expected = progress * a_curve.ratePerLevel;

		if (a_curve.maxMultiplier > 0.0) {
			expected = std::min(expected, std::max(0.0, a_curve.maxMultiplier - 1.0));
		}
		if (a_curve.maxExtrasPerSource > 0) {
			expected = std::min(expected, static_cast<double>(a_curve.maxExtrasPerSource));
		}

		return std::max(0.0, expected);
	}

	std::uint64_t MixSeed(std::uint64_t a_seed, const std::uint64_t a_value) noexcept
	{
		a_seed ^= a_value + 0x9E3779B97F4A7C15ULL + (a_seed << 6U) + (a_seed >> 2U);
		a_seed ^= a_seed >> 30U;
		a_seed *= 0xBF58476D1CE4E5B9ULL;
		a_seed ^= a_seed >> 27U;
		a_seed *= 0x94D049BB133111EBULL;
		return a_seed ^ (a_seed >> 31U);
	}

	SpawnPlan BuildSpawnPlan(
		const std::vector<SourceDescriptor>& a_sources,
		const std::unordered_map<Category, Curve>& a_curves,
		const std::uint32_t a_playerLevel,
		const std::uint64_t a_seed,
		const std::uint32_t a_globalCellCap)
	{
		SpawnPlan plan;
		std::unordered_map<Category, std::uint32_t> categoryTotals;
		plan.sources.reserve(a_sources.size());
		auto orderedSources = a_sources;
		std::ranges::sort(orderedSources, [&](const SourceDescriptor& a_left, const SourceDescriptor& a_right) {
			const auto leftRank = MixSeed(a_seed, a_left.sourceKey);
			const auto rightRank = MixSeed(a_seed, a_right.sourceKey);
			return leftRank != rightRank ? leftRank < rightRank : a_left.sourceKey < a_right.sourceKey;
		});

		for (const auto& source : orderedSources) {
			SourceRoll roll{ .sourceKey = source.sourceKey, .category = source.category };
			const auto curveIt = a_curves.find(source.category);
			if (source.category == Category::Excluded || curveIt == a_curves.end()) {
				plan.sources.push_back(roll);
				continue;
			}

			const auto& curve = curveIt->second;
			roll.expectedExtras = ExpectedExtrasPerSource(curve, a_playerLevel);
			plan.expectedExtras += roll.expectedExtras;

			const auto whole = static_cast<std::uint32_t>(std::floor(roll.expectedExtras));
			const auto fractional = roll.expectedExtras - static_cast<double>(whole);
			const auto randomBits = MixSeed(a_seed, source.sourceKey);
			constexpr double inverse53Bits = 1.0 / 9007199254740992.0;
			const auto stableUnitRoll = static_cast<double>(randomBits >> 11U) * inverse53Bits;
			roll.extras = whole + static_cast<std::uint32_t>(stableUnitRoll < fractional);

			if (curve.maxExtrasPerSource > 0) {
				roll.extras = std::min(roll.extras, curve.maxExtrasPerSource);
			}

			auto& categoryTotal = categoryTotals[source.category];
			if (curve.maxExtrasPerCell > 0 && categoryTotal + roll.extras > curve.maxExtrasPerCell) {
				roll.extras = categoryTotal >= curve.maxExtrasPerCell ? 0U : curve.maxExtrasPerCell - categoryTotal;
			}

			if (a_globalCellCap > 0 && plan.totalExtras + roll.extras > a_globalCellCap) {
				roll.extras = plan.totalExtras >= a_globalCellCap ? 0U : a_globalCellCap - plan.totalExtras;
			}

			categoryTotal += roll.extras;
			plan.totalExtras += roll.extras;
			plan.sources.push_back(roll);
		}

		return plan;
	}
}
