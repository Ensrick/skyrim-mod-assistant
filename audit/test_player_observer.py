# SPDX-License-Identifier: MIT
"""Adversarial unit tests for the read-only player observer. Mocked memory only.

Run from this directory:  py -3 -m unittest test_player_observer -v
No process, engine or game interaction.
"""
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import player_observer as po  # noqa: E402

BASE = 0x7FF6_1000_0000
MODULE_SIZE = 0x3400000
SINGLETON_RVA = 0x3230778
CONTROLS_RVA = 0x31A5690
PLAYER = 0x1D2A_4000_0000
CELL = 0x1D2A_4000_1000
WORLD = 0x1D2A_4000_2000
CONTROLS = 0x1D2A_4000_3000
POSITION = (-65133.664, 96466.03, -13887.999)


class FakeMemory:
    """Only exposes read(); anything else the observer tried would AttributeError."""

    def __init__(self):
        self.regions = {}
        self.calls = []
        self.hooks = {}

    def put(self, address, data):
        self.regions[address] = bytearray(data)

    def after(self, call_number, action):
        self.hooks[call_number] = action

    def read(self, address, size):
        self.calls.append((address, size))
        data = None
        for start, region in self.regions.items():
            if start <= address and address + size <= start + len(region):
                data = bytes(region[address - start:address - start + size])
        hook = self.hooks.pop(len(self.calls), None)
        if hook:
            hook()
        if data is None:
            raise OSError(299, 'ERROR_PARTIAL_COPY')
        return data


class IdentitySource:
    def __init__(self):
        self.current = po.ProcessIdentity(30340, r'C:\Games\SkyrimSE.exe', 'filetime:1', BASE, MODULE_SIZE)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.current


def build(mem, position=POSITION, state=0, cell=CELL, world=WORLD, flag_byte=0, player_id=0x14,
          player_type=0x3E, cell_type=0x3C, world_type=0x47, vtable_rva=po.PINNED.player_vtable_rva,
          water=po.FLT_MAX_LE, controls_vtable_rva=po.CANDIDATE.controls_vtable_rva):
    mem.put(BASE + SINGLETON_RVA, struct.pack('<Q', PLAYER))
    obj = bytearray(po.PINNED.player_span)
    struct.pack_into('<Q', obj, 0, BASE + vtable_rva)
    struct.pack_into('<I', obj, 0x14, player_id)
    obj[0x1A] = player_type
    struct.pack_into('<3f', obj, 0x54, *position)
    struct.pack_into('<Q', obj, 0x60, cell)
    struct.pack_into('<I', obj, 0xC8, state)
    mem.put(PLAYER, obj)
    cell_bytes = bytearray(po.PINNED.cell_span)
    struct.pack_into('<I', cell_bytes, 0x14, 0x92BC)
    cell_bytes[0x1A] = cell_type
    cell_bytes[0x40] = flag_byte
    cell_bytes[0x78:0x7C] = water
    struct.pack_into('<Q', cell_bytes, 0x128, world)
    mem.put(CELL, cell_bytes)
    world_bytes = bytearray(po.PINNED.header_span)
    struct.pack_into('<I', world_bytes, 0x14, 0x3C)
    world_bytes[0x1A] = world_type
    mem.put(WORLD, world_bytes)
    mem.put(BASE + CONTROLS_RVA, struct.pack('<Q', CONTROLS))
    controls = bytearray(po.CANDIDATE.controls_span)
    struct.pack_into('<Q', controls, 0, BASE + controls_vtable_rva)
    struct.pack_into('<ff', controls, 0x24, 0.0, 1.0)
    controls[0x48], controls[0x49], controls[0x1D9] = 1, 0, 0
    mem.put(CONTROLS, controls)
    return mem


def library_fixture():
    count = max(po.PINNED.player_singleton_id, po.CANDIDATE.controls_singleton_id) + 1
    data = bytearray(96 + count * 4)
    struct.pack_into('<5I', data, 0, 5, 1, 7, 104, 0)
    struct.pack_into('<ii', data, 84, 8, 0)
    struct.pack_into('<i', data, 92, count)
    struct.pack_into('<I', data, 96 + 4 * po.PINNED.player_singleton_id, SINGLETON_RVA)
    struct.pack_into('<I', data, 96 + 4 * po.CANDIDATE.controls_singleton_id, CONTROLS_RVA)
    return bytes(data)


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.mem = build(FakeMemory())
        self.ids = IdentitySource()

    def observer(self, **kwargs):
        return po.Observer(self.mem, self.ids, SINGLETON_RVA, **kwargs)

    def refused(self, report, code):
        self.assertEqual(report['status'], 'REFUSED', report)
        self.assertEqual(report['error']['code'], code, report['error'])
        return report['error']['detail']

    # -- happy path and shape ------------------------------------------------

    def test_verified_fields_and_json(self):
        report = self.observer().observe()
        self.assertEqual(report['status'], 'OK')
        sample = report['samples'][0]
        self.assertEqual(sample['player'], {'address': hex(PLAYER), 'formId': '00000014', 'formType': '0x3e',
                                            'vtableRva': hex(po.PINNED.player_vtable_rva)})
        for got, want in zip(sample['position'], POSITION):
            self.assertAlmostEqual(got, want, places=2)
        self.assertEqual(sample['cell']['formId'], '000092BC')
        self.assertFalse(sample['cell']['interior'])
        self.assertEqual(sample['world']['formId'], '0000003C')
        self.assertTrue(all(sample['stable'].values()))
        self.assertNotIn('candidate', sample)
        json.dumps(report)
        self.assertEqual(report['budget']['reads'], 8)  # 4 reads + 4 rechecks of the same addresses
        self.assertEqual(report['budget']['samples'], 1)

    def test_actor_state_masks_only(self):
        build(self.mem, state=0x400 | (2 << 21) | 0x8000_0000)
        state = self.observer().sample()['actorState']
        self.assertEqual(state['raw'], '0x80400400')
        self.assertEqual(state['lowMask0x3FFF'], 0x400)
        self.assertTrue(state['nativeBit0x400'])
        self.assertEqual(state['lifeStateField'], 2)
        self.assertFalse({'health', 'dead', 'combat', 'swimming'} & set(state))

    def test_interior_cell_without_worldspace(self):
        build(self.mem, world=0, flag_byte=0x81)
        sample = self.observer().sample()
        self.assertTrue(sample['cell']['interior'])
        self.assertIsNone(sample['world'])
        self.assertEqual(sample['status'], 'OK')

    def test_no_parent_cell_is_degraded_not_invented(self):
        build(self.mem, cell=0)
        sample = self.observer().sample()
        self.assertEqual(sample['status'], 'DEGRADED')
        self.assertIsNone(sample['cell'])
        self.assertIn('no-parent-cell', sample['degraded'])

    # -- pointer validity ----------------------------------------------------

    def test_null_singleton_pointer(self):
        self.mem.put(BASE + SINGLETON_RVA, bytes(8))
        self.refused(self.observer().observe(), 'null-pointer')

    def test_noncanonical_pointers(self):
        for value in (PLAYER + 4, 0x8, 0xFFFF_8000_0000_0000, po.USER_MAX + 1, 0xFFFF_FFFF_FFFF_FFFF):
            self.mem.put(BASE + SINGLETON_RVA, struct.pack('<Q', value))
            detail = self.refused(self.observer().observe(), 'noncanonical-pointer')
            self.assertEqual(detail['value'], hex(value))

    def test_noncanonical_cell_and_world_pointers(self):
        build(self.mem, cell=CELL + 1)
        self.refused(self.observer().observe(), 'noncanonical-pointer')
        build(self.mem, world=0xFFFF_0000_0000_0000)
        self.refused(self.observer().observe(), 'noncanonical-pointer')

    def test_rva_outside_module(self):
        for rva in (0, MODULE_SIZE, MODULE_SIZE - 4):
            with self.assertRaises(po.Refusal) as ctx:
                po.Observer(self.mem, self.ids, rva)
            self.assertEqual(ctx.exception.code, 'rva-out-of-module')

    # -- read failures -------------------------------------------------------

    def test_unreadable_target_is_structured(self):
        del self.mem.regions[CELL]
        detail = self.refused(self.observer().observe(), 'read-failed')
        self.assertEqual(detail['address'], hex(CELL))
        self.assertIn('ERROR_PARTIAL_COPY', detail['error'])

    def test_partial_read_is_refused(self):
        class Short(FakeMemory):
            def read(self, address, size):
                return super().read(address, size)[:-1]
        mem = build(Short())
        detail = self.refused(po.Observer(mem, self.ids, SINGLETON_RVA).observe(), 'short-read')
        self.assertEqual(detail['got'], 7)

    def test_wrong_read_type_is_refused(self):
        class Wrong(FakeMemory):
            def read(self, address, size):
                super().read(address, size)
                return 'x' * size
        self.refused(po.Observer(build(Wrong()), self.ids, SINGLETON_RVA).observe(), 'short-read')

    # -- identity ------------------------------------------------------------

    def test_wrong_vtable_form_id_and_form_type(self):
        for kwargs, code in (({'vtable_rva': 0x19296C8}, 'player-vtable-mismatch'),
                             ({'player_id': 0x15}, 'player-identity-mismatch'),
                             ({'player_type': 0x3D}, 'player-identity-mismatch'),
                             ({'cell_type': 0x3E}, 'cell-type-mismatch'),
                             ({'world_type': 0x3C}, 'world-type-mismatch')):
            build(self.mem, **kwargs)
            self.refused(self.observer().observe(), code)

    def test_process_identity_change_between_samples(self):
        observer = self.observer()
        first = observer.sample()
        self.assertEqual(first['status'], 'OK')
        self.ids.current = po.ProcessIdentity(30340, r'C:\Games\SkyrimSE.exe', 'filetime:2', BASE, MODULE_SIZE)
        detail = self.refused(observer.observe(2), 'process-identity-changed')
        self.assertEqual(detail['phase'], 'before')
        self.assertEqual(detail['observed']['start_time'], 'filetime:2')

    def test_identity_change_during_sample_is_caught_after(self):
        observer = self.observer()
        self.mem.after(3, lambda: setattr(self.ids, 'current', po.ProcessIdentity(1, 'x', 'y', BASE, MODULE_SIZE)))
        detail = self.refused(observer.observe(), 'process-identity-changed')
        self.assertEqual(detail['phase'], 'after')

    def test_identity_source_failure(self):
        class Broken:
            def __call__(self):
                raise RuntimeError('gone')
        with self.assertRaises(po.Refusal) as ctx:
            po.Observer(self.mem, Broken(), SINGLETON_RVA)
        self.assertEqual(ctx.exception.code, 'identity-unavailable')

    # -- churn preserved, not hidden ------------------------------------------

    def test_singleton_churn_marks_unstable_identity(self):
        self.mem.after(4, lambda: self.mem.put(BASE + SINGLETON_RVA, struct.pack('<Q', PLAYER + 0x100)))
        sample = self.observer().sample()
        self.assertEqual(sample['status'], 'DEGRADED')
        self.assertFalse(sample['stable']['identity'])
        self.assertEqual(sample['playerPointerAfter'], hex(PLAYER + 0x100))

    def test_position_churn_keeps_both_readings(self):
        def move():
            struct.pack_into('<3f', self.mem.regions[PLAYER], 0x54, 1.0, float('nan'), 3.0)
        self.mem.after(4, move)
        sample = self.observer().sample()
        self.assertFalse(sample['stable']['position'])
        self.assertAlmostEqual(sample['position'][0], POSITION[0], places=2)
        self.assertEqual(sample['positionAfter'][0], 1.0)
        self.assertIsNone(sample['positionAfter'][1])
        self.assertEqual(len(sample['positionAfterHex']), 24)
        self.assertIn('unstable-position', sample['degraded'])

    def test_cell_and_state_churn(self):
        def churn():
            struct.pack_into('<Q', self.mem.regions[PLAYER], 0x60, 0)
            struct.pack_into('<I', self.mem.regions[PLAYER], 0xC8, 0x400)
        self.mem.after(4, churn)
        sample = self.observer().sample()
        self.assertFalse(sample['stable']['cell'])
        self.assertFalse(sample['stable']['actorState'])
        self.assertEqual(sample['cellPointerAfter'], '0x0')
        self.assertEqual(sample['actorStateAfter'], '0x00000400')
        self.assertEqual(sample['cell']['formId'], '000092BC')

    def test_cell_data_churn_behind_unchanged_pointer(self):
        cases = {
            'formId': (lambda: struct.pack_into('<I', self.mem.regions[CELL], 0x14, 0x929B), 'formId', '0000929B'),
            'formType': (lambda: self.mem.regions[CELL].__setitem__(0x1A, 0x3E), 'formType', '0x3e'),
            'flagByte': (lambda: self.mem.regions[CELL].__setitem__(0x40, 0x01), 'flagByte', '0x1'),
            'worldPointer': (lambda: struct.pack_into('<Q', self.mem.regions[CELL], 0x128, WORLD + 0x100),
                             'worldPointer', hex(WORLD + 0x100)),
        }
        for name, (mutate, key, expected) in cases.items():
            with self.subTest(name):
                self.setUp()
                self.mem.after(4, mutate)
                sample = self.observer().sample()
                self.assertEqual(sample['status'], 'DEGRADED')
                self.assertTrue(sample['stable']['cell'])          # parent pointer itself unchanged
                self.assertFalse(sample['stable']['cellData'])
                self.assertIn('unstable-cellData', sample['degraded'])
                self.assertEqual(sample['cell']['formId'], '000092BC')  # first reading preserved
                self.assertEqual(sample['cellAfter'][key], expected)

    def test_world_header_churn_preserved(self):
        for mutate, key, expected in (
                (lambda: struct.pack_into('<I', self.mem.regions[WORLD], 0x14, 0x3D), 'formId', '0000003D'),
                (lambda: self.mem.regions[WORLD].__setitem__(0x1A, 0x3C), 'formType', '0x3c')):
            self.setUp()
            self.mem.after(4, mutate)
            sample = self.observer().sample()
            self.assertEqual(sample['status'], 'DEGRADED')
            self.assertFalse(sample['stable']['worldData'])
            self.assertTrue(sample['stable']['cellData'])
            self.assertEqual(sample['world']['formId'], '0000003C')
            self.assertEqual(sample['worldAfter'][key], expected)
            self.assertIn('unstable-worldData', sample['degraded'])

    def test_recheck_read_failure_is_refused_not_guessed(self):
        self.mem.after(4, lambda: self.mem.regions.pop(CELL))
        detail = self.refused(self.observer().observe(), 'read-failed')
        self.assertEqual(detail['what'], 'parent cell (recheck)')
        self.setUp()
        self.mem.after(4, lambda: self.mem.regions.pop(WORLD))
        detail = self.refused(self.observer().observe(), 'read-failed')
        self.assertEqual(detail['what'], 'worldspace (recheck)')

    def test_data_rechecks_not_applicable_are_none_not_degraded(self):
        build(self.mem, world=0)
        sample = self.observer().sample()
        self.assertTrue(sample['stable']['cellData'])
        self.assertIsNone(sample['stable']['worldData'])
        self.assertEqual(sample['status'], 'OK')
        build(self.mem, cell=0)
        sample = self.observer().sample()
        self.assertIsNone(sample['stable']['cellData'])
        self.assertEqual(sample['degraded'], ['no-parent-cell'])

    def test_lifetime_sample_budget_across_sample_and_observe(self):
        observer = self.observer(budget=po.Budget(max_samples=4))
        observer.sample()
        observer.sample()
        report = observer.observe(3)
        detail = self.refused(report, 'sample-limit')
        self.assertEqual(detail['remaining'], 2)
        self.assertEqual(report['samples'], [])
        self.assertEqual(observer.observe(2)['status'], 'OK')
        with self.assertRaises(po.Refusal) as ctx:
            observer.sample()
        self.assertEqual(ctx.exception.detail, {'samples': 4, 'max_samples': 4})
        self.assertEqual(observer.budget.samples, 4)
        self.assertEqual(len(self.mem.calls), 4 * 8)

    def test_refused_sample_attempts_still_consume_lifetime_budget(self):
        observer = self.observer(budget=po.Budget(max_samples=2))
        self.mem.put(BASE + SINGLETON_RVA, bytes(8))
        self.refused(observer.observe(), 'null-pointer')
        build(self.mem)
        self.assertEqual(observer.observe()['status'], 'OK')
        self.refused(observer.observe(), 'sample-limit')

    def test_report_degraded_when_any_sample_degraded(self):
        self.mem.after(10, lambda: struct.pack_into('<I', self.mem.regions[PLAYER], 0xC8, 1))
        report = self.observer().observe(2)
        self.assertEqual(report['status'], 'DEGRADED')
        self.assertEqual([s['status'] for s in report['samples']], ['OK', 'DEGRADED'])

    # -- coordinates -----------------------------------------------------------

    def test_nonfinite_or_implausible_coordinates(self):
        for position, axis in (((float('nan'), 0, 0), 'x'), ((0, float('inf'), 0), 'y'),
                               ((0, 0, -float('inf')), 'z'), ((0, 0, 2e8), 'z')):
            build(self.mem, position=position)
            detail = self.refused(self.observer().observe(), 'implausible-position')
            self.assertEqual(detail['axis'], axis)
            self.assertEqual(len(detail['raw']), 24)

    # -- budgets -----------------------------------------------------------------

    def test_read_budget_preserves_earlier_samples(self):
        report = self.observer(budget=po.Budget(max_reads=8)).observe(3)
        self.refused(report, 'budget-exhausted')
        self.assertEqual(len(report['samples']), 1)
        self.assertEqual(report['budget']['reads'], 8)
        self.assertEqual(len(self.mem.calls), 8)

    def test_byte_budget(self):
        report = self.observer(budget=po.Budget(max_bytes=0x80)).observe()
        detail = self.refused(report, 'budget-exhausted')
        self.assertEqual(detail['requested'], po.PINNED.player_span)
        self.assertEqual(len(self.mem.calls), 1)

    def test_sample_limit_and_zero_samples_read_nothing(self):
        for count in (0, -1, 17, True, 1.5, '2', None):
            self.refused(self.observer().observe(count), 'sample-limit')
        self.assertEqual(self.mem.calls, [])

    def test_read_size_ceiling(self):
        for size in (0, -1, po.MAX_READ + 1):
            with self.assertRaises(po.Refusal) as ctx:
                po.Budget().charge(size)
            self.assertEqual(ctx.exception.code, 'read-size')

    def test_invalid_intervals_refused_before_any_read(self):
        for interval in (float('nan'), float('inf'), -float('inf'), -0.001, -1, '1', None, True):
            detail = self.refused(self.observer().observe(2, interval=interval, sleep=lambda s: None), 'interval-invalid')
            self.assertEqual(detail['interval'], repr(interval))
        self.assertEqual(self.mem.calls, [])

    def test_interval_uses_injected_sleep_only_between_samples(self):
        slept = []
        self.observer().observe(3, interval=0.25, sleep=slept.append)
        self.assertEqual(slept, [0.25, 0.25])
        slept.clear()
        self.observer().observe(2, interval=0, sleep=slept.append)
        self.assertEqual(slept, [])

    # -- candidate section -------------------------------------------------------

    def test_candidate_section_labeled_and_isolated(self):
        sample = self.observer(include_candidate=True, controls_rva=CONTROLS_RVA).sample()
        candidate = sample['candidate']
        self.assertIn('Unvalidated', candidate['scope'])
        self.assertIn('NOT rechecked', candidate['scope'])
        self.assertIs(candidate['reread'], False)
        self.assertNotIn('candidate', sample['stable'])
        self.assertTrue(candidate['cellWaterHeightIsFltMax'])
        self.assertGreater(candidate['cellWaterHeight'], 3e38)  # FLT_MAX is finite; sentinel flagged, not nulled
        self.assertEqual(candidate['controls']['moveY'], 1.0)
        self.assertEqual(candidate['controls']['autoMove'], 1)
        self.assertEqual(sample['status'], 'OK')

    def test_candidate_controls_failure_does_not_drop_verified_sample(self):
        build(self.mem, controls_vtable_rva=0x1935078)
        sample = self.observer(include_candidate=True, controls_rva=CONTROLS_RVA).sample()
        self.assertEqual(sample['candidate']['controls']['error']['code'], 'controls-vtable-mismatch')
        self.assertEqual(sample['cell']['formId'], '000092BC')
        self.mem.put(BASE + CONTROLS_RVA, bytes(8))
        sample = self.observer(include_candidate=True, controls_rva=CONTROLS_RVA).sample()
        self.assertEqual(sample['candidate']['controls']['error']['code'], 'null-pointer')

    def test_candidate_budget_exhaustion_still_global(self):
        report = self.observer(include_candidate=True, controls_rva=CONTROLS_RVA,
                               budget=po.Budget(max_reads=5)).observe()
        self.refused(report, 'budget-exhausted')


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.ids = IdentitySource()

    def test_unknown_engine_or_library_never_reads_memory(self):
        class Untouchable:
            def read(self, address, size):
                raise AssertionError('must not read')
        with self.assertRaises(po.Refusal) as ctx:
            po.build_observer(Untouchable(), self.ids, b'unknown engine', library_fixture())
        self.assertEqual(ctx.exception.code, 'build-not-verified')
        self.assertEqual(ctx.exception.detail['failed'], ['exact engine identity', 'exact library identity'])

    def test_partial_check_failure_is_refused(self):
        checks = [{'name': 'a', 'pass': True}, {'name': 'position z assignment', 'pass': False}]
        with self.assertRaises(po.Refusal) as ctx:
            po.build_observer(FakeMemory(), self.ids, b'', library_fixture(), verify_fn=lambda e, l: checks)
        self.assertEqual(ctx.exception.detail['failed'], ['position z assignment'])
        with self.assertRaises(po.Refusal):
            po.build_observer(FakeMemory(), self.ids, b'', library_fixture(), verify_fn=lambda e, l: [])

    def test_verified_build_resolves_rvas_from_library(self):
        passing = lambda e, l: [{'name': 'x', 'pass': True}]
        mem = build(FakeMemory())
        observer = po.build_observer(mem, self.ids, b'', library_fixture(), verify_fn=passing, include_candidate=True)
        self.assertEqual(observer.singleton_rva, SINGLETON_RVA)
        self.assertEqual(observer.controls_rva, CONTROLS_RVA)
        self.assertEqual(observer.observe()['status'], 'OK')
        plain = po.build_observer(mem, self.ids, b'', library_fixture(), verify_fn=passing)
        self.assertIsNone(plain.controls_rva)

    def test_engine_override_must_be_the_observed_image(self):
        identity = self.ids()
        image = Path(identity.image_path)
        self.assertEqual(po.engine_path_for(identity, None), image)
        self.assertEqual(po.engine_path_for(identity, image), image)
        self.assertEqual(po.engine_path_for(identity, image.parent / '.' / image.name), image)
        for other in (image.with_name('other.exe'), Path('/tmp/SkyrimSE.exe'), image.parent):
            with self.assertRaises(po.Refusal) as ctx:
                po.engine_path_for(identity, other)
            self.assertEqual(ctx.exception.code, 'engine-path-mismatch')
            self.assertEqual(ctx.exception.detail['image_path'], identity.image_path)

    def test_build_for_process_loads_only_observed_image_and_rechecks_identity(self):
        loaded = []
        passing = lambda e, l: [{'name': 'x', 'pass': True}]
        mem = build(FakeMemory())

        def loader(path):
            loaded.append(path)
            return b'engine'
        observer = po.build_for_process(mem, self.ids, loader, library_fixture(), verify_fn=passing)
        self.assertEqual(loaded, [Path(self.ids.current.image_path)])
        self.assertEqual(observer.observe()['status'], 'OK')
        with self.assertRaises(po.Refusal) as ctx:
            po.build_for_process(mem, self.ids, loader, library_fixture(), verify_fn=passing,
                                 engine_override=Path('C:/elsewhere/SkyrimSE.exe'))
        self.assertEqual(ctx.exception.code, 'engine-path-mismatch')
        self.assertEqual(len(loaded), 1)  # mismatch refused before any bytes were loaded

        def restart_during_validation(path):
            self.ids.current = po.ProcessIdentity(30340, self.ids.current.image_path, 'filetime:9', BASE, MODULE_SIZE)
            return b'engine'
        with self.assertRaises(po.Refusal) as ctx:
            po.build_for_process(mem, self.ids, restart_during_validation, library_fixture(), verify_fn=passing)
        self.assertEqual(ctx.exception.code, 'process-identity-changed')
        self.assertEqual(ctx.exception.detail['phase'], 'validation')

    def test_library_offset_rejects_bad_tables(self):
        good = library_fixture()
        for bad in (good[:-1], good + b'\0', b'', bytes(96)):
            with self.assertRaises(po.Refusal):
                po.library_offset(bad, po.PINNED.player_singleton_id)
        with self.assertRaises(po.Refusal):
            po.library_offset(good, len(good))
        wrong_version = bytearray(good)
        struct.pack_into('<I', wrong_version, 12, 105)
        with self.assertRaises(po.Refusal):
            po.library_offset(bytes(wrong_version), po.PINNED.player_singleton_id)


if __name__ == '__main__':
    unittest.main()
