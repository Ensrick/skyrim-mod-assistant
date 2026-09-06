"""Portable, fail-closed driver for the attested denomination asset recipe.

The shipped ``recipe.py`` and ``inputs.json`` define the exact seventeen
non-Septim visual designs bound by ``integration-receipt.json``. This driver
supplies machine-local paths, acquires the already-pinned vendor bytes into a
private cache, and runs the recipe. It never downloads, repins, or overwrites
input or output files.
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
EXPECTED_DESIGNS = (
    "Mede", "Ulfric", "Dram", "Oshka", "Ohzer", "Varken",
    "DrakrDragon", "DrakrMoth", "DrakrOwl", "DrakrWhale",
    "GibberFront", "GibberBack", "Mala", "Mallari", "Nchuark",
    "Sancar", "BrumaAyleid",
)
V030_BASELINE_SHA256 = "D5FCDE1BD5E19B4FDF67BEF4F9411C25062E05FDDC98208647FDCB1D4C7A4B89"


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
        for protected, label in ((self.instance, "MO2 instance"), (self.repo, "repository")):
            if (self.workspace == protected or within(self.workspace, protected)
                    or within(protected, self.workspace)):
                raise ValueError(
                    f"workspace must be a dedicated sibling, not inside or an ancestor of the {label}")
        self.roots = enabled_roots(self.instance, args.profile)
        self.tools = {
            "nif": require_file(args.nif_tool, "nif tool"),
            "magick": require_file(args.magick, "ImageMagick"),
            "texconv": require_file(args.texconv, "texconv"),
        }
        self.pins_raw = PIN_PATH.read_bytes()
        self.pins = json.loads(self.pins_raw)
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        if self.pins.get("schemaVersion") != 2 or self.receipt.get("schemaVersion") != 2:
            raise ValueError("unsupported asset pin or receipt schema")
        if self.pins.get("colors") != recipe.COLORS or self.pins.get("maximumDiffuseDimension") != 1024:
            raise ValueError("asset tier colors or maximum diffuse dimension differ from the recipe")
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

    def source_bytes(self) -> dict[str, tuple[bytes, dict[str, bytes]]]:
        pins = self.pins["sources"]
        labels = tuple(item.get("family") for item in pins)
        if labels != EXPECTED_DESIGNS or len({label.casefold() for label in labels}) != len(labels):
            raise ValueError("asset design pins differ from the exact ordered seventeen-design catalog")
        design_ids = [item.get("designId") for item in pins]
        if any(not value for value in design_ids) or len(set(design_ids)) != len(design_ids):
            raise ValueError("asset design IDs are absent or duplicated")
        result = {}
        catalog_labels = tuple(item.get("label") for item in recipe.DESIGNS)
        if catalog_labels != EXPECTED_DESIGNS:
            raise ValueError("recipe design catalog differs from the supported seventeen-design catalog")
        for pin, design in zip(pins, recipe.DESIGNS):
            label = pin["family"]
            if not label or Path(label).name != label:
                raise ValueError(f"unsafe design label: {label!r}")
            mesh = self.resolve(pin["meshLogicalPath"], pin["mesh"], f"{label} mesh")
            authored = {shape["textures"][0].casefold() for shape in pin["inspection"]["shapeDetails"]}
            configured = {item["sourcePath"].casefold() for item in pin["diffuses"]}
            if not configured or authored != configured:
                raise ValueError(f"{label} diffuse-slot pins differ from the inspected source NIF")
            manifest_pairs = tuple((item["sourcePath"].casefold(), item.get("outputSuffix"))
                                   for item in pin["diffuses"])
            catalog_pairs = tuple((item["path"].casefold(), item.get("outputSuffix"))
                                  for item in design["diffuses"])
            if (pin.get("designId") != design["designId"] or
                    pin.get("currencyId") != design["currencyId"] or
                    pin.get("bindings") != design["bindings"] or
                    pin.get("meshLogicalPath", "").casefold() != design["meshPath"].casefold() or
                    manifest_pairs != catalog_pairs):
                raise ValueError(f"{label} manifest mapping differs from the exact recipe catalog")
            suffixes = tuple(item.get("outputSuffix") for item in pin["diffuses"])
            expected_suffixes = ("Face0", "Face10") if label in ("GibberFront", "GibberBack") else (None,)
            if suffixes != expected_suffixes:
                raise ValueError(f"{label} diffuse output suffix set changed")
            diffuse_bytes = {}
            for diffuse_pin in pin["diffuses"]:
                cache_file = safe_relative(diffuse_pin["cacheFile"], f"{label} diffuse cache file")
                if len(cache_file.parts) != 1 or cache_file.suffix.casefold() != ".dds":
                    raise ValueError(f"unsafe diffuse cache file for {label}")
                diffuse = self.resolve(diffuse_pin["sourcePath"], diffuse_pin["file"],
                                       f"{label} {cache_file.name}")
                if recipe.dds_info(diffuse) != diffuse_pin["dds"]:
                    raise ValueError(f"{label} diffuse metadata drift: {cache_file.name}")
                diffuse_bytes[cache_file.name] = diffuse
            if len(diffuse_bytes) != len(pin["diffuses"]):
                raise ValueError(f"{label} reuses a diffuse cache filename")
            result[label] = (mesh, diffuse_bytes)
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
        for diffuse in source["diffuses"]:
            expected[f"{label}/{diffuse['cacheFile']}"] = diffuse["file"]["sha256"]
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
        input_count = sum(1 + len(diffuses) for _mesh, diffuses in sources.values())
        print(f"PASS: existing private cache matches all {input_count} pinned vendor inputs")
        return
    if not manifest.exists():
        manifest.write_bytes(environment.pins_raw)
    with tempfile.TemporaryDirectory(prefix="currency-inputs-", dir=environment.workspace) as temporary:
        stage = Path(temporary)
        for label, (mesh, diffuses) in sources.items():
            folder = stage / label
            folder.mkdir()
            (folder / "source.nif").write_bytes(mesh)
            for cache_file, diffuse in diffuses.items():
                (folder / cache_file).write_bytes(diffuse)
        stage.rename(cache)
    verify_cache(environment)
    input_count = sum(1 + len(diffuses) for _mesh, diffuses in sources.values())
    print(f"PASS: acquired {input_count} exact vendor inputs into private cache {cache}")


def verify_output(environment: Environment, output_name: str) -> None:
    package = environment.workspace / output_name / "package"
    expected_rows = environment.receipt["files"]
    expected = {row["path"]: (row["bytes"], row["sha256"]) for row in expected_rows}
    deterministic_paths = set()
    for source in environment.pins["sources"]:
        label = source["family"]
        for tier in recipe.COLORS:
            stem = f"{label}_{tier}"
            deterministic_paths.add(f"Meshes/Ensrick/Currency/{label}/{stem}.nif")
            for diffuse in source["diffuses"]:
                suffix = diffuse["outputSuffix"]
                output_stem = stem if suffix is None else f"{stem}_{suffix}"
                deterministic_paths.add(f"textures/Ensrick/Currency/{label}/{output_stem}.dds")
    actual = {path.relative_to(package).as_posix(): (path.stat().st_size, sha256(path.read_bytes()))
              for path in package.rglob("*") if path.is_file()} if package.is_dir() else {}
    expected_count = sum(1 + len(source["diffuses"])
                         for source in environment.pins["sources"]) * len(recipe.COLORS)
    if (expected_count != 108 or environment.receipt.get("outputCount") != expected_count or
            len(expected_rows) != expected_count or len(expected) != expected_count or
            set(expected) != deterministic_paths or actual != expected):
        raise ValueError(f"built output differs from the {expected_count}-file golden integration receipt")
    if environment.receipt["recipeSha256"] != sha256((HERE / "recipe.py").read_bytes()):
        raise ValueError("historical recipe differs from the golden receipt")
    if environment.receipt["inputReceiptSha256"] != sha256(environment.pins_raw):
        raise ValueError("shipped input pins differ from the golden receipt")
    baseline = environment.receipt.get("preservedV030Baseline") or {}
    if (baseline.get("receiptSha256") != V030_BASELINE_SHA256 or
            baseline.get("preservedOutputCount") != 36 or
            baseline.get("status") != "36/36 path, size, and SHA256 tuples unchanged"):
        raise ValueError("golden receipt lacks the exact 0.3.0 baseline-preservation attestation")


def build(environment: Environment, output_name: str) -> None:
    if not output_name or Path(output_name).name != output_name:
        raise ValueError("build output must be one directory name inside the workspace")
    verify_cache(environment)
    recipe.ROOT = environment.workspace
    recipe.COMMANDS.clear()
    recipe.build(output_name)
    verify_output(environment, output_name)
    print(f"PASS: {output_name} is byte-identical to all {len(environment.receipt['files'])} "
          "golden NIF/DDS outputs")


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
        input_count = sum(1 + len(diffuses) for _mesh, diffuses in sources.values())
        print(f"PASS: {len(sources)} designs / {input_count} exact vendor inputs and all tools verified; "
              "no files written")
    elif args.acquire_inputs:
        acquire(environment)
    else:
        build(environment, args.build)


if __name__ == "__main__":
    main()
