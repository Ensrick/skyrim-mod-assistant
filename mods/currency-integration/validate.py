#!/usr/bin/env python3
"""Static regression gate for the Ensrick regional-currency configuration."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "package"
CDF = PACKAGE / "SKSE" / "Plugins" / "ContainerDistributionFramework"
REPO = ROOT.parent.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_jsonc(text: str) -> object:
    """Parse CDF's JSON-with-comments without damaging comment-like text in strings."""
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < len(text) and text[index + 1] == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and index + 1 < len(text) and text[index + 1] == "*":
            index += 2
            while index + 1 < len(text) and text[index:index + 2] != "*/":
                index += 1
            require(index + 1 < len(text), "unterminated JSONC block comment")
            index += 2
            continue
        output.append(char)
        index += 1
    return json.loads("".join(output))


def pex_header_strings(data: bytes) -> tuple[str, str, str]:
    offset = 16
    values: list[str] = []
    for label in ("source-name", "user-name", "machine-name"):
        require(offset + 2 <= len(data), f"truncated PEX {label} field")
        length = int.from_bytes(data[offset:offset + 2], "big")
        offset += 2
        require(offset + length <= len(data), f"invalid PEX {label} length")
        values.append(data[offset:offset + length].decode("utf-8"))
        offset += length
    return values[0], values[1], values[2]


def main() -> None:
    files = sorted(path for path in PACKAGE.rglob("*") if path.is_file())
    require(len(files) == 33, f"expected 33 package files, found {len(files)}")
    build_inputs = json.loads((ROOT / "build-inputs.json").read_text(encoding="utf-8"))

    for path in CDF.glob("*.json"):
        data = load_jsonc(path.read_text(encoding="utf-8"))
        require(isinstance(data.get("rules"), list) and data["rules"],
                f"{path.name}: missing rules")

    mint_json = json.loads((CDF / "MorrowindUsesDrams.json").read_text(encoding="utf-8"))
    sanitize = next(rule for rule in mint_json["rules"]
                    if rule["friendlyName"].startswith("Sanitize"))
    require(sanitize["conditions"].get("locations") == ["0x014293|Dragonborn.esm"],
            "Fort Frostmoth sanitization must be positively scoped")
    require("!locations" not in sanitize["conditions"],
            "the released inverted Fort Frostmoth condition returned")
    vendor_rule = next(rule for rule in mint_json["rules"] if "Vendors" in rule["friendlyName"])
    require(vendor_rule["conditions"].get("allowVendors") is True and
            vendor_rule["conditions"].get("onlyVendors") is True,
            "vendor distribution must remain vendor-only")
    mint_general = mint_json["rules"][0]
    require(set(mint_general["conditions"]["!locationKeywords"]) ==
            {"LocSetNordicRuin", "LocSetDwarvenRuin"},
            "Morrowind Dram rule lost its two shipped ancient-site exclusions")
    require("!locationKeywords" not in vendor_rule["conditions"],
            "Solstheim vendor rule must preserve M.I.N.T.'s one-pass native distribution")
    require(not (CDF / "00_Ensrick_Currency_20_SolstheimDrams.json").exists(),
            "obsolete early Solstheim Dram rule returned and will double-process Gold001")
    kolbjorn = json.loads((CDF / "zz_Ensrick_Currency_99_KolbjornCanonicalDrakr.json")
                          .read_text(encoding="utf-8"))["rules"][0]
    require(kolbjorn["conditions"].get("locationKeywords") == ["IsKolbjorn"] and
            kolbjorn["changes"] == [
                {"remove": "0xDE5029|Update.esm", "add": ["0xDE5015|Update.esm"]},
            ], "Kolbjorn late correction no longer resolves the earlier Dram result to canonical Drakr")

    mede = (CDF / "EC_medes.json").read_text(encoding="utf-8")
    require("0xDE5021|Update.esm" in mede, "Mede must resolve from Update.esm")
    require("0xDE5021|exchangeCurrency_patch_COIN.esp" not in mede,
            "released wrong-master Mede reference returned")

    swap_text = "\n".join(path.read_text(encoding="utf-8")
                           for path in PACKAGE.glob("*_SWAP.ini"))
    require("DES_Mede" not in swap_text, "unresolved DES_Mede alias returned")
    require(not re.search(r"0x0*F~Skyrim\.esm\|0xDE5016~Update\.esm", swap_text,
                          flags=re.IGNORECASE),
            "leveled-list Drakr target returned")

    mint_swap = (PACKAGE / "MorrowindUsesDrams_SWAP.ini").read_text(encoding="utf-8")
    require(len(re.findall(r"\|NONE\|chanceS\(60\)\s*$", mint_swap,
                           flags=re.MULTILINE)) == 4,
            "all four mixed Solstheim swaps must use chanceS(60)")
    require(not re.search(r"\|60\s*$", mint_swap, flags=re.MULTILINE),
            "bare BOS chance field returned")

    default = (PACKAGE / "zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini").read_text(
        encoding="utf-8")
    default_header = next(line for line in default.splitlines() if line.startswith("[Forms|"))
    require("-DLC2SolstheimLocation" in default_header,
            "default BOS rule must yield all Solstheim loose coins to M.I.N.T.'s regional pass")
    require(default.count("chanceS(25)") == 1 and default.count("chanceS(5)") == 1,
            "default loose-coin thresholds changed")
    buckets = {"gold": 0, "silver": 0, "copper": 0}
    for stable_roll in range(100):
        if stable_roll < 5:
            buckets["gold"] += 1
        elif stable_roll < 25:
            buckets["silver"] += 1
        else:
            buckets["copper"] += 1
    require(buckets == {"gold": 5, "silver": 20, "copper": 75},
            f"distribution changed: {buckets}")
    expected_value = (buckets["copper"] * 1 + buckets["silver"] * 25 +
                      buckets["gold"] * 100) / 100
    require(expected_value == 10.75, f"expected value changed: {expected_value}")

    ancient = (PACKAGE / "zz_Ensrick_Currency_90_Ancient_SWAP.ini").read_text(
        encoding="utf-8")
    require("0x6028DC~BSAssets.esm|0xDE5019~Update.esm" in ancient,
            "Bruma native Ayleid coin is not normalized to Mala")
    require("CYRLocSetAyleid" in ancient and "ccBGSSSE067_LocTypeAyleidRuin" in ancient,
            "Bruma/The Cause Ayleid coverage missing")
    require("0xDE5027~Update.esm" in ancient,
            "root caves must use the unified M.I.N.T. Gibber")
    require("-DLC2GyldenhulBarrowLocation,-IsDrakrMoney" in ancient,
            "ancient Nordic rules must defer to every active regional Drakr location")

    regional = (PACKAGE / "zz_Ensrick_Currency_80_Regional_SWAP.ini").read_text(
        encoding="utf-8")
    regional_drkr_header = next(line for line in regional.splitlines()
                                 if "0x000B93~exchangeCurrency_enhanced.esp" in line)
    require("-DLC2GyldenhulBarrowLocation" in regional_drkr_header,
            "regional Drakr swaps must defensively preserve Gyldenhul's Septim exception")
    require("0xDE5023~Update.esm" in regional and "0x000F21~M.I.N.T.esp" in regional,
            "Dominion Sancar loose/purse coverage missing")
    require("0x000B90~exchangeCurrency_enhanced.esp" in regional and
            "0x0009C6~C.O.I.N.esp" in regional,
            "Kolbjorn Drakr loose/purse/pile precedence missing")
    require("0x00000F~Skyrim.esm|0xDE5015~Update.esm" in regional,
            "regional Drakr must resolve to ECE's canonical Drakr Whale MISC")
    require("0xDE5012~Update.esm,0xDE5013~Update.esm,0xDE5014~Update.esm,0xDE5015~Update.esm"
            not in regional, "regional transaction zones must not emit three nonfungible Drakr faces")
    require("0xDE5012~Update.esm,0xDE5013~Update.esm,0xDE5014~Update.esm,0xDE5015~Update.esm"
            in ancient, "ancient Nordic ruins must retain all four physical Drakr faces")

    ece_drams_kid = (PACKAGE / "exchangeCurrency_enhanced_drams_KID.ini").read_text(
        encoding="utf-8")
    require("IsDrakrMoney|Location|0x0142A8~Dragonborn.esm" not in ece_drams_kid,
            "ECE must not re-keyword Gyldenhul as a Drakr region")
    require(len(ece_drams_kid.splitlines()) == 70 and
            "IsDrakrMoney|Location|0x014298~Dragonborn.esm" in ece_drams_kid and
            "IsKolbjorn|Location|0x0142BB~Dragonborn.esm" in ece_drams_kid,
            "ECE KID override must differ only by the one Gyldenhul assignment")

    containers = json.loads((CDF / "EC_septims_containers.json").read_text(
        encoding="utf-8"))
    refs = containers["rules"][0]["conditions"]["!references"]
    require(len(refs) == 12 and len(set(refs)) == 12,
            "quest/storage exception reference set changed")
    require("references" not in containers["rules"][0]["conditions"],
            "quest/storage exceptions must be exclusions, not conversion targets")
    require(containers["rules"][0]["conditions"].get("!locations") ==
            ["0x016E2A|Dragonborn.esm"],
            "generic Septim CDF rule must yield the Solstheim tree to one late Dram pass")

    deployed_names = {path.name for path in files}
    craft_mask = PACKAGE / "SKSE" / "Plugins" / "SkyPatcher" / \
        "constructibleObject" / "ECE_CraftAndRecipes.ini"
    require(craft_mask.exists() and not any(
        line.strip() and not line.lstrip().startswith(";")
        for line in craft_mask.read_text(encoding="utf-8").splitlines()),
        "ECE crafting mask must contain comments only")
    ancient_mask = PACKAGE / "SKSE" / "Plugins" / "SkyPatcher" / \
        "constructibleObject" / "ECE_AncientCoinsToIngot.ini"
    require(ancient_mask.exists() and not any(
        line.strip() and not line.lstrip().startswith(";")
        for line in ancient_mask.read_text(encoding="utf-8").splitlines()),
        "malformed ECE ancient-smelting config must remain masked")
    require("exchangeCurrency_patch_BS.esp" not in deployed_names,
            "broad Bruma crafting/plugin patch must stay out")

    apocrypha = PACKAGE / "zz_Ensrick_Currency_Apocrypha_KID.ini"
    apocrypha_rules = [line.strip() for line in apocrypha.read_text(encoding="utf-8").splitlines()
                       if line.strip() and not line.lstrip().startswith(";")]
    apocrypha_locations = [
        "016E2B", "0142AC", "0142AE", "0142AF", "0142B0",
        "01EE06", "01EE07", "01EE08", "0382F5", "03A1E7",
    ]
    expected_apocrypha = [
        f"Keyword = 0xBB5~exchangeCurrency_enhanced.esp|Location|0x{form_id}~Dragonborn.esm"
        for form_id in apocrypha_locations
    ]
    require(apocrypha_rules == expected_apocrypha,
            "Apocrypha KID policy must use ECE's numeric Ohzer KYWD on the root plus nine exact child LCTNs")
    require("isOhzerMoney|" not in apocrypha.read_text(encoding="utf-8"),
            "bare Ohzer EditorID returned; KID rule must fail closed on numeric owner form")
    ini_text = "\n".join(path.read_text(encoding="utf-8", errors="replace")
                           for path in PACKAGE.rglob("*.ini"))
    require(not re.search(r"^\s*Keyword\s*=.*Varken", ini_text,
                          flags=re.IGNORECASE | re.MULTILINE),
            "Varken received a location keyword despite the deliberate dormant policy")
    ancient_weights = PACKAGE / "SKSE" / "Plugins" / "SkyPatcher" / "misc" / \
        "zz_Ensrick_Currency_AncientWeights.ini"
    weight_lines = [line.strip().lower() for line in
                    ancient_weights.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.lstrip().startswith(";")]
    require(weight_lines == [
        "filterbymiscs=update.esm|0xde5012:weight=0.01",
        "filterbymiscs=update.esm|0xde5013:weight=0.01",
        "filterbymiscs=update.esm|0xde5014:weight=0.01",
        "filterbymiscs=update.esm|0xde5017:weight=0.02",
        "filterbymiscs=update.esm|0xde5018:weight=0.02",
        "filterbymiscs=update.esm|0xde5027:weight=0.02",
    ], "owned ancient-currency weight policy changed")

    modern_weights = PACKAGE / "SKSE" / "Plugins" / "SkyPatcher" / "misc" / \
        "zz_Ensrick_Currency_SeptimWeights.ini"
    modern_weight_text = modern_weights.read_text(encoding="utf-8")
    modern_weight_lines = [line.strip().lower() for line in
                           modern_weight_text.splitlines()
                           if line.strip() and not line.lstrip().startswith(";")]
    septim_baseline = build_inputs["septimWeightBaseline"]
    require(septim_baseline["physicalForms"] == [
                "000B6D:exchangeCurrency_enhanced.esp",
                "000823:exchangeCurrency_enhanced.esp",
                "000824:exchangeCurrency_enhanced.esp",
            ] and septim_baseline["releasedWeights"] == [0.01, 0.02, 0.03] and
            septim_baseline["ownedWeights"] == [0.06, 0.07, 0.13],
            "pinned ECE/owned modern-Septim policy metadata changed")
    expected_modern_weight_lines = []
    for form_key, weight in zip(septim_baseline["physicalForms"],
                                septim_baseline["ownedWeights"], strict=True):
        local_id, owner = form_key.split(":", maxsplit=1)
        local_id = local_id.lstrip("0") or "0"
        expected_modern_weight_lines.append(
            f"filterbymiscs={owner.lower()}|0x{local_id.lower()}:weight={weight:g}")
    require(modern_weight_lines == expected_modern_weight_lines,
            "owned modern-Septim weight policy must target exactly copper/silver/gold")
    modern_weight_lower = modern_weight_text.lower()
    require(":value=" not in modern_weight_lower and ":fullname=" not in modern_weight_lower,
            "modern-Septim weight patch must not change value or name fields")
    require("skyrim.esm|0x00000f" not in modern_weight_lower and
            "skyrim.esm|0xf" not in modern_weight_lower,
            "hidden Gold001 accounting backend must remain weightless")
    require(modern_weights.name.casefold() > "ECE_septims_100.ini".casefold(),
            "owned modern-Septim weight file must sort after ECE's runtime defaults")

    plugin = PACKAGE / "Ensrick Currency Integration Patch.esp"
    pex = PACKAGE / "Scripts" / "Ensrick_CurrencyRuntimeDefaultsAlias.pex"
    ohzer_pex = PACKAGE / "Scripts" / "Ensrick_OhzerCurrencyScript.pex"
    madran_pex = PACKAGE / "Scripts" / "DES_MadranSwapper.pex"
    ece_guard_names = [
        "EC_septimsScript",
        "EC_drakrsScript",
        "EC_dramsScript",
        "EC_medesScript",
        "EC_oshkasScript",
        "EC_ulfricsScript",
    ]
    ece_guard_pex = [PACKAGE / "Scripts" / f"{name}.pex" for name in ece_guard_names]
    seq = PACKAGE / "SEQ" / "Ensrick Currency Integration Patch.seq"
    require(plugin.is_file(), "owned currency ESPFE is missing")
    require(pex.is_file(), "owned runtime-default PEX is missing")
    require(ohzer_pex.is_file(), "owned Ohzer transaction PEX is missing")
    require(seq.is_file(), "start-enabled quest SEQ is missing")
    for script_path in (pex, ohzer_pex, madran_pex, *ece_guard_pex):
        pex_bytes = script_path.read_bytes()
        require(pex_bytes[:4] == bytes.fromhex("FA57C0DE"),
                f"{script_path.name} is not a Skyrim PEX")
        require(int.from_bytes(pex_bytes[8:16], "big") == 946684800,
                f"{script_path.name} timestamp is not normalized to the reproducible epoch")
        source_name, user_name, machine_name = pex_header_strings(pex_bytes)
        expected_source = (build_inputs["papyrusCompiler"]["normalizedSourcePrefix"] +
                           "/" + script_path.stem + ".psc")
        require((source_name, user_name, machine_name) == (
                    expected_source,
                    build_inputs["papyrusCompiler"]["normalizedUserName"],
                    build_inputs["papyrusCompiler"]["normalizedMachineName"],
                ), f"{script_path.name} PEX release metadata is not normalized")
    require(seq.read_bytes() == struct.pack("<II", 0x09000800, 0x09000803),
            "SEQ must target owned QUSTs 000800 and 000803 at file-relative master index 09")
    translation = PACKAGE / "interface" / "translations" / \
        "exchangecurrency_enhanced_english.txt"
    translation_bytes = translation.read_bytes()
    require(translation_bytes.startswith(bytes.fromhex("FFFE")),
            "ECE English translation override must be UTF-16LE with BOM")
    require(translation_bytes.decode("utf-16") ==
            "$Gold\tSeptims\r\n$Currency\tCurrency\r\n",
            "ECE English translation override has unexpected keys/content")
    require("$Ore" not in translation_bytes.decode("utf-16") and
            "$Ingot" not in translation_bytes.decode("utf-16"),
            "speculative I4 translation keys must remain absent")

    i4_path = PACKAGE / "SKSE" / "Plugins" / "InventoryInjector" / \
        "exchangeCurrency_enhanced.json"
    i4_bytes = i4_path.read_bytes()
    require(not i4_bytes.startswith(bytes.fromhex("EFBBBF")),
            "owned ECE I4 override must remain UTF-8 without BOM")
    i4_text = i4_bytes.decode("utf-8")
    require("Métal dwemer" not in i4_text,
            "hard-coded French Dwarven scrap label returned")
    require(i4_text.count('"subTypeDisplay": "$DwarvenScrap"') == 1,
            "ECE I4 override must contain one localized Dwarven scrap label")
    i4 = json.loads(i4_text)
    dwarven_rule = next(rule for rule in i4["rules"]
                        if rule.get("assign", {}).get("iconLabel") == "misc_dwarvenscrap")
    require(dwarven_rule["assign"]["subTypeDisplay"] == "$DwarvenScrap",
            "Dwarven scrap rule is not language-neutral")
    require(len(dwarven_rule["match"]["formId"]["anyOf"]) == 28,
            "ECE Dwarven scrap target set changed")
    expected_i4_hash = build_inputs["inventoryInjectorOverride"]["outputSha256"]
    require(hashlib.sha256(i4_bytes).hexdigest().upper() == expected_i4_hash,
            "owned ECE I4 override differs from the pinned one-change output")
    expected_kid_hash = build_inputs["keywordDistributorOverride"]["outputSha256"]
    require(hashlib.sha256((PACKAGE / "exchangeCurrency_enhanced_drams_KID.ini")
                           .read_bytes()).hexdigest().upper() == expected_kid_hash,
            "owned ECE KID override differs from the pinned one-line-removal output")

    coin_cdf_path = CDF / "C.O.I.N.json"
    coin_cdf_bytes = coin_cdf_path.read_bytes()
    require(not coin_cdf_bytes.startswith(bytes.fromhex("EFBBBF")),
            "owned C.O.I.N. CDF override must remain UTF-8 without BOM")
    coin_cdf_text = coin_cdf_bytes.decode("utf-8")
    require('"remove" : "01DE5012|Update.esm"' not in coin_cdf_text,
            "malformed C.O.I.N. Drakr removal returned")
    require(coin_cdf_text.count('"remove" : "0xDE5012|Update.esm"') == 2,
            "C.O.I.N. CDF must contain the corrected Drakr removal and its existing exact peer")
    coin_cdf = load_jsonc(coin_cdf_text)
    randomize_drakr = next(rule for rule in coin_cdf["rules"]
                           if rule.get("friendlyName") == "Randomize Leveled Drakr")
    require(randomize_drakr["changes"] == [{
        "remove": "0xDE5012|Update.esm",
        "add": ["0xDE5016|Update.esm"],
    }], "C.O.I.N. Randomize Leveled Drakr rule is not the exact intended DE5012 -> DE5016 change")
    expected_coin_cdf_hash = build_inputs["containerDistributionOverride"]["outputSha256"]
    require(hashlib.sha256(coin_cdf_bytes).hexdigest().upper() == expected_coin_cdf_hash,
            "owned C.O.I.N. CDF override differs from the pinned one-change output")

    audit_path = ROOT / "work" / "plugin-audit.json"
    require(audit_path.is_file(), "plugin audit receipt is missing")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    require(audit["eslFlag"] is True and audit["records"] == 45,
            "plugin audit did not prove ESPFE plus the exact 45-record set")
    require(audit.get("exchangeWorkbenchProvider") == {
        "plugin": "SL99Exchanger.esp",
        "formKey": "000801:SL99Exchanger.esp",
        "editorId": "SL99CraftingExchangeBank",
        "sha256": "C9342F1B669A3AE1F4A51E0CA8FBD9CDA3AEC915D36DC4CC9A0798B09E5B2446",
        "bytes": 159056,
        "records": 470,
        "smallFlag": True,
        "exactWinningBinary": True,
    }, "plugin audit did not pin the exact compact ECE exchange-workbench provider")
    require(audit["deletedRecords"] == 0 and audit["disabledRecipeCount"] == 17,
            "plugin audit did not prove no deletions and all 17 disabled recipes")
    require(audit["runtimeQuest"]["seqFileRelativeFormId"] == "09000800" and
            audit["ohzerQuest"]["seqFileRelativeFormId"] == "09000803",
            "plugin audit SEQ identities differ")
    require(audit["masterMinimality"]["exact"] is True and audit["masters"] == [
        "Skyrim.esm", "Update.esm", "Dragonborn.esm", "SL99Exchanger.esp",
        "exchangeCurrency_enhanced.esp", "C.O.I.N.esp", "M.I.N.T.esp",
        "WindhelmUsesUlfrics.esp", "exchangeCurrency_patch_COIN.esp",
    ], "plugin audit did not prove the exact minimal nine-master set")
    require(audit["ohzerTransactionScript"]["script"] == "Ensrick_OhzerCurrencyScript" and
            audit["ohzerTransactionScript"]["neutralBarterRate"] is True and
            audit["ohzerTransactionScript"]["upgradeSafeNewQuest"] is True,
            "plugin audit did not prove the owned Ohzer transaction architecture")
    require([item["script"] for item in audit["eceInheritedAltCoinBindings"]] == [
        "EC_ulfricsScript",
        "EC_dramsScript",
        "EC_medesScript",
        "EC_drakrsScript",
        "EC_oshkasScript",
    ] and all(item["vendorBindingWasAbsent"] is True
              for item in audit["eceInheritedAltCoinBindings"]),
            "plugin audit did not prove all five inherited ECE altCoins repairs")
    require(audit["madranScriptMigration"]["targetScript"] ==
            "DES_CurrencyFramework_BarterExclusion" and
            audit["madranScriptMigration"]["vendorPexBundled"] is False and
            len(audit["madranScriptMigration"]["removedStaleQuestProperties"]) == 8,
            "plugin audit did not prove the current M.I.N.T. Ma'dran migration")
    require(audit["removedStaleVmadProperties"] == [
        "EC_septimsFunctions.busy",
        "EC_septimsScript.busy",
        "EC_septimsScript.DES_ConvertCoins",
    ], "plugin audit did not prove exact ECE stale-property cleanup")
    require(len(audit["drakrPurseAdapters"]["ownedChangeLists"]) == 2 and
            len(audit["drakrPurseAdapters"]["purseOverrides"]) == 3 and
            audit["drakrPurseAdapters"]["sharedC_O_I_N_ChangeListsOverridden"] is False,
            "plugin audit did not prove isolated canonical-Drakr purse adapters")
    require(audit["drakrPileRepair"]["target"] == "DE5015:Update.esm",
            "plugin audit did not prove the canonical-Drakr pile repair")
    expected_exchange = [
        ("DE5012:Update.esm", 20, 3, "coin-default-rate"),
        ("DE5013:Update.esm", 20, 3, "coin-default-rate"),
        ("DE5014:Update.esm", 20, 3, "coin-default-rate"),
        ("DE5015:Update.esm", 20, 3, "coin-default-rate"),
        ("DE5019:Update.esm", 5, 2, "coin-default-rate"),
        ("DE5020:Update.esm", 5, 3, "coin-default-rate"),
        ("DE5022:Update.esm", 4, 1, "coin-default-rate"),
        ("DE5018:Update.esm", 5, 8, "coin-default-rate"),
        ("DE5017:Update.esm", 1, 1, "coin-default-rate"),
        ("DE5027:Update.esm", 1, 1, "effective-mint-core-rate"),
    ]
    actual_exchange = [(item["input"], item["inputCount"], item["outputCount"],
                        item["purpose"]) for item in audit["ancientExchangeRecipes"]]
    require(actual_exchange == expected_exchange and
            all(item["output"] == "00000F:Skyrim.esm" and
                item["workbench"] == "000801:SL99Exchanger.esp" and
                item["oneWayCashout"] is True
                for item in audit["ancientExchangeRecipes"]),
            "plugin audit did not prove all ten one-way ancient bank exchanges")

    forbidden_extensions = {".psc", ".bsa", ".ba2", ".nif", ".dds", ".wav", ".xwm"}
    require(not [path for path in files if path.suffix.lower() in forbidden_extensions],
            "package contains vendor-source or asset-like file types")
    packaged_plugins = [path.name for path in files if path.suffix.lower() in {".esp", ".esm", ".esl"}]
    require(packaged_plugins == ["Ensrick Currency Integration Patch.esp"],
            f"package contains a non-owned plugin: {packaged_plugins}")
    packaged_pex = [path.name for path in files if path.suffix.lower() == ".pex"]
    require(packaged_pex == [
        "DES_MadranSwapper.pex",
        "EC_drakrsScript.pex",
        "EC_dramsScript.pex",
        "EC_medesScript.pex",
        "EC_oshkasScript.pex",
        "EC_septimsScript.pex",
        "EC_ulfricsScript.pex",
        "Ensrick_CurrencyRuntimeDefaultsAlias.pex",
        "Ensrick_OhzerCurrencyScript.pex",
    ],
            f"package contains an unexpected script binary: {packaged_pex}")

    notice = (PACKAGE / "NOTICE.txt").read_text(encoding="utf-8")
    license_text = (PACKAGE / "LICENSE.txt").read_text(encoding="utf-8")
    notice_flat = " ".join(notice.split())
    for nexus_id in (51439, 178940, 141884, 37545):
        require(f"/mods/{nexus_id}" in notice, f"NOTICE lost Nexus attribution {nexus_id}")
    require("MorrowindUsesDrams_SWAP.ini" in notice and "MorrowindUsesDrams.json" in notice,
            "NOTICE lost the M.I.N.T. terms exception")
    require("exchangeCurrency_enhanced.json" in notice and "$DwarvenScrap" in notice,
            "NOTICE lost the ECE I4 terms exception")
    require("exchangeCurrency_enhanced_drams_KID.ini" in notice and
            "Gyldenhul Barrow" in notice and "IsDrakrMoney" in notice,
            "NOTICE lost the ECE Gyldenhul KID terms exception")
    require("EC_medes.json" in notice and "wrong-master" in notice and "Update.esm" in notice,
            "NOTICE lost the ECE Mede wrong-master terms exception")
    require("C.O.I.N.json" in notice and "01DE5012" in notice and "0xDE5012" in notice,
            "NOTICE lost the C.O.I.N. CDF terms exception")
    require("Ensrick_OhzerCurrencyScript" in notice and "interoperability derivative" in notice and
            "excluded from the\nMIT grant" in notice and "Donation Points" in notice and
            "DES_CurrencyFramework_BarterExclusion" in notice,
            "NOTICE lost owned Ohzer or M.I.N.T. interoperability provenance")
    require("DES_MadranSwapper.pex" in notice and "class-loader" in notice,
            "NOTICE lost the independently authored Ma'dran compatibility-shim provenance")
    require("EC_septimsScript.pex" in notice and "HasKeywordString" in notice and
            "six narrow ECE script derivatives" in notice_flat and "no-sale" in notice,
            "NOTICE lost the ECE null-Location script provenance or restrictions")
    require("zz_Ensrick_Currency_SeptimWeights.ini" in notice_flat and
            "original, weight-only" in notice_flat and
            "copies no ECE configuration text" in notice_flat,
            "NOTICE lost the original modern-Septim weight-config boundary")
    require("C.O.I.N. - Coins of Interesting Nature — created by Tate Taylor and VictorF" in
            notice_flat and
            "M.I.N.T. - Mint-Issued National Tenders — created by Tate Taylor" in
            notice_flat and "Exchange Currency Enhanced — created by Nerapharu" in
            notice_flat and "WiZkiD Ancient Imperial Septims — created by WiZkiD" in
            notice_flat,
            "NOTICE lost an upstream creator credit or official project title")
    require("SCOPE NOTICE" in license_text and "excluded" in license_text and
            "MIT License" in license_text and "Copyright (c) 2026 Ensrick" in license_text,
            "owned MIT license text is missing or incomplete")
    require("fourteen newly authored" in notice and
            "thirty-one compatibility" in notice and
            "not be represented or redistributed as an all-MIT work" in notice and
            "vendor-origin data in the ESP's 31" in license_text,
            "NOTICE/LICENSE lost the mixed-terms ESP record boundary")

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("version") == "0.2.6" and
            manifest.get("madranCompatibilityShim", {}).get("file") ==
            "Scripts/DES_MadranSwapper.pex",
            "manifest lost the v0.2.6 Ma'dran compatibility shim")
    require(manifest.get("physicalSeptimWeights", {}).get("weights") == {
                "copper": 0.06, "silver": 0.07, "gold": 0.13,
            } and
            manifest["physicalSeptimWeights"].get("hiddenGold001") == 0,
            "manifest lost the approved modern-Septim weight policy")
    binary_receipts = [
        (manifest["runtimePatch"], plugin),
        (manifest["papyrusHelper"], pex),
        (manifest["ohzerHelper"], ohzer_pex),
        (manifest["madranCompatibilityShim"], madran_pex),
    ]
    guard_receipts = manifest.get("eceLocationGuards", {}).get("scripts", [])
    require([item.get("script") for item in guard_receipts] == ece_guard_names,
            "manifest lost the exact six ECE null-Location overrides")
    require(manifest["eceLocationGuards"].get("behavior") ==
            "old/new None values are tested before every HasKeywordString call; non-null branches are unchanged",
            "manifest lost the ECE null-Location behavioral boundary")
    binary_receipts.extend((receipt, payload)
                           for receipt, payload in zip(guard_receipts, ece_guard_pex, strict=True))
    for receipt, payload in binary_receipts:
        payload_bytes = payload.read_bytes()
        require(receipt.get("bytes") == len(payload_bytes) and
                receipt.get("sha256") == hashlib.sha256(payload_bytes).hexdigest().upper(),
                f"manifest binary receipt differs from {payload.name}")
    hard_dependencies = {
        491, 10917, 12604, 32444, 37545, 51073, 51439, 55728, 60805,
        67925, 85702, 106659, 120152, 127686, 135618, 141884, 178940,
    }
    require(hard_dependencies.issubset(set(manifest["requiredNexusMods"])),
            "manifest lost a hard runtime/content dependency")

    ece_plan = json.loads((REPO / "records" / "fomod-plans" /
                           "141884-ece-coin-mint-wizkid.json").read_text(
                               encoding="utf-8"))
    selected_sources = {mapping["source"] for mapping in ece_plan["mappings"]}
    forbidden_selections = {
        "02 settings skypatcher/SKSE/Plugins/SkyPatcher/constructibleObject/ECE_AncientCoinsToIngot.ini",
        "02 settings skypatcher/SKSE/Plugins/SkyPatcher/constructibleObject/ECE_CraftAndRecipes.ini",
        "20 patches/Bruma/exchangeCurrency_patch_BS.esp",
    }
    require(not (selected_sources & forbidden_selections),
            "ECE plan re-enabled a masked/broad optional component")

    require("000827:exchangeCurrency_patch_COIN.esp" in audit["exactOverrides"],
            "plugin audit did not prove the ECE alternate-currency quest override")

    print(f"PASS: {len(files)} files; loose coin 75/20/5; EV {expected_value:.2f}; "
          "45-record ESPFE, ECE/M.I.N.T. VMAD repairs, weighted modern and ancient currencies, "
          "ten bank exchanges, 17 disabled smelting recipes, Ma'dran class-loader shim, three purses, two runtime quests, "
          "SEQ, Ohzer and notices covered")


if __name__ == "__main__":
    main()
