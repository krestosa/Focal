from __future__ import annotations

import json
import re
import unittest

from tools.automation_state_summary import (
    COMMAND_END,
    COMMAND_START,
    STATE_END,
    STATE_START,
    has_single_managed_blocks,
    render_issue_body,
    render_summary,
)


class AutomationStateSummaryTests(unittest.TestCase):
    def test_idle_summary_places_result_and_checkpoint_first(self) -> None:
        state = {
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "lastResult": "PASS",
            "lastCompletedAt": "2026-07-30T04:20:46Z",
            "checkpointSha": "cf02daaca6d5236bae2023dcb6b7d689b770cda4",
            "note": "Canonical reconciliation complete",
        }
        summary = render_summary(state)
        self.assertIn("## 🟢 IDLE · Disponible", summary)
        self.assertIn("✅ `PASS`", summary)
        self.assertIn("`cf02daaca6d5`", summary)
        self.assertIn("coordinador está libre", summary)

    def test_working_summary_surfaces_remote_activity_and_lease(self) -> None:
        state = {
            "status": "working",
            "mode": "normal",
            "phase": "REMOTE_STATE_AUDIT",
            "startedAt": "2026-07-30T04:00:00Z",
            "heartbeatAt": "2026-07-30T04:05:00Z",
            "leaseExpiresAt": "2026-07-30T04:35:00Z",
            "workBranch": "feature/example",
            "pullRequest": 84,
            "checkpointSha": "a" * 40,
            "note": "Reading remote state | safely",
        }
        summary = render_summary(state)
        self.assertIn("## 🔵 WORKING · Ejecución activa", summary)
        self.assertIn("🌐 Operación remota", summary)
        self.assertIn("2026-07-30T04:35:00Z", summary)
        self.assertIn("Reading remote state \\| safely", summary)

    def test_issue_layout_keeps_json_machine_readable_below_summary(self) -> None:
        command = {"schemaVersion": 3, "commandId": "cmd", "operation": "inspect"}
        state = {
            "schemaVersion": 3,
            "repository": "krestosa/Focal",
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "lastResult": "NO-OP",
        }
        body = render_issue_body(command, state)
        self.assertTrue(has_single_managed_blocks(body))
        self.assertLess(body.index("focal-summary:v1"), body.index(COMMAND_START))
        self.assertIn("<details>", body)
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
        self.assertEqual(command, json.loads(command_match.group(1)))
        self.assertEqual(state, json.loads(state_match.group(1)))


if __name__ == "__main__":
    unittest.main()
