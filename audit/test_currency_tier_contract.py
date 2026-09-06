import copy
import unittest

import currency_tier_contract as gate


def config():
    return {"accounting": {"backendForm": "00000F:Skyrim.esm"}, "families": [{
        "id": "mede", "displayLabel": "Mede", "enabled": True,
        "denominations": [
            {"tier": tier, "value": value, "form": f"{0x800+i:06X}:Test.esp"}
            for i, (tier, value) in enumerate(gate.VALUES.items())]}]}


def sky_rules(data):
    return "\n".join(
        f"filterByMiscs=Test.esp|0x{int(item['form'].split(':')[0],16):x}:value={item['value']}:weight=0.01:fullName=~{item['tier'].title()} Mede~"
        for item in data["families"][0]["denominations"])


def complete_fixture():
    data = {"accounting": {"backendForm": "00000F:Skyrim.esm"}, "families": []}
    policy = {"denominations": {"tieredFamilies": []}}
    for i, (identity, primary) in enumerate(gate.DESIGNS.items()):
        silver, gold = gate.PREVIOUS_TIERS.get(identity, (
            f"{0xA00+2*i:06X}:{gate.PLUGIN}", f"{0xA01+2*i:06X}:{gate.PLUGIN}"))
        family = {"id": identity, "displayLabel": identity, "enabled": True,
                  "denominations": [{"tier": tier, "value": value, "form": key}
                                    for (tier, value), key in zip(gate.VALUES.items(),
                                                                  (primary, silver, gold))]}
        definition = {"id": identity, "primarySource": {"formKey": primary}, "tiers": {
            tier: {"formKey": key, "value": value, "name": f"{tier.title()} {identity}",
                   "model": f"Meshes\\Test\\{identity}_{tier}.nif"}
            for (tier, value), key in zip(gate.VALUES.items(), (primary, silver, gold))}}
        if identity in gate.ALIASES:
            family["inputAliases"] = [{"tier": tier, "form": key} for tier, key in gate.ALIASES[identity]]
            definition["sourceAliases"] = [{"normalizesToTier": tier, "formKey": key}
                                           for tier, key in gate.ALIASES[identity]]
        data["families"].append(family)
        policy["denominations"]["tieredFamilies"].append(definition)
    return policy, data


class TierContractTests(unittest.TestCase):
    def test_routes_pin_memberships_not_just_rule_names_and_design_union(self):
        routing = {"precedence": ["questExceptions", "regionalRoutes", "septimFallback"],
                   "rules": [{"id": identity, "anyKeywords": copy.deepcopy(keywords),
                              "familyIds": copy.deepcopy(families)}
                             for identity, keywords, families in gate.ROUTES]}
        gate.complete_routes({"routing": routing})
        for defect in ("swap families", "wrong keyword", "priority", "extra field"):
            candidate = copy.deepcopy(routing)
            rules = candidate["rules"]
            if defect == "swap families":
                rules[8]["familyIds"], rules[10]["familyIds"] = rules[10]["familyIds"], rules[8]["familyIds"]
            elif defect == "wrong keyword":
                rules[0]["anyKeywords"] = ["000001:Test.esp"]
            elif defect == "priority":
                rules.reverse()
            else:
                rules[0]["unreviewedScope"] = True
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                gate.complete_routes({"routing": candidate})

    def test_correct_named_tiers(self):
        data = config()
        gate.all_families(data)
        gate.skypatcher_values(data, [sky_rules(data)])

    def test_rejects_wrong_value_even_when_all_three_numbers_exist(self):
        data = config()
        tiers = data["families"][0]["denominations"]
        tiers[0]["value"], tiers[2]["value"] = 100, 1
        with self.assertRaisesRegex(ValueError, "copper must be worth 1"):
            gate.all_families(data)

    def test_rejects_old_silver_value_and_boolean(self):
        for value in (25, True, 10.0, "10"):
            data = config()
            data["families"][0]["denominations"][1]["value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                gate.all_families(data)

    def test_no_singleton_or_dormant_exemption(self):
        for enabled in (True, False):
            data = config()
            family = data["families"][0]
            family["enabled"] = enabled
            family["denominations"].pop()
            with self.subTest(enabled=enabled), self.assertRaises(ValueError):
                gate.all_families(data)
        data = config()
        data["families"][0]["legacySingleton"] = False
        with self.assertRaises(ValueError):
            gate.all_families(data)

    def test_rejects_reordered_duplicate_or_unknown_tiers(self):
        for defect in ("reorder", "duplicate", "unknown"):
            data = config()
            tiers = data["families"][0]["denominations"]
            if defect == "reorder":
                tiers.reverse()
            else:
                tiers[1]["tier"] = "copper" if defect == "duplicate" else "platinum"
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                gate.all_families(data)

    def test_alias_is_recognized_without_becoming_fourth_tier(self):
        data = config()
        data["families"][0]["inputAliases"] = [{"tier": "copper", "form": "000900:Test.esp"}]
        self.assertEqual(4, len(gate.all_families(data)[1]))
        self.assertEqual(3, len(data["families"][0]["denominations"]))

    def test_rejects_alias_form_collision_case_insensitively(self):
        data = config()
        data["families"][0]["inputAliases"] = [{"tier": "copper", "form": "800:TEST.ESP"}]
        with self.assertRaises(ValueError):
            gate.all_families(data)

    def test_rejects_backend_as_physical_coin(self):
        data = config()
        data["families"][0]["denominations"][0]["form"] = "f:SKYRIM.ESM"
        with self.assertRaises(ValueError):
            gate.all_families(data)

    def test_rejects_cross_design_form_reuse(self):
        data = config()
        other = copy.deepcopy(data["families"][0])
        other["id"] = "dram"
        data["families"].append(other)
        with self.assertRaises(ValueError):
            gate.all_families(data)

    def test_skypatcher_checks_value_on_same_exact_record(self):
        data = config()
        correct = sky_rules(data)
        wrong = correct.replace("value=1:", "value=100:", 1)
        # Values 1,10,100 elsewhere/comments do not repair the wrong MISC rule.
        with self.assertRaises(ValueError):
            gate.skypatcher_values(data, [wrong + "\n; value=1 value=10 value=100"])

    def test_skypatcher_rejects_missing_duplicate_and_wrong_name(self):
        data = config()
        correct = sky_rules(data)
        candidates = ["\n".join(correct.splitlines()[:-1]),
                      correct + "\n" + correct.splitlines()[0],
                      correct.replace("Silver Mede", "Gold Mede")]
        for text in candidates:
            with self.subTest(text=text), self.assertRaises(ValueError):
                gate.skypatcher_values(data, [text])

    def test_partial_design_list_cannot_claim_complete(self):
        with self.assertRaisesRegex(ValueError, "incomplete design coverage"):
            gate.complete_designs({}, config())

    def test_all_designs_and_alias_accounted_for(self):
        policy, data = complete_fixture()
        gate.complete_designs(policy, data)
        self.assertEqual(18, len(data["families"]))
        self.assertEqual(55, len(gate.all_families(data)[1]))

    def test_primary_source_cannot_be_just_decorative_metadata(self):
        policy, data = complete_fixture()
        policy["denominations"]["tieredFamilies"][0]["tiers"]["copper"]["formKey"] = "000F00:Other.esp"
        data["families"][0]["denominations"][0]["form"] = "000F00:Other.esp"
        with self.assertRaisesRegex(ValueError, "primary coin is not"):
            gate.complete_designs(policy, data)

    def test_old_silver_gold_ids_are_not_silently_replaced(self):
        policy, data = complete_fixture()
        policy["denominations"]["tieredFamilies"][0]["tiers"]["silver"]["formKey"] = "000F01:Other.esp"
        data["families"][0]["denominations"][1]["form"] = "000F01:Other.esp"
        with self.assertRaisesRegex(ValueError, "existing silver/gold FormKeys"):
            gate.complete_designs(policy, data)

    def test_missing_old_alias_is_a_coverage_failure(self):
        policy, data = complete_fixture()
        family = next(f for f in data["families"] if f["id"] == "gibber_mania")
        family["inputAliases"] = []
        with self.assertRaisesRegex(ValueError, "54 canonical tier forms"):
            gate.complete_designs(policy, data)

    def test_model_paths_cannot_be_a_single_shared_asset(self):
        policy, data = complete_fixture()
        tiers = policy["denominations"]["tieredFamilies"][0]["tiers"]
        tiers["gold"]["model"] = tiers["silver"]["model"]
        with self.assertRaisesRegex(ValueError, "share one model"):
            gate.complete_designs(policy, data)

    def test_model_paths_cannot_use_drive_or_root_relative_escape(self):
        for path in ("C:coin.nif", "\\coin.nif", "C:\\coin.nif", "..\\coin.nif"):
            policy, data = complete_fixture()
            policy["denominations"]["tieredFamilies"][0]["tiers"]["copper"]["model"] = path
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "invalid model path"):
                gate.complete_designs(policy, data)


if __name__ == "__main__":
    unittest.main()
