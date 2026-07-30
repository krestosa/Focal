from __future__ import annotations

import argparse
import contextlib
import io
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from tools import stale_lease_watchdog as watchdog


NOW = datetime(2026, 7, 29, 6, 0, tzinfo=timezone.utc)


def command(command_id: str = "cmd-1") -> dict[str, object]:
    return {"schemaVersion": 3, "commandId": command_id, "operation": "heartbeat"}


def working_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "schemaVersion": 3,
        "repository": "krestosa/Focal",
        "version": 10,
        "status": "working",
        "mode": "normal",
        "phase": "CI_VALIDATION",
        "runId": "run-1",
        "startedAt": "2026-07-29T05:00:00Z",
        "heartbeatAt": "2026-07-29T05:10:00Z",
        "leaseExpiresAt": "2026-07-29T05:30:00Z",
        "softStopAt": "2026-07-29T05:50:00Z",
        "cleanupAt": "2026-07-29T05:55:00Z",
        "hardKillAt": "2026-07-29T05:58:30Z",
        "deadlineAt": "2026-07-29T05:59:00Z",
        "baseMainSha": "base",
        "workBranch": "feature/example",
        "workBranchHeadSha": "head",
        "pullRequest": 99,
        "checkpointSha": None,
        "lastCommandId": "cmd-1",
        "lastCommandAccepted": True,
        "lastCommandReason": "HEARTBEAT_ACCEPTED",
        "customField": {"preserve": True},
    }
    state.update(overrides)
    return state


def issue_body(command_value: dict[str, object], state: dict[str, object]) -> str:
    return f"""# state
{watchdog.COMMAND_START}
```json
{json.dumps(command_value)}
```
{watchdog.COMMAND_END}

{watchdog.STATE_START}
```json
{json.dumps(state)}
```
{watchdog.STATE_END}
"""


class DecisionTests(unittest.TestCase):
    def evaluate(self, state: dict[str, object], **kwargs: object) -> watchdog.Decision:
        return watchdog.evaluate(
            command=command(),
            state=state,
            now=NOW,
            expiry_grace=timedelta(minutes=2),
            activity_grace=timedelta(minutes=15),
            active_runs=kwargs.get("active_runs", []),
            branch_activity_at=kwargs.get("branch_activity_at"),
            pr_activity_at=kwargs.get("pr_activity_at"),
        )

    def test_idle_state_is_ignored(self) -> None:
        state = working_state(status="idle", runId=None)
        self.assertEqual(self.evaluate(state).reason, "ALREADY_IDLE")

    def test_future_or_grace_period_lease_is_not_released(self) -> None:
        state = working_state(leaseExpiresAt="2026-07-29T05:59:30Z")
        self.assertEqual(self.evaluate(state).reason, "LEASE_NOT_EXPIRED")

    def test_unprocessed_command_blocks_repair(self) -> None:
        state = working_state(lastCommandId="older-command")
        self.assertEqual(self.evaluate(state).reason, "UNPROCESSED_COMMAND_PRESENT")

    def test_active_mutating_workflow_blocks_repair(self) -> None:
        decision = self.evaluate(
            working_state(),
            active_runs=[{"name": "Autonomous Development", "status": "in_progress"}],
        )
        self.assertEqual(decision.reason, "ACTIVE_MUTATING_WORKFLOW")

    def test_validation_and_coordinator_runs_do_not_block_repair(self) -> None:
        decision = self.evaluate(
            working_state(),
            active_runs=[
                {"name": "Validation", "status": "in_progress"},
                {"name": "Automation State Coordinator", "status": "queued"},
            ],
        )
        self.assertTrue(decision.repair)

    def test_recent_branch_or_pr_activity_blocks_repair(self) -> None:
        self.assertEqual(
            self.evaluate(
                working_state(),
                branch_activity_at=NOW - timedelta(minutes=2),
            ).reason,
            "RECENT_BRANCH_ACTIVITY",
        )
        self.assertEqual(
            self.evaluate(
                working_state(),
                pr_activity_at=NOW - timedelta(minutes=2),
            ).reason,
            "RECENT_PULL_REQUEST_ACTIVITY",
        )

    def test_expired_inactive_lease_is_repairable(self) -> None:
        decision = self.evaluate(
            working_state(),
            branch_activity_at=NOW - timedelta(hours=1),
            pr_activity_at=NOW - timedelta(hours=1),
        )
        self.assertTrue(decision.repair)
        self.assertEqual(decision.reason, "EXPIRED_LEASE_WITHOUT_ACTIVE_REMOTE_WORK")


class SnapshotTests(unittest.TestCase):
    def test_unchanged_snapshot_is_accepted(self) -> None:
        expected_command = command()
        expected_state = working_state()
        self.assertTrue(
            watchdog.state_unchanged_during_evaluation(
                expected_command=expected_command,
                expected_state=expected_state,
                current_command=dict(expected_command),
                current_state=dict(expected_state),
            )
        )

    def test_acquire_heartbeat_and_recover_changes_are_detected(self) -> None:
        expected_command = command()
        expected_state = working_state()

        changed_cases = {
            "acquire": (
                {"schemaVersion": 3, "commandId": "acquire-2", "operation": "acquire"},
                working_state(
                    version=11,
                    runId="run-2",
                    lastCommandId="acquire-2",
                    leaseExpiresAt="2026-07-29T06:30:00Z",
                ),
            ),
            "heartbeat": (
                {
                    "schemaVersion": 3,
                    "commandId": "heartbeat-2",
                    "operation": "heartbeat",
                },
                working_state(
                    version=11,
                    lastCommandId="heartbeat-2",
                    leaseExpiresAt="2026-07-29T06:30:00Z",
                ),
            ),
            "recover": (
                {"schemaVersion": 3, "commandId": "recover-2", "operation": "recover"},
                working_state(
                    version=11,
                    mode="recovery",
                    runId="run-recovered",
                    lastCommandId="recover-2",
                    leaseExpiresAt="2026-07-29T06:30:00Z",
                ),
            ),
        }

        for name, (current_command, current_state) in changed_cases.items():
            with self.subTest(name=name):
                self.assertFalse(
                    watchdog.state_unchanged_during_evaluation(
                        expected_command=expected_command,
                        expected_state=expected_state,
                        current_command=current_command,
                        current_state=current_state,
                    )
                )

    def test_run_rechecks_issue_before_patch(self) -> None:
        initial_command = command()
        initial_state = working_state(workBranch=None, pullRequest=None)
        recovered_command = {
            "schemaVersion": 3,
            "commandId": "recover-2",
            "operation": "recover",
        }
        recovered_state = working_state(
            version=11,
            mode="recovery",
            runId="run-recovered",
            workBranch=None,
            pullRequest=None,
            lastCommandId="recover-2",
            leaseExpiresAt="2026-07-29T06:30:00Z",
        )

        class FakeApi:
            def __init__(self) -> None:
                self.issue_bodies = [
                    issue_body(initial_command, initial_state),
                    issue_body(recovered_command, recovered_state),
                ]
                self.patches: list[dict[str, object]] = []

            def request(
                self,
                method: str,
                path: str,
                payload: dict[str, object] | None = None,
            ) -> object:
                if method == "GET" and path.endswith("/actions/runs?per_page=100"):
                    return {"workflow_runs": []}
                if method == "GET" and path.endswith("/issues/7"):
                    return {"body": self.issue_bodies.pop(0)}
                if method == "PATCH" and path.endswith("/issues/7"):
                    self.patches.append(payload or {})
                    return {}
                raise AssertionError(f"unexpected request: {method} {path}")

        api = FakeApi()
        args = argparse.Namespace(
            repository="krestosa/Focal",
            issue=7,
            expiry_grace_seconds=120,
            activity_grace_seconds=900,
            dry_run=False,
        )

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz: timezone | None = None) -> datetime:
                return NOW if tz is not None else NOW.replace(tzinfo=None)

        with (
            mock.patch.object(watchdog, "GitHubApi", return_value=api),
            mock.patch.object(watchdog, "datetime", FixedDateTime),
            mock.patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=True),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            exit_code = watchdog.run(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(api.patches, [])
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["reason"], "STATE_CHANGED_DURING_EVALUATION")
        self.assertEqual(summary["observedRunId"], "run-recovered")


class RepairTests(unittest.TestCase):
    def test_repair_preserves_checkpoint_unknown_fields_and_audit(self) -> None:
        state = working_state()
        repaired = watchdog.repaired_state(state, repaired_at=NOW)
        self.assertEqual(repaired["status"], "idle")
        self.assertIsNone(repaired["runId"])
        self.assertEqual(repaired["checkpointSha"], "head")
        self.assertEqual(repaired["lastRunId"], "run-1")
        self.assertEqual(repaired["lastResult"], "PARTIAL")
        self.assertEqual(repaired["lastAbandonedRunId"], "run-1")
        self.assertNotIn("owner", repaired)
        self.assertNotIn("executionSource", repaired)
        self.assertNotIn("lastAbandonedOwner", repaired)
        self.assertEqual(repaired["lastAbandonedWorkBranch"], "feature/example")
        self.assertEqual(repaired["lastWatchdogAction"], "STALE_LEASE_RELEASED")
        self.assertEqual(repaired["version"], 11)
        self.assertEqual(repaired["customField"], {"preserve": True})

    def test_state_block_replacement_preserves_other_body_text(self) -> None:
        body = """before
<!-- focal-command:v3 -->
```json
{"schemaVersion":3,"commandId":"cmd-1","operation":"inspect"}
```
<!-- /focal-command -->
middle
<!-- focal-state:v3 -->
```json
{"schemaVersion":3,"repository":"krestosa/Focal","version":1}
```
<!-- /focal-state -->
after
"""
        updated = watchdog.replace_state(
            body,
            {"schemaVersion": 3, "repository": "krestosa/Focal", "version": 2},
        )
        self.assertIn("before", updated)
        self.assertIn("middle", updated)
        self.assertIn("after", updated)
        self.assertIn('"version": 2', updated)
        self.assertIn('"commandId":"cmd-1"', updated)


if __name__ == "__main__":
    unittest.main()
