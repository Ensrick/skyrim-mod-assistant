#include "FocusPolicy.h"
#include <cstdio>
#include <cstdlib>

int main() {
    using namespace focus_guard;
    State state;
    int checks = 0;
    const auto check = [&](bool condition) {
        ++checks;
        if (!condition) { std::fprintf(stderr, "FAIL %d\n", checks); std::exit(1); }
    };
    check(state.Step(false, false, false) == Action::release);
    check(state.Step(true, false, false) == Action::confine);
    check(state.Step(true, true, false) == Action::release);
    check(state.Step(true, false, false) == Action::release); // Start may retain foreground.
    check(state.Step(true, true, true) == Action::release); // Held Win beats click.
    check(state.Step(true, false, true) == Action::confine);
    check(state.Step(true, true, false) == Action::release);
    check(state.Step(false, false, true) == Action::release); // Never capture on desktop click.
    check(state.Step(true, false, false) == Action::confine); // Actual return to game.
    for (int i = 0; i < 10000; ++i) {
        check(state.Step(false, (i & 1) != 0, (i & 2) != 0) == Action::release);
    }
    check(state.Step(true, false, false) == Action::confine);
    std::printf("PASS %d policy checks\n", checks);
}
