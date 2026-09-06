#pragma once

// Minimal QuickLoot IE API v20 client declaration.
//
// Derived from QuickLoot IE's public integration header, used under the MIT
// License. Copyright (c) 2018 ryan-rsm-mckenzie. Permission is hereby granted,
// free of charge, to any person obtaining a copy of this software and associated
// documentation files (the "Software"), to deal in the Software without
// restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software,
// subject to inclusion of this notice. THE SOFTWARE IS PROVIDED "AS IS",
// WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

#include <RE/Skyrim.h>

#include <Windows.h>

#include <cstdint>

namespace QuickLoot::API
{
	namespace Events
	{
		enum class HandleResult : std::uint8_t
		{
			kContinue = 0,
			kStop = 1
		};

		struct OpeningLootMenuEvent
		{
			RE::ObjectRefHandle container;
			HandleResult result = HandleResult::kContinue;
		};

		using OpeningLootMenuHandler = void (*)(OpeningLootMenuEvent*);
	}

	enum class ApiVersion
	{
		kV20,
		kV21,
		kLatest = kV21
	};

	class QuickLootAPI
	{
	public:
		QuickLootAPI() = delete;

		static bool Init(const char* a_plugin, const ApiVersion a_minVersion)
		{
			_plugin = a_plugin;
			const auto module = GetModuleHandleA("QuickLootIE");
			if (!module) {
				return false;
			}
			using Getter = InterfaceV20* (*)();
			const auto getter = reinterpret_cast<Getter>(GetProcAddress(module, "GetQuickLootInterfaceV20"));
			_interface = getter ? getter() : nullptr;
			return a_minVersion == ApiVersion::kV20 && _interface != nullptr;
		}

		static void RegisterOpeningLootMenuHandler(const Events::OpeningLootMenuHandler a_handler)
		{
			if (_interface) {
				_interface->RegisterOpeningLootMenuHandler(_plugin, a_handler);
			}
		}

	private:
		struct InterfaceV20
		{
			virtual void DisableLootMenu(const char* a_plugin);
			virtual void EnableLootMenu(const char* a_plugin);
			virtual void RegisterTakingItemHandler(const char* a_plugin, void* a_handler);
			virtual void RegisterTakeItemHandler(const char* a_plugin, void* a_handler);
			virtual void RegisterSelectItemHandler(const char* a_plugin, void* a_handler);
			virtual void RegisterOpeningLootMenuHandler(
				const char* a_plugin,
				Events::OpeningLootMenuHandler a_handler);
		};

		static inline const char* _plugin{ nullptr };
		static inline InterfaceV20* _interface{ nullptr };
	};
}
