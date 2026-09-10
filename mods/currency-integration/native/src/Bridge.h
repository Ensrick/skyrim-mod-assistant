#pragma once

#include "Config.h"
#include "AdmissionIdentity.h"
#include "LedgerPolicy.h"
#include "SaveMarkerPolicy.h"
#include "SourcePolicy.h"

#include <RE/Skyrim.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace QuickLoot::API::Events
{
	struct OpeningLootMenuEvent;
}

namespace Ensrick::Currency
{
	class Bridge final :
		public RE::BSTEventSink<RE::TESContainerChangedEvent>,
		public RE::BSTEventSink<RE::TESDeathEvent>,
		public RE::BSTEventSink<RE::TESActivateEvent>,
		public RE::BSTEventSink<RE::TESActorLocationChangeEvent>,
		public RE::BSTEventSink<RE::MenuOpenCloseEvent>
	{
	public:
		static Bridge& GetSingleton();

		bool Initialize(const std::filesystem::path& a_configPath);
		void BeginGameAdmission(bool a_freshOrKnownNativeSave, std::optional<SaveCheckpoint> a_checkpoint = std::nullopt);
		void OnCurrencySwapperAdmission(std::uint64_t a_generation, bool a_success);
		void Revert();
		[[nodiscard]] bool IsAdmitted() const noexcept { return _admitted; }
		[[nodiscard]] std::optional<SaveCheckpoint> PrepareSaveCheckpoint() const;
		void ProcessQuickLootOpening(QuickLoot::API::Events::OpeningLootMenuEvent* a_event);

	private:
		struct ResolvedDenomination
		{
			std::uint32_t value{ 0 };
			RE::TESBoundObject* form{ nullptr };
			bool isAlias{ false };
		};

		struct ResolvedFamily
		{
			FamilyConfig config;
			std::vector<ResolvedDenomination> denominations;
			RE::BGSPerk* perk{ nullptr };
		};

		struct ResolvedRoute
		{
			std::string id;
			std::vector<RE::BGSKeyword*> anyKeywords;
			std::vector<RouteDesignCandidate> candidates;
		};

		struct RecognizedSnapshot
		{
			std::int32_t backend{ 0 };
			std::vector<std::vector<std::int32_t>> families;
		};

		enum class SourceKind
		{
			actor,
			container
		};

		RE::BSEventNotifyControl ProcessEvent(
			const RE::TESContainerChangedEvent* a_event,
			RE::BSTEventSource<RE::TESContainerChangedEvent>*) override;
		RE::BSEventNotifyControl ProcessEvent(
			const RE::TESDeathEvent* a_event,
			RE::BSTEventSource<RE::TESDeathEvent>*) override;
		RE::BSEventNotifyControl ProcessEvent(
			const RE::TESActivateEvent* a_event,
			RE::BSTEventSource<RE::TESActivateEvent>*) override;
		RE::BSEventNotifyControl ProcessEvent(
			const RE::TESActorLocationChangeEvent* a_event,
			RE::BSTEventSource<RE::TESActorLocationChangeEvent>*) override;
		RE::BSEventNotifyControl ProcessEvent(
			const RE::MenuOpenCloseEvent* a_event,
			RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override;

		bool ResolveConfiguration();
		void RegisterEventSinks();
		bool InitializeQuickLoot();
		bool StopConflictingQuests();
		bool RequestCurrencySwapperOwnership(std::uint64_t a_generation);
		void CompleteAdmission(std::uint64_t a_generation);

		std::size_t DetermineFamily(const RE::BGSLocation* a_location, std::uint64_t a_sourceIdentity = 0) const;
		bool LocationHasKeyword(const RE::BGSLocation* a_location, const RE::BGSKeyword* a_keyword) const;
		void ApplyRoute(std::size_t a_familyIndex);
		void ApplyPricePerk(bool a_enable);

		void QueuePlayerBackendSync();
		void QueuePlayerPhysicalSync();
		void QueuePlayerMigration(std::size_t a_familyIndex);
		void QueuePlayerFlush();
		void FlushPlayerChanges(std::uint64_t a_generation);
		bool MigratePlayer(std::size_t a_familyIndex);
		bool ReconcileObservedPlayer(std::size_t a_familyIndex);
		bool UpdatePlayerBaseline(std::uint64_t a_value);

		bool ProcessSource(RE::TESObjectREFR* a_source, const char* a_trigger);
		std::optional<SourceKind> ClassifySafeSource(RE::TESObjectREFR* a_source);
		bool IsDeniedActorReference(
			RE::TESObjectREFR* a_source,
			const std::vector<RE::TESNPC*>& a_safetyBases) const;
		bool IsDeniedContainerReference(RE::TESObjectREFR* a_source) const;
		bool HasVendorFaction(const std::vector<RE::TESNPC*>& a_safetyBases) const;

		RecognizedSnapshot ReadSnapshot(RE::TESObjectREFR* a_owner) const;
		std::optional<std::uint64_t> PhysicalValue(const RecognizedSnapshot& a_snapshot) const;
		bool SnapshotMatchesFamily(
			const RecognizedSnapshot& a_snapshot,
			std::size_t a_familyIndex,
			std::uint64_t a_value,
			bool a_broken) const;
		std::optional<std::vector<std::int32_t>> DesiredFamilyCounts(
			std::size_t a_familyIndex,
			std::uint64_t a_value,
			bool a_broken) const;
		bool ApplySnapshot(
			RE::TESObjectREFR* a_owner,
			const RecognizedSnapshot& a_original,
			std::int32_t a_backend,
			std::size_t a_familyIndex,
			const std::vector<std::int32_t>& a_familyCounts);
		bool RestoreSnapshot(RE::TESObjectREFR* a_owner, const RecognizedSnapshot& a_original);
		bool SetCount(RE::TESObjectREFR* a_owner, RE::TESBoundObject* a_form, std::int32_t a_current, std::int32_t a_desired);
		bool SnapshotsEqual(const RecognizedSnapshot& a_left, const RecognizedSnapshot& a_right) const;

		void CountReason(std::string a_reason);
		void LogReasonSummary() const;

		Config _config;
		RE::TESBoundObject* _backend{ nullptr };
		std::vector<ResolvedFamily> _families;
		std::vector<ResolvedRoute> _routes;
		std::unordered_map<RE::FormID, std::uint32_t> _physicalValues;
		std::unordered_set<RE::FormID> _allowedContainerBases;
		std::unordered_set<RE::FormID> _deniedContainerBases;
		std::unordered_set<RE::FormID> _deniedContainerReferences;
		std::unordered_set<RE::FormID> _allowedActorBases;
		std::unordered_set<RE::FormID> _deniedActorBases;
		std::unordered_set<RE::FormID> _deniedActorReferences;
		std::vector<RE::TESQuest*> _disabledQuests;
		std::size_t _fallbackFamily{ 0 };
		std::uint64_t _ledgerFingerprint{ 0 };
		std::size_t _activeFamily{ 0 };
		RE::BGSPerk* _appliedPerk{ nullptr };
		std::uint32_t _priceMenuDepth{ 0 };
		std::atomic_bool _initialized{ false };
		std::atomic_bool _admitted{ false };
		std::atomic_bool _mutating{ false };
		std::atomic_bool _playerTaskQueued{ false };
		std::atomic<std::uint64_t> _admissionGeneration{ 0 };
		mutable std::mutex _pendingLock;
		bool _pendingBackendChanged{ false };
		bool _pendingPhysicalChanged{ false };
		bool _pendingMigration{ false };
		std::size_t _pendingFamily{ 0 };
		LedgerBaseline _playerBaseline;
		bool _playerBaselineValid{ false };
		std::optional<SaveCheckpoint> _loadedCheckpoint;
		mutable std::mutex _reasonLock;
		std::unordered_map<std::string, std::uint64_t> _reasonCounts;
	};
}
