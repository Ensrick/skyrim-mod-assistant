#pragma once

#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace Ensrick::Currency
{
	struct FormSpec
	{
		std::string plugin;
		std::uint32_t localID{ 0 };

		[[nodiscard]] std::string ToString() const;
		auto operator<=>(const FormSpec&) const = default;
	};

	struct DenominationConfig
	{
		std::string tier;
		std::uint32_t value{ 0 };
		FormSpec form;
	};

	struct InputAliasConfig
	{
		std::string tier;
		FormSpec form;
	};

	struct FamilyConfig
	{
		std::string id;
		std::string displayLabel;
		std::string backendLabel;
		std::uint64_t salt{ 0 };
		bool enabled{ false };
		bool fallback{ false };
		std::optional<FormSpec> perk;
		std::vector<DenominationConfig> denominations;
		std::vector<InputAliasConfig> inputAliases;
	};

	struct RoutingRuleConfig
	{
		std::string id;
		std::vector<FormSpec> anyKeywords;
		std::vector<std::string> familyIDs;
	};

	struct DisabledQuestConfig
	{
		FormSpec quest;
		std::string editorID;
		std::uint32_t aliasID{ 0 };
		std::vector<std::string> removedScripts;
		bool startGameEnabledRemoved{ false };
	};

	struct SourceSafetyConfig
	{
		std::string containerMode;
		std::string actorMode;
		std::string purseMode;
		std::vector<FormSpec> allowedContainerBases;
		std::vector<FormSpec> deniedContainerBases;
		std::vector<FormSpec> deniedContainerReferences;
		std::vector<FormSpec> allowedActorBases;
		std::vector<FormSpec> deniedActorBases;
		std::vector<FormSpec> deniedActorReferences;
		std::vector<FormSpec> purseBaseForms;
		std::vector<FormSpec> purseBudgetLists;
	};

	struct Config
	{
		std::string configID;
		std::string owner;
		FormSpec backendForm;
		std::uint32_t canonicalPercent{ 80 };
		std::uint32_t variantPercent{ 20 };
		std::uint64_t seed{ 0 };
		bool strictSingleOwner{ true };
		bool excludePhysicalFormsFromOrdinaryBarter{ true };
		bool excludePhysicalFormsFromDrop{ false };
		std::vector<std::string> routingPrecedence;
		std::vector<RoutingRuleConfig> routingRules;
		std::vector<DisabledQuestConfig> disabledQuests;
		std::vector<FamilyConfig> families;
		SourceSafetyConfig sources;
	};

	[[nodiscard]] FormSpec ParseFormSpec(std::string_view a_text);
	[[nodiscard]] Config LoadConfig(const std::filesystem::path& a_path);
}
