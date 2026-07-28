from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_clouds.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_clouds.fsh"


def test_clouds_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_clouds_vertex_interface() -> None:
    source = VERTEX.read_text(encoding="utf-8")
    assert "#version 150" in source
    assert "out vec2 cloudTexCoord;" in source
    assert "out vec4 cloudColor;" in source
    assert "gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex" in source
    assert "for (" not in source
    assert "while (" not in source


def test_clouds_fragment_interface() -> None:
    source = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 150" in source
    assert "uniform sampler2D texture;" in source
    assert "in vec2 cloudTexCoord;" in source
    assert "in vec4 cloudColor;" in source
    assert "layout(location = 0) out vec4 outColor;" in source
    assert "texture2D(texture, cloudTexCoord) * cloudColor" in source
    assert "sampled.a <= 0.001" in source
    assert "for (" not in source
    assert "while (" not in source
