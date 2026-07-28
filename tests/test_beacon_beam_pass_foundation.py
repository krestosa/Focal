from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERTEX = ROOT / "shaders" / "gbuffers_beaconbeam.vsh"
FRAGMENT = ROOT / "shaders" / "gbuffers_beaconbeam.fsh"


def test_beacon_beam_program_stages_exist() -> None:
    assert VERTEX.is_file()
    assert FRAGMENT.is_file()


def test_beacon_beam_vertex_stage_has_expected_interfaces() -> None:
    source = VERTEX.read_text(encoding="utf-8")
    assert "#version 120" in source
    assert "gl_Position = ftransform();" in source
    assert "varying vec2 texcoord;" in source
    assert "varying vec4 vertexColor;" in source
    assert "for (" not in source
    assert "while (" not in source


def test_beacon_beam_fragment_stage_is_bounded_and_translucent() -> None:
    source = FRAGMENT.read_text(encoding="utf-8")
    assert "#version 120" in source
    assert "uniform sampler2D texture;" in source
    assert "/* DRAWBUFFERS:0 */" in source
    assert "if (beam.a < 0.01)" in source
    assert "gl_FragData[0] = beam;" in source
    assert "for (" not in source
    assert "while (" not in source
