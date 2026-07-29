from pathlib import Path

from tools.shader_inventory import (
    inventory,
    is_recognized_program,
    render_payload,
    validation_errors,
)


ROOT = Path(__file__).resolve().parents[1]


def test_current_shader_tree_has_recognized_complete_programs() -> None:
    records = inventory(ROOT / "shaders")
    assert records
    assert validation_errors(records) == []
    payload = render_payload(records)
    assert payload["valid"] is True
    assert payload["programCount"] == len(records)
    assert payload["stageFileCount"] >= len(records) * 2


def test_repeatable_pass_suffixes_are_bounded() -> None:
    assert is_recognized_program("composite1")
    assert is_recognized_program("deferred99")
    assert not is_recognized_program("composite0")
    assert not is_recognized_program("prepare100")


def test_inventory_reports_unknown_and_incomplete_pairs(tmp_path: Path) -> None:
    shader_dir = tmp_path / "shaders"
    shader_dir.mkdir()
    (shader_dir / "gbuffers_basic.vsh").write_text("#version 120\n", encoding="utf-8")
    (shader_dir / "mystery.fsh").write_text("#version 120\n", encoding="utf-8")

    errors = validation_errors(inventory(shader_dir))
    assert "incomplete vertex/fragment pair: gbuffers_basic (vsh)" in errors
    assert "unrecognized program: mystery" in errors
    assert "incomplete vertex/fragment pair: mystery (fsh)" in errors
