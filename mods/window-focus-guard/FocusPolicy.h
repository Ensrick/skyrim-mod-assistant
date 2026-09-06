#pragma once

namespace focus_guard {
enum class Action { release, confine };
struct State {
    bool desktopIntent{};
    Action Step(bool foreground, bool escapeKey, bool freshGameClick) noexcept {
        if (!foreground) {
            desktopIntent = false;
            return Action::release;
        }
        if (escapeKey) {
            desktopIntent = true;
        } else if (freshGameClick) {
            desktopIntent = false;
        }
        return desktopIntent ? Action::release : Action::confine;
    }
};
}
