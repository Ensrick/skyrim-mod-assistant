#include "LedgerFingerprint.h"

#include <cctype>
#include <string_view>

namespace Ensrick::Currency
{
	std::uint64_t ComputeLedgerFingerprint(const Config& a_config)
	{
		constexpr std::uint64_t offset = 14695981039346656037ULL;
		constexpr std::uint64_t prime = 1099511628211ULL;
		std::uint64_t hash = offset;
		auto appendByte = [&](const std::uint8_t value) {
			hash ^= value;
			hash *= prime;
		};
		auto appendInteger = [&](const std::uint64_t value) {
			for (std::uint32_t shift = 0; shift < 64; shift += 8) {
				appendByte(static_cast<std::uint8_t>((value >> shift) & 0xFF));
			}
		};
		auto appendString = [&](const std::string_view value, const bool foldCase) {
			appendInteger(value.size());
			for (const auto character : value) {
				const auto byte = static_cast<unsigned char>(character);
				appendByte(static_cast<std::uint8_t>(foldCase ? std::tolower(byte) : byte));
			}
		};
		auto appendForm = [&](const FormSpec& form) {
			appendString(form.plugin, true);
			appendInteger(form.localID);
		};

		appendString("EnsrickCurrencyLedgerV1", false);
		appendForm(a_config.backendForm);
		appendInteger(a_config.families.size());
		for (const auto& family : a_config.families) {
			appendString(family.id, false);
			appendInteger(family.enabled ? 1 : 0);
			appendInteger(family.fallback ? 1 : 0);
			appendInteger(family.denominations.size());
			for (const auto& denomination : family.denominations) {
				appendInteger(denomination.value);
				appendForm(denomination.form);
			}
		}
		return hash;
	}
}
