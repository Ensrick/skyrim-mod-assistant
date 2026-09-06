#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <ShlObj.h>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cwchar>
#include <atomic>
#include <array>
#include "FocusPolicy.h"
#include "ClipLease.h"
using UInt32 = std::uint32_t;
using UInt64 = std::uint64_t;
#include "skse64/PluginAPI.h" // External pinned SDK; never vendored in our package.
static_assert(sizeof(SKSEPluginVersionData) == 0x350);
static_assert(offsetof(SKSEInterface, runtimeVersion) == 4);

namespace {
constexpr UInt32 runtime = 0x01070680; // Skyrim SE 1.7.104, no game memory access.
constexpr wchar_t gameClass[] = L"Skyrim Special Edition";
FILE* logFile{};
unsigned logCount{};
struct LogEntry { const char* text{}; DWORD detail{}; };
std::array<LogEntry, 64> logQueue{};
std::atomic_uint logRead{}, logWrite{};
HANDLE logWake{};
bool asyncLogging{};
HWND gameWindow{};
HMODULE moduleHandle{};
bool shortcutPulse{}; // Hook and timer execute on the same worker message thread.
focus_guard::ClipLease<RECT> clip;
focus_guard::State policy;

void Log(const char* message, DWORD detail = 0) noexcept {
    if (logFile && logCount++ < 256) {
        SYSTEMTIME now{};
        GetLocalTime(&now);
        std::fprintf(logFile, "%02u:%02u:%02u.%03u %s (%lu)\n", now.wHour,
            now.wMinute, now.wSecond, now.wMilliseconds, message, detail);
        std::fflush(logFile);
    }
}

void QueueLog(const char* text, DWORD detail = 0) noexcept {
    // Single producer: the hook/timer thread. Drop rather than block when full.
    if (!asyncLogging) { return; }
    const auto write = logWrite.load(std::memory_order_relaxed);
    if (write - logRead.load(std::memory_order_acquire) >= logQueue.size()) { return; }
    logQueue[write % logQueue.size()] = {text, detail};
    logWrite.store(write + 1, std::memory_order_release);
    SetEvent(logWake);
}

DWORD WINAPI Logger(void*) noexcept {
    for (;;) {
        WaitForSingleObject(logWake, INFINITE);
        auto read = logRead.load(std::memory_order_relaxed);
        while (read != logWrite.load(std::memory_order_acquire)) {
            const auto entry = logQueue[read % logQueue.size()];
            Log(entry.text, entry.detail);
            logRead.store(++read, std::memory_order_release);
        }
    }
}

bool SameRect(const RECT& a, const RECT& b) noexcept {
    return a.left == b.left && a.top == b.top && a.right == b.right && a.bottom == b.bottom;
}

bool ValidGameWindow(HWND window) noexcept {
    if (!window || !IsWindow(window)) { return false; }
    DWORD pid{};
    GetWindowThreadProcessId(window, &pid);
    wchar_t name[128]{};
    return pid == GetCurrentProcessId() && !GetWindow(window, GW_OWNER) &&
        GetClassNameW(window, name, 128) && std::wcscmp(name, gameClass) == 0;
}

bool GameForeground() noexcept {
    return ValidGameWindow(gameWindow) && !IsIconic(gameWindow) &&
        IsWindowVisible(gameWindow) && GetForegroundWindow() == gameWindow;
}

struct Win32ClipApi {
    bool Query(RECT& rect) const noexcept { return GetClipCursor(&rect) != FALSE; }
    bool Equal(const RECT& a, const RECT& b) const noexcept { return SameRect(a, b); }
    bool Foreground() const noexcept { return GameForeground(); }
    bool Release() const noexcept { return ClipCursor(nullptr) != FALSE; }
    bool Confine(const RECT& rect) const noexcept { return ClipCursor(&rect) != FALSE; }
};
Win32ClipApi clipApi;
void ReleaseOwnedClip() noexcept { clip.Release(clipApi); }

bool ClientScreenRect(RECT& area) noexcept {
    if (!gameWindow || !GetClientRect(gameWindow, &area)) { return false; }
    POINT top{area.left, area.top}, bottom{area.right, area.bottom};
    if (!ClientToScreen(gameWindow, &top) || !ClientToScreen(gameWindow, &bottom)) { return false; }
    area = {top.x, top.y, bottom.x, bottom.y};
    return area.right > area.left && area.bottom > area.top;
}

void Confine(const RECT& area) noexcept {
    clip.Confine(clipApi, area);
}

BOOL CALLBACK Discover(HWND window, LPARAM parameter) noexcept {
    DWORD pid{};
    GetWindowThreadProcessId(window, &pid);
    if (pid != GetCurrentProcessId() || GetWindow(window, GW_OWNER)) { return TRUE; }
    wchar_t name[128]{};
    if (GetClassNameW(window, name, 128) && std::wcscmp(name, gameClass) == 0) {
        auto* result = reinterpret_cast<HWND*>(parameter);
        if (*result) { *result = nullptr; return FALSE; } // Ambiguous: fail open.
        *result = window;
    }
    return TRUE;
}

void CALLBACK ForegroundEvent(HWINEVENTHOOK, DWORD, HWND window, LONG, LONG, DWORD, DWORD) noexcept {
    if (window != gameWindow) {
        policy.Step(false, false, false);
        shortcutPulse = false;
        ReleaseOwnedClip();
    }
}

LRESULT CALLBACK KeyboardObserver(int code, WPARAM kind, LPARAM data) noexcept {
    // Observe only desktop escape gestures while OUR window is foreground.
    // No key recording, suppression, injection, focus forcing or cursor warp.
    if (code == HC_ACTION && (kind == WM_KEYDOWN || kind == WM_SYSKEYDOWN) && GameForeground()) {
        const auto* key = reinterpret_cast<const KBDLLHOOKSTRUCT*>(data);
        if (key->vkCode == VK_LWIN || key->vkCode == VK_RWIN ||
            (key->vkCode == VK_TAB && (key->flags & LLKHF_ALTDOWN))) {
            shortcutPulse = true;
            policy.Step(true, true, false);
            ReleaseOwnedClip(); // No file IO or logging in the global keyboard hook.
        }
    }
    return CallNextHookEx(nullptr, code, kind, data);
}

DWORD WINAPI Worker(void*) noexcept {
    MSG message{};
    PeekMessageW(&message, nullptr, WM_USER, WM_USER, PM_NOREMOVE); // Create queue.
    const auto foregroundHook = SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND,
        nullptr, ForegroundEvent, 0, 0, WINEVENT_OUTOFCONTEXT);
    const auto keyHook = SetWindowsHookExW(WH_KEYBOARD_LL, KeyboardObserver, moduleHandle, 0);
    if (!foregroundHook) { QueueLog("foreground hook unavailable; watchdog remains", GetLastError()); }
    if (!keyHook) { QueueLog("key observer unavailable; key-state polling remains", GetLastError()); }
    const auto timer = SetTimer(nullptr, 0, 16, nullptr);
    if (!timer) {
        QueueLog("watchdog unavailable; leaving cursor free", GetLastError());
        if (keyHook) { UnhookWindowsHookEx(keyHook); }
        if (foregroundHook) { UnhookWinEvent(foregroundHook); }
        return 0;
    }
    bool previousLeft = (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0;
    bool previouslyOwned = false;
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        if (message.message == WM_TIMER && message.wParam == timer) {
            if (!ValidGameWindow(gameWindow)) {
                ReleaseOwnedClip();
                gameWindow = nullptr;
                EnumWindows(Discover, reinterpret_cast<LPARAM>(&gameWindow));
                if (gameWindow) { QueueLog("game window discovered"); }
            }
            RECT area{};
            POINT cursor{};
            const bool left = (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0;
            const bool foreground = GameForeground();
            const bool geometry = ClientScreenRect(area);
            const bool freshGameClick = left && !previousLeft && foreground && geometry &&
                GetCursorPos(&cursor) && PtInRect(&area, cursor) &&
                GetAncestor(WindowFromPoint(cursor), GA_ROOT) == gameWindow;
            previousLeft = left;
            const bool shortcut = shortcutPulse || (GetAsyncKeyState(VK_LWIN) & 0x8000) ||
                (GetAsyncKeyState(VK_RWIN) & 0x8000) ||
                ((GetAsyncKeyState(VK_MENU) & 0x8000) && (GetAsyncKeyState(VK_TAB) & 0x8000));
            shortcutPulse = false;
            if (policy.Step(foreground, shortcut, freshGameClick) == focus_guard::Action::confine && geometry) {
                Confine(area);
            } else {
                ReleaseOwnedClip();
            }
            if (clip.owned != previouslyOwned) {
                QueueLog(clip.owned ? "game cursor confined" : "game cursor released or superseded");
                previouslyOwned = clip.owned;
            }
        } else {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }
    ReleaseOwnedClip();
    KillTimer(nullptr, timer);
    if (keyHook) { UnhookWindowsHookEx(keyHook); }
    if (foregroundHook) { UnhookWinEvent(foregroundHook); }
    return 0;
}
}

extern "C" {
__declspec(dllexport) SKSEPluginVersionData SKSEPlugin_Version = {
    1, 0x00010000, "WindowFocusGuard", "Ensrick", "", 1, 0, {runtime, 0}, 0
};

__declspec(dllexport) bool SKSEPlugin_Load(const SKSEInterface* skse) noexcept {
    if (!skse || skse->isEditor || skse->runtimeVersion != runtime) { return false; }
    PWSTR documents{};
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_Documents, 0, nullptr, &documents))) {
        wchar_t path[32768]{};
        if (swprintf_s(path, L"%s\\My Games\\Skyrim Special Edition\\SKSE\\WindowFocusGuard.log", documents) > 0) {
            _wfopen_s(&logFile, path, L"w");
        }
        CoTaskMemFree(documents);
    }
    Log("WindowFocusGuard 0.1.0; foreground-only ownership; exact runtime", skse->runtimeVersion);
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
        reinterpret_cast<LPCWSTR>(&SKSEPlugin_Load), &moduleHandle)) { Log("module pin failed"); return false; }
    logWake = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    if (logWake) {
        const auto loggerThread = CreateThread(nullptr, 0, Logger, nullptr, 0, nullptr);
        asyncLogging = loggerThread != nullptr;
        if (loggerThread) { CloseHandle(loggerThread); }
    }
    const HANDLE thread = CreateThread(nullptr, 0, Worker, nullptr, 0, nullptr);
    if (!thread) { Log("worker creation failed", GetLastError()); return false; }
    CloseHandle(thread);
    return true;
}
}
