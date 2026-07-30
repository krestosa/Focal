import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import focal_gl

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
        self.assertEqual(result.stdout.strip(), "focal-gl 0.3.0")

    def test_missing_command_is_usage_error(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        self.assertIn("required", result.stderr)

    def test_invalid_size_is_usage_error(self) -> None:
        result = self.run_cli("probe", "--size", "0x32")
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        self.assertIn("dimensions", result.stderr)

    def test_render_requires_program_and_fixture(self) -> None:
        result = self.run_cli("render", "--json", "--artifacts", "artifacts")
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["harnessVersion"], "0.3.0")
        self.assertEqual(payload["command"], "render")
        self.assertEqual(payload["outcome"], "INVALID")
        self.assertEqual(payload["evidenceLevel"], "STATIC")
        self.assertIn("requires --program", payload["message"])

    def test_suite_remains_factual_unsupported(self) -> None:
        result = self.run_cli("suite", "--json", "--artifacts", "artifacts")
        self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["harnessVersion"], "0.3.0")
        self.assertEqual(payload["command"], "suite")
        self.assertEqual(payload["outcome"], "UNSUPPORTED")
        self.assertEqual(payload["evidenceLevel"], "STATIC")

    def test_compile_preserves_source_metadata_for_unimplemented_backend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shaders = root / "shaders"
            shaders.mkdir()
            (shaders / "common.glsl").write_text("const float VALUE = 1.0;\n", encoding="utf-8")
            (shaders / "example.vsh").write_text(
                '#version 330 core\n#include "common.glsl"\nvoid main() { gl_Position = vec4(VALUE); }\n',
                encoding="utf-8",
            )
            (shaders / "example.fsh").write_text(
                "#version 330 core\nout vec4 fragColor;\nvoid main() { fragColor = vec4(1.0); }\n",
                encoding="utf-8",
            )
            result = self.run_cli(
                "compile",
                "--pack",
                str(root),
                "--program",
                "example",
                "--profile",
                "BALANCED",
                "--dimension",
                "the_nether",
                "--source-mode",
                "preprocessed",
                "--backend",
                "egl",
                "--json",
            )
        self.assertEqual(result.returncode, focal_gl.EXIT_UNSUPPORTED, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["outcome"], "UNSUPPORTED")
        self.assertEqual(payload["evidenceLevel"], "STATIC")
        preparation = payload["context"]["sourcePreparation"]
        self.assertEqual(preparation["sourceMode"], "preprocessed")
        self.assertTrue(preparation["includesResolved"])
        self.assertEqual(
            preparation["defines"],
            {"FOCAL_DIMENSION_THE_NETHER": "1", "FOCAL_PROFILE_BALANCED": "1"},
        )
        self.assertEqual([item["stage"] for item in preparation["stages"]], ["vsh", "fsh"])
        self.assertTrue(all(len(item["sha256"]) == 64 for item in preparation["stages"]))
        self.assertTrue(all("source" not in item for item in preparation["stages"]))
        self.assertIn("use glfw or auto", payload["message"])

    def test_compile_invalid_request_is_usage_error(self) -> None:
        result = self.run_cli("compile", "--json")
        self.assertEqual(result.returncode, focal_gl.EXIT_USAGE)
        self.assertEqual(json.loads(result.stdout)["outcome"], "INVALID")

    def test_unimplemented_backend_is_factual_unsupported(self) -> None:
        result = self.run_cli("probe", "--backend", "wgl", "--json")
        self.assertEqual(result.returncode, focal_gl.EXIT_CONTEXT_UNAVAILABLE)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["outcome"], "UNSUPPORTED")
        self.assertIsNone(payload["context"])

    def test_core_extension_enumeration_uses_gl_get_string_i(self) -> None:
        extensions, api = focal_gl._enumerate_extensions(
            lambda _enum: None,
            lambda enum: 3 if enum == focal_gl.GL_NUM_EXTENSIONS else 0,
            lambda _enum, index: (b"GL_EXT_beta", b"GL_EXT_alpha", b"GL_EXT_alpha")[index],
        )
        self.assertEqual(api, "glGetStringi")
        self.assertEqual(extensions, ["GL_EXT_alpha", "GL_EXT_beta"])

    def test_legacy_extension_enumeration_is_controlled_fallback(self) -> None:
        extensions, api = focal_gl._enumerate_extensions(
            lambda enum: b"GL_EXT_beta GL_EXT_alpha GL_EXT_alpha"
            if enum == focal_gl.GL_EXTENSIONS
            else None,
            lambda _enum: 0,
            None,
        )
        self.assertEqual(api, "glGetString")
        self.assertEqual(extensions, ["GL_EXT_alpha", "GL_EXT_beta"])

    def test_extension_enumeration_fails_factually_without_either_api(self) -> None:
        with self.assertRaisesRegex(focal_gl.ContextUnavailable, "extension enumeration is unavailable"):
            focal_gl._enumerate_extensions(lambda _enum: None, lambda _enum: 0, None)

    def test_egl_probe_reports_real_context_or_factual_unavailability(self) -> None:
        result = self.run_cli("probe", "--backend", "egl", "--json")
        self.assertIn(result.returncode, (focal_gl.EXIT_OK, focal_gl.EXIT_CONTEXT_UNAVAILABLE), result.stderr)
        payload = json.loads(result.stdout)
        if result.returncode == focal_gl.EXIT_OK:
            self.assertEqual(payload["outcome"], "PASS")
            context = payload["context"]
            self.assertIn(context["backend"], ("egl-surfaceless", "egl-default"))
            self.assertIn(context["extensionEnumeration"], ("glGetStringi", "glGetString"))
            for key in ("vendor", "renderer", "version", "glslVersion"):
                self.assertTrue(context[key], key)
            self.assertGreater(context["limits"]["maxColorAttachments"], 0)
            self.assertGreater(context["limits"]["maxTextureSize"], 0)
            self.assertEqual(context["limits"]["numExtensions"], len(context["extensions"]))
        else:
            self.assertEqual(payload["outcome"], "UNSUPPORTED")
            self.assertIsNone(payload["context"])
            self.assertTrue(payload["message"])


if __name__ == "__main__":
    unittest.main()
