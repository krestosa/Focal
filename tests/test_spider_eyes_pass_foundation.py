from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_spidereyes.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_spidereyes.fsh"


def test_spider_eyes_program_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_spider_eyes_vertex_stage_has_expected_interfaces() -> None:
    source = VERTEX.read_text(encoding="utf-8")
    assert "#version 120" in source
    assert "gl_Position = ftransform();" in source
    assert "varying vec2 texcoord;" in source
    assert "varying vec4 vertexColor;" in source
    assert "for (" not in source
    assert "while (" not in source


def test_spider_eyes_fragment_stage_is_bounded_and_emissive() -> None:
    source = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 120" in source
    assert "uniform sampler2D texture;" in source
    assert "/* DRAWBUFFERS:0 */" in source
    assert "if (emissive.a < 0.01)" in source
    assert "gl_FragData[0] = emissive;" in source
    assert "for (" not in source
    assert "while (" not in source
