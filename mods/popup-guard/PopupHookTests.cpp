// Host test: installs the production hooks in this process, calls every
// guarded entry point, loads a foreign module that calls MessageBoxW, spawns a
// child that calls FatalAppExitW, and checks timing, absence of windows, and
// the log's attribution. A regression that lets a real dialog through blocks
// on the dialog; CTest's timeout then fails the test.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <string>
#include "PopupGuardCore.h"

namespace {
int checks{};
void Check(bool ok, const char* what) {
    ++checks;
    if (!ok) { std::fprintf(stderr, "FAIL %d: %s\n", checks, what); std::exit(1); }
}

std::string ReadText(const wchar_t* path) {
    std::string text;
    const HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) { return text; }
    char chunk[4096];
    DWORD read{};
    while (ReadFile(file, chunk, sizeof chunk, &read, nullptr) && read) { text.append(chunk, read); }
    CloseHandle(file);
    return text;
}

BOOL CALLBACK CountWindow(HWND, LPARAM parameter) { ++*reinterpret_cast<int*>(parameter); return TRUE; }
int ThreadWindows() {
    int count = 0;
    EnumThreadWindows(GetCurrentThreadId(), CountWindow, reinterpret_cast<LPARAM>(&count));
    return count;
}

template <class Call> void Timed(const char* name, Call&& call) {
    LARGE_INTEGER frequency{}, before{}, after{};
    QueryPerformanceFrequency(&frequency);
    const int windows = ThreadWindows();
    QueryPerformanceCounter(&before);
    const int result = call();
    QueryPerformanceCounter(&after);
    const double ms = static_cast<double>(after.QuadPart - before.QuadPart) * 1000.0 / static_cast<double>(frequency.QuadPart);
    std::printf("%-22s returned %d in %.3f ms\n", name, result, ms);
    Check(result == IDOK, name);
    Check(ms < 50.0, "under 50 ms");
    Check(ThreadWindows() == windows, "no window created");
}

using MessageBoxTimeoutWFn = int(WINAPI*)(HWND, LPCWSTR, LPCWSTR, UINT, WORD, DWORD);
using MessageBoxTimeoutAFn = int(WINAPI*)(HWND, LPCSTR, LPCSTR, UINT, WORD, DWORD);

std::string User32Version() {
    wchar_t path[MAX_PATH]{};
    GetModuleFileNameW(GetModuleHandleW(L"user32.dll"), path, MAX_PATH);
    DWORD handle{};
    const DWORD size = GetFileVersionInfoSizeW(path, &handle);
    std::string block(size, '\0');
    VS_FIXEDFILEINFO* info{};
    UINT length{};
    char text[128] = "unknown";
    if (size && GetFileVersionInfoW(path, 0, size, block.data()) &&
        VerQueryValueW(block.data(), L"\\", reinterpret_cast<void**>(&info), &length) && info) {
        std::snprintf(text, sizeof text, "%u.%u.%u.%u", info->dwFileVersionMS >> 16, info->dwFileVersionMS & 0xFFFF,
            info->dwFileVersionLS >> 16, info->dwFileVersionLS & 0xFFFF);
    }
    return std::string(text);
}

// Empirical funnel probe, run before hooking: reports direct call/jmp edges
// between the MessageBox exports of the user32 actually loaded. Informational;
// the guard hooks every exported entry point regardless of the result.
void ProbeFunnel() {
    const HMODULE user32 = GetModuleHandleW(L"user32.dll");
    const char* names[] = {"MessageBoxA", "MessageBoxW", "MessageBoxExA", "MessageBoxExW",
        "MessageBoxTimeoutA", "MessageBoxTimeoutW", "MessageBoxIndirectA", "MessageBoxIndirectW"};
    const unsigned char* addresses[8]{};
    for (unsigned i = 0; i < 8; ++i) {
        addresses[i] = reinterpret_cast<const unsigned char*>(GetProcAddress(user32, names[i]));
    }
    std::printf("user32.dll %s funnel probe (first 96 bytes of each export):\n", User32Version().c_str());
    for (unsigned s = 0; s < 8; ++s) {
        bool found = false;
        for (std::size_t i = 0; addresses[s] && i + 5 <= 96; ++i) {
            const unsigned char op = addresses[s][i];
            if (op != 0xE8 && op != 0xE9) { continue; }
            std::int32_t rel{};
            std::memcpy(&rel, addresses[s] + i + 1, 4);
            const unsigned char* target = addresses[s] + i + 5 + rel;
            for (unsigned t = 0; t < 8; ++t) {
                if (t != s && target == addresses[t]) {
                    std::printf("  %s +0x%zx %s %s\n", names[s], i, op == 0xE8 ? "call" : "jmp", names[t]);
                    found = true;
                }
            }
        }
        if (!found) { std::printf("  %s: no direct call/jmp to another MessageBox export\n", names[s]); }
    }
}
}

int wmain(int argc, wchar_t** argv) {
    if (argc >= 3 && std::wcscmp(argv[1], L"--fatal-child") == 0) {
        popup_guard::OpenLog(argv[2]);
        popup_guard::Install();
        FatalAppExitW(0, L"fatal body\nsecond line");
        return 99; // Unreachable when the hook terminates the process.
    }
    if (argc < 3) {
        std::fprintf(stderr, "usage: PopupHookTests <log path> <helper dll path>\n");
        return 2;
    }
    const wchar_t* logPath = argv[1];
    const wchar_t* helperPath = argv[2];
    const HMODULE user32 = GetModuleHandleW(L"user32.dll");
    const auto* messageBoxW = reinterpret_cast<const unsigned char*>(GetProcAddress(user32, "MessageBoxW"));
    Check(messageBoxW != nullptr, "MessageBoxW export");
    unsigned char originalBytes[16];
    std::memcpy(originalBytes, messageBoxW, sizeof originalBytes);
    ProbeFunnel();

    Check(popup_guard::OpenLog(logPath), "open log");
    const unsigned active = popup_guard::Install();
    for (unsigned i = 0; i < popup_guard::hookCount; ++i) {
        const auto& hook = popup_guard::Hook(i);
        std::printf("hook %ls!%s: %s\n", hook.module, hook.api, popup_guard::StatusText(hook.status));
    }
    Check(active == popup_guard::hookCount, "all hooks active");
    Check(std::memcmp(originalBytes, messageBoxW, sizeof originalBytes) != 0, "MessageBoxW prologue patched");

    Timed("MessageBoxW", [] { return MessageBoxW(nullptr, L"body line 1\nline \"two\"\tTab\\", L"Caption W", MB_OK | MB_ICONERROR); });
    Timed("MessageBoxA", [] { return MessageBoxA(nullptr, "ansi body", "Caption A", MB_YESNO); });
    Timed("MessageBoxExW", [] { return MessageBoxExW(nullptr, L"ex body", L"Caption ExW", MB_OKCANCEL, 0); });
    Timed("MessageBoxExA", [] { return MessageBoxExA(nullptr, "ex ansi body", "Caption ExA", MB_OK, 0); });
    const auto timeoutW = reinterpret_cast<MessageBoxTimeoutWFn>(GetProcAddress(user32, "MessageBoxTimeoutW"));
    const auto timeoutA = reinterpret_cast<MessageBoxTimeoutAFn>(GetProcAddress(user32, "MessageBoxTimeoutA"));
    Check(timeoutW && timeoutA, "MessageBoxTimeout exports");
    Timed("MessageBoxTimeoutW", [&] { return timeoutW(nullptr, L"timeout body", L"Caption TW", MB_OK, 0, 1000); });
    Timed("MessageBoxTimeoutA", [&] { return timeoutA(nullptr, "timeout ansi body", "Caption TA", MB_OK, 0, 1000); });
    Timed("MessageBoxIndirectW", [] {
        MSGBOXPARAMSW params{};
        params.cbSize = sizeof params;
        params.lpszText = L"indirect body";
        params.lpszCaption = MAKEINTRESOURCEW(5);
        params.dwStyle = MB_OK;
        return MessageBoxIndirectW(&params);
    });
    Timed("MessageBoxIndirectA", [] {
        MSGBOXPARAMSA params{};
        params.cbSize = sizeof params;
        params.lpszText = "indirect ansi body";
        params.lpszCaption = "Caption IA";
        params.dwStyle = MB_OK;
        return MessageBoxIndirectA(&params);
    });

    // Foreign module: hooks are process-wide and attribution names the caller.
    const HMODULE helper = LoadLibraryW(helperPath);
    Check(helper != nullptr, "helper dll loads");
    const auto helperCall = reinterpret_cast<int (*)()>(GetProcAddress(helper, "PopupHelperCall"));
    Check(helperCall != nullptr, "helper export");
    Timed("helper MessageBoxW", [&] { return helperCall(); });

    // FatalAppExitW in a child: logged, then exit code 1 without a dialog.
    std::wstring fatalLog = std::wstring(logPath) + L".fatal.log";
    wchar_t self[MAX_PATH]{};
    GetModuleFileNameW(nullptr, self, MAX_PATH);
    std::wstring commandLine = L"\"" + std::wstring(self) + L"\" --fatal-child \"" + fatalLog + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof startup;
    PROCESS_INFORMATION process{};
    Check(CreateProcessW(nullptr, commandLine.data(), nullptr, nullptr, FALSE, 0, nullptr, nullptr, &startup, &process) != FALSE, "spawn fatal child");
    Check(WaitForSingleObject(process.hProcess, 5000) == WAIT_OBJECT_0, "fatal child exits within 5 s");
    DWORD exitCode{};
    Check(GetExitCodeProcess(process.hProcess, &exitCode) && exitCode == 1, "fatal child exit code 1");
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);

    const std::string log = ReadText(logPath);
    std::printf("--- %ls ---\n%s---\n", logPath, log.c_str());
    const auto has = [&](const char* needle) { return log.find(needle) != std::string::npos; };
    Check(has("PopupGuard 0.1.0 log opened "), "header");
    Check(has("hooks: MessageBoxA=ok MessageBoxW=ok MessageBoxExA=ok MessageBoxExW=ok MessageBoxTimeoutA=ok "
        "MessageBoxTimeoutW=ok MessageBoxIndirectA=ok MessageBoxIndirectW=ok FatalAppExitA=ok FatalAppExitW=ok"), "hook table line");
    Check(has(" MessageBoxW module=PopupHookTests.exe+0x"), "MessageBoxW attributed to this exe");
    Check(has("type=0x10 caption=\"Caption W\" text=\"body line 1\\nline \\\"two\\\"\\tTab\\\\\""), "escaped W text");
    Check(has(" MessageBoxA module=PopupHookTests.exe+0x") && has("type=0x4 caption=\"Caption A\" text=\"ansi body\""), "MessageBoxA line");
    Check(has(" MessageBoxExW module=PopupHookTests.exe+0x") && has("type=0x1 caption=\"Caption ExW\" text=\"ex body\""), "MessageBoxExW line");
    Check(has(" MessageBoxExA module=PopupHookTests.exe+0x") && has("caption=\"Caption ExA\" text=\"ex ansi body\""), "MessageBoxExA line");
    Check(has(" MessageBoxTimeoutW module=PopupHookTests.exe+0x") && has("caption=\"Caption TW\" text=\"timeout body\""), "MessageBoxTimeoutW line");
    Check(has(" MessageBoxTimeoutA module=PopupHookTests.exe+0x") && has("caption=\"Caption TA\" text=\"timeout ansi body\""), "MessageBoxTimeoutA line");
    Check(has(" MessageBoxIndirectW module=PopupHookTests.exe+0x") && has("caption=\"#5\" text=\"indirect body\""), "MessageBoxIndirectW resource caption");
    Check(has(" MessageBoxIndirectA module=PopupHookTests.exe+0x") && has("caption=\"Caption IA\" text=\"indirect ansi body\""), "MessageBoxIndirectA line");
    Check(has(" MessageBoxW module=PopupHelperDll.dll+0x") && has("caption=\"helper caption\" text=\"helper body\""), "helper module attributed");
    Check(!has("\n\n") && log.find("\n ") == std::string::npos, "one record per line");
    const std::string fatal = ReadText(fatalLog.c_str());
    std::printf("--- %ls ---\n%s---\n", fatalLog.c_str(), fatal.c_str());
    Check(fatal.find(" FatalAppExitW module=PopupHookTests.exe+0x") != std::string::npos, "FatalAppExitW attributed");
    Check(fatal.find("type=0x0 caption=\"(null)\" text=\"fatal body\\nsecond line\"") != std::string::npos, "FatalAppExitW text");

    popup_guard::Remove();
    popup_guard::CloseLog();
    Check(!popup_guard::Installed(), "removed");
    Check(std::memcmp(originalBytes, messageBoxW, sizeof originalBytes) == 0, "MessageBoxW prologue restored");
    std::printf("PASS %d hook checks\n", checks);
}
