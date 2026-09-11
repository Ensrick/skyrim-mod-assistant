cmake_minimum_required(VERSION 3.24)
# NAME_TBD: the mod's public name is the user's call and is not chosen yet.
# "VisibleEquipment" is the placeholder. A rename touches exactly these places:
#   this file (project(), NAME below, test/target names), src/main.cpp (log file
#   name, ini file name), VisibleEquipment.ini, README.md, build.ps1 (package
#   entries), .github/workflows/visible-equipment.yml, and the design doc
#   docs/VISIBLE-EQUIPMENT-PLUGIN-DESIGN-2026-09-10.md. Nothing else in the tree
#   hard-codes the name; the DLL is never referenced by other plugins.

# vcpkg manifest mode (vcpkg.json beside this file) supplies spdlog and the
# CommonLibSSE-NG dependencies. The toolchain must be known before project().
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE FILEPATH "vcpkg toolchain")
  else()
    message(FATAL_ERROR "Pass -DCMAKE_TOOLCHAIN_FILE=<vcpkg>/scripts/buildsystems/vcpkg.cmake or set VCPKG_ROOT")
  endif()
endif()
if(NOT DEFINED VCPKG_TARGET_TRIPLET)
  set(VCPKG_TARGET_TRIPLET "x64-windows-static" CACHE STRING "vcpkg triplet")
endif()
# Static CRT for every target in this tree, CommonLibSSE-NG included (CMP0091),
# so the plugin carries no vcpkg or CRT runtime DLLs.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>" CACHE STRING "MSVC runtime library")

# Four components: the version resource template needs a tweak number.
project(VisibleEquipment VERSION 0.0.1.0 LANGUAGES CXX)
if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "Requires Windows x64 MSVC")
endif()

# CommonLibSSE-NG is an external pinned checkout, never vendored. The reviewed
# revision is the same one MenuPilot, LaunchProbe and the 1.7.104 rebuilds use.
set(COMMONLIB_ROOT "" CACHE PATH "External CommonLibSSE-NG git checkout")
set(VISIBLE_EQUIPMENT_COMMONLIB_REVISION "70c1acd5261210982bd52f6d4468a082fe04d798"
    CACHE STRING "Reviewed CommonLibSSE-NG revision (6.7.1, alandtse/CommonLibSSE-NG)")
option(VISIBLE_EQUIPMENT_ALLOW_UNPINNED_COMMONLIB
       "Accept a CommonLibSSE-NG checkout other than the reviewed revision" OFF)
if(NOT EXISTS "${COMMONLIB_ROOT}/CMakeLists.txt")
  message(FATAL_ERROR "COMMONLIB_ROOT must point at a CommonLibSSE-NG checkout, got '${COMMONLIB_ROOT}'")
endif()
if(NOT VISIBLE_EQUIPMENT_ALLOW_UNPINNED_COMMONLIB)
  find_package(Git REQUIRED)
  execute_process(
    COMMAND "${GIT_EXECUTABLE}" rev-parse HEAD
    WORKING_DIRECTORY "${COMMONLIB_ROOT}"
    RESULT_VARIABLE commonlib_rev_result
    OUTPUT_VARIABLE commonlib_rev
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
  if(NOT commonlib_rev_result EQUAL 0)
    message(FATAL_ERROR "COMMONLIB_ROOT must be a git checkout at ${VISIBLE_EQUIPMENT_COMMONLIB_REVISION}")
  endif()
  if(NOT commonlib_rev STREQUAL VISIBLE_EQUIPMENT_COMMONLIB_REVISION)
    message(FATAL_ERROR "Unreviewed CommonLibSSE-NG revision ${commonlib_rev}; expected ${VISIBLE_EQUIPMENT_COMMONLIB_REVISION}")
  endif()
endif()

# 1.7.104 is an AE-family runtime. VR is out of scope; leaving it off drops the
# VR code paths from the build without changing the SE/AE layouts.
set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(SKSE_SUPPORT_XBYAK OFF CACHE BOOL "" FORCE)
add_subdirectory("${COMMONLIB_ROOT}" "${CMAKE_BINARY_DIR}/_deps/commonlib" EXCLUDE_FROM_ALL)
get_target_property(COMMONLIB_SRC_DIR CommonLibSSE SOURCE_DIR)
include("${COMMONLIB_SRC_DIR}/cmake/CommonLibSSE.cmake")

configure_file("${CMAKE_CURRENT_SOURCE_DIR}/cmake/version.rc.in" "${CMAKE_CURRENT_BINARY_DIR}/version.rc" @ONLY)

set(plugin_sources
  src/PCH.h
  src/main.cpp
  src/SlotRules.h
  "${CMAKE_CURRENT_BINARY_DIR}/version.rc")
source_group(TREE "${CMAKE_CURRENT_SOURCE_DIR}" FILES src/PCH.h src/main.cpp src/SlotRules.h)

# COMPATIBLE_RUNTIMES rather than USE_ADDRESS_LIBRARY: the exported
# SKSEPluginVersionData then carries versionIndependence 0 and an explicit
# 1.7.104 entry, the same declaration the sibling plugins make, because 1.7.104
# is the only runtime this code has been validated against. REL still resolves
# through the Address Library at run time (CommonLibSSE-NG 6.7.1 reads format 5).
add_commonlibsse_plugin(VisibleEquipment
  NAME "VisibleEquipment"
  AUTHOR "Ensrick"
  COMPATIBLE_RUNTIMES 1.7.104
  SOURCES ${plugin_sources})
target_precompile_headers(VisibleEquipment PRIVATE src/PCH.h)
target_include_directories(VisibleEquipment PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")

# The rule engine has no game types, so it is tested as a plain executable.
add_executable(SlotRulesTests tests/SlotRulesTests.cpp src/SlotRules.h)
target_include_directories(SlotRulesTests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")

foreach(target VisibleEquipment SlotRulesTests)
  target_compile_features(${target} PRIVATE cxx_std_23)
  target_compile_options(${target} PRIVATE /W4 /WX /permissive- /Zc:preprocessor /EHsc /utf-8 /Brepro)
  target_link_options(${target} PRIVATE /Brepro)
endforeach()

enable_testing()
add_test(NAME slot_rules COMMAND SlotRulesTests)
