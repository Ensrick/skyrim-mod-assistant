#!/usr/bin/env python3
"""Fail-closed static/release gate for the complete-tier v0.4.0 integration."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "package"
WORK = ROOT / "work"
PLUGIN_NAME = "Ensrick Currency Integration Patch.esp"
PURSE_PLUGIN_NAME = "Ensrick Currency Regional Purses.esp"
RUNTIME_CONFIG = PACKAGE / "SKSE/Plugins/EnsrickCurrencyDenominations.json"
sys.path.insert(0, str(ROOT.parents[1] / "audit"))
sys.path.insert(0, str(ROOT))
import currency_tier_contract as tier_contract
import currency_bos_gate
import currency_purse_gate
from currency_save_gate import ledger_fingerprint
import generate_bos


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
    exact_keys(denominations, {"canonicalPercent", "variantPercent", "tieredFamilies"},
               "complete denomination policy")
    require((denominations["canonicalPercent"], denominations["variantPercent"]) == (80, 20),
            "policy distribution is not exact 80/20")

    families = denominations["tieredFamilies"]
    require(len(families) == 18 and {family["id"] for family in families} ==
            set(tier_contract.DESIGNS), "complete 18-design policy is required")
    require(all(family["enabled"] is True for family in families),
            "no currency design may remain disabled in the complete release")
    septim = next(family for family in families if family["id"] == "septim")
    septim_tiers = [septim["tiers"][tier] for tier in ("copper", "silver", "gold")]
    require([entry["sourceValue"] for entry in septim_tiers] == [1, 25, 100],
            "Septim source values changed; silver 25->10 correction is not pinned")
    require([entry["name"] for entry in septim_tiers] ==
            ["Copper Septim", "Silver Septim", "Gold Septim"],
            "Septim tier names changed")

    for family in families:
        title = family["displayLabel"]
        tiers = [family["tiers"][tier] for tier in ("copper", "silver", "gold")]
        require([entry["value"] for entry in tiers] == [1, 10, 100],
                f"{family['id']}: named tier values must be 1/10/100")
        require([entry["name"] for entry in tiers] ==
                [f"Copper {title}", f"Silver {title}", f"Gold {title}"],
                f"{family['id']}: explicit tier names changed")
        require(family["runtimeWeight"] in (0.01, 0.02),
                f"{family['id']}: approved per-family weight changed")
    sancar = next(family for family in families if family["id"] == "sancar")
    require(sancar["ownedRouteKeywordFormId"] == "000803" and
            sancar["ownedRouteKeywordEditorId"] == "Ensrick_IsSancarMoney",
            "owned Sancar route keyword changed")

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
    require(len(ancient) == 9, "exact nine compatibility exchange recipes are required")
    require(all(item["inputCount"] == item["outputCount"] == 1 and
                item["outputFormKey"] == "00000F:Skyrim.esm" for item in ancient),
            "ancient compatibility recipes must preserve 1:1 backend value")

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
    require(config["schemaVersion"] == 2 and
            config["configId"] == "ensrick-currency-denominations-v0.4.0",
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
    exact_keys(config["routing"], {"precedence", "rules"}, "runtime routing")
    require(config["routing"]["precedence"] == [
        "questExceptions", "regionalRoutes", "septimFallback",
    ], "runtime route precedence changed or ancient bypass returned")
    rules = config["routing"]["rules"]
    tier_contract.complete_routes(config)
    require([rule["id"] for rule in rules] == [
        "bruma-ayleid", "ayleid", "falmer", "root-cave", "nordic-ruin",
        "dwemer-ruin", "drakr-region", "sancar-dominion", "mede-region",
        "ulfric-region", "dram-region", "oshka-region", "ohzer-region", "varken-deadlands",
    ], "exact cultural/site route order changed")
    routed = {identity for rule in rules for identity in rule["familyIds"]}
    require(routed == set(tier_contract.DESIGNS) - {"septim"},
            "some non-fallback currency designs have no distribution route")

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
            "00080F:C.O.I.N.esp", "00080E:C.O.I.N.esp", "00080D:C.O.I.N.esp",
            "000934:C.O.I.N.esp", "000935:C.O.I.N.esp", "000936:C.O.I.N.esp",
            "00093D:C.O.I.N.esp", "00093E:C.O.I.N.esp", "00093F:C.O.I.N.esp",
            "000C5D:C.O.I.N.esp", "000C5E:C.O.I.N.esp", "000C5F:C.O.I.N.esp",
            "000F1C:M.I.N.T.esp", "000F1D:M.I.N.T.esp", "000F1E:M.I.N.T.esp",
            "000F1F:M.I.N.T.esp", "000F20:M.I.N.T.esp", "000F21:M.I.N.T.esp",
            "000F22:M.I.N.T.esp", "000F23:M.I.N.T.esp", "000F24:M.I.N.T.esp",
        ],
        "budgetLists": [
            "0D790B:Skyrim.esm", "0D8E7D:Skyrim.esm", "0D8E7E:Skyrim.esm",
            "000800:C.O.I.N.esp", "000801:C.O.I.N.esp", "000802:C.O.I.N.esp",
            "00080B:C.O.I.N.esp", "00080C:C.O.I.N.esp", "00080A:C.O.I.N.esp",
            "000937:C.O.I.N.esp", "000938:C.O.I.N.esp", "000939:C.O.I.N.esp",
            "000940:C.O.I.N.esp", "000941:C.O.I.N.esp", "000942:C.O.I.N.esp",
            "000C61:C.O.I.N.esp", "000C62:C.O.I.N.esp", "000C63:C.O.I.N.esp",
            "000F2B:M.I.N.T.esp", "000F2C:M.I.N.T.esp", "000F2D:M.I.N.T.esp",
            "000F2E:M.I.N.T.esp", "000F2F:M.I.N.T.esp", "000F30:M.I.N.T.esp",
            "000F31:M.I.N.T.esp", "000F32:M.I.N.T.esp", "000F33:M.I.N.T.esp",
        ],
    }, "typed purse FLOR/LVLI allowlists changed")
    require(config["telemetry"]["requiredReasonCounters"] is True and
            config["telemetry"]["reasonCounters"] == policy["runtimeReasonCounters"] and
            len(config["telemetry"]["reasonCounters"]) == 14 and
            "source-ancient-passthrough" not in config["telemetry"]["reasonCounters"],
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
    tier_contract.complete_designs(policy, config)
    require(all(family["enabled"] is True for family in families),
            "complete release must enable all supported currency designs")
    require(sum(item["enabled"] and item["fallback"] for item in families) == 1 and
            families[0]["id"] == "septim" and families[0]["fallback"],
            "Septim must be the sole enabled fallback")


def validate_distribution_configs(config: dict[str, Any]) -> None:
    cdf = PACKAGE / "SKSE/Plugins/ContainerDistributionFramework"
    masked = [
        "00_Ensrick_Currency_30_Varken.json", "EC_medes.json",
        "EC_ohzers.json", "EC_oshkas.json", "EC_septims_containers.json",
        "EC_ulfrics.json", "EC_varkens.json", "MorrowindUsesDrams.json",
        "WindhelmUsesUlfrics.json", "DominionUsesSancar.json",
        "C.O.I.N.json", "EC_drams_drakrs.json", "00_Ensrick_Currency_10_BrumaAyleid.json",
        "zz_Ensrick_Currency_99_KolbjornCanonicalDrakr.json",
    ]
    require({path.name for path in cdf.glob('*.json')} == set(masked),
            "currency CDF mask set differs from the fourteen inspected legacy owners")
    for name in masked:
        require(load_json(cdf / name) == {"rules": []},
                f"unsafe pre-native CDF currency owner not fully masked: {name}")

    locations = load_json(ROOT / "bos-location-roots.json")
    require(locations['schemaVersion'] == 1 and
            locations['runtimeConfigSha256'] == sha256(RUNTIME_CONFIG) and
            locations['sourceInventorySha256'] ==
            '8625F2F3094F406EE552B27C506712B9EA3E7F51E5BB7AFE21D9CD9ED35B7B52' and
            locations['sourceScriptSha256'] ==
            'BAA42E9FCBEDB51CFEF3BF0265B7997DE20893DC6F6CBD054C1D1FEA63D90DE9',
            'BOS location roots are not bound to the reviewed source/config inventory')
    roots = locations["routeLocations"]
    require(set(roots) == {rule['id'] for rule in config['routing']['rules']} and
            sum(len(items) for items in roots.values()) == 152 and
            all(len(items) == len(set(items)) for items in roots.values()),
            'BOS minimal location-root coverage changed')
    expected_kid = set()
    for assignment in locations['requiredKidAssignments']:
        location = assignment['location']
        require(location['type'] == 'LCTN' and location['deleted'] is False,
                'currency KID target is not an inspected live LCTN')
        keyword = generate_bos.bos_form(assignment['keyword'])
        target = generate_bos.bos_form(location['formKey'])
        expected_kid.add(f'Keyword = {keyword}|Location|{target}'.casefold())
    require(len(expected_kid) == 9, 'exact nine source-proven KID repairs required')
    expected_kid.update({
        'Keyword = 0x000803~Ensrick Currency Integration Patch.esp|Location|NorthwatchKeepLocation'.casefold(),
        'Keyword = 0x000803~Ensrick Currency Integration Patch.esp|Location|ThalmorEmbassyLocation'.casefold(),
    })
    actual_kid = []
    for name in ('AncientSites', 'Deadlands', 'Sancar'):
        text = (PACKAGE / f'zz_Ensrick_Currency_{name}_KID.ini').read_text(encoding='utf-8')
        actual_kid.extend(line.strip().casefold() for line in text.splitlines()
                          if line.strip() and not line.lstrip().startswith(';'))
    require(len(actual_kid) == len(expected_kid) and set(actual_kid) == expected_kid,
            'currency KID repairs differ from exact inspected location/keyword pairs')
    expected = generate_bos.build(config, roots)
    actual = {path.name: path.read_text(encoding='utf-8') for path in PACKAGE.glob('*_SWAP.ini')}
    require(actual == expected, "BOS source/output file set differs from deterministic generation")
    for name, text in expected.items():
        require((PACKAGE / name).read_bytes() == text.encode('utf-8'),
                f"BOS output is not byte-reproducible: {name}")
    currency_bos_gate.check(config, actual, roots, generate_bos.PURSES)


def validate_skypatcher_legacy_masks(sky: Path) -> None:
    # SkyPatcher's file enumeration is not a certified ordering contract.
    # Same-path MO2 overrides remove all competing physical writes, retaining
    # the five original nonphysical ledger/display effects verbatim.
    expected = {
        'ECE_regionalCurrencies.ini': (
            '; Owned same-path compatibility mask for Exchange Currency Enhanced.\n'
            '; All eleven legacy regional coin edits are superseded by the complete-tier\n'
            '; ModernDenominations configuration. No active rows: no file-order dependency.\n'
        ),
        'ECE_septims_100.ini': (
            '; Owned same-path compatibility override for Exchange Currency Enhanced.\n'
            '; Preserve the hidden ledger and four plural-display forms only. Physical\n'
            '; Septim values and weights are owned solely by SeptimWeights, regardless of\n'
            '; SkyPatcher file iteration order.\n'
            'filterByMiscs= skyrim.esm|0xf:value=1:weight=0:fullName=~Septim~\n'
            'filterByMiscs= exchangeCurrency_enhanced.esp|0xbd2:fullName=~Septims~\n'
            'filterByMiscs= exchangeCurrency_enhanced.esp|0xbd0:fullName=~Copper Septims~\n'
            'filterByMiscs= exchangeCurrency_enhanced.esp|0xbcf:fullName=~Silver Septims~\n'
            'filterByMiscs= exchangeCurrency_enhanced.esp|0xbd1:fullName=~Gold Septims~\n'
        ),
    }
    required = set(expected) | {
        'zz_Ensrick_Currency_SeptimWeights.ini',
        'zz_Ensrick_Currency_ModernDenominations.ini',
        'zz_Ensrick_Currency_AncientWeights.ini',
    }
    require({path.relative_to(sky).as_posix() for path in sky.rglob('*.ini')} == required,
            'SkyPatcher misc file set changed; an omitted mask or extra writer is unsafe')
    for name, text in expected.items():
        require((sky / name).read_bytes() == text.encode('utf-8'),
                f'SkyPatcher exact same-path compatibility override changed: {name}')
    ancient = (sky / 'zz_Ensrick_Currency_AncientWeights.ini').read_text(encoding='utf-8')
    require(not any(line.strip() and not line.lstrip().startswith(';')
                    for line in ancient.splitlines()),
            'obsolete ancient weight file must remain an inert compatibility mask')


def validate_ui_and_runtime_overrides(config: dict[str, Any]) -> None:
    sky = PACKAGE / "SKSE/Plugins/SkyPatcher/misc"
    validate_skypatcher_legacy_masks(sky)
    septim = (sky / "zz_Ensrick_Currency_SeptimWeights.ini").read_text(encoding="utf-8")
    for needle in (
        "0xb6d:value=1:weight=0.06:fullName=~Copper Septim~",
        "0x823:value=10:weight=0.07:fullName=~Silver Septim~",
        "0x824:value=100:weight=0.13:fullName=~Gold Septim~",
    ):
        require(needle in septim, f"Septim winning override missing {needle}")
    modern = (sky / "zz_Ensrick_Currency_ModernDenominations.ini").read_text(
        encoding="utf-8")
    tier_contract.skypatcher_values(config, [septim, modern])

    i4 = load_json(PACKAGE / "SKSE/Plugins/InventoryInjector/zz_Ensrick_CurrencyDenominations.json")
    require(len(i4["rules"]) == 3, "I4 must expose exactly copper/silver/gold rules")
    expected_by_color = {
        "#B87333": {i4_form(item["form"])
                    for family in config["families"]
                    for item in [family["denominations"][0], *family.get("inputAliases", [])]},
        "#C0C0C0": {i4_form(family["denominations"][1]["form"])
                    for family in config["families"]},
        "#D4AF37": {i4_form(family["denominations"][2]["form"])
                    for family in config["families"]},
    }
    require({rule["assign"]["iconColor"] for rule in i4["rules"]} == set(expected_by_color),
            "I4 must contain each distinct metal color once")
    for rule in i4["rules"]:
        require(rule["assign"]["subType"] == "Gold" and
                rule["assign"]["subTypeDisplay"] == "$Currency",
                "I4 physical denomination classification changed")
        color = rule["assign"]["iconColor"]
        actual = {item.lower() for item in rule["match"]["formId"]["anyOf"]}
        require(actual == expected_by_color[color] and
                len(actual) == len(rule["match"]["formId"]["anyOf"]),
                f"I4 {color} explicit form set changed or contains duplicates")


def validate_sources_and_package(inputs: dict[str, Any], manifest: dict[str, Any]) -> None:
    runtime_receipt = manifest["runtimeConfig"]
    require(runtime_receipt["file"] == "SKSE/Plugins/EnsrickCurrencyDenominations.json" and
            runtime_receipt["sha256"] == sha256(RUNTIME_CONFIG) and
            runtime_receipt["bytes"] == RUNTIME_CONFIG.stat().st_size and
            runtime_receipt["strictParserFixture"] == "pass" and
            runtime_receipt["ledgerFingerprint"] == "6270B86774F9F4F3" ==
            f"{ledger_fingerprint(load_json(RUNTIME_CONFIG)):016X}",
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
    require(asset_receipt["schemaVersion"] == 2 and
            asset_receipt["designCount"] == 17 and asset_receipt["designTierCount"] == 51 and
            asset_receipt["outputCount"] == len(outputs) == 108,
            "tier recipe must cover all 17 non-Septim designs and 51 design/metal pairs")
    asset_manifest = manifest['tierAssets']
    require(asset_manifest['families'] == [family['displayLabel'] for family in
            load_json(ROOT / 'policy.json')['denominations']['tieredFamilies'] if family['id'] != 'septim'] and
            asset_manifest['tiers'] == ['Copper', 'Silver', 'Gold'] and
            asset_manifest['nifFiles'] == 51 and asset_manifest['diffuseFiles'] == 57 and
            asset_manifest['diffuseResolutionCap'] == 1024 and
            asset_manifest['recipeSha256'] == asset_build['recipeSha256'] and
            asset_manifest['receiptSha256'] == asset_build['receiptSha256'] and
            asset_manifest['repeatability'] == asset_receipt['repeatability'],
            'manifest tier coverage/provenance still describes a partial or stale asset build')
    require(sum(item["path"].lower().endswith(".nif") for item in outputs) == 51 and
            sum(item["path"].lower().endswith(".dds") for item in outputs) == 57,
            "tier asset recipe extensions/counts changed")
    require(len({item["path"].casefold() for item in outputs}) == len(outputs),
            "asset receipt contains duplicate paths")
    required_models = {tier["model"].replace("\\", "/").casefold()
                       for family in load_json(ROOT / "policy.json")["denominations"]["tieredFamilies"]
                       if family["id"] != "septim" for tier in family["tiers"].values()}
    actual_models = {item["path"].casefold() for item in outputs
                     if item["path"].lower().endswith(".nif")}
    require(required_models == actual_models,
            "asset output models do not match every policy design/metal path")
    require(asset_receipt["preservedV030Baseline"]["preservedOutputCount"] == 36 and
            asset_receipt["preservedV030Baseline"]["status"] ==
            "36/36 path, size, and SHA256 tuples unchanged",
            "existing six-family assets drifted during the coverage expansion")
    for item in outputs:
        path = PACKAGE / item["path"]
        require(path.is_file(), f"tier asset missing: {item['path']}")
        require(path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"],
                f"tier asset receipt mismatch: {item['path']}")
        if path.suffix.lower() == ".dds":
            require(item["dds"]["width"] <= 1024 and item["dds"]["height"] <= 1024 and
                    item["dds"]["fourCC"] == "DX10" and item["dds"]["mips"] ==
                    math.floor(math.log2(max(item["dds"]["width"], item["dds"]["height"]))) + 1,
                    f"{item['path']}: diffuse exceeds 1K clutter cap or lacks full mip chain")
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
    license_scope = (PACKAGE / "LICENSE.txt").read_text(encoding='utf-8')
    require('LICENSE SCOPE' in license_scope and 'not under MIT alone' in license_scope and
            'mixed-terms works' in license_scope,
            "package license lost its mixed-work/vendor/native scope limitation")
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
    require(manifest["version"] == "0.4.0", "manifest version is not 0.4.0")
    require(manifest["runtimePatch"]["sha256"] == sha256(plugin) and
            manifest["runtimePatch"]["bytes"] == plugin.stat().st_size,
            "ESP receipt mismatch")
    require(manifest["runtimePatch"]["records"] == 1772 and
            manifest["runtimePatch"]["ownedRecords"] == 1623 and
            manifest["runtimePatch"]["recordsByType"] == {
                "ACTI": 3, "LVLI": 1605, "MISC": 55, "GLOB": 1,
                "COBJ": 42, "QUST": 5, "KYWD": 1, "DIAL": 20, "INFO": 40,
            }, "manifest ESP record/type contract changed")

    # Independently decode the serialized MISC catalog, not only the generator
    # policy or runtime override text. Copper Septim already satisfies the
    # exact source contract and deliberately needs no override; the C# winning-
    # source audit still verifies it. All other physical forms are in this ESP.
    binary = currency_purse_gate.read_plugin(plugin, {'MISC'})
    expected_coins = {}
    config = load_json(RUNTIME_CONFIG)
    policies = {row['id']: row for row in policy['denominations']['tieredFamilies']}
    for family in config['families']:
        for coin in [*family['denominations'], *family.get('inputAliases', [])]:
            tier = policies[family['id']]['tiers'][coin['tier']]
            expected_coins[currency_purse_gate.normalized(coin['form'])] = tier
    source_only = '000B6D:exchangecurrency_enhanced.esp'
    require(set(binary.records) == (set(expected_coins) - {source_only}) | {'00000F:skyrim.esm'} and
            len(expected_coins) == 55,
            'serialized MISC catalog omits or invents a recognized physical currency form')
    for key, tier in expected_coins.items():
        if key == source_only:
            continue
        record = binary.records[key]
        require(struct.unpack('<If', record.one(b'DATA', 8))[0] == tier['value'],
                f'{key}: serialized denomination value is wrong')
        require(record.one(b'FULL').rstrip(b'\0').decode('utf-8') == tier['name'],
                f'{key}: serialized denomination name is wrong')
        model = record.one(b'MODL').rstrip(b'\0').decode('utf-8').replace('\\', '/').casefold()
        require(model == tier['model'].replace('\\', '/').casefold(),
                f'{key}: serialized denomination model is wrong')
        keywords = record.one(b'KWDA')
        require(len(keywords) % 4 == 0 and '0FF9FB:skyrim.esm' in
                {binary.link(keywords[offset:offset+4]) for offset in range(0, len(keywords), 4)},
                f'{key}: serialized coin can be sold twice or has malformed keywords')

    audit = load_json(audit_path)
    require(audit["plugin"] == PLUGIN_NAME and audit["eslFlag"] is True,
            "plugin audit identity/ESL flag mismatch")
    require(audit["records"] == 1772 and audit["deletedRecords"] == 0,
            "integration plugin must contain exactly 1772 records and no deletions")
    require(audit["runtimeReasonCounters"] == policy["runtimeReasonCounters"],
            "plugin audit telemetry contract differs from runtime policy")
    catalog = audit['denominations']
    require(catalog['physicalFormsAudited'] == 55 and catalog['outputValues'] == [1, 10, 100] and
            len(catalog['tieredFamilies']) == 18 and
            {row['id'] for row in catalog['tieredFamilies']} == set(tier_contract.DESIGNS) and
            all(row['Enabled'] is True and len(row['tiers']) == 3
                for row in catalog['tieredFamilies']) and
            sum(len(row['sourceAliases']) for row in catalog['tieredFamilies']) == 1,
            'exact winning-source audit does not account for all54canonicalcoins+alias')
    require(audit["masters"] == [
        "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "BSAssets.esm", "SL99Exchanger.esp",
        "exchangeCurrency_enhanced.esp", "C.O.I.N.esp", "M.I.N.T.esp",
        "MorrowindUsesDrams.esp", "WindhelmUsesUlfrics.esp",
        "exchangeCurrency_patch_COIN.esp",
    ], "exact twelve-master set/order changed")
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

    expected_seq_id = (12 << 24) | 0x800
    require(seq.read_bytes() == struct.pack("<I", expected_seq_id),
            "SEQ must contain only file-relative QUST 0C000800")
    require(audit["runtimeQuest"]["seqFileRelativeFormId"] == f"{expected_seq_id:08X}",
            "plugin audit SEQ identity changed")

    graph = audit['regionalPurseGraph']
    require(graph['ownedNodes'] == 1434 and graph['ownedFormIdRanges'] ==
            [['000990', '0009FF'], ['000A16', '000F3F']] and
            graph['exactSourceProbabilityDag'] is True and
            graph['wholePurseCanonicalPercent'] == 80 and
            graph['wholePurseSingleBreakPercent'] == 20 and
            graph['noCrossFamilyLeaves'] is True and graph['noCrossFamilyNodes'] is True and
            graph['acyclic'] is True and len(graph['flattenedDistributions']) == 24,
            'main regional purse probability/ownership audit changed')

    companion = PACKAGE / PURSE_PLUGIN_NAME
    require(companion.is_file(), 'mandatory regional purse companion ESP is missing')
    receipt = manifest['regionalPursePatch']
    require(receipt['plugin'] == PURSE_PLUGIN_NAME and receipt['sha256'] == sha256(companion) and
            receipt['bytes'] == companion.stat().st_size and receipt['eslFlagged'] is True and
            receipt['records'] == receipt['ownedRecords'] == 405 and
            receipt['recordsByType'] == {'FLOR': 15, 'LVLI': 390} and
            receipt['directMasters'] == ['Skyrim.esm', 'Update.esm', 'BSAssets.esm',
                'exchangeCurrency_patch_COIN.esp', PLUGIN_NAME] and
            receipt['seqFileRelativeFormIds'] == [],
            'regional purse companion manifest/hash contract changed')
    require({path.name for path in (PACKAGE / 'SEQ').glob('*.seq')} == {seq.name},
            'companion must not introduce an extra start-game SEQ')
    proof = load_json(WORK / 'regional-purse-independent-audit.json')
    require(proof['status'] == 'offline-binary-and-exact-probability-pass; not in-game verification' and
            proof['companionSha256'] == sha256(companion) and
            proof['mainSha256'] == sha256(plugin) and
            proof['verifierSha256'] == sha256(ROOT.parents[1] / 'audit/currency_purse_gate.py') and
            proof['parserHelpersCanonicalLfSha256'] == hashlib.sha256(
                (ROOT.parents[1] / 'audit/biped_slot_audit.py').read_bytes().replace(b'\r\n', b'\n')).hexdigest().upper() and
            proof['additionalInputHashes'] == {'policy': sha256(ROOT / 'policy.json'),
                                              'config': sha256(RUNTIME_CONFIG)} and
            proof['masters'] == receipt['directMasters'] and proof['ownedRecords'] == 405 and
            proof['floraClones'] == 15 and proof['reachableLists'] == 390,
            'independent binary purse proof is stale or incomplete')
    require(proof['sourceStrings']['archiveSha256'] ==
            'E3D0C8D13D76DDB5CF9FC4CFFE916475B708EA6CAC2A46956442A558F14324DE' and
            proof['sourceStrings']['memberSha256'] ==
            '9EBA6DE4D1CF9F71816C0571B3D407F54B4251F91386233DFF6B666420E17405' and
            proof['sourceStrings']['bytes'] == 833794 and
            proof['sourceStrings']['member'] == 'strings/skyrim_english.strings' and
            proof['sourceStrings']['recipeSha256'] == sha256(ROOT / 'assets/recipe.py') and
            proof['sourceStrings']['canonicalLfReaderSha256'] ==
            load_json(ROOT / 'assets/inputs.json')['bsaReaderSha256'],
            'independent FLOR localization proof is not bound to the original source strings')
    require(len(proof['purses']) == 15 and all(row['totalProbability'] == '1' and
            row['canonicalFraction'] == '4/5' and row['singleBreakFraction'] == '1/5'
            for row in proof['purses']), 'independent purse probability proof is incomplete')


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
    print("currency integration v0.4.0 static/release validation: PASS")


if __name__ == "__main__":
    main()
