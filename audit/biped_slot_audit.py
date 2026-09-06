"""Strict read-only ARMO/ARMA biped occupancy scan of the current MO2 profile.

Scans every declaration, including losing overrides, conservatively. Only a
zero-hit slot can be reserved. Retains meshes for a separate NIF partition
audit; record occupancy alone is NOT an all-layer compatibility guarantee.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


def zstring(payload: bytes, description: str) -> str:
    if not payload or payload[-1:] != b"\0" or b"\0" in payload[:-1]:
        raise ValueError(f"Malformed {description} string")
    return payload[:-1].decode("cp1252")


def subrecords(data: bytes):
    pos, extended = 0, None
    while pos < len(data):
        if pos + 6 > len(data):
            raise ValueError("Truncated subrecord header")
        tag, size = struct.unpack_from("<4sH", data, pos)
        pos += 6
        if tag == b"XXXX":
            if size != 4 or extended is not None or pos + 4 > len(data):
                raise ValueError("Malformed extended subrecord")
            extended = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            continue
        if extended is not None:
            size, extended = extended, None
        if pos + size > len(data):
            raise ValueError("Subrecord exceeds its record")
        yield tag, data[pos:pos + size]
        pos += size
    if extended is not None:
        raise ValueError("Dangling extended subrecord")


def scan_plugin(path: Path) -> tuple[str, list[dict]]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest().upper()
    if len(data) < 24 or data[:4] != b"TES4":
        raise ValueError(f"Invalid plugin: {path}")
    header_size = struct.unpack_from("<I", data, 4)[0]
    if 24 + header_size > len(data):
        raise ValueError(f"TES4 body exceeds plugin file: {path.name}")
    header = list(subrecords(data[24:24 + header_size]))
    hedr = [payload for tag, payload in header if tag == b"HEDR"]
    if len(hedr) != 1 or len(hedr[0]) != 12:
        raise ValueError(f"TES4 must contain one valid HEDR: {path.name}")
    masters = []
    for tag, payload in header:
        if tag == b"MAST":
            master = zstring(payload, f"MAST in {path.name}")
            if not master or any(char in master for char in ("/", "\\", ":")):
                raise ValueError(f"Malformed MAST name: {path.name}")
            if master.casefold() in {name.casefold() for name in masters + [path.name]}:
                raise ValueError(f"Duplicate or self-referencing master: {path.name}: {master}")
            masters.append(master)
    modules = masters + [path.name]
    rows = []

    def key(raw: int) -> str:
        index = raw >> 24
        if index >= len(modules):
            raise ValueError(f"Invalid local master index in {path.name}: {raw:08X}")
        return f"{raw & 0xFFFFFF:06X}:{modules[index]}"

    def walk(start: int, end: int):
        pos = start
        while pos < end:
            if pos + 24 > end:
                raise ValueError(f"Truncated record header in {path.name}")
            tag, size, flags, raw_form = struct.unpack_from("<4sIII", data, pos)
            if tag == b"GRUP":
                if size < 24 or pos + size > end:
                    raise ValueError(f"Invalid group boundary in {path.name}")
                walk(pos + 24, pos + size)
                pos += size
                continue
            if pos + 24 + size > end:
                raise ValueError(f"Record exceeds group in {path.name}")
            if tag in (b"ARMO", b"ARMA"):
                body = data[pos + 24:pos + 24 + size]
                if flags & 0x40000:
                    if len(body) < 4:
                        raise ValueError("Compressed record has no length")
                    length = struct.unpack_from("<I", body)[0]
                    decoder = zlib.decompressobj()
                    body = decoder.decompress(body[4:], length + 1)
                    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                        raise ValueError("Malformed or trailing compressed record stream")
                    if len(body) != length:
                        raise ValueError("Decompressed length mismatch")
                row = {"formKey": key(raw_form), "type": tag.decode("ascii"),
                       "editorId": None, "mask": 0, "models": [], "armatures": []}
                saw_biped = False
                for sub, payload in subrecords(body):
                    if sub == b"EDID":
                        row["editorId"] = zstring(payload, "EDID")
                    elif sub in (b"BOD2", b"BODT"):
                        if len(payload) < 4:
                            raise ValueError("Truncated biped mask")
                        if saw_biped:
                            raise ValueError("Duplicate biped mask could conceal an occupied slot")
                        saw_biped = True
                        row["mask"] = struct.unpack_from("<I", payload)[0]
                    elif sub in (b"MODL", b"MOD2", b"MOD3", b"MOD4", b"MOD5"):
                        if sub == b"MODL":
                            if len(payload) != 4:
                                raise ValueError("Malformed ARMO armature or ARMA additional-race FormID")
                            linked = key(struct.unpack_from("<I", payload)[0])
                            # MODL is an armature in ARMO, but an additional
                            # race in ARMA; neither is a NIF filename.
                            if tag == b"ARMO":
                                row["armatures"].append(linked)
                        else:
                            model = zstring(payload, f"model path in {path.name}:{raw_form:08X}")
                            if model.lower().endswith(".nif"):
                                row["models"].append(model.replace("\\", "/").lower())
                rows.append(row)
            pos += 24 + size
    walk(24 + header_size, len(data))
    return digest, rows


def runtime_plugins(instance: Path, game_data: Path) -> list[Path]:
    profile = instance / "profiles/Default"
    enabled = [line[1:] for line in (profile / "modlist.txt").read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("+")]
    roots = [instance / "overwrite"] + [instance / "mods" / name for name in enabled] + [game_data]
    winners = {}
    for root in roots:
        if root.is_dir():
            for path in root.iterdir():
                if path.is_file() and path.suffix.lower() in {".esp", ".esm", ".esl"}:
                    winners.setdefault(path.name.lower(), path.resolve())
    official = ["Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm"]
    if (game_data / "_ResourcePack.esl").is_file():
        official.append("_ResourcePack.esl")
    ccc = game_data.parent / "Skyrim.ccc"
    if ccc.is_file():
        official += [line.strip() for line in ccc.read_text(encoding="utf-8-sig").splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
    managed = [line[1:].strip() for line in (profile / "plugins.txt").read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("*")]
    ordered = dict.fromkeys(name.lower() for name in official + managed)
    missing = set(ordered) - set(winners)
    if missing:
        raise ValueError(f"Unresolved runtime plugins: {sorted(missing)}")
    return [winners[name] for name in ordered]


def scan_profile(instance: Path, game_data: Path, slot: int) -> dict:
    if not 30 <= slot <= 61:
        raise ValueError("Biped slot must be between 30 and 61")
    paths = runtime_plugins(instance, game_data)
    inputs, collisions, models, declarations = [], [], set(), []
    armor_count = addon_count = 0
    for path in paths:
        digest, rows = scan_plugin(path)
        inputs.append({"name": path.name, "path": str(path), "sha256": digest})
        for row in rows:
            declaration = {"provider": path.name, **row}
            declarations.append(declaration)
            armor_count += row["type"] == "ARMO"
            addon_count += row["type"] == "ARMA"
            if row["mask"] & (1 << (slot - 30)):
                collisions.append(declaration)
            if row["type"] == "ARMA":
                models.update(row["models"])
    return {"slot": slot, "plugins": len(paths), "armorDeclarations": armor_count,
            "armorAddonDeclarations": addon_count, "collisions": collisions,
            "inputs": inputs, "armorAddonModelPaths": sorted(models),
            "declarations": declarations}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--game-data", type=Path, required=True)
    parser.add_argument("--slot", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output, instance = args.output.resolve(), args.instance.resolve()
    if output == instance or instance in output.parents or output.exists():
        raise ValueError("Output must be a new file outside the MO2 instance")
    result = scan_profile(instance, args.game_data, args.slot)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("slot", "plugins", "armorDeclarations", "armorAddonDeclarations", "collisions")}, indent=2))
