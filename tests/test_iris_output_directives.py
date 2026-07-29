import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "spec" / "iris-output-directives.json"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_has_primary_sources_and_schema() -> None:
    contract = load_contract()
    assert contract["schemaVersion"] == 1
    assert len(contract["sources"]) >= 7
    assert all(source.startswith("https://shaders.properties/") for source in contract["sources"])


def test_rendertargets_is_preferred_and_outputs_are_total() -> None:
    directive = load_contract()["directives"]["rendertargets"]
    assert directive["preferred"] is True
    assert directive["requiresMultilineComment"] is True
    assert directive["defaultWhenAbsent"] == list(range(8))
    assert directive["outputMapping"] == "declared-order"
    assert directive["allBoundOutputsMustBeWritten"] is True


def test_drawbuffers_is_legacy_and_bounded() -> None:
    directive = load_contract()["directives"]["drawbuffers"]
    assert directive["legacy"] is True
    assert directive["indices"] == {"minimum": 0, "maximum": 9}
    assert directive["fallback"] == "RENDERTARGETS"


def test_persistent_buffers_require_clear_and_initialization_rules() -> None:
    directives = load_contract()["directives"]
    assert directives["clear"]["persistentHistoryRequiresFalse"] is True
    assert directives["clear"]["historyAlsoRequiresExplicitInitialization"] is True
    assert directives["clearColor"]["componentsRequired"] == 4


def test_safe_profile_has_portable_output_and_blend_fallbacks() -> None:
    safe = load_contract()["safeProfile"]
    assert safe["useRendertargets"] is True
    assert safe["maximumColorAttachmentIndex"] == 7
    assert safe["requireAllDeclaredOutputsWritten"] is True
    assert safe["perBufferBlendingOptional"] is True
    assert safe["fallbackOnMissingPerBufferBlending"] == (
        "program-level blending or disabled blending"
    )
