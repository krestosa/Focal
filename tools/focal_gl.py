#!/usr/bin/env python3
"""Standalone OpenGL validation harness for Focal shaders.

GLCLI-001 defines the stable command surface. GLCLI-002 provides a real EGL
surfaceless/pbuffer context probe and robust extension enumeration for core and
compatibility profiles. Later roadmap units implement compile, render and suite
execution.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

VERSION = "0.3.0"
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

GL_EXTENSIONS = 0x1F03
GL_NUM_EXTENSIONS = 0x821D


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
    context: dict[str, Any] | None = None


class ContextUnavailable(RuntimeError):
    pass


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
    commands = (
        ("probe", "Create a context and report capabilities."),
        ("compile", "Compile and link a selected shader program."),
        ("render", "Render a deterministic fixture and read it back."),
        ("suite", "Run a declared fixture matrix."),
    )
    for command, description in commands:
        child = subparsers.add_parser(command, help=description, description=description)
        _add_common_options(child)
    return parser


def _decode_gl_string(pointer: bytes | None) -> str | None:
    return pointer.decode("utf-8", errors="replace") if pointer else None


def _enumerate_extensions(
    get_string: Callable[[int], bytes | None],
    get_integer: Callable[[int], int],
    get_string_i: Callable[[int, int], bytes | None] | None,
) -> tuple[list[str], str]:
    """Return sorted extensions and the API used to enumerate them.

    OpenGL 3.0+ core profiles require GL_NUM_EXTENSIONS plus glGetStringi.
    Compatibility contexts may still expose the legacy space-separated string.
    """
    if get_string_i is not None:
        count = get_integer(GL_NUM_EXTENSIONS)
        if count < 0:
            raise ContextUnavailable("GL_NUM_EXTENSIONS returned a negative value")
        names = {
            decoded
            for index in range(count)
            if (decoded := _decode_gl_string(get_string_i(GL_EXTENSIONS, index)))
        }
        return sorted(names), "glGetStringi"

    legacy = _decode_gl_string(get_string(GL_EXTENSIONS))
    if legacy is None:
        raise ContextUnavailable(
            "OpenGL extension enumeration is unavailable: glGetStringi was not resolved and GL_EXTENSIONS is null"
        )
    return sorted(set(legacy.split())), "glGetString"


def _egl_probe(requested_version: str, requested_profile: str, size: str) -> dict[str, Any]:
    egl_name = ctypes.util.find_library("EGL")
    gl_name = ctypes.util.find_library("GL")
    if not egl_name or not gl_name:
        raise ContextUnavailable("libEGL or libGL is unavailable")

    egl = ctypes.CDLL(egl_name)
    gl = ctypes.CDLL(gl_name)
    EGLDisplay = ctypes.c_void_p
    EGLConfig = ctypes.c_void_p
    EGLContext = ctypes.c_void_p
    EGLSurface = ctypes.c_void_p
    EGLint = ctypes.c_int
    EGLBoolean = ctypes.c_uint
    EGL_DEFAULT_DISPLAY = ctypes.c_void_p(0)
    EGL_NO_DISPLAY = ctypes.c_void_p(0)
    EGL_NO_CONTEXT = ctypes.c_void_p(0)
    EGL_NO_SURFACE = ctypes.c_void_p(0)
    EGL_OPENGL_API = 0x30A2
    EGL_SURFACE_TYPE = 0x3033
    EGL_PBUFFER_BIT = 0x0001
    EGL_RENDERABLE_TYPE = 0x3040
    EGL_OPENGL_BIT = 0x0008
    EGL_RED_SIZE, EGL_GREEN_SIZE, EGL_BLUE_SIZE = 0x3024, 0x3023, 0x3022
    EGL_ALPHA_SIZE, EGL_DEPTH_SIZE = 0x3021, 0x3025
    EGL_NONE, EGL_WIDTH, EGL_HEIGHT = 0x3038, 0x3057, 0x3056
    EGL_CONTEXT_MAJOR_VERSION = 0x3098
    EGL_CONTEXT_MINOR_VERSION = 0x30FB
    EGL_CONTEXT_OPENGL_PROFILE_MASK = 0x30FD
    EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT = 1
    EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT = 2
    EGL_PLATFORM_SURFACELESS_MESA = 0x31DD

    egl.eglGetDisplay.argtypes = [ctypes.c_void_p]
    egl.eglGetDisplay.restype = EGLDisplay
    egl.eglInitialize.argtypes = [EGLDisplay, ctypes.POINTER(EGLint), ctypes.POINTER(EGLint)]
    egl.eglInitialize.restype = EGLBoolean
    egl.eglBindAPI.argtypes = [ctypes.c_uint]
    egl.eglBindAPI.restype = EGLBoolean
    egl.eglChooseConfig.argtypes = [
        EGLDisplay,
        ctypes.POINTER(EGLint),
        ctypes.POINTER(EGLConfig),
        EGLint,
        ctypes.POINTER(EGLint),
    ]
    egl.eglChooseConfig.restype = EGLBoolean
    egl.eglCreateContext.argtypes = [EGLDisplay, EGLConfig, EGLContext, ctypes.POINTER(EGLint)]
    egl.eglCreateContext.restype = EGLContext
    egl.eglCreatePbufferSurface.argtypes = [EGLDisplay, EGLConfig, ctypes.POINTER(EGLint)]
    egl.eglCreatePbufferSurface.restype = EGLSurface
    egl.eglMakeCurrent.argtypes = [EGLDisplay, EGLSurface, EGLSurface, EGLContext]
    egl.eglMakeCurrent.restype = EGLBoolean
    egl.eglDestroySurface.argtypes = [EGLDisplay, EGLSurface]
    egl.eglDestroyContext.argtypes = [EGLDisplay, EGLContext]
    egl.eglTerminate.argtypes = [EGLDisplay]
    egl.eglGetError.restype = EGLint
    egl.eglGetProcAddress.argtypes = [ctypes.c_char_p]
    egl.eglGetProcAddress.restype = ctypes.c_void_p

    backend = "egl-default"
    display = EGL_NO_DISPLAY
    platform_ptr = egl.eglGetProcAddress(b"eglGetPlatformDisplayEXT")
    if platform_ptr:
        get_platform_display = ctypes.CFUNCTYPE(
            EGLDisplay, ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(EGLint)
        )(platform_ptr)
        display = get_platform_display(EGL_PLATFORM_SURFACELESS_MESA, None, None)
        if display:
            backend = "egl-surfaceless"
    if not display:
        display = egl.eglGetDisplay(EGL_DEFAULT_DISPLAY)
    if not display:
        raise ContextUnavailable(f"eglGetDisplay failed: 0x{egl.eglGetError():04x}")

    major, minor = EGLint(), EGLint()
    if not egl.eglInitialize(display, ctypes.byref(major), ctypes.byref(minor)):
        raise ContextUnavailable(f"eglInitialize failed: 0x{egl.eglGetError():04x}")

    context = EGL_NO_CONTEXT
    surface = EGL_NO_SURFACE
    try:
        if not egl.eglBindAPI(EGL_OPENGL_API):
            raise ContextUnavailable(f"eglBindAPI(OpenGL) failed: 0x{egl.eglGetError():04x}")

        config_attributes = (EGLint * 15)(
            EGL_SURFACE_TYPE,
            EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE,
            EGL_OPENGL_BIT,
            EGL_RED_SIZE,
            8,
            EGL_GREEN_SIZE,
            8,
            EGL_BLUE_SIZE,
            8,
            EGL_ALPHA_SIZE,
            8,
            EGL_DEPTH_SIZE,
            24,
            EGL_NONE,
        )
        config = EGLConfig()
        config_count = EGLint()
        if (
            not egl.eglChooseConfig(
                display,
                config_attributes,
                ctypes.byref(config),
                1,
                ctypes.byref(config_count),
            )
            or config_count.value < 1
        ):
            raise ContextUnavailable(f"eglChooseConfig failed: 0x{egl.eglGetError():04x}")

        req_major, req_minor = (int(part) for part in requested_version.split("."))
        profile_bit = (
            EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT
            if requested_profile == "core"
            else EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT
        )
        context_attributes = (EGLint * 7)(
            EGL_CONTEXT_MAJOR_VERSION,
            req_major,
            EGL_CONTEXT_MINOR_VERSION,
            req_minor,
            EGL_CONTEXT_OPENGL_PROFILE_MASK,
            profile_bit,
            EGL_NONE,
        )
        context = egl.eglCreateContext(display, config, EGL_NO_CONTEXT, context_attributes)
        if not context:
            raise ContextUnavailable(
                f"eglCreateContext {requested_version} {requested_profile} failed: 0x{egl.eglGetError():04x}"
            )

        width, height = (int(part) for part in size.split("x"))
        surface_attributes = (EGLint * 5)(EGL_WIDTH, width, EGL_HEIGHT, height, EGL_NONE)
        surface = egl.eglCreatePbufferSurface(display, config, surface_attributes)
        if not surface or not egl.eglMakeCurrent(display, surface, surface, context):
            raise ContextUnavailable(f"EGL pbuffer activation failed: 0x{egl.eglGetError():04x}")

        gl.glGetString.argtypes = [ctypes.c_uint]
        gl.glGetString.restype = ctypes.c_char_p
        gl.glGetIntegerv.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_int)]
        GL_VENDOR, GL_RENDERER, GL_VERSION = 0x1F00, 0x1F01, 0x1F02
        GL_SHADING_LANGUAGE_VERSION = 0x8B8C
        GL_MAX_COLOR_ATTACHMENTS = 0x8CDF
        GL_MAX_DRAW_BUFFERS = 0x8824
        GL_MAX_TEXTURE_SIZE = 0x0D33

        def get_integer(enum: int) -> int:
            value = ctypes.c_int()
            gl.glGetIntegerv(enum, ctypes.byref(value))
            return value.value

        get_string_i = None
        string_i_ptr = egl.eglGetProcAddress(b"glGetStringi")
        if string_i_ptr:
            get_string_i = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint)(
                string_i_ptr
            )

        extension_names, extension_api = _enumerate_extensions(
            gl.glGetString,
            get_integer,
            get_string_i,
        )
        strings = {
            "vendor": _decode_gl_string(gl.glGetString(GL_VENDOR)),
            "renderer": _decode_gl_string(gl.glGetString(GL_RENDERER)),
            "version": _decode_gl_string(gl.glGetString(GL_VERSION)),
            "glslVersion": _decode_gl_string(gl.glGetString(GL_SHADING_LANGUAGE_VERSION)),
        }
        limits = {
            "maxColorAttachments": get_integer(GL_MAX_COLOR_ATTACHMENTS),
            "maxDrawBuffers": get_integer(GL_MAX_DRAW_BUFFERS),
            "maxTextureSize": get_integer(GL_MAX_TEXTURE_SIZE),
            "numExtensions": len(extension_names),
        }
        lowered = [extension.lower() for extension in extension_names]
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
            "backend": backend,
            "eglVersion": f"{major.value}.{minor.value}",
            "requestedVersion": requested_version,
            "requestedProfile": requested_profile,
            "extensionEnumeration": extension_api,
            **strings,
            "limits": limits,
            "extensions": extension_names,
            "capabilities": capabilities,
        }
    finally:
        if display:
            egl.eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)
            if surface:
                egl.eglDestroySurface(display, surface)
            if context:
                egl.eglDestroyContext(display, context)
            egl.eglTerminate(display)


def _probe_result(args: argparse.Namespace) -> Result:
    if args.backend not in ("auto", "egl"):
        return Result(
            SCHEMA_VERSION,
            VERSION,
            args.command,
            "UNSUPPORTED",
            EXIT_CONTEXT_UNAVAILABLE,
            "STATIC",
            f"backend {args.backend} is not implemented by GLCLI-002",
            str(args.artifacts) if args.artifacts else None,
        )
    try:
        context = _egl_probe(args.gl_version, args.gl_profile, args.size)
    except (ContextUnavailable, OSError) as exc:
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
        "real OpenGL context created and queried; shader compile/link evidence remains pending",
        str(args.artifacts) if args.artifacts else None,
        context,
    )


def _not_implemented_result(args: argparse.Namespace) -> Result:
    return Result(
        SCHEMA_VERSION,
        VERSION,
        args.command,
        "UNSUPPORTED",
        EXIT_CONTEXT_UNAVAILABLE,
        "STATIC",
        "the command requires GLCLI-003 or a later runtime unit",
        str(args.artifacts) if args.artifacts else None,
    )


def emit(result: Result, json_output: bool) -> None:
    if json_output:
        print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
        return
    print(f"focal-gl {result.harnessVersion}: {result.command}: {result.outcome}")
    print(result.message)
    if result.context:
        print(
            f"backend={result.context['backend']} renderer={result.context.get('renderer')} "
            f"version={result.context.get('version')}"
        )
    print(f"evidence={result.evidenceLevel} exit={result.exitCode}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = _probe_result(args) if args.command == "probe" else _not_implemented_result(args)
    emit(result, args.json_output)
    return result.exitCode


if __name__ == "__main__":
    sys.exit(main())
