from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_state_coordinator as coordinator
from tools import stale_lease_watchdog as watchdog


NOW = datetime(2026, 7, 30, 6, 0, tzinfo=timezone.utc)
REPOSITORY = "krestosa/Focal"


def idle_state() -> dict[str, object]:
    return {
        "schemaVersion": 3,
        "repository": REPOSITORY,
        "version": 1,
        "status": "idle",
        "mode": "normal",
        "phase": "idle",
        "runId": None,
        "leaseExpiresAt": None,
        "lastCommandId": "previous",
        "lastCommandAccepted": True,
        "lastCommandReason": "STATE_OBSERVED",
    }


def acquire_command(command_id: str, run_id: str) -> dict[str, object]:
    timestamp = coordinator.now_iso(NOW)
    return {
        "schemaVersion": 3,
        "commandId": command_id,
        "operation": "acquire",
        "runId": run_id,
        "mode": "normal",
        "phase": "LOCK_ACQUISITION",
        "startedAt": timestamp,
        "heartbeatAt": timestamp,
        "leaseExpiresAt": coordinator.now_iso(NOW + timedelta(minutes=30)),
        "softStopAt": coordinator.now_iso(NOW + timedelta(minutes=50)),
        "cleanupAt": coordinator.now_iso(NOW + timedelta(minutes=55)),
        "hardKillAt": coordinator.now_iso(NOW + timedelta(minutes=58, seconds=30)),
        "deadlineAt": coordinator.now_iso(NOW + timedelta(minutes=58, seconds=30)),
        "baseMainSha": "base",
        "workBranch": None,
        "workBranchHeadSha": None,
        "pullRequest": None,
        "checkpointSha": None,
        "note": None,
    }


class Gov002AcceptanceMatrix(unittest.TestCase):
    def test_two_contenders_preserve_the_first_owner(self) -> None:
        acquired = coordinator.apply_command(
            command=acquire_command("acquire-a", "run-a"),
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        contender = coordinator.apply_command(
            command=acquire_command("acquire-b", "run-b"),
            state=acquired.state,
            repository=REPOSITORY,
            processed_at=NOW,
        )

        self.assertTrue(acquired.accepted)
        self.assertFalse(contender.accepted)
        self.assertEqual(contender.reason, "ACTIVE_LEASE")
        self.assertEqual(contender.state["runId"], "run-a")

    def test_expired_inactive_lease_is_watchdog_repairable(self) -> None:
        state = {
            **idle_state(),
            "status": "working",
            "phase": "VALIDATION",
            "runId": "expired-run",
            "leaseExpiresAt": coordinator.now_iso(NOW - timedelta(minutes=10)),
            "lastCommandId": "heartbeat-expired",
        }
        decision = watchdog.evaluate(
            command={
                "schemaVersion": 3,
                "commandId": "heartbeat-expired",
                "operation": "heartbeat",
            },
            state=state,
            now=NOW,
            expiry_grace=timedelta(minutes=2),
            activity_grace=timedelta(minutes=15),
            active_runs=[],
            branch_activity_at=NOW - timedelta(hours=1),
            pr_activity_at=NOW - timedelta(hours=1),
        )

        self.assertTrue(decision.repair)
        self.assertEqual(decision.reason, "EXPIRED_LEASE_WITHOUT_ACTIVE_REMOTE_WORK")

    def test_invalid_command_token_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "commandId is required"):
            coordinator.validate_contract(
                {"schemaVersion": 3, "commandId": "", "operation": "inspect"},
                idle_state(),
                REPOSITORY,
            )

    def test_lost_owner_cannot_heartbeat(self) -> None:
        acquired = coordinator.apply_command(
            command=acquire_command("acquire-owner", "run-owner"),
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        heartbeat = {
            "schemaVersion": 3,
            "commandId": "foreign-heartbeat",
            "operation": "heartbeat",
            "runId": "run-foreign",
            "phase": "VALIDATION",
            "heartbeatAt": coordinator.now_iso(NOW + timedelta(minutes=1)),
            "leaseExpiresAt": coordinator.now_iso(NOW + timedelta(minutes=31)),
            "workBranch": "foreign/branch",
            "workBranchHeadSha": "foreign-head",
            "pullRequest": 99,
            "checkpointSha": "foreign-checkpoint",
            "note": None,
        }
        result = coordinator.apply_command(
            command=heartbeat,
            state=acquired.state,
            repository=REPOSITORY,
            processed_at=NOW + timedelta(minutes=1),
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "NOT_LEASE_OWNER")
        self.assertEqual(result.state["runId"], "run-owner")
        self.assertNotEqual(result.state.get("workBranch"), "foreign/branch")


if __name__ == "__main__":
    unittest.main()
