from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

STAGE_SUFFIXES = {"vsh", "fsh", "gsh", "tcs", "tes", "csh"}
PAIR_REQUIRED = {"vsh", "fsh"}

# Program families documented in docs/IRIS-CAPABILITY-MATRIX.md and currently
# relevant to Focal. Numeric suffixes 1..99 are accepted for repeatable passes.
EXACT_PROGRAMS = {
    "setup",
    "begin",
    "shadow",
    "shadowcomp",
    "prepare",
    "deferred",
    "composite",
    "final",
}
GBUFFER_PROGRAMS = {
    "gbuffers_basic",
    "gbuffers_line",
    "gbuffers_textured",
    "gbuffers_textured_lit",
    "gbuffers_skybasic",
    "gbuffers_skytextured",
    "gbuffers_clouds",
    "gbuffers_terrain",
    "gbuffers_terrain_solid",
    "gbuffers_terrain_cutout",
    "gbuffers_terrain_translucent",
    "gbuffers_water",
    "gbuffers_entities",
    "gbuffers_entities_translucent",
    "gbuffers_block",
    "gbuffers_hand",
    "gbuffers_hand_water",
    "gbuffers_weather",
    "gbuffers_particles",
    "gbuffers_beaconbeam",
    "gbuffers_damagedblock",
    "gbuffers_spidereyes",
    "gbuffers_armor_glint",
}
REPEATABLE_PREFIXES = {"shadowcomp", "prepare", "deferred", "composite"}


@dataclass(frozen=True)
class ProgramRecord:
    program: str
    stages: tuple[str, ...]
    files: tuple[str, ...]
    recognized: bool
    pair_complete: bool


def _strip_numeric_suffix(program: str) -> tuple[str, int | None]:
    match = re.fullmatch(r"(.+?)(\d{1,2})", program)
    if not match:
        return program, None
    return match.group(1), int(match.group(2))


def is_recognized_program(program: str) -> bool:
    if program in EXACT_PROGRAMS or program in GBUFFER_PROGRAMS:
        return True
    base, suffix = _strip_numeric_suffix(program)
    return base in REPEATABLE_PREFIXES and suffix is not None and 1 <= suffix <= 99


def inventory(shader_dir: Path) -> list[ProgramRecord]:
    grouped: dict[str, list[Path]] = {}
    for path in sorted(shader_dir.iterdir() if shader_dir.is_dir() else []):
        if not path.is_file() or path.suffix.lstrip(".") not in STAGE_SUFFIXES:
            continue
        grouped.setdefault(path.stem, []).append(path)

    records: list[ProgramRecord] = []
    for program, paths in sorted(grouped.items()):
        stages = tuple(sorted(path.suffix.lstrip(".") for path in paths))
        records.append(
            ProgramRecord(
                program=program,
                stages=stages,
                files=tuple(path.name for path in paths),
                recognized=is_recognized_program(program),
                pair_complete=not ({"vsh", "fsh"} & set(stages))
                or PAIR_REQUIRED.issubset(stages),
            )
        )
    return records


def validation_errors(records: Iterable[ProgramRecord]) -> list[str]:
    errors: list[str] = []
    for record in records:
        if not record.recognized:
            errors.append(f"unrecognized program: {record.program}")
        if not record.pair_complete:
            errors.append(
                f"incomplete vertex/fragment pair: {record.program} ({', '.join(record.stages)})"
            )
    return errors


def render_payload(records: list[ProgramRecord]) -> dict[str, object]:
    errors = validation_errors(records)
    return {
        "schemaVersion": 1,
        "programCount": len(records),
        "stageFileCount": sum(len(record.files) for record in records),
        "valid": not errors,
        "errors": errors,
        "programs": [asdict(record) for record in records],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory and validate Iris shader program stages.")
    parser.add_argument("--shader-dir", type=Path, default=Path("shaders"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = render_payload(inventory(args.shader_dir))
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if args.check and not payload["valid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
