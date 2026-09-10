// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace Ensrick::SaveAdmission {
using Bytes = std::span<const std::uint8_t>;
inline constexpr std::size_t MaximumBytes = 256u * 1024u * 1024u;
class InvalidInput : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};
struct PluginTable {
    std::vector<std::string> full, light;
};
struct SaveInfo {
    std::uint32_t number{}, level{};
    std::uint16_t compression{};
    std::uint8_t formVersion{};
    PluginTable plugins;
};
struct Checkpoint {
    std::uint64_t fingerprint{}, value{}, backend{}, physical{};
};
// Read-only parsing, not a save-health certificate. Throws InvalidInput for
// unsupported/malformed input. Allocations can throw std::bad_alloc; callers
// must handle exceptions before crossing an engine ABI boundary.
SaveInfo ParseESS(Bytes raw);
Checkpoint ParseCurrencyCheckpoint(Bytes raw, std::uint64_t expectedFingerprint);
// Active table must come from the running engine in a future runtime adapter.
// New active plugins are allowed; missing names or full/light changes are not.
std::vector<std::string> ComparePlugins(const PluginTable& saved, const PluginTable& active);
}
