#!/usr/bin/env python3
"""Fail-closed static/release gate for the v0.3.0 currency integration."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "package"
WORK = ROOT / "work"
PLUGIN_NAME = "Ensrick Currency Integration Patch.esp"
RUNTIME_CONFIG = PACKAGE / "SKSE/Plugins/EnsrickCurrencyDenominations.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def exact_keys(node: dict[str, Any], expected: set[str], context: str) -> None:
    require(set(node) == expected,
            f"{context}: keys {sorted(node)} differ from {sorted(expected)}")


def denomination_counts(amount: int) -> tuple[int, int, int]:
    gold, remainder = divmod(amount, 100)
    silver, copper = divmod(remainder, 10)
    return copper, silver, gold


def one_break(amount: int) -> tuple[int, int, int, str | None]:
    copper, silver, gold = denomination_counts(amount)
    if gold:
        return copper, silver + 10, gold - 1, "gold"
    if silver:
        return copper + 10, silver - 1, gold, "silver"
    return copper, silver, gold, None


def value(counts: tuple[int, int, int]) -> int:
    copper, silver, gold = counts
    return copper + 10 * silver + 100 * gold


def i4_form(form_key: str) -> str:
    local_id, plugin = form_key.split(":", 1)
    return f"{plugin.lower()}|{int(local_id, 16):x}"


def validate_policy(policy: dict[str, Any]) -> None:
    denominations = policy["denominations"]
    require((denominations["canonicalPercent"], denominations["variantPercent"]) == (80, 20),
            "policy distribution is not exact 80/20")

    septim = denominations["septim"]
    septim_tiers = [septim[tier] for tier in ("copper", "silver", "gold")]
    require([entry["value"] for entry in septim_tiers] == [1, 10, 100],
            "Septim values are not 1/10/100")
    require([entry["sourceValue"] for entry in septim_tiers] == [1, 25, 100],
            "Septim source values changed; silver 25->10 correction is not pinned")
    require([entry["name"] for entry in septim_tiers] ==
            ["Copper Septim", "Silver Septim", "Gold Septim"],
            "Septim tier names changed")

    families = denominations["modernFamilies"]
    expected_ids = ["mede", "ulfric", "dram", "oshka", "ohzer", "varken"]
    require([family["id"] for family in families] == expected_ids,
            "modern family order/set changed")
    require([family["enabled"] for family in families] ==
            [True, True, True, True, True, False],
            "only Varken may remain dormant")
    for family in families:
        title = family["displayLabel"]
        require([family["copperName"], family["silverName"], family["goldName"]] ==
                [f"Copper {title}", f"Silver {title}", f"Gold {title}"],
                f"{family['id']}: explicit tier names changed")
        require(family["copperModel"].endswith(f"{title}\\{title}_Copper.nif") and
                family["silverModel"].endswith(f"{title}\\{title}_Silver.nif") and
                family["goldModel"].endswith(f"{title}\\{title}_Gold.nif"),
                f"{family['id']}: deterministic owned NIF paths changed")
        require(family["runtimeWeight"] in (0.01, 0.02),
                f"{family['id']}: approved per-family weight changed")

    singletons = denominations["singletonFamilies"]
    require([(item["id"], item["formKey"], item["value"]) for item in singletons] == [
        ("drakr", "DE5015:Update.esm", 1),
        ("sancar", "DE5023:Update.esm", 1),
    ], "canonical Drakr/Sancar singleton contract changed")
    require(singletons[0]["routeKeyword"] == "000B93:exchangeCurrency_enhanced.esp" and
            singletons[0]["perk"] == "00082C:exchangeCurrency_patch_COIN.esp",
            "canonical Drakr route/perk changed")
    require(singletons[1]["routeKeyword"] == f"000803:{PLUGIN_NAME}" and
            singletons[1]["ownedRouteKeywordEditorId"] == "Ensrick_IsSancarMoney",
            "owned Sancar route changed")

    overrides = policy["overrides"]
    ece = overrides["ecePlayerCurrencyQuests"]
    require([item["formKey"] for item in ece] == [
        "000B63:exchangeCurrency_enhanced.esp",
        "000827:exchangeCurrency_patch_COIN.esp",
    ], "exact two ECE transaction-owner quests changed")
    require(ece[0]["transactionScripts"] == ["EC_septimsFunctions", "EC_septimsScript"],
            "ECE Septim transaction script set changed")
    require(ece[1]["transactionScripts"] == [
        "EC_altCurrencyFunctions", "EC_ulfricsScript", "EC_dramsScript",
        "EC_medesScript", "EC_drakrsScript", "EC_oshkasScript",
    ], "ECE regional transaction script set changed")

    cost_only = overrides["mintCostOnlyQuests"]
    require([(item["formKey"], item["questScript"], item["playerAliasScript"])
             for item in cost_only] == [
        ("00000D:MorrowindUsesDrams.esp", "DES_DramCurrencySwapper",
         "DES_DramCurrencySwapperAlias"),
        ("000002:WindhelmUsesUlfrics.esp", "DES_UlfricCurrencySwapper",
         "DES_UlfricCurrencySwapperAlias"),
    ], "M.I.N.T. cost-only quest bindings changed")
    require(overrides["mintMadranQuest"] == {
        "formKey": "000002:WindhelmUsesUlfrics.esp",
        "editorId": "DES_UlfricWindhelmServicesQuest",
        "aliasId": 5,
        "transactionScript": "DES_MadranSwapper",
        "staleQuestProperties": [
            "Alias_Brunwulf", "Alias_Nilsine", "Alias_Oengul", "Alias_Tova",
            "Alias_Torsten", "Alias_CaptainLonelyGale", "Alias_Torbjorn", "Alias_Jora",
        ],
    }, "Ma'dran transaction alias removal changed")
    require(len(overrides["disabledMintExchangeInfos"]) == 38,
            "exact 38 obsolete M.I.N.T. exchange/failure INFOs are required")
    require(len({item["formKey"] for item in overrides["disabledMintExchangeInfos"]}) == 38,
            "M.I.N.T. disabled INFO list contains duplicates")
    require([item["formKey"] for item in overrides["mintBackendConditionInfos"]] == [
        "00000A:WindhelmUsesUlfrics.esp", "00000C:WindhelmUsesUlfrics.esp",
    ], "exact two Ulfric horse budget INFOs changed")
    require(all(item["backendCurrency"] == "00000F:Skyrim.esm" and
                item["comparisonGlobal"] == "0000C9:WindhelmUsesUlfrics.esp"
                for item in overrides["mintBackendConditionInfos"]),
            "horse checks must target Gold001 while preserving the original price global")

    require(len(policy["disabledCurrencyToIngotRecipes"]) == 17,
            "exact 17 currency-to-ingot recipes must be disabled")
    bank = policy["disabledModernBankRecipes"]
    expected_bank_ids = [
        "82D", "82E", "82F", "830", "834", "835", "84B", "84C",
        "84D", "84F", "853", "854", "873", "874", "875", "876",
    ]
    require([item["formKey"] for item in bank] ==
            [f"000{local}:exchangeCurrency_patch_COIN.esp" for local in expected_bank_ids],
            "exact 16 non-parity modern bank recipes changed")
    ancient = overrides["ancientExchangeRecipes"]
    require(len(ancient) == 9, "only nine ancient face/Gibber exchanges may remain")
    require("DE5015:Update.esm" not in {item["inputFormKey"] for item in ancient},
            "canonical value-1 Drakr Whale still has a conflicting 20->3 recipe")

    purses = overrides["coinPurses"]
    require(len(purses) == 3 and all(len(item["counts"]) == 16 for item in purses),
            "three pinned 16-outcome purse adapters are required")
    for purse in purses:
        for amount in purse["counts"]:
            canonical = denomination_counts(amount)
            broken = one_break(amount)
            require(value(canonical) == amount and value(broken[:3]) == amount,
                    f"purse {amount}: denomination value is not conserved")
            changed = sum(left != right for left, right in zip(canonical, broken[:3]))
            require(changed <= 2, f"purse {amount}: more than one tier was broken")
    vectors = {
        24: ((4, 2, 0), (14, 1, 0, "silver")),
        100: ((0, 0, 1), (0, 10, 0, "gold")),
        110: ((0, 1, 1), (0, 11, 0, "gold")),
    }
    for amount, (canonical, broken) in vectors.items():
        require(denomination_counts(amount) == canonical and one_break(amount) == broken,
                f"pinned purse vector {amount} changed")


def validate_runtime_config(config: dict[str, Any], policy: dict[str, Any]) -> None:
    exact_keys(config, {
        "schemaVersion", "configId", "accounting", "distribution", "routing",
        "sourceSafety", "sources", "telemetry", "disabledEcePlayerAliasQuests",
        "families", "excludePhysicalFormsFromOrdinaryBarter",
        "excludePhysicalFormsFromDrop",
    }, "runtime root")
    require(config["schemaVersion"] == 1 and
            config["configId"] == "ensrick-currency-denominations-v0.3.0",
            "runtime schema/config identity changed")
    require(config["accounting"] == {
        "backendForm": "00000F:Skyrim.esm",
        "owner": "EnsrickCurrencyDenominations",
        "strictSingleOwner": True,
    }, "Gold001 strict-owner contract changed")
    require(config["distribution"] == {
        "canonicalPercent": 80,
        "variantPercent": 20,
        "breakAtMostOne": True,
        "breakOrder": [100, 10],
        "seed": "0x454E535249434B31",
        "stableIdentity": ["sourceFormKey", "sourceReferenceFormId", "familyId"],
    }, "runtime deterministic 80/20 distribution changed")
    require(config["routing"]["precedence"] == [
        "questExceptions", "ancientExclusions", "modernFamilies", "septimFallback",
    ], "runtime route precedence changed")
    require(config["routing"]["ancientExclusionKeywords"] == [
        "000BAC:exchangeCurrency_enhanced.esp", "000B91:exchangeCurrency_enhanced.esp",
        "DE5038:Update.esm", "DE5039:Update.esm", "DE5040:Update.esm",
        "000D61:ccbgssse067-daedinv.esm", "08400C:BSHeartland.esm",
    ], "reviewed ancient exclusions changed")

    safety = config["sourceSafety"]
    require(safety["actors"] == {
        "mode": "deadGenericOnly", "requireAllowlistedSource": False,
        "denyPlayer": True, "denyFollowers": True, "denyVendors": True,
        "denyUniquePersistentEssentialProtected": True,
    }, "actor safety gate changed")
    require(safety["containers"] == {
        "mode": "respawningSafeOnly", "requireAllowlistedSource": False,
        "denyVendors": True, "denyPlayerStorage": True, "denyQuestStorage": True,
    }, "container safety gate changed")
    require(safety["purses"] == {
        "mode": "allowlistedOnly", "requireAllowlistedBase": True,
    }, "purse safety gate changed")
    sources = config["sources"]
    require(sources["actors"]["allowBaseForms"] == [] and
            sources["containers"]["allowBaseForms"] == [],
            "broad safe classification requires empty actor/container allow arrays")
    require(len(sources["containers"]["denyReferences"]) == 12,
            "reviewed storage deny-reference set changed")
    require(sources["purses"] == {
        "baseForms": [
            "0D790C:Skyrim.esm", "0D8E7F:Skyrim.esm", "0D8E80:Skyrim.esm",
            "000805:C.O.I.N.esp", "000804:C.O.I.N.esp", "000803:C.O.I.N.esp",
        ],
        "budgetLists": [
            "0D790B:Skyrim.esm", "0D8E7D:Skyrim.esm", "0D8E7E:Skyrim.esm",
            "000800:C.O.I.N.esp", "000801:C.O.I.N.esp", "000802:C.O.I.N.esp",
        ],
    }, "typed purse FLOR/LVLI allowlists changed")
    require(config["telemetry"]["requiredReasonCounters"] is True and
            config["telemetry"]["reasonCounters"] == policy["runtimeReasonCounters"] and
            len(config["telemetry"]["reasonCounters"]) == 15 and
            "source-ancient-passthrough" in config["telemetry"]["reasonCounters"],
            "fail-closed source telemetry contract changed")
    require(config["excludePhysicalFormsFromOrdinaryBarter"] is True and
            config["excludePhysicalFormsFromDrop"] is False,
            "physical coins must be VendorNoSale but remain droppable/storable")

    policy_quests = policy["overrides"]["ecePlayerCurrencyQuests"]
    require([(item["quest"], item["removedScripts"])
             for item in config["disabledEcePlayerAliasQuests"]] ==
            [(item["formKey"], item["transactionScripts"]) for item in policy_quests],
            "runtime disabled-owner list differs from ESP policy")
    require(all(item["startGameEnabledRemoved"] is True
                for item in config["disabledEcePlayerAliasQuests"]),
            "both ECE owners must lose start-game-enabled")

    families = config["families"]
    require([item["id"] for item in families] == [
        "septim", "mede", "ulfric", "dram", "oshka", "ohzer", "varken",
        "drakr", "sancar",
    ], "runtime family order/set changed")
    require(sum(item["enabled"] and item["fallback"] for item in families) == 1 and
            families[0]["id"] == "septim" and families[0]["fallback"],
            "Septim must be the sole enabled fallback")
    for family in families:
        values = sorted(item["value"] for item in family["denominations"])
        require(values in ([1], [1, 10, 100]),
                f"{family['id']}: invalid runtime denomination values")
    physical = [denomination["form"] for family in families
                for denomination in family["denominations"]]
    require(len(physical) == len(set(physical)) == 23,
            "each of 23 physical forms must belong to exactly one family")
    require(config["accounting"]["backendForm"] not in physical,
            "hidden Gold001 must never also be a physical denomination")


def validate_distribution_configs(config: dict[str, Any]) -> None:
    cdf = PACKAGE / "SKSE/Plugins/ContainerDistributionFramework"
    masked = [
        "00_Ensrick_Currency_30_Varken.json", "EC_medes.json",
        "EC_ohzers.json", "EC_oshkas.json", "EC_septims_containers.json",
        "EC_ulfrics.json", "EC_varkens.json", "MorrowindUsesDrams.json",
        "WindhelmUsesUlfrics.json", "DominionUsesSancar.json",
    ]
    for name in masked:
        require(load_json(cdf / name) == {"rules": []},
                f"unsafe modern CDF owner not fully masked: {name}")
    drakr_cdf = (cdf / "EC_drams_drakrs.json").read_text(encoding="utf-8")
    require("DE5029" not in drakr_cdf and "Dram" not in drakr_cdf,
            "combined CDF mask still distributes modern Drams")
    require("DE5015" in drakr_cdf and "DE5022" in drakr_cdf,
            "combined CDF mask lost canonical Drakr/Nchuark preservation")
    require((cdf / "00_Ensrick_Currency_10_BrumaAyleid.json").is_file() and
            (cdf / "zz_Ensrick_Currency_99_KolbjornCanonicalDrakr.json").is_file(),
            "Bruma/Kolbjorn ancient route overrides are missing")

    default_bos = (PACKAGE / "zz_Ensrick_Currency_10_DefaultSeptims_SWAP.ini").read_text(
        encoding="utf-8")
    require("chanceS(25)" in default_bos and "chanceS(5)" in default_bos and
            "0x000B6D~exchangeCurrency_enhanced.esp" in default_bos,
            "authored 75/20/5 loose Septim distribution changed")
    regional = (PACKAGE / "zz_Ensrick_Currency_80_Regional_SWAP.ini").read_text(
        encoding="utf-8")
    runtime_by_id = {family["id"]: family for family in config["families"]}
    for family_id in ("mede", "ulfric", "dram", "oshka", "ohzer", "varken"):
        tiers = runtime_by_id[family_id]["denominations"]
        for source, target in zip(runtime_by_id["septim"]["denominations"], tiers,
                                  strict=True):
            source_id, source_plugin = source["form"].split(":", 1)
            target_id, target_plugin = target["form"].split(":", 1)
            mapping = (f"0x{int(source_id, 16):06X}~{source_plugin}|"
                       f"0x{int(target_id, 16):06X}~{target_plugin}")
            require(mapping in regional,
                    f"{family_id}: BOS no longer maps {source['tier']} to matching tier")
    require("NorthwatchKeepLocation,SolitudeJusticiarsHeadquarters,ThalmorEmbassyLocation" in
            regional and "0xDE5023~Update.esm" in regional,
            "Dominion Sancar BOS route changed")
    require("Wyrmstooth" not in regional and "BeyondReach" not in regional and
            "arnima" not in regional.lower(),
            "Wyrmstooth/Beyond Reach must continue through Septim fallback")
    dram_bos = (PACKAGE / "MorrowindUsesDrams_SWAP.ini").read_text(encoding="utf-8")
    require(dram_bos.count("0x000823~exchangeCurrency_enhanced.esp|0x000824~") == 2 and
            dram_bos.count("0x000824~exchangeCurrency_enhanced.esp|0x000825~") == 2,
            "M.I.N.T. Solstheim/Raven Rock routes lost tier-to-tier mapping")


def validate_ui_and_runtime_overrides(config: dict[str, Any]) -> None:
    sky = PACKAGE / "SKSE/Plugins/SkyPatcher/misc"
    septim = (sky / "zz_Ensrick_Currency_SeptimWeights.ini").read_text(encoding="utf-8")
    for needle in (
        "0xb6d:value=1:weight=0.06:fullName=~Copper Septim~",
        "0x823:value=10:weight=0.07:fullName=~Silver Septim~",
        "0x824:value=100:weight=0.13:fullName=~Gold Septim~",
    ):
        require(needle in septim, f"Septim winning override missing {needle}")
    modern = (sky / "zz_Ensrick_Currency_ModernDenominations.ini").read_text(
        encoding="utf-8")
    for family in config["families"][1:7]:
        for denomination in family["denominations"]:
            require(f"value={denomination['value']}" in modern and
                    f"fullName=~{denomination['tier'].title()} {family['displayLabel']}~" in modern,
                    f"{family['id']} {denomination['tier']}: winning name/value missing")

    i4 = load_json(PACKAGE / "SKSE/Plugins/InventoryInjector/zz_Ensrick_CurrencyDenominations.json")
    require(len(i4["rules"]) == 3, "I4 must expose exactly copper/silver/gold rules")
    expected_by_color = {
        "#B87333": {i4_form(family["denominations"][0]["form"])
                    for family in config["families"]},
        "#C0C0C0": {i4_form(family["denominations"][1]["form"])
                    for family in config["families"] if len(family["denominations"]) == 3},
        "#D4AF37": {i4_form(family["denominations"][2]["form"])
                    for family in config["families"] if len(family["denominations"]) == 3},
    }
    for rule in i4["rules"]:
        require(rule["assign"]["subType"] == "Gold" and
                rule["assign"]["subTypeDisplay"] == "$Currency",
                "I4 physical denomination classification changed")
        color = rule["assign"]["iconColor"]
        actual = {item.lower() for item in rule["match"]["formId"]["anyOf"]}
        require(actual == expected_by_color[color], f"I4 {color} explicit form set changed")


def validate_sources_and_package(inputs: dict[str, Any], manifest: dict[str, Any]) -> None:
    runtime_receipt = manifest["runtimeConfig"]
    require(runtime_receipt["file"] == "SKSE/Plugins/EnsrickCurrencyDenominations.json" and
            runtime_receipt["sha256"] == sha256(RUNTIME_CONFIG) and
            runtime_receipt["bytes"] == RUNTIME_CONFIG.stat().st_size and
            runtime_receipt["strictParserFixture"] == "pass" and
            runtime_receipt["ledgerFingerprint"] == "EC66DF8F57CF4726",
            "runtime config parser/fingerprint receipt mismatch")
    expected_psc = {
        "DES_DramCurrencySwapper.psc", "DES_MadranSwapper.psc",
        "DES_UlfricCurrencySwapper.psc", "Ensrick_CurrencyRuntimeDefaultsAlias.psc",
    }
    require({path.name for path in (ROOT / "papyrus").glob("*.psc")} == expected_psc,
            "Papyrus source set must contain only the four owned compatibility scripts")
    for path in (ROOT / "papyrus").glob("*.psc"):
        text = path.read_text(encoding="utf-8").lower()
        require("swapcurrency(" not in text and "resetcurrency(" not in text and
                "setgoldvalue(" not in text and "registermodulequest(" not in text,
                f"{path.name}: legacy CurrencySwapper/value-owner call returned")
    dram_source = (ROOT / "papyrus/DES_DramCurrencySwapper.psc").read_text(encoding="utf-8")
    require('Quest.GetQuest("DES_UlfricWindhelmServicesQuest")' in dram_source and
            'Quest.GetQuest("DES_UlfricWindhelmServices")' not in dram_source,
            "Dram cost helper must resolve the exact audited Windhelm QUST EditorID")
    require(len(inputs["mintCompatibilitySources"]) == 4,
            "four exact M.I.N.T. compatibility source pins are required")

    asset_build = inputs.get("tierAssetBuild")
    require(asset_build is not None, "build-inputs.json is missing the tier-asset recipe")
    for field in ("recipe", "inputs", "finalizer", "receipt"):
        source_path = ROOT / asset_build[f"{field}RelativePath"]
        require(source_path.is_file() and sha256(source_path) == asset_build[f"{field}Sha256"],
                f"tier asset {field} source/receipt hash mismatch")
    asset_receipt = load_json(ROOT / asset_build["receiptRelativePath"])
    require(asset_receipt["status"] == "static-pass/runtime-unverified" and
            asset_receipt["privateOutputs"] is True and
            asset_receipt["recipeSha256"] == asset_build["recipeSha256"] and
            asset_receipt["inputReceiptSha256"] == asset_build["inputsSha256"] and
            asset_receipt["repeatability"] == asset_build["repeatability"],
            "tier asset provenance/repeatability receipt changed")
    outputs = asset_receipt["files"]
    require(len(outputs) == 36, "tier asset recipe must emit exact 18 NIF + 18 DDS files")
    require(sum(item["path"].lower().endswith(".nif") for item in outputs) == 18 and
            sum(item["path"].lower().endswith(".dds") for item in outputs) == 18,
            "tier asset recipe extensions/counts changed")
    for item in outputs:
        path = PACKAGE / item["path"]
        require(path.is_file(), f"tier asset missing: {item['path']}")
        require(path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"],
                f"tier asset receipt mismatch: {item['path']}")
        if path.suffix.lower() == ".dds":
            require(item["dds"]["width"] <= 1024 and item["dds"]["height"] <= 1024 and
                    item["dds"]["fourCC"] == "DX10",
                    f"{item['path']}: diffuse exceeds the approved 1K clutter cap")
        else:
            require(item["sseCompatible"] is True and
                    "exact OBJ geometry equality" in item["transform"] and
                    item["textureBindings"],
                    f"{item['path']}: NIF conversion/binding proof missing")

    dll = PACKAGE / "SKSE/Plugins/EnsrickCurrencyDenominations.dll"
    require(dll.is_file(), "deterministic native ledger-owner DLL is missing")
    native = manifest["nativePlugin"]
    native_build = inputs.get("nativeBuild")
    require(native_build is not None, "build-inputs.json is missing the native-build receipt")
    exact_keys(native_build, {
        "status", "receiptRelativePath", "receiptSha256", "packageSourceRoot",
        "sourceInputCount", "dllOutputPath", "dllSha256", "dllBytes",
        "repeatability", "commonLibUpstream", "commonLibCommit",
        "combinedBinaryLicense", "pluginSourceBundled",
    }, "nativeBuild")
    native_receipt_path = ROOT / native_build["receiptRelativePath"]
    require(native_receipt_path.is_file() and
            sha256(native_receipt_path) == native_build["receiptSha256"],
            "native build receipt hash mismatch")
    native_receipt = load_json(native_receipt_path)
    require(native_build["status"] == "deterministic-pass/runtime-unverified" and
            native_build["repeatability"] == "2/2 SHA256 and size identical" and
            native_build["pluginSourceBundled"] is True and
            native_build["commonLibUpstream"] ==
            "https://github.com/Ensrick/CommonLibSSE-NG" and
            native_build["commonLibCommit"] ==
            "90a64a4d65ce659a139137c968f42151bb6ecec9" and
            native_build["combinedBinaryLicense"] ==
            "GPL-3.0-or-later with CommonLibSSE-NG exceptions",
            "native build policy/provenance changed")
    require(native_receipt["commonLibCommit"] == native_build["commonLibCommit"] and
            native_receipt["commonLibTrackedStatus"] == "clean" and
            native_receipt["runtime"] == "1.7.104.0" and
            native_receipt["skse"] == "2.3.1" and
            native_receipt["runtimeConfig"]["sha256"] == sha256(RUNTIME_CONFIG) and
            native_receipt["runtimeConfig"]["bytes"] == RUNTIME_CONFIG.stat().st_size,
            "native receipt is not bound to the released runtime/config inputs")
    require(native_receipt["dll"]["relativePath"] == native_build["dllOutputPath"] and
            native_receipt["dll"]["sha256"] == native_build["dllSha256"] == sha256(dll) and
            native_receipt["dll"]["bytes"] == native_build["dllBytes"] == dll.stat().st_size,
            "native DLL differs from its deterministic build receipt")
    require(native["file"] == native_build["dllOutputPath"] and
            native["sha256"] == native_build["dllSha256"] and
            native["bytes"] == native_build["dllBytes"] and
            native["deterministicBuilds"] == 2 and
            native["buildReceiptSha256"] == native_build["receiptSha256"] and
            native["sourceInputFiles"] == native_build["sourceInputCount"] and
            native["correspondingSource"] == native_build["packageSourceRoot"] and
            native["commonLibCommit"] == native_build["commonLibCommit"],
            "manifest native DLL/source receipt differs from build-inputs.json")

    source_root = PACKAGE / native_build["packageSourceRoot"]
    require(source_root.is_dir(), "bundled Ensrick native source tree is missing")
    source_inputs = native_receipt["sourceInputs"]
    require(len(source_inputs) == native_build["sourceInputCount"] == 23,
            "native corresponding-source input count changed")
    expected_source_files = {item["relativePath"].replace("\\", "/") for item in source_inputs}
    expected_source_files.add("native-build-receipt.json")
    actual_source_files = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*") if path.is_file()
    }
    require(actual_source_files == expected_source_files,
            "bundled Ensrick native source tree differs from the exact build input set")
    for item in source_inputs:
        source_path = source_root / item["relativePath"]
        require(source_path.stat().st_size == item["bytes"] and
                sha256(source_path) == item["sha256"],
                f"bundled native source mismatch: {item['relativePath']}")
    bundled_receipt = source_root / "native-build-receipt.json"
    require(bundled_receipt.stat().st_size == native_receipt_path.stat().st_size and
            sha256(bundled_receipt) == native_build["receiptSha256"],
            "bundled native receipt differs from the tracked build receipt")

    license_files = {
        "LICENSE.txt", "NOTICE.txt", "SOURCE.txt", "DEPENDENCIES.txt",
        "COMMONLIBSSE-COPYING.txt", "COMMONLIBSSE-EXCEPTIONS.md",
        "QuickLootIE-LICENSE.txt",
    }
    require(all((PACKAGE / name).is_file() for name in license_files),
            "GPL/CommonLib/QuickLoot/source notice bundle is incomplete")
    common_lib_license = native_receipt["commonLibLicense"]
    require(sha256(PACKAGE / "COMMONLIBSSE-COPYING.txt") ==
            common_lib_license["copyingSha256"] ==
            "72D2F09334F8B87DDED94A833BA7DA05E5280E77A037CA23B251F96EAE4CF719" and
            sha256(PACKAGE / "COMMONLIBSSE-EXCEPTIONS.md") ==
            common_lib_license["exceptionsSha256"] ==
            "D3A3EC90E21AE118D3653D0834A2F6D1E6D32B773CC185023824992AD4BDCFCE",
            "CommonLibSSE-NG GPL/exception texts differ from the pinned checkout")
    quickloot_input = next(
        item for item in source_inputs
        if item["relativePath"] == "third_party/QuickLootIE-LICENSE.txt"
    )
    require(sha256(PACKAGE / "QuickLootIE-LICENSE.txt") == quickloot_input["sha256"] and
            (PACKAGE / "QuickLootIE-LICENSE.txt").stat().st_size == quickloot_input["bytes"],
            "QuickLoot IE MIT notice differs from the built source input")
    notice = (PACKAGE / "NOTICE.txt").read_text(encoding="utf-8")
    source = (PACKAGE / "SOURCE.txt").read_text(encoding="utf-8")
    dependencies = (PACKAGE / "DEPENDENCIES.txt").read_text(encoding="utf-8")
    require("GPL-3.0-or-later" in notice and "CommonLibSSE-NG" in notice and
            "combined DLL" in notice and "not an all-MIT" in notice,
            "NOTICE misstates the linked DLL's GPL distribution terms")
    require(native_build["commonLibCommit"] in dependencies and
            native_build["commonLibUpstream"] in dependencies and
            "QuickLoot" in dependencies,
            "dependency provenance is incomplete")
    require("corresponding source" in source.lower() and
            native_build["packageSourceRoot"] in source and
            native_build["commonLibCommit"] in source and
            "https://github.com/Ensrick/skyrim-mod-assistant.git" in source,
            "SOURCE.txt does not identify bundled plug-in source and external corresponding source")

    scripts = PACKAGE / "Scripts"
    expected_pex = {name.removesuffix(".psc") + ".pex" for name in expected_psc}
    require({path.name for path in scripts.glob("*.pex")} == expected_pex,
            "package PEX set still contains an old ECE/Ohzer transaction owner")
    manifest_scripts = {entry["file"]: entry for entry in manifest["papyrusScripts"]}
    require(set(manifest_scripts) == {f"Scripts/{name}" for name in expected_pex},
            "manifest Papyrus receipt set differs")
    for name in expected_pex:
        path = scripts / name
        receipt = manifest_scripts[f"Scripts/{name}"]
        require(receipt["sha256"] == sha256(path) and receipt["bytes"] == path.stat().st_size and
                receipt["deterministicCompilations"] == 2,
                f"{name}: PEX receipt mismatch")


def validate_generated_artifacts(manifest: dict[str, Any], policy: dict[str, Any]) -> None:
    plugin = PACKAGE / PLUGIN_NAME
    seq = PACKAGE / "SEQ/Ensrick Currency Integration Patch.seq"
    audit_path = WORK / "plugin-audit.json"
    require(plugin.is_file() and seq.is_file() and audit_path.is_file(),
            "run the checked generator before release validation")
    require(manifest["version"] == "0.3.0", "manifest version is not 0.3.0")
    require(manifest["runtimePatch"]["sha256"] == sha256(plugin) and
            manifest["runtimePatch"]["bytes"] == plugin.stat().st_size,
            "ESP receipt mismatch")
    require(manifest["runtimePatch"]["records"] == 286 and
            manifest["runtimePatch"]["ownedRecords"] == 169 and
            manifest["runtimePatch"]["recordsByType"] == {
                "ACTI": 3, "LVLI": 152, "MISC": 22, "GLOB": 1,
                "COBJ": 42, "QUST": 5, "KYWD": 1, "DIAL": 20, "INFO": 40,
            }, "manifest ESP record/type contract changed")

    audit = load_json(audit_path)
    require(audit["plugin"] == PLUGIN_NAME and audit["eslFlag"] is True,
            "plugin audit identity/ESL flag mismatch")
    require(audit["records"] == 286 and audit["deletedRecords"] == 0,
            "plugin must contain exactly 286 records and no deletions")
    require(audit["runtimeReasonCounters"] == policy["runtimeReasonCounters"],
            "plugin audit telemetry contract differs from runtime policy")
    require(audit["masters"] == [
        "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "SL99Exchanger.esp",
        "exchangeCurrency_enhanced.esp", "C.O.I.N.esp", "M.I.N.T.esp",
        "MorrowindUsesDrams.esp", "WindhelmUsesUlfrics.esp",
        "exchangeCurrency_patch_COIN.esp",
    ], "exact eleven-master set/order changed")
    require(audit["disabledRecipeCount"] == 33 and
            audit["disabledCurrencyToIngotRecipeCount"] == 17 and
            audit["disabledModernBankRecipeCount"] == 16,
            "disabled recipe counts changed")
    require(len(audit["disabledMintExchangeInfos"]) == 38 and
            len(audit["mintBackendConditionInfos"]) == 2,
            "M.I.N.T. dialogue audit counts changed")
    require(len(audit["dialogParentScopes"]) == 20 and
            sum(len(parent["responseFormKeys"]) for parent in audit["dialogParentScopes"]) == 40 and
            all(parent["metadataIdentical"] is True for parent in audit["dialogParentScopes"]),
            "M.I.N.T. parent DIAL scope/metadata audit changed")
    require(len(audit["neutralizedEcePlayerCurrencyQuests"]) == 2 and
            len(audit["mintCostOnlyQuestBindings"]) == 2,
            "transaction-owner/cost-only quest audit counts changed")
    require(audit["madranTransactionRemoval"]["removedScript"] == "DES_MadranSwapper",
            "Ma'dran transaction alias was not removed")

    expected_seq_id = (11 << 24) | 0x800
    require(seq.read_bytes() == struct.pack("<I", expected_seq_id),
            "SEQ must contain only file-relative QUST 0B000800")
    require(audit["runtimeQuest"]["seqFileRelativeFormId"] == f"{expected_seq_id:08X}",
            "plugin audit SEQ identity changed")


def main() -> None:
    policy = load_json(ROOT / "policy.json")
    inputs = load_json(ROOT / "build-inputs.json")
    config = load_json(RUNTIME_CONFIG)
    manifest = load_json(ROOT / "manifest.json")

    validate_policy(policy)
    validate_runtime_config(config, policy)
    validate_distribution_configs(config)
    validate_ui_and_runtime_overrides(config)
    validate_sources_and_package(inputs, manifest)
    validate_generated_artifacts(manifest, policy)
    print("currency integration v0.3.0 static/release validation: PASS")


if __name__ == "__main__":
    main()
