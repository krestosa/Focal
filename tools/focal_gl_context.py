#!/usr/bin/env python3
"""Bounded offscreen OpenGL context probing for ``focal-gl``.

The implementation uses the platform EGL loader through ``ctypes`` and does
not simulate success. It creates a real pbuffer context, queries the active GL
implementation, and tears every resource down before returning.
"""

from __future__ import annotations

import ctypes
import ctypes.util
from dataclasses import dataclass
from typing import Any


EGL_FALSE = 0
EGL_NONE = 0x3038
EGL_SURFACE_TYPE = 0x3033
EGL_PBUFFER_BIT = 0x0001
EGL_RENDERABLE_TYPE = 0x3040
EGL_OPENGL_BIT = 0x0008
EGL_RED_SIZE = 0x3024
EGL_GREEN_SIZE = 0x3023
EGL_BLUE_SIZE = 0x3022
EGL_ALPHA_SIZE = 0x3021
EGL_DEPTH_SIZE = 0x3025
EGL_WIDTH = 0x3057
EGL_HEIGHT = 0x3056
EGL_CONTEXT_MAJOR_VERSION = 0x3098
EGL_CONTEXT_MINOR_VERSION = 0x30FB
EGL_CONTEXT_OPENGL_PROFILE_MASK = 0x30FD
EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT = 0x00000001
EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT = 0x00000002
EGL_OPENGL_API = 0x30A2
EGL_EXTENSIONS = 0x3055
EGL_VENDOR = 0x3053
EGL_VERSION = 0x3054
EGL_CLIENT_APIS = 0x308D

GL_VENDOR = 0x1F00
GL_RENDERER = 0x1F01
GL_VERSION = 0x1F02
GL_EXTENSIONS = 0x1F03
GL_SHADING_LANGUAGE_VERSION = 0x8B8C
GL_MAJOR_VERSION = 0x821B
GL_MINOR_VERSION = 0x821C
GL_CONTEXT_PROFILE_MASK = 0x9126
GL_CONTEXT_CORE_PROFILE_BIT = 0x00000001
GL_CONTEXT_COMPATIBILITY_PROFILE_BIT = 0x00000002
GL_MAX_COLOR_ATTACHMENTS = 0x8CDF
GL_MAX_DRAW_BUFFERS = 0x8824
GL_MAX_TEXTURE_SIZE = 0x0D33
GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS = 0x8B4D
GL_MAX_VERTEX_ATTRIBS = 0x8869
GL_MAX_UNIFORM_BUFFER_BINDINGS = 0x8A2F
GL_MAX_SHADER_STORAGE_BUFFER_BINDINGS = 0x90DD
GL_MAX_IMAGE_UNITS = 0x8F38
GL_NUM_EXTENSIONS = 0x821D


class ContextUnavailable(RuntimeError):
    """Raised when no real context could be created."""


@dataclass(frozen=True)
class ContextRequest:
    major: int
    minor: int
    profile: str
    width: int
    height: int


class EglProbe:
    def __init__(self) -> None:
        library_name = ctypes.util.find_library("EGL")
        if not library_name:
            raise ContextUnavailable("EGL loader was not found")
        try:
            self.egl = ctypes.CDLL(library_name)
        except OSError as exc:
            raise ContextUnavailable(f"EGL loader could not be opened: {exc}") from exc
        self._configure_egl()
        self.display = ctypes.c_void_p()
        self.surface = ctypes.c_void_p()
        self.context = ctypes.c_void_p()

    def _configure_egl(self) -> None:
        void_p = ctypes.c_void_p
        int_p = ctypes.POINTER(ctypes.c_int)
        self.egl.eglGetDisplay.argtypes = [void_p]
        self.egl.eglGetDisplay.restype = void_p
        self.egl.eglInitialize.argtypes = [void_p, int_p, int_p]
        self.egl.eglInitialize.restype = ctypes.c_uint
        self.egl.eglBindAPI.argtypes = [ctypes.c_uint]
        self.egl.eglBindAPI.restype = ctypes.c_uint
        self.egl.eglChooseConfig.argtypes = [void_p, int_p, ctypes.POINTER(void_p), ctypes.c_int, int_p]
        self.egl.eglChooseConfig.restype = ctypes.c_uint
        self.egl.eglCreatePbufferSurface.argtypes = [void_p, void_p, int_p]
        self.egl.eglCreatePbufferSurface.restype = void_p
        self.egl.eglCreateContext.argtypes = [void_p, void_p, void_p, int_p]
        self.egl.eglCreateContext.restype = void_p
        self.egl.eglMakeCurrent.argtypes = [void_p, void_p, void_p, void_p]
        self.egl.eglMakeCurrent.restype = ctypes.c_uint
        self.egl.eglDestroyContext.argtypes = [void_p, void_p]
        self.egl.eglDestroyContext.restype = ctypes.c_uint
        self.egl.eglDestroySurface.argtypes = [void_p, void_p]
        self.egl.eglDestroySurface.restype = ctypes.c_uint
        self.egl.eglTerminate.argtypes = [void_p]
        self.egl.eglTerminate.restype = ctypes.c_uint
        self.egl.eglQueryString.argtypes = [void_p, ctypes.c_int]
        self.egl.eglQueryString.restype = ctypes.c_char_p
        self.egl.eglGetError.argtypes = []
        self.egl.eglGetError.restype = ctypes.c_uint
        self.egl.eglGetProcAddress.argtypes = [ctypes.c_char_p]
        self.egl.eglGetProcAddress.restype = void_p

    def _error(self, action: str) -> ContextUnavailable:
        return ContextUnavailable(f"{action} failed with EGL error 0x{self.egl.eglGetError():04x}")

    def create(self, request: ContextRequest) -> None:
        self.display = self.egl.eglGetDisplay(ctypes.c_void_p())
        if not self.display:
            raise self._error("eglGetDisplay")
        major = ctypes.c_int()
        minor = ctypes.c_int()
        if self.egl.eglInitialize(self.display, ctypes.byref(major), ctypes.byref(minor)) == EGL_FALSE:
            raise self._error("eglInitialize")
        if self.egl.eglBindAPI(EGL_OPENGL_API) == EGL_FALSE:
            raise self._error("eglBindAPI(OpenGL)")

        config_attributes = (ctypes.c_int * 17)(
            EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
            EGL_RED_SIZE, 8,
            EGL_GREEN_SIZE, 8,
            EGL_BLUE_SIZE, 8,
            EGL_ALPHA_SIZE, 8,
            EGL_DEPTH_SIZE, 24,
            EGL_NONE, EGL_NONE, EGL_NONE,
        )
        config = ctypes.c_void_p()
        config_count = ctypes.c_int()
        if self.egl.eglChooseConfig(
            self.display,
            config_attributes,
            ctypes.byref(config),
            1,
            ctypes.byref(config_count),
        ) == EGL_FALSE or config_count.value < 1:
            raise self._error("eglChooseConfig")

        surface_attributes = (ctypes.c_int * 5)(
            EGL_WIDTH, request.width,
            EGL_HEIGHT, request.height,
            EGL_NONE,
        )
        self.surface = self.egl.eglCreatePbufferSurface(self.display, config, surface_attributes)
        if not self.surface:
            raise self._error("eglCreatePbufferSurface")

        profile_bit = (
            EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT
            if request.profile == "core"
            else EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT
        )
        context_attributes = (ctypes.c_int * 7)(
            EGL_CONTEXT_MAJOR_VERSION, request.major,
            EGL_CONTEXT_MINOR_VERSION, request.minor,
            EGL_CONTEXT_OPENGL_PROFILE_MASK, profile_bit,
            EGL_NONE,
        )
        self.context = self.egl.eglCreateContext(
            self.display,
            config,
            ctypes.c_void_p(),
            context_attributes,
        )
        if not self.context:
            raise self._error("eglCreateContext")
        if self.egl.eglMakeCurrent(
            self.display,
            self.surface,
            self.surface,
            self.context,
        ) == EGL_FALSE:
            raise self._error("eglMakeCurrent")

    def _function(self, name: str, restype: Any, argtypes: list[Any]) -> Any:
        address = self.egl.eglGetProcAddress(name.encode("ascii"))
        if not address:
            gl_name = ctypes.util.find_library("GL")
            if gl_name:
                gl = ctypes.CDLL(gl_name)
                try:
                    function = getattr(gl, name)
                    function.restype = restype
                    function.argtypes = argtypes
                    return function
                except AttributeError:
                    pass
            raise ContextUnavailable(f"OpenGL function {name} is unavailable")
        function_type = ctypes.CFUNCTYPE(restype, *argtypes)
        return function_type(address)

    def query(self) -> dict[str, Any]:
        gl_get_string = self._function("glGetString", ctypes.c_char_p, [ctypes.c_uint])
        gl_get_integer = self._function(
            "glGetIntegerv",
            None,
            [ctypes.c_uint, ctypes.POINTER(ctypes.c_int)],
        )

        def string(name: int) -> str | None:
            value = gl_get_string(name)
            return value.decode("utf-8", errors="replace") if value else None

        def integer(name: int) -> int | None:
            value = ctypes.c_int()
            gl_get_integer(name, ctypes.byref(value))
            return value.value

        profile_mask = integer(GL_CONTEXT_PROFILE_MASK) or 0
        if profile_mask & GL_CONTEXT_CORE_PROFILE_BIT:
            profile = "core"
        elif profile_mask & GL_CONTEXT_COMPATIBILITY_PROFILE_BIT:
            profile = "compatibility"
        else:
            profile = "unknown"

        extension_text = string(GL_EXTENSIONS)
        extensions: list[str] = []
        if extension_text:
            extensions = sorted(item for item in extension_text.split() if item)
        else:
            try:
                gl_get_string_i = self._function(
                    "glGetStringi",
                    ctypes.c_char_p,
                    [ctypes.c_uint, ctypes.c_uint],
                )
                count = max(0, integer(GL_NUM_EXTENSIONS) or 0)
                for index in range(min(count, 16384)):
                    value = gl_get_string_i(GL_EXTENSIONS, index)
                    if value:
                        extensions.append(value.decode("utf-8", errors="replace"))
                extensions.sort()
            except ContextUnavailable:
                extensions = []

        extension_set = set(extensions)
        major = integer(GL_MAJOR_VERSION)
        minor = integer(GL_MINOR_VERSION)
        capabilities = {
            "geometryShader": bool((major or 0) >= 3 or "GL_ARB_geometry_shader4" in extension_set),
            "tessellationShader": bool((major or 0) >= 4 or "GL_ARB_tessellation_shader" in extension_set),
            "computeShader": bool((major or 0) > 4 or ((major or 0) == 4 and (minor or 0) >= 3) or "GL_ARB_compute_shader" in extension_set),
            "shaderStorageBuffer": bool((major or 0) > 4 or ((major or 0) == 4 and (minor or 0) >= 3) or "GL_ARB_shader_storage_buffer_object" in extension_set),
            "imageLoadStore": bool((major or 0) > 4 or ((major or 0) == 4 and (minor or 0) >= 2) or "GL_ARB_shader_image_load_store" in extension_set),
            "debugOutput": bool("GL_KHR_debug" in extension_set or "GL_ARB_debug_output" in extension_set),
            "timerQuery": bool("GL_ARB_timer_query" in extension_set),
        }
        limits = {
            "maxColorAttachments": integer(GL_MAX_COLOR_ATTACHMENTS),
            "maxDrawBuffers": integer(GL_MAX_DRAW_BUFFERS),
            "maxTextureSize": integer(GL_MAX_TEXTURE_SIZE),
            "maxCombinedTextureImageUnits": integer(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS),
            "maxVertexAttribs": integer(GL_MAX_VERTEX_ATTRIBS),
            "maxUniformBufferBindings": integer(GL_MAX_UNIFORM_BUFFER_BINDINGS),
            "maxShaderStorageBufferBindings": integer(GL_MAX_SHADER_STORAGE_BUFFER_BINDINGS),
            "maxImageUnits": integer(GL_MAX_IMAGE_UNITS),
        }
        return {
            "backend": "egl-pbuffer",
            "egl": {
                "vendor": self._egl_string(EGL_VENDOR),
                "version": self._egl_string(EGL_VERSION),
                "clientApis": self._egl_string(EGL_CLIENT_APIS),
                "extensions": sorted((self._egl_string(EGL_EXTENSIONS) or "").split()),
            },
            "gl": {
                "vendor": string(GL_VENDOR),
                "renderer": string(GL_RENDERER),
                "version": string(GL_VERSION),
                "glslVersion": string(GL_SHADING_LANGUAGE_VERSION),
                "major": major,
                "minor": minor,
                "profile": profile,
                "extensions": extensions,
                "limits": limits,
                "capabilities": capabilities,
            },
        }

    def _egl_string(self, name: int) -> str | None:
        value = self.egl.eglQueryString(self.display, name)
        return value.decode("utf-8", errors="replace") if value else None

    def close(self) -> None:
        if self.display and self.context:
            self.egl.eglMakeCurrent(
                self.display,
                ctypes.c_void_p(),
                ctypes.c_void_p(),
                ctypes.c_void_p(),
            )
            self.egl.eglDestroyContext(self.display, self.context)
            self.context = ctypes.c_void_p()
        if self.display and self.surface:
            self.egl.eglDestroySurface(self.display, self.surface)
            self.surface = ctypes.c_void_p()
        if self.display:
            self.egl.eglTerminate(self.display)
            self.display = ctypes.c_void_p()

    def __enter__(self) -> "EglProbe":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def probe_context(*, version: str, profile: str, size: str, backend: str) -> dict[str, Any]:
    if backend not in {"auto", "egl"}:
        raise ContextUnavailable(f"backend {backend!r} is not implemented on this platform")
    major_text, minor_text = version.split(".", 1)
    width_text, height_text = size.split("x", 1)
    request = ContextRequest(
        major=int(major_text),
        minor=int(minor_text),
        profile=profile,
        width=int(width_text),
        height=int(height_text),
    )
    with EglProbe() as probe:
        probe.create(request)
        return probe.query()
