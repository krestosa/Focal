"""Backend dispatch for the public ``focal-gl`` executable.

The core CLI module retains the EGL implementation. This adapter adds the
controlled hidden GLFW route without duplicating the argument or result
contracts, and gives ``auto`` a deterministic EGL-then-GLFW fallback.
"""
from __future__ import annotations

from typing import Sequence

from tools.focal_gl import (
    EXIT_CONTEXT_UNAVAILABLE,
    EXIT_OK,
    SCHEMA_VERSION,
    VERSION,
    ContextUnavailable,
    Result,
    _probe_result,
    build_parser,
    emit,
)
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "probe":
        result = _dispatch_probe(args)
    else:
        # Preserve the existing command contract until later GLCLI units add
        # compile, render and suite execution.
        from tools.focal_gl import _not_implemented_result

        result = _not_implemented_result(args)
    emit(result, args.json_output)
    return result.exitCode
