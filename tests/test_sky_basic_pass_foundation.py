from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_skybasic.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_skybasic.fsh"


class SkyBasicPassFoundationTests(unittest.TestCase):
    def test_sky_basic_program_has_required_stages(self) -> None:
        self.assertTrue(VERTEX.is_file())
        self.assertTrue(FRAGMENT.is_file())

    def test_vertex_stage_forwards_vertex_color(self) -> None:
        source = VERTEX.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("gl_Position = ftransform();", source)
        self.assertIn("focalSkyColor = gl_Color;", source)
        self.assertNotIn("for (", source)
        self.assertNotIn("while (", source)

    def test_fragment_stage_writes_sky_color(self) -> None:
        source = FRAGMENT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("in vec4 focalSkyColor;", source)
        self.assertIn("/* RENDERTARGETS: 0 */", source)
        self.assertIn("layout(location = 0) out vec4 focalColor;", source)
        self.assertIn("focalColor = focalSkyColor;", source)
        self.assertNotIn("for (", source)
        self.assertNotIn("while (", source)


if __name__ == "__main__":
    unittest.main()
