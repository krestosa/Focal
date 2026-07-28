from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_hand_water.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_hand_water.fsh"


def test_hand_water_program_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_hand_water_interfaces_and_output() -> None:
    vertex = VERTEX.read_text(encoding="utf-8")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 120" in vertex
    assert "#version 120" in fragment
    for symbol in ("texcoord", "lightcoord", "vertexColor"):
        assert symbol in vertex
        assert symbol in fragment
    assert "/* DRAWBUFFERS:0 */" in fragment
    assert "texture2D(texture, texcoord)" in fragment
    assert "texture2D(lightmap, lightcoord)" in fragment
    assert "if (albedo.a < 0.1)" in fragment
    assert "gl_FragData[0]" in fragment


def test_hand_water_stages_have_no_loops() -> None:
    for source in (VERTEX.read_text(encoding="utf-8"), FRAGMENT.read_text(encoding="utf-8")):
        assert "for (" not in source
        assert "while (" not in source
        assert "do {" not in source
