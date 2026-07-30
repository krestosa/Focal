from __future__ import annotations

import pathlib
import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_state_v4 as v4


NOW = datetime(2026, 7, 30, 9, 0, tzinfo=timezone.utc)
REPOSITORY = "krestosa/Focal"


def idle_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "schemaVersion": 3,
        "repository": REPOSITORY,
        "version": 20,
        "status": "idle",
        "mode": "normal",
        "phase": "idle",
        "runId": None,
        "startedAt": None,
        "heartbeatAt": None,
        "leaseExpiresAt": None,
        "softStopAt": None,
        "cleanupAt": None,
        "hardKillAt": None,
        "deadlineAt": None,
        "baseMainSha": None,
        "workBranch": None,
        "workBranchHeadSha": None,
        "pullRequest": None,
        "checkpointSha": "base-checkpoint",
        "lastCommandId": "previous",
        "lastCommandAccepted": True,
        "lastCommandReason": "LEASE_RELEASED",
        "lastRunId": "previous-run",
        "processedCommandIds": ["old-command"],
    }
    state.update(overrides)
    return state


def acquire_command() -> dict[str, object]:
    return {
        "schemaVersion": 3,
        "commandId": "acquire-v4",
        "operation": "acquire",
        "runId": "run-v4",
        "mode": "normal",
        "phase": "LOCK_ACQUISITION",
        "startedAt": v4.now_iso(NOW),
        "heartbeatAt": v4.now_iso(NOW),
        "leaseExpiresAt": v4.now_iso(NOW + timedelta(minutes=30)),
        "softStopAt": v4.now_iso(NOW + timedelta(minutes=50)),
        "cleanupAt": v4.now_iso(NOW + timedelta(minutes=55)),
        "hardKillAt": v4.now_iso(NOW + timedelta(minutes=58)),
        "deadlineAt": v4.now_iso(NOW + timedelta(minutes=58)),
        "baseMainSha": "base-sha",
        "checkpointSha": "base-sha",
    }


class TransactionalCommandTests(unittest.TestCase):
    def test_processed_ledger_blocks_non_adjacent_replay(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "old-command",
            "operation": "inspect",
        }
        result = v4.apply_v4_command(
            command=command,
            state=idle_state(lastCommandId="different-command"),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(result.already_processed)
        self.assertEqual(result.reason, "ALREADY_PROCESSED")

    def test_expected_state_version_rejects_stale_writer(self) -> None:
        command = acquire_command()
        command["expectedStateVersion"] = 19
        result = v4.apply_v4_command(
            command=command,
            state=idle_state(version=20),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "STATE_VERSION_MISMATCH")
        self.assertEqual(result.state["status"], "idle")

    def test_phase_checkpoint_is_recorded_on_acquire(self) -> None:
        result = v4.apply_v4_command(
            command=acquire_command(),
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(result.accepted)
        checkpoint = result.state["phaseCheckpoints"]["LOCK_ACQUISITION"]
        self.assertEqual(checkpoint["commandId"], "acquire-v4")
        self.assertEqual(checkpoint["checkpointSha"], "base-sha")

    def test_release_separates_functional_delivery_from_reconciliation(self) -> None:
        acquired = v4.apply_v4_command(
            command=acquire_command(),
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        ).state
        release = {
            "schemaVersion": 3,
            "commandId": "release-v4",
            "operation": "release",
            "runId": "run-v4",
            "completedAt": v4.now_iso(NOW + timedelta(minutes=5)),
            "result": "PARTIAL",
            "checkpointSha": "functional-merge",
            "functionalCheckpointSha": "functional-merge",
            "reconciliationPullRequest": 94,
            "reconciliationBranch": "docs/reconcile-glcli-004",
            "reconciliationCheckpointSha": "docs-head",
            "reconciliationStatus": "pending",
        }
        result = v4.apply_v4_command(
            command=release,
            state=acquired,
            repository=REPOSITORY,
            processed_at=NOW + timedelta(minutes=5),
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.state["status"], "idle")
        self.assertEqual(result.state["functionalCheckpointSha"], "functional-merge")
        self.assertEqual(result.state["reconciliation"]["pullRequest"], 94)
        self.assertEqual(result.state["reconciliation"]["status"], "pending")

    def test_terminal_assertion_requires_idle_state_for_same_run(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "assert-terminal",
            "operation": "assert_terminal",
            "runId": "run-v4",
        }
        rejected = v4.apply_v4_command(
            command=command,
            state=idle_state(status="working", runId="run-v4"),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertFalse(rejected.accepted)

        accepted = v4.apply_v4_command(
            command=command,
            state=idle_state(lastRunId="run-v4", processedCommandIds=[]),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.reason, "TERMINAL_STATE_CONFIRMED")
        self.assertEqual(accepted.state["terminalVerifiedRunId"], "run-v4")


class WorkflowContractTests(unittest.TestCase):
    def test_coordinator_uses_transactional_state_and_always_mirrors(self) -> None:
        workflow = pathlib.Path(".github/workflows/automation-state.yml").read_text(encoding="utf-8")
        self.assertIn("tools.automation_state_v4", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("--mirror-only", workflow)


if __name__ == "__main__":
    unittest.main()
