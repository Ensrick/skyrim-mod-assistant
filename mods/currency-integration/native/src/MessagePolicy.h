#pragma once

#include <cstdint>

namespace Ensrick::Currency
{
	// SKSE's PostLoadGame message carries the bool result as the pointer value
	// itself (nullptr/0x1), with dataLen == 1. It is not a pointer to bool.
	[[nodiscard]] constexpr bool PostLoadSucceeded(
		const void* a_data,
		const std::uint32_t a_dataLength) noexcept
	{
		return a_dataLength == 1 && a_data != nullptr;
	}
}
