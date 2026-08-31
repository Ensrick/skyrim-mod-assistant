#include "PCH.h"

#include "Classifier.h"

#include <cctype>

namespace BoundedEncounters
{
	namespace
	{
		[[nodiscard]] std::string Lowercase(std::string_view a_value)
		{
			std::string result;
			result.reserve(a_value.size());
			for (const auto character : a_value) {
				result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
			}
			return result;
		}

		[[nodiscard]] bool IsDynamicReference(const RE::TESObjectREFR* a_reference)
		{
			return a_reference && (a_reference->GetFormID() & 0xFF000000U) == 0xFF000000U;
		}

		[[nodiscard]] bool HasLeveledTemplate(const RE::TESActorBase* a_source)
		{
			const RE::TESForm* current = a_source ? a_source->baseTemplateForm : nullptr;
			std::unordered_set<RE::FormID> visited;
			for (std::uint32_t depth = 0; current && depth < 64; ++depth) {
				if (!visited.insert(current->GetFormID()).second) {
					return false;
				}
				if (current->GetFormType() == RE::FormType::LeveledNPC) {
					return true;
				}
				const auto* templateBase = current->As<RE::TESActorBase>();
				current = templateBase ? templateBase->baseTemplateForm : nullptr;
			}
			return false;
		}
	}

	bool Classifier::Initialize()
	{
		_actorTypeAnimal = RE::TESForm::LookupByEditorID<RE::BGSKeyword>("ActorTypeAnimal");
		_actorTypeCreature = RE::TESForm::LookupByEditorID<RE::BGSKeyword>("ActorTypeCreature");
		_actorTypeDragon = RE::TESForm::LookupByEditorID<RE::BGSKeyword>("ActorTypeDragon");
		_giantRace = RE::TESForm::LookupByEditorID<RE::TESRace>("GiantRace");
		_mammothRace = RE::TESForm::LookupByEditorID<RE::TESRace>("MammothRace");
		constexpr RE::FormID bossRefTypeLocalFormID = 0x000130F7;
		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		auto* bossByFormID = dataHandler ?
			dataHandler->LookupForm<RE::BGSLocationRefType>(bossRefTypeLocalFormID, "Skyrim.esm") : nullptr;
		auto* bossByEditorID = RE::TESForm::LookupByEditorID<RE::BGSLocationRefType>("Boss");
		const auto* bossDefiningFile = bossByFormID ? bossByFormID->GetFile(0) : nullptr;
		const auto* bossEditorID = bossByFormID ? bossByFormID->GetFormEditorID() : nullptr;
		const bool bossIdentityVerified = bossByFormID && bossByEditorID == bossByFormID &&
			bossByFormID->GetFormID() == bossRefTypeLocalFormID && bossDefiningFile &&
			Lowercase(bossDefiningFile->GetFilename()) == "skyrim.esm" && bossEditorID &&
			std::string_view(bossEditorID) == "Boss";
		_bossRefType = bossIdentityVerified ? bossByFormID : nullptr;

		logger::info(
			"classifier forms: animal={} creature={} dragon={} giantRace={} mammothRace={} bossRefType={}",
			_actorTypeAnimal ? "found" : "missing",
			_actorTypeCreature ? "found" : "missing",
			_actorTypeDragon ? "found" : "missing",
			_giantRace ? "found" : "missing",
			_mammothRace ? "found" : "missing",
			_bossRefType ? "found-and-verified" : "missing-or-mismatched");

		return _actorTypeAnimal && _actorTypeCreature && _actorTypeDragon &&
			_giantRace && _mammothRace && _bossRefType;
	}

	bool Classifier::HasKeyword(const RE::Actor* a_actor, const RE::BGSKeyword* a_keyword) const
	{
		return a_actor && a_keyword && a_actor->HasKeyword(a_keyword);
	}

	bool Classifier::IsDeniedPlugin(const RE::TESForm* a_form, const Config& a_config) const
	{
		if (!a_form) {
			return false;
		}
		const auto denied = [&](const RE::TESFile* a_file) {
			if (!a_file) {
				return false;
			}
			const auto filename = Lowercase(a_file->GetFilename());
			return std::ranges::any_of(a_config.deniedPlugins, [&](const std::string& a_denied) {
				return filename == Lowercase(a_denied);
			});
		};

		// Index zero is the defining plugin; the default index is the final
		// provider. Checking both makes the deny list effective for mod-added
		// references using vanilla bases and for records adopted by a runtime-
		// incompatible override.
		return denied(a_form->GetFile(0)) || denied(a_form->GetFile());
	}

	bool Classifier::IsAllowedSourcePlugin(const RE::TESForm* a_form, const Config& a_config) const
	{
		if (!a_form) {
			return false;
		}
		const auto allowed = [&](const RE::TESFile* a_file) {
			if (!a_file) {
				return false;
			}
			const auto filename = Lowercase(a_file->GetFilename());
			return std::ranges::any_of(a_config.allowedSourcePlugins, [&](const std::string& a_allowed) {
				return filename == Lowercase(a_allowed);
			});
		};

		// Both provenance and the effective winner must be reviewed. A record
		// defined by an official master but behaviorally replaced by an
		// unreviewed override is not an official-only source.
		return allowed(a_form->GetFile(0)) && allowed(a_form->GetFile());
	}

	bool Classifier::IsAllowedLeveledSource(
		const RE::TESActorBase* a_source,
		const Config& a_config) const
	{
		if (!a_source) {
			return false;
		}

		std::unordered_set<RE::FormID> active;
		std::unordered_set<RE::FormID> complete;
		bool reachedLeveledList = false;
		std::function<bool(const RE::TESForm*, std::uint32_t)> inspect;
		inspect = [&](const RE::TESForm* a_form, const std::uint32_t a_depth) -> bool {
			if (!a_form || a_depth >= 64 || complete.size() >= 4096) {
				return false;
			}
			const auto formID = a_form->GetFormID();
			if (complete.contains(formID)) {
				return true;
			}
			if (!active.insert(formID).second) {
				return false;
			}

			const auto finish = [&](const bool a_result) {
				active.erase(formID);
				if (a_result) {
					complete.insert(formID);
				}
				return a_result;
			};
			if (!IsAllowedSourcePlugin(a_form, a_config) || a_form->HasVMAD()) {
				return finish(false);
			}

			if (const auto* leveled = a_form->As<RE::TESLeveledList>()) {
				reachedLeveledList = true;
				for (const auto& entry : leveled->entries) {
					if (!entry.form || !inspect(entry.form, a_depth + 1)) {
						return finish(false);
					}
				}
				return finish(true);
			}

			const auto* actorBase = a_form->As<RE::TESActorBase>();
			if (!actorBase || actorBase->IsUnique() || actorBase->IsEssential() ||
				actorBase->IsProtected() || !actorBase->Respawns()) {
				return finish(false);
			}
			if (actorBase->baseTemplateForm && !inspect(actorBase->baseTemplateForm, a_depth + 1)) {
				return finish(false);
			}
			return finish(true);
		};

		return inspect(a_source, 0) && reachedLeveledList;
	}

	Classification Classifier::Evaluate(
		RE::Actor* a_actor,
		RE::PlayerCharacter* a_player,
		const Config& a_config) const
	{
		return EvaluateImpl(a_actor, a_player, a_config, false);
	}

	Classification Classifier::EvaluateSpawn(
		RE::Actor* a_actor,
		RE::PlayerCharacter* a_player,
		const Config& a_config,
		const Category a_expectedCategory) const
	{
		auto result = EvaluateImpl(a_actor, a_player, a_config, true);
		if (result.category != Category::Excluded && result.category != a_expectedCategory) {
			return { .reason = "resolved-category-mismatch" };
		}
		return result;
	}

	Classification Classifier::EvaluateImpl(
		RE::Actor* a_actor,
		RE::PlayerCharacter* a_player,
		const Config& a_config,
		const bool a_allowDynamicReference) const
	{
		if (!a_actor || !a_player || a_actor == a_player) {
			return { .reason = "not-an-enemy-source" };
		}
		if (!a_allowDynamicReference && IsDynamicReference(a_actor)) {
			return { .reason = "dynamic-reference" };
		}
		if (!a_allowDynamicReference && !IsAllowedSourcePlugin(a_actor, a_config)) {
			return { .reason = "source-plugin-not-allowed" };
		}
		if (a_actor->IsDisabled() || a_actor->IsMarkedForDeletion() || a_actor->IsDead()) {
			return { .reason = "inactive-or-dead" };
		}
		if (a_actor->IsPlayerTeammate() || !a_actor->IsHostileToActor(a_player)) {
			return { .reason = "not-hostile-to-player" };
		}
		if (a_config.exclusions.persistentReferences && a_actor->IsPersistent()) {
			return { .reason = "persistent-reference" };
		}
		if (a_config.exclusions.summons && a_actor->IsSummoned()) {
			return { .reason = "summoned" };
		}
		if (a_config.exclusions.commandedActors && a_actor->GetCommandingActor()) {
			return { .reason = "commanded-actor" };
		}

		auto* actorBase = a_actor->GetActorBase();
		if (!actorBase) {
			return { .reason = "missing-actor-base" };
		}
		if (a_actor->HasVMAD() || actorBase->HasVMAD()) {
			return { .reason = "script-bound-actor" };
		}
		if (a_config.exclusions.unique && actorBase->IsUnique()) {
			return { .reason = "unique-actor" };
		}
		if (a_config.exclusions.essential && (actorBase->IsEssential() || a_actor->IsEssential())) {
			return { .reason = "essential-actor" };
		}
		if (a_config.exclusions.protectedActors && (actorBase->IsProtected() || a_actor->IsProtected())) {
			return { .reason = "protected-actor" };
		}
		// ACHR header bit 30 is not an affirmative respawn flag. xEdit's generic
		// REFR definition calls it No Respawn, while its ACHR-specific definition
		// does not expose the bit at all. Respawn eligibility therefore comes from
		// the actor base; treating the reference bit as positive would reject nearly
		// every ordinary placed actor and could admit the inverse case.
		if (a_config.exclusions.nonRespawning && !PassesNonRespawningExclusion(actorBase->Respawns())) {
			return { .reason = "non-respawning-base" };
		}
		if (a_config.exclusions.questAliases) {
			if (a_actor->HasQuestObject()) {
				return { .reason = "quest-object" };
			}
			if (const auto* aliases = a_actor->extraList.GetByType<RE::ExtraAliasInstanceArray>();
				aliases && !aliases->aliases.empty()) {
				return { .reason = "quest-alias" };
			}
		}
		if (a_config.exclusions.locationBosses) {
			if (const auto* locationType = a_actor->extraList.GetByType<RE::ExtraLocationRefType>();
				locationType && locationType->locRefType && locationType->locRefType == _bossRefType) {
				return { .reason = "location-boss" };
			}
		}

		auto* spawnBase = static_cast<RE::TESBoundObject*>(actorBase);
		bool rerollsLeveledList = false;
		const RE::TESActorBase* leveledSource = nullptr;
		const auto* modifierData = a_actor->extraList.GetByType<RE::ExtraLevCreaModifier>();
		const auto levelModifier = modifierData ?
			modifierData->modifier.get() : RE::LEV_CREA_MODIFIER::kNone;
		if (levelModifier == RE::LEV_CREA_MODIFIER::kNone) {
			// Once Skyrim resolves a leveled actor, GetObjectReference() exposes the
			// resolved NPC_. ExtraLeveledCreature retains the authored source NPC_
			// whose template chain reaches the original LVLN. Reusing that source is
			// what permits a companion to resolve independently.
			if (const auto* leveled = a_actor->extraList.GetByType<RE::ExtraLeveledCreature>();
				leveled && leveled->originalBase && HasLeveledTemplate(leveled->originalBase)) {
				leveledSource = leveled->originalBase;
			} else if (HasLeveledTemplate(actorBase)) {
				leveledSource = actorBase;
			}
		}
		if (leveledSource) {
			if (!IsAllowedLeveledSource(leveledSource, a_config)) {
				return { .reason = "leveled-source-graph-not-allowed" };
			}
			spawnBase = const_cast<RE::TESActorBase*>(leveledSource);
			rerollsLeveledList = true;
		}
		// A non-default XLCM modifier affects leveled resolution before the new
		// reference exists, so it cannot safely be copied in time through the
		// public creation API. Fixed/resolved sources are excluded in the alpha
		// rather than cloned or silently shifted to another encounter tier.
		if (!a_allowDynamicReference && !rerollsLeveledList) {
			return { .reason = "fixed-source-not-allowlisted" };
		}
		if (!IsAllowedSourcePlugin(actorBase, a_config) ||
			!IsAllowedSourcePlugin(spawnBase, a_config)) {
			return { .reason = "source-provider-not-allowed" };
		}
		if (spawnBase->HasVMAD()) {
			return { .reason = "script-bound-source" };
		}
		if (IsDeniedPlugin(a_actor, a_config) || IsDeniedPlugin(actorBase, a_config) ||
			IsDeniedPlugin(spawnBase, a_config)) {
			return { .reason = "denied-plugin" };
		}

		if (a_config.exclusions.dragons && (a_actor->IsDragon() || HasKeyword(a_actor, _actorTypeDragon))) {
			return { .reason = "dragon" };
		}

		const auto* race = a_actor->GetRace();
		Category category = Category::General;
		if ((race && race == _giantRace) || (race && race == _mammothRace)) {
			category = Category::GiantMammoth;
		} else if (HasKeyword(a_actor, _actorTypeAnimal) ||
			HasKeyword(a_actor, _actorTypeCreature) || a_actor->IsAnimal()) {
			category = Category::AnimalBeast;
		}

		return {
			.category = category,
			.spawnBase = spawnBase,
			.reason = rerollsLeveledList ? "eligible-leveled-source" : "eligible-resolved-source",
			.rerollsLeveledList = rerollsLeveledList
		};
	}
}
