#include "PCH.h"

#include "Bridge.h"
#include "MessagePolicy.h"
#include "SaveMarkerPolicy.h"

namespace
{
	std::optional<Ensrick::Currency::SaveCheckpoint> g_loadedCheckpoint;
	bool g_checkpointInvalid{ false };

	void SetupLogging()
	{
		auto directory = SKSE::log::log_directory();
		if (!directory) {
			return;
		}
		*directory /= "EnsrickCurrencyDenominations.log";
		try {
			auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(directory->string(), true);
			auto log = std::make_shared<spdlog::logger>("EnsrickCurrencyDenominations", std::move(sink));
			log->set_level(spdlog::level::info);
			log->flush_on(spdlog::level::info);
			spdlog::set_default_logger(std::move(log));
			spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] %v");
		} catch (...) {
			// Logging must not show a modal dialog or block Skyrim startup.
		}
	}

	std::filesystem::path ConfigPath()
	{
		std::array<wchar_t, 32768> executablePath{};
		const auto length = REX::W32::GetModuleFileNameW(
			nullptr, executablePath.data(), static_cast<std::uint32_t>(executablePath.size()));
		if (length == 0 || length >= executablePath.size()) {
			throw std::runtime_error("could not resolve Skyrim executable path");
		}
		return std::filesystem::path(std::wstring_view(executablePath.data(), length)).parent_path() /
			"Data" / "SKSE" / "Plugins" / "EnsrickCurrencyDenominations.json";
	}

	void HandleMessage(SKSE::MessagingInterface::Message* a_message)
	{
		if (!a_message) {
			return;
		}
		auto& bridge = Ensrick::Currency::Bridge::GetSingleton();
		try {
			switch (a_message->type) {
			case SKSE::MessagingInterface::kDataLoaded:
				if (!bridge.Initialize(ConfigPath())) {
					logger::critical("currency bridge remains inactive because initialization failed");
				}
				break;
			case SKSE::MessagingInterface::kPreLoadGame:
				g_loadedCheckpoint.reset();
				g_checkpointInvalid = false;
				bridge.Revert();
				break;
			case SKSE::MessagingInterface::kPostLoadGame: {
				const bool loaded = Ensrick::Currency::PostLoadSucceeded(a_message->data, a_message->dataLen);
				if (loaded) {
					auto checkpoint = std::move(g_loadedCheckpoint);
					g_loadedCheckpoint.reset();
					bridge.BeginGameAdmission(
						!g_checkpointInvalid && checkpoint.has_value(), std::move(checkpoint));
				} else {
					g_loadedCheckpoint.reset();
				}
				g_checkpointInvalid = false;
				break;
			}
			case SKSE::MessagingInterface::kNewGame:
				g_loadedCheckpoint.reset();
				g_checkpointInvalid = false;
				bridge.BeginGameAdmission(true);
				break;
			default:
				break;
			}
		} catch (const std::exception& error) {
			logger::critical("message handling failed safely: {}", error.what());
			bridge.Revert();
		} catch (...) {
			logger::critical("message handling failed safely with an unknown exception");
			bridge.Revert();
		}
	}

	void SaveCallback(SKSE::SerializationInterface* a_interface)
	{
		if (!a_interface || !Ensrick::Currency::Bridge::GetSingleton().IsAdmitted()) {
			return;
		}
		const auto checkpoint = Ensrick::Currency::Bridge::GetSingleton().PrepareSaveCheckpoint();
		if (!checkpoint) {
			logger::error("refused to mark save because a consistent currency checkpoint could not be computed");
			return;
		}
		if (!a_interface->WriteRecord(
				Ensrick::Currency::SaveRecordType,
				Ensrick::Currency::SaveRecordVersion,
				*checkpoint)) {
			logger::error("failed to write native currency save checkpoint");
		}
	}

	void LoadCallback(SKSE::SerializationInterface* a_interface)
	{
		g_loadedCheckpoint.reset();
		g_checkpointInvalid = false;
		if (!a_interface) {
			return;
		}
		std::uint32_t type = 0;
		std::uint32_t version = 0;
		std::uint32_t length = 0;
		while (a_interface->GetNextRecordInfo(type, version, length)) {
			if (type != Ensrick::Currency::SaveRecordType) {
				continue;
			}
			if (g_loadedCheckpoint || g_checkpointInvalid) {
				logger::error("rejected duplicate native currency save checkpoint");
				g_checkpointInvalid = true;
				g_loadedCheckpoint.reset();
				continue;
			}
			if (length != sizeof(Ensrick::Currency::SaveCheckpoint)) {
				logger::error("rejected malformed native currency save checkpoint length {}", length);
				g_checkpointInvalid = true;
				continue;
			}
			Ensrick::Currency::SaveCheckpoint checkpoint{};
			if (a_interface->ReadRecordData(checkpoint) != sizeof(checkpoint) ||
				!Ensrick::Currency::IsRecognizedNativeSaveCheckpoint(type, version, length, checkpoint)) {
				logger::error("rejected unrecognized native currency save checkpoint");
				g_checkpointInvalid = true;
				continue;
			}
			g_loadedCheckpoint = checkpoint;
		}
	}

	void RevertCallback(SKSE::SerializationInterface*)
	{
		g_loadedCheckpoint.reset();
		g_checkpointInvalid = false;
		Ensrick::Currency::Bridge::GetSingleton().Revert();
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SetupLogging();
	try {
		const auto skseVersion = REL::Version::unpack(a_skse->SKSEVersion());
		logger::info(
			"Ensrick Currency Denominations {} loading on runtime {} with SKSE {}",
			ENSRICK_CURRENCY_VERSION,
			a_skse->RuntimeVersion().string(),
			skseVersion.string());
		if (a_skse->RuntimeVersion() != REL::Version(1, 7, 104, 0)) {
			logger::critical("unsupported Skyrim runtime {}; verified runtime is 1.7.104.0",
				a_skse->RuntimeVersion().string());
			return false;
		}
		if (skseVersion != REL::Version(2, 3, 1, 0)) {
			logger::critical("unsupported SKSE {}; verified SKSE is 2.3.1.0", skseVersion.string());
			return false;
		}
		SKSE::Init(a_skse, false);
		auto* messaging = SKSE::GetMessagingInterface();
		if (!messaging || !messaging->RegisterListener(HandleMessage)) {
			logger::critical("SKSE messaging registration failed");
			return false;
		}
		auto* serialization = SKSE::GetSerializationInterface();
		if (!serialization) {
			logger::critical("SKSE serialization interface is unavailable");
			return false;
		}
		serialization->SetUniqueID(Ensrick::Currency::SerializationID);
		serialization->SetSaveCallback(SaveCallback);
		serialization->SetLoadCallback(LoadCallback);
		serialization->SetRevertCallback(RevertCallback);
		logger::info("plugin loaded; waiting for DataLoaded");
		return true;
	} catch (const std::exception& error) {
		logger::critical("plugin load failed safely: {}", error.what());
		return false;
	} catch (...) {
		logger::critical("plugin load failed safely with an unknown exception");
		return false;
	}
}
