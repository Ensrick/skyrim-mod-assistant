cmake_minimum_required(VERSION 3.24)

# Match the pinned Currency Swapper toolchain and x64-windows-static vcpkg
# dependencies; mixing /MD consumer objects with /MT dependencies is invalid.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

project(
	EnsrickCurrencyDenominations
	VERSION 0.2.3
	LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(COMMONLIBSSE_ROOT "" CACHE PATH "Exact CommonLibSSE-NG source checkout")
set(ENSRICK_COMMONLIB_COMMIT "90a64a4d65ce659a139137c968f42151bb6ecec9")

if(NOT IS_DIRECTORY "${COMMONLIBSSE_ROOT}")
	message(FATAL_ERROR "COMMONLIBSSE_ROOT must name the pinned CommonLibSSE checkout")
endif()

find_package(Git REQUIRED)
execute_process(
	COMMAND "${GIT_EXECUTABLE}" -C "${COMMONLIBSSE_ROOT}" rev-parse HEAD
	RESULT_VARIABLE commonlib_git_result
	OUTPUT_VARIABLE commonlib_git_head
	OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(NOT commonlib_git_result EQUAL 0 OR NOT commonlib_git_head STREQUAL ENSRICK_COMMONLIB_COMMIT)
	message(FATAL_ERROR
		"CommonLibSSE provenance mismatch: expected ${ENSRICK_COMMONLIB_COMMIT}, got '${commonlib_git_head}'")
endif()

add_executable(
	EnsrickCurrencyPolicyTests
	tests/NativePolicyTests.cpp
	src/DenominationMath.cpp
	src/LedgerFingerprint.cpp
	src/LedgerPolicy.cpp
)
target_include_directories(EnsrickCurrencyPolicyTests PRIVATE src)
target_compile_options(EnsrickCurrencyPolicyTests PRIVATE /W4 /WX)
enable_testing()
add_test(NAME EnsrickCurrencyPolicyTests COMMAND EnsrickCurrencyPolicyTests)

add_executable(EnsrickCurrencyFormLookupTests tests/FormLookupTests.cpp)
target_include_directories(EnsrickCurrencyFormLookupTests PRIVATE src)
target_compile_options(EnsrickCurrencyFormLookupTests PRIVATE /W4 /WX)
add_test(NAME EnsrickCurrencyFormLookupTests COMMAND EnsrickCurrencyFormLookupTests)
add_executable(EnsrickCurrencyQuestStateTests tests/QuestStateTests.cpp)
target_include_directories(EnsrickCurrencyQuestStateTests PRIVATE src)
target_compile_options(EnsrickCurrencyQuestStateTests PRIVATE /W4 /WX)
add_test(NAME EnsrickCurrencyQuestStateTests COMMAND EnsrickCurrencyQuestStateTests)

# Compile the actual initialization and exported accessor bodies against
# controlled collaborators; an early readiness publication must fail tests.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS src/Bridge.cpp src/Plugin.cpp)
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/Bridge.cpp" bridge_source)
string(FIND "${bridge_source}" "bool Bridge::Initialize(" identity_begin)
string(FIND "${bridge_source}" "bool Bridge::ResolveConfiguration(" identity_end)
if(identity_begin LESS 0 OR identity_end LESS identity_begin)
  message(FATAL_ERROR "Admission identity test extraction boundaries changed")
endif()
math(EXPR identity_length "${identity_end}-${identity_begin}")
string(SUBSTRING "${bridge_source}" ${identity_begin} ${identity_length} identity_body)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/identity-initialize.inc" "${identity_body}")
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/Plugin.cpp" plugin_source)
string(FIND "${plugin_source}" "extern \"C\" __declspec(dllexport) std::uint64_t EnsrickCurrency_GetAdmissionFingerprintV1()" export_begin)
string(FIND "${plugin_source}" "SKSEPluginLoad(" export_end)
if(export_begin LESS 0 OR export_end LESS export_begin)
  message(FATAL_ERROR "Admission identity export extraction boundaries changed")
endif()
math(EXPR export_length "${export_end}-${export_begin}")
string(SUBSTRING "${plugin_source}" ${export_begin} ${export_length} export_body)
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/identity-export.inc" "${export_body}")
add_executable(EnsrickCurrencyAdmissionIdentityTests tests/AdmissionIdentityTests.cpp)
target_include_directories(EnsrickCurrencyAdmissionIdentityTests PRIVATE src "${CMAKE_CURRENT_BINARY_DIR}")
target_compile_options(EnsrickCurrencyAdmissionIdentityTests PRIVATE /W4 /WX)
add_test(NAME EnsrickCurrencyAdmissionIdentityTests COMMAND EnsrickCurrencyAdmissionIdentityTests)

option(ENSRICK_BUILD_PLUGIN "Build the SKSE plugin in addition to pure policy tests" ON)
if(ENSRICK_BUILD_PLUGIN)
	# The runtime and structure choices are intentional and pinned to the user's
	# current Skyrim/SKSE build. This project installs nothing into the game.
	set(BUILD_TESTS OFF CACHE BOOL "Do not build CommonLib's own tests" FORCE)
	set(ENABLE_SKYRIM_SE OFF CACHE BOOL "Runtime 1.7.104 only" FORCE)
	set(ENABLE_SKYRIM_AE ON CACHE BOOL "Runtime 1.7.104 only" FORCE)
	set(ENABLE_SKYRIM_VR OFF CACHE BOOL "VR is not supported" FORCE)
	set(COMMONLIB_ENABLE_IPO OFF CACHE BOOL "Keep deterministic audit builds bounded" FORCE)
	set(SKSE_SUPPORT_PATCH_SAFETY OFF CACHE BOOL "No runtime patch sites are used" FORCE)
	add_compile_definitions(COMMONLIBSSE_NO_MODAL_ERRORS)
	add_subdirectory("${COMMONLIBSSE_ROOT}" CommonLibSSE EXCLUDE_FROM_ALL)
	# Source builds of the pinned CommonLib checkout do not include the consumer
	# helper themselves (its prebuilt branch does), so import it explicitly.
	include("${COMMONLIBSSE_ROOT}/cmake/CommonLibSSE.cmake")
	find_package(nlohmann_json CONFIG REQUIRED)

	add_executable(
		EnsrickCurrencyConfigTests
		tests/ConfigParserTests.cpp
		src/Config.cpp
		src/LedgerFingerprint.cpp
	)
	target_include_directories(EnsrickCurrencyConfigTests PRIVATE src)
	target_link_libraries(EnsrickCurrencyConfigTests PRIVATE nlohmann_json::nlohmann_json)
	target_compile_options(EnsrickCurrencyConfigTests PRIVATE /W4 /WX)

	add_commonlibsse_plugin(
		EnsrickCurrencyDenominations
		NAME "Ensrick Currency Denominations"
		AUTHOR "Ensrick"
		VERSION "${PROJECT_VERSION}"
		MINIMUM_SKSE_VERSION "2.3.1"
		COMPATIBLE_RUNTIMES "1.7.104"
		SOURCES
			src/Plugin.cpp
			src/Config.cpp
			src/Bridge.cpp
			src/DenominationMath.cpp
			src/LedgerFingerprint.cpp
			src/LedgerPolicy.cpp
	)
	target_include_directories(EnsrickCurrencyDenominations PRIVATE src "${CMAKE_CURRENT_SOURCE_DIR}")
	target_compile_definitions(EnsrickCurrencyDenominations PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
		ENSRICK_CURRENCY_VERSION="${PROJECT_VERSION}")
	target_link_libraries(EnsrickCurrencyDenominations PRIVATE nlohmann_json::nlohmann_json)
	target_precompile_headers(EnsrickCurrencyDenominations PRIVATE src/PCH.h)
	target_compile_options(EnsrickCurrencyDenominations PRIVATE /W4 /WX)
	target_link_options(EnsrickCurrencyDenominations PRIVATE
		"$<$<CONFIG:Release>:/INCREMENTAL:NO;/OPT:REF;/OPT:ICF;/Brepro>")
endif()
