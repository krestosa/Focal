"""Native WGL probe result adapter."""
from __future__ import annotations

from tools.focal_gl import (
    EXIT_CONTEXT_UNAVAILABLE,
    EXIT_OK,
    SCHEMA_VERSION,
    VERSION,
    ContextUnavailable,
    Result,
)
from tools.wgl_context import WglContextUnavailable, create_hidden_wgl_context
from tools.wgl_probe import query_current_wgl_context


def wgl_probe_result(args) -> Result:
    try:
        with create_hidden_wgl_context(
            args.gl_version,
            args.gl_profile,
            args.size,
        ) as context_handle:
            context = query_current_wgl_context(
                context_handle,
                args.gl_version,
                args.gl_profile,
            )
    except (WglContextUnavailable, ContextUnavailable, OSError) as exc:
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
        "real hidden native WGL OpenGL context created and queried",
        str(args.artifacts) if args.artifacts else None,
        context,
    )
