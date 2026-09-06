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

		appendString("EnsrickCurrencyLedgerV2", false);
		appendString(a_config.owner, false);
		appendInteger(a_config.strictSingleOwner ? 1 : 0);
		appendForm(a_config.backendForm);
		appendInteger(a_config.excludePhysicalFormsFromOrdinaryBarter ? 1 : 0);
		appendInteger(a_config.excludePhysicalFormsFromDrop ? 1 : 0);
		appendInteger(a_config.canonicalPercent);
		appendInteger(a_config.variantPercent);
		appendInteger(a_config.seed);
		appendInteger(a_config.routingPrecedence.size());
		for (const auto& phase : a_config.routingPrecedence) {
			appendString(phase, false);
		}
		appendInteger(a_config.families.size());
		for (const auto& family : a_config.families) {
			appendString(family.id, false);
			appendString(family.displayLabel, false);
			appendString(family.backendLabel, false);
			appendInteger(family.salt);
			appendInteger(family.enabled ? 1 : 0);
			appendInteger(family.fallback ? 1 : 0);
			appendInteger(family.perk ? 1 : 0);
			if (family.perk) {
				appendForm(*family.perk);
			}
			appendInteger(family.denominations.size());
			for (const auto& denomination : family.denominations) {
				appendString(denomination.tier, false);
				appendInteger(denomination.value);
				appendForm(denomination.form);
			}
			appendInteger(family.inputAliases.size());
			for (const auto& alias : family.inputAliases) {
				appendString(alias.tier, false);
				appendForm(alias.form);
			}
		}
		appendInteger(a_config.routingRules.size());
		for (const auto& rule : a_config.routingRules) {
			appendString(rule.id, false);
			appendInteger(rule.anyKeywords.size());
			for (const auto& keyword : rule.anyKeywords) {
				appendForm(keyword);
			}
			appendInteger(rule.familyIDs.size());
			for (const auto& familyID : rule.familyIDs) {
				appendString(familyID, false);
			}
		}
		return hash;
	}
}
