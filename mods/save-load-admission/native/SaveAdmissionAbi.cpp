// SPDX-License-Identifier: MIT
// C++20 bridge behind SaveAdmissionAbi.h. It owns no policy: every parse and
// comparison rule lives in SaveAdmission.cpp and every locking rule lives in
// WindowsReadLease.cpp. This file only bounds caller memory, maps exceptions
// to typed statuses, and composes bounded, path-free reason text.
#include "SaveAdmissionAbi.h"
#include "SaveAdmission.h"
#include "WindowsReadLease.h"
#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstring>
#include <memory>
#include <new>
#include <string>
#include <string_view>
#include <wchar.h>

static_assert(sizeof(wchar_t) == 2, "co-save path ABI assumes Windows UTF-16 wchar_t");
static_assert(sizeof(ensrick_admission_result) == 328);
static_assert(offsetof(ensrick_admission_result, reason) == 72);
static_assert(sizeof(ensrick_admission_result::reason) == ENSRICK_ADMISSION_REASON_BYTES);
#if defined(_WIN64)
static_assert(sizeof(ensrick_admission_plugin_name) == 16);
static_assert(sizeof(ensrick_admission_request) == 72);
#endif

using namespace Ensrick::SaveAdmission;

struct ensrick_admission_lease {
    WindowsReadLease reader;
    explicit ensrick_admission_lease(const std::filesystem::path& path) : reader(path) {}
};

namespace {
// Pre-read caps so a lying count cannot make the bridge walk an unbounded
// array. The core's ValidatePlugins stays authoritative; these only bound
// how far the bridge is willing to look before handing names to it.
constexpr std::uint32_t FullCap = 254, LightCap = 4096;
constexpr std::size_t NameScanBytes = 256;   // 255-byte name + NUL
constexpr std::size_t PathScanUnits = 32768; // 32767 units + NUL

struct Refusal {
    std::uint32_t status;
    std::string reason;
    std::uint32_t win32 = 0;
};

void SetReason(ensrick_admission_result& out, std::string_view text) noexcept {
    auto count = std::min(text.size(), sizeof(out.reason) - 1);
    // Never cut a UTF-8 sequence in half: back off to its lead byte.
    if (count < text.size())
        while (count && (static_cast<unsigned char>(text[count]) & 0xC0) == 0x80) --count;
    if (count) std::memcpy(out.reason, text.data(), count);
    out.reason[count] = 0;
}

std::uint32_t Win32From(std::string_view what) noexcept {
    // WindowsReadLease reports "Win32=<code>" and never a path.
    const auto at = what.find("Win32=");
    std::uint32_t code = 0;
    if (at != std::string_view::npos)
        std::from_chars(what.data() + at + 6, what.data() + what.size(), code);
    return code;
}

std::string NameFrom(const ensrick_admission_plugin_name& entry, const char* kind, std::uint32_t index) {
    if (entry.reserved) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "reserved name field must be zero"};
    const auto where = std::string(" for active ") + kind + " plugin " + std::to_string(index);
    if (!entry.utf8) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "null name" + where};
    if (!entry.capacity_bytes) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "empty name buffer" + where};
    const auto scan = std::min<std::size_t>(entry.capacity_bytes, NameScanBytes);
    const auto* end = static_cast<const char*>(std::memchr(entry.utf8, 0, scan));
    if (!end) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "unterminated or over-long name" + where};
    return std::string(entry.utf8, end);
}

std::filesystem::path CoSavePathFrom(const ensrick_admission_request& request) {
    if (!request.cosave_path_utf16 || !request.cosave_path_capacity_units)
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path is missing"};
    const auto scan = std::min<std::size_t>(request.cosave_path_capacity_units, PathScanUnits);
    std::size_t length = 0;
    while (length < scan && request.cosave_path_utf16[length]) ++length;
    if (length == scan) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path is unterminated or over-long"};
    if (!length) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path is empty"};
    std::wstring text(length, L'\0');
    for (std::size_t i = 0; i < length; ++i) text[i] = static_cast<wchar_t>(request.cosave_path_utf16[i]);
    std::filesystem::path path(std::move(text));
    if (!path.is_absolute()) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path must be absolute"};
    if (_wcsicmp(path.extension().c_str(), L".skse") != 0)
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "co-save path must end in .skse"};
    return path;
}

std::string ProblemText(const std::vector<std::string>& problems) {
    std::string text = std::to_string(problems.size()) + " plugin problem(s): ";
    for (std::size_t i = 0; i < problems.size(); ++i) {
        if (i) text += "; ";
        text += problems[i];
        if (text.size() >= ENSRICK_ADMISSION_REASON_BYTES) break; // SetReason truncates
    }
    return text;
}

void Admit(const ensrick_admission_request& request, ensrick_admission_result& out, ensrick_admission_lease** lease) {
    if (request.reserved) throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "reserved request field must be zero"};
    if (!request.ess_bytes || !request.ess_size)
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "save snapshot is missing"};
    if (request.ess_size > MaximumBytes)
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "save snapshot exceeds size limit"};
    if (!request.expected_fingerprint)
        throw Refusal{ENSRICK_ADMISSION_FINGERPRINT_UNAVAILABLE, "live currency fingerprint is unavailable; admission denied"};
    if (request.full_count > FullCap || request.light_count > LightCap)
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "active plugin counts exceed engine limits"};
    if ((request.full_count && !request.full_plugins) || (request.light_count && !request.light_plugins))
        throw Refusal{ENSRICK_ADMISSION_INVALID_ARGUMENT, "active plugin list is null"};
    const auto path = CoSavePathFrom(request);
    PluginTable active;
    for (std::uint32_t i = 0; i < request.full_count; ++i) active.full.push_back(NameFrom(request.full_plugins[i], "full", i));
    for (std::uint32_t i = 0; i < request.light_count; ++i) active.light.push_back(NameFrom(request.light_plugins[i], "light", i));
    SaveInfo save;
    try { save = ParseESS(Bytes(request.ess_bytes, static_cast<std::size_t>(request.ess_size))); }
    catch (const InvalidInput& e) { throw Refusal{ENSRICK_ADMISSION_MALFORMED_SAVE, e.what()}; }
    out.save_number = save.number;
    out.player_level = save.level;
    out.compression = save.compression;
    out.form_version = save.formVersion;
    out.saved_full_count = static_cast<std::uint32_t>(save.plugins.full.size());
    out.saved_light_count = static_cast<std::uint32_t>(save.plugins.light.size());
    std::vector<std::string> problems;
    // ParseESS already validated the saved table, so a refusal here concerns the active table.
    try { problems = ComparePlugins(save.plugins, active); }
    catch (const InvalidInput& e) { throw Refusal{ENSRICK_ADMISSION_ACTIVE_PLUGINS_INVALID, e.what()}; }
    if (!problems.empty()) {
        out.problem_count = static_cast<std::uint32_t>(problems.size());
        throw Refusal{ENSRICK_ADMISSION_PLUGIN_MISMATCH, ProblemText(problems)};
    }
    std::unique_ptr<ensrick_admission_lease> held;
    try { held = std::make_unique<ensrick_admission_lease>(path); }
    catch (const InvalidInput& e) { throw Refusal{ENSRICK_ADMISSION_LEASE_FAILED, e.what(), Win32From(e.what())}; }
    Checkpoint checkpoint;
    try { checkpoint = ParseCurrencyCheckpoint(held->reader.Data(), request.expected_fingerprint); }
    catch (const InvalidInput& e) { throw Refusal{ENSRICK_ADMISSION_COSAVE_REFUSED, e.what()}; } // `held` closes the lease
    out.checkpoint_fingerprint = checkpoint.fingerprint;
    out.checkpoint_value = checkpoint.value;
    out.checkpoint_backend = checkpoint.backend;
    out.checkpoint_physical = checkpoint.physical;
    *lease = held.release();
}
}

std::uint32_t ensrick_admission_abi_version(void) noexcept { return ENSRICK_ADMISSION_ABI_VERSION; }
std::uint64_t ensrick_admission_maximum_bytes(void) noexcept { return MaximumBytes; }

const char* ensrick_admission_status_name(std::uint32_t status) noexcept {
    switch (status) {
    case ENSRICK_ADMISSION_OK: return "admitted";
    case ENSRICK_ADMISSION_INVALID_ARGUMENT: return "invalid argument";
    case ENSRICK_ADMISSION_FINGERPRINT_UNAVAILABLE: return "fingerprint unavailable";
    case ENSRICK_ADMISSION_MALFORMED_SAVE: return "malformed save";
    case ENSRICK_ADMISSION_ACTIVE_PLUGINS_INVALID: return "active plugins invalid";
    case ENSRICK_ADMISSION_PLUGIN_MISMATCH: return "plugin mismatch";
    case ENSRICK_ADMISSION_LEASE_FAILED: return "lease failed";
    case ENSRICK_ADMISSION_COSAVE_REFUSED: return "co-save refused";
    case ENSRICK_ADMISSION_OUT_OF_MEMORY: return "out of memory";
    case ENSRICK_ADMISSION_INTERNAL_ERROR: return "internal error";
    default: return "unknown";
    }
}

std::uint32_t ensrick_admission_begin(const ensrick_admission_request* request,
    ensrick_admission_result* result, ensrick_admission_lease** lease) noexcept {
    if (lease) *lease = nullptr;
    if (!result || result->struct_size != sizeof(*result)) return ENSRICK_ADMISSION_INVALID_ARGUMENT;
    std::memset(result, 0, sizeof(*result));
    result->struct_size = sizeof(*result);
    const auto fail = [result](std::uint32_t status, std::string_view reason, std::uint32_t win32 = 0) noexcept {
        result->status = status;
        result->win32_error = win32;
        SetReason(*result, reason);
        return status;
    };
    if (!lease) return fail(ENSRICK_ADMISSION_INVALID_ARGUMENT, "lease output pointer is null");
    if (!request || request->struct_size != sizeof(*request) || request->abi_version != ENSRICK_ADMISSION_ABI_VERSION)
        return fail(ENSRICK_ADMISSION_INVALID_ARGUMENT, "request is missing or its size/ABI version does not match");
    try {
        Admit(*request, *result, lease);
        result->status = ENSRICK_ADMISSION_OK;
        return ENSRICK_ADMISSION_OK;
    } catch (const Refusal& refusal) {
        return fail(refusal.status, refusal.reason, refusal.win32);
    } catch (const std::bad_alloc&) {
        return fail(ENSRICK_ADMISSION_OUT_OF_MEMORY, "out of memory");
    } catch (...) {
        // Deliberately no e.what(): an unexpected message could carry a path.
        return fail(ENSRICK_ADMISSION_INTERNAL_ERROR, "unexpected internal error");
    }
}

void ensrick_admission_release(ensrick_admission_lease* lease) noexcept { delete lease; }

std::uint32_t ensrick_admission_lease_matches_handle(const ensrick_admission_lease* lease, void* borrowed) noexcept {
    return lease && lease->reader.MatchesHandle(borrowed) ? 1u : 0u;
}

std::uint32_t ensrick_admission_lease_cosave(const ensrick_admission_lease* lease,
    const std::uint8_t** data, std::uint64_t* size) noexcept {
    if (data) *data = nullptr;
    if (size) *size = 0;
    if (!lease || !data || !size) return ENSRICK_ADMISSION_INVALID_ARGUMENT;
    const auto bytes = lease->reader.Data();
    *data = bytes.data();
    *size = bytes.size();
    return ENSRICK_ADMISSION_OK;
}
