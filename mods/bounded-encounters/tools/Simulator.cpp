#include "Config.h"
#include "Diagnostics.h"
#include "SpawnModel.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

namespace
{
	using BoundedEncounters::Category;
	using BoundedEncounters::Curve;
	using BoundedEncounters::CapacityProjection;
	using BoundedEncounters::ProjectFractionalCapacity;
	using BoundedEncounters::SourceDescriptor;

	constexpr std::uint32_t kDefaultSourceCount = 4;
	constexpr std::uint32_t kMaximumSourceCount = 100'000;
	constexpr std::uint32_t kMaximumSpawnsPerEvaluation = 8;
	constexpr std::uint64_t kAuditSeedDomain = 0x42454155444954ULL;
	constexpr std::array<Category, 3> kCategories{
		Category::General,
		Category::AnimalBeast,
		Category::GiantMammoth
	};
	// A deliberately mixed 5:2:1 audit population. The first four entries
	// include every category so the default source count exercises competition.
	constexpr std::array<Category, 8> kMixedCategoryPattern{
		Category::General,
		Category::AnimalBeast,
		Category::GiantMammoth,
		Category::General,
		Category::General,
		Category::AnimalBeast,
		Category::General,
		Category::General
	};
	constexpr std::array<std::uint32_t, 9> kLevels{ 1, 5, 10, 20, 30, 40, 50, 75, 100 };

	class CommandLineError final : public std::runtime_error
	{
	public:
		using std::runtime_error::runtime_error;
	};

	struct Capacity
	{
		std::uint32_t additionalCellCap{ 0 };
		std::uint32_t hostileCellCap{ 0 };
		std::uint32_t existingCellHostiles{ 0 };
		std::uint32_t globalActiveOwnedCap{ 0 };
		std::uint32_t existingActiveOwned{ 0 };
		std::uint32_t remainingHostileCapacity{ 0 };
		std::uint32_t remainingActiveOwnedCapacity{ 0 };
		std::uint32_t effectiveAdditionalCap{ 0 };
	};

	void PrintUsage()
	{
		std::cerr << "Usage: BoundedEncounters.Simulate <config.json> [source-count: 1..100000] [seed]\n";
	}

	template <class UInt>
	[[nodiscard]] UInt ParseUnsigned(const char* a_text, const std::string_view a_name)
	{
		static_assert(std::is_unsigned_v<UInt>);
		const std::string_view input{ a_text ? a_text : "" };
		if (input.empty() || !std::ranges::all_of(input, [](const char character) {
				return character >= '0' && character <= '9';
			})) {
			throw CommandLineError(std::string(a_name) + " must contain only decimal digits");
		}

		UInt value{};
		const auto parsed = std::from_chars(input.data(), input.data() + input.size(), value, 10);
		if (parsed.ec == std::errc::result_out_of_range) {
			throw CommandLineError(std::string(a_name) + " is outside its unsigned integer range");
		}
		if (parsed.ec != std::errc{} || parsed.ptr != input.data() + input.size()) {
			throw CommandLineError(std::string(a_name) + " is not a complete unsigned decimal integer");
		}
		return value;
	}

	[[nodiscard]] double CategoryValue(
		const std::unordered_map<Category, double>& a_values,
		const Category a_category)
	{
		const auto found = a_values.find(a_category);
		return found == a_values.end() ? 0.0 : found->second;
	}

	[[nodiscard]] std::uint32_t CategoryValue(
		const std::unordered_map<Category, std::uint32_t>& a_values,
		const Category a_category)
	{
		const auto found = a_values.find(a_category);
		return found == a_values.end() ? 0U : found->second;
	}

	[[nodiscard]] BoundedEncounters::SpawnPlan BuildCapacityPlan(
		const std::vector<SourceDescriptor>& a_sources,
		const std::unordered_map<Category, Curve>& a_curves,
		const std::uint32_t a_playerLevel,
		const std::uint64_t a_seed,
		const std::uint32_t a_hardCellCap)
	{
		auto plan = BoundedEncounters::BuildSpawnPlan(
			a_sources,
			a_curves,
			a_playerLevel,
			a_seed,
			std::optional<std::uint32_t>{ a_hardCellCap });
		return plan;
	}

	[[nodiscard]] std::vector<SourceDescriptor> MakeCategorySources(
		const std::uint32_t a_count,
		const Category a_category)
	{
		std::vector<SourceDescriptor> sources;
		sources.reserve(a_count);
		for (std::uint32_t index = 0; index < a_count; ++index) {
			sources.push_back({ static_cast<std::uint64_t>(index) + 1U, a_category });
		}
		return sources;
	}

	[[nodiscard]] std::vector<SourceDescriptor> MakeMixedSources(const std::uint32_t a_count)
	{
		std::vector<SourceDescriptor> sources;
		sources.reserve(a_count);
		for (std::uint32_t index = 0; index < a_count; ++index) {
			sources.push_back({
				static_cast<std::uint64_t>(index) + 1U,
				kMixedCategoryPattern[index % kMixedCategoryPattern.size()] });
		}
		return sources;
	}

	[[nodiscard]] std::unordered_map<Category, std::uint32_t> CountCategories(
		const std::vector<SourceDescriptor>& a_sources)
	{
		std::unordered_map<Category, std::uint32_t> counts;
		for (const auto& source : a_sources) {
			++counts[source.category];
		}
		return counts;
	}

	[[nodiscard]] Capacity BuildCapacity(
		const BoundedEncounters::Config& a_config,
		const bool a_interior,
		const std::uint32_t a_existingHostiles,
		const std::uint32_t a_existingActiveOwned)
	{
		Capacity capacity;
		capacity.additionalCellCap = a_interior ?
			a_config.limits.maxAdditionalInterior : a_config.limits.maxAdditionalExterior;
		capacity.hostileCellCap = a_interior ?
			a_config.limits.maxHostilesInterior : a_config.limits.maxHostilesExterior;
		capacity.existingCellHostiles = a_existingHostiles;
		capacity.globalActiveOwnedCap = std::max(
			a_config.limits.maxHostilesInterior,
			a_config.limits.maxHostilesExterior);
		capacity.existingActiveOwned = a_existingActiveOwned;
		capacity.remainingHostileCapacity = a_existingHostiles >= capacity.hostileCellCap ?
			0U : capacity.hostileCellCap - a_existingHostiles;
		capacity.remainingActiveOwnedCapacity = a_existingActiveOwned >= capacity.globalActiveOwnedCap ?
			0U : capacity.globalActiveOwnedCap - a_existingActiveOwned;
		capacity.effectiveAdditionalCap = std::min({
			capacity.additionalCellCap,
			capacity.remainingHostileCapacity,
			capacity.remainingActiveOwnedCapacity,
			kMaximumSpawnsPerEvaluation });
		return capacity;
	}

	[[nodiscard]] nlohmann::json CapacityJson(
		const Capacity& a_capacity,
		const std::uint32_t a_eligibleSources)
	{
		return {
			{ "additionalCellCap", a_capacity.additionalCellCap },
			{ "hostileCellCap", a_capacity.hostileCellCap },
			{ "existingCellHostiles", a_capacity.existingCellHostiles },
			{ "eligibleAuthoredSources", a_eligibleSources },
			{ "otherExistingCellHostiles",
				a_capacity.existingCellHostiles > a_eligibleSources ?
					a_capacity.existingCellHostiles - a_eligibleSources : 0U },
			{ "remainingHostileCapacity", a_capacity.remainingHostileCapacity },
			{ "globalActiveOwnedCap", a_capacity.globalActiveOwnedCap },
			{ "existingActiveOwned", a_capacity.existingActiveOwned },
			{ "remainingGlobalActiveOwnedCapacity", a_capacity.remainingActiveOwnedCapacity },
			{ "perEvaluationCap", kMaximumSpawnsPerEvaluation },
			{ "effectiveAdditionalCap", a_capacity.effectiveAdditionalCap }
		};
	}

	[[nodiscard]] nlohmann::json CategoryBreakdown(
		const std::unordered_map<Category, std::uint32_t>& a_sourceCounts,
		const CapacityProjection& a_projection,
		const BoundedEncounters::SpawnPlan& a_plan)
	{
		std::unordered_map<Category, std::uint32_t> sampledByCategory;
		for (const auto& roll : a_plan.sources) {
			sampledByCategory[roll.category] += roll.extras;
		}

		nlohmann::json breakdown;
		for (const auto category : kCategories) {
			breakdown[BoundedEncounters::ToString(category)] = {
				{ "authoredSources", CategoryValue(a_sourceCounts, category) },
				{ "uncappedExpectedExtras", CategoryValue(a_projection.uncappedExpectedByCategory, category) },
				{ "cappedFractionalCapacityExtras",
					CategoryValue(a_projection.cappedFractionalCapacityByCategory, category) },
				{ "sampledExtras", CategoryValue(sampledByCategory, category) }
			};
		}
		return breakdown;
	}

	[[nodiscard]] nlohmann::json MixedRows(
		const std::vector<SourceDescriptor>& a_sources,
		const std::unordered_map<Category, std::uint32_t>& a_sourceCounts,
		const BoundedEncounters::Config& a_config,
		const Capacity& a_capacity,
		const std::uint64_t a_auditSeed)
	{
		nlohmann::json rows = nlohmann::json::array();
		for (const auto level : kLevels) {
			const auto projection = ProjectFractionalCapacity(
				a_sources,
				a_config.curves,
				level,
				a_auditSeed,
				a_capacity.effectiveAdditionalCap);
			const auto plan = BuildCapacityPlan(
				a_sources,
				a_config.curves,
				level,
				a_auditSeed,
				a_capacity.effectiveAdditionalCap);

			rows.push_back({
				{ "level", level },
				{ "uncappedExpectedExtras", projection.uncappedExpectedExtras },
				{ "cappedFractionalCapacityExtras", projection.cappedFractionalCapacityExtras },
				{ "sampledExtras", plan.totalExtras },
				{ "uncappedExpectedEligiblePopulation",
					static_cast<double>(a_sources.size()) + projection.uncappedExpectedExtras },
				{ "cappedFractionalCapacityEligiblePopulation",
					static_cast<double>(a_sources.size()) + projection.cappedFractionalCapacityExtras },
				{ "sampledEligiblePopulation", a_sources.size() + plan.totalExtras },
				{ "cappedFractionalCapacityCellHostiles",
					static_cast<double>(a_capacity.existingCellHostiles) +
						projection.cappedFractionalCapacityExtras },
				{ "sampledCellHostiles", a_capacity.existingCellHostiles + plan.totalExtras },
				{ "byCategory", CategoryBreakdown(a_sourceCounts, projection, plan) }
			});
		}
		return rows;
	}

	[[nodiscard]] std::uint64_t Fnv1a64(const std::string_view a_bytes) noexcept
	{
		std::uint64_t hash = 14695981039346656037ULL;
		for (const unsigned char byte : a_bytes) {
			hash ^= byte;
			hash *= 1099511628211ULL;
		}
		return hash;
	}

	[[nodiscard]] std::string LowerHex64(std::uint64_t a_value)
	{
		constexpr std::string_view digits = "0123456789abcdef";
		std::string output(16, '0');
		for (auto index = output.size(); index > 0; --index) {
			output[index - 1] = digits[a_value & 0xFU];
			a_value >>= 4U;
		}
		return output;
	}
}

int main(int a_argc, char** a_argv)
{
	try {
		if (a_argc < 2 || a_argc > 4) {
			throw CommandLineError("wrong number of arguments");
		}

		const auto sourceCount = a_argc >= 3 ?
			ParseUnsigned<std::uint32_t>(a_argv[2], "source-count") : kDefaultSourceCount;
		if (sourceCount == 0 || sourceCount > kMaximumSourceCount) {
			throw CommandLineError("source-count must be in the inclusive range 1..100000");
		}
		const auto config = BoundedEncounters::LoadConfig(std::filesystem::path(a_argv[1]));
		const auto effectiveSeed = a_argc >= 4 ?
			ParseUnsigned<std::uint64_t>(a_argv[3], "seed") : config.seed;

		nlohmann::json output;
		output["schemaVersion"] = 1;
		output["sourceCount"] = sourceCount;
		output["seed"] = effectiveSeed;
		output["configurationMode"] = {
			{ "enabled", config.enabled },
			{ "observeOnly", config.observeOnly }
		};
		output["projectionSemantics"] = {
			{ "uncappedExpectedExtras",
				"Sum of per-source curve expectations after per-source multiplier and count limits, "
				"before category and cell-cap competition." },
			{ "cappedFractionalCapacityExtras",
				"Sum of fractional per-source expectations admitted in deterministic source-rank "
				"order through category and applicable cell caps. This is a capacity projection, "
				"not the statistical expected value after capped Bernoulli outcomes." },
			{ "sampledExtras",
				"Deterministic stable-threshold realization after the same applicable caps." }
		};

		for (const auto category : kCategories) {
			nlohmann::json rows = nlohmann::json::array();
			const auto sources = MakeCategorySources(sourceCount, category);
			const auto& curve = config.curves.at(category);
			for (const auto level : kLevels) {
				const auto projection = ProjectFractionalCapacity(
					sources, config.curves, level, effectiveSeed, std::nullopt);
				const auto plan = BoundedEncounters::BuildSpawnPlan(
					sources, config.curves, level, effectiveSeed, std::nullopt);
				rows.push_back({
					{ "level", level },
					{ "authoredSources", sourceCount },
					{ "expectedExtrasPerSource", BoundedEncounters::ExpectedExtrasPerSource(curve, level) },
					{ "uncappedExpectedExtras", projection.uncappedExpectedExtras },
					{ "cappedFractionalCapacityExtras", projection.cappedFractionalCapacityExtras },
					{ "sampledExtras", plan.totalExtras },
					{ "uncappedExpectedTotal",
						static_cast<double>(sourceCount) + projection.uncappedExpectedExtras },
					{ "cappedFractionalCapacityTotal",
						static_cast<double>(sourceCount) + projection.cappedFractionalCapacityExtras },
					{ "sampledTotal", sourceCount + plan.totalExtras }
				});
			}
			const auto categoryName = BoundedEncounters::ToString(category);
			output["categoryCellCaps"][categoryName] = curve.maxExtrasPerCell;
			output["categories"][categoryName] = std::move(rows);
		}

		const auto mixedSources = MakeMixedSources(sourceCount);
		const auto mixedSourceCounts = CountCategories(mixedSources);
		const auto activeOwnedCap = std::max(
			config.limits.maxHostilesInterior,
			config.limits.maxHostilesExterior);
		const auto auditSeed = BoundedEncounters::MixSeed(effectiveSeed, kAuditSeedDomain);
		output["mixedCategoryAudit"]["description"] =
			"A deterministic 5:2:1 general/animal/giant source pattern. Each environment is evaluated "
			"first with only its authored population and then with unrelated hostiles plus an attached-area "
			"owned population that leaves at most three global slots.";
		output["mixedCategoryAudit"]["plannerSeed"] = auditSeed;
		output["mixedCategoryAudit"]["sourceCounts"] = {
			{ "general", CategoryValue(mixedSourceCounts, Category::General) },
			{ "animalBeast", CategoryValue(mixedSourceCounts, Category::AnimalBeast) },
			{ "giantMammoth", CategoryValue(mixedSourceCounts, Category::GiantMammoth) }
		};

		for (const bool interior : { true, false }) {
			const auto environmentName = interior ? "interior" : "exterior";
			const auto hostileCap = interior ?
				config.limits.maxHostilesInterior : config.limits.maxHostilesExterior;
			const auto authoredPopulationCapacity = BuildCapacity(config, interior, sourceCount, 0);
			const auto constrainedExistingHostiles = std::max(
				sourceCount,
				hostileCap > 4 ? hostileCap - 4U : 0U);
			const auto constrainedActiveOwned = activeOwnedCap > 3 ? activeOwnedCap - 3U : 0U;
			const auto constrainedCapacity = BuildCapacity(
				config, interior, constrainedExistingHostiles, constrainedActiveOwned);

			for (const auto& [caseName, capacity] : std::array{
					std::pair{ std::string_view("authoredPopulationOnly"), authoredPopulationCapacity },
					std::pair{ std::string_view("constrainedAttachedArea"), constrainedCapacity } }) {
				output["mixedCategoryAudit"]["environments"][environmentName][caseName] = {
					{ "capacity", CapacityJson(capacity, sourceCount) },
					{ "levels", MixedRows(
						mixedSources,
						mixedSourceCounts,
						config,
						capacity,
						auditSeed) }
				};
			}
		}

		const auto canonicalPayload = output.dump();
		output["repeatability"] = {
			{ "algorithm", "FNV-1a-64" },
			{ "scope", "canonical compact JSON excluding the repeatability object" },
			{ "fingerprint", LowerHex64(Fnv1a64(canonicalPayload)) }
		};

		std::cout << output.dump(2) << '\n';
		return 0;
	} catch (const CommandLineError& error) {
		const auto diagnostic = BoundedEncounters::MakeBoundedDiagnostic(error.what());
		std::cerr << "error: " << diagnostic.View() << '\n';
		PrintUsage();
		return 64;
	} catch (const std::exception& error) {
		const auto diagnostic = BoundedEncounters::MakeBoundedDiagnostic(error.what());
		std::cerr << "error: " << diagnostic.View() << '\n';
		return 1;
	}
}
