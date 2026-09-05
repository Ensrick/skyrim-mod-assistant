"""Prepare a private, undistributed TCOSS equipment conversion for inspection.

This is a dependency-closure extraction across hundreds of records, not a
general-purpose plugin converter. No cells, quests, actors or leveled lists are
allowed. Source files and all generated vendor-derived bytes stay local.
"""
import argparse
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import yaml

SOURCES = {
    "TCOSS.esm": "F3F2D205BBEB6A884497DCA7ACB4DAA5AC243D7AFF1FF7330E6A6F740002EDF0",
    "TCOSS - ChroniclesOfSteel.esp": "D41E6108C37403A7A16BB27E0D3018D9DFB040F5FD3B26DC6AA13520BB3678A9",
    "TCOSS - Weapons Of War.esp": "F2554912BCD78F190D7BA0591421ABE33D5C803320EE412E3647977867D1A59F",
}
BSA_SHA256 = "73BA09B6A2EBEC21EC0449DDD85BBA6C67621AA2FF149407B7DA3FC0AA6B9F99"
ROOT_TYPES = {"Weapons", "Armors", "Ammunitions"}
ALLOWED = ROOT_TYPES | {"ArmorAddons", "Statics", "Keywords", "Projectiles",
                        "ConstructibleObjects"}
FORM = re.compile(r"^[0-9A-Fa-f]{6}:.+\.(?:esm|esp|esl)$", re.I)
OUTPUT_NAME = "Ensrick TCOSS Equipment Review.esp"
ASSET_NAMESPACE = "ensrick/tcossreview/"
ACTOR_SKINS = {"SkinDogCollar", "SkinDraugrBeard03", "5rSkinFrostGiant",
               "5rSkinSkeletonDeadLord", "5rSkinFoxArcticBaby"}


class SpriggitLoader(yaml.SafeLoader):
    pass


def spriggit_int(loader, node):
    # Spriggit uses 0x-prefixed scalars for byte arrays. Preserve their leading
    # zeroes and byte order instead of allowing PyYAML to turn them into ints.
    if node.value.lower().startswith("0x"):
        return node.value
    return yaml.SafeLoader.construct_yaml_int(loader, node)


SpriggitLoader.add_constructor("tag:yaml.org,2002:int", spriggit_int)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def run(*args):
    process = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                             encoding="utf-8", errors="strict",
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode:
        raise RuntimeError(f"{args[0]} failed ({process.returncode}):\n"
                           f"{process.stdout[-3000:]}\n{process.stderr[-3000:]}")
    return process.stdout


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def map_values(value, remapping):
    if isinstance(value, str):
        return remapping.get(value.lower(), value)
    if isinstance(value, dict):
        return {key: map_values(child, remapping) for key, child in value.items()}
    if isinstance(value, list):
        return [map_values(child, remapping) for child in value]
    return value


def asset_key(value, prefix):
    value = value.replace("\\", "/").strip().lower()
    if not value.startswith(prefix + "/"):
        value = prefix + "/" + value
    parts = Path(value).parts
    if ".." in parts or ":" in value or value.startswith("/"):
        raise ValueError(f"Unsafe asset reference: {value}")
    return value


def private_asset_path(value):
    prefix, relative = value.split("/", 1)
    return prefix + "/" + ASSET_NAMESPACE + relative


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spriggit", type=Path, required=True)
    parser.add_argument("--nif-tool", type=Path, required=True)
    parser.add_argument("--record-tool", type=Path, required=True)
    parser.add_argument("--skyrim-master", type=Path, required=True)
    parser.add_argument("--bsarch", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    for source in (args.source.resolve(),):
        if args.output == source or args.output in source.parents or source in args.output.parents:
            raise ValueError("Output and source trees must be separate")
    if args.output.exists():
        raise ValueError("Output must not exist; choose a new isolated work directory")
    for name, expected in SOURCES.items():
        if digest(args.source / name) != expected:
            raise ValueError(f"Unexpected source version: {name}")
    if digest(args.source / "TCOSS.bsa") != BSA_SHA256:
        raise ValueError("Unexpected asset archive version")
    args.output.mkdir(parents=True)
    args.assets = args.output / "source-assets"
    args.assets.mkdir()
    run(args.bsarch, "unpack", args.source / "TCOSS.bsa", args.assets, "-quiet")
    assets = {p.relative_to(args.assets).as_posix().lower(): p
              for p in args.assets.rglob("*") if p.is_file()}
    game_assets = set()
    for archive in sorted(args.skyrim_master.parent.glob("Skyrim - *.bsa")):
        if "Meshes" not in archive.name and "Textures" not in archive.name:
            continue
        for line in run(args.bsarch, archive, "-list").splitlines():
            name = line.strip().replace("\\", "/").lower()
            if name.startswith(("meshes/", "textures/")):
                game_assets.add(name)
    records = {}
    for index, name in enumerate(SOURCES):
        folder = args.output / "source-yaml" / str(index)
        run(args.spriggit, "serialize", "-i", args.source / name, "-o", folder,
            "-g", "SkyrimSE", "-p", "Spriggit.Yaml.Skyrim", "-v", "0.41.0", "-u")
        for path in sorted(folder.glob("*/*.yaml")):
            data = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=SpriggitLoader)
            if isinstance(data, dict) and "FormKey" in data:
                records[data["FormKey"].lower()] = (path.parent.name, data, name)
    excluded_skins = {key for key, (_, data, _) in records.items()
                      if data.get("EditorID") in ACTOR_SKINS}
    roots = {key for key, (kind, _, _) in records.items()
             if kind in ROOT_TYPES and key.split(":", 1)[1] in
             {name.lower() for name in SOURCES} and key not in excluded_skins}
    selected = set(roots)
    # Keep source crafting/tempering as review data. Their final availability is
    # an explicit integration decision; this plugin is never auto-installed.
    for key, (kind, data, _) in records.items():
        if kind == "ConstructibleObjects" and str(data.get("CreatedObject", "")).lower() in roots:
            selected.add(key)
    pending = list(selected)
    while pending:
        key = pending.pop()
        kind, data, _ = records[key]
        if kind not in ALLOWED:
            raise ValueError(f"Equipment depends on non-equipment record: {key} ({kind})")
        if data.get("VirtualMachineAdapter"):
            raise ValueError(f"Equipment has script dependencies: {key}")
        for value in strings(data):
            if not FORM.fullmatch(value) or value.lower().endswith(":skyrim.esm"):
                continue
            child = value.lower()
            if child not in records:
                raise ValueError(f"Unresolved custom form: {key} -> {value}")
            if child not in selected:
                selected.add(child)
                pending.append(child)
    if len(selected) > 2048:
        raise ValueError("Selected record closure exceeds conventional light-plugin range")
    remapping = {key: f"{index + 0x800:06X}:{OUTPUT_NAME}"
                 for index, key in enumerate(sorted(selected))}
    plugin_yaml = args.output / "review-yaml"
    plugin_yaml.mkdir()
    (plugin_yaml / "spriggit-meta.json").write_text(json.dumps({
        "PackageName": "Spriggit.Yaml.Skyrim", "Version": "0.41.0",
        "Release": "SkyrimSE", "ModKey": OUTPUT_NAME}, indent=2), encoding="utf-8")
    header = {
        "SpriggitSource": {"PackageName": "Spriggit.Yaml.Skyrim", "Version": "0.41.0"},
        "ModKey": OUTPUT_NAME, "GameRelease": "SkyrimSE",
        "ModHeader": {"Flags": ["Small"], "FormVersion": 44,
                      "Stats": {"Version": 1.7}, "Author": "Ensrick",
                      "Description": "PRIVATE REVIEW ONLY. TCOSS equipment derived locally from Shingouki and Waalx. Balance, distribution and visual verification pending.",
                      "MasterReferences": [{"Master": "Skyrim.esm", "FileSize": 0}]}}
    (plugin_yaml / "RecordData.yaml").write_text(yaml.safe_dump(header, sort_keys=False), encoding="utf-8")
    model_paths = set()
    inventory = []
    for key in sorted(selected):
        kind, source_data, winner = records[key]
        data = map_values(copy.deepcopy(source_data), remapping)
        data["FormVersion"] = 44
        # Candidate repair: both its original release and current sibling axes
        # have stagger/critical damage. Keep other statistics for balance review.
        if source_data.get("EditorID") == "RSNordAxeWar2HWorn":
            if data["Data"].get("Stagger", 0) != 0 or data["Critical"].get("Damage", 0) != 0:
                raise ValueError("Worn battleaxe no longer matches the audited defect")
            data["Data"]["Stagger"] = 1.15
            data["Critical"]["Damage"] = 10
            data["Critical"]["PercentMult"] = 1
        if data.get("IsDeleted") or "Deleted" in str(data.get("MajorFlags", "")):
            raise ValueError(f"Deleted equipment record: {key}")
        directory = plugin_yaml / kind
        directory.mkdir(exist_ok=True)
        model_remapping = {}
        for value in strings(data):
            if value.lower().endswith(".nif"):
                path = asset_key(value, "meshes")
                model_paths.add(path)
                if path in assets:
                    # Isolate all vendor meshes, including its vanilla-path
                    # replacements, so our preview cannot replace vanilla art.
                    model_remapping[value.lower()] = private_asset_path(path)[7:].replace("/", "\\")
        data = map_values(data, model_remapping)
        (directory / (remapping[key].split(":")[0] + ".yaml")).write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        if key in roots:
            inventory.append({"sourceFormKey": source_data["FormKey"],
                              "reviewFormKey": remapping[key], "winningPlugin": winner,
                              "type": kind, "record": data,
                              "role": "UNDECIDED", "balance": "UNREVIEWED",
                              "distribution": "NONE"})
    external_models = sorted(path for path in model_paths if path not in assets)
    missing_models = sorted(path for path in external_models if path not in game_assets)
    if missing_models:
        (args.output / "missing-models.json").write_text(json.dumps(missing_models, indent=2), encoding="utf-8")
        raise ValueError(f"{len(missing_models)} referenced models absent from source archive; see missing-models.json")
    selected_meshes = {path for path in model_paths if path in assets}
    for key in selected:
        kind, data, _ = records[key]
        if kind != "ArmorAddons":
            continue
        for sex in ("Male", "Female"):
            if not data.get("WeightSliderEnabled", {}).get(sex, False):
                continue
            model = data.get("WorldModel", {}).get(sex, {}).get("File")
            if not model:
                continue
            path = asset_key(model, "meshes")
            if not re.search(r"_[01]\.nif$", path):
                raise ValueError(f"Slider-enabled model has no weight suffix: {key} {sex}")
            for suffix in ("0.nif", "1.nif"):
                endpoint = path[:-5] + suffix
                if endpoint not in assets and endpoint not in game_assets:
                    raise ValueError(f"Missing weight endpoint: {key} {sex} {endpoint}")
    # Skyrim resolves the other weight slider endpoint implicitly.
    for path in list(selected_meshes):
        match = re.search(r"_([01])\.nif$", path)
        if match:
            sibling = path[:-5] + str(1 - int(match[1])) + ".nif"
            if sibling in assets:
                selected_meshes.add(sibling)
    input_meshes = args.output / "conversion-input" / "meshes"
    for path in sorted(selected_meshes):
        target = args.output / "conversion-input" / private_asset_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets[path], target)
    mod = args.output / "mod"
    mod.mkdir()
    converted = args.output / "converted" / "meshes"
    mesh_text = run(args.nif_tool, "convert-sse", input_meshes, converted)
    meshes = [json.loads(line) for line in mesh_text.splitlines() if line.strip()]
    if len(meshes) != len(selected_meshes) or any(not m["valid"] or m["unknownBlocks"]
            or not m["isSSE"] or m["streamVersion"] != 100 for m in meshes):
        raise ValueError("Mesh conversion validation failed")
    texture_paths = {asset_key(t, "textures") for mesh in meshes for t in mesh["textures"]}
    external_textures = []
    for path in sorted(texture_paths):
        if path not in assets:
            external_textures.append(path)
            continue
        target = mod / private_asset_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets[path], target)
    missing_textures = sorted(set(external_textures) - game_assets)
    if missing_textures:
        raise ValueError(f"Unresolved textures: {missing_textures}")
    for mesh in meshes:
        path = Path(mesh["path"])
        target = mod / "meshes" / path.relative_to(converted)
        target.parent.mkdir(parents=True, exist_ok=True)
        replacements = []
        seen_textures = set()
        for texture in mesh["textures"]:
            key = asset_key(texture, "textures")
            if key in assets and key not in seen_textures:
                seen_textures.add(key)
                replacements.extend([texture, private_asset_path(key).replace("/", "\\")])
        if replacements:
            run(args.nif_tool, "remap-textures", path, target, *replacements)
        else:
            shutil.copyfile(path, target)
    plugin = mod / OUTPUT_NAME
    run(args.spriggit, "deserialize", "-i", plugin_yaml, "-o", plugin)
    info = json.loads(run(args.record_tool, "plugin-info", plugin))
    audit = json.loads(run(args.record_tool, "audit-links", args.skyrim_master, plugin))
    if info["masters"] != ["Skyrim.esm"] or audit["unresolved"]:
        raise ValueError(f"Plugin dependency validation failed: {audit}")
    if info["records"] != len(selected):
        raise ValueError("Plugin record count changed during build")
    roundtrip = args.output / "roundtrip-yaml"
    run(args.spriggit, "serialize", "-i", plugin, "-o", roundtrip,
        "-g", "SkyrimSE", "-p", "Spriggit.Yaml.Skyrim", "-v", "0.41.0", "-u")
    payloads = {}
    for path in sorted(mod.rglob("*")):
        if path.is_file():
            payloads[path.relative_to(mod).as_posix()] = digest(path)
    report = {
        "status": "PRIVATE_REVIEW_NOT_INSTALLED", "scope": "equipment-only review",
        "sources": SOURCES, "assetArchiveSha256": BSA_SHA256,
        "recordTypes": dict(collections.Counter(records[k][0] for k in selected)),
        "items": len(roots), "records": len(selected), "pluginInfo": info,
        "actorSkinsExcludedFromEquipmentReview": [records[k][1]["EditorID"] for k in sorted(excluded_skins)],
        "candidateRepairs": [{"editorId": "RSNordAxeWar2HWorn", "Stagger": 1.15,
                              "CriticalDamage": 10, "CriticalPercentMult": 1}],
        "linkAudit": audit, "meshes": len(meshes),
        "texturesCopied": len(texture_paths) - len(external_textures),
        "externalTexturesResolvedInSkyrimArchives": external_textures,
        "externalModelsResolvedInSkyrimArchives": external_models,
        "pending": ["source defects", "balance", "distribution", "visual and in-game checks",
                    "permissions for publication"],
        "payloadSha256": payloads}
    (args.output / "review-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.output / "item-inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "payloadSha256"}, indent=2))


if __name__ == "__main__":
    main()
