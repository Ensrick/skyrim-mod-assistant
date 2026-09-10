// SPDX-License-Identifier: MIT
// Offline read-only harness, NOT the runtime adapter or a save-health verdict.
#include "SaveAdmission.h"
#include <fstream>
#include <iostream>
#include <filesystem>
#include <charconv>
using namespace Ensrick::SaveAdmission;
static std::vector<std::uint8_t> Read(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) throw InvalidInput("cannot open input");
    const auto size = file.tellg();
    if (size < 0 || std::uint64_t(size) > MaximumBytes) throw InvalidInput("input size limit");
    std::vector<std::uint8_t> data(static_cast<std::size_t>(size));
    file.seekg(0);
    if (!file.read(reinterpret_cast<char*>(data.data()), data.size()) || file.peek() != std::char_traits<char>::eof())
        throw InvalidInput("incomplete or changed input read");
    return data;
}
int main(int argc, char** argv) {
    try {
        if (argc < 3) throw InvalidInput("usage: ess FILE | checkpoint FILE HEX_FINGERPRINT | compare SAVE ACTIVE_SAVE");
        const std::string mode = argv[1];
        const auto input = Read(std::filesystem::u8path(argv[2]));
        if (mode == "ess" && argc == 3) {
            const auto save = ParseESS(input);
            std::cout << "META\t" << save.number << '\t' << save.level << '\t' << save.compression << '\t' << unsigned(save.formVersion) << '\n';
            for (const auto& name : save.plugins.full) std::cout << "F\t" << name << '\n';
            for (const auto& name : save.plugins.light) std::cout << "L\t" << name << '\n';
        } else if (mode == "checkpoint" && argc == 4) {
            std::uint64_t fingerprint = 0;
            const std::string_view text = argv[3];
            const auto parsed = std::from_chars(text.data(), text.data() + text.size(), fingerprint, 16);
            if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size()) throw InvalidInput("invalid fingerprint argument");
            const auto c = ParseCurrencyCheckpoint(input, fingerprint);
            std::cout << "CHECKPOINT\t" << c.fingerprint << '\t' << c.value << '\t' << c.backend << '\t' << c.physical << '\n';
        } else if (mode == "compare" && argc == 4) {
            const auto other = Read(std::filesystem::u8path(argv[3]));
            const auto errors = ComparePlugins(ParseESS(input).plugins, ParseESS(other).plugins);
            for (const auto& error : errors) std::cout << error << '\n';
            return errors.empty() ? 0 : 1;
        } else throw InvalidInput("invalid command arguments");
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "REFUSED: " << e.what() << '\n';
        return 2;
    }
}
