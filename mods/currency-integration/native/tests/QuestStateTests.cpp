#include "QuestStatePolicy.h"
#include <cstdint>
#include <iostream>

struct Quest
{
	std::uint16_t flags{};
	bool promoteTask{};
	bool IsStopped() const { return (flags & 0x81) == 0; }
	bool IsRunning() const = delete;  // Do not reintroduce the pinned-library bug.
};

int main()
{
	using Ensrick::Currency::IsTransactionQuestQuiescent;
	if (IsTransactionQuestQuiescent<Quest>(nullptr)) return 1;
	// Exhaust the actual 16-bit flags and promotion states, including all-ones
	// stop/start sentinel; unrelated quest metadata must not change admission.
	for (std::uint32_t flags = 0; flags <= 0xFFFF; ++flags) {
		for (bool promoting : { false, true }) {
			Quest quest{ static_cast<std::uint16_t>(flags), promoting };
			const bool expected = !(flags & 1) && !(flags & 128) && !promoting;
			if (IsTransactionQuestQuiescent(&quest) != expected) return 2;
		}
	}
	std::cout << "PASS: 131072 quest-flag/promotion combinations and null rejection\n";
}
