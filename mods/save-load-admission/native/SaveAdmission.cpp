// SPDX-License-Identifier: MIT
#include "SaveAdmission.h"
#include "SaveMarkerPolicy.h"
#include <algorithm>
#include <string_view>
#include <unordered_set>
#include <zlib.h>

namespace Ensrick::SaveAdmission {
namespace {
class Reader {
    Bytes bytes_;
    std::size_t position_{};
public:
    explicit Reader(Bytes bytes) : bytes_(bytes) {}
    std::size_t remaining() const { return bytes_.size() - position_; }
    Bytes take(std::size_t count) {
        if (count > remaining()) throw InvalidInput("truncated field");
        const auto out = bytes_.subspan(position_, count);
        position_ += count;
        return out;
    }
    template<class T> T number() {
        const auto bytes = take(sizeof(T));
        std::uint64_t value = 0;
        for (std::size_t i = 0; i < sizeof(T); ++i) value |= std::uint64_t(bytes[i]) << (i * 8);
        return static_cast<T>(value);
    }
    std::string string() {
        const auto bytes = take(number<std::uint16_t>());
        return {reinterpret_cast<const char*>(bytes.data()), bytes.size()};
    }
    bool literal(std::string_view expected) {
        const auto value = take(expected.size());
        return std::equal(value.begin(), value.end(), expected.begin());
    }
};

std::string FoldName(const std::string& name) {
    // ASCII folding is stable regardless of process locale. Non-ASCII bytes
    // are preserved, not corrupted by locale-sensitive signed-char tolower.
    std::string out = name;
    for (char& c : out) if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
    return out;
}
bool ValidUtf8(std::string_view text) {
    std::size_t i = 0;
    while (i < text.size()) {
        const auto lead = static_cast<unsigned char>(text[i++]);
        if (lead < 0x80) continue;
        unsigned count = 0, value = 0, minimum = 0;
        if (lead >= 0xC2 && lead <= 0xDF) { count = 1; value = lead & 31; minimum = 0x80; }
        else if (lead >= 0xE0 && lead <= 0xEF) { count = 2; value = lead & 15; minimum = 0x800; }
        else if (lead >= 0xF0 && lead <= 0xF4) { count = 3; value = lead & 7; minimum = 0x10000; }
        else return false;
        if (count > text.size() - i) return false;
        while (count--) {
            const auto next = static_cast<unsigned char>(text[i++]);
            if ((next & 0xC0) != 0x80) return false;
            value = (value << 6) | (next & 63);
        }
        if (value < minimum || value > 0x10FFFF || (value >= 0xD800 && value <= 0xDFFF)) return false;
    }
    return true;
}
void ValidatePlugins(const PluginTable& table) {
    if (table.full.empty() || table.full.size() > 254 || table.light.size() > 4096)
        throw InvalidInput("invalid plugin counts");
    std::unordered_set<std::string> names;
    for (const auto* list : {&table.full, &table.light}) for (const auto& name : *list) {
        const auto key = FoldName(name);
        if (!ValidUtf8(name) || key.size() <= 4 || key.size() > 255 ||
            !(key.ends_with(".esm") || key.ends_with(".esp") || key.ends_with(".esl")))
            throw InvalidInput("invalid plugin filename");
        for (unsigned char c : name)
            if (c < 32 || c == 127 || c == '/' || c == '\\' || c == ':' || c == '"' || c == '<' || c == '>' || c == '|' || c == '?' || c == '*')
                throw InvalidInput("invalid plugin filename character");
        if (!names.insert(key).second) throw InvalidInput("duplicate plugin entry");
    }
}
std::vector<std::uint8_t> Lz4(Bytes packed, std::size_t expected) {
    Reader input(packed);
    std::vector<std::uint8_t> out;
    out.reserve(expected);
    auto length = [&input, expected](std::size_t count) {
        if (count == 15) {
            unsigned extra;
            do {
                extra = input.number<std::uint8_t>();
                if (extra > expected || count > expected - extra)
                    throw InvalidInput("LZ4 length exceeds declared output");
                count += extra;
            } while (extra == 255);
        }
        return count;
    };
    while (input.remaining()) {
        const auto token = input.number<std::uint8_t>();
        const auto literals = length(token >> 4);
        if (literals > expected - out.size()) throw InvalidInput("LZ4 literal overflow");
        const auto bytes = input.take(literals);
        out.insert(out.end(), bytes.begin(), bytes.end());
        if (!input.remaining()) break;
        const auto offset = input.number<std::uint16_t>();
        const auto count = length(token & 15) + 4;
        if (!offset || offset > out.size() || count > expected - out.size())
            throw InvalidInput("invalid LZ4 match");
        for (std::size_t i = 0; i < count; ++i) out.push_back(out[out.size() - offset]);
    }
    if (out.size() != expected) throw InvalidInput("LZ4 output size mismatch");
    return out;
}
}

SaveInfo ParseESS(Bytes raw) {
    if (raw.size() > MaximumBytes) throw InvalidInput("save exceeds size limit");
    Reader file(raw);
    if (!file.literal("TESV_SAVEGAME")) throw InvalidInput("invalid save signature");
    Reader header(file.take(file.number<std::uint32_t>()));
    if (header.number<std::uint32_t>() != 12) throw InvalidInput("unsupported SSE header version");
    SaveInfo result;
    result.number = header.number<std::uint32_t>();
    header.string(); // Player name is not used in admission or logged.
    result.level = header.number<std::uint32_t>();
    header.string(); header.string(); header.string(); // location/date/race
    header.take(2 + 4 + 4 + 8);
    const auto width = header.number<std::uint32_t>();
    const auto height = header.number<std::uint32_t>();
    result.compression = header.number<std::uint16_t>();
    if (header.remaining()) throw InvalidInput("unsupported header extension");
    // Division checks prevent multiplication overflow even on 32-bit hosts.
    if (width > MaximumBytes / 4 || (width && height > MaximumBytes / 4 / width))
        throw InvalidInput("screenshot exceeds size limit");
    file.take(std::size_t(width) * height * 4);
    std::vector<std::uint8_t> decoded;
    Bytes body;
    if (!result.compression) body = file.take(file.remaining());
    else {
        const auto size = file.number<std::uint32_t>();
        const auto packedSize = file.number<std::uint32_t>();
        if (!size || size > MaximumBytes) throw InvalidInput("invalid decompressed size");
        const auto packed = file.take(packedSize);
        if (file.remaining()) throw InvalidInput("trailing compressed save bytes");
        if (result.compression == 1) {
            decoded.resize(size);
            uLongf outputSize = size;
            uLong inputSize = packedSize;
            const auto status = uncompress2(decoded.data(), &outputSize, packed.data(), &inputSize);
            if (status != Z_OK || outputSize != size || inputSize != packedSize)
                throw InvalidInput("invalid zlib payload or size");
        } else if (result.compression == 2) decoded = Lz4(packed, size);
        else throw InvalidInput("unsupported compression mode");
        body = decoded;
    }
    Reader data(body);
    result.formVersion = data.number<std::uint8_t>();
    if (result.formVersion < 78) throw InvalidInput("unsupported SSE form version");
    Reader plugins(data.take(data.number<std::uint32_t>()));
    const auto fullCount = plugins.number<std::uint8_t>();
    for (unsigned i = 0; i < fullCount; ++i) result.plugins.full.push_back(plugins.string());
    const auto lightCount = plugins.number<std::uint16_t>();
    if (lightCount > 4096) throw InvalidInput("too many light plugins");
    for (unsigned i = 0; i < lightCount; ++i) result.plugins.light.push_back(plugins.string());
    if (plugins.remaining()) throw InvalidInput("plugin length/count mismatch");
    ValidatePlugins(result.plugins);
    return result; // Remaining world/script records are deliberately not certified.
}

Checkpoint ParseCurrencyCheckpoint(Bytes raw, std::uint64_t expectedFingerprint) {
    if (raw.size() > MaximumBytes) throw InvalidInput("co-save exceeds size limit");
    Reader file(raw);
    if (!file.literal("SKSE") || file.number<std::uint32_t>() != 1)
        throw InvalidInput("unsupported SKSE co-save header");
    file.take(8); // SKSE/runtime versions, not a substitute for checkpoint identity.
    const auto count = file.number<std::uint32_t>();
    if (count > file.remaining() / 12) throw InvalidInput("invalid plugin block count");
    bool foundPlugin = false, foundCheckpoint = false;
    Currency::SaveCheckpoint checkpoint;
    for (std::uint32_t i = 0; i < count; ++i) {
        const auto identity = file.number<std::uint32_t>();
        const auto chunks = file.number<std::uint32_t>();
        Reader plugin(file.take(file.number<std::uint32_t>()));
        if (chunks > plugin.remaining() / 12) throw InvalidInput("invalid chunk count");
        const bool currency = identity == Currency::SerializationID;
        if (currency) {
            if (foundPlugin) throw InvalidInput("duplicate currency plugin block");
            foundPlugin = true;
        }
        for (std::uint32_t j = 0; j < chunks; ++j) {
            const auto kind = plugin.number<std::uint32_t>();
            const auto version = plugin.number<std::uint32_t>();
            const auto size = plugin.number<std::uint32_t>();
            Reader chunk(plugin.take(size));
            if (currency) {
                if (foundCheckpoint || size != 40) throw InvalidInput("unsupported currency checkpoint layout");
                checkpoint.magic = chunk.number<std::uint32_t>();
                checkpoint.schema = chunk.number<std::uint32_t>();
                checkpoint.ledgerFingerprint = chunk.number<std::uint64_t>();
                checkpoint.ledgerValue = chunk.number<std::uint64_t>();
                checkpoint.observedBackend = chunk.number<std::uint64_t>();
                checkpoint.observedPhysical = chunk.number<std::uint64_t>();
                if (!Currency::IsRecognizedNativeSaveCheckpoint(kind, version, size, checkpoint))
                    throw InvalidInput("invalid currency checkpoint");
                if (!Currency::CheckpointMatchesLedger(checkpoint, expectedFingerprint))
                    throw InvalidInput("currency fingerprint mismatch");
                foundCheckpoint = true;
            }
        }
        if (plugin.remaining()) throw InvalidInput("plugin length/chunk count mismatch");
    }
    if (file.remaining()) throw InvalidInput("trailing co-save bytes");
    if (!foundCheckpoint) throw InvalidInput("native currency v2 checkpoint missing");
    return {checkpoint.ledgerFingerprint, checkpoint.ledgerValue, checkpoint.observedBackend, checkpoint.observedPhysical};
}

std::vector<std::string> ComparePlugins(const PluginTable& saved, const PluginTable& active) {
    ValidatePlugins(saved);
    ValidatePlugins(active);
    std::unordered_set<std::string> full, light;
    for (const auto& name : active.full) full.insert(FoldName(name));
    for (const auto& name : active.light) light.insert(FoldName(name));
    std::vector<std::string> problems;
    auto check = [&problems](const auto& names, const auto& same, const auto& other) {
        for (const auto& name : names) {
            const auto key = FoldName(name);
            if (!same.contains(key)) problems.push_back((other.contains(key) ? "plugin type changed: " : "missing plugin: ") + name);
        }
    };
    check(saved.full, full, light);
    check(saved.light, light, full);
    return problems;
}
}
