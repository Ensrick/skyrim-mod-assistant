#pragma once

#include "Config.h"

#include <string>

namespace BoundedEncounters
{
	struct Classification
	{
		Category category{ Category::Excluded };
		RE::TESBoundObject* spawnBase{ nullptr };
		std::string reason{ "unclassified" };
		bool rerollsLeveledList{ false };
	};

	class Classifier
	{
	public:
		[[nodiscard]] bool Initialize();
		[[nodiscard]] Classification Evaluate(RE::Actor* a_actor, RE::PlayerCharacter* a_player, const Config& a_config) const;
		[[nodiscard]] Classification EvaluateSpawn(
			RE::Actor* a_actor,
			RE::PlayerCharacter* a_player,
			const Config& a_config,
			Category a_expectedCategory) const;

	private:
		[[nodiscard]] Classification EvaluateImpl(
			RE::Actor* a_actor,
			RE::PlayerCharacter* a_player,
			const Config& a_config,
			bool a_allowDynamicReference) const;
		[[nodiscard]] bool IsDeniedPlugin(const RE::TESForm* a_form, const Config& a_config) const;
		[[nodiscard]] bool IsAllowedSourcePlugin(const RE::TESForm* a_form, const Config& a_config) const;
		[[nodiscard]] bool IsAllowedLeveledSource(const RE::TESActorBase* a_source, const Config& a_config) const;
		[[nodiscard]] bool HasKeyword(const RE::Actor* a_actor, const RE::BGSKeyword* a_keyword) const;

		RE::BGSKeyword* _actorTypeAnimal{ nullptr };
		RE::BGSKeyword* _actorTypeCreature{ nullptr };
		RE::BGSKeyword* _actorTypeDragon{ nullptr };
		RE::TESRace* _giantRace{ nullptr };
		RE::TESRace* _mammothRace{ nullptr };
		RE::BGSLocationRefType* _bossRefType{ nullptr };
	};
}
