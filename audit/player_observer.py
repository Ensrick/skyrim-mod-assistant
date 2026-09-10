# SPDX-License-Identifier: MIT
"""Read-only player observer for the pinned Skyrim 1.7.104 build (#267).

Reads the pinned Skyrim 1.7.104 player singleton through an injected reader and
reports position, parent cell/worldspace identities and the raw actor-state word
with only the masks that native code is known to apply. Every dereference is
budgeted, canonical-checked and size-bounded. Core fields are rechecked; every failure is a
structured refusal. Unknown values are reported as errors, never invented.

Non-claims, deliberately: samples are asynchronous observations, not atomic
engine snapshots; the read/byte budget bounds work, not wall-clock time, because
a blocking operating-system read can still stall; nothing here calls the engine,
writes memory, or interprets health/combat. Fields under 'candidate' (controls,
cell water height) are unvalidated layout data and are off by default.

Build acceptance reuses audit/player_layout_audit.verify, which pins the exact
engine MD5, library SHA256, address IDs and native byte sites. A version string
or an unverified CommonLib header is never sufficient.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO_ROOT / 'audit'
DEFAULT_LIBRARY = (REPO_ROOT.parent / 'mo2-instances' / 'skyrim-se' / 'mods' /
                   'Address Library' / 'SKSE' / 'Plugins' / 'versionlib-1-7-104-0.bin')

MAX_READ = 1024                 # per-read ceiling, mirrors ReadOnlyControlMap.Read
USER_MIN = 0x10000              # first 64 KiB of user space is never mapped
USER_MAX = 0x7FFF_FFFE_FFFF     # highest user-mode address on x64 Windows
POSITION_LIMIT = 1e8            # plausibility bound copied from the private probe
FLT_MAX_LE = b'\xff\xff\x7f\x7f'

SCOPE = ('Read-only asynchronous observation of pinned 1.7.104 fields. '
         'Samples are not atomic engine snapshots. The read/byte budget bounds work, '
         'not wall-clock time. No engine calls, memory writes, or health/combat '
         'interpretation. Candidate fields (controls, water height) are unvalidated '
         'layout data, not evidence of input, swimming or water level.')


class Refusal(Exception):
    """Structured, JSON-serializable failure. Code is stable; detail is evidence."""

    def __init__(self, code: str, message: str, **detail):
        super().__init__(f'{code}: {message}')
        self.code = code
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        return {'code': self.code, 'message': self.message, 'detail': self.detail}


class Reader(Protocol):
    def read(self, address: int, size: int) -> bytes: ...


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    image_path: str
    start_time: str
    base: int
    module_size: int


@dataclass(frozen=True)
class PinnedLayout:
    """Offsets backed by exact native byte sites in audit/player_layout_audit.py.

    Form-header offsets (form_id/form_type) are consistency gates that matched
    live (player 14/3E, cell 92BC/3C, world 3C/47); they are not native-byte
    verified and are used only to refuse, never to assert semantics.
    """
    player_singleton_id: int = 403521       # library ID -> RVA 0x3230778, checked by auditor
    player_vtable_rva: int = 0x19296C0      # library ID 208040, observed live
    position: int = 0x54                    # SetPosition x/y/z compare + assign sites
    parent_cell: int = 0x60                 # 'reference parent-cell read'
    actor_state: int = 0xC8                 # receiver +0xC0, reader mov eax,[rcx+8]
    actor_state_low_mask: int = 0x3FFF      # 'actor-state flag reader' and-mask
    actor_state_native_bit: int = 0x400     # edx passed by native input code
    life_state_mask: int = 0x01E00000       # 'native player life-state mask'
    life_state_shift: int = 21
    cell_flags: int = 0x40                  # 'cell interior-flag test', byte, bit 0
    cell_interior_bit: int = 0x1
    cell_worldspace: int = 0x128            # 'cell worldspace read'
    form_id: int = 0x14
    form_type: int = 0x1A
    player_form_id: int = 0x14
    player_form_type: int = 0x3E
    cell_form_type: int = 0x3C
    world_form_type: int = 0x47
    player_span: int = 0xD0
    cell_span: int = 0x130
    header_span: int = 0x20


@dataclass(frozen=True)
class CandidateLayout:
    """Unvalidated offsets, reported only under 'candidate' when enabled."""
    cell_water_height: int = 0x78
    controls_singleton_id: int = 400864
    controls_vtable_rva: int = 0x1935070    # library ID 208694; slot 1 -> 0x7AD900 verified
    controls_span: int = 0x1E0
    move_x: int = 0x24
    move_y: int = 0x28
    auto_move: int = 0x48
    running: int = 0x49
    blocked: int = 0x1D9


PINNED = PinnedLayout()
CANDIDATE = CandidateLayout()


@dataclass
class Budget:
    """Finite read/byte/sample budget for one Observer lifetime. Bounds work, not time."""
    max_reads: int = 160
    max_bytes: int = 256 * 1024
    max_samples: int = 16
    reads: int = 0
    bytes: int = 0
    samples: int = 0

    def charge_sample(self) -> None:
        if self.samples + 1 > self.max_samples:
            raise Refusal('sample-limit', 'lifetime sample budget exhausted',
                          samples=self.samples, max_samples=self.max_samples)
        self.samples += 1

    def charge(self, size: int) -> None:
        if not 1 <= size <= MAX_READ:
            raise Refusal('read-size', 'read size outside 1..MAX_READ', size=size, max_read=MAX_READ)
        if self.reads + 1 > self.max_reads or self.bytes + size > self.max_bytes:
            raise Refusal('budget-exhausted', 'read or byte budget exhausted', **self.to_dict(), requested=size)
        self.reads += 1
        self.bytes += size

    def to_dict(self) -> dict:
        return asdict(self)


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from('<Q', data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]


def _floats(raw: bytes) -> list:
    """Float32 triple as JSON-safe values; nonfinite becomes None, hex is kept alongside."""
    return [v if math.isfinite(v) else None for v in struct.unpack('<3f', raw)]


def library_offset(library: bytes, address_id: int) -> int:
    """Dense format-5 lookup for one ID. Same header rules as the auditor, kept independent."""
    if len(library) < 96 or struct.unpack_from('<5I', library) != (5, 1, 7, 104, 0):
        raise Refusal('library-format', 'unsupported or truncated address-library header')
    if struct.unpack_from('<ii', library, 84) != (8, 0):
        raise Refusal('library-format', 'unsupported pointer size or non-dense format')
    count = struct.unpack_from('<i', library, 92)[0]
    if count <= address_id or len(library) != 96 + count * 4:
        raise Refusal('library-format', 'ID outside dense table or bad length', address_id=address_id, count=count)
    return struct.unpack_from('<I', library, 96 + 4 * address_id)[0]


class Observer:
    """Holds one reader and one pinned process identity; produces structured samples."""

    def __init__(self, reader: Reader, identity_source: Callable[[], ProcessIdentity], singleton_rva: int, *,
                 budget: Optional[Budget] = None, controls_rva: Optional[int] = None,
                 include_candidate: bool = False, layout: PinnedLayout = PINNED,
                 candidate: CandidateLayout = CANDIDATE,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.reader = reader
        self.identity_source = identity_source
        self.budget = budget or Budget()
        self.layout = layout
        self.candidate = candidate
        self.include_candidate = include_candidate
        self.controls_rva = controls_rva
        self.now = now
        self.identity = self._current_identity('construct')
        for name, rva in (('player singleton', singleton_rva), ('controls singleton', controls_rva)):
            if rva is None:
                continue
            if not 0 < rva <= self.identity.module_size - 8:
                raise Refusal('rva-out-of-module', f'{name} RVA not inside main module',
                              rva=hex(rva), module_size=hex(self.identity.module_size))
        self.singleton_rva = singleton_rva

    # -- primitives --------------------------------------------------------

    def _current_identity(self, phase: str) -> ProcessIdentity:
        try:
            identity = self.identity_source()
        except Exception as error:  # identity source is injected; fail closed
            raise Refusal('identity-unavailable', 'process identity could not be read', phase=phase, error=repr(error))
        if not isinstance(identity, ProcessIdentity):
            raise Refusal('identity-unavailable', 'identity source returned wrong type', phase=phase)
        return identity

    def _recheck_identity(self, phase: str) -> None:
        current = self._current_identity(phase)
        if current != self.identity:
            raise Refusal('process-identity-changed', 'process identity differs from construction',
                          phase=phase, expected=asdict(self.identity), observed=asdict(current))

    @staticmethod
    def _require_canonical(value: int, what: str) -> None:
        if value == 0:
            raise Refusal('null-pointer', f'{what} is null', what=what)
        if value % 8 or not USER_MIN <= value <= USER_MAX:
            raise Refusal('noncanonical-pointer', f'{what} is not a canonical aligned user-mode address',
                          what=what, value=hex(value))

    def _read(self, address: int, size: int, what: str) -> bytes:
        self.budget.charge(size)
        self._require_canonical(address, what)
        if address + size - 1 > USER_MAX:
            raise Refusal('noncanonical-pointer', f'{what} span leaves user space', what=what, value=hex(address), size=size)
        try:
            data = self.reader.read(address, size)
        except Refusal:
            raise
        except Exception as error:  # ReadProcessMemory and mocks must fail safely
            raise Refusal('read-failed', f'{what} read failed', what=what, address=hex(address), size=size, error=repr(error))
        if not isinstance(data, (bytes, bytearray)) or len(data) != size:
            got = len(data) if isinstance(data, (bytes, bytearray)) else None
            raise Refusal('short-read', f'{what} read returned wrong length', what=what, address=hex(address), size=size, got=got)
        return bytes(data)

    def _header(self, data: bytes) -> tuple:
        return _u32(data, self.layout.form_id), data[self.layout.form_type]

    # -- observation -------------------------------------------------------

    def sample(self) -> dict:
        L = self.layout
        self.budget.charge_sample()   # lifetime budget: every attempt counts, refused or not
        self._recheck_identity('before')
        base = self.identity.base
        slot = base + self.singleton_rva
        player = _u64(self._read(slot, 8, 'player singleton slot'), 0)
        self._require_canonical(player, 'player pointer')
        obj = self._read(player, L.player_span, 'player object')

        vtable = _u64(obj, 0)
        if vtable - base != L.player_vtable_rva:
            raise Refusal('player-vtable-mismatch', 'player vtable is not the pinned RVA',
                          expected=hex(L.player_vtable_rva), observed=hex(vtable), base=hex(base))
        form_id, form_type = self._header(obj)
        if (form_id, form_type) != (L.player_form_id, L.player_form_type):
            raise Refusal('player-identity-mismatch', 'singleton does not carry the player form header',
                          form_id=f'{form_id:08X}', form_type=hex(form_type))

        pos_raw = obj[L.position:L.position + 12]
        position = struct.unpack('<3f', pos_raw)
        for axis, value in zip('xyz', position):
            if not math.isfinite(value) or abs(value) > POSITION_LIMIT:
                raise Refusal('implausible-position', f'{axis} is nonfinite or beyond plausibility bound',
                              axis=axis, raw=pos_raw.hex(), limit=POSITION_LIMIT)
        state = _u32(obj, L.actor_state)
        cell_ptr = _u64(obj, L.parent_cell)

        cell = world = cell_bytes = None
        if cell_ptr:
            self._require_canonical(cell_ptr, 'parent cell pointer')
            cell_bytes = self._read(cell_ptr, L.cell_span, 'parent cell')
            cell_id, cell_type = self._header(cell_bytes)
            if cell_type != L.cell_form_type:
                raise Refusal('cell-type-mismatch', 'parent cell header type is not CELL',
                              form_id=f'{cell_id:08X}', form_type=hex(cell_type))
            flag_byte = cell_bytes[L.cell_flags]
            cell = {'address': hex(cell_ptr), 'formId': f'{cell_id:08X}', 'flagByte': hex(flag_byte),
                    'interior': bool(flag_byte & L.cell_interior_bit)}
            world_ptr = _u64(cell_bytes, L.cell_worldspace)
            if world_ptr:
                self._require_canonical(world_ptr, 'worldspace pointer')
                world_bytes = self._read(world_ptr, L.header_span, 'worldspace')
                world_id, world_type = self._header(world_bytes)
                if world_type != L.world_form_type:
                    raise Refusal('world-type-mismatch', 'worldspace header type is not WRLD',
                                  form_id=f'{world_id:08X}', form_type=hex(world_type))
                world = {'address': hex(world_ptr), 'formId': f'{world_id:08X}'}

        candidate = self._candidate(base, cell_bytes) if self.include_candidate else None

        # Re-read the same addresses: detects churn, does not prove the first read was fresh.
        player_after = _u64(self._read(slot, 8, 'player singleton slot (recheck)'), 0)
        obj_after = self._read(player, L.player_span, 'player object (recheck)')
        stable = {
            'identity': player_after == player and _u64(obj_after, 0) == vtable
                        and self._header(obj_after) == (L.player_form_id, L.player_form_type),
            'position': obj_after[L.position:L.position + 12] == pos_raw,
            'cell': _u64(obj_after, L.parent_cell) == cell_ptr,
            'actorState': _u32(obj_after, L.actor_state) == state,
            'cellData': None,   # None = not applicable (no parent cell / no worldspace)
            'worldData': None,
        }
        # Dereferenced data is re-read at the SAME addresses so a churned cell/world
        # behind an unchanged pointer is still caught. Still not proof of freshness.
        cell_after = world_after = None
        if cell_bytes is not None:
            cell_bytes_after = self._read(cell_ptr, L.cell_span, 'parent cell (recheck)')
            cell_id_after, cell_type_after = self._header(cell_bytes_after)
            world_ptr_after = _u64(cell_bytes_after, L.cell_worldspace)
            cell_after = {'formId': f'{cell_id_after:08X}', 'formType': hex(cell_type_after),
                          'flagByte': hex(cell_bytes_after[L.cell_flags]), 'worldPointer': hex(world_ptr_after)}
            stable['cellData'] = (cell_id_after, cell_type_after, cell_bytes_after[L.cell_flags], world_ptr_after) == \
                                 (cell_id, cell_type, flag_byte, world_ptr)
            if world_ptr:
                world_bytes_after = self._read(world_ptr, L.header_span, 'worldspace (recheck)')
                world_id_after, world_type_after = self._header(world_bytes_after)
                world_after = {'formId': f'{world_id_after:08X}', 'formType': hex(world_type_after)}
                stable['worldData'] = (world_id_after, world_type_after) == (world_id, world_type)
        self._recheck_identity('after')

        degraded = [f'unstable-{name}' for name, ok in stable.items() if ok is False]
        if cell is None:
            degraded.append('no-parent-cell')
        result = {
            'status': 'OK' if not degraded else 'DEGRADED',
            'degraded': degraded,
            'observedUtc': self.now().isoformat(),
            'pid': self.identity.pid,
            'player': {'address': hex(player), 'formId': f'{form_id:08X}', 'formType': hex(form_type),
                       'vtableRva': hex(vtable - base)},
            'position': list(position),
            'positionHex': pos_raw.hex(),
            'cell': cell,
            'world': world,
            'actorState': {
                'raw': f'0x{state:08X}',
                'lowMask0x3FFF': state & L.actor_state_low_mask,
                'nativeBit0x400': bool(state & L.actor_state_native_bit),
                'lifeStateField': (state & L.life_state_mask) >> L.life_state_shift,
                'scope': 'Raw word and native-applied masks only; no health, death or combat semantics asserted.',
            },
            'stable': stable,
        }
        if not stable['position']:
            after_raw = obj_after[L.position:L.position + 12]
            result['positionAfter'] = _floats(after_raw)
            result['positionAfterHex'] = after_raw.hex()
        if not stable['actorState']:
            result['actorStateAfter'] = f'0x{_u32(obj_after, L.actor_state):08X}'
        if not stable['cell']:
            result['cellPointerAfter'] = hex(_u64(obj_after, L.parent_cell))
        if not stable['identity']:
            result['playerPointerAfter'] = hex(player_after)
        if stable['cellData'] is False:
            result['cellAfter'] = cell_after
        if stable['worldData'] is False:
            result['worldAfter'] = world_after
        if candidate is not None:
            result['candidate'] = candidate
        return result

    def _candidate(self, base: int, cell_bytes: Optional[bytes]) -> dict:
        C = self.candidate
        out = {'scope': 'Unvalidated layout data. Not evidence of input state, swimming or water level. '
                        'Read once per sample and NOT rechecked; no stability claim is made for these fields.',
               'reread': False}
        if cell_bytes is not None:
            raw = cell_bytes[C.cell_water_height:C.cell_water_height + 4]
            value = struct.unpack('<f', raw)[0]
            out['cellWaterHeight'] = value if math.isfinite(value) else None
            out['cellWaterHeightHex'] = raw.hex()
            out['cellWaterHeightIsFltMax'] = raw == FLT_MAX_LE
        if self.controls_rva is None:
            out['controls'] = {'error': Refusal('controls-rva-unavailable', 'no controls RVA supplied').to_dict()}
            return out
        try:
            ptr = _u64(self._read(base + self.controls_rva, 8, 'controls singleton slot'), 0)
            self._require_canonical(ptr, 'controls pointer')
            data = self._read(ptr, C.controls_span, 'controls object')
            vtable = _u64(data, 0)
            if vtable - base != C.controls_vtable_rva:
                raise Refusal('controls-vtable-mismatch', 'controls vtable is not the pinned RVA',
                              expected=hex(C.controls_vtable_rva), observed=hex(vtable))
            out['controls'] = {
                'address': hex(ptr),
                'moveX': _floats(data[C.move_x:C.move_x + 4] + b'\0' * 8)[0],
                'moveY': _floats(data[C.move_y:C.move_y + 4] + b'\0' * 8)[0],
                'autoMove': data[C.auto_move], 'running': data[C.running], 'blocked': data[C.blocked],
            }
        except Refusal as refusal:
            if refusal.code in ('null-pointer', 'noncanonical-pointer', 'read-failed', 'short-read',
                                'controls-vtable-mismatch'):
                out['controls'] = {'error': refusal.to_dict()}   # candidate failure never hides verified data
            else:
                raise                                             # budget/identity refusals are global
        return out

    def observe(self, samples: int = 1, interval: float = 0.0, sleep: Callable[[float], None] = time.sleep) -> dict:
        report = {'status': None, 'pid': self.identity.pid, 'singletonRva': hex(self.singleton_rva),
                  'identity': asdict(self.identity), 'samples': [], 'scope': SCOPE}
        try:
            remaining = self.budget.max_samples - self.budget.samples
            if isinstance(samples, bool) or not isinstance(samples, int) or not 1 <= samples <= remaining:
                raise Refusal('sample-limit', 'requested sample count outside 1..remaining lifetime budget',
                              requested=samples, remaining=remaining, max_samples=self.budget.max_samples)
            if isinstance(interval, bool) or not isinstance(interval, (int, float)) \
                    or not math.isfinite(interval) or interval < 0:
                raise Refusal('interval-invalid', 'interval must be a finite non-negative number', interval=repr(interval))
            for index in range(samples):
                if index and interval > 0:
                    sleep(interval)
                report['samples'].append(self.sample())
            report['status'] = 'OK' if all(s['status'] == 'OK' for s in report['samples']) else 'DEGRADED'
        except Refusal as refusal:
            report['status'] = 'REFUSED'
            report['error'] = refusal.to_dict()
        report['budget'] = self.budget.to_dict()
        return report


# -- build acceptance ----------------------------------------------------------

def _auditor():
    try:
        if str(AUDIT_DIR) not in sys.path:
            sys.path.insert(0, str(AUDIT_DIR))
        import player_layout_audit
        return player_layout_audit
    except ImportError as error:
        raise Refusal('auditor-unavailable', 'audit/player_layout_audit.py not importable', path=str(AUDIT_DIR), error=str(error))


def build_observer(reader: Reader, identity_source: Callable[[], ProcessIdentity], engine: bytes, library: bytes, *,
                   verify_fn: Optional[Callable[[bytes, bytes], list]] = None, include_candidate: bool = False,
                   **kwargs) -> Observer:
    """Refuse unless the existing auditor passes every exact check; only then resolve RVAs."""
    verify = verify_fn or _auditor().verify
    checks = verify(engine, library)
    failed = [c.get('name') for c in checks if not c.get('pass')]
    if not checks or failed:
        raise Refusal('build-not-verified', 'engine/library failed exact-build verification',
                      failed=failed, checks=len(checks))
    singleton = library_offset(library, PINNED.player_singleton_id)
    controls = library_offset(library, CANDIDATE.controls_singleton_id) if include_candidate else None
    return Observer(reader, identity_source, singleton, controls_rva=controls,
                    include_candidate=include_candidate, **kwargs)


def engine_path_for(identity: ProcessIdentity, override: Optional[Path] = None) -> Path:
    """The engine bytes validated must be the observed process image; an override may only restate it."""
    image = Path(identity.image_path)
    if override is None:
        return image
    if os.path.normcase(str(Path(override).resolve())) != os.path.normcase(str(image.resolve())):
        raise Refusal('engine-path-mismatch', 'engine override does not resolve to the observed process image',
                      override=str(override), image_path=identity.image_path)
    return image


def build_for_process(reader: Reader, identity_source: Callable[[], ProcessIdentity],
                      engine_loader: Callable[[Path], bytes], library: bytes, *,
                      engine_override: Optional[Path] = None, **kwargs) -> Observer:
    """Portable wrapper: identity before validation, engine bytes from that image, identity after."""
    before = identity_source()
    engine = engine_loader(engine_path_for(before, engine_override))
    observer = build_observer(reader, identity_source, engine, library, **kwargs)
    if observer.identity != before:
        raise Refusal('process-identity-changed', 'process identity changed during build validation',
                      phase='validation', expected=asdict(before), observed=asdict(observer.identity))
    return observer


# -- live adapter (Windows, read-only) --------------------------------------

class WindowsReadOnlyReader:
    """Held process handle opened with QUERY_INFORMATION | VM_READ only.

    QUERY_INFORMATION (not just QUERY_LIMITED_INFORMATION) is required by
    EnumProcessModulesEx for main-module base/size; it is still read-only.
    No VM_WRITE or VM_OPERATION is ever requested.
    """
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    LIST_MODULES_64BIT = 0x03

    _MODULEINFO = None  # defined once, lazily, so non-Windows imports never touch wintypes

    @classmethod
    def _bind(cls):
        """Explicit restype/argtypes for every Win32 function used; HMODULE/HANDLE stay 64-bit wide."""
        import ctypes
        import ctypes.wintypes as wt
        if cls._MODULEINFO is None:
            class MODULEINFO(ctypes.Structure):
                _fields_ = (('lpBaseOfDll', wt.LPVOID), ('SizeOfImage', wt.DWORD), ('EntryPoint', wt.LPVOID))
            cls._MODULEINFO = MODULEINFO
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        signatures = (
            (k32.OpenProcess, wt.HANDLE, (wt.DWORD, wt.BOOL, wt.DWORD)),
            (k32.CloseHandle, wt.BOOL, (wt.HANDLE,)),
            (k32.ReadProcessMemory, wt.BOOL, (wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t,
                                              ctypes.POINTER(ctypes.c_size_t))),
            (k32.QueryFullProcessImageNameW, wt.BOOL, (wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))),
            (k32.GetProcessTimes, wt.BOOL, (wt.HANDLE,) + (ctypes.POINTER(wt.FILETIME),) * 4),
            (psapi.EnumProcessModulesEx, wt.BOOL, (wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD,
                                                   ctypes.POINTER(wt.DWORD), wt.DWORD)),
            (psapi.GetModuleInformation, wt.BOOL, (wt.HANDLE, wt.HMODULE, ctypes.POINTER(cls._MODULEINFO), wt.DWORD)),
        )
        for function, restype, argtypes in signatures:
            function.restype = restype
            function.argtypes = argtypes
        return ctypes, wt, k32, psapi

    def __init__(self, pid: int):
        self._ctypes, self._wt, self._k32, self._psapi = self._bind()
        ctypes, self.pid = self._ctypes, pid
        self._handle = self._k32.OpenProcess(self.PROCESS_QUERY_INFORMATION | self.PROCESS_VM_READ, False, pid)
        if not self._handle:
            raise Refusal('open-process', 'OpenProcess failed', pid=pid, error=ctypes.get_last_error())

    def read(self, address: int, size: int) -> bytes:
        if not 1 <= size <= MAX_READ:
            raise ValueError(f'size {size} outside 1..{MAX_READ}')
        buffer = self._ctypes.create_string_buffer(size)
        got = self._ctypes.c_size_t(0)
        ok = self._k32.ReadProcessMemory(self._handle, self._ctypes.c_void_p(address), buffer, size,
                                         self._ctypes.byref(got))
        if not ok or got.value != size:
            raise OSError(f'ReadProcessMemory failed: error={self._ctypes.get_last_error()} got={got.value}')
        return buffer.raw

    def identity(self) -> ProcessIdentity:
        ctypes, wt = self._ctypes, self._wt
        size = wt.DWORD(32768)
        path = ctypes.create_unicode_buffer(size.value)
        if not self._k32.QueryFullProcessImageNameW(self._handle, 0, path, ctypes.byref(size)):
            raise Refusal('identity-unavailable', 'QueryFullProcessImageNameW failed', error=ctypes.get_last_error())
        times = [wt.FILETIME() for _ in range(4)]
        if not self._k32.GetProcessTimes(self._handle, *(ctypes.byref(t) for t in times)):
            raise Refusal('identity-unavailable', 'GetProcessTimes failed', error=ctypes.get_last_error())
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        modules = (wt.HMODULE * 1)()
        needed = wt.DWORD(0)
        if not self._psapi.EnumProcessModulesEx(self._handle, modules, ctypes.sizeof(modules),
                                                ctypes.byref(needed), self.LIST_MODULES_64BIT) or not needed.value:
            raise Refusal('identity-unavailable', 'EnumProcessModulesEx failed', error=ctypes.get_last_error())
        info = self._MODULEINFO()
        if not self._psapi.GetModuleInformation(self._handle, modules[0], ctypes.byref(info), ctypes.sizeof(info)):
            raise Refusal('identity-unavailable', 'GetModuleInformation failed', error=ctypes.get_last_error())
        return ProcessIdentity(self.pid, path.value, f'filetime:{created}', int(info.lpBaseOfDll or 0),
                               int(info.SizeOfImage))

    def close(self) -> None:
        if self._handle:
            self._k32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pid', type=int)
    parser.add_argument('--library', type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument('--engine', type=Path, default=None,
                        help='optional; must resolve to the observed process image path, never another file')
    parser.add_argument('--samples', type=int, default=1)
    parser.add_argument('--interval', type=float, default=0.0)
    parser.add_argument('--candidate', action='store_true', help='include unvalidated controls/water fields')
    parser.add_argument('--max-reads', type=int, default=Budget.max_reads)
    parser.add_argument('--max-bytes', type=int, default=Budget.max_bytes)
    args = parser.parse_args(argv)
    if sys.platform != 'win32':
        report = {'status': 'REFUSED', 'error': Refusal('platform', 'live adapter is Windows-only').to_dict(), 'scope': SCOPE}
    else:
        try:
            with WindowsReadOnlyReader(args.pid) as reader:
                auditor = _auditor()
                library = auditor.bounded_read(args.library, 16 * 1024 * 1024)
                observer = build_for_process(
                    reader, reader.identity, lambda path: auditor.bounded_read(path, 64 * 1024 * 1024), library,
                    engine_override=args.engine, include_candidate=args.candidate,
                    budget=Budget(max_reads=args.max_reads, max_bytes=args.max_bytes))
                report = observer.observe(args.samples, args.interval)
        except Refusal as refusal:
            report = {'status': 'REFUSED', 'error': refusal.to_dict(), 'scope': SCOPE}
        except (OSError, ValueError) as error:
            report = {'status': 'REFUSED', 'error': {'code': 'input', 'message': str(error)}, 'scope': SCOPE}
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'OK' else 1


if __name__ == '__main__':
    raise SystemExit(main())
