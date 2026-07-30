from __future__ import annotations

from argparse import Namespace

import tools.focal_gl_dispatch as dispatch
from tools.focal_gl import EXIT_CONTEXT_UNAVAILABLE, EXIT_OK, Result, SCHEMA_VERSION, VERSION


def _args(backend: str = "auto") -> Namespace:
    return Namespace(
        command="probe",
        backend=backend,
        gl_version="3.3",
        gl_profile="core",
        size="64x64",
        artifacts=None,
    )


def _result(code: int, message: str, backend: str | None = None) -> Result:
    return Result(
        SCHEMA_VERSION,
        VERSION,
        "probe",
        "PASS" if code == EXIT_OK else "UNSUPPORTED",
        code,
        "STATIC",
        message,
        None,
        {"backend": backend} if backend else None,
    )


def test_explicit_glfw_uses_hidden_context_route(monkeypatch):
    sentinel = _result(EXIT_OK, "glfw ok", "glfw-hidden")
    monkeypatch.setattr(dispatch, "_glfw_probe_result", lambda args: sentinel)
    monkeypatch.setattr(
        dispatch,
        "_probe_result",
        lambda args: (_ for _ in ()).throw(AssertionError("EGL must not run")),
    )

    assert dispatch._dispatch_probe(_args("glfw")) is sentinel


def test_explicit_egl_preserves_existing_route(monkeypatch):
    sentinel = _result(EXIT_OK, "egl ok", "egl-surfaceless")
    monkeypatch.setattr(dispatch, "_probe_result", lambda args: sentinel)
    monkeypatch.setattr(
        dispatch,
        "_glfw_probe_result",
        lambda args: (_ for _ in ()).throw(AssertionError("GLFW must not run")),
    )

    assert dispatch._dispatch_probe(_args("egl")) is sentinel


def test_auto_prefers_egl_when_available(monkeypatch):
    egl = _result(EXIT_OK, "egl ok", "egl-surfaceless")
    monkeypatch.setattr(dispatch, "_probe_result", lambda args: egl)
    monkeypatch.setattr(
        dispatch,
        "_glfw_probe_result",
        lambda args: (_ for _ in ()).throw(AssertionError("GLFW fallback must not run")),
    )

    assert dispatch._dispatch_probe(_args("auto")) is egl


def test_auto_falls_back_to_glfw(monkeypatch):
    egl = _result(EXIT_CONTEXT_UNAVAILABLE, "no egl")
    glfw = _result(EXIT_OK, "glfw ok", "glfw-hidden")
    monkeypatch.setattr(dispatch, "_probe_result", lambda args: egl)
    monkeypatch.setattr(dispatch, "_glfw_probe_result", lambda args: glfw)

    assert dispatch._dispatch_probe(_args("auto")) is glfw


def test_auto_reports_both_backend_failures(monkeypatch):
    monkeypatch.setattr(
        dispatch,
        "_probe_result",
        lambda args: _result(EXIT_CONTEXT_UNAVAILABLE, "no egl"),
    )
    monkeypatch.setattr(
        dispatch,
        "_glfw_probe_result",
        lambda args: _result(EXIT_CONTEXT_UNAVAILABLE, "no glfw"),
    )

    result = dispatch._dispatch_probe(_args("auto"))

    assert result.exitCode == EXIT_CONTEXT_UNAVAILABLE
    assert result.outcome == "UNSUPPORTED"
    assert result.message == "EGL unavailable: no egl; GLFW unavailable: no glfw"


def test_glfw_probe_closes_context_after_query(monkeypatch):
    events: list[str] = []

    class FakeContext:
        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb):
            events.append("close")

    monkeypatch.setattr(dispatch, "create_hidden_glfw_context", lambda *args: FakeContext())
    monkeypatch.setattr(
        dispatch,
        "query_current_glfw_context",
        lambda *args: {"backend": "glfw-hidden", "renderer": "fixture"},
    )

    result = dispatch._glfw_probe_result(_args("glfw"))

    assert result.exitCode == EXIT_OK
    assert result.context == {"backend": "glfw-hidden", "renderer": "fixture"}
    assert events == ["enter", "close"]
