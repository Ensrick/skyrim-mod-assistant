// SPDX-License-Identifier: MIT
// Exercises the C ABI against the real bridge, reader, and Windows lease with
// synthetic fixtures in a newly created temporary directory only.
#include "SaveAdmissionAbi.h"
#include <Windows.h>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#include <zlib.h>

extern "C" uint32_t ensrick_abi_c_consumer_probe(uint32_t* version, uint64_t* maximum, const char** ok_name);

using Buffer = std::vector<std::uint8_t>;
static unsigned checks;
static void Check(bool value, int line) {
    ++checks;
    if (!value) throw std::runtime_error("ABI contract failed at line " + std::to_string(line));
}
#define CHECK(x) Check((x), __LINE__)

// Local fixture generator (same synthetic layout as Tests.cpp; no parser rules).
template<class T> static void Num(Buffer& b, T v) {
    for (unsigned i = 0; i < sizeof(T); ++i) b.push_back(std::uint8_t(std::uint64_t(v) >> (i * 8)));
}
static void Text(Buffer& b, std::string_view t) { b.insert(b.end(), t.begin(), t.end()); }
static void Str(Buffer& b, std::string_view t) { Num<std::uint16_t>(b, std::uint16_t(t.size())); Text(b, t); }
static void Add(Buffer& b, const Buffer& o) { b.insert(b.end(), o.begin(), o.end()); }
static Buffer Ess(const std::vector<std::string>& full, const std::vector<std::string>& light, bool zlib) {
    Buffer table; Num<std::uint8_t>(table, std::uint8_t(full.size()));
    for (const auto& n : full) Str(table, n);
    Num<std::uint16_t>(table, std::uint16_t(light.size()));
    for (const auto& n : light) Str(table, n);
    Buffer body{78}; Num<std::uint32_t>(body, std::uint32_t(table.size())); Add(body, table);
    Buffer h; Num<std::uint32_t>(h, 12); Num<std::uint32_t>(h, 7); Str(h, "Test");
    Num<std::uint32_t>(h, 3); Str(h, "Winterhold"); Str(h, "000.00.09"); Str(h, "NordRace");
    h.insert(h.end(), 18, 0); Num<std::uint32_t>(h, 1); Num<std::uint32_t>(h, 1); Num<std::uint16_t>(h, zlib ? 1 : 0);
    Buffer out; Text(out, "TESV_SAVEGAME"); Num<std::uint32_t>(out, std::uint32_t(h.size())); Add(out, h);
    out.insert(out.end(), 4, 0);
    if (!zlib) Add(out, body);
    else {
        uLongf size = compressBound(uLong(body.size()));
        Buffer packed(size);
        CHECK(compress2(packed.data(), &size, body.data(), uLong(body.size()), 9) == Z_OK);
        packed.resize(size);
        Num<std::uint32_t>(out, std::uint32_t(body.size())); Num<std::uint32_t>(out, std::uint32_t(packed.size())); Add(out, packed);
    }
    return out;
}
static Buffer CoSave(std::uint64_t fingerprint) {
    Buffer rec; Text(rec, "ECMK"); Num<std::uint32_t>(rec, 2); Num<std::uint32_t>(rec, 40);
    Text(rec, "ECV2"); Num<std::uint32_t>(rec, 2);
    Num<std::uint64_t>(rec, fingerprint); Num<std::uint64_t>(rec, 23); Num<std::uint64_t>(rec, 24); Num<std::uint64_t>(rec, 25);
    Buffer out; Text(out, "SKSE"); Num<std::uint32_t>(out, 1); Num<std::uint32_t>(out, 0); Num<std::uint32_t>(out, 0);
    Num<std::uint32_t>(out, 1); Text(out, "ECDN"); Num<std::uint32_t>(out, 1); Num<std::uint32_t>(out, std::uint32_t(rec.size()));
    Add(out, rec);
    return out;
}
static void Write(const std::filesystem::path& path, const Buffer& bytes) {
    std::ofstream file(path, std::ios::binary);
    file.write(reinterpret_cast<const char*>(bytes.data()), std::streamsize(bytes.size()));
    if (!file) throw std::runtime_error("cannot create fixture");
}
static HANDLE Open(const std::filesystem::path& path, DWORD access) {
    return CreateFileW(path.c_str(), access, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
}
static bool WriteBlocked(const std::filesystem::path& path) {
    const auto handle = Open(path, GENERIC_WRITE);
    const auto error = GetLastError();
    if (handle != INVALID_HANDLE_VALUE) { CloseHandle(handle); return false; }
    CHECK(error == ERROR_SHARING_VIOLATION);
    return true;
}

struct Names {
    std::vector<std::string> storage;
    std::vector<ensrick_admission_plugin_name> entries;
    explicit Names(std::vector<std::string> list) : storage(std::move(list)) {
        for (const auto& s : storage) entries.push_back({s.c_str(), std::uint32_t(s.size() + 1), 0});
    }
    Names(const Names&) = delete;
    Names& operator=(const Names&) = delete;
};
static ensrick_admission_request Request(const Buffer& ess, const Names& full, const Names& light,
    std::uint64_t fingerprint, const std::wstring& path) {
    ensrick_admission_request r{};
    r.struct_size = sizeof r; r.abi_version = ENSRICK_ADMISSION_ABI_VERSION;
    r.ess_bytes = ess.data(); r.ess_size = ess.size();
    r.full_plugins = full.entries.data(); r.full_count = std::uint32_t(full.entries.size());
    r.light_plugins = light.entries.data(); r.light_count = std::uint32_t(light.entries.size());
    r.expected_fingerprint = fingerprint;
    r.cosave_path_utf16 = reinterpret_cast<const std::uint16_t*>(path.c_str());
    r.cosave_path_capacity_units = std::uint32_t(path.size() + 1);
    return r;
}
static std::uint32_t Begin(const ensrick_admission_request& request, ensrick_admission_result& result, ensrick_admission_lease*& lease) {
    std::memset(&result, 0xAB, sizeof result);
    result.struct_size = sizeof result;
    lease = reinterpret_cast<ensrick_admission_lease*>(1);
    const auto status = ensrick_admission_begin(&request, &result, &lease);
    CHECK(status == result.status && result.struct_size == sizeof result);
    CHECK(std::memchr(result.reason, 0, sizeof result.reason) != nullptr);
    const std::string_view reason(result.reason);
    // Phrases such as "size/ABI" contain a slash but aren't file paths.
    CHECK(reason.find('\\') == reason.npos && reason.find("ensrick-abi") == reason.npos);
    CHECK((status == ENSRICK_ADMISSION_OK) == (lease != nullptr));
    CHECK((status == ENSRICK_ADMISSION_OK) == reason.empty());
    CHECK(result.reserved8 == 0 && result.reserved32 == 0);
    return status;
}

int main() {
    const auto root = std::filesystem::temp_directory_path() /
        (L"ensrick-abi-" + std::to_wstring(GetCurrentProcessId()) + L"-" + std::to_wstring(GetTickCount64()));
    if (!std::filesystem::create_directory(root)) return 2;
    const auto co = root / L"test.skse", other = root / L"other.skse";
    int exitCode = 0;
    try {
        std::uint32_t version = 0; std::uint64_t maximum = 0; const char* okName = nullptr;
        CHECK(ensrick_abi_c_consumer_probe(&version, &maximum, &okName) == ENSRICK_ADMISSION_INVALID_ARGUMENT);
        CHECK(version == ENSRICK_ADMISSION_ABI_VERSION && maximum == 256ull * 1024 * 1024);
        CHECK(std::string_view(okName) == "admitted" && std::string_view(ensrick_admission_status_name(0xFFFFFFFFu)) == "unknown");

        ensrick_admission_result result{}; ensrick_admission_lease* lease = nullptr;
        CHECK(ensrick_admission_begin(nullptr, nullptr, &lease) == ENSRICK_ADMISSION_INVALID_ARGUMENT);
        result.struct_size = sizeof(result) - 1; result.status = 77;
        CHECK(ensrick_admission_begin(nullptr, &result, &lease) == ENSRICK_ADMISSION_INVALID_ARGUMENT && result.status == 77);
        result.struct_size = sizeof result;
        CHECK(ensrick_admission_begin(nullptr, &result, nullptr) == ENSRICK_ADMISSION_INVALID_ARGUMENT && result.status == ENSRICK_ADMISSION_INVALID_ARGUMENT);

        const auto coBytes = CoSave(123);
        Write(co, coBytes); Write(other, coBytes);
        const Names full({"Skyrim.esm", "Example.esp"}), light({"TrueHUD.esl"});
        const auto path = co.wstring();

        for (bool zlib : {false, true}) {
            const auto saved = Ess({"Skyrim.esm", "Example.esp"}, {"TrueHUD.esl"}, zlib);
            const auto request = Request(saved, full, light, 123, path);
            CHECK(Begin(request, result, lease) == ENSRICK_ADMISSION_OK);
            CHECK(result.save_number == 7 && result.player_level == 3 && result.compression == (zlib ? 1 : 0) && result.form_version == 78);
            CHECK(result.saved_full_count == 2 && result.saved_light_count == 1 && result.problem_count == 0 && result.win32_error == 0);
            CHECK(result.checkpoint_fingerprint == 123 && result.checkpoint_value == 23 && result.checkpoint_backend == 24 && result.checkpoint_physical == 25);
            const std::uint8_t* data = nullptr; std::uint64_t size = 0;
            CHECK(ensrick_admission_lease_cosave(lease, &data, &size) == ENSRICK_ADMISSION_OK && data && size == coBytes.size());
            CHECK(std::equal(coBytes.begin(), coBytes.end(), data));
            CHECK(ensrick_admission_lease_cosave(nullptr, &data, &size) == ENSRICK_ADMISSION_INVALID_ARGUMENT && !data && !size);
            CHECK(ensrick_admission_lease_cosave(lease, nullptr, &size) == ENSRICK_ADMISSION_INVALID_ARGUMENT);
            const auto same = Open(co, GENERIC_READ), another = Open(other, GENERIC_READ);
            CHECK(same != INVALID_HANDLE_VALUE && another != INVALID_HANDLE_VALUE);
            CHECK(ensrick_admission_lease_matches_handle(lease, same) == 1);
            CHECK(ensrick_admission_lease_matches_handle(lease, another) == 0);
            CHECK(ensrick_admission_lease_matches_handle(nullptr, same) == 0);
            CHECK(ensrick_admission_lease_matches_handle(lease, nullptr) == 0);
            CHECK(ensrick_admission_lease_matches_handle(lease, INVALID_HANDLE_VALUE) == 0);
            CloseHandle(same); CloseHandle(another);
            CHECK(WriteBlocked(co));
            ensrick_admission_release(lease); lease = nullptr;
            CHECK(!WriteBlocked(co));
        }

        const auto saved = Ess({"Skyrim.esm", "Example.esp"}, {"TrueHUD.esl"}, false);
        const auto base = Request(saved, full, light, 123, path);
        const auto expect = [&](const ensrick_admission_request& r, std::uint32_t status, std::string_view part = {}) {
            CHECK(Begin(r, result, lease) == status);
            CHECK(!WriteBlocked(co)); // no lease survives a refusal
            if (!part.empty()) CHECK(std::string_view(result.reason).find(part) != std::string_view::npos);
        };
        { auto r = base; r.expected_fingerprint = 0; expect(r, ENSRICK_ADMISSION_FINGERPRINT_UNAVAILABLE); }
        { auto r = base; r.expected_fingerprint = 124; expect(r, ENSRICK_ADMISSION_COSAVE_REFUSED, "fingerprint mismatch"); }
        { auto r = base; r.abi_version = 2; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.reserved = 1; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "reserved request"); }
        { auto r = base; auto names = full.entries; names[0].reserved = 1; r.full_plugins = names.data(); expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "reserved name"); }
        { auto r = base; r.struct_size = sizeof(r) - 8; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.ess_bytes = nullptr; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.ess_size = 0; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.ess_size = maximum + 1; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "size limit"); }
        for (std::size_t n = 1; n < saved.size(); ++n) { auto r = base; r.ess_size = n; expect(r, ENSRICK_ADMISSION_MALFORMED_SAVE); }

        // Count caps are enforced before any name pointer is dereferenced.
        { auto r = base; r.full_count = 255; r.full_plugins = nullptr; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.light_count = 4097; r.light_plugins = nullptr; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.full_plugins = nullptr; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT); }
        { auto r = base; r.light_count = 0; expect(r, ENSRICK_ADMISSION_PLUGIN_MISMATCH, "missing plugin: TrueHUD.esl"); CHECK(result.problem_count == 1); }
        const Names missing({"Skyrim.esm"});
        { auto r = base; r.full_plugins = missing.entries.data(); r.full_count = 1; expect(r, ENSRICK_ADMISSION_PLUGIN_MISMATCH, "missing plugin: Example.esp"); CHECK(result.problem_count == 1 && result.save_number == 7); }
        const Names swappedFull({"Skyrim.esm", "TrueHUD.esl"}), swappedLight({"Example.esp"});
        expect(Request(saved, swappedFull, swappedLight, 123, path), ENSRICK_ADMISSION_PLUGIN_MISMATCH, "plugin type changed: Example.esp");
        CHECK(result.problem_count == 2);
        const Names extra({"skyrim.ESM", "Example.esp", "Extra.esp"}), lightCase({"truehud.ESL"});
        CHECK(Begin(Request(saved, extra, lightCase, 123, path), result, lease) == ENSRICK_ADMISSION_OK);
        ensrick_admission_release(lease); lease = nullptr;

        // Name buffer contracts.
        {
            char unterminated[11] = {'S','k','y','r','i','m','.','e','s','m','X'};
            const std::string longName = std::string(300, 'a') + ".esp";
            const std::vector<ensrick_admission_plugin_name> bad[] = {
                {{unterminated, sizeof unterminated, 0}, full.entries[1]},
                {{nullptr, 10, 0}, full.entries[1]},
                {{"Skyrim.esm", 0, 0}, full.entries[1]},
                {{longName.c_str(), std::uint32_t(longName.size() + 1), 0}, full.entries[1]}};
            for (const auto& entries : bad) {
                auto r = base; r.full_plugins = entries.data(); r.full_count = std::uint32_t(entries.size());
                expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "name");
            }
        }
        for (const auto& names : {std::vector<std::string>{"../Skyrim.esm", "Example.esp"}, {"", "Example.esp"},
            {"Skyrim.esm", "SKYRIM.ESM", "Example.esp"}, {"A\n.esp", "Example.esp"}, {"Skyrim.exe", "Example.esp"}}) {
            const Names active(names);
            expect(Request(saved, active, light, 123, path), ENSRICK_ADMISSION_ACTIVE_PLUGINS_INVALID);
        }

        // Reason is bounded and still NUL-terminated with many problems.
        {
            std::vector<std::string> many{"Skyrim.esm"};
            for (unsigned i = 0; i < 199; ++i) { char name[16]; std::snprintf(name, sizeof name, "P%03u.esp", i); many.push_back(name); }
            const auto wide = Ess(many, {}, false);
            const Names none({});
            expect(Request(wide, missing, none, 123, path), ENSRICK_ADMISSION_PLUGIN_MISMATCH, "199 plugin problem(s): missing plugin: P000.esp");
            CHECK(result.problem_count == 199 && std::strlen(result.reason) == ENSRICK_ADMISSION_REASON_BYTES - 1);
        }

        // Path contracts: never opened, never echoed.
        { auto r = base; r.cosave_path_utf16 = nullptr; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path"); }
        { auto r = base; r.cosave_path_capacity_units = 0; expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path"); }
        { auto r = base; r.cosave_path_capacity_units = std::uint32_t(path.size()); expect(r, ENSRICK_ADMISSION_INVALID_ARGUMENT, "unterminated"); }
        expect(Request(saved, full, light, 123, L""), ENSRICK_ADMISSION_INVALID_ARGUMENT, "empty");
        expect(Request(saved, full, light, 123, L"relative.skse"), ENSRICK_ADMISSION_INVALID_ARGUMENT, "absolute");
        expect(Request(saved, full, light, 123, (root / L"test.ess").wstring()), ENSRICK_ADMISSION_INVALID_ARGUMENT, ".skse");
        expect(Request(saved, full, light, 123, (root / L"absent.skse").wstring()), ENSRICK_ADMISSION_LEASE_FAILED);
        CHECK(result.win32_error == ERROR_FILE_NOT_FOUND && std::string_view(result.reason).find("absent") == std::string_view::npos);
        {
            const auto writer = Open(co, GENERIC_WRITE);
            CHECK(writer != INVALID_HANDLE_VALUE);
            expect(base, ENSRICK_ADMISSION_LEASE_FAILED);
            CHECK(result.win32_error == ERROR_SHARING_VIOLATION);
            CloseHandle(writer);
        }
        Write(other, Buffer(coBytes.begin(), coBytes.begin() + 20));
        expect(Request(saved, full, light, 123, other.wstring()), ENSRICK_ADMISSION_COSAVE_REFUSED);
        CHECK(!WriteBlocked(other));
        ensrick_admission_release(nullptr);
        std::cout << checks << " ABI checks passed\n";
    } catch (const std::exception& e) { std::cerr << "after " << checks << " checks: " << e.what() << '\n'; exitCode = 1; }
    // Exact test-owned paths only; no recursive deletion.
    for (const auto& path : {co, other}) { std::error_code ec; std::filesystem::remove(path, ec); }
    { std::error_code ec; std::filesystem::remove(root, ec); }
    return exitCode;
}
