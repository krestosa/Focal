#!/usr/bin/env python3
"""Build a deterministic manifest for focal-gl evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
REQUIRED_FILES = (
    "focal-gl-glfw-probe.json",
    "focal-gl-compile-link.json",
    "focal-gl-render-readback.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def build_manifest(evidence_dir: Path, *, commit_sha: str, run_id: str) -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (evidence_dir / name).is_file()]
    if missing:
        raise ValueError(f"missing required evidence files: {', '.join(missing)}")

    probe = _read_json(evidence_dir / REQUIRED_FILES[0])
    context = probe.get("context")
    if not isinstance(context, dict):
        raise ValueError("probe evidence does not contain a context object")

    artifacts = []
    for name in sorted(REQUIRED_FILES):
        path = evidence_dir / name
        _read_json(path)
        artifacts.append(
            {
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "scope": "mesa-software",
        "evidenceLevel": "GL_RENDER_READBACK",
        "commitSha": commit_sha,
        "runId": run_id,
        "environment": {
            "backend": context.get("backend"),
            "vendor": context.get("vendor"),
            "renderer": context.get("renderer"),
            "version": context.get("version"),
            "glslVersion": context.get("glslVersion"),
            "softwareRenderingForced": os.environ.get("LIBGL_ALWAYS_SOFTWARE") == "true",
            "mesaDriverOverride": os.environ.get("MESA_LOADER_DRIVER_OVERRIDE"),
        },
        "artifacts": artifacts,
        "claims": {
            "proves": [
                "Mesa software context creation",
                "representative standalone compile and link",
                "representative standalone render and readback",
            ],
            "doesNotProve": [
                "physical GPU performance",
                "vendor-driver compatibility",
                "Iris-patched shader acceptance",
                "Minecraft or Iris client integration",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    try:
        manifest = build_manifest(
            args.evidence_dir,
            commit_sha=args.commit_sha,
            run_id=args.run_id,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
