from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_entities_translucent.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_entities_translucent.fsh"


def test_translucent_entities_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_translucent_entities_interfaces_are_bounded() -> None:
    vertex = VERTEX.read_text(encoding="utf-8")
    fragment = FRAGMENT.read_text(encoding="utf-8")

    assert "#version 150 compatibility" in vertex
    assert "#version 150 compatibility" in fragment
    assert "out vec2 texcoord;" in vertex
    assert "out vec2 lightcoord;" in vertex
    assert "out vec4 vertexColor;" in vertex
    assert "uniform sampler2D texture;" in fragment
    assert "uniform sampler2D lightmap;" in fragment
    assert "layout(location = 0) out vec4 outColor;" in fragment
    assert "discard;" in fragment
    assert "for (" not in vertex + fragment
    assert "while (" not in vertex + fragment
