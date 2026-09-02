#include "CapacityModel.h"
#include "Config.h"
#include "Diagnostics.h"
#include "SpawnModel.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
	using BoundedEncounters::Category;
	using BoundedEncounters::Config;
	using BoundedEncounters::Curve;
	using BoundedEncounters::SourceDescriptor;
	using BoundedEncounters::SourceRoll;
	using BoundedEncounters::SpawnPlan;

	class TestSuite
	{
	public:
		void Check(const bool a_condition, const std::string_view a_message)
		{
			++checks_;
			if (!a_condition) {
				++failures_;
				std::cerr << "FAILED: " << a_message << '\n';
			}
		}

		void CheckNear(
			const double a_actual,
			const double a_expected,
			const double a_tolerance,
			const std::string_view a_message)
		{
			Check(std::abs(a_actual - a_expected) <= a_tolerance, a_message);
		}

		template <class F>
		void CheckThrows(F&& a_action, const std::string_view a_message)
		{
			bool threw = false;
			try {
				std::invoke(std::forward<F>(a_action));
			} catch (const std::exception&) {
				threw = true;
			} catch (...) {
				threw = true;
			}
			Check(threw, a_message);
		}

		template <class F>
		void CheckDoesNotThrow(F&& a_action, const std::string_view a_message)
		{
			bool threw = false;
			try {
				std::invoke(std::forward<F>(a_action));
			} catch (...) {
				threw = true;
			}
			Check(!threw, a_message);
		}

		[[nodiscard]] int Result() const
		{
			if (failures_ == 0) {
				std::cout << "SpawnModelTests: " << checks_ << " checks passed\n";
				return 0;
			}
			std::cerr << "SpawnModelTests: " << failures_ << " of " << checks_ << " checks failed\n";
			return 1;
		}

	private:
		std::size_t checks_{ 0 };
		std::size_t failures_{ 0 };
	};

	class TemporaryDirectory
	{
	public:
		TemporaryDirectory()
		{
			path_ = std::filesystem::temp_directory_path() / "BoundedEncounters-SpawnModelTests";
			std::error_code ignored;
			std::filesystem::remove_all(path_, ignored);
			std::filesystem::create_directories(path_);
		}

		~TemporaryDirectory()
		{
			std::error_code ignored;
			std::filesystem::remove_all(path_, ignored);
		}

		TemporaryDirectory(const TemporaryDirectory&) = delete;
		TemporaryDirectory& operator=(const TemporaryDirectory&) = delete;

		[[nodiscard]] const std::filesystem::path& Path() const noexcept { return path_; }

	private:
		std::filesystem::path path_;
	};

	void WriteTextFile(const std::filesystem::path& a_path, const std::string_view a_contents)
	{
		std::ofstream stream(a_path, std::ios::binary | std::ios::trunc);
		if (!stream) {
			throw std::runtime_error("could not create test fixture: " + a_path.string());
		}
		stream.write(a_contents.data(), static_cast<std::streamsize>(a_contents.size()));
		if (!stream) {
			throw std::runtime_error("could not write test fixture: " + a_path.string());
		}
	}

	[[nodiscard]] std::string CompleteConfigFixture()
	{
		return R"json({
			"schemaVersion":1,"enabled":true,"observeOnly":true,"debugLogging":false,"seed":42,
			"curves":{
				"general":{"enabled":true,"ratePerLevel":0.05,"baselineLevel":1,"maxMultiplier":3.0,"maxExtrasPerSource":2,"maxExtrasPerCell":12},
				"animalBeast":{"enabled":true,"ratePerLevel":0.025,"baselineLevel":1,"maxMultiplier":2.0,"maxExtrasPerSource":1,"maxExtrasPerCell":6},
				"giantMammoth":{"enabled":true,"ratePerLevel":0.01,"baselineLevel":1,"maxMultiplier":1.5,"maxExtrasPerSource":1,"maxExtrasPerCell":2}
			},
			"limits":{"maxAdditionalInterior":12,"maxAdditionalExterior":20,"maxHostilesInterior":24,"maxHostilesExterior":40,"maximumExteriorDistance":12000.0,"placementRadiusMin":96.0,"placementRadiusMax":256.0,"maximumNavmeshSnapDistance":256.0},
			"exclusions":{"dragons":true,"unique":true,"essential":true,"protected":true,"nonRespawning":true,"persistentReferences":true,"questAliases":true,"locationBosses":true,"summons":true,"commandedActors":true},
			"allowedSourcePlugins":["Skyrim.esm","Update.esm","Dawnguard.esm","HearthFires.esm","Dragonborn.esm"],
			"deniedPlugins":[]
		})json";
	}

	[[nodiscard]] std::string ReplaceOnce(
		std::string a_text,
		const std::string_view a_needle,
		const std::string_view a_replacement)
	{
		const auto position = a_text.find(a_needle);
		if (position == std::string::npos) {
			throw std::logic_error("test fixture replacement target was not found");
		}
		a_text.replace(position, a_needle.size(), a_replacement);
		return a_text;
	}

	[[nodiscard]] std::unordered_map<Category, Curve> OneCurve(
		const Category a_category,
		const Curve& a_curve)
	{
		return { { a_category, a_curve } };
	}

	[[nodiscard]] const SourceRoll& RollFor(const SpawnPlan& a_plan, const std::uint64_t a_sourceKey)
	{
		const auto result = std::ranges::find(a_plan.sources, a_sourceKey, &SourceRoll::sourceKey);
		if (result == a_plan.sources.end()) {
			throw std::logic_error("spawn plan omitted a requested source key");
		}
		return *result;
	}

	void TestCategoryConversions(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		for (const auto category :
			 { Category::General, Category::AnimalBeast, Category::GiantMammoth, Category::Excluded }) {
			a_tests.Check(CategoryFromString(ToString(category)) == category, "category string conversion round-trips");
		}
		a_tests.Check(ToString(static_cast<Category>(255)) == "excluded", "unknown category values stringify safely");
		a_tests.CheckThrows(
			[] { (void)CategoryFromString("animals"); },
			"unknown category names are rejected");
		a_tests.CheckThrows(
			[] { (void)CategoryFromString(""); },
			"empty category names are rejected");
	}

	void TestDefaultConfigurationContract(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const auto config = DefaultConfig();
		a_tests.Check(config.schemaVersion == 1, "default schema is version 1");
		a_tests.Check(config.enabled, "default configuration is enabled");
		a_tests.Check(config.observeOnly, "default configuration is observe-only");
		a_tests.Check(config.seed == 1869507693ULL, "default seed matches the shipping configuration");
		a_tests.Check(config.curves.size() == 3, "default configuration has three eligible categories");
		a_tests.Check(config.curves.contains(Category::General), "default configuration has a general curve");
		a_tests.Check(config.curves.contains(Category::AnimalBeast), "default configuration has an animal curve");
		a_tests.Check(config.curves.contains(Category::GiantMammoth), "default configuration has a giant curve");
		a_tests.Check(!config.curves.contains(Category::Excluded), "excluded is not an eligible curve");
		a_tests.CheckNear(config.curves.at(Category::General).ratePerLevel, 0.05, 0.0, "default general rate is 5 percent");
		a_tests.CheckNear(config.curves.at(Category::AnimalBeast).ratePerLevel, 0.025, 0.0, "default animal rate is 2.5 percent");
		a_tests.CheckNear(config.curves.at(Category::GiantMammoth).ratePerLevel, 0.01, 0.0, "default giant rate is 1 percent");
		a_tests.Check(config.allowedSourcePlugins.size() == 5, "default source allowlist contains the five official masters");
		a_tests.Check(config.allowedSourcePlugins.front() == "Skyrim.esm", "default source allowlist begins with Skyrim.esm");
		a_tests.Check(config.allowedSourcePlugins.back() == "Dragonborn.esm", "default source allowlist includes Dragonborn.esm");
		a_tests.CheckDoesNotThrow([&config] { ValidateConfig(config); }, "default configuration validates");
	}

	void TestExpectedValueBoundaries(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const Curve uncapped{ true, 0.05, 1, 0.0, 0, 0 };
		a_tests.CheckNear(ExpectedExtrasPerSource(uncapped, 0), 0.0, 0.0, "level zero is below baseline");
		a_tests.CheckNear(ExpectedExtrasPerSource(uncapped, 1), 0.0, 0.0, "baseline level has no extras");
		a_tests.CheckNear(ExpectedExtrasPerSource(uncapped, 2), 0.05, 1.0e-12, "first level above baseline adds one rate step");
		a_tests.CheckNear(ExpectedExtrasPerSource(uncapped, 10), 0.45, 1.0e-12, "level ten uses nine rate steps");

		Curve disabled = uncapped;
		disabled.enabled = false;
		a_tests.CheckNear(ExpectedExtrasPerSource(disabled, 100), 0.0, 0.0, "disabled curves produce zero expectation");

		Curve zeroRate = uncapped;
		zeroRate.ratePerLevel = 0.0;
		a_tests.CheckNear(ExpectedExtrasPerSource(zeroRate, 100), 0.0, 0.0, "zero rate produces zero expectation");

		Curve defensiveNegativeRate = uncapped;
		defensiveNegativeRate.ratePerLevel = -0.5;
		a_tests.CheckNear(ExpectedExtrasPerSource(defensiveNegativeRate, 100), 0.0, 0.0, "model defensively rejects a negative rate");

		Curve multiplierCap = uncapped;
		multiplierCap.maxMultiplier = 1.5;
		a_tests.CheckNear(ExpectedExtrasPerSource(multiplierCap, 100), 0.5, 0.0, "multiplier cap is expressed above the authored source");

		Curve sourceCap = uncapped;
		sourceCap.maxExtrasPerSource = 2;
		a_tests.CheckNear(ExpectedExtrasPerSource(sourceCap, 100), 2.0, 0.0, "per-source cap limits expectation");
		a_tests.Check(PassesNonRespawningExclusion(true), "a respawning actor base passes the non-respawning exclusion");
		a_tests.Check(!PassesNonRespawningExclusion(false), "a non-respawning actor base fails the non-respawning exclusion");

		Curve combinedCaps = uncapped;
		combinedCaps.maxMultiplier = 2.75;
		combinedCaps.maxExtrasPerSource = 1;
		a_tests.CheckNear(ExpectedExtrasPerSource(combinedCaps, 100), 1.0, 0.0, "the stricter source cap wins");

		Curve belowOneMultiplier = uncapped;
		belowOneMultiplier.maxMultiplier = 0.5;
		a_tests.CheckNear(ExpectedExtrasPerSource(belowOneMultiplier, 100), 0.0, 0.0, "multiplier below one cannot create negative extras");

		Curve hugeBaseline = uncapped;
		hugeBaseline.baselineLevel = std::numeric_limits<std::uint32_t>::max();
		a_tests.CheckNear(
			ExpectedExtrasPerSource(hugeBaseline, std::numeric_limits<std::uint32_t>::max()),
			0.0,
			0.0,
			"maximum player level does not underflow at maximum baseline");
	}

	void TestExpectedValueMonotonicity(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const Curve curve{ true, 0.05, 1, 3.0, 2, 0 };
		double previous = 0.0;
		for (std::uint32_t level = 0; level <= 250; ++level) {
			const auto current = ExpectedExtrasPerSource(curve, level);
			a_tests.Check(current + 1.0e-12 >= previous, "expected extras are monotonic by player level");
			a_tests.Check(current <= 2.0, "expected extras never exceed the configured cap");
			previous = current;
		}
		a_tests.CheckNear(ExpectedExtrasPerSource(curve, 21), 1.0, 1.0e-12, "5 percent curve reaches one extra at level 21");
		a_tests.CheckNear(ExpectedExtrasPerSource(curve, 41), 2.0, 1.0e-12, "5 percent curve reaches cap at level 41");
		a_tests.CheckNear(ExpectedExtrasPerSource(curve, 250), 2.0, 0.0, "expectation remains at cap thereafter");

		std::vector<SourceDescriptor> sources;
		for (std::uint64_t key = 1; key <= 128; ++key) {
			sources.push_back({ key, Category::General });
		}
		std::unordered_map<std::uint64_t, std::uint32_t> priorRolls;
		for (std::uint32_t level = 0; level <= 100; ++level) {
			const auto plan = BuildSpawnPlan(sources, OneCurve(Category::General, curve), level, 0xA11CE, std::nullopt);
			for (const auto& roll : plan.sources) {
				const auto prior = priorRolls.contains(roll.sourceKey) ? priorRolls.at(roll.sourceKey) : 0U;
				a_tests.Check(roll.extras >= prior, "uncapped deterministic source rolls are monotonic by level");
				priorRolls[roll.sourceKey] = roll.extras;
			}
		}
	}

	void TestDeterministicPlans(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const Curve curve{ true, 0.01, 1, 0.0, 0, 0 };
		const auto curves = OneCurve(Category::General, curve);
		std::vector<SourceDescriptor> sources;
		for (std::uint64_t key = 1; key <= 512; ++key) {
			sources.push_back({ key, Category::General });
		}

		const auto first = BuildSpawnPlan(sources, curves, 38, 0x123456789ABCDEF0ULL, std::nullopt);
		const auto second = BuildSpawnPlan(sources, curves, 38, 0x123456789ABCDEF0ULL, std::nullopt);
		a_tests.Check(first.totalExtras == second.totalExtras, "identical inputs reproduce total extras");
		a_tests.CheckNear(first.expectedExtras, second.expectedExtras, 0.0, "identical inputs reproduce expected totals");
		a_tests.Check(first.sources.size() == second.sources.size(), "identical inputs reproduce result cardinality");
		for (const auto& source : sources) {
			const auto& firstRoll = RollFor(first, source.sourceKey);
			const auto& secondRoll = RollFor(second, source.sourceKey);
			a_tests.Check(firstRoll.category == secondRoll.category, "source category is deterministic");
			a_tests.Check(firstRoll.extras == secondRoll.extras, "per-source roll is deterministic");
			a_tests.CheckNear(firstRoll.expectedExtras, secondRoll.expectedExtras, 0.0, "per-source expectation is deterministic");
		}

		const auto anotherSeed = BuildSpawnPlan(sources, curves, 38, 0x0FEDCBA987654321ULL, std::nullopt);
		const auto anySeedDifference = std::ranges::any_of(sources, [&](const SourceDescriptor& a_source) {
			return RollFor(first, a_source.sourceKey).extras != RollFor(anotherSeed, a_source.sourceKey).extras;
		});
		a_tests.Check(anySeedDifference, "changing the global seed changes at least one per-source roll");

		a_tests.Check(MixSeed(42, 99) == MixSeed(42, 99), "seed mixing is deterministic");
		a_tests.Check(MixSeed(42, 99) != MixSeed(42, 100), "seed mixing includes source identity");
		a_tests.Check(MixSeed(42, 99) != MixSeed(43, 99), "seed mixing includes global seed");
		a_tests.Check(
			SpawnAdmissionRank(42, 99) != SpawnFractionRoll(42, 99),
			"admission ranking and fractional rolling use separate random domains");
	}

	void TestInputOrdering(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const Curve curve{ true, 0.01, 1, 0.0, 0, 0 };
		const auto curves = OneCurve(Category::General, curve);
		std::vector<SourceDescriptor> ascending;
		for (std::uint64_t key = 100; key < 200; ++key) {
			ascending.push_back({ key, Category::General });
		}
		auto descending = ascending;
		std::reverse(descending.begin(), descending.end());

		const auto forward = BuildSpawnPlan(ascending, curves, 44, 8675309, std::nullopt);
		const auto reverse = BuildSpawnPlan(descending, curves, 44, 8675309, std::nullopt);
		a_tests.Check(forward.totalExtras == reverse.totalExtras, "uncapped total is independent of input ordering");
		a_tests.CheckNear(forward.expectedExtras, reverse.expectedExtras, 0.0, "uncapped expectation is independent of input ordering");

		for (const auto& source : ascending) {
			const auto& forwardRoll = RollFor(forward, source.sourceKey);
			const auto& reverseRoll = RollFor(reverse, source.sourceKey);
			a_tests.Check(forwardRoll.extras == reverseRoll.extras, "uncapped source rolls are independent of input ordering");
			a_tests.CheckNear(forwardRoll.expectedExtras, reverseRoll.expectedExtras, 0.0, "uncapped source expectations are independent of input ordering");
		}

		const Curve guaranteedOne{ true, 1.0, 0, 0.0, 1, 0 };
		const auto cappedForward = BuildSpawnPlan(
			ascending,
			OneCurve(Category::General, guaranteedOne),
			1,
			8675309,
			2);
		const auto cappedReverse = BuildSpawnPlan(
			descending,
			OneCurve(Category::General, guaranteedOne),
			1,
			8675309,
			2);
		a_tests.Check(cappedForward.totalExtras == 2 && cappedReverse.totalExtras == 2, "global capped total is order invariant");
		for (const auto& source : ascending) {
			a_tests.Check(
				RollFor(cappedForward, source.sourceKey).extras == RollFor(cappedReverse, source.sourceKey).extras,
				"capped winner identity is input-order invariant by source key");
		}

		auto expectedAdmission = ascending;
		std::ranges::sort(expectedAdmission, [](const SourceDescriptor& a_left, const SourceDescriptor& a_right) {
			const auto leftRank = SpawnAdmissionRank(8675309, a_left.sourceKey);
			const auto rightRank = SpawnAdmissionRank(8675309, a_right.sourceKey);
			return leftRank != rightRank ? leftRank < rightRank : a_left.sourceKey < a_right.sourceKey;
		});
		for (std::size_t rank = 0; rank < expectedAdmission.size(); ++rank) {
			const auto expectedExtras = rank < 2 ? 1U : 0U;
			a_tests.Check(
				RollFor(cappedForward, expectedAdmission[rank].sourceKey).extras == expectedExtras,
				"global cap admission follows stable seed-derived rank");
		}
	}

	void TestFractionalCapacityAdmissionOrdering(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		constexpr std::uint64_t seed = 1;
		constexpr std::uint64_t rawWinner = 1;
		constexpr std::uint64_t admissionWinner = 2;
		const std::vector<SourceDescriptor> sources{
			{ rawWinner, Category::General },
			{ admissionWinner, Category::AnimalBeast }
		};
		const Curve guaranteedOne{ true, 1.0, 0, 0.0, 1, 0 };
		const std::unordered_map<Category, Curve> curves{
			{ Category::General, guaranteedOne },
			{ Category::AnimalBeast, guaranteedOne }
		};

		a_tests.Check(
			MixSeed(seed, rawWinner) < MixSeed(seed, admissionWinner),
			"projection admission fixture would select the other category with an undomained raw seed mix");
		a_tests.Check(
			SpawnAdmissionRank(seed, admissionWinner) < SpawnAdmissionRank(seed, rawWinner),
			"projection admission fixture has a distinct domain-separated winner");

		const auto projection = ProjectFractionalCapacity(sources, curves, 1, seed, 1);
		const auto plan = BuildSpawnPlan(sources, curves, 1, seed, 1);
		a_tests.CheckNear(projection.uncappedExpectedExtras, 2.0, 0.0, "projection preserves both uncapped source expectations");
		a_tests.CheckNear(projection.cappedFractionalCapacityExtras, 1.0, 0.0, "projection applies the one-slot global cap");
		a_tests.CheckNear(
			projection.cappedFractionalCapacityByCategory.at(Category::General),
			0.0,
			0.0,
			"projection blocks the lower-priority raw-mix winner");
		a_tests.CheckNear(
			projection.cappedFractionalCapacityByCategory.at(Category::AnimalBeast),
			1.0,
			0.0,
			"projection admits the domain-separated rank winner");
		a_tests.Check(RollFor(plan, rawWinner).extras == 0, "runtime planner blocks the same lower-priority source");
		a_tests.Check(RollFor(plan, admissionWinner).extras == 1, "runtime planner admits the same winning source");

		const Curve halfChance{ true, 0.5, 0, 0.0, 1, 0 };
		const std::vector<SourceDescriptor> halfChanceSources{
			{ 10, Category::General },
			{ 11, Category::General }
		};
		const auto halfChanceProjection = ProjectFractionalCapacity(
			halfChanceSources,
			OneCurve(Category::General, halfChance),
			1,
			seed,
			1);
		a_tests.CheckNear(
			halfChanceProjection.cappedFractionalCapacityExtras,
			1.0,
			0.0,
			"two half-unit demands project to one full capacity unit, not their 0.75 capped statistical expectation");
	}

	void TestCanonicalExpectationAccumulation(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const std::unordered_map<Category, Curve> curves{
			{ Category::General, Curve{ true, 0.45, 1, 0.0, 0, 0 } },
			{ Category::AnimalBeast, Curve{ true, 0.225, 1, 0.0, 0, 0 } },
			{ Category::GiantMammoth, Curve{ true, 0.09, 1, 0.0, 0, 0 } }
		};
		std::vector<SourceDescriptor> sources;
		sources.reserve(100000);
		for (std::uint64_t key = 1; key <= 100000; ++key) {
			const auto category = key % 8 == 0 ? Category::GiantMammoth :
				(key % 4 == 0 ? Category::AnimalBeast : Category::General);
			sources.push_back({ key, category });
		}

		constexpr std::uint64_t firstSeed = 0x0123456789ABCDEFULL;
		constexpr std::uint64_t secondSeed = 0xFEDCBA9876543210ULL;
		const auto firstPlan = BuildSpawnPlan(sources, curves, 2, firstSeed, std::nullopt);
		const auto secondPlan = BuildSpawnPlan(sources, curves, 2, secondSeed, std::nullopt);
		const auto firstProjection = ProjectFractionalCapacity(sources, curves, 2, firstSeed, std::nullopt);
		const auto secondProjection = ProjectFractionalCapacity(sources, curves, 2, secondSeed, std::nullopt);

		a_tests.Check(
			firstPlan.expectedExtras == secondPlan.expectedExtras,
			"uncapped planner expectation is bit-stable when only the admission seed changes");
		a_tests.Check(
			firstProjection.uncappedExpectedExtras == secondProjection.uncappedExpectedExtras,
			"uncapped projection total is bit-stable when only the admission seed changes");
		for (const auto category : { Category::General, Category::AnimalBeast, Category::GiantMammoth }) {
			a_tests.Check(
				firstProjection.uncappedExpectedByCategory.at(category) ==
					secondProjection.uncappedExpectedByCategory.at(category),
				"uncapped category projection is bit-stable when only the admission seed changes");
		}
	}

	void TestStatisticalExpectations(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		constexpr std::uint64_t sampleCount = 100000;
		std::vector<SourceDescriptor> sources;
		sources.reserve(sampleCount);
		for (std::uint64_t key = 1; key <= sampleCount; ++key) {
			sources.push_back({ key, Category::General });
		}

		const Curve fractionalCurve{ true, 0.37, 0, 0.0, 0, 0 };
		const auto fractionalPlan = BuildSpawnPlan(
			sources,
			OneCurve(Category::General, fractionalCurve),
			1,
			0xD15EA5E5ULL,
			std::nullopt);
		const auto fractionalMean = static_cast<double>(fractionalPlan.totalExtras) / static_cast<double>(sampleCount);
		a_tests.CheckNear(fractionalMean, 0.37, 0.01, "Bernoulli rounding converges to fractional expectation");
		a_tests.CheckNear(fractionalPlan.expectedExtras, 37000.0, 1.0e-6, "fractional expected total is accumulated exactly enough");

		std::array<std::uint64_t, 4> rankBucketCounts{};
		std::array<std::uint64_t, 4> acceptedByRankBucket{};
		constexpr double inverse53Bits = 1.0 / 9007199254740992.0;
		for (const auto& source : sources) {
			const auto rankBits = SpawnAdmissionRank(0xD15EA5E5ULL, source.sourceKey);
			const auto rollBits = SpawnFractionRoll(0xD15EA5E5ULL, source.sourceKey);
			const auto bucket = static_cast<std::size_t>(rankBits >> 62U);
			++rankBucketCounts[bucket];
			const auto unitRoll = static_cast<double>(rollBits >> 11U) * inverse53Bits;
			acceptedByRankBucket[bucket] += static_cast<std::uint64_t>(unitRoll < 0.37);
		}
		for (std::size_t bucket = 0; bucket < rankBucketCounts.size(); ++bucket) {
			const auto conditionalAcceptance = static_cast<double>(acceptedByRankBucket[bucket]) /
				static_cast<double>(rankBucketCounts[bucket]);
			a_tests.CheckNear(
				conditionalAcceptance,
				0.37,
				0.015,
				"fractional acceptance is statistically independent of admission-rank quartile");
		}

		const Curve lowFraction{ true, 0.1, 0, 0.0, 1, 0 };
		const Curve highFraction{ true, 0.9, 0, 0.0, 1, 0 };
		const std::unordered_map<Category, Curve> mixedFractions{
			{ Category::General, lowFraction },
			{ Category::AnimalBeast, highFraction }
		};
		const std::vector<SourceDescriptor> competingSources{
			{ 0x1001, Category::General },
			{ 0x2002, Category::AnimalBeast }
		};
		std::uint64_t bothPassed = 0;
		std::uint64_t lowFractionWins = 0;
		std::uint64_t invalidCappedPlans = 0;
		for (std::uint64_t seed = 1; seed <= sampleCount; ++seed) {
			const auto lowUnit = static_cast<double>(SpawnFractionRoll(seed, 0x1001) >> 11U) * inverse53Bits;
			const auto highUnit = static_cast<double>(SpawnFractionRoll(seed, 0x2002) >> 11U) * inverse53Bits;
			if (lowUnit >= 0.1 || highUnit >= 0.9) {
				continue;
			}
			++bothPassed;
			const auto capped = BuildSpawnPlan(competingSources, mixedFractions, 1, seed, 1);
			if (capped.totalExtras != 1) {
				++invalidCappedPlans;
				continue;
			}
			lowFractionWins += RollFor(capped, 0x1001).extras;
		}
		a_tests.Check(bothPassed > 5000, "mixed-fraction cap fairness sample has enough joint successes");
		a_tests.Check(invalidCappedPlans == 0, "a one-slot global cap admits exactly one jointly successful source");
		a_tests.CheckNear(
			static_cast<double>(lowFractionWins) / static_cast<double>(bothPassed),
			0.5,
			0.03,
			"cap winner is unbiased when low- and high-fraction sources both roll successfully");

		const Curve wholePlusFractionCurve{ true, 0.137, 0, 0.0, 0, 0 };
		const auto wholePlusFractionPlan = BuildSpawnPlan(
			sources,
			OneCurve(Category::General, wholePlusFractionCurve),
			10,
			0xB0A1DEDULL,
			std::nullopt);
		const auto wholePlusFractionMean = static_cast<double>(wholePlusFractionPlan.totalExtras) / static_cast<double>(sampleCount);
		a_tests.CheckNear(wholePlusFractionMean, 1.37, 0.01, "stochastic rounding preserves whole plus fractional expectation");
		a_tests.Check(
			std::all_of(
				wholePlusFractionPlan.sources.begin(),
				wholePlusFractionPlan.sources.end(),
				[](const auto& a_roll) { return a_roll.extras == 1 || a_roll.extras == 2; }),
			"whole plus fractional rolls use adjacent integers only");
	}

	void TestCapsAndCategories(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		Curve general{ true, 1.0, 0, 0.0, 2, 5 };
		Curve animal{ true, 1.0, 0, 0.0, 1, 2 };
		const std::unordered_map<Category, Curve> curves{
			{ Category::General, general },
			{ Category::AnimalBeast, animal }
		};
		const std::vector<SourceDescriptor> generalSources{
			{ 1, Category::General },
			{ 2, Category::General },
			{ 3, Category::General },
			{ 4, Category::General }
		};

		const auto categoryCapped = BuildSpawnPlan(generalSources, curves, 10, 1, std::nullopt);
		a_tests.Check(categoryCapped.totalExtras == 5, "category cell cap is enforced");
		a_tests.Check(std::ranges::count(categoryCapped.sources, 2U, &SourceRoll::extras) == 2, "two ranked sources receive their per-source cap");
		a_tests.Check(std::ranges::count(categoryCapped.sources, 1U, &SourceRoll::extras) == 1, "category remainder is allocated without overflow");
		a_tests.Check(std::ranges::count(categoryCapped.sources, 0U, &SourceRoll::extras) == 1, "category cap blocks remaining source demand");
		a_tests.CheckNear(categoryCapped.expectedExtras, 8.0, 0.0, "expected total records pre-cell-cap demand");

		const auto globallyCapped = BuildSpawnPlan(generalSources, curves, 10, 1, 3);
		a_tests.Check(globallyCapped.totalExtras == 3, "global cell cap is enforced");
		a_tests.Check(std::ranges::count(globallyCapped.sources, 2U, &SourceRoll::extras) == 1, "global cap admits one complete allocation");
		a_tests.Check(std::ranges::count(globallyCapped.sources, 1U, &SourceRoll::extras) == 1, "global cap allocates only its remainder");
		a_tests.Check(std::ranges::count(globallyCapped.sources, 0U, &SourceRoll::extras) == 2, "global cap blocks remaining source demand");

		const std::vector<SourceDescriptor> mixedSources{
			{ 10, Category::General },
			{ 11, Category::AnimalBeast },
			{ 12, Category::General },
			{ 13, Category::AnimalBeast },
			{ 14, Category::AnimalBeast },
			{ 15, Category::General }
		};
		const auto mixed = BuildSpawnPlan(mixedSources, curves, 10, 9, std::nullopt);
		a_tests.Check(mixed.totalExtras == 7, "category caps are tracked independently");
		std::uint32_t generalTotal = 0;
		std::uint32_t animalTotal = 0;
		for (const auto& roll : mixed.sources) {
			if (roll.category == Category::General) {
				generalTotal += roll.extras;
			} else if (roll.category == Category::AnimalBeast) {
				animalTotal += roll.extras;
			}
		}
		a_tests.Check(generalTotal == 5, "general category observes its own cap");
		a_tests.Check(animalTotal == 2, "animal category observes its own cap");

		Curve unlimited = general;
		unlimited.maxExtrasPerSource = 0;
		unlimited.maxExtrasPerCell = 0;
		const auto noCapMeansUnlimited = BuildSpawnPlan(
			generalSources,
			OneCurve(Category::General, unlimited),
			3,
			3,
			std::nullopt);
		a_tests.Check(noCapMeansUnlimited.totalExtras == 12, "zero source/category caps and absent global cap mean unlimited");

		const auto hardZeroGlobalCap = BuildSpawnPlan(
			generalSources,
			OneCurve(Category::General, unlimited),
			3,
			3,
			std::optional<std::uint32_t>{ 0 });
		a_tests.Check(hardZeroGlobalCap.totalExtras == 0, "an explicit zero global cap is a hard stop");
		a_tests.Check(
			std::ranges::all_of(hardZeroGlobalCap.sources, [](const SourceRoll& a_roll) { return a_roll.extras == 0; }),
			"an explicit zero global cap clears every per-source admission");
	}

	void TestExcludedAndIneligibleSources(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		Curve enabled{ true, 1.0, 0, 0.0, 0, 0 };
		Curve disabled = enabled;
		disabled.enabled = false;
		const std::unordered_map<Category, Curve> curves{
			{ Category::General, enabled },
			{ Category::AnimalBeast, disabled }
		};
		const std::vector<SourceDescriptor> sources{
			{ 1, Category::Excluded },
			{ 2, Category::GiantMammoth },
			{ 3, Category::AnimalBeast },
			{ 4, Category::General }
		};
		const auto plan = BuildSpawnPlan(sources, curves, 10, 99, std::nullopt);

		a_tests.Check(plan.sources.size() == sources.size(), "every input source receives an auditable result");
		a_tests.Check(RollFor(plan, 1).extras == 0, "explicitly excluded sources produce no extras");
		a_tests.CheckNear(RollFor(plan, 1).expectedExtras, 0.0, 0.0, "excluded source expectation is zero");
		a_tests.Check(RollFor(plan, 2).extras == 0, "sources with no configured curve produce no extras");
		a_tests.CheckNear(RollFor(plan, 2).expectedExtras, 0.0, 0.0, "missing curve expectation is zero");
		a_tests.Check(RollFor(plan, 3).extras == 0, "disabled category produces no extras");
		a_tests.CheckNear(RollFor(plan, 3).expectedExtras, 0.0, 0.0, "disabled category expectation is zero");
		a_tests.Check(RollFor(plan, 4).extras == 10, "eligible source remains active beside excluded sources");
		a_tests.Check(plan.totalExtras == 10, "only eligible source contributes to total");

		const auto empty = BuildSpawnPlan({}, curves, 100, 7, 100);
		a_tests.Check(empty.sources.empty(), "empty input produces empty audit results");
		a_tests.Check(empty.totalExtras == 0, "empty input produces no extras");
		a_tests.CheckNear(empty.expectedExtras, 0.0, 0.0, "empty input produces zero expectation");
	}

	void TestConfigLoading(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		TemporaryDirectory temporary;
		const auto validPath = temporary.Path() / "valid-complete.json";
		WriteTextFile(
			validPath,
			R"json({
				// Comments are intentionally supported by the loader.
				"schemaVersion": 1,
				"enabled": false,
				"observeOnly": true,
				"debugLogging": true,
				"seed": 42,
				"curves": {
					"general": {
						"enabled": true,
						"ratePerLevel": 0.2,
						"baselineLevel": 5,
						"maxMultiplier": 2.5,
						"maxExtrasPerSource": 3,
						"maxExtrasPerCell": 9
					},
					"animalBeast": {
						"enabled": true,
						"ratePerLevel": 0.025,
						"baselineLevel": 1,
						"maxMultiplier": 2.0,
						"maxExtrasPerSource": 1,
						"maxExtrasPerCell": 6
					},
					"giantMammoth": {
						"enabled": true,
						"ratePerLevel": 0.01,
						"baselineLevel": 1,
						"maxMultiplier": 1.5,
						"maxExtrasPerSource": 1,
						"maxExtrasPerCell": 2
					}
				},
				"limits": {
					"maxAdditionalInterior": 8,
					"maxAdditionalExterior": 10,
					"maxHostilesInterior": 20,
					"maxHostilesExterior": 30,
					"maximumExteriorDistance": 9000.0,
					"placementRadiusMin": 80.0,
					"placementRadiusMax": 180.0,
					"maximumNavmeshSnapDistance": 220.0
				},
				"exclusions": {
					"dragons": true,
					"unique": true,
					"essential": true,
					"protected": true,
					"nonRespawning": true,
					"persistentReferences": true,
					"questAliases": true,
					"locationBosses": true,
					"summons": true,
					"commandedActors": true
				},
				"allowedSourcePlugins": ["Skyrim.esm", "Update.esm"],
				"deniedPlugins": ["Example.esp", "Another.esm"]
			})json");

		const auto loaded = LoadConfig(validPath);
		a_tests.Check(!loaded.enabled, "loader reads enabled override");
		a_tests.Check(loaded.observeOnly, "loader reads observe-only safety mode");
		a_tests.Check(loaded.debugLogging, "loader reads debug logging override");
		a_tests.Check(loaded.seed == 42, "loader reads deterministic seed");
		const auto& general = loaded.curves.at(Category::General);
		a_tests.CheckNear(general.ratePerLevel, 0.2, 0.0, "loader reads curve rate");
		a_tests.Check(general.baselineLevel == 5, "loader reads curve baseline");
		a_tests.CheckNear(general.maxMultiplier, 2.5, 0.0, "loader reads multiplier cap");
		a_tests.Check(general.maxExtrasPerSource == 3, "loader reads source cap");
		a_tests.Check(general.maxExtrasPerCell == 9, "loader reads category cell cap");
		a_tests.CheckNear(loaded.curves.at(Category::AnimalBeast).ratePerLevel, 0.025, 0.0, "loader reads animal curve");
		a_tests.CheckNear(loaded.curves.at(Category::GiantMammoth).ratePerLevel, 0.01, 0.0, "loader reads giant curve");
		a_tests.Check(loaded.limits.maxAdditionalInterior == 8, "loader reads interior additional cap");
		a_tests.Check(loaded.limits.maxAdditionalExterior == 10, "loader reads exterior additional cap");
		a_tests.Check(loaded.limits.maxHostilesInterior == 20, "loader reads interior hostile cap");
		a_tests.Check(loaded.limits.maxHostilesExterior == 30, "loader reads exterior hostile cap");
		a_tests.CheckNear(loaded.limits.maximumExteriorDistance, 9000.0, 0.0, "loader reads exterior distance");
		a_tests.CheckNear(loaded.limits.placementRadiusMin, 80.0, 0.0, "loader reads minimum placement radius");
		a_tests.CheckNear(loaded.limits.placementRadiusMax, 180.0, 0.0, "loader reads maximum placement radius");
		a_tests.CheckNear(loaded.limits.maximumNavmeshSnapDistance, 220.0, 0.0, "loader reads maximum navmesh snap distance");
		a_tests.Check(loaded.deniedPlugins.size() == 2, "loader reads denied plugin list");
		a_tests.Check(loaded.deniedPlugins[0] == "Example.esp", "denied plugin order is preserved");
		a_tests.Check(loaded.allowedSourcePlugins.size() == 2, "loader reads allowed source plugin list");
		a_tests.Check(loaded.allowedSourcePlugins[1] == "Update.esm", "allowed source plugin order is preserved");

		a_tests.Check(loaded.exclusions.questAliases, "loader reads mandatory exclusions");
	}

	void TestConfigFileFailures(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		TemporaryDirectory temporary;
		a_tests.CheckThrows(
			[&temporary] { (void)LoadConfig(temporary.Path() / "does-not-exist.json"); },
			"missing configuration file is rejected");

		const auto malformedPath = temporary.Path() / "malformed.json";
		WriteTextFile(malformedPath, R"json({ "schemaVersion": 1, "enabled": tru )json");
		a_tests.CheckThrows([&malformedPath] { (void)LoadConfig(malformedPath); }, "malformed JSON is rejected");

		const auto wrongRootPath = temporary.Path() / "wrong-root.json";
		WriteTextFile(wrongRootPath, "[]");
		a_tests.CheckThrows([&wrongRootPath] { (void)LoadConfig(wrongRootPath); }, "non-object JSON root is rejected");

		const auto emptyObjectPath = temporary.Path() / "empty-object.json";
		WriteTextFile(emptyObjectPath, "{}");
		a_tests.CheckThrows([&emptyObjectPath] { (void)LoadConfig(emptyObjectPath); }, "missing required root keys are rejected");

		const auto duplicateRootKeyPath = temporary.Path() / "duplicate-root-key.json";
		WriteTextFile(
			duplicateRootKeyPath,
			ReplaceOnce(CompleteConfigFixture(), R"json("enabled":true)json", R"json("enabled":true,"enabled":false)json"));
		a_tests.CheckThrows(
			[&duplicateRootKeyPath] { (void)LoadConfig(duplicateRootKeyPath); },
			"duplicate root keys are rejected before DOM materialization");

		const auto duplicateNestedKeyPath = temporary.Path() / "duplicate-nested-key.json";
		WriteTextFile(
			duplicateNestedKeyPath,
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("placementRadiusMax":256.0)json",
				R"json("placementRadiusMax":256.0,"placementRadiusMax":128.0)json"));
		a_tests.CheckThrows(
			[&duplicateNestedKeyPath] { (void)LoadConfig(duplicateNestedKeyPath); },
			"duplicate nested keys are rejected before DOM materialization");

		const auto wrongTypePath = temporary.Path() / "wrong-type.json";
		WriteTextFile(
			wrongTypePath,
			ReplaceOnce(CompleteConfigFixture(), R"json("enabled":true)json", R"json("enabled":"yes")json"));
		a_tests.CheckThrows([&wrongTypePath] { (void)LoadConfig(wrongTypePath); }, "wrong scalar types are rejected");

		const auto wrongListPath = temporary.Path() / "wrong-plugin-list.json";
		WriteTextFile(
			wrongListPath,
			ReplaceOnce(CompleteConfigFixture(), R"json("deniedPlugins":[])json", R"json("deniedPlugins":[1,2])json"));
		a_tests.CheckThrows([&wrongListPath] { (void)LoadConfig(wrongListPath); }, "non-string denied plugins are rejected");

		const auto unknownRootKeyPath = temporary.Path() / "unknown-root-key.json";
		WriteTextFile(
			unknownRootKeyPath,
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("deniedPlugins":[])json",
				R"json("deniedPlugins":[],"surprise":true)json"));
		a_tests.CheckThrows([&unknownRootKeyPath] { (void)LoadConfig(unknownRootKeyPath); }, "unknown root keys are rejected");

		const auto oversizedDiagnosticPath = temporary.Path() / "oversized-diagnostic.json";
		const std::string oversizedKey(8U * 1024U * 1024U + 1U, 'x');
		WriteTextFile(
			oversizedDiagnosticPath,
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("deniedPlugins":[])json",
				std::string{ "\"deniedPlugins\":[],\"" } + oversizedKey + "\":true"));
		bool oversizedRejected = false;
		try {
			(void)LoadConfig(oversizedDiagnosticPath);
		} catch (const std::exception& error) {
			oversizedRejected = true;
			const auto diagnostic = MakeBoundedDiagnostic(error.what());
			a_tests.Check(
				diagnostic.View().size() <= MaxDiagnosticBytes,
				">8 MiB malformed-key diagnostic is bounded before reaching a log sink");
			a_tests.Check(
				diagnostic.truncated && diagnostic.View().ends_with(DiagnosticTruncationSuffix),
				">8 MiB malformed-key diagnostic carries an explicit truncation marker");
		}
		a_tests.Check(oversizedRejected, ">8 MiB unknown root key is rejected");

		const auto unknownCategoryPath = temporary.Path() / "unknown-category.json";
		WriteTextFile(
			unknownCategoryPath,
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("giantMammoth":{)json",
				R"json("typo":{},"giantMammoth":{)json"));
		a_tests.CheckThrows([&unknownCategoryPath] { (void)LoadConfig(unknownCategoryPath); }, "unknown curve categories are rejected");

		const auto missingCurveFieldPath = temporary.Path() / "missing-curve-field.json";
		WriteTextFile(
			missingCurveFieldPath,
			ReplaceOnce(CompleteConfigFixture(), R"json(,"maxExtrasPerCell":12)json", ""));
		a_tests.CheckThrows([&missingCurveFieldPath] { (void)LoadConfig(missingCurveFieldPath); }, "missing curve fields are rejected");

		const auto unsafeExclusionPath = temporary.Path() / "unsafe-exclusion.json";
		WriteTextFile(
			unsafeExclusionPath,
			ReplaceOnce(CompleteConfigFixture(), R"json("dragons":true)json", R"json("dragons":false)json"));
		a_tests.CheckThrows([&unsafeExclusionPath] { (void)LoadConfig(unsafeExclusionPath); }, "unsafe exclusion overrides are rejected after parsing");

		std::uint32_t rejectedFixtureIndex = 0;
		const auto ExpectRejected = [&a_tests, &temporary, &rejectedFixtureIndex](
			const std::string& a_contents,
			const std::string_view a_message) {
			const auto path = temporary.Path() / ("numeric-rejection-" + std::to_string(rejectedFixtureIndex++) + ".json");
			WriteTextFile(path, a_contents);
			a_tests.CheckThrows([&path] { (void)LoadConfig(path); }, a_message);
		};

		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("schemaVersion":1)json", R"json("schemaVersion":1.5)json"),
			"fractional schema version is rejected before integer conversion");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("schemaVersion":1)json", R"json("schemaVersion":1.0)json"),
			"floating representation of schema version is not coerced to integer");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("schemaVersion":1)json", R"json("schemaVersion":-1)json"),
			"negative schema version is rejected before unsigned conversion");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("seed":42)json", R"json("seed":42.5)json"),
			"fractional seed is rejected before integer conversion");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("seed":42)json", R"json("seed":42.0)json"),
			"floating representation of seed is not coerced to integer");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("seed":42)json", R"json("seed":-1)json"),
			"negative seed is rejected before unsigned conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("seed":42)json",
				R"json("seed":18446744073709551616)json"),
			"integer above uint64 range is rejected without narrowing");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("seed":42)json", R"json("seed":1e100)json"),
			"floating approximation of an unrepresentable seed is rejected");

		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("baselineLevel":1)json", R"json("baselineLevel":1.5)json"),
			"fractional baseline level is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("baselineLevel":1)json", R"json("baselineLevel":1.0)json"),
			"floating representation of baseline is not coerced to uint32");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("baselineLevel":1)json", R"json("baselineLevel":-1)json"),
			"negative baseline level is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("baselineLevel":1)json",
				R"json("baselineLevel":4294967296)json"),
			"uint32-overflowing baseline level is rejected without narrowing");

		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("maxExtrasPerSource":2)json", R"json("maxExtrasPerSource":2.5)json"),
			"fractional per-source cap is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("maxExtrasPerSource":2)json", R"json("maxExtrasPerSource":2.0)json"),
			"floating representation of per-source cap is not coerced to uint32");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("maxExtrasPerSource":2)json", R"json("maxExtrasPerSource":-1)json"),
			"negative per-source cap is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maxExtrasPerSource":2)json",
				R"json("maxExtrasPerSource":4294967296)json"),
			"uint32-overflowing per-source cap is rejected without narrowing");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("maxExtrasPerCell":12)json", R"json("maxExtrasPerCell":12.5)json"),
			"fractional category cap is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maxAdditionalInterior":12)json",
				R"json("maxAdditionalInterior":12.5)json"),
			"fractional global cap is rejected before uint32 conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maxAdditionalInterior":12)json",
				R"json("maxAdditionalInterior":4294967296)json"),
			"uint32-overflowing global cap is rejected without narrowing");

		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("ratePerLevel":0.05)json", R"json("ratePerLevel":NaN)json"),
			"NaN token is rejected by strict JSON parsing");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("ratePerLevel":0.05)json", R"json("ratePerLevel":Infinity)json"),
			"Infinity token is rejected by strict JSON parsing");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("ratePerLevel":0.05)json", R"json("ratePerLevel":1e400)json"),
			"overflowing floating exponent is rejected");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maximumExteriorDistance":12000.0)json",
				R"json("maximumExteriorDistance":1e39)json"),
			"finite double outside float representation is rejected before narrowing");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maximumExteriorDistance":12000.0)json",
				R"json("maximumExteriorDistance":100000.1)json"),
			"exterior distance above conservative world-unit bound is rejected");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("placementRadiusMax":256.0)json",
				R"json("placementRadiusMax":100000.1)json"),
			"maximum placement radius above conservative world-unit bound is rejected");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("maximumNavmeshSnapDistance":256.0)json",
				R"json("maximumNavmeshSnapDistance":4096.1)json"),
			"navmesh snap distance above its conservative bound is rejected");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("placementRadiusMin":96.0)json",
				R"json("placementRadiusMin":-0.5)json"),
			"negative placement radius is rejected before float conversion");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("placementRadiusMin":96.0)json",
				R"json("placementRadiusMin":300.0)json"),
			"minimum placement radius above maximum placement radius is rejected");

		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("enabled":true)json", R"json("enabled":1)json"),
			"numeric enabled value is not coerced to boolean");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("observeOnly":true)json", R"json("observeOnly":0)json"),
			"numeric observe-only value is not coerced to boolean");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("dragons":true)json", R"json("dragons":"true")json"),
			"string exclusion value is not coerced to boolean");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("deniedPlugins":[])json",
				R"json("deniedPlugins":["Example.esp","example.ESP"])json"),
			"denied plugin names must be unique case-insensitively");
		ExpectRejected(
			ReplaceOnce(CompleteConfigFixture(), R"json("deniedPlugins":[])json", R"json("deniedPlugins":[""])json"),
			"empty denied plugin name is rejected during parsing");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("allowedSourcePlugins":["Skyrim.esm","Update.esm","Dawnguard.esm","HearthFires.esm","Dragonborn.esm"])json",
				R"json("allowedSourcePlugins":[])json"),
			"source plugin allowlist cannot be empty");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("allowedSourcePlugins":["Skyrim.esm","Update.esm","Dawnguard.esm","HearthFires.esm","Dragonborn.esm"])json",
				R"json("allowedSourcePlugins":["Skyrim.esm",""])json"),
			"source plugin allowlist entries cannot be empty");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("allowedSourcePlugins":["Skyrim.esm","Update.esm","Dawnguard.esm","HearthFires.esm","Dragonborn.esm"])json",
				R"json("allowedSourcePlugins":["Skyrim.esm","SKYRIM.ESM"])json"),
			"source plugin allowlist names must be unique case-insensitively");
		ExpectRejected(
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("allowedSourcePlugins":["Skyrim.esm","Update.esm","Dawnguard.esm","HearthFires.esm","Dragonborn.esm"])json",
				R"json("allowedSourcePlugins":["Skyrim.esm",42])json"),
			"source plugin allowlist entries must be strings");

		const auto maximumSeedPath = temporary.Path() / "maximum-seed.json";
		WriteTextFile(
			maximumSeedPath,
			ReplaceOnce(
				CompleteConfigFixture(),
				R"json("seed":42)json",
				R"json("seed":18446744073709551615)json"));
		const auto maximumSeed = LoadConfig(maximumSeedPath);
		a_tests.Check(
			maximumSeed.seed == std::numeric_limits<std::uint64_t>::max(),
			"maximum uint64 seed loads without precision loss");
	}

	void TestInvalidConfigurations(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		auto ExpectInvalid = [&a_tests](const std::function<void(Config&)>& a_mutation, const std::string_view a_message) {
			auto config = DefaultConfig();
			a_mutation(config);
			a_tests.CheckThrows([&config] { ValidateConfig(config); }, a_message);
		};

		ExpectInvalid([](Config& a_config) { a_config.schemaVersion = 2; }, "unsupported schema is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).ratePerLevel = -0.001; },
			"negative rate is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).ratePerLevel = 1.001; },
			"rate above one is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).ratePerLevel = std::numeric_limits<double>::quiet_NaN(); },
			"NaN rate is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).ratePerLevel = std::numeric_limits<double>::infinity(); },
			"infinite rate is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxMultiplier = -0.001; },
			"negative multiplier cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxMultiplier = 0.999; },
			"multiplier cap below one is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxMultiplier = 10.001; },
			"multiplier cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxMultiplier = std::numeric_limits<double>::quiet_NaN(); },
			"NaN multiplier cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxMultiplier = std::numeric_limits<double>::infinity(); },
			"infinite multiplier cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).baselineLevel = 0; },
			"zero baseline level is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).baselineLevel = 1001; },
			"baseline level above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxExtrasPerSource = 0; },
			"zero per-source cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxExtrasPerSource = 33; },
			"per-source cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxExtrasPerCell = 0; },
			"zero category cell cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.at(Category::General).maxExtrasPerCell = 257; },
			"category cell cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.erase(Category::General); },
			"missing general curve is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.erase(Category::AnimalBeast); },
			"missing animal curve is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.curves.erase(Category::GiantMammoth); },
			"missing giant curve is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.placementRadiusMin = -1.0F; },
			"negative minimum placement radius is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.placementRadiusMax = a_config.limits.placementRadiusMin - 1.0F; },
			"reversed placement radius range is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.placementRadiusMin = std::numeric_limits<float>::quiet_NaN(); },
			"NaN minimum placement radius is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.placementRadiusMax = std::numeric_limits<float>::infinity(); },
			"infinite maximum placement radius is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maximumExteriorDistance = -1.0F; },
			"negative exterior distance is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maximumExteriorDistance = std::numeric_limits<float>::quiet_NaN(); },
			"NaN exterior distance is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maximumExteriorDistance = std::numeric_limits<float>::infinity(); },
			"infinite exterior distance is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maximumExteriorDistance = 100000.1F; },
			"exterior distance above conservative world-unit bound is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.placementRadiusMax = 100000.1F; },
			"maximum placement radius above conservative world-unit bound is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maximumNavmeshSnapDistance = 4096.1F; },
			"navmesh snap distance above conservative world-unit bound is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesInterior = a_config.limits.maxAdditionalInterior - 1; },
			"interior hostile cap below additional cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesExterior = a_config.limits.maxAdditionalExterior - 1; },
			"exterior hostile cap below additional cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxAdditionalInterior = 0; },
			"zero interior additional cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxAdditionalExterior = 0; },
			"zero exterior additional cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesInterior = 0; },
			"zero interior hostile cap is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesExterior = 0; },
			"zero exterior hostile cap is rejected");
		ExpectInvalid(
			[](Config& a_config) {
				a_config.limits.maxAdditionalInterior = 257;
				a_config.limits.maxHostilesInterior = 512;
			},
			"interior additional cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) {
				a_config.limits.maxAdditionalExterior = 257;
				a_config.limits.maxHostilesExterior = 512;
			},
			"exterior additional cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesInterior = 513; },
			"interior hostile cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.limits.maxHostilesExterior = 513; },
			"exterior hostile cap above schema safety limit is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.deniedPlugins.emplace_back(); },
			"empty denied plugin entry is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.deniedPlugins = { "Example.esp", "example.ESP" }; },
			"case-insensitive duplicate denied plugin entry is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.allowedSourcePlugins.clear(); },
			"empty source plugin allowlist is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.allowedSourcePlugins = { "" }; },
			"empty source plugin allowlist entry is rejected");
		ExpectInvalid(
			[](Config& a_config) { a_config.allowedSourcePlugins = { "Skyrim.esm", "SKYRIM.ESM" }; },
			"case-insensitive duplicate source allowlist entry is rejected");

		const std::vector<std::pair<std::string_view, std::function<void(Config&)>>> mandatoryExclusions{
			{ "dragons", [](Config& a_config) { a_config.exclusions.dragons = false; } },
			{ "unique", [](Config& a_config) { a_config.exclusions.unique = false; } },
			{ "essential", [](Config& a_config) { a_config.exclusions.essential = false; } },
			{ "protected", [](Config& a_config) { a_config.exclusions.protectedActors = false; } },
			{ "non-respawning", [](Config& a_config) { a_config.exclusions.nonRespawning = false; } },
			{ "persistent reference", [](Config& a_config) { a_config.exclusions.persistentReferences = false; } },
			{ "quest alias", [](Config& a_config) { a_config.exclusions.questAliases = false; } },
			{ "location boss", [](Config& a_config) { a_config.exclusions.locationBosses = false; } },
			{ "summon", [](Config& a_config) { a_config.exclusions.summons = false; } },
			{ "commanded actor", [](Config& a_config) { a_config.exclusions.commandedActors = false; } }
		};
		for (const auto& [name, mutation] : mandatoryExclusions) {
			const std::string message = std::string("mandatory ") + std::string(name) + " exclusion cannot be disabled";
			ExpectInvalid(mutation, message);
		}

		auto validBoundaries = DefaultConfig();
		auto& edgeCurve = validBoundaries.curves.at(Category::General);
		edgeCurve.ratePerLevel = 1.0;
		edgeCurve.baselineLevel = 1000;
		edgeCurve.maxMultiplier = 10.0;
		edgeCurve.maxExtrasPerSource = 32;
		edgeCurve.maxExtrasPerCell = 256;
		validBoundaries.limits.maxAdditionalInterior = 256;
		validBoundaries.limits.maxAdditionalExterior = 256;
		validBoundaries.limits.maxHostilesInterior = 512;
		validBoundaries.limits.maxHostilesExterior = 512;
		validBoundaries.limits.maximumExteriorDistance = 100000.0F;
		validBoundaries.limits.placementRadiusMin = 100000.0F;
		validBoundaries.limits.placementRadiusMax = 100000.0F;
		validBoundaries.limits.maximumNavmeshSnapDistance = 4096.0F;
		a_tests.CheckDoesNotThrow(
			[&validBoundaries] { ValidateConfig(validBoundaries); },
			"inclusive schema safety boundaries validate");
	}

	void TestBoundedDiagnostics(TestSuite& a_tests)
	{
		using namespace BoundedEncounters;

		const auto nullDiagnostic = MakeBoundedDiagnostic(nullptr);
		a_tests.Check(nullDiagnostic.View() == "unknown error", "null diagnostic text has a bounded fallback");
		a_tests.Check(!nullDiagnostic.truncated, "null diagnostic fallback is not marked truncated");

		const std::string exact(MaxDiagnosticBytes, 'a');
		const auto exactDiagnostic = MakeBoundedDiagnostic(exact.c_str());
		a_tests.Check(exactDiagnostic.View().size() == MaxDiagnosticBytes, "exact-limit diagnostic is preserved");
		a_tests.Check(!exactDiagnostic.truncated, "exact-limit diagnostic is not marked truncated");

		const std::string overLimit(MaxDiagnosticBytes + 1U, 'b');
		const auto overLimitDiagnostic = MakeBoundedDiagnostic(overLimit.c_str());
		a_tests.Check(overLimitDiagnostic.View().size() == MaxDiagnosticBytes, "over-limit diagnostic is hard-capped");
		a_tests.Check(
			overLimitDiagnostic.truncated && overLimitDiagnostic.View().ends_with(DiagnosticTruncationSuffix),
			"over-limit diagnostic carries an explicit truncation marker");
	}

	void TestPopulationCapacity(TestSuite& a_tests)
	{
		using BoundedEncounters::ComputePopulationCapacity;
		using BoundedEncounters::MaxSpawnsPerEvaluation;

		const auto ordinary = ComputePopulationCapacity(12, 24, 9, 40, 7);
		a_tests.Check(ordinary.remainingHostileCapacity == 15, "capacity subtracts existing cell hostiles");
		a_tests.Check(ordinary.remainingActiveOwnedCapacity == 33, "capacity subtracts existing active-owned actors");
		a_tests.Check(ordinary.perEvaluationCap == MaxSpawnsPerEvaluation, "capacity exposes the default evaluation cap");
		a_tests.Check(ordinary.effectiveAdditionalCap == MaxSpawnsPerEvaluation, "evaluation cap bounds an ordinary calculation");

		a_tests.Check(
			ComputePopulationCapacity(3, 24, 0, 40, 0).effectiveAdditionalCap == 3,
			"additional-cell cap can be the limiting bound");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 22, 40, 0).effectiveAdditionalCap == 2,
			"remaining hostile capacity can be the limiting bound");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 0, 40, 39).effectiveAdditionalCap == 1,
			"remaining active-owned capacity can be the limiting bound");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 0, 40, 0, 5).effectiveAdditionalCap == 5,
			"custom evaluation cap can be the limiting bound");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 24, 40, 0).effectiveAdditionalCap == 0,
			"hostile capacity saturates at its cap");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 25, 40, 0).effectiveAdditionalCap == 0,
			"hostile capacity saturates above its cap without underflow");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 0, 40, 40).effectiveAdditionalCap == 0,
			"active-owned capacity saturates at its cap");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 0, 40, 41).effectiveAdditionalCap == 0,
			"active-owned capacity saturates above its cap without underflow");
		a_tests.Check(
			ComputePopulationCapacity(12, 24, 0, 40, 0, 0).effectiveAdditionalCap == 0,
			"zero evaluation capacity is a hard zero");
	}
}

int main()
{
	TestSuite tests;
	const auto Run = [&tests](const std::string_view a_name, const auto& a_test) {
		std::cerr << "Running " << a_name << "..." << std::endl;
		a_test(tests);
	};
	Run("configuration loading", TestConfigLoading);
	Run("category conversions", TestCategoryConversions);
	Run("default configuration", TestDefaultConfigurationContract);
	Run("expected-value boundaries", TestExpectedValueBoundaries);
	Run("expected-value monotonicity", TestExpectedValueMonotonicity);
	Run("deterministic plans", TestDeterministicPlans);
	Run("input ordering", TestInputOrdering);
	Run("fractional-capacity admission ordering", TestFractionalCapacityAdmissionOrdering);
	Run("canonical expectation accumulation", TestCanonicalExpectationAccumulation);
	Run("statistical expectations", TestStatisticalExpectations);
	Run("caps and categories", TestCapsAndCategories);
	Run("excluded and ineligible sources", TestExcludedAndIneligibleSources);
	Run("configuration file failures", TestConfigFileFailures);
	Run("invalid configurations", TestInvalidConfigurations);
	Run("bounded diagnostics", TestBoundedDiagnostics);
	Run("population capacity", TestPopulationCapacity);
	return tests.Result();
}
