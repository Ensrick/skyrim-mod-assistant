"""Portable, fail-closed driver for the attested denomination asset recipe.

The shipped ``recipe.py`` and ``inputs.json`` are the historical build inputs
bound by ``integration-receipt.json``.  This driver supplies machine-local
paths, acquires the already-pinned vendor bytes into a private cache, and then
runs that unchanged recipe.  It never downloads, repins, or overwrites input
or output files.
"""

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import tempfile

import recipe


HERE = Path(__file__).resolve().parent
PIN_PATH = HERE / "inputs.json"
RECEIPT_PATH = HERE / "integration-receipt.json"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def require_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"{label} is not a file: {resolved}")
    return resolved


def safe_relative(value: str, label: str) -> Path:
    normalized = value.replace("\\", "/")
    relative = Path(normalized)
    if not normalized or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe {label}: {value!r}")
    return relative


def within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def enabled_roots(instance: Path, profile: str) -> list[Path]:
    profile_name = safe_relative(profile, "profile")
    if len(profile_name.parts) != 1:
        raise ValueError(f"profile must be one directory name: {profile!r}")
    profile_root = instance / "profiles" / profile_name
    rows = (profile_root / "modlist.txt").read_text(encoding="utf-8-sig").splitlines()
    mods_root = (instance / "mods").resolve()
    roots = [(instance / "overwrite").resolve()]
    for row in rows:
        if not row.startswith("+"):
            continue
        candidate = (mods_root / row[1:]).resolve()
        if not within(candidate, mods_root) or candidate == mods_root:
            raise ValueError(f"unsafe enabled mod path in modlist.txt: {row[1:]!r}")
        roots.append(candidate)
    return roots


class Environment:
    def __init__(self, args: argparse.Namespace):
        self.instance = args.instance_root.expanduser().resolve()
        self.repo = args.repo_root.expanduser().resolve()
        self.policy = require_file(args.policy, "policy")
        self.workspace = args.workspace.expanduser().resolve()
        if not self.instance.is_dir():
            raise ValueError(f"instance root is not a directory: {self.instance}")
        if self.workspace == self.instance or within(self.workspace, self.instance):
            raise ValueError("workspace must not be inside the MO2 instance")
        if (self.workspace == self.repo or within(self.instance, self.workspace)
                or within(self.repo, self.workspace)):
            raise ValueError("workspace must be a dedicated directory, not a repository/instance ancestor")
        self.roots = enabled_roots(self.instance, args.profile)
        self.tools = {
            "nif": require_file(args.nif_tool, "nif tool"),
            "magick": require_file(args.magick, "ImageMagick"),
            "texconv": require_file(args.texconv, "texconv"),
        }
        self.pins_raw = PIN_PATH.read_bytes()
        self.pins = json.loads(self.pins_raw)
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        if self.pins.get("schemaVersion") != 1 or self.receipt.get("schemaVersion") != 1:
            raise ValueError("unsupported asset pin or receipt schema")
        for name, path in self.tools.items():
            expected = self.pins["tools"][name]["sha256"]
            if sha256(path.read_bytes()) != expected:
                raise ValueError(f"tool hash drift: {name}")
        reader_path = require_file(self.repo / "audit/modasset.py", "BSA reader source")
        if sha256(reader_path.read_bytes()) != self.pins["bsaReaderSha256"]:
            raise ValueError("BSA reader source hash drift")

        recipe.INSTANCE = self.instance
        recipe.REPO = self.repo
        recipe.POLICY = self.policy
        recipe.TOOLS = self.tools
        recipe.roots = lambda: list(self.roots)
        self.reader_type = recipe.bsa_reader()
        self._archive_hashes: dict[Path, str] = {}
        self._archives: dict[Path, object] = {}

    def archive(self, pin: dict) -> object:
        archive_name = PureWindowsPath(pin["path"]).name
        candidates = [root / archive_name for root in self.roots if (root / archive_name).is_file()]
        if not candidates:
            raise ValueError(f"pinned archive is not visible in enabled mods: {archive_name}")
        winner = candidates[0]
        if winner not in self._archive_hashes:
            self._archive_hashes[winner] = sha256(winner.read_bytes())
        digest = self._archive_hashes[winner]
        if digest != pin.get("archiveSha256"):
            raise ValueError(f"winning archive hash drift: {archive_name}")
        if winner not in self._archives:
            self._archives[winner] = self.reader_type(winner)
        return self._archives[winner]

    def resolve(self, logical_path: str, pin: dict, label: str) -> bytes:
        relative = safe_relative(logical_path, label)
        for root in self.roots:
            candidate = root / relative
            if candidate.is_file():
                raw = candidate.read_bytes()
                if sha256(raw) != pin["sha256"]:
                    raise ValueError(f"winning loose {label} hash drift: {logical_path}")
                return raw

        member = pin.get("member")
        if not member:
            raise ValueError(f"pinned loose {label} is missing: {logical_path}")
        archive = self.archive(pin)
        wanted = member.replace("/", "\\").casefold()
        matches = [index for index, name in enumerate(archive.names())
                   if name.replace("/", "\\").casefold() == wanted]
        if len(matches) != 1:
            raise ValueError(f"pinned archive member is absent or ambiguous: {member}")
        raw = archive.read(matches[0])
        if sha256(raw) != pin["sha256"]:
            raise ValueError(f"pinned archive member hash drift: {member}")
        return raw

    def source_bytes(self) -> dict[str, tuple[bytes, bytes]]:
        policy = json.loads(self.policy.read_text(encoding="utf-8-sig"))
        families = policy["denominations"]["modernFamilies"]
        pins = self.pins["sources"]
        by_family = {item["family"]: item for item in pins}
        labels = [item["displayLabel"] for item in families]
        if len(by_family) != len(pins) or set(labels) != set(by_family) or len(labels) != 6:
            raise ValueError("asset family pins differ from the six policy families")
        result = {}
        for family in families:
            label = family["displayLabel"]
            if not label or Path(label).name != label:
                raise ValueError(f"unsafe family label: {label!r}")
            pin = by_family[label]
            mesh = self.resolve(family["sourceModel"], pin["mesh"], f"{label} mesh")
            diffuse = self.resolve(pin["diffusePath"], pin["diffuse"], f"{label} diffuse")
            if recipe.dds_info(diffuse) != pin["dds"]:
                raise ValueError(f"{label} diffuse metadata drift")
            result[label] = (mesh, diffuse)
        return result


def verify_cache(environment: Environment) -> None:
    manifest = environment.workspace / "inputs.json"
    cache = environment.workspace / "inputs"
    if not manifest.is_file() or manifest.read_bytes() != environment.pins_raw:
        raise ValueError("workspace input manifest is missing or differs from shipped pins")
    expected = {}
    for source in environment.pins["sources"]:
        label = source["family"]
        expected[f"{label}/source.nif"] = source["mesh"]["sha256"]
        expected[f"{label}/source.dds"] = source["diffuse"]["sha256"]
    actual = {path.relative_to(cache).as_posix(): sha256(path.read_bytes())
              for path in cache.rglob("*") if path.is_file()} if cache.is_dir() else {}
    if actual != expected:
        raise ValueError("private input cache is incomplete, contains extras, or differs from shipped pins")


def acquire(environment: Environment) -> None:
    sources = environment.source_bytes()
    environment.workspace.mkdir(parents=True, exist_ok=True)
    manifest = environment.workspace / "inputs.json"
    if manifest.exists() and (not manifest.is_file() or manifest.read_bytes() != environment.pins_raw):
        raise ValueError("refusing to replace an existing workspace input manifest")
    cache = environment.workspace / "inputs"
    if cache.exists():
        verify_cache(environment)
        print(f"PASS: existing private cache matches all {len(sources) * 2} pinned vendor inputs")
        return
    if not manifest.exists():
        manifest.write_bytes(environment.pins_raw)
    with tempfile.TemporaryDirectory(prefix="currency-inputs-", dir=environment.workspace) as temporary:
        stage = Path(temporary)
        for label, (mesh, diffuse) in sources.items():
            folder = stage / label
            folder.mkdir()
            (folder / "source.nif").write_bytes(mesh)
            (folder / "source.dds").write_bytes(diffuse)
        stage.rename(cache)
    verify_cache(environment)
    print(f"PASS: acquired {len(sources) * 2} exact vendor inputs into private cache {cache}")


def verify_output(environment: Environment, output_name: str) -> None:
    package = environment.workspace / output_name / "package"
    expected_rows = environment.receipt["files"]
    expected = {row["path"]: (row["bytes"], row["sha256"]) for row in expected_rows}
    actual = {path.relative_to(package).as_posix(): (path.stat().st_size, sha256(path.read_bytes()))
              for path in package.rglob("*") if path.is_file()} if package.is_dir() else {}
    if len(expected) != 36 or actual != expected:
        raise ValueError("built output differs from the 36-file golden integration receipt")
    if environment.receipt["recipeSha256"] != sha256((HERE / "recipe.py").read_bytes()):
        raise ValueError("historical recipe differs from the golden receipt")
    if environment.receipt["inputReceiptSha256"] != sha256(environment.pins_raw):
        raise ValueError("shipped input pins differ from the golden receipt")


def build(environment: Environment, output_name: str) -> None:
    if not output_name or Path(output_name).name != output_name:
        raise ValueError("build output must be one directory name inside the workspace")
    verify_cache(environment)
    recipe.ROOT = environment.workspace
    recipe.COMMANDS.clear()
    recipe.build(output_name)
    verify_output(environment, output_name)
    print(f"PASS: {output_name} is byte-identical to all 36 golden NIF/DDS outputs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-environment", action="store_true")
    mode.add_argument("--acquire-inputs", action="store_true")
    mode.add_argument("--build", metavar="OUTPUT_NAME")
    parser.add_argument("--instance-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=HERE.parent / "policy.json")
    parser.add_argument("--profile", default="Default")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--nif-tool", type=Path, required=True)
    parser.add_argument("--magick", type=Path, required=True)
    parser.add_argument("--texconv", type=Path, required=True)
    args = parser.parse_args()
    environment = Environment(args)
    if args.verify_environment:
        sources = environment.source_bytes()
        print(f"PASS: {len(sources)} families / {len(sources) * 2} exact vendor inputs and all tools verified; no files written")
    elif args.acquire_inputs:
        acquire(environment)
    else:
        build(environment, args.build)


if __name__ == "__main__":
    main()
