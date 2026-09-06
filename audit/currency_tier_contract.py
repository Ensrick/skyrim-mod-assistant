"""Independent complete-design/tier gate; no game, assets, or profile writes."""
from pathlib import PureWindowsPath


VALUES = {"copper": 1, "silver": 10, "gold": 100}
PLUGIN = "Ensrick Currency Integration Patch.esp"
# Audited installed currency designs, not the implementation's self-reported set.
DESIGNS = {
    "septim": "000B6D:exchangeCurrency_enhanced.esp",
    "mede": "DE5021:Update.esm",
    "ulfric": "DE5024:Update.esm",
    "dram": "DE5029:Update.esm",
    "oshka": "000871:exchangeCurrency_patch_COIN.esp",
    "ohzer": "00086F:exchangeCurrency_patch_COIN.esp",
    "varken": "000870:exchangeCurrency_patch_COIN.esp",
    "drakr_dragon": "DE5012:Update.esm",
    "drakr_moth": "DE5013:Update.esm",
    "drakr_owl": "DE5014:Update.esm",
    "drakr_whale": "DE5015:Update.esm",
    "gibber_dementia": "DE5017:Update.esm",
    "gibber_mania": "DE5018:Update.esm",
    "mala": "DE5019:Update.esm",
    "mallari": "DE5020:Update.esm",
    "nchuark": "DE5022:Update.esm",
    "sancar": "DE5023:Update.esm",
    "bruma_ayleid_mala": "6028DC:BSAssets.esm",
}
ALIASES = {"gibber_mania": [("copper", "DE5027:Update.esm")]}
PREVIOUS_TIERS = {
    "septim": ("000823:exchangeCurrency_enhanced.esp", "000824:exchangeCurrency_enhanced.esp"),
    **{identity: (f"{0x820+2*i:06X}:{PLUGIN}", f"{0x821+2*i:06X}:{PLUGIN}")
       for i, identity in enumerate(("mede", "ulfric", "dram", "oshka", "ohzer", "varken"))},
}
ROUTES = [
    ("bruma-ayleid", ["08400C:BSHeartland.esm"], ["bruma_ayleid_mala"]),
    ("ayleid", ["DE5039:Update.esm", "000D61:ccbgssse067-daedinv.esm"], ["mala"]),
    ("falmer", ["DE5038:Update.esm"], ["mallari"]),
    ("root-cave", ["DE5040:Update.esm"], ["gibber_dementia", "gibber_mania"]),
    ("nordic-ruin", ["0130F2:Skyrim.esm"],
     ["drakr_dragon", "drakr_moth", "drakr_owl", "drakr_whale"]),
    ("dwemer-ruin", ["0130F0:Skyrim.esm", "000B91:exchangeCurrency_enhanced.esp"], ["nchuark"]),
    ("drakr-region", ["000B93:exchangeCurrency_enhanced.esp", "000B90:exchangeCurrency_enhanced.esp"],
     ["drakr_dragon", "drakr_moth", "drakr_owl", "drakr_whale"]),
    ("sancar-dominion", ["000803:Ensrick Currency Integration Patch.esp"], ["sancar"]),
    ("mede-region", ["000B94:exchangeCurrency_enhanced.esp"], ["mede"]),
    ("ulfric-region", ["000B73:exchangeCurrency_enhanced.esp"], ["ulfric"]),
    ("dram-region", ["000B92:exchangeCurrency_enhanced.esp"], ["dram"]),
    ("oshka-region", ["000BB4:exchangeCurrency_enhanced.esp"], ["oshka"]),
    ("ohzer-region", ["000BB5:exchangeCurrency_enhanced.esp"], ["ohzer"]),
    ("varken-deadlands", ["000BB6:exchangeCurrency_enhanced.esp"], ["varken"]),
]


def complete_routes(config):
    expected = [{"id": identity, "anyKeywords": keywords, "familyIds": families}
                for identity, keywords, families in ROUTES]
    need(config["routing"] == {
        "precedence": ["questExceptions", "regionalRoutes", "septimFallback"],
        "rules": expected}, "exact inventoried route keyword/design matrix differs")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def form_key(text):
    need(isinstance(text, str) and text.count(":") == 1, "invalid FormKey")
    local, plugin = text.split(":")
    need(1 <= len(local) <= 6 and all(c in "0123456789abcdefABCDEF" for c in local)
         and plugin and plugin == plugin.strip(), "invalid FormKey")
    return f"{int(local, 16):06x}:{plugin.casefold()}"


def named_tiers(family):
    """No sorted-value-set loophole: each metal must have its own exact value."""
    label = family.get("id", "unknown family")
    need("legacySingleton" not in family, f"{label}: singleton exemption is forbidden")
    tiers = family.get("denominations")
    need(isinstance(tiers, list) and len(tiers) == 3, f"{label}: requires all three tiers")
    need([item.get("tier") for item in tiers] == list(VALUES),
         f"{label}: exact copper/silver/gold order and names required")
    seen = set()
    for item in tiers:
        tier, value = item["tier"], item.get("value")
        need(type(value) is int and value == VALUES[tier],
             f"{label}: {tier} must be worth {VALUES[tier]}")
        key = form_key(item.get("form"))
        need(key not in seen, f"{label}: duplicate tier FormKey")
        seen.add(key)
    return seen


def all_families(config):
    families = config.get("families")
    need(isinstance(families, list) and families, "no currency families")
    seen_ids, seen_forms = set(), set()
    for family in families:
        identity = family.get("id")
        need(isinstance(identity, str) and identity and identity not in seen_ids,
             "missing or duplicate currency design")
        seen_ids.add(identity)
        keys = named_tiers(family)
        need(not keys & seen_forms, f"{identity}: form shared across designs")
        seen_forms.update(keys)
        for alias in family.get("inputAliases", []):
            need(set(alias) == {"tier", "form"} and alias["tier"] in VALUES,
                 f"{identity}: alias must name one existing tier")
            key = form_key(alias["form"])
            need(key not in seen_forms, f"{identity}: duplicate alias/canonical form")
            seen_forms.add(key)
    backend = form_key(config["accounting"]["backendForm"])
    need(backend not in seen_forms, "hidden backend cannot also be a physical coin")
    return seen_ids, seen_forms


def complete_designs(policy, config):
    """Cross-check all 18 independently inventoried designs and their alias."""
    ids, forms = all_families(config)
    need(ids == set(DESIGNS), f"incomplete design coverage: missing={sorted(set(DESIGNS)-ids)}, extra={sorted(ids-set(DESIGNS))}")
    need(len(forms) == 55, "expected 54 canonical tier forms and one input alias")
    definitions = policy["denominations"]["tieredFamilies"]
    need(len(definitions) == len(DESIGNS) and {f["id"] for f in definitions} == ids,
         "policy must account for all 18 designs exactly once")
    runtime = {family["id"]: family for family in config["families"]}
    need(not policy["denominations"].get("singletonFamilies"), "policy still exempts singleton coins")
    for definition in definitions:
        identity = definition["id"]
        family = runtime[identity]
        need(form_key(definition["primarySource"]["formKey"]) == form_key(DESIGNS[identity]),
             f"{identity}: inventoried primary design was replaced")
        need(form_key(family["denominations"][0]["form"]) == form_key(DESIGNS[identity]),
             f"{identity}: inventoried primary coin is not the recognized copper tier")
        if identity in PREVIOUS_TIERS:
            need([form_key(item["form"]) for item in family["denominations"][1:]] ==
                 [form_key(key) for key in PREVIOUS_TIERS[identity]],
                 f"{identity}: existing silver/gold FormKeys changed")
        need(set(definition["tiers"]) == set(VALUES), f"{identity}: policy tier missing")
        expected_aliases = {(tier, form_key(key)) for tier, key in ALIASES.get(identity, [])}
        actual_aliases = {(item["tier"], form_key(item["form"])) for item in family.get("inputAliases", [])}
        need(actual_aliases == expected_aliases, f"{identity}: source alias lost or invented")
        policy_aliases = {(item["normalizesToTier"], form_key(item["formKey"]))
                          for item in definition.get("sourceAliases", [])}
        need(policy_aliases == expected_aliases, f"{identity}: policy alias differs")
        model_paths = []
        for item in family["denominations"]:
            tier = item["tier"]
            planned = definition["tiers"][tier]
            key = planned.get("formKey") or f"{planned['formId']}:{PLUGIN}"
            need(form_key(key) == form_key(item["form"]), f"{identity}/{tier}: wrong physical form")
            need(type(planned["value"]) is int and planned["value"] == VALUES[tier],
                 f"{identity}/{tier}: wrong policy value")
            need(planned["name"] == f"{tier.title()} {family['displayLabel']}",
                 f"{identity}/{tier}: denomination name is not explicit")
            path = PureWindowsPath(planned["model"])
            need(not path.drive and not path.root and ".." not in path.parts and path.suffix.lower() == ".nif",
                 f"{identity}/{tier}: invalid model path")
            model_paths.append(str(path).casefold())
        need(len(set(model_paths)) == 3, f"{identity}: metal tiers share one model path")


def skypatcher_values(config, texts):
    """Associate values/names with their exact winning form, not file substrings."""
    all_families(config)
    rules = {}
    for text in texts:
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith((";", "#")):
                continue
            fields = {}
            for part in line.split(":"):
                key, separator, value = part.partition("=")
                need(separator and key not in fields, "malformed or duplicate SkyPatcher field")
                fields[key] = value
            need(set(fields) == {"filterByMiscs", "value", "weight", "fullName"},
                 "unexpected denomination override fields")
            plugin, separator, local = fields["filterByMiscs"].partition("|")
            need(separator and local.lower().startswith("0x"), "invalid exact MISC selector")
            key = form_key(local[2:] + ":" + plugin)
            need(key not in rules, "duplicate denomination override form")
            rules[key] = fields
    expected = {}
    for family in config["families"]:
        for item in family["denominations"] + family.get("inputAliases", []):
            tier = item["tier"]
            expected[form_key(item["form"])] = (str(VALUES[tier]), f"~{tier.title()} {family['displayLabel']}~")
    need(set(rules) == set(expected), "missing or unexpected denomination overrides")
    for key, (value, name) in expected.items():
        need(rules[key]["value"] == value and rules[key]["fullName"] == name,
             f"{key}: exact metal/value/name binding mismatch")
