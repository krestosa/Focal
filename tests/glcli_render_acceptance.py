#!/usr/bin/env python3
"""Exercise GLCLI-005 framebuffer draw and color/depth readback on Mesa/GLFW."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "focal-gl"

FIXTURES = {
    "gbuffers_fixture": {
        "fixture": "geometry",
        "sampler": False,
        "vsh": """#version 330 core
layout(location = 0) in vec3 position;
out vec3 vertexColor;
void main() {
    vertexColor = position * 0.5 + 0.5;
    gl_Position = vec4(position, 1.0);
}
""",
        "fsh": """#version 330 core
in vec3 vertexColor;
layout(location = 0) out vec4 fragColor;
void main() {
    fragColor = vec4(vertexColor, 1.0);
}
""",
    },
    "composite_fixture": {
        "fixture": "fullscreen",
        "sampler": True,
        "vsh": """#version 330 core
out vec2 uv;
void main() {
    vec2 position = vec2(
        (gl_VertexID == 1) ? 3.0 : -1.0,
        (gl_VertexID == 2) ? 3.0 : -1.0
    );
    uv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
""",
        "fsh": """#version 330 core
in vec2 uv;
uniform sampler2D sourceTexture;
layout(location = 0) out vec4 fragColor;
void main() {
    fragColor = texture(sourceTexture, clamp(uv, 0.0, 1.0));
}
""",
    },
    "final_fixture": {
        "fixture": "fullscreen",
        "sampler": True,
        "vsh": """#version 330 core
out vec2 uv;
void main() {
    vec2 position = vec2(
        (gl_VertexID == 1) ? 3.0 : -1.0,
        (gl_VertexID == 2) ? 3.0 : -1.0
    );
    uv = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
""",
        "fsh": """#version 330 core
in vec2 uv;
uniform sampler2D sourceTexture;
layout(location = 0) out vec4 finalColor;
void main() {
    vec4 source = texture(sourceTexture, clamp(uv, 0.0, 1.0));
    finalColor = vec4(source.rgb * vec3(0.75, 0.875, 1.0), 1.0);
}
""",
    },
}


def write_program(shader_root: Path, name: str, fixture: dict[str, object]) -> None:
    for suffix in ("vsh", "fsh"):
        (shader_root / f"{name}.{suffix}").write_text(str(fixture[suffix]), encoding="utf-8")


def run_render(pack: Path, program: str, fixture: str, artifacts: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            "render",
            "--pack",
            str(pack),
            "--program",
            program,
            "--fixture",
            fixture,
            "--backend",
            "glfw",
            "--gl-version",
            "3.3",
            "--gl-profile",
            "core",
            "--size",
            "32x32",
            "--source-mode",
            "preprocessed",
            "--artifacts",
            str(artifacts),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if not completed.stdout.strip():
        raise AssertionError(f"render produced no JSON for {program}: {completed.stderr}")
    return completed, json.loads(completed.stdout)


def main() -> int:
    summary: dict[str, object] = {"schemaVersion": 1, "programs": {}}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        pack = root / "pack"
        shaders = pack / "shaders"
        shaders.mkdir(parents=True)
        artifacts = root / "artifacts"

        for program, fixture in FIXTURES.items():
            write_program(shaders, program, fixture)
            completed, payload = run_render(pack, program, str(fixture["fixture"]), artifacts)
            assert completed.returncode == 0, (program, completed.stderr, payload)
            assert payload["outcome"] == "PASS", payload
            assert payload["exitCode"] == 0, payload
            assert payload["evidenceLevel"] == "GL_RENDER_READBACK", payload
            render = payload["context"]["render"]
            assert render["backend"] == "glfw-hidden", render
            assert render["framebufferStatus"] == "GL_FRAMEBUFFER_COMPLETE", render
            assert render["samplerBound"] is fixture["sampler"], render
            assert render["color"]["finite"] is True, render
            assert render["color"]["drawnPixels"] > 0, render
            assert render["depth"]["finite"] is True, render
            assert render["depth"]["drawnPixels"] > 0, render
            for artifact in render["artifacts"].values():
                assert Path(artifact).is_file(), artifact
            summary["programs"][program] = render

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
