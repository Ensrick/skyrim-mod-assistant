"""Convert the user's exact TCOSS Finale download to a PRIVATE review mod.

No downloads, credentials, automatic installation, GUI, or game launch. This
front end orchestrates the audited recipe; it is not a general-purpose CAO clone.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import zipfile

ARCHIVE_SHA256 = "CED4BA4A8FB6705C62706FF2F80FA988E1520917470D3A31171A78ED25568CF5"
REQUIRED_FILES = {"TCOSS.esm", "TCOSS - ChroniclesOfSteel.esp",
                  "TCOSS - Weapons Of War.esp", "TCOSS.bsa"}
TOOL_FLAGS = {"spriggit": "--spriggit", "nifPortCli": "--nif-tool",
              "skyrimRecordCli": "--record-tool", "bsarch": "--bsarch"}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def source_members(archive):
    """Inspect the entire directory, then select only four inert source files."""
    selected = {}
    names = set()
    for item in archive.infolist():
        name = item.filename.replace("\\", "/")
        parts = PurePosixPath(name).parts
        if (not parts or name.startswith("/") or ".." in parts or ":" in name
                or stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError("Unsafe path or symlink in archive")
        normalized = name.casefold().rstrip("/")
        if normalized in names:
            raise ValueError("Duplicate archive path")
        names.add(normalized)
        if item.is_dir():
            continue
        if item.flag_bits & 1:
            raise ValueError("Encrypted archives are not supported")
        leaf = parts[-1]
        if leaf not in REQUIRED_FILES:
            continue
        if leaf in selected or not 0 < item.file_size <= 2 * 1024**3:
            raise ValueError("Duplicate or oversized source file")
        selected[leaf] = item
    if set(selected) != REQUIRED_FILES:
        raise ValueError("Archive does not contain the four required Finale files")
    return selected


def existing_ancestor(path):
    while not path.exists():
        parent = path.parent
        if parent == path:
            raise ValueError("Output drive or network share is unavailable")
        path = parent
    return path


def preflight(args):
    archive = args.archive.resolve(strict=True)
    game = args.game_data.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Output already exists; choose a new isolated directory")
    if output == game or game in output.parents or output in game.parents:
        raise ValueError("Output must not overlap the game directory")
    if output in archive.parents:
        raise ValueError("Output must not contain the source archive")
    master = game / "Skyrim.esm"
    if not master.is_file() or not list(game.glob("Skyrim - Meshes*.bsa")) or not list(game.glob("Skyrim - Textures*.bsa")):
        raise ValueError("Skyrim SE master and base mesh/texture archives are required")
    if sha256(archive) != ARCHIVE_SHA256:
        raise ValueError("Wrong source version. Obtain Nexus Skyrim 103289, Finale, file 1000320407")
    with zipfile.ZipFile(archive) as packed:
        source_members(packed)
    config_path = args.toolchain.resolve(strict=True)
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))["tools"]
    selected_tools = {}
    for name in TOOL_FLAGS:
        item = config.get(name, {})
        supplied = args.bsarch if name == "bsarch" and args.bsarch else item.get("path")
        if not supplied:
            raise ValueError(f"Tool path missing: {name}")
        path = Path(supplied)
        if not path.is_absolute():
            path = config_path.parent / path
        path = path.resolve(strict=True)
        if not path.is_file():
            raise ValueError(f"Tool is not a file: {name}")
        actual = sha256(path)
        expected = item.get("sha256")
        if expected and actual != expected.upper():
            raise ValueError(f"Pinned tool hash mismatch: {name}")
        selected_tools[name] = {"path": str(path), "sha256": actual}
    ancestor = existing_ancestor(output.parent)
    if shutil.disk_usage(ancestor).free < 8 * 1024**3:
        raise ValueError("At least 8 GiB free scratch space is required")
    return archive, master, output, selected_tools


def execute(command, log):
    # CREATE_NO_WINDOW also covers console-subsystem helpers launched by Python
    # on Windows. Stdout/stderr remain available in the caller's private log.
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                creationflags=flags, check=False)
    if result.returncode:
        raise RuntimeError(f"Conversion step failed ({result.returncode}); inspect {log}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--toolchain", type=Path, required=True,
                        help="Local JSON containing tools.NAME.path and optional sha256")
    parser.add_argument("--game-data", type=Path, required=True)
    parser.add_argument("--bsarch", type=Path, help="Override missing toolchain bsarch path")
    parser.add_argument("--check-only", action="store_true",
                        help="Validate all inputs without creating files or running tools")
    args = parser.parse_args()
    archive, master, output, selected_tools = preflight(args)
    receipt = {"sourceArchiveSha256": ARCHIVE_SHA256, "tools": selected_tools,
               "skyrimMasterSha256": sha256(master), "scope": "equipment review only",
               "installed": False, "publicRedistributionAuthorized": False}
    if args.check_only:
        print(json.dumps({"preflight": "PASS", "outputCreated": False, **receipt}, indent=2))
        return
    output.mkdir(parents=True, exist_ok=False)
    source = output / "source"
    source.mkdir()
    with zipfile.ZipFile(archive) as packed:
        for name, member in source_members(packed).items():
            with packed.open(member) as incoming, (source / name).open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
    scripts = Path(__file__).resolve().parent
    review = output / "review"
    command = [sys.executable, str(scripts / "prepare-review.py"),
               "--source", str(source), "--output", str(review), "--skyrim-master", str(master)]
    for name, flag in TOOL_FLAGS.items():
        command.extend([flag, selected_tools[name]["path"]])
    print("Building private equipment review; progress is captured in prepare.log.", flush=True)
    execute(command, output / "prepare.log")
    execute([sys.executable, str(scripts / "verify-review.py"), str(review),
             "--nif-tool", selected_tools["nifPortCli"]["path"]], output / "verify.log")
    verification = json.loads((review / "verification.json").read_text(encoding="utf-8"))
    receipt.update({"status": "REVIEW_ONLY_NOT_INSTALLED", "verification": verification})
    (output / "conversion-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "payload": str(review / "mod"),
                      "textureMipRepairsPending": verification["texturesWithoutMipChain"],
                      "remaining": ["balance", "distribution", "visual/runtime validation", "release permissions"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as error:
        print(f"Conversion stopped: {error}", file=sys.stderr)
        sys.exit(1)
