#pragma once

#include <array>
#include <cstdint>
#include <string_view>

namespace BoundedEncounters::Version
{
	inline constexpr std::string_view Name = "Bounded Encounters";
	inline constexpr std::string_view ShortName = "BoundedEncounters";
	inline constexpr std::string_view Semantic = "0.1.0-alpha.1";
	inline constexpr std::array<std::uint16_t, 4> SupportedRuntime{ 1, 7, 104, 0 };
}
