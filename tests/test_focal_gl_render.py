from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import tools.focal_gl_dispatch as dispatch
from tools.focal_gl import (
    EXIT_INVARIANT,
    EXIT_OK,
    EXIT_OPENGL_EXECUTION,
    EXIT_UNSUPPORTED,
    EXIT_USAGE,
)
from tools.focal_gl_render import RenderExecutionError, RenderInvariantError


class _Prepared:
    def metadata(self):
        return {"program": "fixture", "sourceMode": "preprocessed"}


class _Report:
    def metadata(self):
        return {
            "backend": "glfw-hidden",
            "framebufferStatus": "GL_FRAMEBUFFER_COMPLETE",
            "color": {"finite": True, "drawnPixels": 4},
            "depth": {"finite": True, "drawnPixels": 4},
        }


def _args(**overrides) -> Namespace:
    values = {
        "command": "render",
        "backend": "glfw",
        "gl_version": "3.3",
        "gl_profile": "core",
        "size": "4x4",
        "artifacts": None,
        "pack": Path("."),
        "program": "fixture",
        "fixture": "fullscreen",
        "profile": "SAFE",
        "dimension": "overworld",
        "source_mode": "preprocessed",
    }
    values.update(overrides)
    return Namespace(**values)


def test_render_requires_fixture(monkeypatch):
    monkeypatch.setattr(dispatch, "_prepare_sources", lambda _args: _Prepared())
    result = dispatch._render_result(_args(fixture=None))
    assert result.exitCode == EXIT_USAGE
    assert result.outcome == "INVALID"
    assert "requires --fixture" in result.message


def test_render_rejects_unimplemented_backend(monkeypatch):
    monkeypatch.setattr(dispatch, "_prepare_sources", lambda _args: _Prepared())
    result = dispatch._render_result(_args(backend="egl"))
    assert result.exitCode == EXIT_UNSUPPORTED
    assert result.outcome == "UNSUPPORTED"


def test_render_success_reports_readback_evidence(monkeypatch):
    monkeypatch.setattr(dispatch, "_prepare_sources", lambda _args: _Prepared())
    monkeypatch.setattr(dispatch, "render_with_hidden_glfw", lambda *args: _Report())
    result = dispatch._render_result(_args())
    assert result.exitCode == EXIT_OK
    assert result.outcome == "PASS"
    assert result.evidenceLevel == "GL_RENDER_READBACK"
    assert result.context["render"]["framebufferStatus"] == "GL_FRAMEBUFFER_COMPLETE"


def test_render_maps_execution_failure(monkeypatch):
    monkeypatch.setattr(dispatch, "_prepare_sources", lambda _args: _Prepared())
    monkeypatch.setattr(
        dispatch,
        "render_with_hidden_glfw",
        lambda *args: (_ for _ in ()).throw(RenderExecutionError("framebuffer failed")),
    )
    result = dispatch._render_result(_args())
    assert result.exitCode == EXIT_OPENGL_EXECUTION
    assert result.evidenceLevel == "GL_COMPILE_LINK"


def test_render_maps_invariant_failure(monkeypatch):
    monkeypatch.setattr(dispatch, "_prepare_sources", lambda _args: _Prepared())
    monkeypatch.setattr(
        dispatch,
        "render_with_hidden_glfw",
        lambda *args: (_ for _ in ()).throw(RenderInvariantError("NaN")),
    )
    result = dispatch._render_result(_args())
    assert result.exitCode == EXIT_INVARIANT
    assert result.evidenceLevel == "GL_RENDER_READBACK"
