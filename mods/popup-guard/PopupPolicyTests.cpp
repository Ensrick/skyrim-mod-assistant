#include "PopupPolicy.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

int main() {
    using namespace popup_guard;
    int checks = 0;
    const auto check = [&](bool condition, const char* what) {
        ++checks;
        if (!condition) { std::fprintf(stderr, "FAIL %d: %s\n", checks, what); std::exit(1); }
    };
    char line[lineCapacity];

    // Escaping keeps every record on one line and unambiguous.
    LineFields f{};
    f.stamp = "12:34:56.789"; f.api = "MessageBoxW"; f.module = "SmoothCam.dll"; f.offset = 0x1a2b;
    f.type = 0x10; f.caption = "Cap \"q\""; f.text = "a\nb\r\nc\td\\e\x01z";
    FormatLine(line, sizeof line, f);
    check(std::strcmp(line, "12:34:56.789 MessageBoxW module=SmoothCam.dll+0x1a2b type=0x10 "
        "caption=\"Cap \\\"q\\\"\" text=\"a\\nb\\r\\nc\\td\\\\e\\x01z\"") == 0, "escaped line");
    check(std::strchr(line, '\n') == nullptr && std::strchr(line, '\r') == nullptr, "no raw line breaks");

    // Null fields are named, not dereferenced; non-ASCII UTF-8 passes through.
    f.caption = nullptr; f.text = "\xC3\xA9"; f.offset = 0; f.type = 0;
    FormatLine(line, sizeof line, f);
    check(std::strstr(line, "caption=\"(null)\" text=\"\xC3\xA9\"") != nullptr, "null caption and utf8 text");

    // Per-field truncation is bounded and marked.
    std::string longText(textLimit * 3, 'x');
    std::string longCaption(captionLimit * 3, 'c');
    f.caption = longCaption.c_str(); f.text = longText.c_str();
    const std::size_t n = FormatLine(line, sizeof line, f);
    check(n == std::strlen(line) && n < lineCapacity, "length reported");
    check(std::strstr(line, std::string(captionLimit, 'c').append("...\" text=\"").c_str()) != nullptr, "caption truncated");
    check(std::strstr(line, std::string(textLimit, 'x').append("...\"").c_str()) != nullptr, "text truncated");
    check(std::strstr(line, std::string(textLimit + 1, 'x').c_str()) == nullptr, "text bounded");
    // Escapes count toward the limit as emitted bytes, never split.
    std::string quotes(textLimit, '"');
    f.text = quotes.c_str(); f.caption = "c";
    FormatLine(line, sizeof line, f);
    check(std::strstr(line, std::string(textLimit / 2, '\\').c_str()) == nullptr, "escaped bytes bounded");
    check(std::strstr(line, "\\\"...\"") != nullptr, "truncation after a whole escape");

    // A small capacity never overflows and stays NUL-terminated.
    char small[40];
    std::memset(small, 'S', sizeof small);
    f.text = longText.c_str();
    const std::size_t written = FormatLine(small, 32, f);
    check(written == 31 && small[31] == '\0' && small[32] == 'S' && small[39] == 'S', "capacity respected");
    check(FormatLine(small, 0, f) == 0 && FormatLine(nullptr, 10, f) == 0, "degenerate buffers");
    char one[1] = {'x'};
    check(FormatLine(one, 1, f) == 0 && one[0] == '\0', "capacity one");

    // Opt-out parsing.
    const auto enabled = [](const char* text) { return ParseEnabled(text, std::strlen(text)); };
    check(ParseEnabled(nullptr, 0), "null text enabled");
    check(enabled(""), "empty enabled");
    check(!enabled("Enabled=false"), "false");
    check(!enabled("[PopupGuard]\r\nenabled = FALSE\r\n"), "section and case");
    check(!enabled("\xEF\xBB\xBF" "Enabled=0\n"), "bom and zero");
    check(!enabled("Enabled=no") && !enabled("Enabled=off"), "no/off");
    check(enabled("Enabled=true") && enabled("Enabled=1") && enabled("Enabled=yes") && enabled("Enabled=on"), "true tokens");
    check(enabled(";Enabled=false\n#Enabled=false\n"), "comments ignored");
    check(enabled("Enabled=maybe") && enabled("Enabled=falsehood") && enabled("Enabled="), "unknown values keep default");
    check(enabled("Enabledx=false") && enabled("XEnabled=false") && enabled("Enabled false"), "key must match exactly");
    check(!enabled("Enabled=true\nEnabled=false"), "last assignment wins");
    check(enabled("Enabled=false\nEnabled=true"), "last assignment wins reverse");
    check(!ParseEnabled("Enabled=false", 13, true) && ParseEnabled("Enabled=fals", 12, true), "length bounded");
    check(!ParseEnabled("x", 1, false), "fallback honoured");

    // Line budget: exactly lineBudget successes per session.
    LineBudget budget;
    unsigned taken = 0;
    for (unsigned i = 0; i < lineBudget + 5; ++i) { if (budget.Take()) { ++taken; } }
    check(taken == lineBudget, "budget cap");
    check(!budget.Take(), "budget stays exhausted");
    budget = LineBudget{};
    check(budget.Take(), "budget resets");

    std::printf("PASS %d policy checks\n", checks);
}
