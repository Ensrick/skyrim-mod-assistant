#include "ClipLease.h"
#include <cstdio>
#include <cstdlib>
struct FakeApi {
    int rectangle{};
    bool foreground{true}, queryOk{true}, releaseOk{true}, confineOk{true}, loseDuringConfine{};
    unsigned releases{}, confines{};
    bool Query(int& value) noexcept { value = rectangle; return queryOk; }
    bool Equal(int a, int b) const noexcept { return a == b; }
    bool Foreground() const noexcept { return foreground; }
    bool Release() noexcept { ++releases; if (releaseOk) { rectangle = 0; } return releaseOk; }
    bool Confine(int value) noexcept {
        ++confines;
        if (loseDuringConfine) { foreground = false; }
        if (confineOk) { rectangle = value; }
        return confineOk;
    }
};
int main() {
    int checks{};
    const auto check = [&](bool ok) { if (++checks && !ok) { std::fprintf(stderr, "FAIL %d\n", checks); std::exit(1); } };
    FakeApi api;
    focus_guard::ClipLease<int> lease;
    lease.Release(api); check(api.releases == 0);
    lease.Confine(api, 1); check(lease.owned && api.rectangle == 1);
    lease.Confine(api, 1); check(api.confines == 1);
    api.foreground = false; api.queryOk = false;
    lease.Release(api); check(lease.owned && api.releases == 0);
    api.queryOk = true; api.releaseOk = false;
    lease.Release(api); check(lease.owned && api.releases == 1);
    api.releaseOk = true;
    lease.Release(api); check(!lease.owned && api.rectangle == 0);
    lease.Confine(api, 1); check(!lease.owned && api.confines == 1);
    api.foreground = true;
    lease.Confine(api, 1); api.foreground = false; api.rectangle = 99;
    const auto releases = api.releases;
    lease.Release(api); check(!lease.owned && api.rectangle == 99 && api.releases == releases);
    api.foreground = true; api.loseDuringConfine = true;
    lease.Confine(api, 1); check(!lease.owned && api.rectangle == 0);
    api.foreground = true; api.loseDuringConfine = false; api.confineOk = false;
    lease.Confine(api, 1); check(!lease.owned);
    for (int i = 0; i < 10000; ++i) { api.foreground = false; lease.Confine(api, 1); }
    check(!lease.owned && api.rectangle == 0);
    std::printf("PASS %d ownership/failure checks\n", checks);
}
