from __future__ import annotations

import argparse
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weapon_timing as timing


def object_index(root: ET.Element) -> dict[str, ET.Element]:
    return {
        obj.get("name", ""): obj
        for obj in root.findall(".//hkobject")
        if obj.get("name")
    }


class RateTests(unittest.TestCase):
    def test_positive_finite_rate(self) -> None:
        self.assertEqual(timing.parse_rate("current=1.2"), ("current", 1.2))

    def test_non_finite_rates_are_rejected(self) -> None:
        for value in ("x=nan", "x=inf", "x=-inf"):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                timing.parse_rate(value)

    def test_duplicate_labels_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate rate label"):
            timing.rates_from_pairs([("same", 1.0), ("same", 1.5)])


class EventTableTests(unittest.TestCase):
    def test_resolves_referenced_table_not_longest_table(self) -> None:
        root = ET.fromstring(
            """
            <hkpackfile><hksection>
              <hkobject name="#graph" class="hkbBehaviorGraph">
                <hkparam name="data">#data</hkparam>
              </hkobject>
              <hkobject name="#data" class="hkbBehaviorGraphData">
                <hkparam name="stringData">#wanted</hkparam>
              </hkobject>
              <hkobject name="#wanted" class="hkbBehaviorGraphStringData">
                <hkparam name="eventNames"><hkcstring>HitFrame</hkcstring></hkparam>
              </hkobject>
              <hkobject name="#stray" class="hkbBehaviorGraphStringData">
                <hkparam name="eventNames">
                  <hkcstring>wrong-a</hkcstring><hkcstring>wrong-b</hkcstring>
                </hkparam>
              </hkobject>
            </hksection></hkpackfile>
            """
        )
        self.assertEqual(timing.event_names(root, object_index(root)), ["HitFrame"])

    def test_distinct_referenced_tables_fail_closed(self) -> None:
        root = ET.fromstring(
            """
            <hkpackfile><hksection>
              <hkobject name="#graph-a" class="hkbBehaviorGraph">
                <hkparam name="data">#data-a</hkparam>
              </hkobject>
              <hkobject name="#graph-b" class="hkbBehaviorGraph">
                <hkparam name="data">#data-b</hkparam>
              </hkobject>
              <hkobject name="#data-a" class="hkbBehaviorGraphData">
                <hkparam name="stringData">#strings-a</hkparam>
              </hkobject>
              <hkobject name="#data-b" class="hkbBehaviorGraphData">
                <hkparam name="stringData">#strings-b</hkparam>
              </hkobject>
              <hkobject name="#strings-a" class="hkbBehaviorGraphStringData">
                <hkparam name="eventNames"><hkcstring>a</hkcstring></hkparam>
              </hkobject>
              <hkobject name="#strings-b" class="hkbBehaviorGraphStringData">
                <hkparam name="eventNames"><hkcstring>b</hkcstring></hkparam>
              </hkobject>
            </hksection></hkpackfile>
            """
        )
        with self.assertRaisesRegex(ValueError, "multiple event string tables"):
            timing.event_names(root, object_index(root))


if __name__ == "__main__":
    unittest.main()
