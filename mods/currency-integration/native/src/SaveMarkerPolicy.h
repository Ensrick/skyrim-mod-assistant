#pragma once

#include <cstdint>
#include <type_traits>

namespace Ensrick::Currency
{
	[[nodiscard]] constexpr std::uint32_t FourCC(
		const char a,
		const char b,
		const char c,
		const char d) noexcept
	{
		return static_cast<std::uint32_t>(static_cast<unsigned char>(a)) |
			(static_cast<std::uint32_t>(static_cast<unsigned char>(b)) << 8) |
			(static_cast<std::uint32_t>(static_cast<unsigned char>(c)) << 16) |
			(static_cast<std::uint32_t>(static_cast<unsigned char>(d)) << 24);
	}

	inline constexpr std::uint32_t SerializationID = FourCC('E', 'C', 'D', 'N');
	inline constexpr std::uint32_t SaveRecordType = FourCC('E', 'C', 'M', 'K');
	inline constexpr std::uint32_t SaveRecordVersion = 2;
	inline constexpr std::uint32_t SaveCheckpointMagic = FourCC('E', 'C', 'V', '2');
	inline constexpr std::uint64_t MaximumLedgerValue = 0x7FFFFFFFULL;

	// This is a logical checkpoint, not just an ownership marker.  The observed
	// counts let load admission preserve changes that occurred after the last
	// normalized baseline but before Skyrim serialized the inventory.
	struct SaveCheckpoint
	{
		std::uint32_t magic{ SaveCheckpointMagic };
		std::uint32_t schema{ 2 };
		std::uint64_t ledgerFingerprint{ 0 };
		std::uint64_t ledgerValue{ 0 };
		std::uint64_t observedBackend{ 0 };
		std::uint64_t observedPhysical{ 0 };
	};

	[[nodiscard]] constexpr bool IsRecognizedNativeSaveCheckpoint(
		const std::uint32_t a_type,
		const std::uint32_t a_version,
		const std::uint32_t a_length,
		const SaveCheckpoint& a_checkpoint) noexcept
	{
		return a_type == SaveRecordType && a_version == SaveRecordVersion &&
			a_length == sizeof(SaveCheckpoint) && a_checkpoint.magic == SaveCheckpointMagic &&
			a_checkpoint.schema == 2 && a_checkpoint.ledgerValue <= MaximumLedgerValue &&
			a_checkpoint.observedBackend <= MaximumLedgerValue &&
			a_checkpoint.observedPhysical <= MaximumLedgerValue;
	}

	[[nodiscard]] constexpr bool CheckpointMatchesLedger(
		const SaveCheckpoint& a_checkpoint,
		const std::uint64_t a_expectedFingerprint) noexcept
	{
		return a_expectedFingerprint != 0 &&
			a_checkpoint.ledgerFingerprint == a_expectedFingerprint;
	}

	static_assert(std::is_trivially_copyable_v<SaveCheckpoint>);
	static_assert(sizeof(SaveCheckpoint) == 40);
}
