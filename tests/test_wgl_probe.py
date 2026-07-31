from __future__ import annotations

from argparse import Namespace

import pytest

import tools.focal_gl_worker as worker
import tools.wgl_dispatch as dispatch
import tools.wgl_context as context
from tools.focal_gl import EXIT_CONTEXT_UNAVAILABLE, EXIT_OK


def _args() -> Namespace:
    return Namespace(
        command="probe",
        backend="wgl",
        gl_version="3.3",
        gl_profile="core",
        size="64x64",
        artifacts=None,
        json_output=False,
    )


def test_non_windows_wgl_is_reported_as_unavailable(monkeypatch):
    monkeypatch.setattr(context.sys, "platform", "linux")

    with pytest.raises(context.WglContextUnavailable, match="only on Windows"):
        context.create_hidden_wgl_context("3.3", "core", "64x64")


def test_wgl_probe_queries_and_closes_context(monkeypatch):
    events: list[str] = []

    class FakeContext:
        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb):
            events.append("close")

    monkeypatch.setattr(dispatch, "create_hidden_wgl_context", lambda *args: FakeContext())
    monkeypatch.setattr(
        dispatch,
        "query_current_wgl_context",
        lambda *args: {"backend": "wgl-hidden", "renderer": "fixture"},
    )

    result = dispatch.wgl_probe_result(_args())

    assert result.exitCode == EXIT_OK
    assert result.context == {"backend": "wgl-hidden", "renderer": "fixture"}
    assert events == ["enter", "close"]


def test_wgl_probe_maps_context_failure(monkeypatch):
    monkeypatch.setattr(
        dispatch,
        "create_hidden_wgl_context",
        lambda *args: (_ for _ in ()).throw(context.WglContextUnavailable("no WGL")),
    )

    result = dispatch.wgl_probe_result(_args())

    assert result.exitCode == EXIT_CONTEXT_UNAVAILABLE
    assert result.outcome == "UNSUPPORTED"
    assert result.message == "no WGL"


def test_isolated_worker_routes_only_explicit_wgl_probe(monkeypatch):
    sentinel = type("Sentinel", (), {"exitCode": 0})()
    monkeypatch.setattr(dispatch, "wgl_probe_result", lambda args: sentinel)
    monkeypatch.setattr(worker, "emit", lambda result, json_output: None)

    assert worker._dispatch_isolated(["probe", "--backend", "wgl"]) == 0
