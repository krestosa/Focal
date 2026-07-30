"""Backend and source dispatch for the public ``focal-gl`` executable.

The core CLI module retains the EGL implementation. This adapter adds the
controlled hidden GLFW route, deterministic EGL-then-GLFW fallback, and the
GLCLI-003 source-preparation boundary used by ``compile`` before GLCLI-004 adds
real OpenGL stage compilation and program linking.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from tools.focal_gl import (
    EXIT_CONTEXT_UNAVAILABLE,
    EXIT_OK,
    EXIT_UNSUPPORTED,
    EXIT_USAGE,
    SCHEMA_VERSION,
    VERSION,
    ContextUnavailable,
    Result,
    _probe_result,
    build_parser,
    emit,
)
from tools.focal_gl_sources import SourceResolutionError, prepare_program
from tools.glfw_context import GlfwContextUnavailable, create_hidden_glfw_context
from tools.glfw_probe import GlfwProbeUnavailable, query_current_glfw_context


def _glfw_probe_result(args) -> Result:
    try:
        with create_hidden_glfw_context(
            args.gl_version,
            args.gl_profile,
            args.size,
        ) as context_handle:
            context = query_current_glfw_context(
                context_handle,
                args.gl_version,
                args.gl_profile,
            )
    except (GlfwContextUnavailable, GlfwProbeUnavailable, ContextUnavailable, OSError) as exc:
        return Result(
            SCHEMA_VERSION,
            VERSION,
            args.command,
            "UNSUPPORTED",
            EXIT_CONTEXT_UNAVAILABLE,
            "STATIC",
            str(exc),
            str(args.artifacts) if args.artifacts else None,
        )

    return Result(
        SCHEMA_VERSION,
        VERSION,
        args.command,
        "PASS",
        EXIT_OK,
        "STATIC",
        "real hidden GLFW OpenGL context created and queried; shader compile/link evidence remains pending",
        str(args.artifacts) if args.artifacts else None,
        context,
    )


def _dispatch_probe(args) -> Result:
    if args.backend == "glfw":
        return _glfw_probe_result(args)
    if args.backend == "egl":
        return _probe_result(args)
    if args.backend == "auto":
        egl_result = _probe_result(args)
        if egl_result.exitCode == EXIT_OK:
            return egl_result
        glfw_result = _glfw_probe_result(args)
        if glfw_result.exitCode == EXIT_OK:
            return glfw_result
        return Result(
            SCHEMA_VERSION,
            VERSION,
            args.command,
            "UNSUPPORTED",
            EXIT_CONTEXT_UNAVAILABLE,
            "STATIC",
            f"EGL unavailable: {egl_result.message}; GLFW unavailable: {glfw_result.message}",
            str(args.artifacts) if args.artifacts else None,
        )
    return _probe_result(args)


def _macro_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]", "_", value.upper()).strip("_")
    return token or "DEFAULT"


def _compile_source_result(args) -> Result:
    if not args.program:
        return Result(
            SCHEMA_VERSION,
            VERSION,
            args.command,
            "INVALID",
            EXIT_USAGE,
            "STATIC",
            "compile requires --program",
            str(args.artifacts) if args.artifacts else None,
        )

    source_root: Path | None = None
    if args.source_mode == "iris-patched":
        source_root = (
            args.artifacts / "iris-patched"
            if args.artifacts
            else args.pack / ".focal-gl" / "iris-patched"
        )
    define_values: tuple[str, ...] = ()
    if args.source_mode == "preprocessed":
        define_values = (
            f"FOCAL_PROFILE_{_macro_token(args.profile)}=1",
            f"FOCAL_DIMENSION_{_macro_token(args.dimension)}=1",
        )

    try:
        prepared = prepare_program(
            pack=args.pack,
            source_root=source_root,
            program=args.program,
            source_mode=args.source_mode,
            define_values=define_values,
        )
    except SourceResolutionError as exc:
        return Result(
            SCHEMA_VERSION,
            VERSION,
            args.command,
            "INVALID",
            EXIT_USAGE,
            "STATIC",
            str(exc),
            str(args.artifacts) if args.artifacts else None,
        )

    return Result(
        SCHEMA_VERSION,
        VERSION,
        args.command,
        "UNSUPPORTED",
        EXIT_UNSUPPORTED,
        "STATIC",
        "shader sources prepared and hashed; real OpenGL compile/link remains pending GLCLI-004",
        str(args.artifacts) if args.artifacts else None,
        {"sourcePreparation": prepared.metadata()},
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "probe":
        result = _dispatch_probe(args)
    elif args.command == "compile":
        result = _compile_source_result(args)
    else:
        from tools.focal_gl import _not_implemented_result

        result = _not_implemented_result(args)
    emit(result, args.json_output)
    return result.exitCode
