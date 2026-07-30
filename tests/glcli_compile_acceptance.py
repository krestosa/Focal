#!/usr/bin/env python3
"""Exercise GLCLI-004 against a real current hidden GLFW context."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "focal-gl"

POSITIVE_FIXTURES = {
    "gbuffers_fixture": {
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
layout(location = 0) out vec4 fragColor;
void main() {
    fragColor = vec4(uv, 0.25, 1.0);
}
""",
    },
    "final_fixture": {
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
layout(location = 0) out vec4 finalColor;
void main() {
    finalColor = vec4(uv.x, uv.y, 1.0 - uv.x, 1.0);
}
""",
    },
}


def write_program(shader_root: Path, name: str, stages: dict[str, str]) -> None:
    for suffix, source in stages.items():
        (shader_root / f"{name}.{suffix}").write_text(source, encoding="utf-8")


def run_compile(pack: Path, program: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    completed = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            "compile",
            "--pack",
            str(pack),
            "--program",
            program,
            "--backend",
            "glfw",
            "--gl-version",
            "3.3",
            "--gl-profile",
            "core",
            "--size",
            "64x64",
            "--source-mode",
            "preprocessed",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if not completed.stdout.strip():
        raise AssertionError(f"compile produced no JSON for {program}: {completed.stderr}")
    return completed, json.loads(completed.stdout)


def main() -> int:
    summary: dict[str, object] = {"schemaVersion": 1, "positive": {}, "negative": {}}
    with tempfile.TemporaryDirectory() as directory:
        pack = Path(directory)
        shaders = pack / "shaders"
        shaders.mkdir()
        for program, stages in POSITIVE_FIXTURES.items():
            write_program(shaders, program, stages)
            completed, payload = run_compile(pack, program)
            assert completed.returncode == 0, (program, completed.stderr, payload)
            assert payload["outcome"] == "PASS", payload
            assert payload["exitCode"] == 0, payload
            assert payload["evidenceLevel"] == "GL_COMPILE_LINK", payload
            compile_link = payload["context"]["compileLink"]
            assert compile_link["backend"] == "glfw-hidden", compile_link
            assert compile_link["sourceMode"] == "preprocessed", compile_link
            assert [item["stage"] for item in compile_link["stages"]] == ["vsh", "fsh"], compile_link
            summary["positive"][program] = {
                "outcome": payload["outcome"],
                "evidenceLevel": payload["evidenceLevel"],
                "stages": compile_link["stages"],
                "linkLog": compile_link["linkLog"],
            }

        write_program(
            shaders,
            "invalid_fixture",
            {
                "vsh": "#version 330 core\nvoid main() { gl_Position = vec4(1.0) }\n",
                "fsh": "#version 330 core\nout vec4 color;\nvoid main() { color = vec4(1.0); }\n",
            },
        )
        completed, payload = run_compile(pack, "invalid_fixture")
        assert completed.returncode == 4, (completed.stderr, payload)
        assert payload["outcome"] == "FAIL", payload
        assert payload["exitCode"] == 4, payload
        assert payload["evidenceLevel"] == "STATIC", payload
        failure = payload["context"]["compileFailure"]
        assert failure["phase"] == "stage", failure
        assert failure["stage"] == "vsh", failure
        assert failure["log"].strip(), failure
        summary["negative"] = failure

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
