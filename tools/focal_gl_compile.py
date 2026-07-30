"""Real OpenGL stage compilation and program linking for ``focal-gl``.

The compiler consumes a GLCLI-003 ``PreparedProgram`` and a current hidden GLFW
context. It resolves only the OpenGL entry points needed for compilation, keeps
full driver logs, deletes every temporary shader/program object, and reports
``GL_COMPILE_LINK`` only after every stage compiles and the complete program
links successfully.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Callable

from tools.focal_gl_sources import PreparedProgram
from tools.glfw_context import GlfwContextUnavailable, create_hidden_glfw_context

GL_FALSE = 0
GL_COMPILE_STATUS = 0x8B81
GL_LINK_STATUS = 0x8B82
GL_INFO_LOG_LENGTH = 0x8B84

STAGE_ENUMS = {
    "vsh": 0x8B31,
    "fsh": 0x8B30,
    "gsh": 0x8DD9,
    "tcs": 0x8E88,
    "tes": 0x8E87,
    "csh": 0x91B9,
}


class CompileLinkError(RuntimeError):
    """A driver-reported shader compilation or program-link failure."""

    def __init__(self, phase: str, message: str, *, stage: str | None = None, log: str = "") -> None:
        super().__init__(message)
        self.phase = phase
        self.stage = stage
        self.log = log


@dataclass(frozen=True)
class CompiledStage:
    stage: str
    path: str
    log: str


@dataclass(frozen=True)
class CompileLinkReport:
    backend: str
    sourceMode: str
    program: str
    stages: tuple[CompiledStage, ...]
    linkLog: str

    def metadata(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "sourceMode": self.sourceMode,
            "program": self.program,
            "stages": [
                {"stage": item.stage, "path": item.path, "log": item.log}
                for item in self.stages
            ],
            "linkLog": self.linkLog,
        }


class _GlFunctions:
    def __init__(self, resolver: Callable[[bytes], int | None]) -> None:
        self.create_shader = self._load(resolver, b"glCreateShader", ctypes.c_uint, ctypes.c_uint)
        self.shader_source = self._load(
            resolver,
            b"glShaderSource",
            None,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.POINTER(ctypes.c_int),
        )
        self.compile_shader = self._load(resolver, b"glCompileShader", None, ctypes.c_uint)
        self.get_shader_iv = self._load(
            resolver, b"glGetShaderiv", None, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_int)
        )
        self.get_shader_log = self._load(
            resolver,
            b"glGetShaderInfoLog",
            None,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
        )
        self.delete_shader = self._load(resolver, b"glDeleteShader", None, ctypes.c_uint)
        self.create_program = self._load(resolver, b"glCreateProgram", ctypes.c_uint)
        self.attach_shader = self._load(resolver, b"glAttachShader", None, ctypes.c_uint, ctypes.c_uint)
        self.link_program = self._load(resolver, b"glLinkProgram", None, ctypes.c_uint)
        self.get_program_iv = self._load(
            resolver, b"glGetProgramiv", None, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_int)
        )
        self.get_program_log = self._load(
            resolver,
            b"glGetProgramInfoLog",
            None,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_char_p,
        )
        self.delete_program = self._load(resolver, b"glDeleteProgram", None, ctypes.c_uint)

    @staticmethod
    def _load(
        resolver: Callable[[bytes], int | None],
        name: bytes,
        restype,
        *argtypes,
    ):
        pointer = resolver(name)
        if not pointer:
            raise GlfwContextUnavailable(f"required OpenGL symbol is unavailable: {name.decode()}")
        return ctypes.CFUNCTYPE(restype, *argtypes)(pointer)


def _object_log(get_iv, get_log, handle: int) -> str:
    length = ctypes.c_int()
    get_iv(handle, GL_INFO_LOG_LENGTH, ctypes.byref(length))
    if length.value <= 1:
        return ""
    buffer = ctypes.create_string_buffer(length.value)
    written = ctypes.c_int()
    get_log(handle, length.value, ctypes.byref(written), buffer)
    return buffer.raw[: max(0, written.value)].decode("utf-8", errors="replace")


def _validate_stage_set(prepared: PreparedProgram) -> None:
    stages = {stage.stage for stage in prepared.stages}
    unknown = sorted(stages.difference(STAGE_ENUMS))
    if unknown:
        raise CompileLinkError("configuration", f"unsupported shader stages: {', '.join(unknown)}")
    has_compute = "csh" in stages
    has_graphics = bool(stages.difference({"csh"}))
    if has_compute and has_graphics:
        raise CompileLinkError("configuration", "compute and graphics stages cannot share one program fixture")
    if has_graphics and not {"vsh", "fsh"}.issubset(stages):
        raise CompileLinkError("configuration", "graphics programs require vertex and fragment stages")
    if ("tcs" in stages) != ("tes" in stages):
        raise CompileLinkError("configuration", "tessellation control and evaluation stages must be paired")


def compile_current_context(prepared: PreparedProgram, resolver: Callable[[bytes], int | None]) -> CompileLinkReport:
    _validate_stage_set(prepared)
    gl = _GlFunctions(resolver)
    shaders: list[int] = []
    compiled: list[CompiledStage] = []
    program_handle = 0
    try:
        for stage in prepared.stages:
            handle = int(gl.create_shader(STAGE_ENUMS[stage.stage]))
            if not handle:
                raise CompileLinkError("stage", f"glCreateShader failed for {stage.path}", stage=stage.stage)
            shaders.append(handle)
            encoded = stage.source.encode("utf-8")
            source_pointer = ctypes.c_char_p(encoded)
            source_array = (ctypes.c_char_p * 1)(source_pointer)
            source_length = (ctypes.c_int * 1)(len(encoded))
            gl.shader_source(handle, 1, source_array, source_length)
            gl.compile_shader(handle)
            status = ctypes.c_int()
            gl.get_shader_iv(handle, GL_COMPILE_STATUS, ctypes.byref(status))
            log = _object_log(gl.get_shader_iv, gl.get_shader_log, handle)
            if status.value == GL_FALSE:
                raise CompileLinkError(
                    "stage",
                    f"shader compilation failed for {stage.path}",
                    stage=stage.stage,
                    log=log,
                )
            compiled.append(CompiledStage(stage=stage.stage, path=stage.path, log=log))

        program_handle = int(gl.create_program())
        if not program_handle:
            raise CompileLinkError("link", "glCreateProgram failed")
        for shader in shaders:
            gl.attach_shader(program_handle, shader)
        gl.link_program(program_handle)
        status = ctypes.c_int()
        gl.get_program_iv(program_handle, GL_LINK_STATUS, ctypes.byref(status))
        link_log = _object_log(gl.get_program_iv, gl.get_program_log, program_handle)
        if status.value == GL_FALSE:
            raise CompileLinkError("link", "program link failed", log=link_log)
        return CompileLinkReport(
            backend="glfw-hidden",
            sourceMode=prepared.sourceMode,
            program=prepared.program,
            stages=tuple(compiled),
            linkLog=link_log,
        )
    finally:
        if program_handle:
            gl.delete_program(program_handle)
        for shader in shaders:
            gl.delete_shader(shader)


def compile_with_hidden_glfw(
    prepared: PreparedProgram,
    requested_version: str,
    requested_profile: str,
    size: str,
) -> CompileLinkReport:
    with create_hidden_glfw_context(requested_version, requested_profile, size) as context:
        return compile_current_context(prepared, context.get_proc_address)
