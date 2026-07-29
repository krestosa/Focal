import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools import focal_gl

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "focal-gl"


class FocalGlCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(ENTRYPOINT), *args], cwd=ROOT, text=True, capture_output=True, timeout=10, check=False)

    def test_stable_exit_code_meanings(self) -> None:
        self.assertEqual(focal_gl.EXIT_CODES, {0:"all required checks passed",2:"invalid usage or configuration",3:"OpenGL context unavailable",4:"shader compilation or link failure",5:"OpenGL, framebuffer or execution failure",6:"output invariant failure",7:"timeout, worker termination or context loss",8:"required capability unsupported without accepted fallback"})

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
                self.assertEqual(payload["harnessVersion"], "0.2.0")
                self.assertEqual(payload["command"], command)
                self.assertEqual(payload["outcome"], "UNSUPPORTED")
                self.assertEqual(payload["evidenceLevel"], "STATIC")

    def test_unimplemented_backend_is_factual_unsupported(self) -> None:
        result = self.run_cli("probe", "--backend", "wgl", "--json")
        self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["outcome"], "UNSUPPORTED")
        self.assertIsNone(payload["context"])

    def test_egl_probe_reports_real_context_or_factual_unavailability(self) -> None:
        result = self.run_cli("probe", "--backend", "egl", "--json")
        self.assertIn(result.returncode, (focal_gl.EXIT_OK, focal_gl.EXIT_CONTEXT_UNAVAILABLE), result.stderr)
        payload = json.loads(result.stdout)
        if result.returncode == focal_gl.EXIT_OK:
            self.assertEqual(payload["outcome"], "PASS")
            context = payload["context"]
            self.assertIn(context["backend"], ("egl-surfaceless", "egl-default"))
            for key in ("vendor", "renderer", "version", "glslVersion"):
                self.assertTrue(context[key], key)
            self.assertGreater(context["limits"]["maxColorAttachments"], 0)
            self.assertGreater(context["limits"]["maxTextureSize"], 0)
        else:
            self.assertEqual(payload["outcome"], "UNSUPPORTED")
            self.assertIsNone(payload["context"])
            self.assertTrue(payload["message"])

    def test_common_contract_arguments_parse(self) -> None:
        result = self.run_cli("compile", "--pack", "shaders", "--program", "gbuffers_basic", "--fixture", "triangle", "--profile", "BALANCED", "--dimension", "the_nether", "--backend", "egl", "--gl-version", "4.3", "--gl-profile", "core", "--size", "640x360", "--frames", "2", "--timeout", "5", "--source-mode", "preprocessed", "--json")
        self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        self.assertEqual(json.loads(result.stdout)["command"], "compile")


if __name__ == "__main__":
    unittest.main()
