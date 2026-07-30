from __future__ import annotations

import base64
import pathlib
import unittest

from tools import repository_maintenance as maintenance


class BlobApi:
    def __init__(self, blobs: dict[str, str]) -> None:
        self.blobs = blobs

    def request(self, method: str, path: str, payload=None):
        if method == "GET" and "/git/blobs/" in path:
            sha = path.rsplit("/", 1)[-1]
            return {
                "content": base64.b64encode(self.blobs.get(sha, "").encode()).decode(),
            }
        raise AssertionError((method, path, payload))


class IssueApi:
    def __init__(self, body: str, title: str = maintenance.MAINTENANCE_ISSUE_TITLE) -> None:
        self.body = body
        self.title = title

    def request(self, method: str, path: str, payload=None):
        if method == "GET" and path.endswith("/issues/101"):
            return {"title": self.title, "body": self.body}
        raise AssertionError((method, path, payload))


def maintenance_body(command: str) -> str:
    return (
        "# Maintenance\n\n"
        f"{maintenance.MAINTENANCE_COMMAND_START}\n"
        "```json\n"
        f"{command}\n"
        "```\n"
        f"{maintenance.MAINTENANCE_COMMAND_END}\n"
    )


class ScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = [
            {"type": "blob", "path": ".github/workflows/tmp-one.yml", "sha": "marked"},
            {"type": "blob", "path": ".github/workflows/tmp-two.yml", "sha": "plain"},
            {"type": "blob", "path": "build/.DS_Store", "sha": "ds"},
            {"type": "blob", "path": "src/change.orig", "sha": "orig"},
        ]
        self.api = BlobApi(
            {
                "marked": maintenance.TEMPORARY_WORKFLOW_MARKER + "\nname: temporary\n",
                "plain": "name: permanent\n",
            }
        )

    def test_branches_scope_does_not_select_files(self) -> None:
        self.assertEqual(
            maintenance.garbage_paths(self.api, "krestosa/Focal", self.tree, scope="branches"),
            [],
        )

    def test_garbage_scope_excludes_workflows(self) -> None:
        paths = maintenance.garbage_paths(
            self.api, "krestosa/Focal", self.tree, scope="garbage"
        )
        self.assertEqual(paths, ["build/.DS_Store", "src/change.orig"])

    def test_temporary_workflow_scope_requires_explicit_marker(self) -> None:
        paths = maintenance.garbage_paths(
            self.api, "krestosa/Focal", self.tree, scope="temporary_workflows"
        )
        self.assertEqual(paths, [".github/workflows/tmp-one.yml"])

    def test_all_scope_combines_allowlists(self) -> None:
        paths = maintenance.garbage_paths(self.api, "krestosa/Focal", self.tree, scope="all")
        self.assertEqual(
            paths,
            [".github/workflows/tmp-one.yml", "build/.DS_Store", "src/change.orig"],
        )

    def test_invalid_scope_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "MAINTENANCE_SCOPE_INVALID"):
            maintenance.validate_scope("everything")


class CommandIngressTests(unittest.TestCase):
    def test_dedicated_issue_parses_scoped_command(self) -> None:
        api = IssueApi(
            maintenance_body(
                '{"schemaVersion": 1, "commandId": "cmd-1", '
                '"operation": "repository_maintenance", "scope": "branches", '
                '"dryRun": false}'
            )
        )
        command = maintenance._maintenance_request_from_issue(api, "krestosa/Focal", 101)
        self.assertIsNotNone(command)
        self.assertEqual(command["scope"], "branches")
        self.assertFalse(command["dryRun"])

    def test_idle_placeholder_does_not_execute(self) -> None:
        api = IssueApi(
            maintenance_body(
                '{"schemaVersion": 1, "commandId": "idle", '
                '"operation": "idle", "scope": "branches", "dryRun": true}'
            )
        )
        self.assertIsNone(
            maintenance._maintenance_request_from_issue(api, "krestosa/Focal", 101)
        )

    def test_wrong_issue_title_is_rejected(self) -> None:
        api = IssueApi(maintenance_body("{}"), title="wrong")
        with self.assertRaisesRegex(ValueError, "title mismatch"):
            maintenance._maintenance_request_from_issue(api, "krestosa/Focal", 101)


class MutationInvariantTests(unittest.TestCase):
    def test_branch_creation_is_forbidden(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "MAINTENANCE_CREATED_REF"):
            maintenance._guard_mutation(
                "POST", "/repos/krestosa/Focal/git/refs", {"ref": "refs/heads/new"}
            )

    def test_pull_request_mutation_is_forbidden(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "MAINTENANCE_CREATED_PR"):
            maintenance._guard_mutation(
                "POST", "/repos/krestosa/Focal/pulls", {"head": "new"}
            )

    def test_workflow_creation_is_forbidden(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "MAINTENANCE_CREATED_WORKFLOW"):
            maintenance._guard_mutation(
                "POST",
                "/repos/krestosa/Focal/git/trees",
                {
                    "tree": [
                        {
                            "path": ".github/workflows/new.yml",
                            "mode": "100644",
                            "type": "blob",
                            "sha": "abc",
                        }
                    ]
                },
            )

    def test_workflow_deletion_remains_allowed(self) -> None:
        maintenance._guard_mutation(
            "POST",
            "/repos/krestosa/Focal/git/trees",
            {
                "tree": [
                    {
                        "path": ".github/workflows/temporary.yml",
                        "mode": "100644",
                        "type": "blob",
                        "sha": None,
                    }
                ]
            },
        )


class WorkflowContractTests(unittest.TestCase):
    def test_permanent_workflow_routes_only_dedicated_issue(self) -> None:
        workflow = pathlib.Path(".github/workflows/repository-maintenance.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("group: focal-automation-state", workflow)
        self.assertIn("github.event.issue.number == 101", workflow)
        self.assertIn("--state-issue 7", workflow)
        self.assertIn("--command-issue 101", workflow)
        self.assertIn("--from-issue", workflow)
        self.assertIn("- branches", workflow)
        self.assertIn("- garbage", workflow)
        self.assertIn("- temporary_workflows", workflow)
        self.assertNotIn("create_branch", workflow)
        self.assertNotIn("git checkout -b", workflow)


if __name__ == "__main__":
    unittest.main()
