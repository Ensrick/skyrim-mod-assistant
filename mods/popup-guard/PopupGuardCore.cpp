#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <intrin.h>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <MinHook.h>
#include "PopupPolicy.h"
#include "PopupGuardCore.h"

namespace {
using namespace popup_guard;

// Static import anchor: guarantees user32 is mapped before this module's
// DllMain runs (MinHook resolves the targets with GetProcAddress, which would
// otherwise leave the linker free to drop the import).
volatile const void* const user32Anchor = reinterpret_cast<const void*>(&MessageBoxW);

// ---- logging: one SRW lock, one WriteFile per line, bounded pre-open buffer.
SRWLOCK logLock = SRWLOCK_INIT;
HANDLE logFile = INVALID_HANDLE_VALUE;
LineBudget budget;
bool budgetNoted{};
constexpr unsigned pendingCapacity = 16;
constexpr std::size_t pendingBytes = 512;
char pending[pendingCapacity][pendingBytes];
unsigned pendingCount{};
__declspec(thread) bool insideRecord{}; // Belt and braces: recursion is impossible by construction.

void Stamp(char (&out)[32], bool withDate) noexcept {
    SYSTEMTIME now{};
    GetLocalTime(&now);
    LineWriter w{out, sizeof out};
    if (withDate) {
        w.PutDecimal(now.wYear, 4); w.Put('-'); w.PutDecimal(now.wMonth, 2); w.Put('-');
        w.PutDecimal(now.wDay, 2); w.Put(' ');
    }
    w.PutDecimal(now.wHour, 2); w.Put(':'); w.PutDecimal(now.wMinute, 2); w.Put(':');
    w.PutDecimal(now.wSecond, 2); w.Put('.'); w.PutDecimal(now.wMilliseconds, 3);
    w.Finish();
}

void WriteLocked(const char* line, std::size_t length) noexcept {
    // Caller holds logLock. The handle is unbuffered, so the line is handed to
    // the OS before the hook returns; a following TerminateProcess keeps it.
    DWORD written{};
    WriteFile(logFile, line, static_cast<DWORD>(length), &written, nullptr);
    WriteFile(logFile, "\r\n", 2, &written, nullptr);
}

void Emit(const char* line, std::size_t length) noexcept {
    AcquireSRWLockExclusive(&logLock);
    if (logFile != INVALID_HANDLE_VALUE) {
        if (budget.Take()) {
            WriteLocked(line, length);
        } else if (!budgetNoted) {
            budgetNoted = true;
            const char message[] = "line budget exhausted; further calls are suppressed without logging";
            WriteLocked(message, sizeof message - 1);
        }
    } else if (pendingCount < pendingCapacity) {
        const std::size_t n = length < pendingBytes - 1 ? length : pendingBytes - 1;
        std::memcpy(pending[pendingCount], line, n);
        pending[pendingCount][n] = '\0';
        ++pendingCount;
    }
    ReleaseSRWLockExclusive(&logLock);
}

void DescribeCaller(const void* returnAddress, char (&name)[128], unsigned long long& offset) noexcept {
    void* base{};
    RtlPcToFileHeader(const_cast<void*>(returnAddress), &base);
    name[0] = '?';
    name[1] = '\0';
    if (!base) {
        offset = reinterpret_cast<std::uintptr_t>(returnAddress);
        return;
    }
    offset = reinterpret_cast<std::uintptr_t>(returnAddress) - reinterpret_cast<std::uintptr_t>(base);
    wchar_t path[MAX_PATH + 1]{};
    if (!GetModuleFileNameW(static_cast<HMODULE>(base), path, MAX_PATH)) { return; }
    const wchar_t* tail = path;
    for (const wchar_t* p = path; *p; ++p) {
        if (*p == L'\\' || *p == L'/') { tail = p + 1; }
    }
    if (!WideCharToMultiByte(CP_UTF8, 0, tail, -1, name, sizeof name, nullptr, nullptr)) {
        name[0] = '?';
        name[1] = '\0';
    }
}

// Bounded UTF-16 to UTF-8; scans at most `maxChars` so unterminated input is safe.
const char* Utf8FromWide(const wchar_t* s, char* out, std::size_t capacity, std::size_t maxChars) noexcept {
    if (!s) { return nullptr; }
    const std::size_t length = wcsnlen(s, maxChars);
    if (length == 0) { out[0] = '\0'; return out; }
    const int n = WideCharToMultiByte(CP_UTF8, 0, s, static_cast<int>(length), out,
        static_cast<int>(capacity - 1), nullptr, nullptr);
    if (n <= 0) {
        const char failed[] = "(conversion failed)";
        std::memcpy(out, failed, sizeof failed);
        return out;
    }
    out[n] = '\0';
    return out;
}

const wchar_t* WideFromAnsi(const char* s, wchar_t* out, std::size_t capacity) noexcept {
    if (!s) { return nullptr; }
    const std::size_t length = strnlen(s, capacity - 1);
    if (length == 0) { out[0] = L'\0'; return out; }
    const int n = MultiByteToWideChar(CP_ACP, 0, s, static_cast<int>(length), out, static_cast<int>(capacity - 1));
    out[n > 0 ? n : 0] = L'\0';
    return out;
}

const wchar_t* ResourceOrString(const wchar_t* s, wchar_t (&scratch)[16]) noexcept {
    if (!s || !IS_INTRESOURCE(s)) { return s; }
    char digits[16];
    LineWriter w{digits, sizeof digits};
    w.Put('#');
    w.PutDecimal(reinterpret_cast<std::uintptr_t>(s) & 0xFFFF);
    w.Finish();
    for (std::size_t i = 0; i < sizeof scratch / sizeof scratch[0]; ++i) {
        scratch[i] = static_cast<wchar_t>(digits[i]);
        if (!digits[i]) { break; }
    }
    return scratch;
}

void RecordAnsi(const char* api, const void* returnAddress, unsigned type, const char* caption, const char* text) noexcept {
    wchar_t captionWide[512];
    wchar_t textWide[3072];
    Record(api, returnAddress, type, WideFromAnsi(caption, captionWide, 512), WideFromAnsi(text, textWide, 3072));
}

// ---- detours: never call the original, never show UI, return IDOK at once.
int WINAPI HookMessageBoxA(HWND, LPCSTR text, LPCSTR caption, UINT type) noexcept {
    RecordAnsi("MessageBoxA", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxW(HWND, LPCWSTR text, LPCWSTR caption, UINT type) noexcept {
    Record("MessageBoxW", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxExA(HWND, LPCSTR text, LPCSTR caption, UINT type, WORD) noexcept {
    RecordAnsi("MessageBoxExA", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxExW(HWND, LPCWSTR text, LPCWSTR caption, UINT type, WORD) noexcept {
    Record("MessageBoxExW", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxTimeoutA(HWND, LPCSTR text, LPCSTR caption, UINT type, WORD, DWORD) noexcept {
    RecordAnsi("MessageBoxTimeoutA", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxTimeoutW(HWND, LPCWSTR text, LPCWSTR caption, UINT type, WORD, DWORD) noexcept {
    Record("MessageBoxTimeoutW", _ReturnAddress(), type, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxIndirectA(const MSGBOXPARAMSA* params) noexcept {
    if (!params) { Record("MessageBoxIndirectA", _ReturnAddress(), 0, nullptr, nullptr); return IDOK; }
    const char* text = IS_INTRESOURCE(params->lpszText) ? nullptr : params->lpszText;
    const char* caption = IS_INTRESOURCE(params->lpszCaption) ? nullptr : params->lpszCaption;
    RecordAnsi("MessageBoxIndirectA", _ReturnAddress(), params->dwStyle, caption, text);
    return IDOK;
}
int WINAPI HookMessageBoxIndirectW(const MSGBOXPARAMSW* params) noexcept {
    if (!params) { Record("MessageBoxIndirectW", _ReturnAddress(), 0, nullptr, nullptr); return IDOK; }
    wchar_t captionScratch[16]{}, textScratch[16]{};
    Record("MessageBoxIndirectW", _ReturnAddress(), params->dwStyle,
        ResourceOrString(params->lpszCaption, captionScratch), ResourceOrString(params->lpszText, textScratch));
    return IDOK;
}
void WINAPI HookFatalAppExitA(UINT action, LPCSTR text) noexcept {
    RecordAnsi("FatalAppExitA", _ReturnAddress(), action, nullptr, text);
    TerminateProcess(GetCurrentProcess(), 1);
}
void WINAPI HookFatalAppExitW(UINT action, LPCWSTR text) noexcept {
    Record("FatalAppExitW", _ReturnAddress(), action, nullptr, text);
    TerminateProcess(GetCurrentProcess(), 1);
}

struct Entry {
    HookStatus status;
    LPVOID detour;
    LPVOID original;
    LPVOID target;
};
Entry entries[hookCount] = {
    {{L"user32", "MessageBoxA"}, reinterpret_cast<LPVOID>(&HookMessageBoxA), nullptr, nullptr},
    {{L"user32", "MessageBoxW"}, reinterpret_cast<LPVOID>(&HookMessageBoxW), nullptr, nullptr},
    {{L"user32", "MessageBoxExA"}, reinterpret_cast<LPVOID>(&HookMessageBoxExA), nullptr, nullptr},
    {{L"user32", "MessageBoxExW"}, reinterpret_cast<LPVOID>(&HookMessageBoxExW), nullptr, nullptr},
    {{L"user32", "MessageBoxTimeoutA"}, reinterpret_cast<LPVOID>(&HookMessageBoxTimeoutA), nullptr, nullptr},
    {{L"user32", "MessageBoxTimeoutW"}, reinterpret_cast<LPVOID>(&HookMessageBoxTimeoutW), nullptr, nullptr},
    {{L"user32", "MessageBoxIndirectA"}, reinterpret_cast<LPVOID>(&HookMessageBoxIndirectA), nullptr, nullptr},
    {{L"user32", "MessageBoxIndirectW"}, reinterpret_cast<LPVOID>(&HookMessageBoxIndirectW), nullptr, nullptr},
    {{L"kernel32", "FatalAppExitA"}, reinterpret_cast<LPVOID>(&HookFatalAppExitA), nullptr, nullptr},
    {{L"kernel32", "FatalAppExitW"}, reinterpret_cast<LPVOID>(&HookFatalAppExitW), nullptr, nullptr},
};
bool installed{};
bool ownsMinHook{};
unsigned active{};

void NoteHookTable() noexcept {
    char line[1024];
    LineWriter w{line, sizeof line};
    w.Puts("hooks:");
    for (const Entry& e : entries) {
        w.Put(' ');
        w.Puts(e.status.api);
        w.Put('=');
        w.Puts(StatusText(e.status.status));
    }
    w.Finish();
    Note(line);
}
}

namespace popup_guard {
const char* StatusText(int status) noexcept {
    if (status == hookNotAttempted) { return "not-attempted"; }
    if (status == MH_OK) { return "ok"; }
    return MH_StatusToString(static_cast<MH_STATUS>(status));
}

unsigned Install() noexcept {
    if (installed) { return active; }
    installed = true;
    const MH_STATUS init = MH_Initialize();
    if (init != MH_OK && init != MH_ERROR_ALREADY_INITIALIZED) {
        Note("MinHook initialisation failed; no hooks installed");
        Note(MH_StatusToString(init));
        return 0;
    }
    ownsMinHook = init == MH_OK;
    bool queued = false;
    for (Entry& e : entries) {
        e.status.status = MH_CreateHookApiEx(e.status.module, e.status.api, e.detour, &e.original, &e.target);
        if (e.status.status == MH_OK) {
            e.status.status = MH_QueueEnableHook(e.target);
            queued = queued || e.status.status == MH_OK;
        }
    }
    if (queued) {
        const MH_STATUS applied = MH_ApplyQueued(); // One thread freeze for the whole table.
        if (applied != MH_OK) {
            for (Entry& e : entries) {
                if (e.status.status == MH_OK) { e.status.status = applied; }
            }
        }
    }
    active = 0;
    for (const Entry& e : entries) {
        if (e.status.status == MH_OK) { ++active; }
    }
    NoteHookTable();
    return active;
}

void Remove() noexcept {
    if (!installed) { return; }
    MH_DisableHook(MH_ALL_HOOKS);
    if (ownsMinHook) { MH_Uninitialize(); }
    for (Entry& e : entries) {
        e.status.status = hookNotAttempted;
        e.original = nullptr;
        e.target = nullptr;
    }
    installed = false;
    ownsMinHook = false;
    active = 0;
}

bool Installed() noexcept { return installed; }

const HookStatus& Hook(unsigned index) noexcept {
    return entries[index < hookCount ? index : hookCount - 1].status;
}

bool OpenLog(const wchar_t* path) noexcept {
    if (!path) { return false; }
    const HANDLE file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) { return false; }
    AcquireSRWLockExclusive(&logLock);
    if (logFile != INVALID_HANDLE_VALUE) { CloseHandle(logFile); }
    logFile = file;
    budget = LineBudget{};
    budgetNoted = false;
    char header[160];
    {
        char stamp[32];
        Stamp(stamp, true);
        LineWriter w{header, sizeof header};
        w.Puts("PopupGuard 0.1.0 log opened ");
        w.Puts(stamp);
        w.Puts(" pid=");
        w.PutDecimal(GetCurrentProcessId());
        w.Finish();
        if (budget.Take()) { WriteLocked(header, w.length); }
    }
    for (unsigned i = 0; i < pendingCount; ++i) {
        if (budget.Take()) { WriteLocked(pending[i], strnlen(pending[i], pendingBytes)); }
    }
    pendingCount = 0;
    ReleaseSRWLockExclusive(&logLock);
    return true;
}

void CloseLog() noexcept {
    AcquireSRWLockExclusive(&logLock);
    if (logFile != INVALID_HANDLE_VALUE) { CloseHandle(logFile); }
    logFile = INVALID_HANDLE_VALUE;
    ReleaseSRWLockExclusive(&logLock);
}

bool LogOpen() noexcept {
    AcquireSRWLockShared(&logLock);
    const bool open = logFile != INVALID_HANDLE_VALUE;
    ReleaseSRWLockShared(&logLock);
    return open;
}

void Note(const char* text) noexcept {
    char stamp[32];
    Stamp(stamp, false);
    char line[512];
    LineWriter w{line, sizeof line};
    w.Puts(stamp);
    w.Put(' ');
    w.Puts(text ? text : "(null)");
    w.Finish();
    Emit(line, w.length);
}

void Record(const char* api, const void* returnAddress, unsigned type,
    const wchar_t* caption, const wchar_t* text) noexcept {
    if (insideRecord) { return; }
    insideRecord = true;
    char stamp[32];
    Stamp(stamp, false);
    char module[128];
    unsigned long long offset{};
    DescribeCaller(returnAddress, module, offset);
    char captionUtf8[2048];
    char textUtf8[9600];
    LineFields fields{};
    fields.stamp = stamp;
    fields.api = api;
    fields.module = module;
    fields.offset = offset;
    fields.type = type;
    fields.caption = Utf8FromWide(caption, captionUtf8, sizeof captionUtf8, 512);
    fields.text = Utf8FromWide(text, textUtf8, sizeof textUtf8, 3072);
    char line[lineCapacity];
    const std::size_t length = FormatLine(line, sizeof line, fields);
    Emit(line, length);
    insideRecord = false;
}
}
