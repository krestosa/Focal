import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tools import focal_gl
from tools.focal_gl_context import ContextUnavailable


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "focal-gl"


class FocalGlCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ENTRYPOINT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def test_stable_exit_code_meanings(self) -> None:
        self.assertEqual(
            focal_gl.EXIT_CODES,
            {
                0: "all required checks passed",
                2: "invalid usage or configuration",
                3: "OpenGL context unavailable",
                4: "shader compilation or link failure",
                5: "OpenGL, framebuffer or execution failure",
                6: "output invariant failure",
                7: "timeout, worker termination or context loss",
                8: "required capability unsupported without accepted fallback",
            },
        )

    def test_help_lists_all_commands(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("probe", "compile", "render", "suite"):
            self.assertIn(command, result.stdout)

    def test_version_is_stable(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "focal-gl 0.2.0")

    def test_missing_command_is_usage_error(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        self.assertIn("required", result.stderr)

    def test_invalid_size_is_usage_error(self) -> None:
        result = self.run_cli("probe", "--size", "0x32")
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        self.assertIn("dimensions", result.stderr)

    def test_non_probe_commands_remain_factual_unsupported(self) -> None:
        for command in ("compile", "render", "suite"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--json", "--artifacts", "artifacts")
                self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["schemaVersion"], 1)
                self.assertEqual(payload["harnessVersion"], "0.2.0")
                self.assertEqual(payload["command"], command)
                self.assertEqual(payload["outcome"], "UNSUPPORTED")
                self.assertEqual(payload["exitCode"], 3)
                self.assertEqual(payload["evidenceLevel"], "STATIC")
                self.assertEqual(payload["artifacts"], "artifacts")

    def test_common_contract_arguments_parse(self) -> None:
        result = self.run_cli(
            "compile",
            "--pack", "shaders",
            "--program", "gbuffers_basic",
            "--fixture", "triangle",
            "--profile", "BALANCED",
            "--dimension", "the_nether",
            "--backend", "egl",
            "--gl-version", "4.3",
            "--gl-profile", "core",
            "--size", "640x360",
            "--frames", "2",
            "--timeout", "5",
            "--source-mode", "preprocessed",
            "--json",
        )
        self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        self.assertEqual(json.loads(result.stdout)["command"], "compile")

    def test_probe_success_reports_real_context_details(self) -> None:
        details = {
            "backend": "egl-pbuffer",
            "egl": {"vendor": "Mesa Project"},
            "gl": {
                "vendor": "Mesa",
                "renderer": "llvmpipe",
                "version": "4.5",
                "glslVersion": "4.50",
                "profile": "core",
                "extensions": [],
                "limits": {"maxColorAttachments": 8},
                "capabilities": {"computeShader": True},
            },
        }
        output = io.StringIO()
        with mock.patch.object(focal_gl, "probe_context", return_value=details), redirect_stdout(output):
            exit_code = focal_gl.main(["probe", "--backend", "egl", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, focal_gl.EXIT_OK)
        self.assertEqual(payload["outcome"], "PASS")
        self.assertEqual(payload["details"], details)
        self.assertEqual(payload["evidenceLevel"], "GL_CONTEXT")

    def test_probe_failure_is_context_unavailable(self) -> None:
        output = io.StringIO()
        with mock.patch.object(
            focal_gl,
            "probe_context",
            side_effect=ContextUnavailable("EGL loader was not found"),
        ), redirect_stdout(output):
            exit_code = focal_gl.main(["probe", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        self.assertEqual(payload["outcome"], "UNSUPPORTED")
        self.assertIn("EGL loader", payload["message"])


if __name__ == "__main__":
    unittest.main()
