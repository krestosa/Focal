from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_state_coordinator as coordinator


NOW = datetime(2026, 7, 30, 6, 0, tzinfo=timezone.utc)
REPOSITORY = "krestosa/Focal"


def working_state(run_id: str = "run-owner") -> dict[str, object]:
    return {
        "schemaVersion": 3,
        "repository": REPOSITORY,
        "version": 1,
        "status": "working",
        "mode": "normal",
        "phase": "IMPLEMENTATION",
        "runId": run_id,
        "startedAt": coordinator.now_iso(NOW - timedelta(minutes=1)),
        "heartbeatAt": coordinator.now_iso(NOW - timedelta(seconds=30)),
        "leaseExpiresAt": coordinator.now_iso(NOW + timedelta(minutes=20)),
        "softStopAt": coordinator.now_iso(NOW + timedelta(minutes=40)),
        "cleanupAt": coordinator.now_iso(NOW + timedelta(minutes=45)),
        "hardKillAt": coordinator.now_iso(NOW + timedelta(minutes=48, seconds=30)),
        "deadlineAt": coordinator.now_iso(NOW + timedelta(minutes=48, seconds=30)),
        "baseMainSha": "base",
        "workBranch": "test/branch",
        "workBranchHeadSha": "head",
        "pullRequest": 1,
        "checkpointSha": "checkpoint",
        "lastCommandId": "previous-command",
        "lastCommandAccepted": True,
        "lastCommandReason": "HEARTBEAT_ACCEPTED",
    }


class MalformedCommandFixtures(unittest.TestCase):
    def test_missing_command_id_is_rejected(self) -> None:
        command = {"schemaVersion": 3, "operation": "inspect"}

        with self.assertRaisesRegex(ValueError, "commandId is required"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_empty_command_id_is_rejected(self) -> None:
        command = {"schemaVersion": 3, "commandId": "", "operation": "inspect"}

        with self.assertRaisesRegex(ValueError, "commandId is required"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_non_string_command_id_is_rejected(self) -> None:
        command = {"schemaVersion": 3, "commandId": 123, "operation": "inspect"}

        with self.assertRaisesRegex(ValueError, "commandId is required"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_unknown_operation_is_rejected(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "bad-operation",
            "operation": "overwrite-state",
        }

        with self.assertRaisesRegex(ValueError, "unsupported operation"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_wrong_schema_is_rejected(self) -> None:
        command = {
            "schemaVersion": 2,
            "commandId": "old-schema",
            "operation": "inspect",
        }

        with self.assertRaisesRegex(ValueError, "schemaVersion 3"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_mutating_commands_require_run_id(self) -> None:
        for operation in ("acquire", "recover", "heartbeat", "release"):
            command = {
                "schemaVersion": 3,
                "commandId": f"missing-run-{operation}",
                "operation": operation,
            }
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, "runId is required"):
                    coordinator.validate_contract(command, working_state(), REPOSITORY)

    def test_empty_run_id_is_rejected(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "empty-run-id",
            "operation": "heartbeat",
            "runId": "",
        }

        with self.assertRaisesRegex(ValueError, "runId is required"):
            coordinator.validate_contract(command, working_state(), REPOSITORY)


class OwnershipLossFixtures(unittest.TestCase):
    def test_foreign_heartbeat_cannot_mutate_active_owner_state(self) -> None:
        state = working_state()
        command = {
            "schemaVersion": 3,
            "commandId": "foreign-heartbeat",
            "operation": "heartbeat",
            "runId": "different-run",
            "phase": "VALIDATION",
            "heartbeatAt": coordinator.now_iso(NOW),
            "leaseExpiresAt": coordinator.now_iso(NOW + timedelta(minutes=30)),
            "workBranch": "foreign/branch",
            "workBranchHeadSha": "foreign-head",
            "pullRequest": 99,
            "checkpointSha": "foreign-checkpoint",
            "note": "must not be applied",
        }

        result = coordinator.apply_command(
            command=command,
            state=state,
            repository=REPOSITORY,
            processed_at=NOW,
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "NOT_LEASE_OWNER")
        self.assertEqual(result.state["runId"], "run-owner")
        self.assertEqual(result.state["phase"], "IMPLEMENTATION")
        self.assertEqual(result.state["workBranch"], "test/branch")
        self.assertEqual(result.state["checkpointSha"], "checkpoint")

    def test_foreign_release_cannot_clear_active_owner_lease(self) -> None:
        state = working_state()
        command = {
            "schemaVersion": 3,
            "commandId": "foreign-release",
            "operation": "release",
            "runId": "different-run",
            "completedAt": coordinator.now_iso(NOW),
            "result": "PASS",
            "checkpointSha": "foreign-final",
            "note": "must not be applied",
        }

        result = coordinator.apply_command(
            command=command,
            state=state,
            repository=REPOSITORY,
            processed_at=NOW,
        )

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "NOT_LEASE_OWNER")
        self.assertEqual(result.state["status"], "working")
        self.assertEqual(result.state["runId"], "run-owner")
        self.assertEqual(result.state["checkpointSha"], "checkpoint")


if __name__ == "__main__":
    unittest.main()
