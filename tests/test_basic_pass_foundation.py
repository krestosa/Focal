from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_basic.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_basic.fsh"


class BasicPassFoundationTests(unittest.TestCase):
    def test_basic_program_has_required_stages(self) -> None:
        self.assertTrue(VERTEX.is_file())
        self.assertTrue(FRAGMENT.is_file())

    def test_vertex_stage_forwards_clip_position_and_vertex_color(self) -> None:
        source = VERTEX.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("gl_Position = ftransform();", source)
        self.assertIn("focalVertexColor = gl_Color;", source)
        self.assertNotIn("texture(", source)

    def test_fragment_stage_writes_untextured_vertex_color(self) -> None:
        source = FRAGMENT.read_text(encoding="utf-8")

        self.assertTrue(source.startswith("#version 330 compatibility\n"))
        self.assertIn("/* RENDERTARGETS: 0 */", source)
        self.assertIn("layout(location = 0) out vec4 focalColor;", source)
        self.assertIn("focalColor = focalVertexColor;", source)
        self.assertNotIn("uniform sampler", source)
        self.assertNotIn("texture(", source)
        self.assertNotIn("while (", source)
        self.assertNotIn("for (", source)


if __name__ == "__main__":
    unittest.main()
