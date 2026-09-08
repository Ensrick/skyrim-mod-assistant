#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <ShlObj.h>
#include <cstddef>
#include <cstdint>
#include <cwchar>
#include "PopupPolicy.h"
#include "PopupGuardCore.h"
using UInt32 = std::uint32_t;
using UInt64 = std::uint64_t;
#include "skse64/PluginAPI.h" // External pinned SDK; never vendored in our package.
static_assert(sizeof(SKSEPluginVersionData) == 0x350);
static_assert(offsetof(SKSEInterface, runtimeVersion) == 4);

// Load-order design (see README): the DLL is named "!PopupGuard.dll" so every
// directory enumeration (NTFS and MO2's virtual listing, which skse64.log shows
// to be name-ordered) yields it first, and it exports SKSEPlugin_Preload so SKSE
// maps it in the preload phase, before any Load-phase plugin's DllMain runs.
// Hooks go in at DLL attach: only kernel32/ntdll calls and MinHook's private
// heap are touched under the loader lock. The Documents log needs shell32, so
// it opens at the first SKSE entry point, on the main thread outside DllMain;
// attach-time lines are buffered until then.

namespace {
constexpr UInt32 runtime = 0x01070680; // Skyrim SE 1.7.104, no game memory access.
bool enabled = true;
bool pinned{};
bool documentsLogOpened{};
unsigned activeHooks{};

bool ReadEnabledFromIni(HMODULE self) noexcept {
    wchar_t path[1024]{};
    const DWORD length = GetModuleFileNameW(self, path, 1024 - 32);
    if (!length || length >= 1024 - 32) { return true; }
    wchar_t* tail = path;
    for (wchar_t* p = path; *p; ++p) {
        if (*p == L'\\' || *p == L'/') { tail = p + 1; }
    }
    if (wcscpy_s(tail, static_cast<std::size_t>(path + 1024 - tail), L"PopupGuard.ini") != 0) { return true; }
    const HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) { return true; } // Missing file keeps the guard on.
    char text[4096];
    DWORD read{};
    const bool ok = ReadFile(file, text, sizeof text, &read, nullptr) != FALSE;
    CloseHandle(file);
    return ok ? popup_guard::ParseEnabled(text, read) : true;
}

void Pin() noexcept {
    // Inline hooks must never outlive their code: once SKSE owns us, FreeLibrary
    // becomes a no-op. Done here rather than in DllMain so a plain LoadLibrary /
    // FreeLibrary pair (the host tests) still unhooks cleanly on detach.
    if (pinned) { return; }
    HMODULE self{};
    pinned = GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&Pin), &self) != FALSE;
    if (!pinned) { popup_guard::Note("module pin failed; hooks stay while loaded"); }
}

void OpenDocumentsLog() noexcept {
    if (documentsLogOpened) { return; }
    PWSTR documents{};
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_Documents, 0, nullptr, &documents))) {
        wchar_t path[32768]{};
        if (swprintf_s(path, L"%s\\My Games\\Skyrim Special Edition\\SKSE\\PopupGuard.log", documents) > 0) {
            documentsLogOpened = popup_guard::OpenLog(path);
        }
        CoTaskMemFree(documents);
    }
}

void NotePhase(const char* phase, const SKSEInterface* skse) noexcept {
    char line[160];
    popup_guard::LineWriter w{line, sizeof line};
    w.Puts(phase);
    w.Puts(" phase; runtime=0x");
    w.PutHex(skse->runtimeVersion);
    w.Puts("; hooks active ");
    w.PutDecimal(activeHooks);
    w.Puts(" of ");
    w.PutDecimal(popup_guard::hookCount);
    w.Puts(enabled ? "" : "; disabled by PopupGuard.ini");
    w.Finish();
    popup_guard::Note(line);
}

bool Enter(const char* phase, const SKSEInterface* skse) noexcept {
    if (!skse || skse->isEditor || skse->runtimeVersion != runtime) { return false; }
    Pin();
    OpenDocumentsLog();
    NotePhase(phase, skse);
    return true;
}
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        // No DisableThreadLibraryCalls: the static CRT needs thread notifications.
        enabled = ReadEnabledFromIni(instance);
        if (!enabled) {
            popup_guard::Note("PopupGuard 0.1.0 disabled by PopupGuard.ini; no hooks installed");
            return TRUE;
        }
        activeHooks = popup_guard::Install();
        popup_guard::Note(activeHooks == popup_guard::hookCount
            ? "PopupGuard 0.1.0 hooks installed at DLL attach"
            : "PopupGuard 0.1.0 hooks only partially installed at DLL attach");
    } else if (reason == DLL_PROCESS_DETACH && !reserved) {
        // Explicit FreeLibrary before any SKSE entry point pinned us (host tests,
        // or SKSE rejecting the plugin): take the hooks out with the code.
        popup_guard::Remove();
        popup_guard::CloseLog();
    }
    return TRUE;
}

extern "C" {
__declspec(dllexport) SKSEPluginVersionData SKSEPlugin_Version = {
    1, 0x00010000, "PopupGuard", "Ensrick", "", 1, 0, {runtime, 0}, 0
};

__declspec(dllexport) bool SKSEPlugin_Preload(const SKSEInterface* skse) noexcept {
    return Enter("preload", skse);
}

__declspec(dllexport) bool SKSEPlugin_Load(const SKSEInterface* skse) noexcept {
    return Enter("load", skse);
}
}
