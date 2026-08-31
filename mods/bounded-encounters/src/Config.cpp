#include "Config.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <type_traits>

#include <nlohmann/json.hpp>

namespace BoundedEncounters
{
	namespace
	{
		[[nodiscard]] std::string FieldLabel(
			const std::string_view a_context,
			const std::string_view a_key)
		{
			return std::string(a_context) + "." + std::string(a_key);
		}

		[[nodiscard]] bool EqualsCaseInsensitive(
			const std::string_view a_left,
			const std::string_view a_right)
		{
			if (a_left.size() != a_right.size()) {
				return false;
			}
			for (std::size_t index = 0; index < a_left.size(); ++index) {
				const auto left = static_cast<unsigned char>(a_left[index]);
				const auto right = static_cast<unsigned char>(a_right[index]);
				if (std::tolower(left) != std::tolower(right)) {
					return false;
				}
			}
			return true;
		}

		void ValidateObjectShape(
			const nlohmann::json& a_json,
			const std::initializer_list<std::string_view> a_required,
			const std::string_view a_context)
		{
			if (!a_json.is_object()) {
				throw std::runtime_error(std::string(a_context) + " must be an object");
			}
			for (const auto key : a_required) {
				if (!a_json.contains(key)) {
					throw std::runtime_error(std::string(a_context) + " is missing required key: " + std::string(key));
				}
			}
			for (const auto& [key, value] : a_json.items()) {
				(void)value;
				if (std::ranges::find(a_required, key) == a_required.end()) {
					throw std::runtime_error(std::string(a_context) + " contains unknown key: " + key);
				}
			}
		}

		[[nodiscard]] bool ReadBoolean(
			const nlohmann::json& a_object,
			const std::string_view a_key,
			const std::string_view a_context)
		{
			const auto& value = a_object.at(a_key);
			if (!value.is_boolean()) {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " must be a boolean");
			}
			return value.get_ref<const nlohmann::json::boolean_t&>();
		}

		template <class T>
		[[nodiscard]] T ReadUnsignedInteger(
			const nlohmann::json& a_object,
			const std::string_view a_key,
			const T a_minimum,
			const T a_maximum,
			const std::string_view a_context)
		{
			static_assert(std::is_unsigned_v<T>);
			const auto& value = a_object.at(a_key);
			if (!value.is_number_unsigned()) {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " must be an unsigned integer");
			}

			const auto raw = value.get_ref<const nlohmann::json::number_unsigned_t&>();
			if (raw < static_cast<nlohmann::json::number_unsigned_t>(a_minimum) ||
				raw > static_cast<nlohmann::json::number_unsigned_t>(a_maximum)) {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " is outside its permitted range");
			}
			return static_cast<T>(raw);
		}

		[[nodiscard]] double ReadFiniteNumber(
			const nlohmann::json& a_object,
			const std::string_view a_key,
			const double a_minimum,
			const double a_maximum,
			const std::string_view a_context)
		{
			const auto& value = a_object.at(a_key);
			double raw = 0.0;
			if (value.is_number_float()) {
				raw = value.get_ref<const nlohmann::json::number_float_t&>();
			} else if (value.is_number_unsigned()) {
				raw = static_cast<double>(value.get_ref<const nlohmann::json::number_unsigned_t&>());
			} else if (value.is_number_integer()) {
				raw = static_cast<double>(value.get_ref<const nlohmann::json::number_integer_t&>());
			} else {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " must be a number");
			}

			if (!std::isfinite(raw) || raw < a_minimum || raw > a_maximum) {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " must be finite and within its permitted range");
			}
			return raw;
		}

		[[nodiscard]] float ReadFiniteFloat(
			const nlohmann::json& a_object,
			const std::string_view a_key,
			const float a_minimum,
			const float a_maximum,
			const std::string_view a_context)
		{
			const auto raw = ReadFiniteNumber(
				a_object,
				a_key,
				static_cast<double>(a_minimum),
				static_cast<double>(a_maximum),
				a_context);
			return static_cast<float>(raw);
		}

		[[nodiscard]] std::vector<std::string> ReadStringArray(
			const nlohmann::json& a_object,
			const std::string_view a_key,
			const std::string_view a_context)
		{
			const auto& value = a_object.at(a_key);
			if (!value.is_array()) {
				throw std::runtime_error(FieldLabel(a_context, a_key) + " must be an array");
			}

			std::vector<std::string> result;
			result.reserve(value.size());
			for (const auto& entry : value) {
				if (!entry.is_string()) {
					throw std::runtime_error(FieldLabel(a_context, a_key) + " entries must be strings");
				}
				const auto& text = entry.get_ref<const nlohmann::json::string_t&>();
				if (text.empty()) {
					throw std::runtime_error(FieldLabel(a_context, a_key) + " entries cannot be empty");
				}
				if (std::ranges::find_if(
						result,
						[&text](const std::string& a_existing) { return EqualsCaseInsensitive(a_existing, text); }) != result.end()) {
					throw std::runtime_error(FieldLabel(a_context, a_key) + " entries must be case-insensitively unique");
				}
				result.push_back(text);
			}
			return result;
		}

		Curve ReadCurve(const nlohmann::json& a_json, const std::string_view a_context)
		{
			ValidateObjectShape(
				a_json,
				{ "enabled", "ratePerLevel", "baselineLevel", "maxMultiplier", "maxExtrasPerSource", "maxExtrasPerCell" },
				a_context);
			Curve result;
			result.enabled = ReadBoolean(a_json, "enabled", a_context);
			result.ratePerLevel = ReadFiniteNumber(a_json, "ratePerLevel", 0.0, 1.0, a_context);
			result.baselineLevel = ReadUnsignedInteger<std::uint32_t>(a_json, "baselineLevel", 1, 1000, a_context);
			result.maxMultiplier = ReadFiniteNumber(a_json, "maxMultiplier", 1.0, 10.0, a_context);
			result.maxExtrasPerSource = ReadUnsignedInteger<std::uint32_t>(a_json, "maxExtrasPerSource", 1, 32, a_context);
			result.maxExtrasPerCell = ReadUnsignedInteger<std::uint32_t>(a_json, "maxExtrasPerCell", 1, 256, a_context);
			return result;
		}
	}

	Config DefaultConfig()
	{
		Config config;
		config.curves.emplace(Category::General, Curve{ true, 0.05, 1, 3.0, 2, 12 });
		config.curves.emplace(Category::AnimalBeast, Curve{ true, 0.025, 1, 2.0, 1, 6 });
		config.curves.emplace(Category::GiantMammoth, Curve{ true, 0.01, 1, 1.5, 1, 2 });
		config.allowedSourcePlugins = {
			"Skyrim.esm",
			"Update.esm",
			"Dawnguard.esm",
			"HearthFires.esm",
			"Dragonborn.esm"
		};
		return config;
	}

	Config LoadConfig(const std::filesystem::path& a_path)
	{
		std::ifstream stream(a_path);
		if (!stream) {
			throw std::runtime_error("configuration file is missing: " + a_path.string());
		}

		nlohmann::json root;
		root = nlohmann::json::parse(stream, nullptr, true, true);
		ValidateObjectShape(
			root,
			{ "schemaVersion", "enabled", "observeOnly", "debugLogging", "seed", "curves", "limits", "exclusions", "allowedSourcePlugins", "deniedPlugins" },
			"configuration");
		Config config = DefaultConfig();
		config.schemaVersion = ReadUnsignedInteger<std::uint32_t>(root, "schemaVersion", 1, 1, "configuration");
		config.enabled = ReadBoolean(root, "enabled", "configuration");
		config.observeOnly = ReadBoolean(root, "observeOnly", "configuration");
		config.debugLogging = ReadBoolean(root, "debugLogging", "configuration");
		config.seed = ReadUnsignedInteger<std::uint64_t>(
			root,
			"seed",
			0,
			std::numeric_limits<std::uint64_t>::max(),
			"configuration");

		const auto& curves = root.at("curves");
		ValidateObjectShape(curves, { "general", "animalBeast", "giantMammoth" }, "curves");
		for (const auto category : { Category::General, Category::AnimalBeast, Category::GiantMammoth }) {
			const auto name = ToString(category);
			config.curves[category] = ReadCurve(curves.at(name), "curves." + name);
		}

		const auto& limits = root.at("limits");
		ValidateObjectShape(
			limits,
			{ "maxAdditionalInterior", "maxAdditionalExterior", "maxHostilesInterior", "maxHostilesExterior", "maximumExteriorDistance", "placementRadiusMin", "placementRadiusMax" },
			"limits");
		config.limits.maxAdditionalInterior = ReadUnsignedInteger<std::uint32_t>(limits, "maxAdditionalInterior", 1, 256, "limits");
		config.limits.maxAdditionalExterior = ReadUnsignedInteger<std::uint32_t>(limits, "maxAdditionalExterior", 1, 256, "limits");
		config.limits.maxHostilesInterior = ReadUnsignedInteger<std::uint32_t>(limits, "maxHostilesInterior", 1, 512, "limits");
		config.limits.maxHostilesExterior = ReadUnsignedInteger<std::uint32_t>(limits, "maxHostilesExterior", 1, 512, "limits");
		config.limits.maximumExteriorDistance = ReadFiniteFloat(limits, "maximumExteriorDistance", 0.0F, 100000.0F, "limits");
		config.limits.placementRadiusMin = ReadFiniteFloat(limits, "placementRadiusMin", 0.0F, 100000.0F, "limits");
		config.limits.placementRadiusMax = ReadFiniteFloat(limits, "placementRadiusMax", 0.0F, 100000.0F, "limits");

		const auto& exclusions = root.at("exclusions");
		ValidateObjectShape(
			exclusions,
			{ "dragons", "unique", "essential", "protected", "nonRespawning", "persistentReferences", "questAliases", "locationBosses", "summons", "commandedActors" },
			"exclusions");
		config.exclusions.dragons = ReadBoolean(exclusions, "dragons", "exclusions");
		config.exclusions.unique = ReadBoolean(exclusions, "unique", "exclusions");
		config.exclusions.essential = ReadBoolean(exclusions, "essential", "exclusions");
		config.exclusions.protectedActors = ReadBoolean(exclusions, "protected", "exclusions");
		config.exclusions.nonRespawning = ReadBoolean(exclusions, "nonRespawning", "exclusions");
		config.exclusions.persistentReferences = ReadBoolean(exclusions, "persistentReferences", "exclusions");
		config.exclusions.questAliases = ReadBoolean(exclusions, "questAliases", "exclusions");
		config.exclusions.locationBosses = ReadBoolean(exclusions, "locationBosses", "exclusions");
		config.exclusions.summons = ReadBoolean(exclusions, "summons", "exclusions");
		config.exclusions.commandedActors = ReadBoolean(exclusions, "commandedActors", "exclusions");

		config.allowedSourcePlugins = ReadStringArray(root, "allowedSourcePlugins", "configuration");
		config.deniedPlugins = ReadStringArray(root, "deniedPlugins", "configuration");
		ValidateConfig(config);
		return config;
	}

	void ValidateConfig(const Config& a_config)
	{
		if (a_config.schemaVersion != 1) {
			throw std::runtime_error("unsupported schemaVersion");
		}
		for (const auto& [category, curve] : a_config.curves) {
			(void)category;
			if (!std::isfinite(curve.ratePerLevel) || curve.ratePerLevel < 0.0 || curve.ratePerLevel > 1.0) {
				throw std::runtime_error("ratePerLevel must be finite and between 0 and 1");
			}
			if (!std::isfinite(curve.maxMultiplier) || curve.maxMultiplier < 1.0 || curve.maxMultiplier > 10.0) {
				throw std::runtime_error("maxMultiplier must be finite and between 1 and 10");
			}
			if (curve.baselineLevel == 0 || curve.baselineLevel > 1000) {
				throw std::runtime_error("baselineLevel must be between 1 and 1000");
			}
			if (curve.maxExtrasPerSource == 0 || curve.maxExtrasPerSource > 32 ||
				curve.maxExtrasPerCell == 0 || curve.maxExtrasPerCell > 256) {
				throw std::runtime_error("curve safety caps must be non-zero and within schema 1 limits");
			}
		}
		for (const auto required : { Category::General, Category::AnimalBeast, Category::GiantMammoth }) {
			if (!a_config.curves.contains(required)) {
				throw std::runtime_error("all schema 1 categories require an explicit or default curve");
			}
		}
		if (a_config.limits.placementRadiusMin < 0.0F ||
			a_config.limits.placementRadiusMax < a_config.limits.placementRadiusMin) {
			throw std::runtime_error("placement radius range is invalid");
		}
		if (a_config.limits.maxHostilesInterior < a_config.limits.maxAdditionalInterior ||
			a_config.limits.maxHostilesExterior < a_config.limits.maxAdditionalExterior) {
			throw std::runtime_error("hostile caps must be at least as large as additional-actor caps");
		}
		if (a_config.limits.maxAdditionalInterior == 0 || a_config.limits.maxAdditionalExterior == 0 ||
			a_config.limits.maxHostilesInterior == 0 || a_config.limits.maxHostilesExterior == 0 ||
			a_config.limits.maxAdditionalInterior > 256 || a_config.limits.maxAdditionalExterior > 256 ||
			a_config.limits.maxHostilesInterior > 512 || a_config.limits.maxHostilesExterior > 512) {
			throw std::runtime_error("global actor caps must be non-zero and within schema 1 limits");
		}
		if (a_config.limits.maximumExteriorDistance < 0.0F ||
			a_config.limits.maximumExteriorDistance > 100000.0F ||
			a_config.limits.placementRadiusMax > 100000.0F ||
			!std::isfinite(a_config.limits.maximumExteriorDistance) ||
			!std::isfinite(a_config.limits.placementRadiusMin) ||
			!std::isfinite(a_config.limits.placementRadiusMax)) {
			throw std::runtime_error("distance and placement limits must be finite and non-negative");
		}

		const auto& exclusions = a_config.exclusions;
		if (!exclusions.dragons || !exclusions.unique || !exclusions.essential ||
			!exclusions.protectedActors || !exclusions.nonRespawning ||
			!exclusions.persistentReferences || !exclusions.questAliases ||
			!exclusions.locationBosses || !exclusions.summons ||
			!exclusions.commandedActors) {
			throw std::runtime_error("schema 1 safety exclusions are mandatory and cannot be disabled");
		}
		const auto ValidatePluginNames = [](const std::vector<std::string>& a_plugins, const std::string_view a_name) {
			for (std::size_t index = 0; index < a_plugins.size(); ++index) {
				if (a_plugins[index].empty()) {
					throw std::runtime_error(std::string(a_name) + " entries cannot be empty");
				}
				for (std::size_t prior = 0; prior < index; ++prior) {
					if (EqualsCaseInsensitive(a_plugins[prior], a_plugins[index])) {
						throw std::runtime_error(std::string(a_name) + " entries must be case-insensitively unique");
					}
				}
			}
		};
		if (a_config.allowedSourcePlugins.empty()) {
			throw std::runtime_error("allowedSourcePlugins must contain at least one plugin filename");
		}
		ValidatePluginNames(a_config.allowedSourcePlugins, "allowedSourcePlugins");
		ValidatePluginNames(a_config.deniedPlugins, "deniedPlugins");
	}
}
