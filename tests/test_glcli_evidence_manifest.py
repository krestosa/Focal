from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.glcli_evidence_manifest import REQUIRED_FILES, build_manifest


class EvidenceManifestTests(unittest.TestCase):
    def _write_evidence(self, root: Path) -> None:
        payloads = {
            "focal-gl-glfw-probe.json": {
                "context": {
                    "backend": "glfw-hidden",
                    "vendor": "Mesa",
                    "renderer": "llvmpipe",
                    "version": "4.5",
                    "glslVersion": "4.50",
                }
            },
            "focal-gl-compile-link.json": {"outcome": "PASS"},
            "focal-gl-render-readback.json": {"outcome": "PASS"},
        }
        for name, payload in payloads.items():
            (root / name).write_text(
                json.dumps(payload, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    def test_builds_deterministic_scoped_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_evidence(root)
            with mock.patch.dict(
                os.environ,
                {
                    "LIBGL_ALWAYS_SOFTWARE": "true",
                    "MESA_LOADER_DRIVER_OVERRIDE": "llvmpipe",
                },
                clear=False,
            ):
                first = build_manifest(root, commit_sha="abc123", run_id="42")
                second = build_manifest(root, commit_sha="abc123", run_id="42")

            self.assertEqual(first, second)
            self.assertEqual(first["scope"], "mesa-software")
            self.assertEqual(first["evidenceLevel"], "GL_RENDER_READBACK")
            self.assertTrue(first["environment"]["softwareRenderingForced"])
            self.assertEqual(first["environment"]["mesaDriverOverride"], "llvmpipe")
            self.assertEqual(
                [artifact["path"] for artifact in first["artifacts"]],
                sorted(REQUIRED_FILES),
            )
            for artifact in first["artifacts"]:
                self.assertEqual(len(artifact["sha256"]), 64)
                self.assertGreater(artifact["bytes"], 0)
            self.assertIn("physical GPU performance", first["claims"]["doesNotProve"])

    def test_rejects_missing_required_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / REQUIRED_FILES[0]).write_text(
                json.dumps({"context": {}}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "missing required evidence files"):
                build_manifest(root, commit_sha="abc123", run_id="42")

    def test_rejects_probe_without_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_evidence(root)
            (root / REQUIRED_FILES[0]).write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "context object"):
                build_manifest(root, commit_sha="abc123", run_id="42")


if __name__ == "__main__":
    unittest.main()
