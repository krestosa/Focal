from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

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
            self.evaluate(working_state(), branch_activity_at=NOW - timedelta(minutes=2)).reason,
            "RECENT_BRANCH_ACTIVITY",
        )
        self.assertEqual(
            self.evaluate(working_state(), pr_activity_at=NOW - timedelta(minutes=2)).reason,
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
        updated = watchdog.replace_state(body, {"schemaVersion": 3, "repository": "krestosa/Focal", "version": 2})
        self.assertIn("before", updated)
        self.assertIn("middle", updated)
        self.assertIn("after", updated)
        self.assertIn('"version": 2', updated)
        self.assertIn('"commandId":"cmd-1"', updated)


if __name__ == "__main__":
    unittest.main()
