@echo off
setlocal EnableExtensions
call :main > "%~dp0build.log" 2>&1
exit /b %errorlevel%

:main
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" goto :fail
for /f "usebackq tokens=*" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "BE_VSROOT=%%I"
if not defined BE_VSROOT goto :fail
call "%BE_VSROOT%\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 goto :fail
if not defined BE_VCPKG_ROOT set "BE_VCPKG_ROOT=%USERPROFILE%\source\repos\vcpkg"
set "VCPKG_ROOT=%BE_VCPKG_ROOT%"
if not exist "%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake" goto :fail
set "BE_NINJA=%BE_VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
set "BE_CMAKE=%BE_VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set "BE_CTEST=%BE_VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe"
if not exist "%BE_NINJA%" goto :fail
if not exist "%BE_CMAKE%" goto :fail
if not exist "%BE_CTEST%" goto :fail
set "PATH=%BE_VSROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
if not defined CMAKE_BUILD_PARALLEL_LEVEL set "CMAKE_BUILD_PARALLEL_LEVEL=3"
if not defined VCPKG_MAX_CONCURRENCY set "VCPKG_MAX_CONCURRENCY=3"
cd /d "%~dp0.."
echo === CONFIGURE START ===
"%BE_CMAKE%" --fresh --preset release -DCMAKE_MAKE_PROGRAM="%BE_NINJA%" -DCOMMONLIB_PREBUILT=OFF -DENABLE_SKYRIM_VR=OFF
if errorlevel 1 goto :fail
echo === BUILD START ===
"%BE_CMAKE%" --build build/release
if errorlevel 1 goto :fail
echo === TEST START ===
"%BE_CTEST%" --test-dir build/release --output-on-failure
if errorlevel 1 goto :fail
echo === SIMULATOR SMOKE START ===
build\release\BoundedEncounters.Simulate.exe config\BoundedEncounters.json 4 12345 > build\release\simulation-smoke.json
if errorlevel 1 goto :fail
echo === BINARY AUDIT START ===
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File tools\audit-binary.ps1 > build\release\binary-audit.json
if errorlevel 1 goto :fail
echo === ALL_DONE ===
exit /b 0

:fail
echo ***BUILD_FAILED*** errorlevel %errorlevel%
exit /b 1
