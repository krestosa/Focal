import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "iris-stage-capabilities.json"
SHADERS = ROOT / "shaders"


def load_spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def test_stage_spec_has_supported_extensions_and_safe_baseline() -> None:
    spec = load_spec()
    stages = spec["stages"]
    assert set(stages) == {"vsh", "fsh", "gsh", "csh", "tcs", "tes"}
    assert stages["vsh"]["safe"] is True
    assert stages["fsh"]["safe"] is True
    assert all(stages[name]["safe"] is False for name in ("gsh", "csh", "tcs", "tes"))


def test_compute_constraints_are_bounded_and_macos_safe() -> None:
    spec = load_spec()
    compute = spec["stages"]["csh"]
    assert compute["minimumOpenGL"] == "4.3"
    assert compute["macosOpenGL"] is False
    assert compute["programFamilies"] == ["setup", "composite"]
    assert compute["featureFlag"] == "COMPUTE_SHADERS"
    assert spec["compute"]["perPassFiles"] == 27
    assert len(spec["compute"]["suffixes"]) == 27
    assert spec["compute"]["suffixes"][0] == ""
    assert spec["compute"]["suffixes"][-1] == "_z"


def test_tessellation_requires_paired_triangle_stages_and_fallback() -> None:
    stages = load_spec()["stages"]
    for name in ("tcs", "tes"):
        assert stages[name]["programFamilies"] == ["gbuffers"]
        assert stages[name]["primitive"] == "triangles"
        assert stages[name]["featureFlag"] == "TESSELLATION_SHADERS"
        assert stages[name]["fallback"] == "vertex-fragment path"


def test_current_shader_tree_uses_only_declared_stage_extensions() -> None:
    declared = set(load_spec()["stages"])
    actual = {path.suffix.removeprefix(".") for path in SHADERS.rglob("*") if path.is_file() and path.suffix in {".vsh", ".fsh", ".gsh", ".csh", ".tcs", ".tes"}}
    assert actual <= declared
