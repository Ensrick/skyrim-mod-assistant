#pragma once

#include "DenominationMath.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace Ensrick::Currency
{
	struct RouteDesignCandidate
	{
		std::size_t familyIndex{ 0 };
		std::uint64_t familySalt{ 0 };
	};

	// Rendezvous selection gives each explicitly listed face design an equal
	// deterministic opportunity without depending on candidate array order.
	// It selects one family for the entire existing budget; it never copies the
	// budget per candidate or changes its purchasing power. Config validation
	// requires unique family salts, so identical candidate scores cannot occur.
	[[nodiscard]] inline std::optional<std::size_t> SelectRouteDesign(
		const std::span<const RouteDesignCandidate> a_candidates,
		const std::uint64_t a_sourceIdentity) noexcept
	{
		std::optional<std::size_t> selected;
		std::uint64_t highestScore = 0;
		for (const auto& candidate : a_candidates) {
			const auto score = StableHash(a_sourceIdentity ^ StableHash(candidate.familySalt));
			if (!selected || score > highestScore) {
				selected = candidate.familyIndex;
				highestScore = score;
			}
		}
		return selected;
	}
}
