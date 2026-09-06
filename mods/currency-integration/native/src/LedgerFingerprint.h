#pragma once

#include "Config.h"

#include <cstdint>

namespace Ensrick::Currency
{
	[[nodiscard]] std::uint64_t ComputeLedgerFingerprint(const Config& a_config);
}
