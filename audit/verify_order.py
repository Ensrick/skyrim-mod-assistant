"""Verify every active plugin's masters are present, active, and load earlier.

Run: py -3 audit/verify_order.py        (exit 0 clean, 2 on any violation)

A missing, inactive, or late-loading master is a launch blocker or a guaranteed
CTD. This reads the TES4 header of every starred plugin straight off disk,
resolving each name through the same search order the VFS presents: enabled mod
folders by descending MO2 priority, then the real game Data directory.

Only the five official base masters and entries in Skyrim.ccc are implicitly
active. Merely placing an ESP/ESM/ESL in the physical Data directory does not
activate it.
"""

import io
import os
import struct
import sys


sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)

INSTANCE = r"C:\Users\danjo\source\repos\mo2-instances\skyrim-se"
GAME_DATA = (
    r"C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition\Data"
)
PROFILE = os.path.join(INSTANCE, "profiles", "Default")
SKYRIM_CCC = os.path.join(os.path.dirname(GAME_DATA), "Skyrim.ccc")

PLUGIN_EXTENSIONS = (".esp", ".esm", ".esl")
OFFICIAL_BASE_MASTERS = frozenset(
    {
        "skyrim.esm",
        "update.esm",
        "dawnguard.esm",
        "hearthfires.esm",
        "dragonborn.esm",
    }
)


def masters_of(path):
    """Return MAST entries from a plugin's TES4 header in declaration order."""
    with open(path, "rb") as fh:
        head = fh.read(24)
        if len(head) != 24 or head[:4] != b"TES4":
            raise ValueError("not a plugin")
        record_size = struct.unpack_from("<I", head, 4)[0]
        body = fh.read(record_size)
        if len(body) != record_size:
            raise ValueError("truncated TES4 record")

    out, sp = [], 0
    while sp + 6 <= len(body):
        signature = body[sp : sp + 4]
        size = struct.unpack_from("<H", body, sp + 4)[0]
        end = sp + 6 + size
        if end > len(body):
            raise ValueError("truncated TES4 subrecord")
        if signature == b"MAST":
            raw = body[sp + 6 : end]
            if not raw.endswith(b"\x00"):
                raise ValueError("unterminated MAST name")
            out.append(raw[:-1].decode("cp1252", "replace"))
        sp = end
    return out


def creation_club_masters(path=SKYRIM_CCC):
    """Return normalized plugin names explicitly activated by Skyrim.ccc."""
    if not os.path.isfile(path):
        return set()

    with io.open(path, encoding="utf-8-sig", errors="strict") as stream:
        lines = stream.read().splitlines()

    result = set()
    for line_number, raw in enumerate(lines, start=1):
        name = raw.strip()
        if not name or name.startswith(("#", ";")):
            continue
        if os.path.basename(name) != name or not name.lower().endswith(
            PLUGIN_EXTENSIONS
        ):
            raise ValueError(
                f"invalid Skyrim.ccc entry at line {line_number}: {name!r}"
            )
        result.add(name.lower())
    return result


def implicit_masters(creation_club_path=SKYRIM_CCC):
    """Return plugins activated outside plugins.txt by the game itself."""
    return set(OFFICIAL_BASE_MASTERS) | creation_club_masters(creation_club_path)


def build_index(instance=INSTANCE, profile=PROFILE, game_data=GAME_DATA):
    """Map plugin name to provider path while honoring MO2 asset priority.

    modlist.txt is highest-priority-first, so the first enabled mod that ships a
    plugin wins. The physical game Data directory is the final fallback.
    """
    index = {}
    modlist_path = os.path.join(profile, "modlist.txt")
    lines = io.open(modlist_path, encoding="utf-8").read().splitlines()
    for line in lines:
        if not line.startswith("+"):
            continue
        directory = os.path.join(instance, "mods", line[1:])
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if name.lower().endswith(PLUGIN_EXTENSIONS):
                index.setdefault(name.lower(), os.path.join(directory, name))

    if os.path.isdir(game_data):
        for name in os.listdir(game_data):
            if name.lower().endswith(PLUGIN_EXTENSIONS):
                index.setdefault(name.lower(), os.path.join(game_data, name))
    return index


def evaluate_load_order(starred, index, implicit):
    """Evaluate active plugin names against providers, masters, and load order."""
    positions = {name.lower(): position for position, name in enumerate(starred)}
    findings = {
        "missing_file": [],
        "missing_master": [],
        "inactive_master": [],
        "order_violation": [],
        "unreadable": [],
    }

    for name in starred:
        key = name.lower()
        path = index.get(key)
        if not path:
            findings["missing_file"].append(name)
            continue
        try:
            masters = masters_of(path)
        except Exception as error:  # Report malformed vendor input, then fail closed.
            findings["unreadable"].append((name, str(error)))
            continue

        for master in masters:
            master_key = master.lower()
            master_position = positions.get(master_key)
            if master_key not in index:
                findings["missing_master"].append((name, master))
            elif master_position is None:
                if master_key not in implicit:
                    findings["inactive_master"].append((name, master))
            elif master_position >= positions[key]:
                findings["order_violation"].append((name, master))

    return findings


def _active_plugins(profile=PROFILE):
    path = os.path.join(profile, "plugins.txt")
    return [
        line[1:]
        for line in io.open(path, encoding="utf-8").read().splitlines()
        if line.startswith("*")
    ]


def main():
    index = build_index()
    try:
        implicit = implicit_masters()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"   INVALID CCC     Skyrim.ccc cannot be trusted: {error}")
        print("1 problem(s)")
        return 2

    starred = _active_plugins()
    findings = evaluate_load_order(starred, index, implicit)

    print(f"{len(starred)} active plugins, {len(index)} discoverable")
    for name in findings["missing_file"]:
        print(f"   NO PROVIDER     {name} is active but no enabled mod or Data dir ships it")
    for name, master in findings["missing_master"]:
        print(f"   MISSING MASTER  {name} needs {master}")
    for name, master in findings["inactive_master"]:
        print(f"   INACTIVE MASTER {name} needs {master}, which has a provider but is not active")
    for name, master in findings["order_violation"]:
        print(f"   ORDER           {name} loads before its master {master}")
    for name, error in findings["unreadable"]:
        print(f"   UNREADABLE      {name}: {error}")

    bad = sum(len(items) for items in findings.values())
    print("CLEAN" if not bad else f"{bad} problem(s)")
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
