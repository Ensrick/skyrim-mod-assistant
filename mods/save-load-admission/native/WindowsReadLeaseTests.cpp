// SPDX-License-Identifier: MIT
// Synthetic files in a newly created temporary directory only.
#include "WindowsReadLease.h"
#include <Windows.h>
#include <fstream>
#include <iostream>
using namespace Ensrick::SaveAdmission;
static unsigned checks;
static void Check(bool value) { ++checks; if (!value) throw std::runtime_error("read lease contract"); }
static void Write(const std::filesystem::path& path) {
    std::ofstream file(path, std::ios::binary); file << "synthetic";
    if (!file) throw std::runtime_error("cannot create fixture");
}
static HANDLE Open(const std::filesystem::path& path, DWORD access) {
    return CreateFileW(path.c_str(), access, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
}
int main() {
    const auto root = std::filesystem::temp_directory_path() /
        (L"ensrick-lease-" + std::to_wstring(GetCurrentProcessId()) + L"-" + std::to_wstring(GetTickCount64()));
    if (!std::filesystem::create_directory(root)) return 2;
    const auto save = root / L"test.ess", co = root / L"test.skse", other = root / L"other.ess";
    int result = 0;
    try {
        Write(save); Write(co); Write(other);
        const auto alreadyOpen = Open(save, GENERIC_READ);
        Check(alreadyOpen != INVALID_HANDLE_VALUE);
        {
            WindowsSavePairLease lease(save);
            Check(lease.Save().Data().size() == 9 && lease.CoSave().Data().size() == 9);
            Check(lease.Save().MatchesHandle(alreadyOpen));
            const auto another = Open(other, GENERIC_READ);
            Check(another != INVALID_HANDLE_VALUE);
            Check(!lease.Save().MatchesHandle(another)); CloseHandle(another);
            Check(!lease.Save().MatchesHandle(nullptr));
            Check(!lease.Save().MatchesHandle(INVALID_HANDLE_VALUE));
            for (const auto& path : {save, co}) {
                for (auto access : {GENERIC_WRITE, DELETE}) {
                    const auto attempt = Open(path, access);
                    const auto error = GetLastError();
                    if (attempt != INVALID_HANDLE_VALUE) CloseHandle(attempt);
                    Check(attempt == INVALID_HANDLE_VALUE && error == ERROR_SHARING_VIOLATION);
                }
                const auto reader = Open(path, GENERIC_READ);
                Check(reader != INVALID_HANDLE_VALUE); CloseHandle(reader);
            }
        }
        CloseHandle(alreadyOpen);
        auto writer = Open(save, GENERIC_WRITE);
        Check(writer != INVALID_HANDLE_VALUE);
        bool refused = false;
        try { WindowsSavePairLease lease(save); } catch (const InvalidInput&) { refused = true; }
        Check(refused); CloseHandle(writer);
        std::filesystem::remove(co);
        refused = false;
        try { WindowsSavePairLease lease(save); } catch (const InvalidInput&) { refused = true; }
        Check(refused);
        // Failure to open the second file must release the first file's lease.
        writer = Open(save, GENERIC_WRITE);
        Check(writer != INVALID_HANDLE_VALUE); CloseHandle(writer);
        refused = false;
        try { WindowsSavePairLease lease(L"relative.ess"); } catch (const InvalidInput&) { refused = true; }
        Check(refused);
        std::cout << checks << " Windows lease checks passed\n";
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; result = 1; }
    // Exact test-owned paths only; no recursive deletion.
    for (const auto& path : {save, co, other}) { std::error_code ec; std::filesystem::remove(path, ec); }
    { std::error_code ec; std::filesystem::remove(root, ec); }
    return result;
}
