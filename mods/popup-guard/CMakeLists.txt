cmake_minimum_required(VERSION 3.24)
# MinHook comes from vcpkg manifest mode (vcpkg.json beside this file). The
# toolchain must be known before project(); pass -DCMAKE_TOOLCHAIN_FILE or set
# VCPKG_ROOT. Static triplet keeps the plugin free of vcpkg runtime DLLs.
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
project(PopupGuard VERSION 0.1.0 LANGUAGES CXX)
if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "Requires Windows x64 MSVC")
endif()
set(SKSE_SDK_ROOT "" CACHE PATH "External pinned SKSE source checkout")
file(SHA256 "${SKSE_SDK_ROOT}/skse64/PluginAPI.h" sdk_hash)
if(NOT sdk_hash STREQUAL "0f238cc870c726a91befcf96f1c45db0019e223242434b8300b973ab2b0a3c95")
  message(FATAL_ERROR "Unexpected SKSE ABI header; review before updating pin")
endif()
find_package(minhook CONFIG REQUIRED)

add_library(PopupGuard SHARED PopupGuard.cpp PopupGuardCore.cpp)
# "!" sorts before every digit and letter in NTFS and MO2 virtual listings, so
# SKSE maps this plugin first (see README, load order).
set_target_properties(PopupGuard PROPERTIES OUTPUT_NAME "!PopupGuard" PREFIX "")
target_include_directories(PopupGuard PRIVATE "${SKSE_SDK_ROOT}")
target_link_libraries(PopupGuard PRIVATE minhook::minhook user32 shell32 ole32)

add_library(PopupHelperDll SHARED PopupHelperDll.cpp)
target_link_libraries(PopupHelperDll PRIVATE user32)
add_executable(PopupPolicyTests PopupPolicyTests.cpp)
add_executable(PopupHookTests PopupHookTests.cpp PopupGuardCore.cpp)
target_link_libraries(PopupHookTests PRIVATE minhook::minhook user32 version)
add_executable(PopupPluginLoadTests PopupPluginLoadTests.cpp)
target_include_directories(PopupPluginLoadTests PRIVATE "${SKSE_SDK_ROOT}")
target_link_libraries(PopupPluginLoadTests PRIVATE user32)

foreach(target PopupGuard PopupHelperDll PopupPolicyTests PopupHookTests PopupPluginLoadTests)
  target_compile_features(${target} PRIVATE cxx_std_20)
  target_compile_options(${target} PRIVATE /W4 /WX /permissive- /Brepro)
  target_link_options(${target} PRIVATE /Brepro)
  set_property(TARGET ${target} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endforeach()

enable_testing()
add_test(NAME line_policy COMMAND PopupPolicyTests)
add_test(NAME process_wide_hooks COMMAND PopupHookTests
  "$<TARGET_FILE_DIR:PopupHookTests>/PopupGuard-hooktest.log" "$<TARGET_FILE:PopupHelperDll>")
add_test(NAME plugin_dll_attach COMMAND PopupPluginLoadTests
  "$<TARGET_FILE:PopupGuard>" "$<TARGET_FILE_DIR:PopupGuard>/disabled-copy")
set_tests_properties(process_wide_hooks plugin_dll_attach PROPERTIES TIMEOUT 60)
