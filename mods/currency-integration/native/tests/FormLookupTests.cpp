#include "FormLookup.h"
#include <iostream>
#include <type_traits>

namespace
{
	struct Form
	{
		virtual ~Form() = default;
		template <class T> T* As() { return dynamic_cast<T*>(this); }
	};
	struct BoundObject : Form {};
	struct Misc : BoundObject {};
	struct Keyword : Form {};
	struct Handler
	{
		Form* value{};
		std::uint32_t lastID{};
		std::string_view lastPlugin;
		Form* LookupForm(std::uint32_t id, std::string_view plugin)
		{
			lastID = id;
			lastPlugin = plugin;
			return value;
		}
		// A compile-time regression tripwire: never call the exact-type overload.
		template <class T> T* LookupForm(std::uint32_t, std::string_view) = delete;
	};
}

int main()
{
	using Ensrick::Currency::LookupCompatibleForm;
	Misc gold;
	Keyword keyword;
	Handler handler;
	handler.value = &gold;
	int failures = 0;
	auto check = [&](bool ok) { if (!ok) { ++failures; } };
	check(LookupCompatibleForm<Form>(&handler, 15, "Skyrim.esm") == &gold);
	check(LookupCompatibleForm<BoundObject>(&handler, 15, "Skyrim.esm") == &gold);
	check(LookupCompatibleForm<Misc>(&handler, 15, "Skyrim.esm") == &gold);
	check(LookupCompatibleForm<Keyword>(&handler, 15, "Skyrim.esm") == nullptr);
	check(handler.lastID == 15 && handler.lastPlugin == "Skyrim.esm");
	handler.value = &keyword;
	check(LookupCompatibleForm<Keyword>(&handler, 1, "Example.esl") == &keyword);
	check(LookupCompatibleForm<BoundObject>(&handler, 1, "Example.esl") == nullptr);
	handler.value = nullptr;
	check(LookupCompatibleForm<Form>(&handler, 15, "Missing.esm") == nullptr);
	check(LookupCompatibleForm<Form>(static_cast<Handler*>(nullptr), 15, "Skyrim.esm") == nullptr);
	if (failures) {
		std::cerr << failures << " form lookup regression(s)\n";
		return 1;
	}
	std::cout << "PASS: nine base/concrete/null/wrong-type form lookup checks\n";
}
