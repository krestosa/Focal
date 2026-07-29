import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "spec" / "iris-buffer-lifecycle.json"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_has_primary_sources_and_schema() -> None:
    data = load_contract()
    assert data["schemaVersion"] == 1
    assert len(data["sources"]) >= 8
    assert all(source.startswith("https://shaders.properties/") for source in data["sources"])


def test_safe_color_attachment_policy_is_portable() -> None:
    color = load_contract()["colorAttachments"]
    safe = color["safePolicy"]
    assert color["minimumPortableCount"] >= 16
    assert safe["maximumRequiredIndex"] <= 7
    assert safe["historyRequiresClearDisabled"] is True
    assert safe["historyRequiresExplicitResetProtocol"] is True
    assert safe["resizedAttachmentsForbiddenForGbuffersOutputs"] is True


def test_color_ping_pong_and_resize_rules_are_explicit() -> None:
    data = load_contract()
    color = data["colorAttachments"]
    ping_pong = data["pingPong"]
    assert color["doubleBuffered"] is True
    assert color["computeOnlyPassTriggersFlip"] is False
    assert color["resizedBufferGbuffersWritable"] is False
    assert color["samePassOutputSizesMustMatch"] is True
    assert ping_pong["swapAfterProgramByDefault"] is True
    assert ping_pong["noFragmentStageMeansNoAutomaticFlip"] is True


def test_depth_buffers_do_not_claim_configurable_lifecycle() -> None:
    depth = load_contract()["depthAttachments"]
    assert depth["count"] == 3
    assert depth["clearConfigurable"] is False
    assert depth["flips"] is False
    assert depth["resolution"] == "display-fixed"
    assert depth["manualWriteRequiresAllPaths"] is True


def test_shadow_depth_rules_and_fallbacks_are_bounded() -> None:
    data = load_contract()
    shadow = data["shadowDepthAttachments"]
    fallback = data["fallbacks"]
    assert shadow["count"] == 2
    assert shadow["clearConfigurable"] is False
    assert shadow["flips"] is False
    assert shadow["mipmapsSupported"] is True
    assert shadow["separateHardwareSamplersRequireFlag"] == "SEPARATE_HARDWARE_SAMPLERS"
    assert fallback["safeNoShadowColorMipmapDependency"] is True
    assert fallback["safeNoHardwareComparisonDependency"] is True


def test_mipmap_timing_and_known_limit_are_recorded() -> None:
    mipmaps = load_contract()["mipmaps"]
    assert "before" in mipmaps["colortexGenerationTiming"]
    assert set(mipmaps["colortexAllowedPrograms"]) == {
        "begin",
        "prepare",
        "deferred",
        "composite",
    }
    assert "before shadowcomp" in mipmaps["shadowDepthGenerationTiming"]
    assert "do not generate" in mipmaps["shadowColorKnownLimitation"]
