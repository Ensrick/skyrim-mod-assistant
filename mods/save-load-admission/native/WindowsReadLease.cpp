// SPDX-License-Identifier: MIT
#include "WindowsReadLease.h"
#include <algorithm>
#include <Windows.h>

namespace Ensrick::SaveAdmission {
namespace {
bool SameIdentity(const BY_HANDLE_FILE_INFORMATION& a, const BY_HANDLE_FILE_INFORMATION& b) noexcept {
    return a.dwVolumeSerialNumber == b.dwVolumeSerialNumber && a.nFileIndexHigh == b.nFileIndexHigh &&
        a.nFileIndexLow == b.nFileIndexLow && a.nFileSizeHigh == b.nFileSizeHigh && a.nFileSizeLow == b.nFileSizeLow &&
        a.ftLastWriteTime.dwHighDateTime == b.ftLastWriteTime.dwHighDateTime &&
        a.ftLastWriteTime.dwLowDateTime == b.ftLastWriteTime.dwLowDateTime;
}
std::filesystem::path ValidateSavePath(const std::filesystem::path& path) {
    if (!path.is_absolute() || _wcsicmp(path.extension().c_str(), L".ess") != 0)
        throw InvalidInput("expected an absolute ESS path");
    return path;
}
std::filesystem::path CoSavePath(const std::filesystem::path& path) {
    auto out = ValidateSavePath(path);
    out.replace_extension(L".skse");
    return out;
}
}

WindowsReadLease::WindowsReadLease(const std::filesystem::path& path) {
    if (!path.is_absolute()) throw InvalidInput("read lease requires absolute path");
    const auto handle = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (handle == INVALID_HANDLE_VALUE) throw InvalidInput("cannot acquire read-sharing lease, Win32=" + std::to_string(GetLastError()));
    // Constructor failure must release the handle too.
    try {
        BY_HANDLE_FILE_INFORMATION before{}, after{};
        if (GetFileType(handle) != FILE_TYPE_DISK || !GetFileInformationByHandle(handle, &before) ||
            (before.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) throw InvalidInput("unsupported input file type");
        const auto size = (std::uint64_t(before.nFileSizeHigh) << 32) | before.nFileSizeLow;
        if (size > MaximumBytes) throw InvalidInput("read lease input exceeds size limit");
        _data.resize(static_cast<std::size_t>(size));
        std::size_t offset = 0;
        while (offset < _data.size()) {
            const auto wanted = static_cast<DWORD>(std::min<std::size_t>(_data.size() - offset, 1024 * 1024));
            DWORD count = 0;
            if (!ReadFile(handle, _data.data() + offset, wanted, &count, nullptr) || !count)
                throw InvalidInput("read lease incomplete input");
            offset += count;
        }
        if (!GetFileInformationByHandle(handle, &after) || !SameIdentity(before, after))
            throw InvalidInput("input identity changed during read");
        _handle = handle;
    } catch (...) { CloseHandle(handle); throw; }
}
WindowsReadLease::~WindowsReadLease() { if (_handle) CloseHandle(_handle); }
bool WindowsReadLease::MatchesHandle(void* borrowed) const noexcept {
    BY_HANDLE_FILE_INFORMATION ours{}, other{};
    return _handle && borrowed && borrowed != INVALID_HANDLE_VALUE &&
        GetFileInformationByHandle(_handle, &ours) && GetFileInformationByHandle(borrowed, &other) && SameIdentity(ours, other);
}
WindowsSavePairLease::WindowsSavePairLease(const std::filesystem::path& path) :
    _save(ValidateSavePath(path)), _coSave(CoSavePath(path)) {}
}
