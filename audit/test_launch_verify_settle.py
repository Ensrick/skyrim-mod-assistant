"""Offline recurrence regressions; never start or modify Skyrim."""
import datetime
from pathlib import Path
import tempfile
import unittest

from launch_verify import decide, latest_load_observation, session_crash


class PostLoadEvidenceTests(unittest.TestCase):
    def verdict(self, **changes):
        state = dict(alive=True, elapsed=50, menu_at=29, save_at=49,
                     save_ok=True, state='at-menu', detail='success=1')
        state.update(changes)
        done, verdict, _ = decide(state, dict(menu_budget=60, save_budget=180))
        return verdict if done else None

    def test_success_callback_does_not_pass(self):
        self.assertIsNone(self.verdict())

    def test_observed_crash_one_second_after_load_fails(self):
        self.assertEqual(self.verdict(alive=False), 'FAIL')

    def test_full_settle_is_required(self):
        self.assertIsNone(self.verdict(elapsed=108.9))
        self.assertEqual(self.verdict(elapsed=109), 'PASS')

    def test_hang_and_failure_outrank_prior_success(self):
        self.assertEqual(self.verdict(elapsed=110, state='hung-spin'), 'FAIL')
        self.assertEqual(self.verdict(elapsed=110, save_ok=False), 'FAIL')

    def test_crash_handler_alive_cannot_pass(self):
        self.assertEqual(self.verdict(elapsed=110, crash_log='current.log'), 'FAIL')

    def test_crash_report_identity_and_freshness(self):
        start = datetime.datetime(2026, 9, 9, 20, 12).timestamp()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'crash-fixture.log'
            def report(pid, when):
                path.write_text(f'CRASH TIME: {when}\n\tProcess ID: {pid}\n')
                # The fixture's filesystem time must be fresh on future CI too.
                import os
                os.utime(path, (start + 70, start + 70))
            report(21424, '2026-09-09 20:12:50')
            self.assertEqual(session_crash(21424, start, temp), str(path))
            self.assertIsNone(session_crash(999, start, temp))
            report(21424, '2026-09-08 20:12:50')
            self.assertIsNone(session_crash(21424, start, temp))

    def test_matching_pid_bad_timestamp_cannot_be_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'crash-fixture.log'
            path.write_text('CRASH TIME: invalid\nProcess ID: 21424\n')
            self.assertIn('invalid crash timestamp', session_crash(21424, 0, temp))

    def test_menu_evidence_is_required(self):
        self.assertIsNone(self.verdict(menu_at=None, elapsed=50))
        self.assertEqual(self.verdict(menu_at=None, elapsed=110), 'FAIL')

    def test_reload_resets_prior_success(self):
        start = datetime.datetime(2026, 9, 9, 20, 12).timestamp()
        events = [dict(event='kPostLoadGame', rest='success=1',
                       wall='2026-09-09 20:12:49.000')]
        self.assertEqual(latest_load_observation(events, start), (49, True))
        events.append(dict(event='kPreLoadGame', rest='',
                           wall='2026-09-09 20:13:30.000'))
        self.assertEqual(latest_load_observation(events, start), (None, None))
        events.append(dict(event='kPostLoadGame', rest='success=1',
                           wall='2026-09-09 20:13:40.000'))
        self.assertEqual(latest_load_observation(events, start), (100, True))

    def test_failed_reload_is_not_previous_success(self):
        events = [dict(event='kPostLoadGame', rest='success=1',
                       wall='2026-09-09 20:12:49.000'),
                  dict(event='kPostLoadGame', rest='success=0',
                       wall='2026-09-09 20:12:50.000')]
        self.assertEqual(latest_load_observation(events, 0), (None, False))

    def test_malformed_latest_timestamp_invalidates_old_success(self):
        events = [dict(event='kPostLoadGame', rest='success=1',
                       wall='2026-09-09 20:12:49.000'),
                  dict(event='kPostLoadGame', rest='success=1', wall='invalid')]
        self.assertEqual(latest_load_observation(events, 0), (None, True))


if __name__ == '__main__':
    unittest.main()
