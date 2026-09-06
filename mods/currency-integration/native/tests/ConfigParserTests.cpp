#include "Config.h"
#include "LedgerFingerprint.h"

#include <exception>
#include <filesystem>
#include <iostream>

int main(const int a_argc, const char* const* a_argv)
{
	if (a_argc != 2) {
		std::cerr << "usage: EnsrickCurrencyConfigTests <runtime-config.json>\n";
		return 2;
	}
	try {
		const auto config = Ensrick::Currency::LoadConfig(std::filesystem::path(a_argv[1]));
		if (config.owner != "EnsrickCurrencyDenominations" || config.families.size() != 9 ||
			!config.strictSingleOwner || !config.excludePhysicalFormsFromOrdinaryBarter ||
			config.excludePhysicalFormsFromDrop || config.disabledQuests.size() != 2) {
			std::cerr << "runtime config did not satisfy the reviewed bridge contract\n";
			return 1;
		}
		std::cout << "PASS: strict runtime config parsed with nine families and two ECE owners; ledgerFingerprint="
			<< std::hex << std::uppercase << Ensrick::Currency::ComputeLedgerFingerprint(config) << '\n';
		return 0;
	} catch (const std::exception& error) {
		std::cerr << error.what() << '\n';
		return 1;
	}
}
