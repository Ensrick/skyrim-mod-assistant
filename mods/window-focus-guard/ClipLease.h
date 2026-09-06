#pragma once

namespace focus_guard {
// Platform-independent ownership policy; the production Win32 adapter and
// deterministic failure/race tests call the exact same implementation.
template <class Rect> struct ClipLease {
    bool owned{};
    Rect area{};
    template <class Api> void Release(Api& api) noexcept {
        if (!owned) { return; }
        Rect current{};
        if (!api.Query(current)) { return; } // Preserve ownership for retry.
        if (api.Equal(current, area) && !api.Release()) { return; }
        owned = false; // Released, or positively superseded by a different rect.
    }
    template <class Api> void Confine(Api& api, const Rect& requested) noexcept {
        if (!api.Foreground()) { Release(api); return; }
        Rect current{};
        if (owned && api.Equal(area, requested) && api.Query(current) && api.Equal(current, area)) { return; }
        if (!api.Foreground()) { Release(api); return; }
        if (api.Confine(requested)) {
            area = requested;
            owned = true;
            if (!api.Foreground()) { Release(api); }
        }
    }
};
}
