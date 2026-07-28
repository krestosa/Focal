from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_block.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_block.fsh"


def test_block_entity_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_block_entity_interfaces_and_output() -> None:
    vertex = VERTEX.read_text(encoding="utf-8")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 150 compatibility" in vertex
    assert "#version 150 compatibility" in fragment
    for symbol in ("focalTexCoord", "focalLightCoord", "focalVertexColor"):
        assert symbol in vertex
        assert symbol in fragment
    assert "/* DRAWBUFFERS:0 */" in fragment
    assert "layout(location = 0) out vec4 focalColor;" in fragment
    assert "texture2D(texture, focalTexCoord)" in fragment
    assert "texture2D(lightmap, focalLightCoord)" in fragment
    assert "if (albedo.a < 0.1)" in fragment


def test_block_entity_stages_have_no_loops() -> None:
    for source in (VERTEX.read_text(encoding="utf-8"), FRAGMENT.read_text(encoding="utf-8")):
        assert "for (" not in source
        assert "while (" not in source
        assert "do {" not in source
