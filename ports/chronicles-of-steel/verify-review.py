"""Verify an actual generated TCOSS review payload; never launch or deploy it."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    parser.add_argument("--nif-tool", type=Path, required=True)
    args = parser.parse_args()
    recipe_path = Path(__file__).with_name("prepare-review.py")
    spec = importlib.util.spec_from_file_location("tcoss_review_recipe", recipe_path)
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    expected = {}
    actual = {}
    for folder, target in (("review-yaml", expected), ("roundtrip-yaml", actual)):
        for path in (args.review / folder).glob("*/*.yaml"):
            data = yaml.load(path.read_text(encoding="utf-8-sig"), Loader=recipe.SpriggitLoader)
            target[data["FormKey"]] = data
    assert expected.keys() == actual.keys(), "Roundtrip lost or introduced records"
    byte_fields_checked = 0

    def check_bytes(before, after):
        nonlocal byte_fields_checked
        if isinstance(before, str) and before.startswith("0x"):
            assert before.lower() == str(after).lower(), "Opaque byte-array field changed"
            byte_fields_checked += 1
        elif isinstance(before, dict):
            for key, value in before.items():
                check_bytes(value, after.get(key) if isinstance(after, dict) else None)
        elif isinstance(before, list):
            for index, value in enumerate(before):
                check_bytes(value, after[index] if isinstance(after, list) and index < len(after) else None)

    for key, data in expected.items():
        assert actual[key].get("FormVersion", 44) == 44
        assert key.endswith(":" + recipe.OUTPUT_NAME)
        assert 0x800 <= int(key.split(":")[0], 16) <= 0xFFF
        check_bytes(data, actual[key])
    axe = next(data for data in actual.values() if data.get("EditorID") == "RSNordAxeWar2HWorn")
    assert abs(axe["Data"]["Stagger"] - 1.15) < 0.00001
    assert axe["Critical"]["Damage"] == 10
    assert axe["Critical"]["PercentMult"] == 1
    mod = args.review / "mod"
    plugin = mod / recipe.OUTPUT_NAME
    binary = plugin.read_bytes()
    header = binary[:24]
    assert struct.unpack_from("<I", header, 8)[0] & 0x200, "Plugin lacks light flag"
    binary_records = []

    def walk(start, end):
        pos = start
        while pos < end:
            assert pos + 24 <= end
            typ = binary[pos:pos + 4]
            size = struct.unpack_from("<I", binary, pos + 4)[0]
            if typ == b"GRUP":
                assert size >= 24 and pos + size <= end
                walk(pos + 24, pos + size)
                pos += size
                continue
            assert pos + 24 + size <= end
            assert struct.unpack_from("<H", binary, pos + 20)[0] == 44
            form = struct.unpack_from("<I", binary, pos + 12)[0]
            assert form >> 24 == 1 and 0x800 <= (form & 0xFFFFFF) <= 0xFFF
            assert typ in {b"WEAP", b"ARMO", b"ARMA", b"AMMO", b"PROJ", b"STAT", b"KYWD", b"COBJ"}
            binary_records.append(form)
            pos += 24 + size

    walk(24 + struct.unpack_from("<I", header, 4)[0], len(binary))
    assert len(binary_records) == len(actual) == len(set(binary_records))
    assert {f"{form & 0xFFFFFF:06X}:{recipe.OUTPUT_NAME}" for form in binary_records} == actual.keys()
    output = subprocess.run([str(args.nif_tool), "inspect", str(mod / "meshes")],
                            capture_output=True, text=True, encoding="utf-8", check=True)
    meshes = [json.loads(line) for line in output.stdout.splitlines() if line.strip()]
    local_assets = {p.relative_to(mod).as_posix().lower(): p for p in mod.rglob("*") if p.is_file()}
    report = json.loads((args.review / "review-report.json").read_text(encoding="utf-8"))
    external = set(report["externalTexturesResolvedInSkyrimArchives"])
    for mesh in meshes:
        assert mesh["valid"] and not mesh["unknownBlocks"]
        assert mesh["isSSE"] and mesh["streamVersion"] == 100 and mesh["sseGeometryCompatible"]
        for texture in mesh["textures"]:
            key = recipe.asset_key(texture, "textures")
            assert key in local_assets or key in external, f"Unresolved final texture: {key}"
    textures_without_mips = []
    texture_formats = {}
    for relative, path in local_assets.items():
        if path.suffix.lower() not in (".nif", ".dds"):
            assert path.name == recipe.OUTPUT_NAME
            continue
        assert relative.split("/", 1)[1].startswith(recipe.ASSET_NAMESPACE), relative
        if path.suffix.lower() != ".dds":
            continue
        with path.open("rb") as stream:
            dds = stream.read(128)
        assert dds[:4] == b"DDS " and struct.unpack_from("<I", dds, 4)[0] == 124
        height, width = struct.unpack_from("<II", dds, 12)
        assert 0 < max(height, width) <= 4096
        assert width & (width - 1) == 0 and height & (height - 1) == 0
        mips = struct.unpack_from("<I", dds, 28)[0]
        if mips <= 1 and max(width, height) > 1:
            textures_without_mips.append(relative)
        fourcc = dds[84:88].decode("ascii").rstrip("\x00") or "uncompressed"
        texture_formats[fourcc] = texture_formats.get(fourcc, 0) + 1
    result = {"structuralChecks": "PASS", "records": len(actual), "meshes": len(meshes),
              "opaqueByteFieldsRoundtripped": byte_fields_checked, "lightFlag": True,
              "sourceTextureFormats": texture_formats, "texturesWithoutMipChain": textures_without_mips,
              "runtimeTested": False, "visualTested": False,
              "readyForInstallation": False, "status": "REVIEW ONLY"}
    (args.review / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
