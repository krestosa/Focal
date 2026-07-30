from __future__ import annotations

import json
import re
import unittest

from tools.automation_state_summary import (
    COMMAND_END,
    COMMAND_START,
    STATE_END,
    STATE_START,
    SUMMARY_END,
    has_single_managed_blocks,
    render_issue_body,
    render_summary,
)


class AutomationStateSummaryTests(unittest.TestCase):
    def assert_callout_below_grid(self, summary: str, marker: str) -> None:
        last_row = summary.rfind("| **")
        callout = summary.index(marker)
        summary_end = summary.index(SUMMARY_END)
        self.assertGreater(callout, last_row)
        self.assertLess(callout, summary_end)

    def test_idle_summary_links_checkpoint_and_references_only_in_markdown(self) -> None:
        state = {
            "repository": "krestosa/Focal",
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "lastResult": "PARTIAL",
            "lastCompletedAt": "2026-07-30T07:42:30Z",
            "checkpointSha": "2e7ef31c6de99b57ddd2fa0f4b35a33f8b62526f",
            "note": (
                "GLCLI-004 merged in PR #93 with Validation run 30523122062 successful; "
                "documentation reconciliation remains recoverable in open PR #94"
            ),
        }
        summary = render_summary(state)
        self.assertIn("## 🟢 IDLE · Disponible", summary)
        self.assertIn("🟡 `PARTIAL`", summary)
        self.assertIn(
            "[`2e7ef31c6de9`](https://github.com/krestosa/Focal/commit/2e7ef31c6de99b57ddd2fa0f4b35a33f8b62526f)",
            summary,
        )
        self.assertIn("[PR #93](https://github.com/krestosa/Focal/pull/93)", summary)
        self.assertIn(
            "[Validation run 30523122062](https://github.com/krestosa/Focal/actions/runs/30523122062)",
            summary,
        )
        self.assertIn("[PR #94](https://github.com/krestosa/Focal/pull/94)", summary)
        self.assertIn("coordinador está libre", summary)
        self.assert_callout_below_grid(summary, "> [!TIP]")

    def test_working_summary_links_branch_pr_checkpoint_workflow_and_run(self) -> None:
        state = {
            "repository": "krestosa/Focal",
            "status": "working",
            "mode": "normal",
            "phase": "REMOTE_STATE_AUDIT",
            "startedAt": "2026-07-30T04:00:00Z",
            "heartbeatAt": "2026-07-30T04:05:00Z",
            "leaseExpiresAt": "2026-07-30T04:35:00Z",
            "workBranch": "feature/example",
            "pullRequest": 84,
            "workflowPath": "validation.yml",
            "workflowRun": 30515739060,
            "checkpointSha": "a" * 40,
            "note": "Reading docs/ROADMAP.md from branch feature/example | safely",
        }
        summary = render_summary(state)
        self.assertIn("## 🔵 WORKING · Ejecución activa", summary)
        self.assertIn("🌐 Operación remota", summary)
        self.assertIn("2026-07-30T04:35:00Z", summary)
        self.assertIn(
            "[`feature/example`](https://github.com/krestosa/Focal/tree/feature/example)",
            summary,
        )
        self.assertIn("[PR #84](https://github.com/krestosa/Focal/pull/84)", summary)
        self.assertIn(
            "[`validation.yml`](https://github.com/krestosa/Focal/actions/workflows/validation.yml)",
            summary,
        )
        self.assertIn(
            "[run 30515739060](https://github.com/krestosa/Focal/actions/runs/30515739060)",
            summary,
        )
        self.assertIn(
            "[`docs/ROADMAP.md`](https://github.com/krestosa/Focal/blob/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/docs/ROADMAP.md)",
            summary,
        )
        self.assertIn(
            "[branch `feature/example`](https://github.com/krestosa/Focal/tree/feature/example)",
            summary,
        )
        self.assertIn("Reading", summary)
        self.assertIn("\\| safely", summary)
        self.assert_callout_below_grid(summary, "> [!IMPORTANT]")

    def test_recovery_and_unknown_callouts_are_below_their_grids(self) -> None:
        recovery = render_summary(
            {
                "repository": "krestosa/Focal",
                "status": "working",
                "mode": "recovery",
                "phase": "RECOVERY",
                "note": "Recovering coordinator state",
            }
        )
        unknown = render_summary(
            {
                "repository": "krestosa/Focal",
                "status": "invalid",
                "mode": "normal",
                "phase": "unknown",
                "note": "Invalid state",
            }
        )
        self.assert_callout_below_grid(recovery, "> [!WARNING]")
        self.assert_callout_below_grid(unknown, "> [!CAUTION]")

    def test_issue_layout_keeps_json_plain_and_machine_readable_below_summary(self) -> None:
        command = {
            "schemaVersion": 3,
            "commandId": "cmd",
            "operation": "inspect",
            "pullRequest": 84,
        }
        state = {
            "schemaVersion": 3,
            "repository": "krestosa/Focal",
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "lastResult": "NO-OP",
            "checkpointSha": "a" * 40,
            "note": "PR #84 validated in run 30515739060",
        }
        body = render_issue_body(command, state)
        self.assertTrue(has_single_managed_blocks(body))
        self.assertLess(body.index("focal-summary:v1"), body.index(COMMAND_START))
        self.assertIn("<details>", body)
        self.assertIn("[PR #84](https://github.com/krestosa/Focal/pull/84)", body)
        self.assertIn(
            "[run 30515739060](https://github.com/krestosa/Focal/actions/runs/30515739060)",
            body,
        )
        command_match = re.search(
            re.escape(COMMAND_START) + r"\s*```json\s*(.*?)\s*```\s*" + re.escape(COMMAND_END),
            body,
            flags=re.DOTALL,
        )
        state_match = re.search(
            re.escape(STATE_START) + r"\s*```json\s*(.*?)\s*```\s*" + re.escape(STATE_END),
            body,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(command_match)
        self.assertIsNotNone(state_match)
        command_json = command_match.group(1)
        state_json = state_match.group(1)
        self.assertNotIn("https://", command_json)
        self.assertNotIn("https://", state_json)
        self.assertNotIn("[PR #", state_json)
        self.assertEqual(command, json.loads(command_json))
        self.assertEqual(state, json.loads(state_json))


if __name__ == "__main__":
    unittest.main()
