#pragma once

#include "SpawnModel.h"

#include <cstdint>
#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>

namespace BoundedEncounters
{
	struct Limits
	{
		std::uint32_t maxAdditionalInterior{ 12 };
		std::uint32_t maxAdditionalExterior{ 20 };
		std::uint32_t maxHostilesInterior{ 24 };
		std::uint32_t maxHostilesExterior{ 40 };
		float maximumExteriorDistance{ 12000.0F };
		float placementRadiusMin{ 96.0F };
		float placementRadiusMax{ 256.0F };
	};

	struct Exclusions
	{
		bool dragons{ true };
		bool unique{ true };
		bool essential{ true };
		bool protectedActors{ true };
		bool nonRespawning{ true };
		bool persistentReferences{ true };
		bool questAliases{ true };
		bool locationBosses{ true };
		bool summons{ true };
		bool commandedActors{ true };
	};

	struct Config
	{
		std::uint32_t schemaVersion{ 1 };
		bool enabled{ true };
		bool observeOnly{ true };
		bool debugLogging{ false };
		std::uint64_t seed{ 0x424F554E444544ULL };
		std::unordered_map<Category, Curve> curves;
		Limits limits;
		Exclusions exclusions;
		std::vector<std::string> allowedSourcePlugins;
		std::vector<std::string> deniedPlugins;
	};

	[[nodiscard]] Config DefaultConfig();
	[[nodiscard]] Config LoadConfig(const std::filesystem::path& a_path);
	void ValidateConfig(const Config& a_config);
}
