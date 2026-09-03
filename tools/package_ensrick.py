#!/usr/bin/env python3
"""Build the Ensrick patch collection and recipe set from the ledger (#160).

Two output sets, both under dist/ (gitignored, never committed):

  dist/ensrick-patches/<MO2 mod name>/...   every ledger row with
      `distribution: distributable`, minus files matched by .packagingignore
      or the row's `packagingExcludes`, minus rows whose `sharedList` says
      excluded. manifest.json beside them lists every shipped file with its
      SHA-256, the row's licence/basis text and the source-build record.
  dist/ensrick-recipes/recipes.json          every `distribution: recipe` row
      as a machine-readable regeneration recipe: tool + pin (commit or
      version + hash), input archive/file hashes, command, expected output
      hashes. A row whose recorded recipe lacks any of those is listed under
      "gaps" and NOT included.
  dist/README.md                             what the two sets are and which
      vendor downloads / tools the recipes need.

Before anything is written, every file destined for ensrick-patches is
compared by SHA-256 against vendor bytes: every file in every other MO2 mod
folder, every extracted folder and zip entry under the instance's downloads/,
and every input hash recorded in ledger recipes and source-build records.
A match is a violation: the file is withheld, listed in the manifest under
"withheld", and the exit code is 2. 7z/rar archives cannot be read with the
standard library and are reported as not scanned (their MO2-extracted mod
folders are scanned instead).

Exception (#160 ruling, 2026-09-02): a ledger row may carry
`vendorBytesAllowed: {"basis": "...", "files": [...]}`. A vendor-hash match on
a file listed there passes, and is reported under "allowedVendorFiles"
instead of "withheld", ONLY when the basis names a permissive licence (MIT,
BSD, Apache, CC-BY, CC-BY-SA) or quotes a Nexus permission that grants upload
of modified files. Any other basis is ignored and the match stays a violation.
MIT explicitly permits redistributing the verbatim files with the notice, so
the byte check alone is over-strict for permissively licensed sources.

Recipe kinds understood in a ledger row's `recipe` field: texconv,
nif-port-cli <verb>, archive-extract, script (a build.py in this repo) and
tool (any pinned external tool: name + version/commit + sha256, with either
1:1 `steps` or aggregate `inputs`/`outputs` lists). Rows without a `recipe`
field fall back to their records/source-builds json.

Read-only on the MO2 instance. Standard library only.

    py -3 tools/package_ensrick.py --dry-run   # plan + verification, no writes
    py -3 tools/package_ensrick.py             # writes dist/

Eligibility (ruling 2026-09-02): only Ensrick-made rows may carry a
`distribution` field: rows with an Ensrick source-build record, or whose name
starts with `Ensrick` / ends with `- Ensrick <ver>`. Any other classified row
(an unmodified third-party release, whatever its licence) is a vendor row and
a required download from its source; it is reported under
"classificationErrors" and not packaged.

Exit codes: 0 clean, 2 vendor-byte violations or classification errors, 1 error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "records" / "installed-mods.json"
PACKAGING_IGNORE = REPO / ".packagingignore"
SOURCE_BUILDS = REPO / "records" / "source-builds"
DEFAULT_DIST = REPO / "dist"

HEX64 = re.compile(r"^[0-9A-Fa-f]{64}$")
RECORD_RE = re.compile(r"records/source-builds/[A-Za-z0-9._-]+\.json")
SCRIPT_RE = re.compile(r"(overlays/[A-Za-z0-9._/-]+?/build\.py)")
NEXUS_RE = re.compile(r"Nexus\s+(\d+)\s+file\s+(\d+)", re.IGNORECASE)
NEXUS_URL_RE = re.compile(r"nexusmods\.com/skyrimspecialedition/mods/(\d+)")
PLUGIN_EXT = {".esp", ".esl", ".esm"}
CHUNK = 1 << 20
# vendorBytesAllowed basis must name a permissive licence ...
LICENCE_BASIS_RE = re.compile(r"\b(MIT|BSD|Apache|CC[- ]BY(?:[- ]SA)?)\b", re.IGNORECASE)
# ... or quote a Nexus permission line that grants uploading (modified) files.
QUOTED_UPLOAD_RE = re.compile(r"[\"'“‘][^\"'”’]*upload[^\"'”’]*[\"'”’]", re.IGNORECASE)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def sha256_stream(fh) -> str:
    h = hashlib.sha256()
    for block in iter(lambda: fh.read(CHUNK), b""):
        h.update(block)
    return h.hexdigest()


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def norm_hash(value) -> str | None:
    if isinstance(value, str) and HEX64.match(value):
        return value.lower()
    return None


def walk_files(root: Path):
    """Yield (relative posix path, absolute path, size) for every file."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = Path(dirpath) / name
            try:
                size = full.stat().st_size
            except OSError:
                continue
            out.append((full.relative_to(root).as_posix(), full, size))
    return out


def is_invocation(command) -> bool:
    """A recorded command must be more than a bare verb to be executable."""
    return isinstance(command, str) and " " in command.strip()


def vendor_allow(row):
    """Normalise a ledger row's vendorBytesAllowed field (#160 ruling).

    Returns None when the row has no such field; otherwise a dict with the
    lower-cased forward-slash file list, the basis text and whether the basis
    is acceptable (permissive licence name or a quoted upload permission).
    """
    allow = row.get("vendorBytesAllowed")
    if not isinstance(allow, dict):
        return None
    basis = str(allow.get("basis") or "").strip()
    files = sorted({str(f).replace("\\", "/").strip("/").lower()
                    for f in allow.get("files") or [] if isinstance(f, str) and f.strip()})
    accepted = bool(basis) and bool(files) and bool(LICENCE_BASIS_RE.search(basis) or QUOTED_UPLOAD_RE.search(basis))
    reason = None
    if not accepted:
        reason = ("vendorBytesAllowed ignored: basis must name a permissive licence (MIT/BSD/Apache/CC-BY/CC-BY-SA) "
                  "or quote a Nexus permission granting upload of modified files, and files must be listed")
    return {"basis": basis, "files": files, "accepted": accepted, "reason": reason}


# --------------------------------------------------------------------------
# .packagingignore + ledger packagingExcludes
# --------------------------------------------------------------------------

def load_ignore_patterns(path: Path):
    patterns = []
    if not path.exists():
        return patterns
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line.replace("\\", "/").lower())
    return patterns


def ignore_reason(mod_name: str, rel: str, patterns, row_excludes):
    key = f"{mod_name}/{rel}".lower()
    for pattern in patterns:
        if fnmatch.fnmatchcase(key, pattern):
            return f".packagingignore: {pattern}"
    rel_l = rel.lower()
    for exclude in row_excludes or []:
        if rel_l == str(exclude).replace("\\", "/").strip("/").lower():
            return f"ledger packagingExcludes: {exclude}"
    return None


# --------------------------------------------------------------------------
# source-build records
# --------------------------------------------------------------------------

def load_source_build_records():
    records = {}
    if not SOURCE_BUILDS.is_dir():
        return records
    for path in sorted(SOURCE_BUILDS.glob("*.json")):
        try:
            records[path.relative_to(REPO).as_posix()] = load_json(path)
        except (OSError, ValueError) as exc:
            print(f"WARN: cannot read {path}: {exc}", file=sys.stderr)
    return records


def record_mod_names(record) -> set:
    names = set()
    for key in ("mo2Mod", "mo2OverlayMod", "modName"):
        if isinstance(record.get(key), str):
            names.add(record[key])
    installation = record.get("installation")
    if isinstance(installation, dict) and isinstance(installation.get("mo2Mod"), str):
        names.add(installation["mo2Mod"])
    component = record.get("component")
    if isinstance(component, str):
        # e.g. "LaunchProbe (SKSE launch-verification instrumentation)" names the mod before the parenthesis
        names.add(component.split(" (", 1)[0].strip())
    return names


def find_record(row, records):
    recipe = row.get("recipe") or {}
    candidates = []
    if isinstance(recipe.get("record"), str):
        candidates.append(recipe["record"])
    file_name = (row.get("fileName") or "").replace("\\", "/")
    candidates += RECORD_RE.findall(file_name)
    match = re.match(r"records/source-builds/([A-Za-z0-9._-]+)$", file_name.strip())
    if match:
        candidates.append(f"records/source-builds/{match.group(1)}.json")
    for path, data in records.items():
        if row["modName"] in record_mod_names(data):
            candidates.append(path)
    for candidate in candidates:
        if candidate in records:
            return candidate
    return None


def find_script(row):
    recipe = row.get("recipe") or {}
    if isinstance(recipe.get("script"), str) and (REPO / recipe["script"]).exists():
        return recipe["script"]
    file_name = (row.get("fileName") or "").replace("\\", "/")
    match = SCRIPT_RE.search(file_name)
    if match and (REPO / match.group(1)).exists():
        return match.group(1)
    match = re.match(r"(overlays/[A-Za-z0-9._-]+)$", file_name.strip())
    if match and (REPO / match.group(1) / "build.py").exists():
        return f"{match.group(1)}/build.py"
    return None


def find_tracked_overlay(row):
    file_name = (row.get("fileName") or "").replace("\\", "/").strip()
    match = re.match(r"(overlays/[A-Za-z0-9._-]+)$", file_name)
    if match and (REPO / match.group(1)).is_dir():
        return match.group(1)
    return None


def record_expected_files(record) -> dict:
    """rel path -> sha256 for records that list the whole package."""
    expected = {}
    package = record.get("package")
    files = package.get("files") if isinstance(package, dict) else None
    if isinstance(files, dict):
        for rel, value in files.items():
            sha = norm_hash(value) if isinstance(value, str) else norm_hash(
                value.get("sha256") if isinstance(value, dict) else None)
            if sha:
                expected[rel.replace("\\", "/").lower()] = sha
    return expected


def record_single_output_hash(record):
    output = record.get("output")
    if isinstance(output, dict):
        for key in ("sha256", "meshSha256"):
            sha = norm_hash(output.get(key))
            if sha:
                return sha
    return norm_hash(record.get("outputSha256"))


# --------------------------------------------------------------------------
# vendor download references
# --------------------------------------------------------------------------

def vendor_rows_by_mod_id(rows):
    by_id = {}
    for row in rows:
        mod_id = row.get("modId")
        if isinstance(mod_id, int) and mod_id > 0 and not row.get("distribution"):
            by_id.setdefault(mod_id, []).append(row)
    return by_id


def vendor_refs_in_text(texts, by_id):
    """Every distinct 'Nexus <mod> file <file>' reference found in the given strings."""
    seen, refs = set(), []
    for text in texts:
        for match in NEXUS_RE.finditer(text or ""):
            key = (int(match.group(1)), int(match.group(2)))
            if key in seen:
                continue
            seen.add(key)
            refs.extend(vendor_refs(key[0], key[1], by_id))
    return refs


def vendor_refs(mod_id, file_id, by_id):
    hits = by_id.get(mod_id, [])
    if file_id:
        exact = [r for r in hits if r.get("fileId") == file_id]
        hits = exact or hits
    refs = []
    for row in hits:
        refs.append({
            "ledgerRow": row["modName"],
            "nexusModId": mod_id,
            "fileId": row.get("fileId"),
            "fileName": row.get("fileName"),
            "version": row.get("version"),
            "archiveSha256": norm_hash(row.get("sha256")),
            "nexusUrl": f"https://www.nexusmods.com/skyrimspecialedition/mods/{mod_id}",
        })
    if not refs:
        refs.append({
            "ledgerRow": None,
            "nexusModId": mod_id,
            "fileId": file_id,
            "fileName": None,
            "version": None,
            "archiveSha256": None,
            "nexusUrl": f"https://www.nexusmods.com/skyrimspecialedition/mods/{mod_id}",
        })
    return refs


# --------------------------------------------------------------------------
# recipe normalisation
# --------------------------------------------------------------------------

def _step(inp, inp_sha, inp_bytes, command, output, out_sha, out_bytes):
    return {
        "input": inp,
        "inputSha256": norm_hash(inp_sha),
        "inputBytes": inp_bytes,
        "command": command,
        "output": output,
        "outputSha256": norm_hash(out_sha),
        "outputBytes": out_bytes,
    }


def _multi_step(inputs, command, outputs):
    """One aggregate step: many inputs -> one command -> many outputs."""
    return {
        "inputs": [{"input": i.get("source") or i.get("input"), "inputSha256": norm_hash(i.get("sha256") or i.get("inputSha256")),
                    "inputBytes": i.get("bytes") if i.get("bytes") is not None else i.get("inputBytes"),
                    **{k: v for k, v in i.items() if k in ("files", "aggregate", "provider", "note", "role")}}
                   for i in inputs],
        "command": command,
        "outputs": [{"output": o.get("path") or o.get("output"), "outputSha256": norm_hash(o.get("sha256") or o.get("outputSha256")),
                     "outputBytes": o.get("bytes") if o.get("bytes") is not None else o.get("outputBytes")}
                    for o in outputs],
    }


def _check_steps(steps, missing):
    if not steps:
        missing.append("no steps (no input/output pairs recorded)")
        return
    for step in steps:
        if "inputs" in step or "outputs" in step:
            _check_multi(step, missing)
            continue
        label = step.get("output") or step.get("input") or "?"
        if not step.get("inputSha256"):
            missing.append(f"input hash for {label}")
        if not is_invocation(step.get("command")):
            missing.append(f"executable command for {label} (recorded: {step.get('command')!r})")
        if not step.get("outputSha256"):
            missing.append(f"expected output hash for {label}")


def _check_multi(step, missing):
    inputs, outputs = step.get("inputs") or [], step.get("outputs") or []
    if not inputs:
        missing.append("input archive/file hashes")
    for item in inputs:
        if not item.get("inputSha256"):
            missing.append(f"input hash for {item.get('input') or '?'}")
    if not is_invocation(step.get("command")):
        missing.append(f"executable command (recorded: {step.get('command')!r})")
    if not outputs:
        missing.append("expected output hashes")
    for item in outputs:
        if not item.get("outputSha256"):
            missing.append(f"expected output hash for {item.get('output') or '?'}")


def _pin_ok(tool) -> bool:
    """A tool is pinned when it has a commit or version AND a binary/script hash."""
    return bool((tool.get("commit") or tool.get("version"))
                and norm_hash(tool.get("sha256") or tool.get("binarySha256") or tool.get("scriptSha256")))


def normalize_recipe(row, records, by_id):
    """Return (recipe dict, missing list). The recipe is complete iff missing is empty."""
    name = row["modName"]
    recipe_field = row.get("recipe") or {}
    record_path = find_record(row, records)
    record = records.get(record_path) if record_path else None
    out = {
        "modName": name,
        "version": row.get("version"),
        "kind": recipe_field.get("kind"),
        "tool": None,
        "vendorDownloads": [],
        "steps": [],
        "basis": row.get("distributionBasis"),
        "sourceBuildRecord": record_path,
        "recordedAt": recipe_field.get("recordedAt"),
        "verification": recipe_field.get("verification"),
        "notes": [],
    }
    missing = []
    kind = recipe_field.get("kind")

    if kind == "texconv":
        tool = recipe_field.get("tool") or {}
        out["tool"] = {
            "name": "texconv (DirectXTex)",
            "toolchainKey": tool.get("toolchainKey"),
            "version": tool.get("version"),
            "sha256": norm_hash(tool.get("sha256")),
            "wingetPackage": tool.get("wingetPackage"),
            "wingetVersion": tool.get("wingetVersion"),
        }
        if not (tool.get("version") and norm_hash(tool.get("sha256"))):
            missing.append("tool pin (texconv version + sha256)")
        for step in recipe_field.get("steps") or []:
            out["steps"].append(_step(step.get("source"), step.get("sourceSha256"), step.get("sourceBytes"),
                                      step.get("command"), step.get("output"), step.get("outputSha256"),
                                      step.get("outputBytes")))
        out["sourceForm"] = recipe_field.get("sourceForm")
        match = NEXUS_RE.search(recipe_field.get("sourceForm") or "")
        if match:
            out["vendorDownloads"] = vendor_refs(int(match.group(1)), int(match.group(2)), by_id)
        _check_steps(out["steps"], missing)

    elif kind and kind.startswith("nif-port-cli"):
        tool = recipe_field.get("tool") or {}
        out["tool"] = {
            "name": "nif-port-cli " + kind.split(" ", 1)[1] if " " in kind else "nif-port-cli",
            "toolchainKey": tool.get("toolchainKey"),
            "repository": tool.get("repository"),
            "commit": tool.get("commit"),
            "branch": tool.get("branch"),
            "pullRequest": tool.get("pullRequest"),
            "binarySha256": norm_hash(tool.get("binarySha256")),
            "upstreamCommit": tool.get("upstreamCommit"),
            "niflyCommit": tool.get("niflyCommit"),
            "commitNote": tool.get("commitNote"),
        }
        if not tool.get("commit"):
            missing.append("tool pin (nif-port-cli commit)")
        if record is None:
            missing.append("source-builds record with per-file input/output hashes")
        else:
            transformation = record.get("transformation") or {}
            command = transformation.get("command")
            for mesh in record.get("meshes") or []:
                inp = mesh.get("source") or f"vendor mod: {record.get('mo2VendorMod')}/{mesh.get('path')}"
                out["steps"].append(_step(inp, mesh.get("sourceSha256"), mesh.get("sourceBytes"), command,
                                          mesh.get("path"), mesh.get("outputSha256"), mesh.get("outputBytes")))
            source = record.get("source") or {}
            match = NEXUS_URL_RE.search(source.get("nexusUrl") or "")
            if match:
                out["vendorDownloads"] = vendor_refs(int(match.group(1)), source.get("fileId"), by_id)
            out["inputForm"] = source.get("inputForm")
        _check_steps(out["steps"], missing)

    elif kind == "archive-extract":
        archive = recipe_field.get("archive") or {}
        out["tool"] = {"name": "archive extraction (any zip reader)", "version": "n/a",
                       "note": "verbatim copy of one archive entry; no transformation tool"}
        out["vendorDownloads"] = [{
            "ledgerRow": None,
            "nexusModId": archive.get("nexusModId"),
            "fileId": archive.get("fileId"),
            "fileName": archive.get("fileName"),
            "version": None,
            "archiveSha256": norm_hash(archive.get("sha256")),
            "archiveBytes": archive.get("bytes"),
            "nexusUrl": f"https://www.nexusmods.com/skyrimspecialedition/mods/{archive.get('nexusModId')}",
        }]
        if archive.get("nexusModId"):
            for ref in vendor_refs(archive["nexusModId"], archive.get("fileId"), by_id):
                if ref["ledgerRow"]:
                    out["vendorDownloads"][0]["ledgerRow"] = ref["ledgerRow"]
                    out["vendorDownloads"][0]["version"] = ref["version"]
        if not norm_hash(archive.get("sha256")):
            missing.append("input archive hash")
        for step in recipe_field.get("steps") or []:
            transform = (step.get("transform") or "").strip().lower()
            verbatim = transform.startswith("none")
            command = (f"extract archive entry '{step.get('archiveInternalPath')}' from "
                       f"'{archive.get('fileName')}' to '{step.get('destination')}' ({step.get('transform')})")
            out["steps"].append(_step(f"archive entry: {step.get('archiveInternalPath')}", step.get("sourceSha256"),
                                      step.get("sourceBytes"), command, step.get("destination"),
                                      step.get("sourceSha256") if verbatim else step.get("outputSha256"),
                                      step.get("sourceBytes") if verbatim else step.get("outputBytes")))
        _check_steps(out["steps"], missing)

    elif kind == "script":
        script = recipe_field.get("script")
        script_path = REPO / script if isinstance(script, str) else None
        out["tool"] = {
            "name": script,
            "repository": "https://github.com/Ensrick/skyrim-mod-assistant",
            "scriptSha256": sha256_path(script_path) if script_path and script_path.exists() else None,
            "interpreter": "py -3 (standard library only)",
        }
        if not out["tool"]["scriptSha256"]:
            missing.append(f"script {script!r} not found in the repository")
        dependencies = []
        for dep in recipe_field.get("dependencies") or []:
            dep_path = REPO / dep.get("path", "") if isinstance(dep, dict) and dep.get("path") else None
            dependencies.append({"path": dep.get("path") if isinstance(dep, dict) else str(dep),
                                 "sha256": sha256_path(dep_path) if dep_path and dep_path.exists() else None,
                                 "role": dep.get("role") if isinstance(dep, dict) else None})
            if not dependencies[-1]["sha256"]:
                missing.append(f"script dependency {dependencies[-1]['path']!r} not found in the repository")
        if dependencies:
            out["tool"]["dependencies"] = dependencies
        command = recipe_field.get("command")
        inputs = recipe_field.get("inputs") or []
        outputs = recipe_field.get("outputs") or []
        if len(inputs) == len(outputs) and inputs and not recipe_field.get("aggregate"):
            for inp, outp in zip(inputs, outputs):
                out["steps"].append(_step(inp.get("source"), inp.get("sha256"), inp.get("bytes"), command,
                                          outp.get("path"), outp.get("sha256"), outp.get("bytes")))
                if inp.get("action") or outp.get("action"):
                    out["steps"][-1]["action"] = inp.get("action") or outp.get("action")
        else:
            out["steps"].append(_multi_step(inputs, command, outputs))
        out["method"] = recipe_field.get("method")
        out["vendorDownloads"] = vendor_refs_in_text([i.get("source") for i in inputs], by_id)
        _check_steps(out["steps"], missing)

    elif kind == "tool":
        tool = recipe_field.get("tool") or {}
        out["tool"] = {key: tool.get(key) for key in ("name", "version", "repository", "commit", "branch", "sha256",
                                                        "binarySha256", "path", "license", "note")}
        out["tool"]["sha256"] = norm_hash(tool.get("sha256") or tool.get("binarySha256"))
        out["tool"].pop("binarySha256", None)
        if not _pin_ok(tool):
            missing.append(f"tool pin ({tool.get('name') or 'tool'}: version or commit + sha256)")
        aux = []
        for extra in recipe_field.get("auxiliaryTools") or []:
            aux.append(extra)
            if isinstance(extra, dict) and extra.get("required") and not _pin_ok(extra):
                missing.append(f"tool pin ({extra.get('name') or 'auxiliary tool'}: version or commit + sha256)")
        if aux:
            out["tool"]["auxiliaryTools"] = aux
        default_command = recipe_field.get("command")
        steps = recipe_field.get("steps") or []
        inputs = recipe_field.get("inputs") or []
        outputs = recipe_field.get("outputs") or []
        texts = []
        if steps:
            for step in steps:
                normalized = _step(step.get("source"), step.get("sourceSha256"), step.get("sourceBytes"),
                                   step.get("command") or default_command, step.get("output"),
                                   step.get("outputSha256"), step.get("outputBytes"))
                for key in ("edits", "note", "action"):
                    if step.get(key) is not None:
                        normalized[key] = step[key]
                out["steps"].append(normalized)
                texts.append(step.get("source"))
        else:
            out["steps"].append(_multi_step(inputs, default_command, outputs))
            texts.extend(i.get("source") for i in inputs)
        out["method"] = recipe_field.get("method")
        out["vendorDownloads"] = vendor_refs_in_text(texts + [recipe_field.get("sourceForm")], by_id)
        out["sourceForm"] = recipe_field.get("sourceForm")
        if recipe_field.get("notes"):
            out["notes"].extend(recipe_field["notes"] if isinstance(recipe_field["notes"], list)
                                else [recipe_field["notes"]])
        _check_steps(out["steps"], missing)

    elif kind:
        missing.append(f"unknown recipe kind {kind!r}")

    elif record is not None:
        # No ledger recipe field: best-effort read of the source-builds record.
        out["kind"] = "source-builds record"
        transformation = record.get("transformation") or {}
        tool = transformation.get("tool") if isinstance(transformation.get("tool"), dict) else {}
        source = record.get("source") or {}
        commit = (tool.get("commit") or transformation.get("toolCommit") or source.get("commit"))
        repository = (tool.get("repository") or transformation.get("toolRepository") or source.get("repository"))
        syntax = (transformation.get("commandSyntax") or "").split(" <")[0].strip()
        out["tool"] = {
            "name": (tool.get("name") or tool.get("toolchainKey") or syntax or record.get("component")),
            "repository": repository,
            "commit": commit,
            "binarySha256": norm_hash(tool.get("binarySha256") or transformation.get("toolBinarySha256")),
            "generator": record.get("generator"),
            "commandSyntax": transformation.get("commandSyntax"),
        }
        if not commit:
            missing.append("tool pin (no commit recorded)")
        build = record.get("build") if isinstance(record.get("build"), dict) else {}
        command = (transformation.get("command") or record.get("regenerate") or record.get("usage")
                   or build.get("command"))
        input_hashes, output_hashes, per_file = [], [], []
        for mesh in record.get("meshes") or []:
            for key in ("sourceSha256", "vendorSourceSha256", "bodySourceSha256"):
                if norm_hash(mesh.get(key)):
                    label = mesh.get({"sourceSha256": "source", "vendorSourceSha256": "donorSource",
                                      "bodySourceSha256": "baseSource"}[key]) or f"{mesh.get('path')} <- {key}"
                    input_hashes.append((label, mesh[key], mesh.get("sourceBytes")))
            if norm_hash(mesh.get("outputSha256")):
                output_hashes.append((mesh.get("path"), mesh["outputSha256"], mesh.get("outputBytes")))
            if is_invocation(mesh.get("command")):
                per_file.append({"output": mesh.get("path"), "command": mesh["command"]})
        for key in ("archiveSha256", "meshSha256"):
            if norm_hash(source.get(key)):
                input_hashes.append((source.get("meshPath") if key == "meshSha256" and source.get("meshPath")
                                     else f"source.{key}", source[key], source.get("archiveBytes")))
        for item in record.get("inputs") or []:
            if isinstance(item, dict) and norm_hash(item.get("sha256")):
                label = item.get("source") or item.get("plugin") or item.get("path") or "input"
                if item.get("provider"):
                    label = f"{label} (from {item['provider']})"
                input_hashes.append((label, item["sha256"], item.get("bytes")))
        for copy in transformation.get("verbatimCopies") or []:
            if is_invocation(copy.get("command")):
                per_file.append({"output": copy.get("destination"), "command": copy["command"]})
        output = record.get("output") if isinstance(record.get("output"), dict) else {}
        for key in ("sha256", "meshSha256"):
            if norm_hash(output.get(key)):
                output_hashes.append((record.get("outputPlugin") or "output", output[key], output.get("bytes")))
        if isinstance(output.get("textureFiles"), dict):
            for rel, sha in output["textureFiles"].items():
                if norm_hash(sha):
                    output_hashes.append((rel, sha, None))
        if norm_hash(record.get("outputSha256")):
            output_hashes.append((record.get("outputPlugin") or "output", record["outputSha256"], record.get("outputBytes")))
        if not input_hashes:
            missing.append("input archive/file hashes")
        if not output_hashes:
            missing.append("expected output hashes")
        if not is_invocation(command):
            missing.append(f"executable command (recorded: {command!r})")
        step = {
            "inputs": [{"input": i, "inputSha256": norm_hash(s), "inputBytes": b} for i, s, b in input_hashes],
            "command": command,
            "outputs": [{"output": o, "outputSha256": norm_hash(s), "outputBytes": b} for o, s, b in output_hashes],
        }
        if per_file:
            step["perFileCommands"] = per_file
        out["steps"].append(step)
        match = NEXUS_URL_RE.search(source.get("nexusUrl") or "")
        if match:
            out["vendorDownloads"] = vendor_refs(int(match.group(1)), source.get("fileId"), by_id)
        extra_refs = vendor_refs_in_text([i.get("source") for i in record.get("inputs") or [] if isinstance(i, dict)], by_id)
        for ref in extra_refs:
            if all((ref["nexusModId"], ref["fileId"]) != (r["nexusModId"], r["fileId"]) for r in out["vendorDownloads"]):
                out["vendorDownloads"].append(ref)
        if transformation.get("reproduction"):
            out["verification"] = transformation["reproduction"]
        out["notes"].append("derived from the source-builds record; the ledger row has no `recipe` field")

    else:
        script = find_script(row)
        if script:
            missing.append(f"no `recipe` field on the ledger row; {script} exists but its input/output hashes "
                           "are not recorded in machine-readable form")
        else:
            missing.append("no `recipe` field on the ledger row and no source-builds record matched")

    return out, missing


# --------------------------------------------------------------------------
# vendor-byte verification
# --------------------------------------------------------------------------

def collect_recorded_hashes(obj, keypath, sink, origin):
    if isinstance(obj, dict):
        for key, value in obj.items():
            collect_recorded_hashes(value, keypath + [str(key)], sink, origin)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            collect_recorded_hashes(value, keypath + [str(index)], sink, origin)
    else:
        sha = norm_hash(obj)
        if sha:
            # Judge by key NAMES only: list indices and path-like keys (a file
            # path such as "Source/Scripts/x.psc" used as a dict key) say
            # nothing about whether the hash is a vendor input.
            names = [k.lower() for k in keypath if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)]
            joined = ".".join(names)
            vendor_input = any(t in joined for t in ("source", "vendor", "input"))
            # A ledger recipe's `archive` block is the vendor download itself.
            if keypath[:2] == ["recipe", "archive"]:
                vendor_input = True
            if vendor_input and "output" not in joined:
                sink.setdefault(sha, []).append(f"{origin}#{'.'.join(keypath)}")


def build_vendor_index(instance: Path, packaged_names, sizes, scan_archives, rows, records):
    index = {}
    stats = {
        "modFoldersScanned": 0,
        "looseFilesSeen": 0,
        "looseFilesHashed": 0,
        "downloadFoldersScanned": 0,
        "zipArchivesScanned": 0,
        "zipEntriesSeen": 0,
        "zipEntriesHashed": 0,
        "unscannedArchives": [],
        "unreadableArchives": [],
        "recordedInputHashes": 0,
        "sizeFilter": "only vendor files whose byte size equals a packaged file's size are hashed",
    }

    def scan_tree(root: Path, origin_prefix: str):
        for rel, full, size in walk_files(root):
            stats["looseFilesSeen"] += 1
            if size in sizes:
                try:
                    sha = sha256_path(full)
                except OSError:
                    continue
                stats["looseFilesHashed"] += 1
                index.setdefault(sha, []).append(f"{origin_prefix}/{rel}")

    mods_root = instance / "mods"
    if mods_root.is_dir():
        for entry in sorted(mods_root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir() or entry.name in packaged_names:
                continue
            stats["modFoldersScanned"] += 1
            scan_tree(entry, f"mods/{entry.name}")

    downloads = instance / "downloads"
    if downloads.is_dir():
        for entry in sorted(downloads.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                stats["downloadFoldersScanned"] += 1
                scan_tree(entry, f"downloads/{entry.name}")
                continue
            suffix = entry.suffix.lower()
            if suffix == ".zip":
                if not scan_archives:
                    stats["unscannedArchives"].append(f"{entry.name} (--no-archive-scan)")
                    continue
                try:
                    with zipfile.ZipFile(entry) as archive:
                        stats["zipArchivesScanned"] += 1
                        for info in archive.infolist():
                            if info.is_dir():
                                continue
                            stats["zipEntriesSeen"] += 1
                            if info.file_size in sizes:
                                with archive.open(info) as fh:
                                    sha = sha256_stream(fh)
                                stats["zipEntriesHashed"] += 1
                                index.setdefault(sha, []).append(f"downloads/{entry.name}::{info.filename}")
                except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as exc:
                    stats["unreadableArchives"].append(f"{entry.name}: {exc}")
            elif suffix in (".7z", ".rar"):
                stats["unscannedArchives"].append(entry.name)

    # Recorded vendor input hashes (ledger recipes, vendor archive hashes, source-build records).
    recorded = {}
    for row in rows:
        if row.get("distribution"):
            if row.get("recipe"):
                collect_recorded_hashes(row["recipe"], ["recipe"], recorded, f"ledger:{row['modName']}")
        else:
            sha = norm_hash(row.get("sha256"))
            if sha:
                recorded.setdefault(sha, []).append(f"ledger archive:{row['modName']} ({row.get('fileName')})")
    for path, record in records.items():
        collect_recorded_hashes(record, [], recorded, path)
    stats["recordedInputHashes"] = len(recorded)
    for sha, origins in recorded.items():
        index.setdefault(sha, []).extend(origins)
    return index, stats


# --------------------------------------------------------------------------
# plan
# --------------------------------------------------------------------------

ENSRICK_NAME_RE = re.compile(r"^Ensrick\b|- Ensrick(\s+\S+)?$")


def is_ensrick_row(row, records) -> bool:
    """Eligibility for a `distribution` field (#160 ruling 2026-09-02): the
    collection carries only our own work. A row qualifies when it has an
    Ensrick source-build record or its name starts with `Ensrick` / ends with
    `- Ensrick <ver>`. Everything else is a vendor row: a required download
    from its source, never collection payload, whatever its licence."""
    return bool(ENSRICK_NAME_RE.search(row["modName"])) or find_record(row, records) is not None


def build_plan(rows, instance: Path, patterns, records, by_id):
    plan = {"packaged": [], "skipped": [], "recipes": [], "gaps": [], "errors": [], "classificationErrors": []}
    for row in sorted((r for r in rows if r.get("distribution")), key=lambda r: r["modName"].lower()):
        name = row["modName"]
        distribution = row["distribution"]
        if not is_ensrick_row(row, records):
            plan["classificationErrors"].append({
                "modName": name, "distribution": distribution, "basis": row.get("distributionBasis"),
                "reason": ("not an Ensrick row: no Ensrick source-build record and the name neither starts with 'Ensrick' "
                           "nor ends with '- Ensrick <ver>'. An unmodified third-party release is a vendor row and a required "
                           "download from its source; drop the `distribution` fields from it"),
            })
            continue
        shared = str(row.get("sharedList") or "")
        if shared.lower().startswith("excluded"):
            plan["skipped"].append({"modName": name, "distribution": distribution,
                                    "reason": f"sharedList: {shared}"})
            continue
        if distribution == "local-only":
            plan["skipped"].append({"modName": name, "distribution": distribution,
                                    "reason": "local-only: cannot be reproduced by an installer; publication blocker",
                                    "basis": row.get("distributionBasis")})
            continue
        if distribution == "recipe":
            recipe, missing = normalize_recipe(row, records, by_id)
            if missing:
                plan["gaps"].append({"modName": name, "kind": recipe.get("kind"),
                                     "sourceBuildRecord": recipe.get("sourceBuildRecord"),
                                     "missing": missing, "basis": row.get("distributionBasis")})
            else:
                plan["recipes"].append(recipe)
            continue
        if distribution != "distributable":
            plan["skipped"].append({"modName": name, "distribution": distribution,
                                    "reason": f"unknown distribution class {distribution!r}"})
            continue

        mod_dir = instance / "mods" / name
        if not mod_dir.is_dir():
            plan["errors"].append(f"{name}: MO2 mod folder not found at {mod_dir}")
            continue
        record_path = find_record(row, records)
        record = records.get(record_path) if record_path else None
        entry = {
            "modName": name,
            "version": row.get("version"),
            "distribution": distribution,
            "sharedList": row.get("sharedList"),
            "plugins": row.get("plugins") or [],
            "enabled": row.get("enabled"),
            "installedUtc": row.get("installedUtc"),
            "basis": row.get("distributionBasis"),
            "sourceBuildRecord": record_path,
            "sourceScript": find_script(row),
            "sourceOverlay": find_tracked_overlay(row),
            "recipe": None,
            "vendorBytesAllowed": vendor_allow(row),
            "files": [],
            "excluded": [],
            "withheld": [],
            "allowedVendorFiles": [],
            "warnings": [],
            "fileCount": 0,
            "bytes": 0,
        }
        if entry["vendorBytesAllowed"] and not entry["vendorBytesAllowed"]["accepted"]:
            entry["warnings"].append(entry["vendorBytesAllowed"]["reason"])
        if row.get("recipe"):
            recipe, missing = normalize_recipe(row, records, by_id)
            entry["recipe"] = {"kind": recipe.get("kind"), "tool": recipe.get("tool"),
                               "steps": len(recipe.get("steps") or []),
                               "vendorDownloads": recipe.get("vendorDownloads"),
                               "complete": not missing, "missing": missing}
        if not entry["basis"]:
            entry["warnings"].append("ledger row has no distributionBasis text")
        if (record_path is None and entry["sourceScript"] is None and entry["sourceOverlay"] is None
                and not row.get("recipe")):
            entry["warnings"].append("no source-builds record, build script, tracked overlay or ledger recipe for this row")

        for rel, full, size in walk_files(mod_dir):
            reason = ignore_reason(name, rel, patterns, row.get("packagingExcludes"))
            if reason:
                entry["excluded"].append({"path": rel, "reason": reason})
                continue
            entry["files"].append({"path": rel, "sha256": sha256_path(full), "bytes": size, "_src": full})
        entry["fileCount"] = len(entry["files"])
        entry["bytes"] = sum(f["bytes"] for f in entry["files"])
        if not entry["files"]:
            entry["warnings"].append("no files left after exclusions")

        # Cross-check the installed bytes against what the source-build record says was built.
        if record is not None:
            by_rel = {f["path"].lower(): f["sha256"] for f in entry["files"]}
            expected = record_expected_files(record)
            for rel, sha in expected.items():
                actual = by_rel.get(rel)
                if actual is None:
                    entry["warnings"].append(f"record lists {rel} but the mod folder does not ship it")
                elif actual != sha:
                    entry["warnings"].append(f"{rel}: installed sha256 {actual[:12]}... differs from the record's {sha[:12]}...")
            plugins = [f for f in entry["files"] if Path(f["path"]).suffix.lower() in PLUGIN_EXT]
            single = record_single_output_hash(record)
            if single and len(plugins) == 1 and plugins[0]["sha256"] != single:
                entry["warnings"].append(f"{plugins[0]['path']}: installed sha256 {plugins[0]['sha256'][:12]}... "
                                         f"differs from the record's output {single[:12]}... (see the record's gap note)")
        plan["packaged"].append(entry)
    return plan


def apply_vendor_check(plan, index):
    violations = []
    for entry in plan["packaged"]:
        kept = []
        allow = entry.get("vendorBytesAllowed")
        allowed_paths = set(allow["files"]) if allow and allow["accepted"] else set()
        used = set()
        for file in entry["files"]:
            matches = index.get(file["sha256"])
            if matches and file["path"].lower() in allowed_paths:
                used.add(file["path"].lower())
                entry["allowedVendorFiles"].append({"path": file["path"], "sha256": file["sha256"], "bytes": file["bytes"],
                                                    "matches": sorted(set(matches)), "basis": allow["basis"]})
                kept.append(file)
            elif matches:
                violation = {"modName": entry["modName"], "path": file["path"], "sha256": file["sha256"],
                             "bytes": file["bytes"], "matches": sorted(set(matches))}
                entry["withheld"].append(violation)
                violations.append(violation)
            else:
                kept.append(file)
        for path in sorted(allowed_paths - used):
            entry["warnings"].append(f"vendorBytesAllowed lists {path} but no vendor-byte match was found for it "
                                     "(stale allow entry, or the file is not shipped)")
        entry["files"] = kept
        entry["fileCount"] = len(kept)
        entry["bytes"] = sum(f["bytes"] for f in kept)
    return violations


# --------------------------------------------------------------------------
# outputs
# --------------------------------------------------------------------------

def strip_private(entry):
    clean = dict(entry)
    clean["files"] = [{k: v for k, v in f.items() if not k.startswith("_")} for f in entry["files"]]
    return clean


def render_readme(manifest, recipes, plan, stats, violations):
    lines = []
    lines.append("# Ensrick patch collection and recipe set")
    lines.append("")
    lines.append(f"Generated {manifest['generatedUtc']} by `tools/package_ensrick.py` from "
                 f"`records/installed-mods.json` (sha256 `{manifest['ledger']['sha256'][:16]}...`) "
                 f"for issue #160. Collection version `{manifest['collectionVersion']}`.")
    lines.append("")
    lines.append("Every `Ensrick - *` overlay in the shared modlist falls into one of two sets. The rule "
                 "(`docs/PATCH_INTENTS.md`, \"Every fix is a shippable patch or a reproducible recipe\") is: "
                 "our own bytes ship; modified vendor assets never ship and are regenerated on the installing "
                 "machine from the user's own downloads.")
    lines.append("")
    lines.append("**Eligibility (ruling 2026-09-02, #160):** the collection carries only our own work. A ledger row may "
                 "carry a `distribution` field only if it is an Ensrick-made overlay, patch or rebuild: it has an Ensrick "
                 "source-build record, or its name starts with `Ensrick` or ends with `- Ensrick <ver>`. An unmodified "
                 "third-party release (GPL or not) is a vendor row and a required download from its own source, exactly "
                 "like any Nexus mod; the packager reports any other classified row as a classification error and does not "
                 "package it. The `vendorBytesAllowed` exception is only for permissive licences (MIT/BSD/Apache/CC-BY) or a "
                 "quoted upload permission and is never extended to GPL.")
    lines.append("")
    if plan.get("classificationErrors"):
        lines.append("### Classification errors (rows NOT packaged)")
        lines.append("")
        for item in plan["classificationErrors"]:
            lines.append(f"- **{item['modName']}** (`distribution: {item['distribution']}`): {item['reason']}")
        lines.append("")
    lines.append("## Set 1: `ensrick-patches/` (shipped bytes)")
    lines.append("")
    lines.append("Each folder is one Mod Organizer 2 mod; install it under the same name and place it where the "
                 "shared modlist puts it. `manifest.json` lists every file with its SHA-256, the ledger's "
                 "permission basis and the source-build record that produced it.")
    lines.append("")
    lines.append("| Mod | Version | Files | Bytes | Plugins | Source record |")
    lines.append("|---|---|---:|---:|---|---|")
    for mod in manifest["mods"]:
        source = (mod.get("sourceBuildRecord") or mod.get("sourceScript") or mod.get("sourceOverlay")
                  or (f"ledger recipe field ({mod['recipe'].get('kind')})" if mod.get("recipe") else "none recorded"))
        lines.append(f"| {mod['modName']} | {mod.get('version') or ''} | {mod['fileCount']} | {mod['bytes']:,} | "
                     f"{', '.join(mod['plugins']) or ''} | `{source}` |")
    lines.append("")
    lines.append("### Credits and permission basis")
    lines.append("")
    lines.append("Quoted from the ledger (`distributionBasis`); the vendor page terms it cites were read on the "
                 "date given inside each entry. Credit lines and licence files must travel with the folder.")
    lines.append("")
    for mod in manifest["mods"]:
        lines.append(f"- **{mod['modName']}**: {mod.get('basis') or '(no basis text recorded)'}")
    lines.append("")
    if any(m["allowedVendorFiles"] for m in manifest["mods"]):
        lines.append("### Vendor bytes shipped under licence (`vendorBytesAllowed`)")
        lines.append("")
        lines.append("These files are byte-identical to a vendor file and ship anyway because the ledger row lists them "
                     "under an explicit allow whose basis is a permissive licence or a quoted upload permission. "
                     "The licence notice travels in the same folder.")
        lines.append("")
        for mod in manifest["mods"]:
            for item in mod["allowedVendorFiles"]:
                lines.append(f"- {mod['modName']} / `{item['path']}` (matches " + "; ".join(f"`{m}`" for m in item["matches"])
                             + f"): {item['basis']}")
        lines.append("")
    if any(m["withheld"] for m in manifest["mods"]):
        lines.append("### Withheld files (vendor-byte violations)")
        lines.append("")
        lines.append("These files were NOT copied because their bytes match a vendor file. They stay listed so the "
                     "decision is visible; see `manifest.json` `withheld`.")
        lines.append("")
        for mod in manifest["mods"]:
            for item in mod["withheld"]:
                lines.append(f"- {mod['modName']} / `{item['path']}` matches: " + "; ".join(f"`{m}`" for m in item["matches"]))
        lines.append("")
    lines.append("## Set 2: `ensrick-recipes/recipes.json` (regenerate locally)")
    lines.append("")
    lines.append("Nothing in this set ships vendor bytes. For each recipe the installer downloads the vendor "
                 "archive listed below from Nexus with the user's own account, verifies the archive hash, "
                 "runs the pinned tool with the recorded command, and checks every output against the expected "
                 "SHA-256. A recipe is only listed here when tool pin, input hashes, command and output hashes "
                 "are all recorded; anything else is a gap (below), not a recipe.")
    lines.append("")
    downloads = {}
    for recipe in recipes["recipes"]:
        for ref in recipe.get("vendorDownloads") or []:
            key = (ref.get("nexusModId"), ref.get("fileId"))
            downloads.setdefault(key, {"ref": ref, "usedBy": []})["usedBy"].append(recipe["modName"])
    lines.append("### Vendor downloads required")
    lines.append("")
    if downloads:
        lines.append("| Nexus mod | File id | Archive | Archive SHA-256 | Used by |")
        lines.append("|---|---|---|---|---|")
        for key in sorted(downloads, key=lambda k: (k[0] or 0, k[1] or 0)):
            ref = downloads[key]["ref"]
            lines.append(f"| [{ref.get('ledgerRow') or ref.get('nexusModId')}]({ref.get('nexusUrl')}) | "
                         f"{ref.get('fileId') or ''} | `{ref.get('fileName') or 'see ledger'}` | "
                         f"`{ref.get('archiveSha256') or 'not recorded'}` | {', '.join(downloads[key]['usedBy'])} |")
    else:
        lines.append("(none: no complete recipe references a vendor download)")
    lines.append("")
    tools = {}
    for recipe in recipes["recipes"]:
        tool = recipe.get("tool") or {}
        pin = tool.get("commit") or tool.get("version") or tool.get("scriptSha256") or "n/a"
        tools.setdefault((tool.get("name"), pin), tool)
    lines.append("### Tools required")
    lines.append("")
    for (name, pin), tool in sorted(tools.items(), key=lambda kv: str(kv[0][0])):
        extra = tool.get("repository") or tool.get("wingetPackage") or ""
        sha = tool.get("sha256") or tool.get("binarySha256") or tool.get("scriptSha256") or ""
        lines.append(f"- `{name}` pin `{pin}`" + (f" ({extra})" if extra else "") + (f", sha256 `{sha}`" if sha else ""))
    lines.append("")
    lines.append("### Recipes")
    lines.append("")
    lines.append("| Mod | Kind | Tool | Steps |")
    lines.append("|---|---|---|---:|")
    for recipe in recipes["recipes"]:
        tool = recipe.get("tool") or {}
        lines.append(f"| {recipe['modName']} | {recipe.get('kind')} | {tool.get('name')} | {len(recipe.get('steps') or [])} |")
    lines.append("")
    lines.append("### Gaps (recipe rows NOT included)")
    lines.append("")
    if recipes["gaps"]:
        for gap in recipes["gaps"]:
            lines.append(f"- **{gap['modName']}** ({gap.get('kind') or 'no recipe field'}): " + "; ".join(gap["missing"]))
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Not in either set")
    lines.append("")
    for item in plan["skipped"]:
        lines.append(f"- {item['modName']} ({item['distribution']}): {item['reason']}")
    lines.append("")
    lines.append("## Vendor-byte verification")
    lines.append("")
    allowed_total = sum(len(m["allowedVendorFiles"]) for m in manifest["mods"])
    lines.append(f"Every shipped file was hashed and compared against {stats['modFoldersScanned']} other MO2 mod "
                 f"folders ({stats['looseFilesHashed']:,} size-matched files hashed of {stats['looseFilesSeen']:,} seen), "
                 f"{stats['downloadFoldersScanned']} extracted download folders, {stats['zipArchivesScanned']} zip "
                 f"archives ({stats['zipEntriesHashed']:,} size-matched entries hashed of {stats['zipEntriesSeen']:,}) "
                 f"and {stats['recordedInputHashes']:,} recorded vendor input hashes. Violations: {len(violations)}; "
                 f"vendor-identical files shipped under an explicit licence allow: {allowed_total}.")
    if stats["unscannedArchives"]:
        lines.append("")
        lines.append(f"{len(stats['unscannedArchives'])} 7z/rar download archives could not be read with the "
                     "standard library and were not scanned; their MO2-extracted mod folders were.")
    lines.append("")
    lines.append("Nothing under `dist/` is committed to git.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(dist_root: Path, plan, manifest, recipes, readme_text):
    patches = dist_root / "ensrick-patches"
    recipes_dir = dist_root / "ensrick-recipes"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for directory in (patches, recipes_dir):
        if directory.exists():
            backup = directory.with_name(f"{directory.name}.bak.v{stamp}")
            directory.rename(backup)
            print(f"previous output kept as {backup}")
    patches.mkdir(parents=True)
    recipes_dir.mkdir(parents=True)
    copy_errors = []
    for entry in plan["packaged"]:
        for file in entry["files"]:
            dest = patches / entry["modName"] / file["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file["_src"], dest)
            if sha256_path(dest) != file["sha256"]:
                copy_errors.append(f"{entry['modName']}/{file['path']}: copy hash mismatch")
        if not entry["files"]:
            (patches / entry["modName"]).mkdir(parents=True, exist_ok=True)
    with open(patches / "manifest.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(recipes_dir / "recipes.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(recipes, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(dist_root / "README.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme_text)
    return copy_errors


def print_summary(plan, manifest, recipes, stats, violations, dry_run, dist_root):
    total_files = sum(m["fileCount"] for m in manifest["mods"])
    total_bytes = sum(m["bytes"] for m in manifest["mods"])
    print()
    print("=== Ensrick patch collection: " + ("DRY RUN (nothing written)" if dry_run else f"written under {dist_root}"))
    print(f"collection version : {manifest['collectionVersion']}")
    print(f"distributable mods : {len(manifest['mods'])} packaged, {total_files} files, {total_bytes:,} bytes")
    for mod in manifest["mods"]:
        flags = []
        if mod["excluded"]:
            flags.append(f"{len(mod['excluded'])} excluded")
        if mod["withheld"]:
            flags.append(f"{len(mod['withheld'])} WITHHELD")
        if mod["allowedVendorFiles"]:
            flags.append(f"{len(mod['allowedVendorFiles'])} vendor-identical allowed")
        if mod["warnings"]:
            flags.append(f"{len(mod['warnings'])} warning(s)")
        print(f"  - {mod['modName']}: {mod['fileCount']} files, {mod['bytes']:,} B" + (f" [{'; '.join(flags)}]" if flags else ""))
        for item in mod["excluded"]:
            print(f"      excluded {item['path']} ({item['reason']})")
        for item in mod["withheld"]:
            print(f"      WITHHELD {item['path']} matches " + "; ".join(item["matches"]))
        for item in mod["allowedVendorFiles"]:
            print(f"      allowed  {item['path']} (vendorBytesAllowed) matches " + "; ".join(item["matches"]))
        for warning in mod["warnings"]:
            print(f"      warning: {warning}")
    print(f"skipped rows       : {len(plan['skipped'])}")
    for item in plan["skipped"]:
        print(f"  - {item['modName']} ({item['distribution']}): {item['reason']}")
    print(f"recipes            : {len(recipes['recipes'])} complete")
    for recipe in recipes["recipes"]:
        print(f"  - {recipe['modName']}: {recipe.get('kind')}, {len(recipe.get('steps') or [])} step(s)")
    print(f"recipe gaps        : {len(recipes['gaps'])}")
    for gap in recipes["gaps"]:
        print(f"  - {gap['modName']} ({gap.get('kind') or 'no recipe field'}): " + "; ".join(gap["missing"]))
    print(f"vendor-byte check  : {len(violations)} violation(s); scanned {stats['modFoldersScanned']} mod folders "
          f"({stats['looseFilesHashed']:,}/{stats['looseFilesSeen']:,} files hashed), {stats['downloadFoldersScanned']} "
          f"download folders, {stats['zipArchivesScanned']} zips ({stats['zipEntriesHashed']:,}/{stats['zipEntriesSeen']:,} "
          f"entries hashed), {stats['recordedInputHashes']:,} recorded input hashes; "
          f"{len(stats['unscannedArchives'])} 7z/rar archives not scannable")
    for violation in violations:
        print(f"  ! {violation['modName']} / {violation['path']} == " + "; ".join(violation["matches"]))
    print(f"classification errs: {len(plan['classificationErrors'])}")
    for item in plan["classificationErrors"]:
        print(f"  ! {item['modName']} (distribution: {item['distribution']}): {item['reason']}")
    if plan["errors"]:
        print(f"errors             : {len(plan['errors'])}")
        for error in plan["errors"]:
            print(f"  ! {error}")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="plan and verify only; write nothing")
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST, help="output root (default: <repo>/dist)")
    parser.add_argument("--instance", type=Path, default=None,
                        help="MO2 instance root (default: the ledger's `instance` field)")
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--no-archive-scan", action="store_true",
                        help="skip hashing zip entries under downloads/ (faster; mod folders still scanned)")
    parser.add_argument("--collection-version", default=None,
                        help="label for this build (default: <UTC date>+<ledger sha256 prefix>)")
    parser.add_argument("--json", action="store_true", help="also print the manifest/recipes summary as JSON")
    args = parser.parse_args(argv)

    try:
        ledger = load_json(args.ledger)
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read ledger {args.ledger}: {exc}", file=sys.stderr)
        return 1
    rows = ledger.get("mods") if isinstance(ledger, dict) else ledger
    if not isinstance(rows, list):
        print("ERROR: ledger has no `mods` list", file=sys.stderr)
        return 1
    instance = args.instance
    if instance is None and isinstance(ledger, dict) and ledger.get("instance"):
        instance = Path(ledger["instance"])
    if instance is None or not (instance / "mods").is_dir():
        print(f"ERROR: MO2 instance mods folder not found under {instance}", file=sys.stderr)
        return 1
    ledger_sha = sha256_path(args.ledger)
    patterns = load_ignore_patterns(PACKAGING_IGNORE)
    records = load_source_build_records()
    by_id = vendor_rows_by_mod_id(rows)

    print(f"ledger   : {args.ledger} ({len(rows)} rows, {sum(1 for r in rows if r.get('distribution'))} classified)")
    print(f"instance : {instance}")
    print(f"ignore   : {PACKAGING_IGNORE} ({len(patterns)} patterns)")
    print(f"records  : {len(records)} source-build records")

    plan = build_plan(rows, instance, patterns, records, by_id)
    if plan["errors"]:
        for error in plan["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    packaged_names = {entry["modName"] for entry in plan["packaged"]}
    sizes = {f["bytes"] for entry in plan["packaged"] for f in entry["files"]}
    print(f"verify   : hashing vendor bytes against {sum(len(e['files']) for e in plan['packaged'])} candidate files "
          f"({len(sizes)} distinct sizes) ...")
    index, stats = build_vendor_index(instance, packaged_names, sizes, not args.no_archive_scan, rows, records)
    violations = apply_vendor_check(plan, index)

    generated = utc_now()
    version = args.collection_version or f"{generated[:10]}+{ledger_sha[:12]}"
    manifest = {
        "schemaVersion": 1,
        "collection": "Ensrick patch collection",
        "collectionVersion": version,
        "generatedUtc": generated,
        "issue": "https://github.com/Ensrick/skyrim-mod-assistant/issues/160",
        "ledger": {"path": args.ledger.relative_to(REPO).as_posix() if args.ledger.is_relative_to(REPO) else str(args.ledger),
                   "sha256": ledger_sha, "instance": str(instance),
                   "profile": ledger.get("profile") if isinstance(ledger, dict) else None},
        "packagingIgnore": {"path": ".packagingignore", "patterns": patterns,
                            "sha256": sha256_path(PACKAGING_IGNORE) if PACKAGING_IGNORE.exists() else None},
        "counts": {
            "distributableRows": len(plan["packaged"]) + sum(1 for s in plan["skipped"] if s["distribution"] == "distributable"),
            "packagedMods": len(plan["packaged"]),
            "packagedFiles": sum(e["fileCount"] for e in plan["packaged"]),
            "packagedBytes": sum(e["bytes"] for e in plan["packaged"]),
            "excludedFiles": sum(len(e["excluded"]) for e in plan["packaged"]),
            "withheldFiles": len(violations),
            "allowedVendorFiles": sum(len(e["allowedVendorFiles"]) for e in plan["packaged"]),
            "skippedRows": len(plan["skipped"]),
            "classificationErrors": len(plan["classificationErrors"]),
        },
        "eligibility": ("ruling 2026-09-02 (#160): only Ensrick-made rows (Ensrick source-build record, or name starting with "
                        "'Ensrick' / ending with '- Ensrick <ver>') may carry a distribution field; vendor releases are downloads"),
        "vendorByteCheck": {"stats": stats, "violations": violations},
        "mods": [strip_private(entry) for entry in plan["packaged"]],
        "skipped": plan["skipped"],
        "classificationErrors": plan["classificationErrors"],
    }
    recipes = {
        "schemaVersion": 1,
        "collection": "Ensrick recipe set",
        "collectionVersion": version,
        "generatedUtc": generated,
        "issue": manifest["issue"],
        "ledger": manifest["ledger"],
        "counts": {"recipeRows": len(plan["recipes"]) + len(plan["gaps"]),
                   "recipes": len(plan["recipes"]), "gaps": len(plan["gaps"])},
        "recipes": plan["recipes"],
        "gaps": plan["gaps"],
    }
    readme_text = render_readme(manifest, recipes, plan, stats, violations)

    print_summary(plan, manifest, recipes, stats, violations, args.dry_run, args.dist)
    if args.json:
        print(json.dumps({"counts": manifest["counts"], "recipeCounts": recipes["counts"],
                          "gaps": recipes["gaps"], "violations": violations}, indent=2, ensure_ascii=False))

    if not args.dry_run:
        copy_errors = write_outputs(args.dist, plan, manifest, recipes, readme_text)
        if copy_errors:
            for error in copy_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"\nwrote {args.dist / 'ensrick-patches' / 'manifest.json'}")
        print(f"wrote {args.dist / 'ensrick-recipes' / 'recipes.json'}")
        print(f"wrote {args.dist / 'README.md'}")
    return 2 if (violations or plan["classificationErrors"]) else 0


if __name__ == "__main__":
    sys.exit(main())
