from __future__ import annotations

import base64
import pathlib
import unittest

from tools import repository_maintenance as maintenance


class FakeApi:
    def __init__(self, blobs: dict[str, str]) -> None:
        self.blobs = blobs

    def request(self, method: str, path: str, payload=None):
        if method == "GET" and "/git/blobs/" in path:
            sha = path.rsplit("/", 1)[-1]
            return {
                "content": base64.b64encode(self.blobs.get(sha, "").encode()).decode(),
            }
        raise AssertionError((method, path, payload))


class GarbageTests(unittest.TestCase):
    def test_temporary_workflow_requires_explicit_marker(self) -> None:
        tree = [
            {"type": "blob", "path": ".github/workflows/tmp-one.yml", "sha": "marked"},
            {"type": "blob", "path": ".github/workflows/tmp-two.yml", "sha": "plain"},
            {"type": "blob", "path": "build/.DS_Store", "sha": "ds"},
            {"type": "blob", "path": "src/change.orig", "sha": "orig"},
        ]
        api = FakeApi(
            {
                "marked": maintenance.TEMPORARY_WORKFLOW_MARKER + "\nname: temporary\n",
                "plain": "name: permanent\n",
            }
        )
        paths = maintenance.garbage_paths(api, "krestosa/Focal", tree)
        self.assertIn(".github/workflows/tmp-one.yml", paths)
        self.assertNotIn(".github/workflows/tmp-two.yml", paths)
        self.assertIn("build/.DS_Store", paths)
        self.assertIn("src/change.orig", paths)

    def test_permanent_maintenance_workflow_shares_coordinator_lock(self) -> None:
        workflow = pathlib.Path(".github/workflows/repository-maintenance.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("group: focal-automation-state", workflow)
        self.assertIn("--require-idle", workflow)
        self.assertIn("tools.repository_maintenance", workflow)


if __name__ == "__main__":
    unittest.main()
