import hashlib
import unittest
from unittest.mock import patch

import prepare


class PreparationTests(unittest.TestCase):
    def test_unknown_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unreviewed source'):
            prepare.transform(b'not the reviewed vendor source')

    def fixture(self, copies=1):
        return ('function SelectLocation()\n' + (prepare.OLD + '\n') * copies
                + prepare.TRACE_ANCHOR + '\nendif\nendFunction\n').encode()

    def test_unique_pinned_transform_and_log(self):
        raw = self.fixture()
        with patch.object(prepare, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest()):
            result = prepare.transform(raw)
        self.assertNotIn(prepare.OLD, result)
        self.assertEqual(1, result.count(prepare.NEW))
        self.assertEqual(1, result.count(prepare.TRACE))
        self.assertIn('jailCandidate && HoldsWithJail.HasForm(jailCandidate)', result)
        self.assertIn('SuitableLocations.AddForm(jailCandidate)', result)
        self.assertIn('SuitableLocationsConditionless.AddForm(jailCandidate)', result)
        self.assertNotIn('Property ', result)

    def test_ambiguous_anchor_rejected_even_with_matching_hash(self):
        raw = self.fixture(copies=2)
        with patch.object(prepare, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'not unique'):
                prepare.transform(raw)

    def test_crlf_input_normalized(self):
        raw = self.fixture().replace(b'\n', b'\r\n')
        with patch.object(prepare, 'SOURCE_SHA256', hashlib.sha256(raw).hexdigest()):
            self.assertNotIn('\r', prepare.transform(raw))

    def test_candidate_policy_exhaustive_small_sets(self):
        # Policy reference, NOT execution of the compiled Papyrus.
        # 0=None, 1/2=jail holds, 3=Other, 4=custom non-jail hold.
        from itertools import combinations
        forms = range(5)
        for size in range(6):
            for selected in combinations(forms, size):
                accepted = [f for f in selected if f and f in {1, 2}]
                self.assertEqual(set(selected) & {1, 2}, set(accepted))
                self.assertNotIn(3, accepted)
                self.assertNotIn(4, accepted)


if __name__ == '__main__':
    unittest.main()
