#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace BoundedEncounters
{
	inline constexpr std::size_t MaxDiagnosticBytes = 4096;
	inline constexpr std::string_view DiagnosticTruncationSuffix = "... [truncated]";

	struct BoundedDiagnostic final
	{
		[[nodiscard]] std::string_view View() const noexcept
		{
			return { bytes.data(), size };
		}

		std::array<char, MaxDiagnosticBytes> bytes{};
		std::size_t size{ 0 };
		bool truncated{ false };
	};

	// Error text can originate in a malformed local configuration. Inspect at
	// most MaxDiagnosticBytes + 1 bytes and copy into fixed storage so a catch
	// path never performs an unbounded strlen or heap allocation before logging.
	[[nodiscard]] inline BoundedDiagnostic MakeBoundedDiagnostic(const char* a_message) noexcept
	{
		static_assert(DiagnosticTruncationSuffix.size() < MaxDiagnosticBytes);
		constexpr std::string_view fallback = "unknown error";
		const char* message = a_message ? a_message : fallback.data();

		std::size_t observed = 0;
		while (observed <= MaxDiagnosticBytes && message[observed] != '\0') {
			++observed;
		}

		BoundedDiagnostic result;
		if (observed <= MaxDiagnosticBytes) {
			for (std::size_t index = 0; index < observed; ++index) {
				result.bytes[index] = message[index];
			}
			result.size = observed;
			return result;
		}

		const auto prefixSize = MaxDiagnosticBytes - DiagnosticTruncationSuffix.size();
		for (std::size_t index = 0; index < prefixSize; ++index) {
			result.bytes[index] = message[index];
		}
		for (std::size_t index = 0; index < DiagnosticTruncationSuffix.size(); ++index) {
			result.bytes[prefixSize + index] = DiagnosticTruncationSuffix[index];
		}
		result.size = MaxDiagnosticBytes;
		result.truncated = true;
		return result;
	}
}
