"""Pure unit tests; no game, no MO2 writes, no vendor input required."""
import unittest
import tempfile
import hashlib
from pathlib import Path
from cloak_exclusivity import (body_mask, directive, full_cloak, MASK, PELT_MASK,
                               MOD_NAME, RELATIVE_MANIFEST, check_installed,
                               conservative_addon_scope, expand_weight_models, validate_layer_proof)


class CloakExclusivityTests(unittest.TestCase):
    def test_numeric_and_symbolic_flags(self):
        self.assertEqual(body_mask("66560"), (1 << 10) | (1 << 16))
        self.assertEqual(body_mask("Hair, Circlet"), (1 << 1) | (1 << 12))
        self.assertEqual(body_mask("Body"), 4)

    def test_unknown_flags_fail_closed(self):
        for value in ("mystery", "", -1, 1 << 33):
            with self.assertRaises(ValueError):
                body_mask(value)

    def test_sons_collar_and_cuirass_excluded(self):
        for editor_id in ("0_Fur_Collar_Brown", "0_Fur_Collar_Brown_P", "ArmorStormcloakCuirass", "0_SC_Armor_Hide"):
            self.assertFalse(full_cloak("NW_Sons_of_Skyrim.esp", editor_id))
        for editor_id in ("0_Officer_Cloak", "0_Windhelm_Cloak_P", "0_Whiterun_Cloak_Ligth"):
            self.assertTrue(full_cloak("NW_Sons_of_Skyrim.esp", editor_id))

    def test_pelt_hood_is_not_cloak(self):
        self.assertTrue(full_cloak("Pelt Cloaks.esp", "TrimmedBearPeltCloakHeavyShort"))
        self.assertFalse(full_cloak("Pelt Cloaks.esp", "FurPeltHoodBear"))
        self.assertFalse(full_cloak("Pelt Cloaks.esp", "BearPeltMantle"))
        self.assertFalse(full_cloak("Pelt Cloaks.esp", "FurPeltMantle"))

    def test_only_three_more_scarves_capes(self):
        self.assertTrue(full_cloak("moe-scarves.esl", "_MOE_cape001AM"))
        for editor_id in ("_MOE_scarf001aAM", "_MOE_neck001AM", "_MOE_cape999AM"):
            self.assertFalse(full_cloak("moe-scarves.esl", editor_id))

    def test_scale_nord_collars_untouched(self):
        self.assertFalse(full_cloak("DIS_NordScale.esp", "DIS_FurCollar"))

    def test_union_preserves_every_original_bit(self):
        for mask in (66560, 65536, 45058, 47106, MASK):
            union = mask | MASK
            self.assertEqual(mask & union, mask)
            self.assertTrue(union & MASK)

    def test_sons_and_pelts_originally_do_not_conflict(self):
        self.assertEqual(66560 & PELT_MASK, 0)
        self.assertEqual((66560 | MASK) & (PELT_MASK | MASK), MASK)

    def test_add_only_slot_index_is_28_not_58(self):
        self.assertEqual(directive("005610:NW_Sons_of_Skyrim.esp"),
                         "filterByArmors=NW_Sons_of_Skyrim.esp|005610:bipedSlotsToAdd=28")
        with self.assertRaises(ValueError):
            directive("005610:SomeUnknownMod.esp")

    def test_cross_plugin_addon_sharing_rejected(self):
        declarations = [
            {"type": "ARMO", "formKey": "000001:Target.esp", "armatures": ["000002:Target.esp"]},
            {"type": "ARMO", "formKey": "000001:Other.esp", "armatures": ["000002:Target.esp"],
             "editorId": "Mantle", "provider": "Other.esp"},
        ]
        with self.assertRaisesRegex(ValueError, "excluded active declaration"):
            conservative_addon_scope({"declarations": declarations}, {"000001:target.esp"})

    def test_override_addon_links_are_included(self):
        declarations = [
            {"type": "ARMO", "formKey": "000001:Target.esp", "armatures": ["000002:Target.esp"]},
            {"type": "ARMO", "formKey": "000001:Target.esp", "armatures": ["000003:Override.esp"]},
            {"type": "ARMA", "formKey": "000002:Target.esp", "models": ["clothes/old.nif"]},
            {"type": "ARMA", "formKey": "000003:Override.esp", "models": ["clothes/new.nif"]},
        ]
        self.assertEqual(conservative_addon_scope({"declarations": declarations}, {"000001:target.esp"}),
                         {"meshes/clothes/old.nif", "meshes/clothes/new.nif"})

    def test_one_missing_allowlist_target_fails(self):
        declarations = [{"type": "ARMO", "formKey": "000001:Target.esp", "armatures": ["000002:Target.esp"]}]
        with self.assertRaisesRegex(ValueError, "absent from active plugins"):
            conservative_addon_scope({"declarations": declarations}, {"000001:target.esp", "000005:target.esp"})

    def test_weight_zero_companions_are_bound(self):
        self.assertEqual(expand_weight_models({"meshes/cloak_1.nif", "meshes/scarf.nif"}),
                         {"meshes/cloak_1.nif", "meshes/cloak_0.nif", "meshes/scarf.nif"})

    def test_enabled_missing_config_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            instance = Path(tmp) / "instance"
            profile = instance / "profiles/Default"
            profile.mkdir(parents=True)
            (profile / "modlist.txt").write_text("+" + MOD_NAME + "\n", encoding="utf-8")
            self.assertTrue(check_installed(instance, Path(tmp) / "Data"))

    def test_orphan_manifest_missing_config_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            instance = Path(tmp) / "instance"
            profile = instance / "profiles/Default"
            profile.mkdir(parents=True)
            (profile / "modlist.txt").write_text("+OtherOverlay\n", encoding="utf-8")
            manifest = instance / "mods/OtherOverlay" / RELATIVE_MANIFEST
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}", encoding="utf-8")
            self.assertTrue(check_installed(instance, Path(tmp) / "Data"))

    def test_proof_rejects_different_profile_and_missing_companion(self):
        proof = {"slot": 58, "status": "PASS", "profileFingerprint": {"plugins": ["old"]},
                 "assets": [{"relativePath": "meshes/cloak_1.nif", "state": "absent"}]}
        errors = validate_layer_proof(proof, [], {"plugins": ["new"]},
                                      {"meshes/cloak_1.nif", "meshes/cloak_0.nif"})
        self.assertEqual(len(errors), 2)

    def test_changed_mesh_same_mod_is_not_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mesh = root / "meshes/cloak.nif"
            mesh.parent.mkdir()
            mesh.write_bytes(b"original")
            proof = {"slot": 58, "status": "PASS", "profileFingerprint": {}, "assets": [
                {"relativePath": "meshes/cloak.nif", "state": "present", "providerKind": "loose",
                 "parseSucceeded": True, "partitionSlots": [46],
                 "sha256": hashlib.sha256(b"original").hexdigest().upper()}]}
            self.assertEqual(validate_layer_proof(proof, [root], {}, {"meshes/cloak.nif"}), [])
            mesh.write_bytes(b"changed")
            self.assertTrue(validate_layer_proof(proof, [root], {}, {"meshes/cloak.nif"}))

    def test_absence_sentinel_and_packed_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = {"slot": 58, "status": "PASS", "profileFingerprint": {}, "assets": [
                {"relativePath": "meshes/cloak.nif", "state": "absent"}]}
            self.assertEqual(validate_layer_proof(proof, [root], {}, {"meshes/cloak.nif"}), [])
            mesh = root / "meshes/cloak.nif"
            mesh.parent.mkdir()
            mesh.write_bytes(b"new")
            self.assertTrue(validate_layer_proof(proof, [root], {}, {"meshes/cloak.nif"}))
            archive = root / "Fixture.bsa"
            archive.write_bytes(b"original archive")
            proof["assets"][0] = {"relativePath": "meshes/cloak.nif", "state": "present", "providerKind": "bsa",
                                   "parseSucceeded": True, "partitionSlots": [46],
                                   "archiveName": "Fixture.bsa", "archiveSha256": hashlib.sha256(archive.read_bytes()).hexdigest().upper()}
            self.assertTrue(validate_layer_proof(proof, [root], {}, {"meshes/cloak.nif"}))

    def test_proof_path_cannot_escape_data_roots(self):
        proof = {"slot": 58, "status": "PASS", "profileFingerprint": {}, "assets": [
            {"relativePath": "../outside.nif", "state": "absent"}]}
        self.assertTrue(validate_layer_proof(proof, [], {}, {"../outside.nif"}))

    def test_contradictory_pass_does_not_override_partition_collision(self):
        proof = {"slot": 58, "status": "PASS", "profileFingerprint": {}, "assets": [
            {"relativePath": "meshes/cloak.nif", "state": "present", "providerKind": "loose",
             "sha256": "A" * 64, "parseSucceeded": True, "partitionSlots": [58]}]}
        self.assertTrue(any("already uses reserved partition" in error for error in
                            validate_layer_proof(proof, [], {}, {"meshes/cloak.nif"})))
        del proof["assets"][0]["parseSucceeded"]
        self.assertTrue(any("lacks successful parse" in error for error in
                            validate_layer_proof(proof, [], {}, {"meshes/cloak.nif"})))

    def test_malformed_proof_types_return_errors(self):
        for proof in (None, [], "PASS", {"slot": 58, "status": "PASS", "assets": {}},
                      {"slot": 58, "status": "PASS", "assets": [False]}):
            with self.subTest(proof=proof):
                self.assertTrue(validate_layer_proof(proof, [], {}, {"meshes/cloak.nif"}))


if __name__ == "__main__":
    unittest.main()
