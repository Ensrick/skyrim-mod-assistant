#include "PCH.h"

#include "Diagnostics.h"
#include "EncounterManager.h"

namespace BoundedEncounters
{
	namespace
	{
		class PendingSpawn final
		{
		public:
			explicit PendingSpawn(RE::TESObjectREFR* a_reference) noexcept :
				_reference(a_reference)
			{}

			~PendingSpawn() noexcept
			{
				if (!_reference || _committed) {
					return;
				}
				try {
					_reference->Disable();
					_reference->SetDelete(true);
				} catch (...) {
					try {
						logger::critical("failed to roll back an uncommitted generated reference");
					} catch (...) {
					}
				}
			}

			PendingSpawn(const PendingSpawn&) = delete;
			PendingSpawn& operator=(const PendingSpawn&) = delete;

			void Commit() noexcept { _committed = true; }

		private:
			RE::TESObjectREFR* _reference{ nullptr };
			bool _committed{ false };
		};

		[[nodiscard]] bool IsDynamicReference(const RE::TESObjectREFR* a_reference)
		{
			return a_reference && (a_reference->GetFormID() & 0xFF000000U) == 0xFF000000U;
		}

		[[nodiscard]] bool InExteriorRange(
			const RE::Actor& a_actor,
			RE::PlayerCharacter& a_player,
			const Config& a_config)
		{
			const auto* cell = a_actor.GetParentCell();
			return !cell || !cell->IsExteriorCell() ||
				a_actor.GetDistance(std::addressof(a_player)) <= a_config.limits.maximumExteriorDistance;
		}
	}

	void EncounterManager::Initialize(Config a_config)
	{
		_config = std::move(a_config);
		const bool classifierReady = _classifier.Initialize();
		_classifierReady.store(classifierReady, std::memory_order_release);
		const bool enabled = _config.enabled && classifierReady &&
			_registered.load(std::memory_order_acquire);
		_enabled.store(enabled, std::memory_order_release);
		if (_config.enabled && !classifierReady) {
			logger::critical("one or more mandatory classification forms are missing; encounter scaling is disabled");
		}
		logger::info(
			"manager initialized: requestedEnabled={} effectiveEnabled={} observeOnly={} seed={} interiorExtraCap={} exteriorExtraCap={}",
			_config.enabled,
			enabled,
			_config.observeOnly,
			_config.seed,
			_config.limits.maxAdditionalInterior,
			_config.limits.maxAdditionalExterior);
	}

	void EncounterManager::Disable() noexcept
	{
		_config.enabled = false;
		_enabled.store(false, std::memory_order_release);
	}

	void EncounterManager::Register()
	{
		if (_registered.load(std::memory_order_acquire)) {
			return;
		}
		auto* source = RE::ScriptEventSourceHolder::GetSingleton();
		auto* player = RE::PlayerCharacter::GetSingleton();
		auto* playerCellSource = player ? player->AsBGSActorCellEventSource() : nullptr;
		if (!source || !playerCellSource) {
			logger::error("required cell event sources are unavailable; encounter scaling is disabled");
			_registered.store(false, std::memory_order_release);
			_enabled.store(false, std::memory_order_release);
			return;
		}
		source->AddEventSink<RE::TESCellFullyLoadedEvent>(this);
		playerCellSource->AddEventSink<RE::BGSActorCellEvent>(this);
		_registered.store(true, std::memory_order_release);
		_enabled.store(
			_config.enabled && _classifierReady.load(std::memory_order_acquire),
			std::memory_order_release);
		logger::info("registered loaded-cell and player-cell event sinks");
	}

	void EncounterManager::BeginSession(const std::string_view a_reason)
	{
		_enabled.store(false, std::memory_order_release);
		_loadSuspended.store(false, std::memory_order_release);
		const auto nextSession = _session.fetch_add(1, std::memory_order_acq_rel) + 1;
		{
			std::unique_lock lock(_stateLock);
			_processedCells.clear();
			_spawnedHandles.clear();
			_spawnsByCell.clear();
		}
		_enabled.store(
			_config.enabled && _classifierReady.load(std::memory_order_acquire) &&
				_registered.load(std::memory_order_acquire),
			std::memory_order_release);
		logger::info("session reset: id={} reason={}", nextSession, a_reason);
	}

	void EncounterManager::SuspendForLoad()
	{
		_enabled.store(false, std::memory_order_release);
		_loadSuspended.store(true, std::memory_order_release);
		const auto nextSession = _session.fetch_add(1, std::memory_order_acq_rel) + 1;
		// Preserve the current registry until SKSE confirms that the load
		// succeeded. If loading fails, Skyrim resumes the current world and its
		// recursion/cap state must remain authoritative.
		logger::info("load suspended: pendingSession={}", nextSession);
	}

	void EncounterManager::CompleteLoad(const bool a_succeeded)
	{
		if (!_loadSuspended.exchange(false, std::memory_order_acq_rel)) {
			logger::warn("post-load message arrived without a matching pre-load message; spawning remains disabled");
			_enabled.store(false, std::memory_order_release);
			return;
		}

		if (a_succeeded) {
			std::unique_lock lock(_stateLock);
			_processedCells.clear();
			_spawnedHandles.clear();
			_spawnsByCell.clear();
		}

		_enabled.store(
			_config.enabled && _classifierReady.load(std::memory_order_acquire) &&
				_registered.load(std::memory_order_acquire),
			std::memory_order_release);
		logger::info(
			"load completed: session={} succeeded={} effectiveEnabled={}",
			_session.load(std::memory_order_acquire),
			a_succeeded,
			_enabled.load(std::memory_order_acquire));
	}

	void EncounterManager::QueueCurrentCell()
	{
		const auto* player = RE::PlayerCharacter::GetSingleton();
		const auto* cell = player ? player->GetParentCell() : nullptr;
		if (cell) {
			QueueCell(cell->GetFormID());
		}
	}

	bool EncounterManager::IsSpawned(const RE::Character* a_actor) const
	{
		if (!a_actor) {
			return false;
		}
		const auto handle = const_cast<RE::Character*>(a_actor)->GetHandle();
		if (!handle) {
			return false;
		}
		std::shared_lock lock(_stateLock);
		return _spawnedHandles.contains(handle.native_handle());
	}

	RE::BSEventNotifyControl EncounterManager::ProcessEvent(
		const RE::TESCellFullyLoadedEvent* a_event,
		RE::BSTEventSource<RE::TESCellFullyLoadedEvent>*)
	{
		try {
			const auto* player = RE::PlayerCharacter::GetSingleton();
			if (a_event && a_event->cell && player &&
				a_event->cell == player->GetParentCell() &&
				_enabled.load(std::memory_order_acquire)) {
				QueueCell(a_event->cell->GetFormID());
			}
		} catch (const std::exception& error) {
			_enabled.store(false, std::memory_order_release);
			const auto diagnostic = MakeBoundedDiagnostic(error.what());
			try {
				logger::critical("loaded-cell event failed closed: {}", diagnostic.View());
			} catch (...) {
			}
		} catch (...) {
			_enabled.store(false, std::memory_order_release);
			try {
				logger::critical("loaded-cell event failed closed with an unknown exception");
			} catch (...) {
			}
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	RE::BSEventNotifyControl EncounterManager::ProcessEvent(
		const RE::BGSActorCellEvent* a_event,
		RE::BSTEventSource<RE::BGSActorCellEvent>*)
	{
		try {
			if (!a_event || a_event->flags != RE::BGSActorCellEvent::CellFlag::kEnter ||
				!_enabled.load(std::memory_order_acquire)) {
				return RE::BSEventNotifyControl::kContinue;
			}
			auto eventActor = a_event->actor.get();
			if (eventActor && eventActor.get() == RE::PlayerCharacter::GetSingleton()) {
				QueueCell(a_event->cellID);
			}
		} catch (const std::exception& error) {
			_enabled.store(false, std::memory_order_release);
			const auto diagnostic = MakeBoundedDiagnostic(error.what());
			try {
				logger::critical("actor-cell event failed closed: {}", diagnostic.View());
			} catch (...) {
			}
		} catch (...) {
			_enabled.store(false, std::memory_order_release);
			try {
				logger::critical("actor-cell event failed closed with an unknown exception");
			} catch (...) {
			}
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	void EncounterManager::QueueCell(const RE::FormID a_cellID)
	{
		if (a_cellID == 0 || !_enabled.load(std::memory_order_acquire)) {
			return;
		}
		const auto session = _session.load(std::memory_order_acquire);
		if (const auto* tasks = SKSE::GetTaskInterface()) {
			tasks->AddTask([this, a_cellID, session]() {
				try {
					ProcessCell(a_cellID, session);
				} catch (const std::exception& error) {
					_enabled.store(false, std::memory_order_release);
					const auto diagnostic = MakeBoundedDiagnostic(error.what());
					try {
						logger::critical(
							"cell task failed closed: cell={:08X} error={}",
							a_cellID,
							diagnostic.View());
					} catch (...) {
					}
				} catch (...) {
					_enabled.store(false, std::memory_order_release);
					try {
						logger::critical("cell task failed closed: cell={:08X} unknown error", a_cellID);
					} catch (...) {
					}
				}
			});
		} else {
			logger::error("SKSE task interface is unavailable; cell {:08X} was not processed", a_cellID);
		}
	}

	RE::NiPoint3 EncounterManager::PlacementFor(
		const RE::Actor& a_source,
		const std::uint64_t a_sourceKey,
		const std::uint32_t a_extraIndex,
		const std::uint32_t a_playerLevel) const
	{
		auto seed = MixSeed(_config.seed, a_sourceKey);
		seed = MixSeed(seed, a_extraIndex);
		seed = MixSeed(seed, a_playerLevel);
		constexpr double inverse53Bits = 1.0 / 9007199254740992.0;
		const auto angleUnit = static_cast<double>(seed >> 11U) * inverse53Bits;
		const auto radiusBits = MixSeed(seed, 0x504C4143454D454EULL);
		const auto radiusUnit = static_cast<double>(radiusBits >> 11U) * inverse53Bits;
		const auto chosenAngle = static_cast<float>(angleUnit * 2.0 * std::numbers::pi);
		const auto chosenRadius = _config.limits.placementRadiusMin +
			static_cast<float>(radiusUnit) *
			(_config.limits.placementRadiusMax - _config.limits.placementRadiusMin);

		const auto sourcePosition = a_source.GetPosition();
		return {
			sourcePosition.x + std::cos(chosenAngle) * chosenRadius,
			sourcePosition.y + std::sin(chosenAngle) * chosenRadius,
			sourcePosition.z
		};
	}

	bool EncounterManager::TrackSpawn(RE::Character& a_actor, const RE::FormID a_cellID)
	{
		const auto handle = a_actor.GetHandle();
		if (!handle || !IsDynamicReference(std::addressof(a_actor))) {
			return false;
		}
		std::unique_lock lock(_stateLock);
		const auto nativeHandle = handle.native_handle();
		const auto [handleIt, inserted] = _spawnedHandles.insert(nativeHandle);
		(void)handleIt;
		if (!inserted) {
			return false;
		}
		try {
			_spawnsByCell[a_cellID].push_back(handle);
		} catch (...) {
			_spawnedHandles.erase(nativeHandle);
			const auto cellIt = _spawnsByCell.find(a_cellID);
			if (cellIt != _spawnsByCell.end() && cellIt->second.empty()) {
				_spawnsByCell.erase(cellIt);
			}
			throw;
		}
		return true;
	}

	std::uint32_t EncounterManager::CountActiveGeneratedActors() const
	{
		std::uint32_t count = 0;
		std::shared_lock lock(_stateLock);
		for (const auto& [cellID, handles] : _spawnsByCell) {
			(void)cellID;
			for (const auto& handle : handles) {
				auto reference = handle.get();
				auto* actor = reference ? reference->As<RE::Character>() : nullptr;
				const auto* parentCell = actor ? actor->GetParentCell() : nullptr;
				if (actor && parentCell && parentCell->IsAttached() &&
					!actor->IsDisabled() && !actor->IsMarkedForDeletion()) {
					++count;
				}
			}
		}
		return count;
	}

	void EncounterManager::ProcessCell(const RE::FormID a_cellID, const std::uint64_t a_session)
	{
		if (!_enabled.load(std::memory_order_acquire) ||
			a_session != _session.load(std::memory_order_acquire)) {
			return;
		}

		auto* cell = RE::TESForm::LookupByID<RE::TESObjectCELL>(a_cellID);
		auto* player = RE::PlayerCharacter::GetSingleton();
		const auto* loadedData = cell ? cell->GetRuntimeData().loadedData : nullptr;
		if (!cell || !player || player->GetParentCell() != cell || !cell->IsAttached() ||
			!loadedData || !loadedData->refsFullyLoaded) {
			return;
		}

		{
			std::unique_lock lock(_stateLock);
			if (_processedCells.contains(a_cellID)) {
				return;
			}
			_processedCells.insert(a_cellID);
		}

		std::vector<RE::ActorHandle> actorHandles;
		cell->ForEachReference([&](RE::TESObjectREFR* a_reference) {
			if (auto* actor = a_reference ? a_reference->As<RE::Actor>() : nullptr) {
				actorHandles.push_back(actor->GetHandle());
			}
			return RE::BSContainer::ForEachResult::kContinue;
		});

		std::vector<SourceCandidate> candidates;
		std::uint32_t liveHostiles = 0;
		std::uint32_t rejected = 0;
		std::uint32_t statefulReferenceRejections = 0;
		std::uint32_t leveledSources = 0;

		for (const auto& actorHandle : actorHandles) {
			auto actorPointer = actorHandle.get();
			auto* actor = actorPointer.get();
			if (!actor || actor == player || actor->IsDead() ||
				actor->IsDisabled() || actor->IsMarkedForDeletion() || !InExteriorRange(*actor, *player, _config)) {
				continue;
			}

			if (actor->IsHostileToActor(player)) {
				++liveHostiles;
			}
			// Runtime-created enemies are never eligible sources, but they still
			// consume the cell's total-hostile budget. Ignoring them here would let
			// this plugin oversubscribe encounters already populated by another
			// runtime system (or by an earlier Bounded Encounters spawn).
			if (IsDynamicReference(actor)) {
				continue;
			}

			const auto classification = _classifier.Evaluate(actor, player, _config);
			if (classification.category == Category::Excluded || !classification.spawnBase) {
				++rejected;
				statefulReferenceRejections += static_cast<std::uint32_t>(
					classification.reason.starts_with("stateful-reference-"));
				if (_config.debugLogging) {
					logger::debug(
						"source rejected: cell={:08X} ref={:08X} reason={}",
						a_cellID,
						actor->GetFormID(),
						classification.reason);
				}
				continue;
			}

			const auto curve = _config.curves.find(classification.category);
			if (curve == _config.curves.end() || !curve->second.enabled) {
				++rejected;
				continue;
			}

			const std::uint64_t sourceKey =
				(static_cast<std::uint64_t>(a_cellID) << 32U) | actor->GetFormID();
			candidates.push_back({
				.key = sourceKey,
				.actor = actor->GetHandle(),
				.spawnBase = classification.spawnBase,
				.category = classification.category,
				.rerollsLeveledList = classification.rerollsLeveledList
			});
			leveledSources += static_cast<std::uint32_t>(classification.rerollsLeveledList);
		}
		std::ranges::sort(candidates, {}, &SourceCandidate::key);

		const bool interior = cell->IsInteriorCell();
		const auto additionalCap = interior ?
			_config.limits.maxAdditionalInterior : _config.limits.maxAdditionalExterior;
		const auto hostileCap = interior ?
			_config.limits.maxHostilesInterior : _config.limits.maxHostilesExterior;
		const auto remainingHostileCapacity = liveHostiles >= hostileCap ? 0U : hostileCap - liveHostiles;
		// Exterior streaming may fully load several adjacent cells together.
		// Bound the whole attached area as well as each cell, and cap one event
		// evaluation's creation burst to keep main-thread work predictable.
		const auto activeGenerated = CountActiveGeneratedActors();
		const auto activeAreaCap = std::max(
			_config.limits.maxHostilesInterior,
			_config.limits.maxHostilesExterior);
		const auto remainingActiveCapacity = activeGenerated >= activeAreaCap ?
			0U : activeAreaCap - activeGenerated;
		constexpr std::uint32_t maxSpawnsPerEvaluation = 8;
		const auto effectiveCap = std::min({
			additionalCap,
			remainingHostileCapacity,
			remainingActiveCapacity,
			maxSpawnsPerEvaluation });

		std::vector<SourceDescriptor> descriptors;
		descriptors.reserve(candidates.size());
		for (const auto& candidate : candidates) {
			descriptors.push_back({ candidate.key, candidate.category });
		}

		const auto playerLevel = static_cast<std::uint32_t>(player->GetLevel());
		const auto cellSeed = MixSeed(_config.seed, a_cellID);
		const auto plan = BuildSpawnPlan(
			descriptors,
			_config.curves,
			playerLevel,
			cellSeed,
			std::optional<std::uint32_t>{ effectiveCap });
		if (_config.debugLogging) {
			for (const auto& candidate : candidates) {
				auto source = candidate.actor.get();
				logger::debug(
					"source audit: cell={:08X} ref={:08X} base={:08X} category={} rerollsLeveledList={}",
					a_cellID,
					source ? source->GetFormID() : 0,
					candidate.spawnBase ? candidate.spawnBase->GetFormID() : 0,
					ToString(candidate.category),
					candidate.rerollsLeveledList);
			}
		}
		if (_config.observeOnly) {
			logger::info(
				"cell audit: session={} cell={:08X} observeOnly=true interior={} playerLevel={} liveHostiles={} activeGenerated={} eligibleSources={} leveledSources={} rejected={} statefulReferenceRejections={} expectedExtras={:.3f} plannedExtras={} created=0 failures=0 cap={}",
				a_session,
				a_cellID,
				interior,
				playerLevel,
				liveHostiles,
				activeGenerated,
				candidates.size(),
				leveledSources,
				rejected,
				statefulReferenceRejections,
				plan.expectedExtras,
				plan.totalExtras,
				effectiveCap);
			return;
		}
		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		std::uint32_t created = 0;
		std::uint32_t failures = 0;

		for (const auto& roll : plan.sources) {
			if (roll.extras == 0 || created >= effectiveCap) {
				continue;
			}
			const auto candidate = std::ranges::find(candidates, roll.sourceKey, &SourceCandidate::key);
			if (candidate == candidates.end()) {
				continue;
			}
			auto sourceActor = candidate->actor.get();
			if (!sourceActor || sourceActor->IsDead() || sourceActor->GetParentCell() != cell) {
				continue;
			}

			for (std::uint32_t index = 0; index < roll.extras && created < effectiveCap; ++index) {
				const auto position = PlacementFor(*sourceActor, candidate->key, index, playerLevel);
				if (!std::isfinite(position.x) || !std::isfinite(position.y) || !std::isfinite(position.z)) {
					logger::error(
						"spawn rejected before creation due to non-finite placement: cell={:08X} source={:08X}",
						a_cellID,
						sourceActor->GetFormID());
					++failures;
					continue;
				}
				const auto rotation = sourceActor->GetAngle();
				const auto newHandle = dataHandler ? dataHandler->CreateReferenceAtLocation(
					candidate->spawnBase,
					position,
					rotation,
					cell,
					sourceActor->GetWorldspace(),
					nullptr,
					nullptr,
					RE::ObjectRefHandle{},
					false,
					true) : RE::ObjectRefHandle{};
				auto newReference = newHandle.get();
				PendingSpawn pendingSpawn(newReference.get());
				auto* newActor = newReference ? newReference->As<RE::Character>() : nullptr;
				if (!newActor) {
					++failures;
					continue;
				}

				newActor->SetTemporary();
				if ((newActor->GetFormFlags() & RE::TESForm::RecordFlags::kTemporary) == 0) {
					logger::error(
						"temporary-reference safety check failed: cell={:08X} source={:08X} spawned={:08X}; deleting spawn",
						a_cellID,
						sourceActor->GetFormID(),
						newActor->GetFormID());
					++failures;
					continue;
				}

				const auto nearestNavmeshVertex = newActor->FindNearestVertex(0.0F);
				const auto nearestDistance = nearestNavmeshVertex ?
					position.GetDistance(*nearestNavmeshVertex) : std::numeric_limits<float>::infinity();
				if (!nearestNavmeshVertex || !std::isfinite(nearestDistance) ||
					nearestDistance > _config.limits.maximumNavmeshSnapDistance ||
					!newActor->MoveToNearestNavmesh(0.0F)) {
					logger::warn(
						"spawn rejected after bounded navmesh placement failed: cell={:08X} source={:08X} spawned={:08X} nearestDistance={}",
						a_cellID,
						sourceActor->GetFormID(),
						newActor->GetFormID(),
						nearestDistance);
					++failures;
					continue;
				}
				const auto finalPosition = newActor->GetPosition();
				const auto desiredDistance = finalPosition.GetDistance(position);
				const auto sourceDistance = finalPosition.GetDistance(sourceActor->GetPosition());
				constexpr float placementTolerance = 1.0F;
				if (!std::isfinite(finalPosition.x) || !std::isfinite(finalPosition.y) ||
					!std::isfinite(finalPosition.z) || !std::isfinite(desiredDistance) ||
					!std::isfinite(sourceDistance) || newActor->GetParentCell() != cell ||
					newActor->GetWorldspace() != sourceActor->GetWorldspace() ||
					desiredDistance > _config.limits.maximumNavmeshSnapDistance + placementTolerance ||
					sourceDistance > _config.limits.placementRadiusMax +
						_config.limits.maximumNavmeshSnapDistance + placementTolerance) {
					logger::warn(
						"spawn rejected after navmesh postcondition failed: cell={:08X} source={:08X} spawned={:08X}",
						a_cellID,
						sourceActor->GetFormID(),
						newActor->GetFormID());
					++failures;
					continue;
				}

				const auto resolved = _classifier.EvaluateSpawn(
					newActor,
					player,
					_config,
					candidate->category,
					candidate->rerollsLeveledList ? candidate->spawnBase : nullptr);
				if (resolved.category == Category::Excluded) {
					logger::warn(
						"spawn rejected after resolution: cell={:08X} source={:08X} spawned={:08X} reason={}",
						a_cellID,
						sourceActor->GetFormID(),
						newActor->GetFormID(),
						resolved.reason);
					++failures;
					continue;
				}

				if (!TrackSpawn(*newActor, a_cellID)) {
					++failures;
					continue;
				}
				pendingSpawn.Commit();
				++created;
			}
		}

		logger::info(
			"cell audit: session={} cell={:08X} observeOnly=false interior={} playerLevel={} liveHostiles={} activeGenerated={} eligibleSources={} leveledSources={} rejected={} statefulReferenceRejections={} expectedExtras={:.3f} plannedExtras={} created={} failures={} cap={}",
			a_session,
			a_cellID,
			interior,
			playerLevel,
			liveHostiles,
			activeGenerated,
			candidates.size(),
			leveledSources,
			rejected,
			statefulReferenceRejections,
			plan.expectedExtras,
			plan.totalExtras,
			created,
			failures,
			effectiveCap);
	}
}
