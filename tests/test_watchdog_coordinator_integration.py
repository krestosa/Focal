from __future__ import annotations

import pathlib
import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_state_coordinator as coordinator
from tools import stale_lease_watchdog as watchdog


NOW = datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
REPOSITORY = "krestosa/Focal"


def expired_working_state() -> dict[str, object]:
    return {
        "schemaVersion": 3,
        "repository": REPOSITORY,
        "version": 20,
        "status": "working",
        "mode": "normal",
        "phase": "REMOTE_STATE_AUDIT",
        "runId": "stale-run",
        "startedAt": "2026-07-30T01:00:00Z",
        "heartbeatAt": "2026-07-30T01:10:00Z",
        "leaseExpiresAt": "2026-07-30T01:30:00Z",
        "softStopAt": "2026-07-30T01:50:00Z",
        "cleanupAt": "2026-07-30T01:55:00Z",
        "hardKillAt": "2026-07-30T01:58:30Z",
        "deadlineAt": "2026-07-30T01:59:00Z",
        "baseMainSha": "base",
        "workBranch": None,
        "workBranchHeadSha": None,
        "pullRequest": None,
        "checkpointSha": "checkpoint",
        "lastCommandId": "previous-command",
        "lastCommandAccepted": True,
        "lastCommandReason": "HEARTBEAT_ACCEPTED",
    }


class CoordinatorWatchdogIntegrationTests(unittest.TestCase):
    def test_processed_inspect_makes_expired_lease_repairable(self) -> None:
        inspect = {
            "schemaVersion": 3,
            "commandId": "inspect-stale-lease",
            "operation": "inspect",
        }
        processed = coordinator.apply_command(
            command=inspect,
            state=expired_working_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )

        self.assertTrue(processed.accepted)
        self.assertEqual(processed.reason, "STATE_OBSERVED")
        self.assertEqual(processed.state["lastCommandId"], inspect["commandId"])

        decision = watchdog.evaluate(
            command=inspect,
            state=processed.state,
            now=NOW,
            expiry_grace=timedelta(minutes=2),
            activity_grace=timedelta(minutes=15),
            active_runs=[],
            branch_activity_at=None,
            pr_activity_at=None,
        )

        self.assertTrue(decision.repair)
        self.assertEqual(decision.reason, "EXPIRED_LEASE_WITHOUT_ACTIVE_REMOTE_WORK")

    def test_coordinator_workflow_runs_watchdog_after_command(self) -> None:
        workflow = pathlib.Path(".github/workflows/automation-state.yml").read_text(
            encoding="utf-8"
        )

        coordinator_command = "python -m tools.automation_state_coordinator"
        watchdog_command = "python tools/stale_lease_watchdog.py"
        self.assertIn("actions: read", workflow)
        self.assertIn(coordinator_command, workflow)
        self.assertIn(watchdog_command, workflow)
        self.assertLess(workflow.index(coordinator_command), workflow.index(watchdog_command))
        self.assertIn("--expiry-grace-seconds 120", workflow)
        self.assertIn("--activity-grace-seconds 900", workflow)


if __name__ == "__main__":
    unittest.main()
