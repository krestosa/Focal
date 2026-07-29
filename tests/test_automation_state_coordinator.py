from __future__ import annotations

import pathlib
import unittest
from datetime import datetime, timedelta, timezone

from tools import automation_state_coordinator as coordinator


NOW = datetime(2026, 7, 29, 13, 30, tzinfo=timezone.utc)
REPOSITORY = "krestosa/Focal"


def idle_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "schemaVersion": 3,
        "repository": REPOSITORY,
        "version": 10,
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
        "checkpointSha": "checkpoint",
        "lastCommandId": "previous",
        "lastCommandAccepted": True,
        "lastCommandReason": "STATE_OBSERVED",
        "customField": {"preserve": True},
    }
    state.update(overrides)
    return state


def acquire_command(run_id: str = "run-1") -> dict[str, object]:
    started = coordinator.now_iso(NOW)
    return {
        "schemaVersion": 3,
        "commandId": "acquire-1",
        "operation": "acquire",
        "runId": run_id,
        "mode": "normal",
        "phase": "LOCK_ACQUISITION",
        "startedAt": started,
        "heartbeatAt": started,
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


class CommandTests(unittest.TestCase):
    def test_inspect_depends_on_issue_command_not_sender_login(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "inspect-from-installed-app",
            "operation": "inspect",
        }
        result = coordinator.apply_command(
            command=command,
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.reason, "STATE_OBSERVED")
        self.assertEqual(result.state["lastCommandId"], command["commandId"])
        self.assertEqual(result.state["customField"], {"preserve": True})

    def test_acquire_heartbeat_and_release_round_trip(self) -> None:
        acquired = coordinator.apply_command(
            command=acquire_command(),
            state=idle_state(),
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(acquired.accepted)
        self.assertEqual(acquired.reason, "LEASE_ACQUIRED")
        self.assertEqual(acquired.state["status"], "working")
        self.assertEqual(acquired.state["runId"], "run-1")

        heartbeat = {
            "schemaVersion": 3,
            "commandId": "heartbeat-1",
            "operation": "heartbeat",
            "runId": "run-1",
            "phase": "REMOTE_STATE_AUDIT",
            "heartbeatAt": coordinator.now_iso(NOW + timedelta(minutes=1)),
            "leaseExpiresAt": coordinator.now_iso(NOW + timedelta(minutes=31)),
            "workBranch": None,
            "workBranchHeadSha": None,
            "pullRequest": None,
            "checkpointSha": None,
            "note": None,
        }
        renewed = coordinator.apply_command(
            command=heartbeat,
            state=acquired.state,
            repository=REPOSITORY,
            processed_at=NOW + timedelta(minutes=1),
        )
        self.assertTrue(renewed.accepted)
        self.assertEqual(renewed.reason, "HEARTBEAT_ACCEPTED")
        self.assertEqual(renewed.state["phase"], "REMOTE_STATE_AUDIT")

        release = {
            "schemaVersion": 3,
            "commandId": "release-1",
            "operation": "release",
            "runId": "run-1",
            "completedAt": coordinator.now_iso(NOW + timedelta(minutes=2)),
            "result": "PASS",
            "checkpointSha": "final",
            "note": "coordinator smoke test",
        }
        released = coordinator.apply_command(
            command=release,
            state=renewed.state,
            repository=REPOSITORY,
            processed_at=NOW + timedelta(minutes=2),
        )
        self.assertTrue(released.accepted)
        self.assertEqual(released.reason, "LEASE_RELEASED")
        self.assertEqual(released.state["status"], "idle")
        self.assertIsNone(released.state["runId"])
        self.assertEqual(released.state["lastRunId"], "run-1")
        self.assertEqual(released.state["checkpointSha"], "final")

    def test_foreign_active_lease_rejects_acquire(self) -> None:
        state = idle_state(
            status="working",
            runId="other-run",
            leaseExpiresAt=coordinator.now_iso(NOW + timedelta(minutes=10)),
        )
        result = coordinator.apply_command(
            command=acquire_command("new-run"),
            state=state,
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "ACTIVE_LEASE")
        self.assertEqual(result.state["runId"], "other-run")

    def test_duplicate_command_is_idempotent(self) -> None:
        state = idle_state(lastCommandId="same")
        command = {"schemaVersion": 3, "commandId": "same", "operation": "inspect"}
        result = coordinator.apply_command(
            command=command,
            state=state,
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(result.already_processed)
        self.assertEqual(result.state, state)

    def test_provenance_fields_are_rejected_in_commands(self) -> None:
        for field in coordinator.FORBIDDEN_PROVENANCE_FIELDS:
            command = acquire_command()
            command[field] = "forbidden"
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "provenance"):
                    coordinator.validate_contract(command, idle_state(), REPOSITORY)

    def test_legacy_provenance_is_removed_from_state(self) -> None:
        state = idle_state(
            owner="legacy-client",
            executionSource="legacy-source",
            lastAbandonedOwner="legacy-owner",
        )
        command = {
            "schemaVersion": 3,
            "commandId": "inspect-scrub",
            "operation": "inspect",
        }
        result = coordinator.apply_command(
            command=command,
            state=state,
            repository=REPOSITORY,
            processed_at=NOW,
        )
        self.assertTrue(result.accepted)
        self.assertNotIn("owner", result.state)
        self.assertNotIn("executionSource", result.state)
        self.assertNotIn("lastAbandonedOwner", result.state)


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_uses_importable_module_without_sender_allowlist(self) -> None:
        workflow = pathlib.Path(".github/workflows/automation-state.yml").read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH: .", workflow)
        self.assertIn("python -m tools.automation_state_coordinator", workflow)
        self.assertNotIn("unauthorized sender", workflow)
        self.assertNotIn("sender not in", workflow)

    def test_workflow_has_event_loss_fallbacks(self) -> None:
        workflow = pathlib.Path(".github/workflows/automation-state.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "*/5 * * * *"', workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("github.event_name != 'issues'", workflow)

    def test_operational_sources_do_not_name_execution_clients(self) -> None:
        paths = (
            pathlib.Path(".github/workflows/automation-state.yml"),
            pathlib.Path("tools/automation_state_coordinator.py"),
            pathlib.Path("tests/test_automation_state_coordinator.py"),
        )
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        forbidden_fragments = ("chatgpt", "openai", "scheduled-chat", "github-connector")
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, combined)


if __name__ == "__main__":
    unittest.main()
