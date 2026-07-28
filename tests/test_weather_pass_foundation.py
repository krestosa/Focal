from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_weather.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_weather.fsh"


def test_weather_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_weather_interfaces_and_output() -> None:
    vertex = VERTEX.read_text(encoding="utf-8")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 120" in vertex
    assert "#version 120" in fragment
    for symbol in ("texcoord", "vertexColor"):
        assert symbol in vertex
        assert symbol in fragment
    assert "gl_Position = ftransform();" in vertex
    assert "texture2D(texture, texcoord)" in fragment
    assert "if (albedo.a < 0.01)" in fragment
    assert "/* DRAWBUFFERS:0 */" in fragment
    assert "gl_FragData[0] = albedo;" in fragment


def test_weather_stages_have_no_loops() -> None:
    for source in (VERTEX.read_text(encoding="utf-8"), FRAGMENT.read_text(encoding="utf-8")):
        assert "for (" not in source
        assert "while (" not in source
        assert "do {" not in source
