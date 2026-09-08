// Host test against the real plugin DLL: DllMain installs the hooks (no SKSE
// entry point is called), the opt-out INI installs nothing, the exported
// version data matches the SKSE 1.7.104 gate, and a plain FreeLibrary restores
// user32 before the code goes away.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
using UInt32 = std::uint32_t;
using UInt64 = std::uint64_t;
#include "skse64/PluginAPI.h"

namespace {
int checks{};
void Check(bool ok, const char* what) {
    ++checks;
    if (!ok) { std::fprintf(stderr, "FAIL %d: %s (last error %lu)\n", checks, what, GetLastError()); std::exit(1); }
}
BOOL CALLBACK CountWindow(HWND, LPARAM parameter) { ++*reinterpret_cast<int*>(parameter); return TRUE; }
int ThreadWindows() {
    int count = 0;
    EnumThreadWindows(GetCurrentThreadId(), CountWindow, reinterpret_cast<LPARAM>(&count));
    return count;
}
bool WriteText(const std::wstring& path, const char* text) {
    const HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) { return false; }
    DWORD written{};
    const bool ok = WriteFile(file, text, static_cast<DWORD>(std::strlen(text)), &written, nullptr) != FALSE;
    CloseHandle(file);
    return ok;
}
}

int wmain(int argc, wchar_t** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: PopupPluginLoadTests <plugin dll> <scratch directory>\n");
        return 2;
    }
    const std::wstring plugin = argv[1];
    const std::wstring scratch = argv[2];
    const HMODULE user32 = GetModuleHandleW(L"user32.dll");
    const auto* messageBoxW = reinterpret_cast<const unsigned char*>(GetProcAddress(user32, "MessageBoxW"));
    Check(messageBoxW != nullptr, "MessageBoxW export");
    unsigned char originalBytes[16];
    std::memcpy(originalBytes, messageBoxW, sizeof originalBytes);

    // Opt-out copy: same DLL beside an INI that disables it; nothing is patched.
    CreateDirectoryW(scratch.c_str(), nullptr);
    const std::wstring disabledDll = scratch + L"\\!PopupGuard.dll";
    Check(CopyFileW(plugin.c_str(), disabledDll.c_str(), FALSE) != FALSE, "copy plugin for disabled test");
    Check(WriteText(scratch + L"\\PopupGuard.ini", "[PopupGuard]\r\nEnabled=false\r\n"), "write disabling ini");
    const HMODULE disabled = LoadLibraryW(disabledDll.c_str());
    Check(disabled != nullptr, "disabled copy loads");
    Check(std::memcmp(originalBytes, messageBoxW, sizeof originalBytes) == 0, "disabled copy patches nothing");
    Check(FreeLibrary(disabled) != FALSE, "disabled copy unloads");

    // Real plugin: attach-time hooks, correct version data, clean detach.
    const HMODULE module = LoadLibraryW(plugin.c_str());
    Check(module != nullptr, "plugin loads");
    Check(std::memcmp(originalBytes, messageBoxW, sizeof originalBytes) != 0, "DllMain patched MessageBoxW");
    const auto* version = reinterpret_cast<const SKSEPluginVersionData*>(GetProcAddress(module, "SKSEPlugin_Version"));
    Check(version != nullptr, "SKSEPlugin_Version export");
    Check(version->dataVersion == 1 && std::strcmp(version->name, "PopupGuard") == 0 && std::strcmp(version->author, "Ensrick") == 0, "version data identity");
    Check(version->compatibleVersions[0] == 0x01070680 && version->compatibleVersions[1] == 0, "exact 1.7.104 runtime");
    Check(version->versionIndependence == 0 && version->versionIndependenceEx == 1, "no address library, no struct use");
    Check(GetProcAddress(module, "SKSEPlugin_Preload") != nullptr, "SKSEPlugin_Preload export");
    Check(GetProcAddress(module, "SKSEPlugin_Load") != nullptr, "SKSEPlugin_Load export");
    LARGE_INTEGER frequency{}, before{}, after{};
    QueryPerformanceFrequency(&frequency);
    const int windows = ThreadWindows();
    QueryPerformanceCounter(&before);
    const int result = MessageBoxW(nullptr, L"attach-time body", L"attach-time caption", MB_OK);
    QueryPerformanceCounter(&after);
    const double ms = static_cast<double>(after.QuadPart - before.QuadPart) * 1000.0 / static_cast<double>(frequency.QuadPart);
    std::printf("MessageBoxW through the loaded plugin returned %d in %.3f ms\n", result, ms);
    Check(result == IDOK && ms < 50.0 && ThreadWindows() == windows, "attach-time hook answers IDOK without a window");
    Check(FreeLibrary(module) != FALSE, "plugin unloads");
    Check(std::memcmp(originalBytes, messageBoxW, sizeof originalBytes) == 0, "detach restored MessageBoxW");
    std::printf("PASS %d plugin load checks\n", checks);
}
