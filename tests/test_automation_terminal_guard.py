from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_terminal_guard as guard


NOW = datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc)


def working_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "schemaVersion": 3,
        "repository": "krestosa/Focal",
        "version": 8,
        "status": "working",
        "mode": "normal",
        "phase": "CI_VALIDATION",
        "runId": "run-guard",
        "startedAt": "2026-07-30T08:00:00Z",
        "heartbeatAt": "2026-07-30T08:20:00Z",
        "leaseExpiresAt": "2026-07-30T08:30:00Z",
        "softStopAt": "2026-07-30T08:50:00Z",
        "cleanupAt": "2026-07-30T08:55:00Z",
        "hardKillAt": "2026-07-30T09:00:00Z",
        "deadlineAt": "2026-07-30T09:00:00Z",
        "workBranch": "feature/example",
        "workBranchHeadSha": "head-sha",
        "pullRequest": 123,
        "checkpointSha": "checkpoint-sha",
        "lastCommandId": "heartbeat-command",
    }
    state.update(overrides)
    return state


class GuardTests(unittest.TestCase):
    def test_hard_kill_releases_even_when_remote_activity_exists(self) -> None:
        decision = guard.decide(
            command={"schemaVersion": 3, "commandId": "heartbeat-command"},
            state=working_state(),
            now=NOW,
            expiry_grace=timedelta(seconds=120),
            activity_grace=timedelta(minutes=15),
            active_runs=[{"status": "in_progress", "name": "Mutating delivery"}],
            branch_activity_at=NOW,
            pr_activity_at=NOW,
        )
        self.assertTrue(decision.release)
        self.assertEqual(decision.reason, "HARD_KILL_RELEASED")

    def test_release_preserves_recovery_checkpoint_and_clears_lease(self) -> None:
        released = guard.release_state(
            working_state(),
            reason="HARD_KILL_RELEASED",
            released_at=NOW,
        )
        self.assertEqual(released["status"], "idle")
        self.assertIsNone(released["runId"])
        self.assertEqual(released["lastResult"], "PARTIAL")
        self.assertEqual(released["pendingRecovery"]["pullRequest"], 123)
        self.assertEqual(released["pendingRecovery"]["checkpointSha"], "checkpoint-sha")


if __name__ == "__main__":
    unittest.main()
