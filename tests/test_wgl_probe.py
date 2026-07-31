from __future__ import annotations

import unittest
from argparse import Namespace
from unittest import mock

import tools.focal_gl_worker as worker
import tools.wgl_context as context
import tools.wgl_dispatch as dispatch
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


class WglProbeTests(unittest.TestCase):
    def test_non_windows_wgl_is_reported_as_unavailable(self) -> None:
        with mock.patch.object(context.sys, "platform", "linux"):
            with self.assertRaisesRegex(context.WglContextUnavailable, "only on Windows"):
                context.create_hidden_wgl_context("3.3", "core", "64x64")

    def test_wgl_probe_queries_and_closes_context(self) -> None:
        events: list[str] = []

        class FakeContext:
            def __enter__(self):
                events.append("enter")
                return self

            def __exit__(self, exc_type, exc, tb):
                events.append("close")

        with (
            mock.patch.object(
                dispatch,
                "create_hidden_wgl_context",
                side_effect=lambda *args: FakeContext(),
            ),
            mock.patch.object(
                dispatch,
                "query_current_wgl_context",
                return_value={"backend": "wgl-hidden", "renderer": "fixture"},
            ),
        ):
            result = dispatch.wgl_probe_result(_args())

        self.assertEqual(result.exitCode, EXIT_OK)
        self.assertEqual(result.context, {"backend": "wgl-hidden", "renderer": "fixture"})
        self.assertEqual(events, ["enter", "close"])

    def test_wgl_probe_maps_context_failure(self) -> None:
        with mock.patch.object(
            dispatch,
            "create_hidden_wgl_context",
            side_effect=context.WglContextUnavailable("no WGL"),
        ):
            result = dispatch.wgl_probe_result(_args())

        self.assertEqual(result.exitCode, EXIT_CONTEXT_UNAVAILABLE)
        self.assertEqual(result.outcome, "UNSUPPORTED")
        self.assertEqual(result.message, "no WGL")

    def test_isolated_worker_routes_only_explicit_wgl_probe(self) -> None:
        sentinel = type("Sentinel", (), {"exitCode": 0})()
        with (
            mock.patch.object(dispatch, "wgl_probe_result", return_value=sentinel),
            mock.patch.object(worker, "emit"),
        ):
            self.assertEqual(worker._dispatch_isolated(["probe", "--backend", "wgl"]), 0)


if __name__ == "__main__":
    unittest.main()
