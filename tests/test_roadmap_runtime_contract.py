from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "ROADMAP.md"
MATRIX = ROOT / "docs" / "IRIS-CAPABILITY-MATRIX.md"
HARNESS = ROOT / "docs" / "OPENGL-RUNTIME-HARNESS.md"

ALLOWED_IRIS_PREFIXES = (
    "https://shaders.properties/current/reference/",
    "https://github.com/IrisShaders/Iris",
    "https://github.com/IrisShaders/docs",
    "https://github.com/IrisShaders/ShaderDoc",
)


class RoadmapRuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.roadmap = ROADMAP.read_text(encoding="utf-8")
        cls.matrix = MATRIX.read_text(encoding="utf-8")
        cls.harness = HARNESS.read_text(encoding="utf-8")

    def test_required_documents_exist(self) -> None:
        self.assertTrue(ROADMAP.is_file())
        self.assertTrue(MATRIX.is_file())
        self.assertTrue(HARNESS.is_file())

    def test_feature_rows_are_detailed_and_have_iris_docs(self) -> None:
        rows = [
            line
            for line in self.roadmap.splitlines()
            if re.match(r"^\| \[(?: |x)\] [^|]+`[A-Z][A-Z0-9-]+` \|", line)
        ]
        self.assertGreaterEqual(len(rows), 50)

        identifiers: list[str] = []
        for row in rows:
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            self.assertGreaterEqual(len(cells), 6, row)
            identifier_match = re.search(r"`([A-Z][A-Z0-9-]+)`", cells[0])
            self.assertIsNotNone(identifier_match, row)
            identifiers.append(identifier_match.group(1))
            self.assertGreaterEqual(len(cells[2]), 20, f"missing observable scope: {row}")
            self.assertGreaterEqual(len(cells[3]), 20, f"missing acceptance/tests: {row}")
            self.assertIn("]", cells[4], f"missing Iris documentation link: {row}")
            self.assertGreaterEqual(len(cells[5]), 8, f"missing dependency or next action: {row}")

        self.assertEqual(len(identifiers), len(set(identifiers)), "roadmap feature IDs must be unique")

    def test_official_iris_reference_links_are_primary(self) -> None:
        definitions = re.findall(r"^\[[^]]+\]:\s+(https://\S+)$", self.roadmap, flags=re.MULTILINE)
        self.assertGreaterEqual(len(definitions), 20)
        for url in definitions:
            self.assertTrue(url.startswith(ALLOWED_IRIS_PREFIXES), url)

    def test_terminal_harness_feature_family_is_complete(self) -> None:
        required = ["QA-003"] + [f"GLCLI-{number:03d}" for number in range(1, 9)]
        for identifier in required:
            self.assertIn(f"`{identifier}`", self.roadmap)

        self.assertIn("`GLCLI-001 — Stable terminal interface`", self.roadmap)
        self.assertIn("focal-gl", self.roadmap)
        self.assertIn("GL_RENDER_READBACK", self.roadmap)

    def test_matrix_tracks_terminal_opengl_capability(self) -> None:
        self.assertIn("`IRIS-GL-005`", self.matrix)
        self.assertIn("OPENGL-RUNTIME-HARNESS.md", self.matrix)
        self.assertIn("GL_COMPILE_LINK", self.matrix)
        self.assertIn("GL_RENDER_READBACK", self.matrix)
        self.assertIn("Iris Patcher", self.matrix)

    def test_harness_commands_and_exit_codes_are_versioned(self) -> None:
        for command in ("probe", "compile", "render", "suite"):
            self.assertIn(f"focal-gl {command}", self.harness)

        for code in (0, 2, 3, 4, 5, 6, 7, 8):
            self.assertRegex(self.harness, rf"- `{code}`:")

        for level in (
            "STATIC",
            "GL_COMPILE_LINK",
            "GL_RENDER_READBACK",
            "IRIS_PATCHED",
            "IRIS_CLIENT",
        ):
            self.assertIn(level, self.harness)

    def test_runtime_contract_requires_real_context_and_readback(self) -> None:
        required_phrases = (
            "real OpenGL context",
            "framebuffer",
            "read color and depth output",
            "isolated worker process",
            "Mesa software OpenGL",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, self.harness)


if __name__ == "__main__":
    unittest.main()
