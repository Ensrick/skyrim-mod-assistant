#include "Config.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <charconv>
#include <cctype>
#include <format>
#include <fstream>
#include <limits>
#include <ranges>
#include <set>
#include <stdexcept>
#include <string_view>

namespace Ensrick::Currency
{
	namespace
	{
		using json = nlohmann::json;

		[[noreturn]] void Fail(const std::string& a_message)
		{
			throw std::runtime_error("currency configuration: " + a_message);
		}

		void ExactKeys(
			const json& a_node,
			const std::initializer_list<std::string_view> a_required,
			const std::initializer_list<std::string_view> a_optional,
			const std::string_view a_context)
		{
			if (!a_node.is_object()) {
				Fail(std::string(a_context) + " must be an object");
			}
			std::set<std::string, std::less<>> allowed;
			for (const auto key : a_required) {
				allowed.emplace(key);
				if (!a_node.contains(key)) {
					Fail(std::string(a_context) + " is missing required key '" + std::string(key) + "'");
				}
			}
			for (const auto key : a_optional) {
				allowed.emplace(key);
			}
			for (const auto& [key, value] : a_node.items()) {
				(void)value;
				if (!allowed.contains(key)) {
					Fail(std::string(a_context) + " has unknown key '" + key + "'");
				}
			}
		}

		std::string String(const json& a_node, const std::string_view a_context)
		{
			if (!a_node.is_string()) {
				Fail(std::string(a_context) + " must be a string");
			}
			const auto result = a_node.get<std::string>();
			if (result.empty()) {
				Fail(std::string(a_context) + " must not be empty");
			}
			return result;
		}

		bool Bool(const json& a_node, const std::string_view a_context)
		{
			if (!a_node.is_boolean()) {
				Fail(std::string(a_context) + " must be a boolean");
			}
			return a_node.get<bool>();
		}

		std::uint32_t UInt32(const json& a_node, const std::string_view a_context)
		{
			if (!a_node.is_number_unsigned()) {
				Fail(std::string(a_context) + " must be an unsigned integer");
			}
			const auto value = a_node.get<std::uint64_t>();
			if (value > std::numeric_limits<std::uint32_t>::max()) {
				Fail(std::string(a_context) + " is outside uint32 range");
			}
			return static_cast<std::uint32_t>(value);
		}

		std::uint64_t Hex64(const json& a_node, const std::string_view a_context)
		{
			const auto text = String(a_node, a_context);
			if (!text.starts_with("0x") || text.size() <= 2) {
				Fail(std::string(a_context) + " must be a 0x-prefixed hexadecimal string");
			}
			std::uint64_t value = 0;
			const auto* begin = text.data() + 2;
			const auto* end = text.data() + text.size();
			const auto parsed = std::from_chars(begin, end, value, 16);
			if (parsed.ec != std::errc{} || parsed.ptr != end) {
				Fail(std::string(a_context) + " contains invalid hexadecimal data");
			}
			return value;
		}

		std::vector<FormSpec> FormArray(const json& a_node, const std::string_view a_context)
		{
			if (!a_node.is_array()) {
				Fail(std::string(a_context) + " must be an array");
			}
			std::vector<FormSpec> result;
			for (std::size_t index = 0; index < a_node.size(); ++index) {
				result.push_back(ParseFormSpec(String(a_node[index],
					std::format("{}[{}]", a_context, index))));
			}
			return result;
		}

		std::vector<std::string> StringArray(const json& a_node, const std::string_view a_context)
		{
			if (!a_node.is_array()) {
				Fail(std::string(a_context) + " must be an array");
			}
			std::vector<std::string> result;
			for (std::size_t index = 0; index < a_node.size(); ++index) {
				result.push_back(String(a_node[index], std::format("{}[{}]", a_context, index)));
			}
			return result;
		}

		template <class T, class Projection>
		void RequireUnique(const std::vector<T>& a_values, Projection a_projection, const std::string_view a_context)
		{
			std::set<std::string, std::less<>> seen;
			for (const auto& value : a_values) {
				const auto key = a_projection(value);
				if (!seen.emplace(key).second) {
					Fail(std::string(a_context) + " contains duplicate '" + key + "'");
				}
			}
		}

		std::vector<FormSpec> OptionalForms(
			const json& a_node,
			const std::string_view a_key,
			const std::string_view a_context)
		{
			return a_node.contains(a_key) ? FormArray(a_node.at(a_key),
				std::format("{}.{}", a_context, a_key)) : std::vector<FormSpec>{};
		}

		std::string FormIdentity(const FormSpec& a_form)
		{
			auto plugin = a_form.plugin;
			std::ranges::transform(plugin, plugin.begin(), [](const unsigned char a_character) {
				return static_cast<char>(std::tolower(a_character));
			});
			return std::format("{:06X}:{}", a_form.localID, plugin);
		}
	}

	std::string FormSpec::ToString() const
	{
		return std::format("{:06X}:{}", localID, plugin);
	}

	FormSpec ParseFormSpec(const std::string_view a_text)
	{
		const auto colon = a_text.find(':');
		if (colon == std::string_view::npos || colon == 0 || colon + 1 >= a_text.size() ||
			a_text.find(':', colon + 1) != std::string_view::npos) {
			Fail("invalid FormKey '" + std::string(a_text) + "'");
		}
		const auto idText = a_text.substr(0, colon);
		if (idText.size() > 6) {
			Fail("FormKey local ID is wider than 6 hex digits: '" + std::string(a_text) + "'");
		}
		std::uint32_t id = 0;
		const auto parsed = std::from_chars(idText.data(), idText.data() + idText.size(), id, 16);
		if (parsed.ec != std::errc{} || parsed.ptr != idText.data() + idText.size()) {
			Fail("invalid FormKey ID: '" + std::string(a_text) + "'");
		}
		return FormSpec{ .plugin = std::string(a_text.substr(colon + 1)), .localID = id };
	}

	Config LoadConfig(const std::filesystem::path& a_path)
	{
		std::ifstream stream(a_path, std::ios::binary);
		if (!stream) {
			Fail("cannot open " + a_path.string());
		}
		json root;
		try {
			root = json::parse(stream, nullptr, true, true);
		} catch (const std::exception& error) {
			Fail("cannot parse " + a_path.string() + ": " + error.what());
		}

		ExactKeys(root,
			{ "schemaVersion", "configId", "accounting", "distribution", "routing", "sourceSafety",
				"sources", "telemetry", "disabledEcePlayerAliasQuests", "families",
				"excludePhysicalFormsFromOrdinaryBarter", "excludePhysicalFormsFromDrop" },
			{ "ancientExclusions" }, "root");
		if (UInt32(root.at("schemaVersion"), "schemaVersion") != 1) {
			Fail("schemaVersion must be exactly 1");
		}

		Config result;
		result.configID = String(root.at("configId"), "configId");
		result.excludePhysicalFormsFromOrdinaryBarter = Bool(
			root.at("excludePhysicalFormsFromOrdinaryBarter"), "excludePhysicalFormsFromOrdinaryBarter");
		result.excludePhysicalFormsFromDrop = Bool(
			root.at("excludePhysicalFormsFromDrop"), "excludePhysicalFormsFromDrop");

		const auto& accounting = root.at("accounting");
		ExactKeys(accounting, { "backendForm", "owner", "strictSingleOwner" }, {}, "accounting");
		result.backendForm = ParseFormSpec(String(accounting.at("backendForm"), "accounting.backendForm"));
		result.owner = String(accounting.at("owner"), "accounting.owner");
		result.strictSingleOwner = Bool(accounting.at("strictSingleOwner"), "accounting.strictSingleOwner");
		if (!result.strictSingleOwner || result.owner != "EnsrickCurrencyDenominations") {
			Fail("accounting must name EnsrickCurrencyDenominations as the strict single owner");
		}

		const auto& distribution = root.at("distribution");
		ExactKeys(distribution,
			{ "canonicalPercent", "variantPercent", "breakAtMostOne", "breakOrder", "seed", "stableIdentity" },
			{}, "distribution");
		result.canonicalPercent = UInt32(distribution.at("canonicalPercent"), "distribution.canonicalPercent");
		result.variantPercent = UInt32(distribution.at("variantPercent"), "distribution.variantPercent");
		if (result.canonicalPercent + result.variantPercent != 100 || result.canonicalPercent != 80 ||
			result.variantPercent != 20) {
			Fail("distribution must be the reviewed 80/20 policy");
		}
		if (!Bool(distribution.at("breakAtMostOne"), "distribution.breakAtMostOne")) {
			Fail("distribution.breakAtMostOne must be true");
		}
		if (distribution.at("breakOrder") != json::array({ 100, 10 })) {
			Fail("distribution.breakOrder must be exactly [100,10]");
		}
		if (distribution.at("stableIdentity") !=
			json::array({ "sourceFormKey", "sourceReferenceFormId", "familyId" })) {
			Fail("distribution.stableIdentity has drifted");
		}
		result.seed = Hex64(distribution.at("seed"), "distribution.seed");

		const auto& routing = root.at("routing");
		ExactKeys(routing, { "precedence" }, { "ancientExclusionKeywords" }, "routing");
		result.routingPrecedence = StringArray(routing.at("precedence"), "routing.precedence");
		const std::vector<std::string> requiredPrecedence{
			"questExceptions", "ancientExclusions", "modernFamilies", "septimFallback"
		};
		if (result.routingPrecedence != requiredPrecedence) {
			Fail("routing.precedence does not match the reviewed order");
		}
		result.ancientExclusionKeywords = OptionalForms(routing, "ancientExclusionKeywords", "routing");

		const auto& sourceSafety = root.at("sourceSafety");
		ExactKeys(sourceSafety, { "containers", "actors", "purses" }, {}, "sourceSafety");
		const auto& containers = sourceSafety.at("containers");
		ExactKeys(containers,
			{ "mode", "requireAllowlistedSource", "denyVendors", "denyPlayerStorage", "denyQuestStorage" },
			{}, "sourceSafety.containers");
		result.sources.containerMode = String(containers.at("mode"), "sourceSafety.containers.mode");
		if (result.sources.containerMode != "respawningSafeOnly" ||
			Bool(containers.at("requireAllowlistedSource"), "sourceSafety.containers.requireAllowlistedSource") ||
			!Bool(containers.at("denyVendors"), "sourceSafety.containers.denyVendors") ||
			!Bool(containers.at("denyPlayerStorage"), "sourceSafety.containers.denyPlayerStorage") ||
			!Bool(containers.at("denyQuestStorage"), "sourceSafety.containers.denyQuestStorage")) {
			Fail("container safety contract has drifted");
		}
		const auto& actors = sourceSafety.at("actors");
		ExactKeys(actors,
			{ "mode", "requireAllowlistedSource", "denyPlayer", "denyFollowers", "denyVendors",
				"denyUniquePersistentEssentialProtected" }, {}, "sourceSafety.actors");
		result.sources.actorMode = String(actors.at("mode"), "sourceSafety.actors.mode");
		if (result.sources.actorMode != "deadGenericOnly" ||
			Bool(actors.at("requireAllowlistedSource"), "sourceSafety.actors.requireAllowlistedSource") ||
			!Bool(actors.at("denyPlayer"), "sourceSafety.actors.denyPlayer") ||
			!Bool(actors.at("denyFollowers"), "sourceSafety.actors.denyFollowers") ||
			!Bool(actors.at("denyVendors"), "sourceSafety.actors.denyVendors") ||
			!Bool(actors.at("denyUniquePersistentEssentialProtected"),
				"sourceSafety.actors.denyUniquePersistentEssentialProtected")) {
			Fail("actor safety contract has drifted");
		}
		const auto& purses = sourceSafety.at("purses");
		ExactKeys(purses, { "mode", "requireAllowlistedBase" }, {}, "sourceSafety.purses");
		result.sources.purseMode = String(purses.at("mode"), "sourceSafety.purses.mode");
		if (result.sources.purseMode != "allowlistedOnly" ||
			!Bool(purses.at("requireAllowlistedBase"), "sourceSafety.purses.requireAllowlistedBase")) {
			Fail("purse safety contract has drifted");
		}

		const auto& sources = root.at("sources");
		ExactKeys(sources, { "containers", "actors", "purses" }, {}, "sources");
		const auto& sourceContainers = sources.at("containers");
		ExactKeys(sourceContainers, { "allowBaseForms", "denyBaseForms", "denyReferences" }, {}, "sources.containers");
		result.sources.allowedContainerBases = FormArray(sourceContainers.at("allowBaseForms"), "sources.containers.allowBaseForms");
		result.sources.deniedContainerBases = FormArray(sourceContainers.at("denyBaseForms"), "sources.containers.denyBaseForms");
		result.sources.deniedContainerReferences = FormArray(sourceContainers.at("denyReferences"), "sources.containers.denyReferences");
		const auto& sourceActors = sources.at("actors");
		ExactKeys(sourceActors, { "allowBaseForms", "denyBaseForms", "denyReferences" }, {}, "sources.actors");
		result.sources.allowedActorBases = FormArray(sourceActors.at("allowBaseForms"), "sources.actors.allowBaseForms");
		result.sources.deniedActorBases = FormArray(sourceActors.at("denyBaseForms"), "sources.actors.denyBaseForms");
		result.sources.deniedActorReferences = FormArray(sourceActors.at("denyReferences"), "sources.actors.denyReferences");
		const auto& sourcePurses = sources.at("purses");
		ExactKeys(sourcePurses, { "baseForms", "budgetLists" }, {}, "sources.purses");
		result.sources.purseBaseForms = FormArray(sourcePurses.at("baseForms"), "sources.purses.baseForms");
		result.sources.purseBudgetLists = FormArray(sourcePurses.at("budgetLists"), "sources.purses.budgetLists");

		const auto& telemetry = root.at("telemetry");
		ExactKeys(telemetry, { "requiredReasonCounters", "reasonCounters" }, {}, "telemetry");
		if (!Bool(telemetry.at("requiredReasonCounters"), "telemetry.requiredReasonCounters")) {
			Fail("telemetry.requiredReasonCounters must be true");
		}
		(void)StringArray(telemetry.at("reasonCounters"), "telemetry.reasonCounters");

		const auto& disabled = root.at("disabledEcePlayerAliasQuests");
		if (!disabled.is_array() || disabled.empty()) {
			Fail("disabledEcePlayerAliasQuests must be a non-empty array");
		}
		for (std::size_t index = 0; index < disabled.size(); ++index) {
			const auto& node = disabled[index];
			const auto context = std::format("disabledEcePlayerAliasQuests[{}]", index);
			ExactKeys(node, { "quest", "editorId", "aliasId", "removedScripts", "startGameEnabledRemoved" }, {}, context);
			result.disabledQuests.push_back(DisabledQuestConfig{
				.quest = ParseFormSpec(String(node.at("quest"), context + ".quest")),
				.editorID = String(node.at("editorId"), context + ".editorId"),
				.aliasID = UInt32(node.at("aliasId"), context + ".aliasId"),
				.removedScripts = StringArray(node.at("removedScripts"), context + ".removedScripts"),
				.startGameEnabledRemoved = Bool(node.at("startGameEnabledRemoved"), context + ".startGameEnabledRemoved"),
			});
		}

		const auto& families = root.at("families");
		if (!families.is_array() || families.empty()) {
			Fail("families must be a non-empty array");
		}
		std::set<std::string, std::less<>> allForms;
		for (std::size_t index = 0; index < families.size(); ++index) {
			const auto& node = families[index];
			const auto context = std::format("families[{}]", index);
			ExactKeys(node,
				{ "id", "enabled", "fallback", "displayLabel", "backendLabel", "salt",
					"routeKeywords", "perk", "denominations" },
				{ "legacySingleton" }, context);
			FamilyConfig family{
				.id = String(node.at("id"), context + ".id"),
				.displayLabel = String(node.at("displayLabel"), context + ".displayLabel"),
				.backendLabel = String(node.at("backendLabel"), context + ".backendLabel"),
				.salt = Hex64(node.at("salt"), context + ".salt"),
				.enabled = Bool(node.at("enabled"), context + ".enabled"),
				.fallback = Bool(node.at("fallback"), context + ".fallback"),
				.routeKeywords = FormArray(node.at("routeKeywords"), context + ".routeKeywords"),
			};
			if (!node.at("perk").is_null()) {
				family.perk = ParseFormSpec(String(node.at("perk"), context + ".perk"));
			}
			const auto& denominations = node.at("denominations");
			if (!denominations.is_array() || denominations.empty()) {
				Fail(context + ".denominations must be a non-empty array");
			}
			for (std::size_t denominationIndex = 0; denominationIndex < denominations.size(); ++denominationIndex) {
				const auto& denomination = denominations[denominationIndex];
				const auto denominationContext = std::format("{}.denominations[{}]", context, denominationIndex);
				ExactKeys(denomination, { "tier", "value", "form" }, {}, denominationContext);
				DenominationConfig parsedDenomination{
					.tier = String(denomination.at("tier"), denominationContext + ".tier"),
					.value = UInt32(denomination.at("value"), denominationContext + ".value"),
					.form = ParseFormSpec(String(denomination.at("form"), denominationContext + ".form")),
				};
				if (!allForms.emplace(FormIdentity(parsedDenomination.form)).second) {
					Fail("physical denomination form appears in more than one family: " + parsedDenomination.form.ToString());
				}
				family.denominations.push_back(std::move(parsedDenomination));
			}
			std::vector<std::uint32_t> values;
			for (const auto& denomination : family.denominations) {
				values.push_back(denomination.value);
			}
			std::ranges::sort(values);
			if (values != std::vector<std::uint32_t>{ 1 } &&
				values != std::vector<std::uint32_t>{ 1, 10, 100 }) {
				Fail(context + " must provide either singleton value 1 or exact values 1/10/100");
			}
			result.families.push_back(std::move(family));
		}

		RequireUnique(result.families, [](const FamilyConfig& family) { return family.id; }, "families");
		if (allForms.contains(FormIdentity(result.backendForm))) {
			Fail("accounting backend must not also be a physical denomination form");
		}
		if (std::ranges::count_if(result.families, [](const FamilyConfig& family) {
				return family.enabled && family.fallback;
			}) != 1) {
			Fail("exactly one enabled family must be the fallback");
		}
		return result;
	}
}
