#!/usr/bin/env python3
"""Stable command-line contract for Focal's standalone OpenGL harness.

This module intentionally implements only GLCLI-001. Runtime OpenGL context,
compile, render and suite execution are introduced by later roadmap units.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

VERSION = "0.1.0"
SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONTEXT_UNAVAILABLE = 3
EXIT_COMPILE_LINK = 4
EXIT_OPENGL_EXECUTION = 5
EXIT_INVARIANT = 6
EXIT_TIMEOUT_OR_CONTEXT_LOSS = 7
EXIT_UNSUPPORTED = 8

EXIT_CODES = {
    EXIT_OK: "all required checks passed",
    EXIT_USAGE: "invalid usage or configuration",
    EXIT_CONTEXT_UNAVAILABLE: "OpenGL context unavailable",
    EXIT_COMPILE_LINK: "shader compilation or link failure",
    EXIT_OPENGL_EXECUTION: "OpenGL, framebuffer or execution failure",
    EXIT_INVARIANT: "output invariant failure",
    EXIT_TIMEOUT_OR_CONTEXT_LOSS: "timeout, worker termination or context loss",
    EXIT_UNSUPPORTED: "required capability unsupported without accepted fallback",
}

PROFILES = ("SAFE", "BALANCED", "HIGH", "ULTRA")
BACKENDS = ("auto", "egl", "glfw", "wgl", "cgl")
GL_PROFILES = ("core", "compatibility")
SOURCE_MODES = ("source", "preprocessed", "iris-patched")


@dataclass(frozen=True)
class Result:
    schemaVersion: int
    harnessVersion: str
    command: str
    outcome: str
    exitCode: int
    evidenceLevel: str
    message: str
    artifacts: str | None


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _size(value: str) -> str:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("expected WIDTHxHEIGHT") from exc
    if width <= 0 or height <= 0 or width > 8192 or height > 8192:
        raise argparse.ArgumentTypeError("dimensions must be between 1 and 8192")
    return f"{width}x{height}"


def _gl_version(value: str) -> str:
    parts = value.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError("expected MAJOR.MINOR")
    return value


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pack", type=Path, default=Path("."))
    parser.add_argument("--program")
    parser.add_argument("--fixture")
    parser.add_argument("--profile", choices=PROFILES, default="SAFE")
    parser.add_argument("--dimension", default="overworld")
    parser.add_argument("--backend", choices=BACKENDS, default="auto")
    parser.add_argument("--gl-version", type=_gl_version, default="3.3")
    parser.add_argument("--gl-profile", choices=GL_PROFILES, default="core")
    parser.add_argument("--size", type=_size, default="256x256")
    parser.add_argument("--frames", type=_positive_int, default=1)
    parser.add_argument("--timeout", type=_positive_float, default=30.0)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--source-mode", choices=SOURCE_MODES, default="source")
    parser.add_argument("--json", action="store_true", dest="json_output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="focal-gl",
        description="Standalone OpenGL validation harness for Focal shaders.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, description in (
        ("probe", "Create a context and report capabilities."),
        ("compile", "Compile and link a selected shader program."),
        ("render", "Render a deterministic fixture and read it back."),
        ("suite", "Run a declared fixture matrix."),
    ):
        child = subparsers.add_parser(command, help=description, description=description)
        _add_common_options(child)
    return parser


def _not_implemented_result(args: argparse.Namespace) -> Result:
    return Result(
        schemaVersion=SCHEMA_VERSION,
        harnessVersion=VERSION,
        command=args.command,
        outcome="UNSUPPORTED",
        exitCode=EXIT_CONTEXT_UNAVAILABLE,
        evidenceLevel="STATIC",
        message=(
            "GLCLI-001 command contract is available; real OpenGL execution "
            "requires GLCLI-002 and subsequent runtime units."
        ),
        artifacts=str(args.artifacts) if args.artifacts else None,
    )


def emit(result: Result, json_output: bool) -> None:
    if json_output:
        print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
        return
    print(f"focal-gl {result.harnessVersion}: {result.command}: {result.outcome}")
    print(result.message)
    print(f"evidence={result.evidenceLevel} exit={result.exitCode}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = _not_implemented_result(args)
    emit(result, args.json_output)
    return result.exitCode


if __name__ == "__main__":
    sys.exit(main())
