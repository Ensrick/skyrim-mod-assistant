#pragma once

#include <cstdint>
#include <string_view>

namespace Ensrick::Currency
{
	// TESDataHandler::LookupForm<T> in the pinned CommonLib compares T::FORMTYPE
	// exactly. TESForm/TESBoundObject inherit FormType::None, so that overload
	// cannot resolve concrete records through either base type. Resolve first,
	// then use CommonLib's inheritance-aware, checked As<T> conversion.
	template <class T, class Handler>
	T* LookupCompatibleForm(Handler* a_handler, std::uint32_t a_localID, std::string_view a_plugin)
	{
		auto* form = a_handler ? a_handler->LookupForm(a_localID, a_plugin) : nullptr;
		return form ? form->template As<T>() : nullptr;
	}
}
