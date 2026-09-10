// SPDX-License-Identifier: MIT
#pragma once
#include <atomic>
#include <cstdint>

namespace Ensrick::Currency {
// Read-only C ABI. Zero means that no successfully initialized identity has
// been published. A nonzero result identifies the configuration, NOT whether
// the current character/save is admitted or the whole mod package is valid.
inline constexpr char AdmissionFingerprintExportV1[] = "EnsrickCurrency_GetAdmissionFingerprintV1";
using GetAdmissionFingerprintV1 = std::uint64_t (*)() noexcept;

class PublishedAdmissionIdentity final {
public:
    void Publish(std::uint64_t fingerprint) noexcept {
        _fingerprint.store(fingerprint, std::memory_order_release);
    }
    [[nodiscard]] std::uint64_t Read() const noexcept {
        return _fingerprint.load(std::memory_order_acquire);
    }
private:
    std::atomic<std::uint64_t> _fingerprint{0};
};
// Constant-initialized module state: querying readiness must not construct
// the Bridge singleton, allocate collections or register anything.
inline constinit PublishedAdmissionIdentity g_publishedAdmissionIdentity;
}
