#include "Config.h"
#include "LedgerFingerprint.h"

#include <nlohmann/json.hpp>

#include <chrono>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace
{
	using json = nlohmann::json;

	class MutationFile
	{
	public:
		MutationFile() : path(std::filesystem::temp_directory_path() /
			("ensrick-currency-config-tests-" + std::to_string(
				std::chrono::steady_clock::now().time_since_epoch().count()) + ".json"))
		{}
		~MutationFile()
		{
			std::error_code ignored;
			std::filesystem::remove(path, ignored);
		}
		std::filesystem::path path;
	};
}

int main(const int a_argc, const char* const* a_argv)
{
	if (a_argc != 2) {
		std::cerr << "usage: EnsrickCurrencyConfigTests <runtime-config.json>\n";
		return 2;
	}
	try {
		const auto config = Ensrick::Currency::LoadConfig(std::filesystem::path(a_argv[1]));
		if (config.owner != "EnsrickCurrencyDenominations" || config.families.size() < 2 || config.routingRules.empty() ||
			!config.strictSingleOwner || !config.excludePhysicalFormsFromOrdinaryBarter ||
			config.excludePhysicalFormsFromDrop || config.disabledQuests.size() != 2) {
			std::cerr << "runtime config did not satisfy the reviewed bridge contract\n";
			return 1;
		}
		std::ifstream input(a_argv[1], std::ios::binary);
		const auto fixture = json::parse(input);
		MutationFile mutation;
		std::size_t rejected = 0;
		auto reject = [&](const char* label, auto modify) {
			auto changed = fixture;
			modify(changed);
			{
				std::ofstream output(mutation.path, std::ios::binary | std::ios::trunc);
				output << changed.dump(2);
				if (!output) {
					throw std::runtime_error("could not write isolated config mutation fixture");
				}
			}
			try {
				(void)Ensrick::Currency::LoadConfig(mutation.path);
			} catch (const std::exception&) {
				++rejected;
				return;
			}
			throw std::runtime_error(std::string("invalid config accepted: ") + label);
		};
		reject("old schema", [](json& j) { j["schemaVersion"] = 1; });
		reject("old root exclusion", [](json& j) { j["ancientExclusions"] = json::array(); });
		reject("old routing exclusion", [](json& j) { j["routing"]["ancientExclusionKeywords"] = json::array(); });
		reject("old family route", [](json& j) { j["families"][0]["routeKeywords"] = json::array(); });
		reject("legacy singleton marker", [](json& j) { j["families"][0]["legacySingleton"] = true; });
		reject("singleton", [](json& j) {
			j["families"][0]["denominations"] = json::array({ j["families"][0]["denominations"][0] });
		});
		reject("missing gold", [](json& j) { j["families"][0]["denominations"].erase(2); });
		reject("wrong named value", [](json& j) { j["families"][0]["denominations"][0]["value"] = 25; });
		reject("unknown tier", [](json& j) { j["families"][0]["denominations"][0]["tier"] = "platinum"; });
		reject("duplicate named tier", [](json& j) {
			j["families"][0]["denominations"][1]["tier"] = j["families"][0]["denominations"][0]["tier"];
			j["families"][0]["denominations"][1]["value"] = j["families"][0]["denominations"][0]["value"];
		});
		reject("duplicate physical form", [](json& j) {
			j["families"][0]["denominations"][1]["form"] = j["families"][0]["denominations"][0]["form"];
		});
		reject("backend physical form", [](json& j) {
			j["families"][0]["denominations"][0]["form"] = j["accounting"]["backendForm"];
		});
		reject("missing regional rules", [](json& j) { j["routing"]["rules"] = json::array(); });
		reject("empty route keyword", [](json& j) { j["routing"]["rules"][0]["anyKeywords"] = json::array(); });
		reject("empty route family", [](json& j) { j["routing"]["rules"][0]["familyIds"] = json::array(); });
		reject("unknown route family", [](json& j) { j["routing"]["rules"][0]["familyIds"][0] = "does-not-exist"; });
		reject("duplicate route family", [](json& j) {
			auto& ids = j["routing"]["rules"][0]["familyIds"];
			ids.push_back(ids[0]);
		});
		reject("duplicate route keyword", [](json& j) {
			auto& keywords = j["routing"]["rules"][0]["anyKeywords"];
			keywords.push_back(keywords[0]);
		});
		reject("duplicate route id", [](json& j) { j["routing"]["rules"].push_back(j["routing"]["rules"][0]); });
		reject("duplicate family id/salt", [](json& j) { j["families"].push_back(j["families"][0]); });
		reject("duplicate family salt", [](json& j) { j["families"][1]["salt"] = j["families"][0]["salt"]; });
		reject("alias repeats canonical", [](json& j) {
			j["families"][0]["inputAliases"] = json::array({ {
				{ "tier", "copper" }, { "form", j["families"][0]["denominations"][0]["form"] } } });
		});
		reject("alias names unknown tier", [](json& j) {
			j["families"][0]["inputAliases"] = json::array({ {
				{ "tier", "platinum" }, { "form", "000800:AliasMutation.esp" } } });
		});
		reject("alias independently sets value", [](json& j) {
			j["families"][0]["inputAliases"] = json::array({ {
				{ "tier", "copper" }, { "form", "000800:AliasMutation.esp" }, { "value", 500 } } });
		});
		reject("alias uses backend", [](json& j) {
			j["families"][0]["inputAliases"] = json::array({ {
				{ "tier", "copper" }, { "form", j["accounting"]["backendForm"] } } });
		});
		reject("disabled routed family", [](json& j) {
			const auto id = j["routing"]["rules"][0]["familyIds"][0];
			for (auto& family : j["families"]) {
				if (family["id"] == id) {
					family["enabled"] = false;
				}
			}
		});
		reject("wrong precedence", [](json& j) { j["routing"]["precedence"][1] = "ancientExclusions"; });
		std::cout << "PASS: strict complete-tier config parsed with " << config.families.size()
			<< " families and " << rejected << " invalid contracts rejected; ledgerFingerprint="
			<< std::hex << std::uppercase << Ensrick::Currency::ComputeLedgerFingerprint(config) << '\n';
		return 0;
	} catch (const std::exception& error) {
		std::cerr << error.what() << '\n';
		return 1;
	}
}
