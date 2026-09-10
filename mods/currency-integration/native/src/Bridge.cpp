#include "PCH.h"

#include "Bridge.h"
#include "FormLookup.h"
#include "QuestStatePolicy.h"
#include "LedgerFingerprint.h"
#include "SourcePolicy.h"
#include "third_party/QuickLootAPI.h"

namespace Ensrick::Currency
{
	namespace
	{
		template <class T>
		T* ResolveForm(const FormSpec& a_spec, const std::string_view a_context)
		{
			auto* handler = RE::TESDataHandler::GetSingleton();
			auto* form = LookupCompatibleForm<T>(handler, a_spec.localID, a_spec.plugin);
			if (!form) {
				throw std::runtime_error(std::format(
					"{} did not resolve as the required form type: {}", a_context, a_spec.ToString()));
			}
			return form;
		}

		std::optional<std::uint64_t> NonNegative(const std::int32_t a_value)
		{
			return a_value < 0 ? std::nullopt : std::optional<std::uint64_t>(
				static_cast<std::uint64_t>(a_value));
		}

		std::vector<RE::TESNPC*> ActorSafetyBases(RE::Actor* a_actor)
		{
			std::vector<RE::TESNPC*> result;
			std::unordered_set<RE::FormID> visited;
			auto appendChain = [&](RE::TESNPC* a_base) {
				for (auto* current = a_base; current && visited.insert(current->GetFormID()).second;) {
					result.push_back(current);
					auto* parent = current->baseTemplateForm;
					current = parent ? parent->As<RE::TESNPC>() : nullptr;
				}
			};

			if (a_actor) {
				appendChain(a_actor->GetActorBase());
				// Leveled actors expose their selected template through
				// ExtraLeveledCreature, not through GetActorBase(). Inspect both
				// identities so raw template flags cannot hide a protected/vendor
				// ancestor or an explicit deny entry.
				appendChain(a_actor->GetTemplateBase());
			}
			return result;
		}

		class CurrencySwapperCallback final : public RE::BSScript::IStackCallbackFunctor
		{
		public:
			explicit CurrencySwapperCallback(const std::uint64_t a_generation) :
				_generation(a_generation)
			{}

			void operator()(RE::BSScript::Variable a_result) override
			{
				const bool success = a_result.IsBool() && a_result.GetBool();
				Bridge::GetSingleton().OnCurrencySwapperAdmission(_generation, success);
			}

			void SetObject(const RE::BSTSmartPointer<RE::BSScript::Object>&) override {}

		private:
			std::uint64_t _generation;
		};

		void QuickLootOpening(QuickLoot::API::Events::OpeningLootMenuEvent* a_event)
		{
			Bridge::GetSingleton().ProcessQuickLootOpening(a_event);
		}
	}

	Bridge& Bridge::GetSingleton()
	{
		static Bridge singleton;
		return singleton;
	}

	bool Bridge::Initialize(const std::filesystem::path& a_configPath)
	{
		if (_initialized.exchange(true)) {
			return true;
		}

		try {
			_config = LoadConfig(a_configPath);
			if (!ResolveConfiguration() || !InitializeQuickLoot()) {
				_initialized = false;
				return false;
			}
			RegisterEventSinks();
			logger::info(
				"initialized config {} with {} currency families and {} recognized physical forms",
				_config.configID,
				_families.size(),
				_physicalValues.size());
			// Publish only after configuration resolution and sink registration
			// succeed. _initialized is an entry guard, not readiness publication.
			g_publishedAdmissionIdentity.Publish(_ledgerFingerprint);
			return true;
		} catch (const std::exception& error) {
			logger::critical("initialization failed safely: {}", error.what());
			_initialized = false;
			return false;
		} catch (...) {
			logger::critical("initialization failed safely with an unknown exception");
			_initialized = false;
			return false;
		}
	}

	bool Bridge::ResolveConfiguration()
	{
		_backend = ResolveForm<RE::TESBoundObject>(_config.backendForm, "accounting backend");
		auto* vendorNoSale = ResolveForm<RE::BGSKeyword>(
			FormSpec{ .plugin = "Skyrim.esm", .localID = 0x0FF9FB }, "VendorItemNoSale keyword");
		_families.clear();
		_physicalValues.clear();
		_fallbackFamily = std::numeric_limits<std::size_t>::max();

		for (const auto& familyConfig : _config.families) {
			ResolvedFamily family{ .config = familyConfig };
			for (const auto& denomination : familyConfig.denominations) {
				auto* form = ResolveForm<RE::TESBoundObject>(
					denomination.form,
					std::format("{}.{} denomination", familyConfig.id, denomination.tier));
				auto* misc = form->As<RE::TESObjectMISC>();
				if (!misc || !misc->HasKeyword(vendorNoSale) || misc->value != static_cast<std::int32_t>(denomination.value)) {
					throw std::runtime_error(std::format(
						"{}.{} denomination is not a MISC form with the exact configured value and VendorItemNoSale: {}",
						familyConfig.id,
						denomination.tier,
						denomination.form.ToString()));
				}
				if (!_physicalValues.emplace(form->GetFormID(), denomination.value).second) {
					throw std::runtime_error("a physical currency form belongs to more than one family");
				}
				family.denominations.push_back(ResolvedDenomination{
					.value = denomination.value,
					.form = form,
				});
			}
			std::ranges::sort(family.denominations, {}, &ResolvedDenomination::value);
			// Canonical tiers always occupy indices 0/1/2. Input aliases follow
			// them so snapshots and rollback retain every recognized source form,
			// while normalization emits zero of every alias.
			for (const auto& alias : familyConfig.inputAliases) {
				const auto tier = std::ranges::find(familyConfig.denominations, alias.tier, &DenominationConfig::tier);
				if (tier == familyConfig.denominations.end()) {
					throw std::runtime_error("source alias canonical tier did not resolve");
				}
				auto* misc = ResolveForm<RE::TESObjectMISC>(alias.form,
					std::format("{}.{} input alias", familyConfig.id, alias.tier));
				if (!misc->HasKeyword(vendorNoSale) || misc->value != static_cast<std::int32_t>(tier->value) ||
					!_physicalValues.emplace(misc->GetFormID(), tier->value).second) {
					throw std::runtime_error("source alias has a wrong value, lacks VendorItemNoSale, or duplicates a physical form");
				}
				family.denominations.push_back(ResolvedDenomination{
					.value = tier->value,
					.form = misc,
					.isAlias = true,
				});
			}
			if (familyConfig.perk) {
				family.perk = ResolveForm<RE::BGSPerk>(*familyConfig.perk,
					std::format("{} price perk", familyConfig.id));
			}
			if (familyConfig.enabled && familyConfig.fallback) {
				_fallbackFamily = _families.size();
			}
			_families.push_back(std::move(family));
		}

		if (_fallbackFamily == std::numeric_limits<std::size_t>::max()) {
			throw std::runtime_error("no enabled fallback currency family resolved");
		}
		_routes.clear();
		for (const auto& rule : _config.routingRules) {
			ResolvedRoute route{ .id = rule.id };
			for (const auto& keyword : rule.anyKeywords) {
				route.anyKeywords.push_back(ResolveForm<RE::BGSKeyword>(
					keyword, std::format("{} route keyword", rule.id)));
			}
			for (const auto& id : rule.familyIDs) {
				const auto found = std::ranges::find_if(_families, [&](const ResolvedFamily& family) {
					return family.config.id == id && family.config.enabled;
				});
				if (found == _families.end()) {
					throw std::runtime_error(std::format("{} route family did not resolve: {}", rule.id, id));
				}
				route.candidates.push_back(RouteDesignCandidate{
					.familyIndex = static_cast<std::size_t>(std::distance(_families.begin(), found)),
					.familySalt = found->config.salt,
				});
			}
			_routes.push_back(std::move(route));
		}

		auto resolveSet = [](const std::vector<FormSpec>& a_specs, const std::string_view a_context) {
			std::unordered_set<RE::FormID> result;
			for (const auto& spec : a_specs) {
				auto* form = ResolveForm<RE::TESForm>(spec, a_context);
				result.insert(form->GetFormID());
			}
			return result;
		};

		_allowedContainerBases = resolveSet(_config.sources.allowedContainerBases, "allowed container base");
		_deniedContainerBases = resolveSet(_config.sources.deniedContainerBases, "denied container base");
		_deniedContainerReferences = resolveSet(_config.sources.deniedContainerReferences, "denied container reference");
		_allowedActorBases = resolveSet(_config.sources.allowedActorBases, "allowed actor base");
		_deniedActorBases = resolveSet(_config.sources.deniedActorBases, "denied actor base");
		_deniedActorReferences = resolveSet(_config.sources.deniedActorReferences, "denied actor reference");

		_disabledQuests.clear();
		for (const auto& disabled : _config.disabledQuests) {
			auto* quest = ResolveForm<RE::TESQuest>(disabled.quest, "disabled transaction quest");
			const std::string_view actualEditorID = quest->GetFormEditorID() ? quest->GetFormEditorID() : "";
			if (actualEditorID != disabled.editorID) {
				throw std::runtime_error(std::format(
					"disabled quest EditorID mismatch for {}: expected {}, got {}",
					disabled.quest.ToString(), disabled.editorID, actualEditorID));
			}
			_disabledQuests.push_back(quest);
		}
		_ledgerFingerprint = ComputeLedgerFingerprint(_config);
		if (_ledgerFingerprint == 0) {
			throw std::runtime_error("ledger configuration fingerprint is invalid");
		}

		return true;
	}

	void Bridge::RegisterEventSinks()
	{
		auto* scripts = RE::ScriptEventSourceHolder::GetSingleton();
		auto* ui = RE::UI::GetSingleton();
		if (!scripts || !ui) {
			throw std::runtime_error("required Skyrim event sources are unavailable");
		}
		scripts->AddEventSink<RE::TESContainerChangedEvent>(this);
		scripts->AddEventSink<RE::TESDeathEvent>(this);
		scripts->AddEventSink<RE::TESActivateEvent>(this);
		scripts->AddEventSink<RE::TESActorLocationChangeEvent>(this);
		ui->AddEventSink<RE::MenuOpenCloseEvent>(this);
	}

	bool Bridge::InitializeQuickLoot()
	{
		if (!GetModuleHandleA("QuickLootIE")) {
			logger::info("QuickLoot IE is not loaded; vanilla activation/death source paths remain available");
			return true;
		}
		if (!QuickLoot::API::QuickLootAPI::Init(
				"EnsrickCurrencyDenominations", QuickLoot::API::ApiVersion::kV20)) {
			logger::critical("QuickLoot IE is loaded but its required API v20 interface is unavailable");
			return false;
		}
		QuickLoot::API::QuickLootAPI::RegisterOpeningLootMenuHandler(QuickLootOpening);
		logger::info("registered QuickLoot IE v20 pre-display source handler");
		return true;
	}

	void Bridge::BeginGameAdmission(
		const bool a_freshOrKnownNativeSave,
		std::optional<SaveCheckpoint> a_checkpoint)
	{
		if (!_initialized) {
			return;
		}
		const auto generation = ++_admissionGeneration;
		_admitted = false;
		_playerBaselineValid = false;
		_playerTaskQueued = false;
		_loadedCheckpoint = std::move(a_checkpoint);
		_priceMenuDepth = 0;
		ApplyPricePerk(false);
		{
			std::scoped_lock lock(_pendingLock);
			_pendingBackendChanged = false;
			_pendingPhysicalChanged = false;
			_pendingMigration = false;
		}
		if (!a_freshOrKnownNativeSave) {
			logger::critical(
				"admission {} refused: this save predates the native currency ledger; start a new game",
				generation);
			_loadedCheckpoint.reset();
			return;
		}
		if (_loadedCheckpoint && !CheckpointMatchesLedger(*_loadedCheckpoint, _ledgerFingerprint)) {
			logger::critical(
				"admission {} refused: save checkpoint belongs to a different currency ledger configuration",
				generation);
			_loadedCheckpoint.reset();
			return;
		}

		if (!RE::PlayerCharacter::GetSingleton() || !StopConflictingQuests()) {
			logger::critical("admission {} failed before Currency Swapper ownership", generation);
			return;
		}
		if (!RequestCurrencySwapperOwnership(generation)) {
			logger::critical("admission {} Currency Swapper dispatch was rejected", generation);
		}
	}

	bool Bridge::StopConflictingQuests()
	{
		for (auto* quest : _disabledQuests) {
			if (!quest) {
				return false;
			}
			if (quest->IsEnabled()) {
				quest->Stop();
			}
		}
		return true;
	}

	bool Bridge::RequestCurrencySwapperOwnership(const std::uint64_t a_generation)
	{
		auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
		if (!vm || !_backend) {
			return false;
		}
		RE::BSTSmartPointer<RE::BSScript::IStackCallbackFunctor> callback(
			new CurrencySwapperCallback(a_generation));
		auto* arguments = RE::MakeFunctionArguments(static_cast<RE::TESForm*>(_backend));
		return vm->DispatchStaticCall(
			"SEA_BarterFunctions", "SetCurrency", arguments, callback);
	}

	void Bridge::OnCurrencySwapperAdmission(const std::uint64_t a_generation, const bool a_success)
	{
		auto* tasks = SKSE::GetTaskInterface();
		if (!tasks) {
			logger::critical("admission {} callback cannot return to the game thread", a_generation);
			return;
		}
		tasks->AddTask([a_generation, a_success]() {
			if (!a_success) {
				logger::critical("admission {} Currency Swapper callback returned failure", a_generation);
				return;
			}
			Bridge::GetSingleton().CompleteAdmission(a_generation);
		});
	}

	void Bridge::CompleteAdmission(const std::uint64_t a_generation)
	{
		if (a_generation != _admissionGeneration || _admitted || !_initialized) {
			return;
		}
		if (!StopConflictingQuests()) {
			logger::critical("admission {} could not reassert transaction-quest ownership", a_generation);
			return;
		}
		for (const auto* quest : _disabledQuests) {
			if (!IsTransactionQuestQuiescent(quest)) {
				logger::critical("admission {} transaction quest {:08X} is not quiescent (enabled={} stopped={} promoting={})",
					a_generation, quest ? quest->GetFormID() : 0,
					quest && quest->IsEnabled(), quest && quest->IsStopped(), quest && static_cast<bool>(quest->promoteTask));
				return;
			}
		}

		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			logger::critical("admission {} player is unavailable", a_generation);
			return;
		}
		const auto family = DetermineFamily(player->GetCurrentLocation());
		ApplyRoute(family);
		bool migrated = false;
		if (_loadedCheckpoint) {
			const auto checkpoint = *_loadedCheckpoint;
			_loadedCheckpoint.reset();
			_playerBaseline = LedgerBaseline{
				.value = checkpoint.ledgerValue,
				.backend = checkpoint.observedBackend,
				.physical = checkpoint.observedPhysical,
			};
			_playerBaselineValid = true;
			migrated = ReconcileObservedPlayer(family);
		} else {
			migrated = MigratePlayer(family);
		}
		if (!migrated) {
			logger::critical("admission {} failed closed during currency migration", a_generation);
			_playerBaselineValid = false;
			ApplyPricePerk(false);
			return;
		}
		_admitted = true;
		logger::info(
			"admission {} complete: family={} ledger={}",
			a_generation,
			_families[family].config.id,
			_playerBaseline.value);
	}

	void Bridge::Revert()
	{
		++_admissionGeneration;
		_admitted = false;
		_playerBaselineValid = false;
		_loadedCheckpoint.reset();
		_playerTaskQueued = false;
		_priceMenuDepth = 0;
		ApplyPricePerk(false);
		LogReasonSummary();
	}

	std::size_t Bridge::DetermineFamily(
		const RE::BGSLocation* a_location,
		const std::uint64_t a_sourceIdentity) const
	{
		// Ordered, explicit rules cover modern and ancient currencies alike.
		// Only unmatched locations use the fallback. Identity zero gives the
		// player's wallet a stable regional design; sources retain individual
		// deterministic choices across repeated activation/QuickLoot reads.
		for (const auto& route : _routes) {
			if (std::ranges::any_of(route.anyKeywords, [&](const auto* keyword) {
					return LocationHasKeyword(a_location, keyword);
				})) {
				return SelectRouteDesign(route.candidates, a_sourceIdentity).value_or(_fallbackFamily);
			}
		}
		return _fallbackFamily;
	}

	bool Bridge::LocationHasKeyword(
		const RE::BGSLocation* a_location,
		const RE::BGSKeyword* a_keyword) const
	{
		std::unordered_set<const RE::BGSLocation*> visited;
		for (auto* current = a_location; current && visited.insert(current).second; current = current->parentLoc) {
			if (current->HasKeyword(a_keyword)) {
				return true;
			}
		}
		return false;
	}

	void Bridge::ApplyRoute(const std::size_t a_familyIndex)
	{
		if (a_familyIndex >= _families.size() || !_families[a_familyIndex].config.enabled) {
			return;
		}
		ApplyPricePerk(false);
		_activeFamily = a_familyIndex;
		if (auto* named = _backend ? _backend->As<RE::TESFullName>() : nullptr) {
			named->SetFullName(_families[_activeFamily].config.backendLabel.c_str());
		}
		if (_priceMenuDepth > 0) {
			ApplyPricePerk(true);
		}
	}

	void Bridge::ApplyPricePerk(const bool a_enable)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return;
		}
		if (_appliedPerk) {
			player->RemovePerk(_appliedPerk);
			_appliedPerk = nullptr;
		}
		if (a_enable && _activeFamily < _families.size()) {
			if (auto* perk = _families[_activeFamily].perk) {
				player->AddPerk(perk);
				_appliedPerk = perk;
			}
		}
	}

	void Bridge::QueuePlayerBackendSync()
	{
		{
			std::scoped_lock lock(_pendingLock);
			_pendingBackendChanged = true;
		}
		QueuePlayerFlush();
	}

	void Bridge::QueuePlayerPhysicalSync()
	{
		{
			std::scoped_lock lock(_pendingLock);
			_pendingPhysicalChanged = true;
		}
		QueuePlayerFlush();
	}

	void Bridge::QueuePlayerMigration(const std::size_t a_familyIndex)
	{
		{
			std::scoped_lock lock(_pendingLock);
			_pendingMigration = true;
			_pendingFamily = a_familyIndex;
		}
		QueuePlayerFlush();
	}

	void Bridge::QueuePlayerFlush()
	{
		if (!_admitted || _mutating || _playerTaskQueued.exchange(true)) {
			return;
		}
		auto* tasks = SKSE::GetTaskInterface();
		if (!tasks) {
			_playerTaskQueued = false;
			CountReason("player-task-interface-unavailable");
			return;
		}
		const auto generation = _admissionGeneration.load();
		tasks->AddTask([generation]() { Bridge::GetSingleton().FlushPlayerChanges(generation); });
	}

	void Bridge::FlushPlayerChanges(const std::uint64_t a_generation)
	{
		if (a_generation != _admissionGeneration) {
			return;
		}
		_playerTaskQueued = false;
		if (!_admitted || _mutating) {
			return;
		}

		bool migrate = false;
		std::size_t family = _activeFamily;
		{
			std::scoped_lock lock(_pendingLock);
			migrate = _pendingMigration;
			if (migrate) {
				family = _pendingFamily;
			}
			_pendingMigration = false;
			_pendingBackendChanged = false;
			_pendingPhysicalChanged = false;
		}

		if (migrate) {
			ApplyRoute(family);
		}
		if (!_playerBaselineValid || !ReconcileObservedPlayer(family)) {
			CountReason("player-reconcile-failed");
			logger::critical("player reconciliation failed closed; admission suspended");
			_admitted = false;
			ApplyPricePerk(false);
		}
	}

	bool Bridge::MigratePlayer(const std::size_t a_familyIndex)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return false;
		}
		const auto snapshot = ReadSnapshot(player);
		const auto backend = NonNegative(snapshot.backend);
		const auto physical = PhysicalValue(snapshot);
		if (!backend || !physical) {
			return false;
		}
		// This path is new-game-only. Legacy saves are refused before admission,
		// so any recognized physical coins received while the asynchronous
		// Currency Swapper callback was pending are independent starting value,
		// not a stale mirror to discard.
		const auto value = FreshAdmissionValue(*backend, *physical);
		if (!value || *value > static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())) {
			return false;
		}
		const auto desired = DesiredFamilyCounts(a_familyIndex, *value, false);
		if (!desired) {
			return false;
		}
		if (!ApplySnapshot(player, snapshot, static_cast<std::int32_t>(*value), a_familyIndex, *desired)) {
			return false;
		}
		return UpdatePlayerBaseline(*value);
	}

	bool Bridge::ReconcileObservedPlayer(const std::size_t a_familyIndex)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || !_playerBaselineValid) {
			return false;
		}
		const auto snapshot = ReadSnapshot(player);
		const auto backend = NonNegative(snapshot.backend);
		const auto physical = PhysicalValue(snapshot);
		if (!backend || !physical) {
			return false;
		}
		const auto plan = PlanObservedChanges(
			_playerBaseline, *backend, *physical, a_familyIndex, _families.size(), false);
		if (!plan || plan->backend > static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())) {
			return false;
		}
		const auto desired = DesiredFamilyCounts(a_familyIndex, plan->value, false);
		if (!desired || !ApplySnapshot(
				player, snapshot, static_cast<std::int32_t>(plan->backend), a_familyIndex, *desired)) {
			return false;
		}
		return UpdatePlayerBaseline(plan->value);
	}

	bool Bridge::UpdatePlayerBaseline(const std::uint64_t a_value)
	{
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return false;
		}
		const auto snapshot = ReadSnapshot(player);
		const auto backend = NonNegative(snapshot.backend);
		const auto physical = PhysicalValue(snapshot);
		if (!backend || !physical || *backend != a_value || *physical != a_value) {
			return false;
		}
		_playerBaseline = LedgerBaseline{ .value = a_value, .backend = *backend, .physical = *physical };
		_playerBaselineValid = true;
		return true;
	}

	std::optional<SaveCheckpoint> Bridge::PrepareSaveCheckpoint() const
	{
		if (!_admitted || _mutating || !_playerBaselineValid || _activeFamily >= _families.size()) {
			return std::nullopt;
		}
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player) {
			return std::nullopt;
		}
		const auto snapshot = ReadSnapshot(player);
		const auto backend = NonNegative(snapshot.backend);
		const auto physical = PhysicalValue(snapshot);
		if (!backend || !physical) {
			return std::nullopt;
		}
		const auto plan = PlanObservedChanges(
			_playerBaseline, *backend, *physical, _activeFamily, _families.size(), false);
		if (!plan || plan->value > MaximumLedgerValue || *backend > MaximumLedgerValue ||
			*physical > MaximumLedgerValue) {
			return std::nullopt;
		}
		return SaveCheckpoint{
			.ledgerFingerprint = _ledgerFingerprint,
			.ledgerValue = plan->value,
			.observedBackend = *backend,
			.observedPhysical = *physical,
		};
	}

	bool Bridge::ProcessSource(RE::TESObjectREFR* a_source, const char* a_trigger)
	{
		if (!_admitted || _mutating || !a_source) {
			return false;
		}
		const auto kind = ClassifySafeSource(a_source);
		if (!kind) {
			return false;
		}
		const auto* sourceLocation = a_source->GetCurrentLocation();
		const auto* effectiveLocation = sourceLocation ? sourceLocation :
			RE::PlayerCharacter::GetSingleton()->GetCurrentLocation();
		const auto original = ReadSnapshot(a_source);
		const auto backend = NonNegative(original.backend);
		const auto physical = PhysicalValue(original);
		if (!backend || !physical) {
			CountReason("source-invalid-count");
			return false;
		}
		if (*backend > 0 && *physical > 0) {
			CountReason("source-ambiguous-dual-accounting");
			return false;
		}
		const auto value = *backend > 0 ? *backend : *physical;
		if (value == 0) {
			CountReason("source-empty");
			return false;
		}

		const std::uint64_t identity =
			(static_cast<std::uint64_t>(a_source->GetFormID()) << 32) ^
			static_cast<std::uint64_t>(a_source->GetBaseObject()->GetFormID()) ^ _config.seed;
		const auto family = DetermineFamily(effectiveLocation, identity);
		const bool broken = UseBrokenVariant(identity, _families[family].config.salt, _config.variantPercent);
		if (*backend == 0 && SnapshotMatchesFamily(original, family, value, broken)) {
			CountReason(broken ? "source-already-broken" : "source-already-canonical");
			return true;
		}
		const auto desired = DesiredFamilyCounts(family, value, broken);
		if (!desired || value > static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())) {
			CountReason("source-value-out-of-range");
			return false;
		}
		if (!ApplySnapshot(a_source, original, 0, family, *desired)) {
			CountReason("source-apply-failed");
			return false;
		}
		CountReason(*kind == SourceKind::actor ? "source-converted-actor" : "source-converted-container");
		CountReason(std::format("source-trigger-{}", a_trigger));
		return true;
	}

	std::optional<Bridge::SourceKind> Bridge::ClassifySafeSource(RE::TESObjectREFR* a_source)
	{
		if (!a_source || a_source == RE::PlayerCharacter::GetSingleton() || a_source->IsPersistent() ||
			a_source->HasQuestObject() || a_source->extraList.HasQuestObjectAlias()) {
			CountReason("source-reference-safety-rejected");
			return std::nullopt;
		}

		if (auto* actor = a_source->As<RE::Actor>()) {
			const auto safetyBases = ActorSafetyBases(actor);
			const bool protectedBase = std::ranges::any_of(safetyBases, [](const auto* base) {
				return !base || base->IsUnique() || base->IsEssential() || base->IsProtected();
			});
			const bool respawningBase = std::ranges::any_of(safetyBases, [](const auto* base) {
				return base && base->Respawns();
			});
			// Pinned CommonLib's first GetVendorFaction call computes but returns
			// the pre-computation snapshot. The second read observes the runtime
			// result and complements the cycle-safe base/template faction walk.
			(void)actor->GetVendorFaction();
			const bool runtimeVendor = actor->GetVendorFaction() != nullptr;
			if (safetyBases.empty() || !actor->IsDead() || actor->IsPlayerTeammate() ||
				actor->IsEssential() || actor->IsProtected() || protectedBase || !respawningBase ||
				runtimeVendor || HasVendorFaction(safetyBases) ||
				IsDeniedActorReference(a_source, safetyBases)) {
				CountReason("source-actor-safety-rejected");
				return std::nullopt;
			}
			return SourceKind::actor;
		}

		auto* base = a_source->GetBaseObject();
		auto* container = base ? base->As<RE::TESObjectCONT>() : nullptr;
		if (!container || !container->data.flags.all(RE::CONT_DATA::Flag::kRespawn) ||
			a_source->GetOwner() || a_source->GetFactionOwner() ||
			IsDeniedContainerReference(a_source)) {
			CountReason("source-container-safety-rejected");
			return std::nullopt;
		}
		return SourceKind::container;
	}

	bool Bridge::IsDeniedActorReference(
		RE::TESObjectREFR* a_source,
		const std::vector<RE::TESNPC*>& a_safetyBases) const
	{
		if (!a_source || _deniedActorReferences.contains(a_source->GetFormID())) {
			return true;
		}
		if (std::ranges::any_of(a_safetyBases, [&](const auto* base) {
				return !base || _deniedActorBases.contains(base->GetFormID());
			})) {
			return true;
		}
		return !_allowedActorBases.empty() &&
			std::ranges::none_of(a_safetyBases, [&](const auto* base) {
				return base && _allowedActorBases.contains(base->GetFormID());
			});
	}

	bool Bridge::IsDeniedContainerReference(RE::TESObjectREFR* a_source) const
	{
		if (!a_source) {
			return true;
		}
		const auto refID = a_source->GetFormID();
		const auto* base = a_source->GetBaseObject();
		if (!base) {
			return true;
		}
		const auto baseID = base->GetFormID();
		if (_deniedContainerReferences.contains(refID) || _deniedContainerBases.contains(baseID)) {
			return true;
		}
		return !_allowedContainerBases.empty() && !_allowedContainerBases.contains(baseID);
	}

	bool Bridge::HasVendorFaction(const std::vector<RE::TESNPC*>& a_safetyBases) const
	{
		return std::ranges::any_of(a_safetyBases, [](const auto* base) {
			return !base || std::ranges::any_of(base->factions, [](const auto& entry) {
				return entry.faction && entry.faction->IsVendor();
			});
		});
	}

	Bridge::RecognizedSnapshot Bridge::ReadSnapshot(RE::TESObjectREFR* a_owner) const
	{
		RecognizedSnapshot snapshot;
		snapshot.families.resize(_families.size());
		for (std::size_t index = 0; index < _families.size(); ++index) {
			snapshot.families[index].resize(_families[index].denominations.size(), 0);
		}
		if (!a_owner) {
			return snapshot;
		}
		const auto inventory = a_owner->GetInventoryCounts();
		if (const auto found = inventory.find(_backend); found != inventory.end()) {
			snapshot.backend = found->second;
		}
		for (std::size_t family = 0; family < _families.size(); ++family) {
			for (std::size_t tier = 0; tier < _families[family].denominations.size(); ++tier) {
				if (const auto found = inventory.find(_families[family].denominations[tier].form);
					found != inventory.end()) {
					snapshot.families[family][tier] = found->second;
				}
			}
		}
		return snapshot;
	}

	std::optional<std::uint64_t> Bridge::PhysicalValue(const RecognizedSnapshot& a_snapshot) const
	{
		if (a_snapshot.families.size() != _families.size()) {
			return std::nullopt;
		}
		std::uint64_t total = 0;
		for (std::size_t family = 0; family < _families.size(); ++family) {
			if (a_snapshot.families[family].size() != _families[family].denominations.size()) {
				return std::nullopt;
			}
			for (std::size_t tier = 0; tier < _families[family].denominations.size(); ++tier) {
				const auto count = NonNegative(a_snapshot.families[family][tier]);
				const auto value = _families[family].denominations[tier].value;
				if (!count || (value != 0 && *count > std::numeric_limits<std::uint64_t>::max() / value)) {
					return std::nullopt;
				}
				const auto contribution = *count * value;
				if (contribution > std::numeric_limits<std::uint64_t>::max() - total) {
					return std::nullopt;
				}
				total += contribution;
			}
		}
		return total;
	}

	bool Bridge::SnapshotMatchesFamily(
		const RecognizedSnapshot& a_snapshot,
		const std::size_t a_familyIndex,
		const std::uint64_t a_value,
		const bool a_broken) const
	{
		if (a_snapshot.backend != 0 || a_familyIndex >= _families.size()) {
			return false;
		}
		const auto desired = DesiredFamilyCounts(a_familyIndex, a_value, a_broken);
		if (!desired || a_snapshot.families[a_familyIndex] != *desired) {
			return false;
		}
		for (std::size_t index = 0; index < a_snapshot.families.size(); ++index) {
			if (index != a_familyIndex && std::ranges::any_of(a_snapshot.families[index], [](const auto count) {
					return count != 0;
				})) {
				return false;
			}
		}
		return true;
	}

	std::optional<std::vector<std::int32_t>> Bridge::DesiredFamilyCounts(
		const std::size_t a_familyIndex,
		const std::uint64_t a_value,
		const bool a_broken) const
	{
		if (a_familyIndex >= _families.size()) {
			return std::nullopt;
		}
		const auto& denominations = _families[a_familyIndex].denominations;
		if (denominations.size() < 3 || denominations[0].value != 1 ||
			denominations[1].value != 10 || denominations[2].value != 100 ||
			denominations[0].isAlias || denominations[1].isAlias || denominations[2].isAlias ||
			!std::all_of(denominations.begin() + 3, denominations.end(), [](const ResolvedDenomination& entry) {
				return entry.isAlias;
			})) {
			return std::nullopt;
		}
		return CanonicalCountsWithAliases(a_value, a_broken, denominations.size() - 3);
	}

	bool Bridge::ApplySnapshot(
		RE::TESObjectREFR* a_owner,
		const RecognizedSnapshot& a_original,
		const std::int32_t a_backend,
		const std::size_t a_familyIndex,
		const std::vector<std::int32_t>& a_familyCounts)
	{
		if (!a_owner || a_backend < 0 || a_familyIndex >= _families.size() ||
			a_familyCounts.size() != _families[a_familyIndex].denominations.size()) {
			return false;
		}
		if (_mutating.exchange(true)) {
			return false;
		}
		bool success = SetCount(a_owner, _backend, a_original.backend, a_backend);
		for (std::size_t family = 0; success && family < _families.size(); ++family) {
			for (std::size_t tier = 0; success && tier < _families[family].denominations.size(); ++tier) {
				const auto desired = family == a_familyIndex ? a_familyCounts[tier] : 0;
				success = SetCount(
					a_owner,
					_families[family].denominations[tier].form,
					a_original.families[family][tier],
					desired);
			}
		}
		_mutating = false;

		if (success) {
			RecognizedSnapshot expected;
			expected.backend = a_backend;
			expected.families.resize(_families.size());
			for (std::size_t family = 0; family < _families.size(); ++family) {
				expected.families[family].assign(_families[family].denominations.size(), 0);
			}
			expected.families[a_familyIndex] = a_familyCounts;
			success = SnapshotsEqual(ReadSnapshot(a_owner), expected);
		}
		if (!success && !RestoreSnapshot(a_owner, a_original)) {
			logger::critical("currency mutation rollback failed for reference {:08X}; admission suspended",
				a_owner->GetFormID());
			_admitted = false;
			_playerBaselineValid = false;
			ApplyPricePerk(false);
		}
		return success;
	}

	bool Bridge::RestoreSnapshot(RE::TESObjectREFR* a_owner, const RecognizedSnapshot& a_original)
	{
		if (!a_owner || _mutating.exchange(true)) {
			return false;
		}
		auto current = ReadSnapshot(a_owner);
		bool success = SetCount(a_owner, _backend, current.backend, a_original.backend);
		for (std::size_t family = 0; success && family < _families.size(); ++family) {
			for (std::size_t tier = 0; success && tier < _families[family].denominations.size(); ++tier) {
				success = SetCount(
					a_owner,
					_families[family].denominations[tier].form,
					current.families[family][tier],
					a_original.families[family][tier]);
			}
		}
		_mutating = false;
		return success && SnapshotsEqual(ReadSnapshot(a_owner), a_original);
	}

	bool Bridge::SetCount(
		RE::TESObjectREFR* a_owner,
		RE::TESBoundObject* a_form,
		const std::int32_t a_current,
		const std::int32_t a_desired)
	{
		if (!a_owner || !a_form || a_current < 0 || a_desired < 0) {
			return false;
		}
		if (a_desired < a_current) {
			a_owner->RemoveItem(
				a_form,
				a_current - a_desired,
				RE::ITEM_REMOVE_REASON::kRemove,
				nullptr,
				nullptr);
		} else if (a_desired > a_current) {
			a_owner->AddObjectToContainer(a_form, nullptr, a_desired - a_current, nullptr);
		}
		return true;
	}

	bool Bridge::SnapshotsEqual(
		const RecognizedSnapshot& a_left,
		const RecognizedSnapshot& a_right) const
	{
		return a_left.backend == a_right.backend && a_left.families == a_right.families;
	}

	void Bridge::ProcessQuickLootOpening(QuickLoot::API::Events::OpeningLootMenuEvent* a_event)
	{
		if (!a_event) {
			return;
		}
		auto source = a_event->container.get();
		ProcessSource(source.get(), "quickloot-open");
	}

	RE::BSEventNotifyControl Bridge::ProcessEvent(
		const RE::TESContainerChangedEvent* a_event,
		RE::BSTEventSource<RE::TESContainerChangedEvent>*)
	{
		if (!_admitted || _mutating || !a_event || a_event->itemCount == 0) {
			return RE::BSEventNotifyControl::kContinue;
		}
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player || (a_event->oldContainer != player->GetFormID() &&
			a_event->newContainer != player->GetFormID())) {
			return RE::BSEventNotifyControl::kContinue;
		}
		if (a_event->baseObj == _backend->GetFormID()) {
			QueuePlayerBackendSync();
		} else if (_physicalValues.contains(a_event->baseObj)) {
			QueuePlayerPhysicalSync();
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	RE::BSEventNotifyControl Bridge::ProcessEvent(
		const RE::TESDeathEvent* a_event,
		RE::BSTEventSource<RE::TESDeathEvent>*)
	{
		if (_admitted && a_event && a_event->dead) {
			ProcessSource(a_event->actorDying.get(), "death");
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	RE::BSEventNotifyControl Bridge::ProcessEvent(
		const RE::TESActivateEvent* a_event,
		RE::BSTEventSource<RE::TESActivateEvent>*)
	{
		if (_admitted && a_event && a_event->actionRef.get() == RE::PlayerCharacter::GetSingleton()) {
			ProcessSource(a_event->objectActivated.get(), "activate");
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	RE::BSEventNotifyControl Bridge::ProcessEvent(
		const RE::TESActorLocationChangeEvent* a_event,
		RE::BSTEventSource<RE::TESActorLocationChangeEvent>*)
	{
		if (_admitted && a_event && a_event->actor.get() == RE::PlayerCharacter::GetSingleton()) {
			QueuePlayerMigration(DetermineFamily(a_event->newLoc));
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	RE::BSEventNotifyControl Bridge::ProcessEvent(
		const RE::MenuOpenCloseEvent* a_event,
		RE::BSTEventSource<RE::MenuOpenCloseEvent>*)
	{
		if (!_admitted || !a_event) {
			return RE::BSEventNotifyControl::kContinue;
		}
		const bool priceMenu =
			a_event->menuName == RE::DialogueMenu::MENU_NAME ||
			a_event->menuName == RE::BarterMenu::MENU_NAME ||
			a_event->menuName == RE::CraftingMenu::MENU_NAME;
		if (!priceMenu) {
			return RE::BSEventNotifyControl::kContinue;
		}
		if (a_event->opening) {
			if (_priceMenuDepth++ == 0) {
				ApplyPricePerk(true);
			}
		} else {
			if (_priceMenuDepth > 0 && --_priceMenuDepth == 0) {
				ApplyPricePerk(false);
			}
		}
		return RE::BSEventNotifyControl::kContinue;
	}

	void Bridge::CountReason(std::string a_reason)
	{
		std::scoped_lock lock(_reasonLock);
		++_reasonCounts[std::move(a_reason)];
	}

	void Bridge::LogReasonSummary() const
	{
		std::scoped_lock lock(_reasonLock);
		for (const auto& [reason, count] : _reasonCounts) {
			logger::info("reason {}={}", reason, count);
		}
	}
}
