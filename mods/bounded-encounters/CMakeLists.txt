cmake_minimum_required(VERSION 3.24)

project(BoundedEncounters VERSION 0.1.0 LANGUAGES CXX)

if(MSVC)
    add_compile_options("/experimental:deterministic" "/pathmap:${CMAKE_SOURCE_DIR}=.")
    add_link_options("/Brepro")
endif()

set(BUILD_TESTS OFF CACHE BOOL "Do not build CommonLib tests" FORCE)
set(ENABLE_SKYRIM_SE ON CACHE BOOL "Build Skyrim SE support" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "Build Skyrim AE support" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "VR is not currently supported" FORCE)
set(SKSE_SUPPORT_XBYAK ON CACHE BOOL "Enable trampoline support" FORCE)

add_subdirectory(extern/CommonLibSSE-NG)
include(extern/CommonLibSSE-NG/cmake/CommonLibSSE.cmake)
target_compile_definitions(CommonLibSSE PUBLIC COMMONLIBSSE_NO_MODAL_ERRORS=1)
find_package(nlohmann_json CONFIG REQUIRED)

add_library(BoundedEncountersCore STATIC
    src/Config.cpp
    src/Config.h
    src/SpawnModel.cpp
    src/SpawnModel.h
)
target_compile_features(BoundedEncountersCore PUBLIC cxx_std_23)
target_include_directories(BoundedEncountersCore PUBLIC src)
target_link_libraries(BoundedEncountersCore PUBLIC nlohmann_json::nlohmann_json)

add_commonlibsse_plugin(${PROJECT_NAME}
    AUTHOR "Ensrick"
    MINIMUM_SKSE_VERSION "2.3.1"
    COMPATIBLE_RUNTIMES "1.7.104.0"
    SOURCES
        src/PCH.h
        src/Plugin.cpp
        src/Classifier.cpp
        src/Classifier.h
        src/EncounterManager.cpp
        src/EncounterManager.h
        src/Version.h
)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_23)
target_precompile_headers(${PROJECT_NAME} PRIVATE src/PCH.h)
target_link_libraries(${PROJECT_NAME} PRIVATE BoundedEncountersCore)

add_executable(BoundedEncountersSim tools/Simulator.cpp)
target_compile_features(BoundedEncountersSim PRIVATE cxx_std_23)
target_link_libraries(BoundedEncountersSim PRIVATE BoundedEncountersCore)
set_target_properties(BoundedEncountersSim PROPERTIES OUTPUT_NAME "BoundedEncounters.Simulate")
add_dependencies(${PROJECT_NAME} BoundedEncountersSim)

add_executable(BoundedEncountersTests tests/SpawnModelTests.cpp)
target_compile_features(BoundedEncountersTests PRIVATE cxx_std_23)
target_link_libraries(BoundedEncountersTests PRIVATE BoundedEncountersCore)

enable_testing()
add_test(NAME SpawnModelTests COMMAND BoundedEncountersTests)

if(NOT DEFINED OUTPUT_FOLDER)
    set(OUTPUT_FOLDER "${CMAKE_BINARY_DIR}/stage")
endif()
set(DLL_FOLDER "${OUTPUT_FOLDER}/SKSE/Plugins")

add_custom_target(BoundedEncountersStage ALL
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${DLL_FOLDER}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "$<TARGET_FILE:${PROJECT_NAME}>" "${DLL_FOLDER}/$<TARGET_FILE_NAME:${PROJECT_NAME}>"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/config/BoundedEncounters.json" "${DLL_FOLDER}/BoundedEncounters.json"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/config/BoundedEncounters.schema.json" "${DLL_FOLDER}/BoundedEncounters.schema.json"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${OUTPUT_FOLDER}/tools"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "$<TARGET_FILE:BoundedEncountersSim>" "${OUTPUT_FOLDER}/tools/$<TARGET_FILE_NAME:BoundedEncountersSim>"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE" "${OUTPUT_FOLDER}/LICENSE"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${CMAKE_CURRENT_SOURCE_DIR}/README.md" "${OUTPUT_FOLDER}/README.md"
	DEPENDS ${PROJECT_NAME} BoundedEncountersSim
    VERBATIM)
