"""GLCLI-005 deterministic framebuffer rendering and color/depth readback."""
from __future__ import annotations

import ctypes
import hashlib
import json
import math
import struct
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from tools.focal_gl_compile import (
    GL_COMPILE_STATUS,
    GL_FALSE,
    GL_LINK_STATUS,
    STAGE_ENUMS,
    CompileLinkError,
    CompileLinkReport,
    CompiledStage,
    _GlFunctions,
    _object_log,
    _validate_stage_set,
)
from tools.focal_gl_sources import PreparedProgram
from tools.glfw_context import create_hidden_glfw_context

GL_FLOAT = 0x1406
GL_TRIANGLES = 0x0004
GL_ARRAY_BUFFER = 0x8892
GL_STATIC_DRAW = 0x88E4
GL_COLOR_BUFFER_BIT = 0x4000
GL_DEPTH_BUFFER_BIT = 0x0100
GL_DEPTH_TEST = 0x0B71
GL_TEXTURE_2D = 0x0DE1
GL_TEXTURE0 = 0x84C0
GL_RGBA = 0x1908
GL_RGBA32F = 0x8814
GL_DEPTH_COMPONENT = 0x1902
GL_DEPTH_COMPONENT24 = 0x81A6
GL_TEXTURE_MIN_FILTER = 0x2801
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_WRAP_S = 0x2802
GL_TEXTURE_WRAP_T = 0x2803
GL_NEAREST = 0x2600
GL_CLAMP_TO_EDGE = 0x812F
GL_FRAMEBUFFER = 0x8D40
GL_RENDERBUFFER = 0x8D41
GL_COLOR_ATTACHMENT0 = 0x8CE0
GL_DEPTH_ATTACHMENT = 0x8D00
GL_FRAMEBUFFER_COMPLETE = 0x8CD5
MAX_READBACK_PIXELS = 1024 * 1024


class RenderExecutionError(RuntimeError):
    pass


class RenderInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class RenderReport:
    program: str
    fixture: str
    width: int
    height: int
    compileLink: CompileLinkReport
    samplerBound: bool
    color: dict[str, object]
    depth: dict[str, object]
    artifacts: dict[str, str]

    def metadata(self) -> dict[str, object]:
        return {
            "backend": "glfw-hidden",
            "sourceMode": self.compileLink.sourceMode,
            "program": self.program,
            "fixture": self.fixture,
            "size": {"width": self.width, "height": self.height},
            "compileLink": self.compileLink.metadata(),
            "samplerBound": self.samplerBound,
            "framebufferStatus": "GL_FRAMEBUFFER_COMPLETE",
            "color": self.color,
            "depth": self.depth,
            "artifacts": self.artifacts,
        }


@contextmanager
def _linked_program(
    prepared: PreparedProgram,
    resolver: Callable[[bytes], int | None],
) -> Iterator[tuple[int, CompileLinkReport]]:
    _validate_stage_set(prepared)
    gl = _GlFunctions(resolver)
    shaders: list[int] = []
    compiled: list[CompiledStage] = []
    program = 0
    try:
        for stage in prepared.stages:
            shader = int(gl.create_shader(STAGE_ENUMS[stage.stage]))
            if not shader:
                raise CompileLinkError("stage", f"glCreateShader failed for {stage.path}", stage=stage.stage)
            shaders.append(shader)
            encoded = stage.source.encode()
            sources = (ctypes.c_char_p * 1)(ctypes.c_char_p(encoded))
            lengths = (ctypes.c_int * 1)(len(encoded))
            gl.shader_source(shader, 1, sources, lengths)
            gl.compile_shader(shader)
            status = ctypes.c_int()
            gl.get_shader_iv(shader, GL_COMPILE_STATUS, ctypes.byref(status))
            log = _object_log(gl.get_shader_iv, gl.get_shader_log, shader)
            if status.value == GL_FALSE:
                raise CompileLinkError("stage", f"shader compilation failed for {stage.path}", stage=stage.stage, log=log)
            compiled.append(CompiledStage(stage.stage, stage.path, log))
        program = int(gl.create_program())
        if not program:
            raise CompileLinkError("link", "glCreateProgram failed")
        for shader in shaders:
            gl.attach_shader(program, shader)
        gl.link_program(program)
        status = ctypes.c_int()
        gl.get_program_iv(program, GL_LINK_STATUS, ctypes.byref(status))
        log = _object_log(gl.get_program_iv, gl.get_program_log, program)
        if status.value == GL_FALSE:
            raise CompileLinkError("link", "program link failed", log=log)
        yield program, CompileLinkReport("glfw-hidden", prepared.sourceMode, prepared.program, tuple(compiled), log)
    finally:
        if program:
            gl.delete_program(program)
        for shader in shaders:
            gl.delete_shader(shader)


class _GL:
    def __init__(self, resolver: Callable[[bytes], int | None]) -> None:
        P = ctypes.POINTER
        specs = {
            "gen_vertex_arrays": (b"glGenVertexArrays", None, ctypes.c_int, P(ctypes.c_uint)),
            "bind_vertex_array": (b"glBindVertexArray", None, ctypes.c_uint),
            "delete_vertex_arrays": (b"glDeleteVertexArrays", None, ctypes.c_int, P(ctypes.c_uint)),
            "gen_buffers": (b"glGenBuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "bind_buffer": (b"glBindBuffer", None, ctypes.c_uint, ctypes.c_uint),
            "buffer_data": (b"glBufferData", None, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_uint),
            "delete_buffers": (b"glDeleteBuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "enable_vertex_attrib_array": (b"glEnableVertexAttribArray", None, ctypes.c_uint),
            "vertex_attrib_pointer": (b"glVertexAttribPointer", None, ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_ubyte, ctypes.c_int, ctypes.c_void_p),
            "gen_textures": (b"glGenTextures", None, ctypes.c_int, P(ctypes.c_uint)),
            "active_texture": (b"glActiveTexture", None, ctypes.c_uint),
            "bind_texture": (b"glBindTexture", None, ctypes.c_uint, ctypes.c_uint),
            "tex_parameter_i": (b"glTexParameteri", None, ctypes.c_uint, ctypes.c_uint, ctypes.c_int),
            "tex_image_2d": (b"glTexImage2D", None, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p),
            "delete_textures": (b"glDeleteTextures", None, ctypes.c_int, P(ctypes.c_uint)),
            "gen_framebuffers": (b"glGenFramebuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "bind_framebuffer": (b"glBindFramebuffer", None, ctypes.c_uint, ctypes.c_uint),
            "framebuffer_texture_2d": (b"glFramebufferTexture2D", None, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_int),
            "check_framebuffer_status": (b"glCheckFramebufferStatus", ctypes.c_uint, ctypes.c_uint),
            "delete_framebuffers": (b"glDeleteFramebuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "gen_renderbuffers": (b"glGenRenderbuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "bind_renderbuffer": (b"glBindRenderbuffer", None, ctypes.c_uint, ctypes.c_uint),
            "renderbuffer_storage": (b"glRenderbufferStorage", None, ctypes.c_uint, ctypes.c_uint, ctypes.c_int, ctypes.c_int),
            "framebuffer_renderbuffer": (b"glFramebufferRenderbuffer", None, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint),
            "delete_renderbuffers": (b"glDeleteRenderbuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "draw_buffers": (b"glDrawBuffers", None, ctypes.c_int, P(ctypes.c_uint)),
            "read_buffer": (b"glReadBuffer", None, ctypes.c_uint),
            "viewport": (b"glViewport", None, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int),
            "clear_color": (b"glClearColor", None, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float),
            "clear_depth": (b"glClearDepth", None, ctypes.c_double),
            "clear": (b"glClear", None, ctypes.c_uint),
            "enable": (b"glEnable", None, ctypes.c_uint),
            "use_program": (b"glUseProgram", None, ctypes.c_uint),
            "get_uniform_location": (b"glGetUniformLocation", ctypes.c_int, ctypes.c_uint, ctypes.c_char_p),
            "uniform_1i": (b"glUniform1i", None, ctypes.c_int, ctypes.c_int),
            "draw_arrays": (b"glDrawArrays", None, ctypes.c_uint, ctypes.c_int, ctypes.c_int),
            "finish": (b"glFinish", None),
            "read_pixels": (b"glReadPixels", None, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p),
            "get_error": (b"glGetError", ctypes.c_uint),
        }
        for attribute, (name, restype, *argtypes) in specs.items():
            pointer = resolver(name)
            if not pointer:
                raise RenderExecutionError(f"required OpenGL symbol is unavailable: {name.decode()}")
            setattr(self, attribute, ctypes.CFUNCTYPE(restype, *argtypes)(pointer))


def _texture(gl: _GL, width: int, height: int, data=None) -> int:
    handle = ctypes.c_uint()
    gl.gen_textures(1, ctypes.byref(handle))
    gl.bind_texture(GL_TEXTURE_2D, handle.value)
    for parameter, value in (
        (GL_TEXTURE_MIN_FILTER, GL_NEAREST),
        (GL_TEXTURE_MAG_FILTER, GL_NEAREST),
        (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE),
        (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE),
    ):
        gl.tex_parameter_i(GL_TEXTURE_2D, parameter, value)
    gl.tex_image_2d(
        GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT,
        ctypes.cast(data, ctypes.c_void_p) if data is not None else None,
    )
    return int(handle.value)


def _stats(values: list[float], channels: int) -> dict[str, object]:
    if not values or any(not math.isfinite(value) for value in values):
        raise RenderInvariantError("readback contains NaN or Inf")
    return {
        "finite": True,
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
        "channels": channels,
        "sha256": hashlib.sha256(struct.pack(f"<{len(values)}f", *values)).hexdigest(),
    }


def _write_artifacts(directory: Path, program: str, width: int, height: int, color: list[float], depth: list[float], report: dict[str, object]) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    color_path = directory / f"{program}-color.ppm"
    depth_path = directory / f"{program}-depth.pgm"
    report_path = directory / f"{program}-render.json"
    rgb = bytes(round(max(0.0, min(1.0, value)) * 255) for index, value in enumerate(color) if index % 4 != 3)
    gray = bytes(round(max(0.0, min(1.0, value)) * 255) for value in depth)
    color_path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + rgb)
    depth_path.write_bytes(f"P5\n{width} {height}\n255\n".encode() + gray)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"color": str(color_path), "depth": str(depth_path), "report": str(report_path)}


def render_current_context(prepared: PreparedProgram, resolver: Callable[[bytes], int | None], *, fixture: str, size: str, artifacts: Path | None) -> RenderReport:
    width, height = (int(part) for part in size.split("x", 1))
    if fixture not in {"geometry", "fullscreen"}:
        raise RenderInvariantError("render requires --fixture geometry or fullscreen")
    if width * height > MAX_READBACK_PIXELS:
        raise RenderInvariantError(f"render readback exceeds {MAX_READBACK_PIXELS} pixels")

    gl = _GL(resolver)
    vao, vbo, fbo, depth_buffer = (ctypes.c_uint() for _ in range(4))
    color_texture = source_texture = 0
    clear = (0.03125, 0.0625, 0.125, 1.0)
    try:
        with _linked_program(prepared, resolver) as (program, compile_report):
            gl.gen_vertex_arrays(1, ctypes.byref(vao))
            gl.bind_vertex_array(vao.value)
            if fixture == "geometry":
                vertices = (ctypes.c_float * 9)(-0.75, -0.75, 0.0, 0.75, -0.75, 0.0, 0.0, 0.75, 0.0)
                gl.gen_buffers(1, ctypes.byref(vbo))
                gl.bind_buffer(GL_ARRAY_BUFFER, vbo.value)
                gl.buffer_data(GL_ARRAY_BUFFER, ctypes.sizeof(vertices), ctypes.cast(vertices, ctypes.c_void_p), GL_STATIC_DRAW)
                gl.enable_vertex_attrib_array(0)
                gl.vertex_attrib_pointer(0, 3, GL_FLOAT, 0, 0, None)

            gl.gen_framebuffers(1, ctypes.byref(fbo))
            gl.bind_framebuffer(GL_FRAMEBUFFER, fbo.value)
            color_texture = _texture(gl, width, height)
            gl.framebuffer_texture_2d(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color_texture, 0)
            gl.gen_renderbuffers(1, ctypes.byref(depth_buffer))
            gl.bind_renderbuffer(GL_RENDERBUFFER, depth_buffer.value)
            gl.renderbuffer_storage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
            gl.framebuffer_renderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth_buffer.value)
            gl.draw_buffers(1, (ctypes.c_uint * 1)(GL_COLOR_ATTACHMENT0))
            status = int(gl.check_framebuffer_status(GL_FRAMEBUFFER))
            if status != GL_FRAMEBUFFER_COMPLETE:
                raise RenderExecutionError(f"framebuffer is incomplete: 0x{status:04x}")

            source = (ctypes.c_float * 16)(1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1)
            gl.active_texture(GL_TEXTURE0)
            source_texture = _texture(gl, 2, 2, source)
            sampler = int(gl.get_uniform_location(program, b"sourceTexture"))
            gl.use_program(program)
            if sampler >= 0:
                gl.uniform_1i(sampler, 0)
            gl.viewport(0, 0, width, height)
            gl.enable(GL_DEPTH_TEST)
            gl.clear_color(*clear)
            gl.clear_depth(1.0)
            gl.clear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            gl.draw_arrays(GL_TRIANGLES, 0, 3)
            gl.finish()
            error = int(gl.get_error())
            if error:
                raise RenderExecutionError(f"draw produced OpenGL error 0x{error:04x}")

            color_buffer = (ctypes.c_float * (width * height * 4))()
            depth_values = (ctypes.c_float * (width * height))()
            gl.read_buffer(GL_COLOR_ATTACHMENT0)
            gl.read_pixels(0, 0, width, height, GL_RGBA, GL_FLOAT, color_buffer)
            gl.read_pixels(0, 0, width, height, GL_DEPTH_COMPONENT, GL_FLOAT, depth_values)
            error = int(gl.get_error())
            if error:
                raise RenderExecutionError(f"readback produced OpenGL error 0x{error:04x}")

            color, depth = list(color_buffer), list(depth_values)
            color_stats, depth_stats = _stats(color, 4), _stats(depth, 1)
            tolerance = 1e-5
            if color_stats["minimum"] < -tolerance or color_stats["maximum"] > 1 + tolerance:
                raise RenderInvariantError("color readback is outside [0, 1]")
            if depth_stats["minimum"] < -tolerance or depth_stats["maximum"] > 1 + tolerance:
                raise RenderInvariantError("depth readback is outside [0, 1]")
            clear_pixels = sum(
                all(abs(color[index + channel] - clear[channel]) <= tolerance for channel in range(4))
                for index in range(0, len(color), 4)
            )
            color_stats["drawnPixels"] = width * height - clear_pixels
            depth_stats["drawnPixels"] = sum(value < 1 - tolerance for value in depth)
            if not color_stats["drawnPixels"] or not depth_stats["drawnPixels"]:
                raise RenderInvariantError("draw did not change both color and depth attachments")
            artifact_paths: dict[str, str] = {}
            if artifacts:
                artifact_paths = _write_artifacts(
                    artifacts, prepared.program, width, height, color, depth,
                    {"program": prepared.program, "fixture": fixture, "color": color_stats, "depth": depth_stats},
                )
            return RenderReport(prepared.program, fixture, width, height, compile_report, sampler >= 0, color_stats, depth_stats, artifact_paths)
    finally:
        gl.use_program(0)
        gl.bind_framebuffer(GL_FRAMEBUFFER, 0)
        for handle_value in (source_texture, color_texture):
            if handle_value:
                handle = ctypes.c_uint(handle_value)
                gl.delete_textures(1, ctypes.byref(handle))
        if depth_buffer.value:
            gl.delete_renderbuffers(1, ctypes.byref(depth_buffer))
        if fbo.value:
            gl.delete_framebuffers(1, ctypes.byref(fbo))
        if vbo.value:
            gl.delete_buffers(1, ctypes.byref(vbo))
        if vao.value:
            gl.delete_vertex_arrays(1, ctypes.byref(vao))


def render_with_hidden_glfw(prepared: PreparedProgram, requested_version: str, requested_profile: str, size: str, fixture: str, artifacts: Path | None) -> RenderReport:
    with create_hidden_glfw_context(requested_version, requested_profile, size) as context:
        return render_current_context(prepared, context.get_proc_address, fixture=fixture, size=size, artifacts=artifacts)
