// VisibleEquipment (working name; the rename anchor is NAME_TBD in CMakeLists.txt).
// M0 scaffold, issue #272.
//
// What this build does: loads on Skyrim SE 1.7.104 through SKSE, writes one log
// file under Documents\My Games\Skyrim Special Edition\SKSE\, registers two
// no-op event sinks (equip, container change) and counts what they see. It
// attaches nothing to any actor and changes no game state. The rule engine in
// SlotRules.h is compiled into the DLL and unit-tested but not wired to the game.
//
// Posture (docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md, "Logging"):
//   * log-only. No MessageBox path exists in this module; SKSE::Init is asked
//     not to install CommonLibSSE-NG's default logger so the only sink is ours.
//   * every engine-called handler catches everything; an exception unwinding
//     into an engine frame is a crash, a logged line is not.
//   * nothing runs in DllMain.

#include "PCH.h"

#include "SlotRules.h"

#include <SimpleIni.h>

namespace
{
	constexpr auto kLogFileName = "VisibleEquipment.log"sv;
	constexpr auto kIniPath = "Data\\SKSE\\Plugins\\VisibleEquipment.ini"sv;

	std::atomic<std::uint64_t> g_equipEvents{ 0 };
	std::atomic<std::uint64_t> g_containerEvents{ 0 };

	// Opens the log next to every other SKSE plugin log. A missing Documents path
	// leaves the plugin silent; it never raises a dialog.
	bool OpenLog()
	{
		auto directory = logger::log_directory();
		if (!directory) {
			return false;
		}
		*directory /= kLogFileName;

		auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(directory->string(), true);
		auto log = std::make_shared<spdlog::logger>("VisibleEquipment", std::move(sink));
		log->set_level(spdlog::level::info);
		// M0 flushes every line: a crash must never eat the evidence of what ran.
		log->flush_on(spdlog::level::trace);
		spdlog::set_default_logger(std::move(log));
		spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] %v");
		return true;
	}

	spdlog::level::level_enum ParseLevel(std::string_view a_value, spdlog::level::level_enum a_fallback)
	{
		if (a_value == "trace"sv) {
			return spdlog::level::trace;
		}
		if (a_value == "debug"sv) {
			return spdlog::level::debug;
		}
		if (a_value == "info"sv) {
			return spdlog::level::info;
		}
		if (a_value == "warn"sv) {
			return spdlog::level::warn;
		}
		if (a_value == "error"sv) {
			return spdlog::level::err;
		}
		if (a_value == "off"sv) {
			return spdlog::level::off;
		}
		return a_fallback;
	}

	// [Log] Level is the only key M0 reads. The file is optional; absent or
	// unreadable means defaults, which is information, not a fault.
	void ApplyIni()
	{
		CSimpleIniA ini;
		ini.SetUnicode();
		if (ini.LoadFile(std::string{ kIniPath }.c_str()) < 0) {
			logger::info("no ini at {}; defaults in effect", kIniPath);
			return;
		}
		const auto level = ParseLevel(ini.GetValue("Log", "Level", "info"), spdlog::level::info);
		spdlog::default_logger()->set_level(level);
		logger::info("loaded {}; log level {}", kIniPath, spdlog::level::to_string_view(level));
	}

	class EquipSink final : public RE::BSTEventSink<RE::TESEquipEvent>
	{
	public:
		static EquipSink* GetSingleton()
		{
			static EquipSink instance;
			return &instance;
		}

		RE::BSEventNotifyControl ProcessEvent(const RE::TESEquipEvent* a_event, RE::BSTEventSource<RE::TESEquipEvent>*) override
		{
			try {
				if (a_event) {
					const auto n = ++g_equipEvents;
					logger::trace("equip event {}: actor {:08X} base {:08X} equipped={}",
						n,
						a_event->actor ? a_event->actor->GetFormID() : 0u,
						a_event->baseObject,
						a_event->equipped);
				}
			} catch (...) {
				logger::error("equip sink threw; swallowed");
			}
			return RE::BSEventNotifyControl::kContinue;
		}

	private:
		EquipSink() = default;
	};

	class ContainerSink final : public RE::BSTEventSink<RE::TESContainerChangedEvent>
	{
	public:
		static ContainerSink* GetSingleton()
		{
			static ContainerSink instance;
			return &instance;
		}

		RE::BSEventNotifyControl ProcessEvent(const RE::TESContainerChangedEvent* a_event, RE::BSTEventSource<RE::TESContainerChangedEvent>*) override
		{
			try {
				if (a_event) {
					const auto n = ++g_containerEvents;
					logger::trace("container event {}: {:08X} -> {:08X} base {:08X} count {}",
						n,
						a_event->oldContainer,
						a_event->newContainer,
						a_event->baseObj,
						a_event->itemCount);
				}
			} catch (...) {
				logger::error("container sink threw; swallowed");
			}
			return RE::BSEventNotifyControl::kContinue;
		}

	private:
		ContainerSink() = default;
	};

	void OnMessage(SKSE::MessagingInterface::Message* a_message)
	{
		if (!a_message) {
			return;
		}
		switch (a_message->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			if (auto* holder = RE::ScriptEventSourceHolder::GetSingleton()) {
				holder->AddEventSink<RE::TESEquipEvent>(EquipSink::GetSingleton());
				holder->AddEventSink<RE::TESContainerChangedEvent>(ContainerSink::GetSingleton());
				logger::info("kDataLoaded: equip and container sinks registered (no-op, counting only)");
			} else {
				logger::error("kDataLoaded: no ScriptEventSourceHolder; sinks not registered");
			}
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
			logger::info("kPostLoadGame: events observed so far equip={} container={}", g_equipEvents.load(), g_containerEvents.load());
			break;
		case SKSE::MessagingInterface::kNewGame:
			logger::info("kNewGame: events observed so far equip={} container={}", g_equipEvents.load(), g_containerEvents.load());
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	// false: do not let CommonLibSSE-NG open its own log; this module owns the file.
	SKSE::Init(a_skse, false);

	const bool logOpen = OpenLog();
	if (logOpen) {
		ApplyIni();
		const auto* declaration = SKSE::PluginDeclaration::GetSingleton();
		logger::info("{} {} loading; runtime {}; declared compatible runtime 1.7.104; M0 scaffold, attaches nothing",
			declaration->GetName(),
			declaration->GetVersion().string(),
			REL::Module::get().version().string());
		logger::info("slot rules: default roster has {} slots", veq::rules::DefaultRoster().size());
	}

	if (const auto* messaging = SKSE::GetMessagingInterface(); messaging && messaging->RegisterListener(OnMessage)) {
		if (logOpen) {
			logger::info("messaging listener registered");
		}
	} else if (logOpen) {
		logger::error("messaging interface unavailable; running with no event sinks");
	}

	return true;
}
