"""Native hidden WGL context adapter for the ``focal-gl probe`` command."""
from __future__ import annotations

import ctypes
import sys
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any

if sys.platform == "win32":
    from ctypes import wintypes
else:
    wintypes = None


class WglContextUnavailable(RuntimeError):
    """Raised when a native Windows OpenGL context cannot be created."""


@dataclass
class HiddenWglContext(AbstractContextManager["HiddenWglContext"]):
    user32: Any
    gdi32: Any
    opengl32: Any
    hwnd: int
    hdc: int
    hglrc: int
    class_name: str
    instance: int

    def get_proc_address(self, name: bytes) -> int:
        pointer = self.opengl32.wglGetProcAddress(name)
        invalid = {0, 1, 2, 3, ctypes.c_void_p(-1).value}
        if pointer not in invalid:
            return int(pointer)
        address = ctypes.windll.kernel32.GetProcAddress(self.opengl32._handle, name)
        return int(address or 0)

    def close(self) -> None:
        if self.hglrc:
            self.opengl32.wglMakeCurrent(0, 0)
            self.opengl32.wglDeleteContext(self.hglrc)
            self.hglrc = 0
        if self.hdc and self.hwnd:
            self.user32.ReleaseDC(self.hwnd, self.hdc)
            self.hdc = 0
        if self.hwnd:
            self.user32.DestroyWindow(self.hwnd)
            self.hwnd = 0
        if self.class_name:
            self.user32.UnregisterClassW(self.class_name, self.instance)
            self.class_name = ""

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _parse_version(value: str) -> tuple[int, int]:
    major, minor = value.split(".", 1)
    return int(major), int(minor)


def create_hidden_wgl_context(
    requested_version: str,
    requested_profile: str,
    size: str,
) -> HiddenWglContext:
    """Create a native hidden WGL context, upgrading from a legacy bootstrap context."""
    if sys.platform != "win32" or wintypes is None:
        raise WglContextUnavailable("native WGL is available only on Windows")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    opengl32 = ctypes.WinDLL("opengl32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    WNDPROC = ctypes.WINFUNCTYPE(
        wintypes.LRESULT,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class PIXELFORMATDESCRIPTOR(ctypes.Structure):
        _fields_ = [
            ("nSize", wintypes.WORD),
            ("nVersion", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("iPixelType", ctypes.c_ubyte),
            ("cColorBits", ctypes.c_ubyte),
            ("cRedBits", ctypes.c_ubyte),
            ("cRedShift", ctypes.c_ubyte),
            ("cGreenBits", ctypes.c_ubyte),
            ("cGreenShift", ctypes.c_ubyte),
            ("cBlueBits", ctypes.c_ubyte),
            ("cBlueShift", ctypes.c_ubyte),
            ("cAlphaBits", ctypes.c_ubyte),
            ("cAlphaShift", ctypes.c_ubyte),
            ("cAccumBits", ctypes.c_ubyte),
            ("cAccumRedBits", ctypes.c_ubyte),
            ("cAccumGreenBits", ctypes.c_ubyte),
            ("cAccumBlueBits", ctypes.c_ubyte),
            ("cAccumAlphaBits", ctypes.c_ubyte),
            ("cDepthBits", ctypes.c_ubyte),
            ("cStencilBits", ctypes.c_ubyte),
            ("cAuxBuffers", ctypes.c_ubyte),
            ("iLayerType", ctypes.c_ubyte),
            ("bReserved", ctypes.c_ubyte),
            ("dwLayerMask", wintypes.DWORD),
            ("dwVisibleMask", wintypes.DWORD),
            ("dwDamageMask", wintypes.DWORD),
        ]

    user32.DefWindowProcW.restype = wintypes.LRESULT
    user32.DefWindowProcW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    wnd_proc = WNDPROC(user32.DefWindowProcW)

    instance = kernel32.GetModuleHandleW(None)
    class_name = f"FocalWglHidden_{id(wnd_proc):x}"
    wc = WNDCLASSW()
    wc.style = 0x0020 | 0x0001 | 0x0002
    wc.lpfnWndProc = wnd_proc
    wc.hInstance = instance
    wc.lpszClassName = class_name
    if not user32.RegisterClassW(ctypes.byref(wc)):
        raise WglContextUnavailable(f"RegisterClassW failed: {ctypes.get_last_error()}")

    width, height = (int(part) for part in size.split("x", 1))
    hwnd = user32.CreateWindowExW(
        0,
        class_name,
        "Focal hidden WGL",
        0,
        0,
        0,
        width,
        height,
        0,
        0,
        instance,
        None,
    )
    if not hwnd:
        user32.UnregisterClassW(class_name, instance)
        raise WglContextUnavailable(f"CreateWindowExW failed: {ctypes.get_last_error()}")

    hdc = user32.GetDC(hwnd)
    if not hdc:
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, instance)
        raise WglContextUnavailable(f"GetDC failed: {ctypes.get_last_error()}")

    pfd = PIXELFORMATDESCRIPTOR()
    pfd.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR)
    pfd.nVersion = 1
    pfd.dwFlags = 0x00000004 | 0x00000020 | 0x00000001
    pfd.iPixelType = 0
    pfd.cColorBits = 32
    pfd.cAlphaBits = 8
    pfd.cDepthBits = 24
    pfd.cStencilBits = 8
    pfd.iLayerType = 0

    pixel_format = gdi32.ChoosePixelFormat(hdc, ctypes.byref(pfd))
    if not pixel_format or not gdi32.SetPixelFormat(hdc, pixel_format, ctypes.byref(pfd)):
        user32.ReleaseDC(hwnd, hdc)
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, instance)
        raise WglContextUnavailable(f"pixel format setup failed: {ctypes.get_last_error()}")

    opengl32.wglCreateContext.restype = wintypes.HANDLE
    opengl32.wglCreateContext.argtypes = [wintypes.HDC]
    opengl32.wglMakeCurrent.argtypes = [wintypes.HDC, wintypes.HANDLE]
    opengl32.wglMakeCurrent.restype = wintypes.BOOL
    opengl32.wglDeleteContext.argtypes = [wintypes.HANDLE]
    opengl32.wglGetProcAddress.argtypes = [ctypes.c_char_p]
    opengl32.wglGetProcAddress.restype = ctypes.c_void_p

    legacy = opengl32.wglCreateContext(hdc)
    if not legacy or not opengl32.wglMakeCurrent(hdc, legacy):
        user32.ReleaseDC(hwnd, hdc)
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, instance)
        raise WglContextUnavailable(f"legacy WGL context creation failed: {ctypes.get_last_error()}")

    hglrc = legacy
    try:
        create_pointer = opengl32.wglGetProcAddress(b"wglCreateContextAttribsARB")
        if create_pointer:
            create_attribs = ctypes.WINFUNCTYPE(
                wintypes.HANDLE,
                wintypes.HDC,
                wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_int),
            )(create_pointer)
            major, minor = _parse_version(requested_version)
            profile_mask = 0x00000001 if requested_profile == "core" else 0x00000002
            attributes = (ctypes.c_int * 9)(
                0x2091,
                major,
                0x2092,
                minor,
                0x9126,
                profile_mask,
                0x2094,
                0,
                0,
            )
            modern = create_attribs(hdc, 0, attributes)
            if not modern:
                raise WglContextUnavailable(
                    f"wglCreateContextAttribsARB {requested_version} {requested_profile} failed"
                )
            opengl32.wglMakeCurrent(0, 0)
            opengl32.wglDeleteContext(legacy)
            legacy = 0
            if not opengl32.wglMakeCurrent(hdc, modern):
                opengl32.wglDeleteContext(modern)
                raise WglContextUnavailable("wglMakeCurrent failed for upgraded context")
            hglrc = modern
        elif requested_profile == "core" or _parse_version(requested_version) > (2, 1):
            raise WglContextUnavailable(
                "WGL_ARB_create_context is unavailable for the requested context"
            )
    except Exception:
        if hglrc:
            opengl32.wglMakeCurrent(0, 0)
            opengl32.wglDeleteContext(hglrc)
        user32.ReleaseDC(hwnd, hdc)
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, instance)
        raise

    return HiddenWglContext(
        user32=user32,
        gdi32=gdi32,
        opengl32=opengl32,
        hwnd=int(hwnd),
        hdc=int(hdc),
        hglrc=int(hglrc),
        class_name=class_name,
        instance=int(instance),
    )
