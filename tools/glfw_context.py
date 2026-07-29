"""Minimal ctypes-based hidden GLFW OpenGL context adapter.

This module is intentionally independent from PyGLFW. It loads a system GLFW
library, creates an invisible window, makes its OpenGL context current and
exposes glfwGetProcAddress for the existing focal-gl probe. The caller owns
OpenGL symbol decoding and capability reporting.
"""
from __future__ import annotations

import ctypes
import ctypes.util
from dataclasses import dataclass
from typing import Callable

GLFW_FALSE = 0
GLFW_TRUE = 1
GLFW_VISIBLE = 0x00020004
GLFW_CLIENT_API = 0x00022001
GLFW_OPENGL_API = 0x00030001
GLFW_CONTEXT_VERSION_MAJOR = 0x00022002
GLFW_CONTEXT_VERSION_MINOR = 0x00022003
GLFW_OPENGL_PROFILE = 0x00022008
GLFW_OPENGL_CORE_PROFILE = 0x00032001
GLFW_OPENGL_COMPAT_PROFILE = 0x00032002


class GlfwContextUnavailable(RuntimeError):
    """Raised when a controlled hidden GLFW context cannot be created."""


@dataclass
class HiddenGlfwContext:
    library: ctypes.CDLL
    window: int

    def get_proc_address(self, name: bytes) -> int | None:
        pointer = self.library.glfwGetProcAddress(name)
        return int(pointer) if pointer else None

    def close(self) -> None:
        if self.window:
            self.library.glfwDestroyWindow(ctypes.c_void_p(self.window))
            self.window = 0
        self.library.glfwTerminate()

    def __enter__(self) -> "HiddenGlfwContext":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()


def _resolve_glfw_library(find_library: Callable[[str], str | None]) -> str:
    for candidate in ("glfw", "glfw3"):
        resolved = find_library(candidate)
        if resolved:
            return resolved
    raise GlfwContextUnavailable("GLFW shared library is unavailable")


def create_hidden_glfw_context(
    requested_version: str,
    requested_profile: str,
    size: str,
    *,
    find_library: Callable[[str], str | None] = ctypes.util.find_library,
    loader: Callable[[str], ctypes.CDLL] = ctypes.CDLL,
) -> HiddenGlfwContext:
    """Create an invisible GLFW window with a current desktop OpenGL context."""
    try:
        major_text, minor_text = requested_version.split(".", 1)
        major, minor = int(major_text), int(minor_text)
        width_text, height_text = size.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (TypeError, ValueError) as exc:
        raise GlfwContextUnavailable("invalid GLFW context request") from exc

    library = loader(_resolve_glfw_library(find_library))
    library.glfwInit.restype = ctypes.c_int
    library.glfwWindowHint.argtypes = [ctypes.c_int, ctypes.c_int]
    library.glfwCreateWindow.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    library.glfwCreateWindow.restype = ctypes.c_void_p
    library.glfwMakeContextCurrent.argtypes = [ctypes.c_void_p]
    library.glfwDestroyWindow.argtypes = [ctypes.c_void_p]
    library.glfwGetProcAddress.argtypes = [ctypes.c_char_p]
    library.glfwGetProcAddress.restype = ctypes.c_void_p

    if library.glfwInit() != GLFW_TRUE:
        raise GlfwContextUnavailable("glfwInit failed")

    window = 0
    try:
        library.glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE)
        library.glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_API)
        library.glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, major)
        library.glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, minor)
        profile = (
            GLFW_OPENGL_CORE_PROFILE
            if requested_profile == "core"
            else GLFW_OPENGL_COMPAT_PROFILE
        )
        library.glfwWindowHint(GLFW_OPENGL_PROFILE, profile)
        pointer = library.glfwCreateWindow(width, height, b"focal-gl", None, None)
        if not pointer:
            raise GlfwContextUnavailable(
                f"glfwCreateWindow {requested_version} {requested_profile} failed"
            )
        window = int(pointer)
        library.glfwMakeContextCurrent(ctypes.c_void_p(window))
        return HiddenGlfwContext(library=library, window=window)
    except Exception:
        if window:
            library.glfwDestroyWindow(ctypes.c_void_p(window))
        library.glfwTerminate()
        raise
