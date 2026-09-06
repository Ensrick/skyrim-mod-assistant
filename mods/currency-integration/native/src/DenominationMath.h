#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace Ensrick::Currency
{
	struct TierCounts
	{
		std::uint64_t copper{ 0 };
		std::uint64_t silver{ 0 };
		std::uint64_t gold{ 0 };

		auto operator<=>(const TierCounts&) const = default;
	};

	[[nodiscard]] TierCounts Decompose(std::uint64_t a_value, bool a_breakOneLargerCoin) noexcept;
	[[nodiscard]] std::optional<std::uint64_t> ValueOf(const TierCounts& a_counts) noexcept;
	[[nodiscard]] std::optional<std::vector<std::int32_t>> CanonicalCountsWithAliases(
		std::uint64_t a_value, bool a_breakOneLargerCoin, std::size_t a_aliasCount);
	[[nodiscard]] std::uint64_t StableHash(std::uint64_t a_value) noexcept;
	[[nodiscard]] bool UseBrokenVariant(
		std::uint64_t a_sourceIdentity,
		std::uint64_t a_familySalt,
		std::uint32_t a_percent) noexcept;
}
