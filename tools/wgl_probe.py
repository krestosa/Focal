"""Capability query for a current native WGL context."""
from __future__ import annotations

from typing import Any

from tools.glfw_probe import query_current_glfw_context
from tools.wgl_context import HiddenWglContext


def query_current_wgl_context(
    context: HiddenWglContext,
    requested_version: str,
    requested_profile: str,
) -> dict[str, Any]:
    """Reuse the bounded current-context query and identify native WGL evidence."""
    report = query_current_glfw_context(context, requested_version, requested_profile)
    report["backend"] = "wgl-hidden"
    return report
