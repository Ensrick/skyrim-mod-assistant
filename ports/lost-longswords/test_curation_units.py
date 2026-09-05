"""Original synthetic fixtures for the private curation verifier; no game inputs."""

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


_spec = importlib.util.spec_from_file_location(
    "lost_longswords_verifier", Path(__file__).with_name("test-private-curation.py"))
v = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v
_spec.loader.exec_module(v)


ITEM = "000100:Fixture.esm"
LIST = "000200:Fixture.esm"
PARENT = "000300:Fixture.esm"
CHILD = "000301:Fixture.esm"


def entry(form=ITEM, level=1, count=1):
    return {"referenceFormKey": form, "level": level, "count": count}


def npc(form, *, template=None, flags="", items=None):
    return {"formKey": form, "editorId": form, "templateFormKey": template,
            "templateFlags": flags, "items": items or [], "defaultOutfitFormKey": None}


def empty_policy():
    return {"vendorLeveledEdges": [], "excludedInternalEdges": [],
            "safeLeveledAdditions": [], "npcOperations": [],
            "containerOperations": [], "disabledConstructibleObjects": []}


class GraphTests(unittest.TestCase):
    def test_inventory_template_flag_controls_inheritance(self):
        actors = {
            PARENT.casefold(): npc(PARENT, items=[{"itemFormKey": ITEM, "count": 1}]),
            CHILD.casefold(): npc(CHILD, template=PARENT, flags="Inventory"),
        }
        reached = v.acquisition_ancestors({}, actors, {}, ITEM, set())
        self.assertIn(CHILD.casefold(), reached)
        actors[CHILD.casefold()]["templateFlags"] = "Traits"
        self.assertNotIn(CHILD.casefold(), v.acquisition_ancestors({}, actors, {}, ITEM, set()))

    def test_noninherited_raw_inventory_is_not_used(self):
        actors = {
            PARENT.casefold(): npc(PARENT),
            CHILD.casefold(): npc(CHILD, template=PARENT, flags="Inventory",
                                  items=[{"itemFormKey": ITEM, "count": 1}]),
        }
        self.assertNotIn(CHILD.casefold(), v.acquisition_ancestors({}, actors, {}, ITEM, set()))

    def test_empty_nullable_outfit_is_valid(self):
        outfits = {LIST.casefold(): {"formKey": LIST, "editorId": "Empty", "items": None}}
        self.assertEqual({}, v.acquisition_ancestors({}, {}, outfits, ITEM, set()))

    def test_leveled_cycles_terminate(self):
        other = "000201:Fixture.esm"
        lists = {
            LIST.casefold(): {"formKey": LIST, "entries": [entry(ITEM), entry(other)]},
            other.casefold(): {"formKey": other, "entries": [entry(LIST)]},
        }
        reached = v.acquisition_ancestors(lists, {}, {}, ITEM, set())
        self.assertEqual({LIST.casefold(), other.casefold()}, set(reached))

    def test_native_add_once_is_reference_only_and_preserves_input(self):
        lists = {LIST.casefold(): {"formKey": LIST, "entries": [entry(level=20, count=2)]}}
        original = copy.deepcopy(lists)
        policy = empty_policy()
        policy["safeLeveledAdditions"] = [{"target": LIST, "add": ITEM.lower(), "level": 1, "count": 1}]
        result = v.apply_leveled_policy(lists, policy, [])
        self.assertEqual(original, lists)
        self.assertEqual([entry(level=20, count=2)], result[LIST.casefold()]["entries"])

    def test_removal_is_case_insensitive_and_keeps_other_entries(self):
        other = "000101:Fixture.esm"
        lists = {LIST.casefold(): {"formKey": LIST, "entries": [entry(), entry(other)]}}
        policy = empty_policy()
        policy["vendorLeveledEdges"] = [{"target": LIST.lower(), "remove": ITEM.lower()}]
        result = v.apply_leveled_policy(lists, policy, [])
        self.assertEqual([entry(other)], result[LIST.casefold()]["entries"])
        self.assertEqual(2, len(lists[LIST.casefold()]["entries"]))

    def test_missing_removal_target_fails_closed(self):
        policy = empty_policy()
        policy["vendorLeveledEdges"] = [{"target": LIST, "remove": ITEM}]
        with self.assertRaises(AssertionError):
            v.apply_leveled_policy({}, policy, [])

    def test_npc_replacement_preserves_count_and_input(self):
        actors = {PARENT.casefold(): npc(PARENT, items=[{"itemFormKey": ITEM, "count": 3}])}
        before = copy.deepcopy(actors)
        policy = empty_policy()
        policy["npcOperations"] = [{"target": PARENT, "replace": ITEM, "with": LIST}]
        result = v.apply_npc_policy(actors, policy)
        self.assertEqual([{"itemFormKey": LIST, "count": 3}], result[PARENT.casefold()]["items"])
        self.assertEqual(before, actors)

    def test_missing_npc_replacement_fails_closed(self):
        policy = empty_policy()
        policy["npcOperations"] = [{"target": PARENT, "replace": ITEM, "with": LIST}]
        with self.assertRaises(AssertionError):
            v.apply_npc_policy({PARENT.casefold(): npc(PARENT)}, policy)

    def test_recipe_selector_matches_native_parser_name(self):
        policy = empty_policy()
        policy["disabledConstructibleObjects"] = [{"formKey": ITEM}]
        configs = v.expected_config_lines(policy)
        emitted = [line for lines in configs.values() for line in lines]
        self.assertEqual(["filterByCobjs=Fixture.esm|000100:workbenchKeyword=null"], emitted)

    def test_isolated_soldier_branch_does_not_reach_shared_guard_consumer(self):
        wanted = "000101:Fixture.esm"
        owned = "000800:FixturePatch.esp"
        guard = "000302:Fixture.esm"
        lists = {
            LIST.casefold(): {"formKey": LIST, "entries": [entry()]},
            owned.casefold(): {"formKey": owned, "entries": [entry(), entry(wanted)]},
        }
        actors = {
            PARENT.casefold(): npc(PARENT, items=[{"itemFormKey": LIST, "count": 1}]),
            CHILD.casefold(): npc(CHILD, template=PARENT, flags="Inventory"),
            guard.casefold(): npc(guard, items=[{"itemFormKey": LIST, "count": 1}]),
        }
        policy = empty_policy()
        policy["npcOperations"] = [{"target": PARENT, "replace": LIST, "with": owned}]
        patched = v.apply_npc_policy(actors, policy)
        reached = v.acquisition_ancestors(lists, patched, {}, wanted, set())
        self.assertIn(PARENT.casefold(), reached)
        self.assertIn(CHILD.casefold(), reached)
        self.assertNotIn(guard.casefold(), reached)
        self.assertEqual([entry()], lists[LIST.casefold()]["entries"])

    def test_explicit_child_replacement_accepts_only_proven_inherited_noop(self):
        actors = {
            PARENT.casefold(): npc(PARENT, items=[{"itemFormKey": ITEM, "count": 1}]),
            CHILD.casefold(): npc(CHILD, template=PARENT, flags="Inventory"),
        }
        policy = empty_policy()
        policy["npcOperations"] = [
            {"target": PARENT, "replace": ITEM, "with": LIST},
            {"target": CHILD, "replace": ITEM, "with": LIST, "allowInheritedNoOp": True},
        ]
        result = v.apply_npc_policy(actors, policy)
        self.assertEqual(LIST, result[PARENT.casefold()]["items"][0]["itemFormKey"])
        self.assertEqual([], result[CHILD.casefold()]["items"])

        for flags, template_items in (
            ("Traits", [{"itemFormKey": LIST, "count": 1}]),
            ("Inventory", [{"itemFormKey": ITEM, "count": 1}]),
            ("Inventory", []),
        ):
            with self.subTest(flags=flags, template_items=template_items):
                actors[CHILD.casefold()]["templateFlags"] = flags
                actors[PARENT.casefold()]["items"] = template_items
                child_only = empty_policy()
                child_only["npcOperations"] = policy["npcOperations"][1:]
                with self.assertRaises(AssertionError):
                    v.apply_npc_policy(actors, child_only)

    def test_inherited_noop_rejects_missing_or_cyclic_template(self):
        child_only = empty_policy()
        child_only["npcOperations"] = [
            {"target": CHILD, "replace": ITEM, "with": LIST, "allowInheritedNoOp": True}]
        actors = {CHILD.casefold(): npc(CHILD, template=PARENT, flags="Inventory")}
        with self.assertRaises(AssertionError):
            v.apply_npc_policy(actors, child_only)
        actors[PARENT.casefold()] = npc(PARENT, template=CHILD, flags="Inventory")
        with self.assertRaises(AssertionError):
            v.apply_npc_policy(actors, child_only)


if __name__ == "__main__":
    unittest.main()
