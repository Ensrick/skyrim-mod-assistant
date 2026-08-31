#include "PCH.h"

#include "Config.h"
#include "Diagnostics.h"
#include "EncounterManager.h"
#include "Version.h"

namespace
{
	void SetupLogging()
	{
		constexpr std::size_t maxLogBytes = 8U * 1024U * 1024U;
		// spdlog's max_files argument counts rotated archives in addition to
		// the active file: two archives keeps the total footprint to three files.
		constexpr std::size_t retainedLogArchives = 2U;
		auto directory = SKSE::log::log_directory();
		if (!directory) {
			return;
		}
		*directory /= "BoundedEncounters.log";
		try {
			auto sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
				directory->string(), maxLogBytes, retainedLogArchives, true);
			auto log = std::make_shared<spdlog::logger>("BoundedEncounters", std::move(sink));
			log->set_level(spdlog::level::info);
			log->flush_on(spdlog::level::warn);
			spdlog::set_default_logger(std::move(log));
			spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] %v");
		} catch (...) {
			// Logging must never interrupt the desktop or block plugin startup.
		}
	}

	[[nodiscard]] std::filesystem::path ConfigPath()
	{
		std::array<wchar_t, 32768> executablePath{};
		const auto length = REX::W32::GetModuleFileNameW(
			nullptr,
			executablePath.data(),
			static_cast<std::uint32_t>(executablePath.size()));
		if (length == 0 || length >= executablePath.size()) {
			throw std::runtime_error("could not resolve Skyrim executable path");
		}
		return std::filesystem::path(std::wstring_view(executablePath.data(), length)).parent_path() /
			"Data" / "SKSE" / "Plugins" / "BoundedEncounters.json";
	}

	void HandleMessage(SKSE::MessagingInterface::Message* a_message)
	{
		if (!a_message) {
			return;
		}
		auto* manager = BoundedEncounters::EncounterManager::GetSingleton();
		try {
			switch (a_message->type) {
			case SKSE::MessagingInterface::kDataLoaded: {
				auto config = BoundedEncounters::LoadConfig(ConfigPath());
				spdlog::set_level(config.debugLogging ? spdlog::level::debug : spdlog::level::info);
				manager->Initialize(std::move(config));
				manager->Register();
				break;
			}
			case SKSE::MessagingInterface::kPreLoadGame:
				manager->SuspendForLoad();
				break;
			case SKSE::MessagingInterface::kPostLoadGame: {
				const bool loadSucceeded = a_message->data &&
					a_message->dataLen == sizeof(bool) &&
					*static_cast<const bool*>(a_message->data);
				manager->CompleteLoad(loadSucceeded);
				if (loadSucceeded) {
					manager->QueueCurrentCell();
				}
				break;
			}
			case SKSE::MessagingInterface::kNewGame:
				manager->BeginSession("new-game");
				manager->QueueCurrentCell();
				break;
			default:
				break;
			}
		} catch (const std::exception& error) {
			const auto diagnostic = BoundedEncounters::MakeBoundedDiagnostic(error.what());
			logger::critical("message handling failed safely: {}", diagnostic.View());
			manager->Disable();
		} catch (...) {
			logger::critical("message handling failed safely with an unknown exception");
			manager->Disable();
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SetupLogging();
	try {
		const auto skseVersion = REL::Version::unpack(a_skse->SKSEVersion());
		logger::info(
			"{} {} loading on runtime {} with SKSE {}",
			BoundedEncounters::Version::Name,
			BoundedEncounters::Version::Semantic,
			a_skse->RuntimeVersion().string(),
			skseVersion.string());
		if (a_skse->RuntimeVersion() != REL::Version(1, 7, 104, 0)) {
			logger::critical("unsupported Skyrim runtime {}; verified runtime is 1.7.104.0", a_skse->RuntimeVersion().string());
			return false;
		}
		if (skseVersion != REL::Version(2, 3, 1, 0)) {
			logger::critical("unsupported SKSE {}; verified SKSE is 2.3.1.0", skseVersion.string());
			return false;
		}

		// Keep the project-owned file logger. CommonLib's default initialization
		// would replace it and truncate the pre-initialization runtime evidence.
		SKSE::Init(a_skse, false);

		auto* messaging = SKSE::GetMessagingInterface();
		if (!messaging || !messaging->RegisterListener(HandleMessage)) {
			logger::critical("SKSE messaging registration failed");
			return false;
		}
		logger::info("plugin loaded; waiting for DataLoaded");
		return true;
	} catch (const std::exception& error) {
		const auto diagnostic = BoundedEncounters::MakeBoundedDiagnostic(error.what());
		logger::critical("plugin load failed safely: {}", diagnostic.View());
		return false;
	} catch (...) {
		logger::critical("plugin load failed safely with an unknown exception");
		return false;
	}
}
