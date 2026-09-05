#!/usr/bin/env python3
"""Read Skyrim SE attack HKX timing without launching the game.

This tool deserializes animation clips and behavior graphs with the local
HKX2-Enhanced library.  It reports source clip durations, clip-generator
settings, and named behavior-event timestamps.  It is deliberately not a DPS
calculator: a ``HitFrame`` label does not prove that an attack hit anything,
and behavior-local timestamps do not establish repeat cadence.

Typical use after extracting ``Skyrim - Animations.bsa`` to a scratch folder::

    py -3 audit/weapon_timing.py \
      --character-root work/weapon-timing-static/meshes/actors/character \
      --rate onehand=1.0 --rate greatsword_current=1.2 \
      --rate longsword_proposed=1.5 > timing.json

The command is read-only.  Redirection, if requested by the caller, is handled
by the shell; this program never writes an input, profile, game, or output file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PureWindowsPath
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CHARACTER_ROOT = (
    REPO
    / "work"
    / "weapon-timing-static-20260905"
    / "meshes"
    / "actors"
    / "character"
)
DEFAULT_HKX2 = (
    REPO.parent
    / "pandora-behaviour-engine"
    / "Pandora API"
    / "HKX2-Enhanced-Library"
    / "HKX2"
    / "bin"
    / "Release"
    / "net10.0"
    / "HKX2E.dll"
)

# Ordinary standing normal attacks and the vanilla directional power attacks.
# Movement/sneak/sprint/dual-wield/killmove clips are excluded unless --all is
# passed, keeping the default evidence set relevant and reviewable.
REPRESENTATIVE = re.compile(
    r"^(?:1hm|2hm|2hw)_attack(?:"
    r"right(?:intro)?|left(?:intro)?|power(?:fwd|forward|bwd|left|right)?"
    r")\.hkx$",
    re.IGNORECASE,
)
ALL_ATTACKS = re.compile(r"^(?:1hm|2hm|2hw).*attack.*\.hkx$", re.IGNORECASE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_rate(value: str) -> tuple[str, float]:
    try:
        label, raw = value.split("=", 1)
        rate = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("rate must be LABEL=POSITIVE_NUMBER") from exc
    if not label.strip() or not math.isfinite(rate) or rate <= 0:
        raise argparse.ArgumentTypeError("rate must be LABEL=POSITIVE_NUMBER")
    return label.strip(), rate


def rates_from_pairs(pairs: list[tuple[str, float]]) -> dict[str, float]:
    rates: dict[str, float] = {}
    for label, rate in pairs:
        if label in rates:
            raise ValueError(f"duplicate rate label: {label}")
        rates[label] = rate
    return rates


def dotnet_property(obj: Any, name: str) -> Any:
    prop = obj.GetType().GetProperty(name)
    if prop is None:
        raise AttributeError(f"{obj.GetType().FullName} has no property {name}")
    return prop.GetValue(obj)


def direct_params(node: ET.Element) -> dict[str, str]:
    return {
        param.get("name", ""): (param.text or "").strip()
        for param in node.findall("./hkparam")
    }


def load_hkx_runtime(dll: Path) -> tuple[Any, Any, Any]:
    if not dll.is_file():
        raise FileNotFoundError(f"HKX2 library is missing: {dll}")
    from pythonnet import load

    load("coreclr")
    import clr

    clr.AddReference(str(dll))
    import HKX2E
    from System.IO import File, MemoryStream

    return HKX2E, File, MemoryStream


def deserialize(path: Path, hkx: Any, dotnet_file: Any) -> Any:
    stream = dotnet_file.OpenRead(str(path))
    try:
        return hkx.PackFileDeserializer().Deserialize(hkx.BinaryReaderEx(stream))
    finally:
        stream.Dispose()


def animation_record(path: Path, hkx: Any, dotnet_file: Any,
                     rates: dict[str, float]) -> dict[str, Any]:
    root = deserialize(path, hkx, dotnet_file)
    variants = dotnet_property(root, "namedVariants")
    animations: list[dict[str, Any]] = []
    for named_variant in variants:
        variant = dotnet_property(named_variant, "variant")
        if not str(variant.GetType().FullName).endswith("hkaAnimationContainer"):
            continue
        for animation in dotnet_property(variant, "animations"):
            duration = float(dotnet_property(animation, "duration"))
            annotations: list[dict[str, Any]] = []
            for track in dotnet_property(animation, "annotationTracks"):
                track_name = str(dotnet_property(track, "trackName"))
                for annotation in dotnet_property(track, "annotations"):
                    annotations.append(
                        {
                            "track": track_name,
                            "time_seconds": float(dotnet_property(annotation, "time")),
                            "text": str(dotnet_property(annotation, "text")),
                        }
                    )
            animations.append(
                {
                    "class": str(animation.GetType().FullName),
                    "source_duration_seconds": duration,
                    "projected_full_clip_seconds": {
                        label: duration / rate for label, rate in rates.items()
                    },
                    "embedded_annotations": annotations,
                }
            )
    if not animations:
        raise ValueError(f"no hkaAnimationContainer animations found in {path}")
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "animations": animations,
    }


def behavior_xml(path: Path, hkx: Any, dotnet_file: Any,
                 memory_stream: Any) -> ET.Element:
    root = deserialize(path, hkx, dotnet_file)
    stream = memory_stream()
    try:
        hkx.HavokXmlSerializer().Serialize(root, hkx.HKXHeader.SkyrimSE(), stream)
        return ET.fromstring(bytes(stream.ToArray()))
    finally:
        stream.Dispose()


def event_names(xml_root: ET.Element, objects: dict[str, ET.Element]) -> list[str]:
    """Resolve the event table actually referenced by the behavior graph.

    Clip-generator event IDs are graph-local. If a pack contains graphs that
    reference distinct string tables, this analyzer cannot safely assign a
    clip to one of them and therefore fails closed instead of guessing.
    """
    data_refs = {
        direct_params(graph).get("data", "")
        for graph in xml_root.findall('.//hkobject[@class="hkbBehaviorGraph"]')
    }
    data_refs.discard("")
    data_refs.discard("null")
    if not data_refs:
        raise ValueError("behavior pack has no referenced hkbBehaviorGraphData")

    string_refs: set[str] = set()
    for ref in data_refs:
        graph_data = objects.get(ref)
        if graph_data is None or graph_data.get("class") != "hkbBehaviorGraphData":
            raise ValueError(f"behavior graph data reference does not resolve: {ref}")
        string_ref = direct_params(graph_data).get("stringData", "")
        if not string_ref or string_ref == "null":
            raise ValueError(f"behavior graph data has no stringData reference: {ref}")
        string_refs.add(string_ref)
    if len(string_refs) != 1:
        raise ValueError(
            "behavior pack references multiple event string tables; "
            "clip ownership is ambiguous"
        )

    string_ref = next(iter(string_refs))
    string_data = objects.get(string_ref)
    if string_data is None or string_data.get("class") != "hkbBehaviorGraphStringData":
        raise ValueError(f"behavior string-data reference does not resolve: {string_ref}")
    event_param = next(
        (param for param in string_data.findall("./hkparam")
         if param.get("name") == "eventNames"),
        None,
    )
    if event_param is None:
        raise ValueError(f"behavior string data has no eventNames: {string_ref}")
    return [(child.text or "") for child in list(event_param)]


def behavior_record(path: Path, selector: re.Pattern[str], hkx: Any,
                    dotnet_file: Any, memory_stream: Any,
                    rates: dict[str, float]) -> dict[str, Any]:
    xml_root = behavior_xml(path, hkx, dotnet_file, memory_stream)
    objects = {
        obj.get("name", ""): obj
        for obj in xml_root.findall(".//hkobject")
        if obj.get("name")
    }
    names = event_names(xml_root, objects)
    clips: list[dict[str, Any]] = []
    for obj in xml_root.findall('.//hkobject[@class="hkbClipGenerator"]'):
        params = direct_params(obj)
        animation_name = params.get("animationName", "")
        base_name = PureWindowsPath(animation_name).name
        if not selector.match(base_name):
            continue
        playback = float(params.get("playbackSpeed", "1"))
        trigger_rows: list[dict[str, Any]] = []
        trigger_object = objects.get(params.get("triggers", ""))
        if trigger_object is not None:
            trigger_param = next(
                (p for p in trigger_object.findall("./hkparam")
                 if p.get("name") == "triggers"),
                None,
            )
            for trigger in list(trigger_param) if trigger_param is not None else []:
                trigger_params = direct_params(trigger)
                event_param = next(
                    (p for p in trigger.findall("./hkparam")
                     if p.get("name") == "event"),
                    None,
                )
                event_obj = event_param.find("./hkobject") if event_param is not None else None
                event_id = None
                if event_obj is not None:
                    raw_id = direct_params(event_obj).get("id", "")
                    event_id = int(raw_id) if raw_id else None
                local_time = float(trigger_params.get("localTime", "0"))
                relative_to_end = (
                    trigger_params.get("relativeToEndOfClip", "false").lower() == "true"
                )
                event_name = (
                    names[event_id]
                    if event_id is not None and 0 <= event_id < len(names)
                    else None
                )
                trigger_rows.append(
                    {
                        "event_id": event_id,
                        "event_name": event_name,
                        "source_local_time_seconds": local_time,
                        "relative_to_end_of_clip": relative_to_end,
                        "acyclic": trigger_params.get("acyclic", "false").lower() == "true",
                        "is_annotation": (
                            trigger_params.get("isAnnotation", "false").lower() == "true"
                        ),
                        # This is only a scalar projection of the local event
                        # time.  It intentionally does not combine graph nodes,
                        # transition effects, crop/start offsets, or input delay.
                        "projected_local_seconds": (
                            {}
                            if relative_to_end
                            else {
                                label: local_time / (rate * playback)
                                for label, rate in rates.items()
                            }
                        ),
                    }
                )
        clips.append(
            {
                "object_id": obj.get("name"),
                "node_name": params.get("name"),
                "animation_name": animation_name,
                "start_time_seconds": float(params.get("startTime", "0")),
                "crop_start_seconds": float(params.get("cropStartAmountLocalTime", "0")),
                "crop_end_seconds": float(params.get("cropEndAmountLocalTime", "0")),
                "playback_speed": playback,
                "enforced_duration_seconds": float(params.get("enforcedDuration", "0")),
                "mode": params.get("mode"),
                "triggers": trigger_rows,
            }
        )
    clips.sort(key=lambda row: (row["animation_name"].lower(), row["node_name"] or ""))
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "event_name_count": len(names),
        "clip_generators": clips,
    }


def selected_hkx(directory: Path, selector: re.Pattern[str]) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file() and selector.match(path.name)
        ),
        key=lambda path: path.name.lower(),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--character-root",
        type=Path,
        default=DEFAULT_CHARACTER_ROOT,
        help="extracted meshes/actors/character directory",
    )
    parser.add_argument(
        "--hkx2", type=Path, default=DEFAULT_HKX2, help="local HKX2E.dll path"
    )
    parser.add_argument(
        "--rate",
        action="append",
        type=parse_rate,
        default=[],
        metavar="LABEL=VALUE",
        help=(
            "project source-local values through an externally established effective "
            "animation-rate scalar; repeat for multiple scenarios"
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include movement, sneak, sprint, and other 1HM/2HM/2HW attack clips",
    )
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)

    character_root = args.character_root.resolve()
    if not character_root.is_dir():
        parser.error(f"character root is missing: {character_root}")
    try:
        rates = rates_from_pairs(args.rate)
    except ValueError as exc:
        parser.error(str(exc))
    selector = ALL_ATTACKS if args.all else REPRESENTATIVE
    hkx, dotnet_file, memory_stream = load_hkx_runtime(args.hkx2.resolve())

    scopes = {
        "third_person": character_root / "animations",
        "first_person": character_root / "_1stperson" / "animations",
    }
    behaviors = {
        "third_person": character_root / "behaviors" / "1hm_behavior.hkx",
        "first_person": character_root / "_1stperson" / "behaviors" / "1hm_behavior.hkx",
    }

    result: dict[str, Any] = {
        "schema": "skyrim-static-weapon-timing-v1",
        "character_root": str(character_root),
        "hkx2_library": {
            "path": str(args.hkx2.resolve()),
            "sha256": sha256(args.hkx2.resolve()),
        },
        "rate_scalars": rates,
        "interpretation_limits": [
            "A WEAP Speed value and an effective animation-rate scalar are not attacks per second.",
            "HitFrame and weaponSwing are behavior event names, not proof of a successful impact or damage.",
            "Projected values scale source-local timestamps only; they are not measured end-to-end cadence.",
            "Graph state selection, transitions, input buffering, recovery, animation replacement, perks, stamina, and actor state require runtime validation.",
        ],
        "animation_scopes": {},
        "behavior_graphs": {},
    }
    for label, directory in scopes.items():
        result["animation_scopes"][label] = {
            "directory": str(directory.resolve()),
            "clips": [
                animation_record(path, hkx, dotnet_file, rates)
                for path in selected_hkx(directory, selector)
            ],
        }
    for label, path in behaviors.items():
        if path.is_file():
            result["behavior_graphs"][label] = behavior_record(
                path, selector, hkx, dotnet_file, memory_stream, rates
            )
        else:
            result["behavior_graphs"][label] = {"path": str(path), "missing": True}

    json.dump(
        result,
        sys.stdout,
        ensure_ascii=False,
        indent=None if args.compact else 2,
        sort_keys=False,
        allow_nan=False,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
