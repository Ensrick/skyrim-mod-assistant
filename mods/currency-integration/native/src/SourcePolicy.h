#pragma once

namespace Ensrick::Currency
{
	enum class SourceLocationPolicy
	{
		normalizeModern,
		preserveAncient
	};

	[[nodiscard]] constexpr SourceLocationPolicy ClassifySourceLocation(
		const bool a_hasAncientExclusion) noexcept
	{
		return a_hasAncientExclusion ? SourceLocationPolicy::preserveAncient :
			SourceLocationPolicy::normalizeModern;
	}
}
