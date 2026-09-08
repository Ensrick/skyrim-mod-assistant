// Test-only helper: a separate module whose own code calls MessageBoxW, proving
// the guard is process-wide and that the log attributes the calling module.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>

namespace {
volatile int lastResult{};
}

extern "C" __declspec(dllexport) int PopupHelperCall() {
    // Work after the call keeps this a real call. A bare `return MessageBoxW(...)`
    // becomes a tail jump under /O2, which leaves no helper frame to attribute
    // (see README, attribution).
    const int result = MessageBoxW(nullptr, L"helper body", L"helper caption", MB_OK | MB_ICONERROR);
    lastResult = result;
    return result;
}
