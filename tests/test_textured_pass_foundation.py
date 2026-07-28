from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_textured.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_textured.fsh"


class TexturedPassFoundationTests(unittest.TestCase):
    def test_textured_program_has_required_stages(self) -> None:
        self.assertTrue(VERTEX.is_file())
        self.assertTrue(FRAGMENT.is_file())

    def test_vertex_stage_forwards_texture_coordinates_and_color(self) -> None:
        source = VERTEX.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("gl_Position = ftransform();", source)
        self.assertIn("focalTexCoord = gl_MultiTexCoord0.xy;", source)
        self.assertIn("focalVertexColor = gl_Color;", source)
        self.assertNotIn("for (", source)
        self.assertNotIn("while (", source)

    def test_fragment_stage_samples_tints_and_alpha_tests(self) -> None:
        source = FRAGMENT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("uniform sampler2D texture;", source)
        self.assertIn("texture2D(texture, focalTexCoord)", source)
        self.assertIn("* focalVertexColor", source)
        self.assertIn("if (albedo.a < 0.1)", source)
        self.assertIn("discard;", source)
        self.assertIn("/* RENDERTARGETS: 0 */", source)
        self.assertIn("layout(location = 0) out vec4 focalColor;", source)
        self.assertNotIn("for (", source)
        self.assertNotIn("while (", source)


if __name__ == "__main__":
    unittest.main()
