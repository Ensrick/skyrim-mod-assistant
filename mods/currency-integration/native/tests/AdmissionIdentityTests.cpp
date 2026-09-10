// SPDX-License-Identifier: MIT
#include "AdmissionIdentity.h"
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <vector>

namespace {
    int failureMode = 0;
    unsigned stages = 0, checks = 0;
    void Check(bool value) {
        ++checks;
        if (!value) throw std::logic_error("identity publication contract failed");
    }
    void Stage(int n) {
        ++stages;
        Check(Ensrick::Currency::g_publishedAdmissionIdentity.Read() == 0);
        if (failureMode == n) throw std::runtime_error("injected initialization failure");
        if (failureMode == -n) throw n;
    }
}
namespace logger {
    template<class... Args> void info(Args...) { Stage(5); }
    template<class... Args> void critical(Args...) {}
}
namespace Ensrick::Currency {
    struct Config { const char* configID = "test"; };
    Config LoadConfig(const std::filesystem::path&) { Stage(1); return {}; }
    struct Bridge {
        std::atomic_bool _initialized{false};
        Config _config;
        std::vector<int> _families, _physicalValues;
        std::uint64_t _ledgerFingerprint{0};
        bool Initialize(const std::filesystem::path&);
        bool ResolveConfiguration() {
            Stage(2); _ledgerFingerprint = 123;
            return failureMode != 6;
        }
        bool InitializeQuickLoot() { Stage(3); return failureMode != 7; }
        void RegisterEventSinks() { Stage(4); }
        // No GetSingleton: accessor may not construct or access Bridge.
    };
    #include "identity-initialize.inc"
}
#include "identity-export.inc"
static_assert(std::is_same_v<decltype(&EnsrickCurrency_GetAdmissionFingerprintV1), Ensrick::Currency::GetAdmissionFingerprintV1>);

int main() {
    try {
        using namespace Ensrick::Currency;
        Check(EnsrickCurrency_GetAdmissionFingerprintV1() == 0);
        for (int mode = -5; mode <= 7; ++mode) {
            g_publishedAdmissionIdentity.Publish(0);
            failureMode = mode; stages = 0;
            Bridge bridge;
            const auto ok = bridge.Initialize("unused-mocked-path");
            Check(ok == (mode == 0));
            Check(bridge._initialized.load() == ok);
            Check(EnsrickCurrency_GetAdmissionFingerprintV1() == (ok ? 123u : 0u));
            if (!ok) {
                // Retry after each failed stage may publish only upon success.
                failureMode = 0;
                Check(bridge.Initialize("unused-mocked-retry"));
                Check(EnsrickCurrency_GetAdmissionFingerprintV1() == 123);
            }
            const auto completedStages = stages;
            failureMode = 1;
            Check(bridge.Initialize("already-initialized"));
            Check(stages == completedStages);
            Check(EnsrickCurrency_GetAdmissionFingerprintV1() == 123);
        }
        // Atomic reads of alternating 64-bit patterns must never tear.
        PublishedAdmissionIdentity identity;
        constexpr std::uint64_t a = 0xA5A5A5A55A5A5A5AULL;
        constexpr std::uint64_t b = 0x5A5A5A5AA5A5A5A5ULL;
        std::atomic_bool started{false}, stop{false}, bad{false};
        std::thread reader([&] {
            do {
                const auto value = identity.Read();
                if (value != 0 && value != a && value != b) bad.store(true);
                started.store(true);
            } while (!stop.load());
        });
        while (!started.load()) std::this_thread::yield();
        for (unsigned i = 0; i < 100000; ++i) identity.Publish(i % 2 ? a : b);
        stop.store(true); reader.join();
        Check(!bad.load());
        Check(identity.Read() == a);
        std::cout << checks << " production initialization/export checks and 100000 concurrent publications passed\n";
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
