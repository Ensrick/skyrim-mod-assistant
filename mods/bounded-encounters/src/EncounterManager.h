#pragma once

#include "Classifier.h"

namespace BoundedEncounters
{
	class EncounterManager final :
		public REX::Singleton<EncounterManager>,
		public RE::BSTEventSink<RE::TESCellFullyLoadedEvent>,
		public RE::BSTEventSink<RE::BGSActorCellEvent>
	{
	public:
		void Initialize(Config a_config);
		void Register();
		void BeginSession(std::string_view a_reason);
		void SuspendForLoad();
		void CompleteLoad(bool a_succeeded);
		void QueueCurrentCell();
		[[nodiscard]] bool IsSpawned(const RE::Character* a_actor) const;

		RE::BSEventNotifyControl ProcessEvent(
			const RE::TESCellFullyLoadedEvent* a_event,
			RE::BSTEventSource<RE::TESCellFullyLoadedEvent>* a_source) override;
		RE::BSEventNotifyControl ProcessEvent(
			const RE::BGSActorCellEvent* a_event,
			RE::BSTEventSource<RE::BGSActorCellEvent>* a_source) override;

	private:
		struct SourceCandidate
		{
			std::uint64_t key{ 0 };
			RE::ActorHandle actor;
			RE::TESBoundObject* spawnBase{ nullptr };
			Category category{ Category::Excluded };
			bool rerollsLeveledList{ false };
		};

		void QueueCell(RE::FormID a_cellID);
		void ProcessCell(RE::FormID a_cellID, std::uint64_t a_session);
		[[nodiscard]] RE::NiPoint3 PlacementFor(
			const RE::Actor& a_source,
			std::uint64_t a_sourceKey,
			std::uint32_t a_extraIndex,
			std::uint32_t a_playerLevel) const;
		[[nodiscard]] bool TrackSpawn(RE::Character& a_actor, RE::FormID a_cellID);
		[[nodiscard]] std::uint32_t CountActiveGeneratedActors() const;

		Config _config{ DefaultConfig() };
		Classifier _classifier;
		std::atomic_bool _enabled{ false };
		std::atomic_bool _classifierReady{ false };
		std::atomic_bool _registered{ false };
		std::atomic_bool _loadSuspended{ false };
		std::atomic<std::uint64_t> _session{ 1 };
		mutable std::shared_mutex _stateLock;
		std::unordered_set<RE::FormID> _processedCells;
		std::unordered_set<std::uint32_t> _spawnedHandles;
		std::unordered_map<RE::FormID, std::vector<RE::ObjectRefHandle>> _spawnsByCell;
	};
}
