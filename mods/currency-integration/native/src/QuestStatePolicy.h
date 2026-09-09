#pragma once

namespace Ensrick::Currency
{
	// Pinned CommonLib90a64a4 IsRunning() omits the enabled-state test:
	// a fully stopped, non-promoting quest can return true. Require the
	// positive stopped-state contract AND no pending promotion instead.
	// Never admit a stage-waiting, enabled, unknown or promoting quest.
	template <class Quest>
	bool IsTransactionQuestQuiescent(const Quest* a_quest)
	{
		return a_quest && a_quest->IsStopped() && !a_quest->promoteTask;
	}
}
