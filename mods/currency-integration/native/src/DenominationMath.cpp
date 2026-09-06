#include "DenominationMath.h"

#include <limits>

namespace Ensrick::Currency
{
	TierCounts Decompose(const std::uint64_t a_value, const bool a_breakOneLargerCoin) noexcept
	{
		TierCounts result{
			.copper = a_value % 10,
			.silver = (a_value % 100) / 10,
			.gold = a_value / 100,
		};

		if (!a_breakOneLargerCoin) {
			return result;
		}

		if (result.gold > 0) {
			--result.gold;
			result.silver += 10;
		} else if (result.silver > 0) {
			--result.silver;
			result.copper += 10;
		}
		return result;
	}

	std::optional<std::uint64_t> ValueOf(const TierCounts& a_counts) noexcept
	{
		constexpr auto max = std::numeric_limits<std::uint64_t>::max();
		if (a_counts.gold > max / 100 || a_counts.silver > max / 10) {
			return std::nullopt;
		}
		const auto goldValue = a_counts.gold * 100;
		const auto silverValue = a_counts.silver * 10;
		if (goldValue > max - silverValue) {
			return std::nullopt;
		}
		const auto subtotal = goldValue + silverValue;
		if (subtotal > max - a_counts.copper) {
			return std::nullopt;
		}
		return subtotal + a_counts.copper;
	}

	std::uint64_t StableHash(std::uint64_t a_value) noexcept
	{
		// SplitMix64 finalizer. This is deterministic across builds and avoids the
		// implementation-defined output of std::hash.
		a_value += 0x9E3779B97F4A7C15ULL;
		a_value = (a_value ^ (a_value >> 30)) * 0xBF58476D1CE4E5B9ULL;
		a_value = (a_value ^ (a_value >> 27)) * 0x94D049BB133111EBULL;
		return a_value ^ (a_value >> 31);
	}

	bool UseBrokenVariant(
		const std::uint64_t a_sourceIdentity,
		const std::uint64_t a_familySalt,
		const std::uint32_t a_percent) noexcept
	{
		if (a_percent == 0) {
			return false;
		}
		if (a_percent >= 100) {
			return true;
		}
		return StableHash(a_sourceIdentity ^ StableHash(a_familySalt)) % 100 < a_percent;
	}
}
