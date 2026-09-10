// SPDX-License-Identifier: MIT
#pragma once
#include "SaveAdmission.h"
#include <filesystem>

namespace Ensrick::SaveAdmission {
// Windows-only, read-sharing lease. Blocks ordinary writer/delete handles
// while alive. This is not protection against preexisting writable mappings
// or privileged mutation. Keep alive through the engine's actual reads.
class WindowsReadLease final {
public:
    explicit WindowsReadLease(const std::filesystem::path& absolutePath);
    ~WindowsReadLease();
    WindowsReadLease(const WindowsReadLease&) = delete;
    WindowsReadLease& operator=(const WindowsReadLease&) = delete;
    Bytes Data() const noexcept { return _data; }
    // The adapter must compare an already-open engine input handle, if any;
    // matching a pathname alone cannot prove it references this file object.
    bool MatchesHandle(void* borrowedHandle) const noexcept;
private:
    void* _handle{};
    std::vector<std::uint8_t> _data;
};

class WindowsSavePairLease final {
public:
    explicit WindowsSavePairLease(const std::filesystem::path& essPath);
    const WindowsReadLease& Save() const noexcept { return _save; }
    const WindowsReadLease& CoSave() const noexcept { return _coSave; }
private:
    WindowsReadLease _save;
    WindowsReadLease _coSave;
};
}
