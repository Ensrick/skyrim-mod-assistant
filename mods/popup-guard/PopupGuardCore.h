#pragma once
#include <cstddef>

namespace popup_guard {
// Win32 adapter shared by the SKSE plugin and the host tests. Everything here
// is kernel32/ntdll/user32-address work plus MinHook; no shell, COM or CRT
// file I/O, so Install() is safe to run from DllMain under the loader lock.

constexpr unsigned hookCount = 10;
constexpr int hookNotAttempted = -100;

struct HookStatus {
    const wchar_t* module{}; // "user32" / "kernel32"
    const char* api{};       // exported entry point name
    int status{hookNotAttempted}; // MH_STATUS value once attempted
};

// Installs every hook in the table; returns the number that are active.
// Idempotent: a second call returns the current count without touching code.
unsigned Install() noexcept;
// Disables and removes every hook (test teardown only; production pins the DLL).
void Remove() noexcept;
bool Installed() noexcept;
const HookStatus& Hook(unsigned index) noexcept;
const char* StatusText(int status) noexcept;

// Creates/truncates the log file and flushes lines recorded before it existed.
bool OpenLog(const wchar_t* path) noexcept;
void CloseLog() noexcept;
bool LogOpen() noexcept;
// One plain diagnostic line (timestamped). Buffered while the log is closed.
void Note(const char* text) noexcept;
// Formats and records one intercepted call. Exposed for tests.
void Record(const char* api, const void* returnAddress, unsigned type,
    const wchar_t* caption, const wchar_t* text) noexcept;
}
