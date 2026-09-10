#pragma once
// Scratch-only shim for the IED feasibility compile (2026-09-10).
// The author's private 2023 framework evidently exposes __m128 operators
// before bullet3 is included (bullet is built with
// BT_NO_SIMD_OPERATOR_OVERLOADS in IED's vcxproj). We do not have that
// header; pull the DirectXMath ones into the global namespace instead.
#ifndef NTDDI_VERSION
#	define NTDDI_VERSION 0x0A000000
#endif
#ifndef _WIN32_WINNT
#	define _WIN32_WINNT 0x0A00
#endif
#include <DirectXMath.h>
using DirectX::operator+;
using DirectX::operator-;
using DirectX::operator*;
using DirectX::operator/;
using DirectX::operator+=;
using DirectX::operator-=;
using DirectX::operator*=;
using DirectX::operator/=;
