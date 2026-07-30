"""OpenGL capability query for a current hidden GLFW context.

The context adapter owns window creation and teardown. This module only resolves
OpenGL entry points through ``glfwGetProcAddress`` and returns the same bounded,
machine-readable capability shape used by the EGL probe.
"""
from __future__ import annotations

import ctypes
from typing import Any, Callable

from tools.glfw_context import HiddenGlfwContext

GL_VENDOR = 0x1F00
GL_RENDERER = 0x1F01
GL_VERSION = 0x1F02
GL_EXTENSIONS = 0x1F03
GL_SHADING_LANGUAGE_VERSION = 0x8B8C
GL_NUM_EXTENSIONS = 0x821D
GL_MAX_COLOR_ATTACHMENTS = 0x8CDF
GL_MAX_DRAW_BUFFERS = 0x8824
GL_MAX_TEXTURE_SIZE = 0x0D33


class GlfwProbeUnavailable(RuntimeError):
    """Raised when required OpenGL query entry points cannot be resolved."""


def _function(
    context: HiddenGlfwContext,
    name: bytes,
    restype: Any,
    *argtypes: Any,
) -> Callable[..., Any]:
    pointer = context.get_proc_address(name)
    if not pointer:
        raise GlfwProbeUnavailable(f"required OpenGL symbol {name.decode()} is unavailable")
    return ctypes.CFUNCTYPE(restype, *argtypes)(pointer)


def _decode(pointer: bytes | None) -> str | None:
    return pointer.decode("utf-8", errors="replace") if pointer else None


def query_current_glfw_context(
    context: HiddenGlfwContext,
    requested_version: str,
    requested_profile: str,
) -> dict[str, Any]:
    """Query strings, limits, extensions and derived capabilities."""
    get_string = _function(context, b"glGetString", ctypes.c_char_p, ctypes.c_uint)
    get_integer = _function(
        context,
        b"glGetIntegerv",
        None,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_int),
    )
    get_string_i_pointer = context.get_proc_address(b"glGetStringi")
    get_string_i = (
        ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint)(
            get_string_i_pointer
        )
        if get_string_i_pointer
        else None
    )

    def integer(enum: int) -> int:
        value = ctypes.c_int()
        get_integer(enum, ctypes.byref(value))
        return value.value

    extensions: list[str]
    extension_api: str
    if get_string_i is not None:
        count = integer(GL_NUM_EXTENSIONS)
        if count < 0:
            raise GlfwProbeUnavailable("GL_NUM_EXTENSIONS returned a negative value")
        extensions = sorted(
            {
                decoded
                for index in range(count)
                if (decoded := _decode(get_string_i(GL_EXTENSIONS, index)))
            }
        )
        extension_api = "glGetStringi"
    else:
        legacy = _decode(get_string(GL_EXTENSIONS))
        if legacy is None:
            raise GlfwProbeUnavailable(
                "OpenGL extension enumeration is unavailable: glGetStringi was not resolved and GL_EXTENSIONS is null"
            )
        extensions = sorted(set(legacy.split()))
        extension_api = "glGetString"

    limits = {
        "maxColorAttachments": integer(GL_MAX_COLOR_ATTACHMENTS),
        "maxDrawBuffers": integer(GL_MAX_DRAW_BUFFERS),
        "maxTextureSize": integer(GL_MAX_TEXTURE_SIZE),
        "numExtensions": len(extensions),
    }
    lowered = [extension.lower() for extension in extensions]
    capabilities = {
        "framebuffer": limits["maxColorAttachments"] > 0,
        "geometry": any("geometry_shader" in extension for extension in lowered),
        "tessellation": any("tessellation_shader" in extension for extension in lowered),
        "compute": any("compute_shader" in extension for extension in lowered),
        "images": any("shader_image_load_store" in extension for extension in lowered),
        "ssbo": any("shader_storage_buffer_object" in extension for extension in lowered),
        "debugOutput": any("debug" in extension for extension in lowered),
        "timerQuery": any("timer_query" in extension for extension in lowered),
    }
    return {
        "backend": "glfw-hidden",
        "requestedVersion": requested_version,
        "requestedProfile": requested_profile,
        "extensionEnumeration": extension_api,
        "vendor": _decode(get_string(GL_VENDOR)),
        "renderer": _decode(get_string(GL_RENDERER)),
        "version": _decode(get_string(GL_VERSION)),
        "glslVersion": _decode(get_string(GL_SHADING_LANGUAGE_VERSION)),
        "limits": limits,
        "extensions": extensions,
        "capabilities": capabilities,
    }
