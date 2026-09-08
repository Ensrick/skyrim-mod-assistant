#pragma once
#include <cstddef>

namespace popup_guard {
// Platform-independent log-line policy shared by the production hooks and the
// host tests: escaping, per-field truncation, whole-line bounding, the opt-out
// INI parse and the per-session line budget. No Windows headers, no
// allocation, no exceptions, no printf; every function is bounded by its
// arguments so a hook can run it on any thread at any time.

constexpr std::size_t captionLimit = 256;  // escaped bytes kept per caption
constexpr std::size_t textLimit = 2048;    // escaped bytes kept per message text
constexpr std::size_t lineCapacity = 4096; // bytes per formatted line incl. NUL
constexpr unsigned lineBudget = 1000;      // lines per session, then silence

struct LineWriter {
    char* out{};
    std::size_t capacity{};
    std::size_t length{};
    bool clipped{};

    void Put(char c) noexcept {
        if (length + 1 < capacity) { out[length++] = c; } else { clipped = true; }
    }
    void Puts(const char* s) noexcept {
        for (; s && *s; ++s) { Put(*s); }
    }
    void PutHex(unsigned long long value) noexcept {
        char digits[16];
        std::size_t n = 0;
        do {
            digits[n++] = "0123456789abcdef"[value & 0xF];
            value >>= 4;
        } while (value && n < sizeof digits);
        while (n) { Put(digits[--n]); }
    }
    void PutDecimal(unsigned long long value, unsigned minimumDigits = 1) noexcept {
        char digits[20];
        std::size_t n = 0;
        do {
            digits[n++] = static_cast<char>('0' + value % 10);
            value /= 10;
        } while (value && n < sizeof digits);
        while (n < minimumDigits && n < sizeof digits) { digits[n++] = '0'; }
        while (n) { Put(digits[--n]); }
    }
    // Escaped, bounded copy: quotes, backslashes and control bytes become C
    // escapes so one call is always exactly one line. `limit` counts escaped
    // output bytes; overflow is marked with "..." so truncation is visible.
    void PutEscaped(const char* s, std::size_t limit) noexcept {
        if (!s) { Puts("(null)"); return; }
        std::size_t used = 0;
        for (; *s; ++s) {
            const unsigned char c = static_cast<unsigned char>(*s);
            char piece[5]{};
            std::size_t n = 0;
            switch (c) {
            case '\\': piece[0] = '\\'; piece[1] = '\\'; n = 2; break;
            case '"': piece[0] = '\\'; piece[1] = '"'; n = 2; break;
            case '\n': piece[0] = '\\'; piece[1] = 'n'; n = 2; break;
            case '\r': piece[0] = '\\'; piece[1] = 'r'; n = 2; break;
            case '\t': piece[0] = '\\'; piece[1] = 't'; n = 2; break;
            default:
                if (c < 0x20 || c == 0x7F) {
                    piece[0] = '\\'; piece[1] = 'x';
                    piece[2] = "0123456789abcdef"[c >> 4];
                    piece[3] = "0123456789abcdef"[c & 0xF];
                    n = 4;
                } else {
                    piece[0] = static_cast<char>(c);
                    n = 1;
                }
            }
            if (used + n > limit) { Puts("..."); return; }
            for (std::size_t i = 0; i < n; ++i) { Put(piece[i]); }
            used += n;
        }
    }
    void Finish() noexcept {
        if (out && capacity) { out[length] = '\0'; }
    }
};

struct LineFields {
    const char* stamp{};   // "HH:MM:SS.mmm", produced by the platform layer
    const char* api{};     // e.g. "MessageBoxW"
    const char* module{};  // calling module base name, "?" when unresolved
    unsigned long long offset{}; // return address minus module base
    unsigned type{};       // MessageBox flags or FatalAppExit action
    const char* caption{}; // UTF-8, may be null
    const char* text{};    // UTF-8, may be null
};

// Formats one bounded, single-line record. Returns the byte length written
// (without NUL). Never writes beyond `capacity`; a zero capacity writes nothing.
inline std::size_t FormatLine(char* out, std::size_t capacity, const LineFields& f) noexcept {
    if (!out || capacity == 0) { return 0; }
    LineWriter w{out, capacity};
    w.Puts(f.stamp ? f.stamp : "--:--:--.---");
    w.Put(' ');
    w.Puts(f.api ? f.api : "?");
    w.Puts(" module=");
    w.Puts(f.module ? f.module : "?");
    w.Puts("+0x");
    w.PutHex(f.offset);
    w.Puts(" type=0x");
    w.PutHex(f.type);
    w.Puts(" caption=\"");
    w.PutEscaped(f.caption, captionLimit);
    w.Puts("\" text=\"");
    w.PutEscaped(f.text, textLimit);
    w.Put('"');
    w.Finish();
    return w.length;
}

// Opt-out file: a line `Enabled=false` (case-insensitive key; false/0/no/off)
// disables the guard. Missing file, missing key or an unrecognised value keep
// the default (enabled). Section headers and ;/# comments are ignored. The last
// recognised assignment wins. A UTF-8 byte-order mark is skipped.
inline bool ParseEnabled(const char* text, std::size_t length, bool fallback = true) noexcept {
    if (!text) { return fallback; }
    std::size_t i = 0;
    if (length >= 3 && static_cast<unsigned char>(text[0]) == 0xEF &&
        static_cast<unsigned char>(text[1]) == 0xBB && static_cast<unsigned char>(text[2]) == 0xBF) {
        i = 3;
    }
    const auto lower = [](char c) noexcept { return (c >= 'A' && c <= 'Z') ? static_cast<char>(c + 32) : c; };
    const auto blank = [](char c) noexcept { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; };
    bool enabled = fallback;
    while (i < length) {
        std::size_t end = i;
        while (end < length && text[end] != '\n') { ++end; }
        std::size_t start = i;
        std::size_t stop = end;
        while (start < stop && blank(text[start])) { ++start; }
        while (stop > start && blank(text[stop - 1])) { --stop; }
        i = end + 1;
        if (start == stop || text[start] == ';' || text[start] == '#' || text[start] == '[') { continue; }
        std::size_t eq = start;
        while (eq < stop && text[eq] != '=') { ++eq; }
        if (eq == stop) { continue; }
        std::size_t keyEnd = eq;
        while (keyEnd > start && blank(text[keyEnd - 1])) { --keyEnd; }
        const char key[] = "enabled";
        bool match = (keyEnd - start) == sizeof(key) - 1;
        for (std::size_t k = 0; match && k < sizeof(key) - 1; ++k) { match = lower(text[start + k]) == key[k]; }
        if (!match) { continue; }
        std::size_t v = eq + 1;
        while (v < stop && blank(text[v])) { ++v; }
        char value[8]{};
        std::size_t n = 0;
        for (; v < stop && n < sizeof(value) - 1; ++v) { value[n++] = lower(text[v]); }
        if (v != stop) { continue; } // value longer than any recognised token
        const char* falses[] = {"false", "0", "no", "off"};
        const char* trues[] = {"true", "1", "yes", "on"};
        const auto equals = [](const char* a, const char* b) noexcept {
            while (*a && *a == *b) { ++a; ++b; }
            return *a == *b;
        };
        for (const char* f : falses) { if (equals(value, f)) { enabled = false; } }
        for (const char* t : trues) { if (equals(value, t)) { enabled = true; } }
    }
    return enabled;
}

// Per-session line budget; once exhausted the guard keeps suppressing dialogs
// but writes nothing more, so a popup loop cannot fill the disk.
struct LineBudget {
    unsigned remaining{lineBudget};
    bool Take() noexcept {
        if (!remaining) { return false; }
        --remaining;
        return true;
    }
};
}
