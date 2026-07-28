from __future__ import annotations

import sys
import unittest
from unittest import mock

from tools.runtime_guard import supervise


class RuntimeGuardPhaseGateTests(unittest.TestCase):
    def test_rejects_functional_phase_after_soft_stop_without_launching(self) -> None:
        with mock.patch("tools.runtime_guard.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "not allowed after soft stop"):
                supervise(
                    [sys.executable, "-c", "raise SystemExit(0)"],
                    limit_seconds=2.0,
                    soft_stop_seconds=1.0,
                    grace_seconds=0.2,
                    phase="IMPLEMENTATION",
                    soft_stop_active=True,
                )

        popen.assert_not_called()

    def test_allows_finalization_phase_after_soft_stop(self) -> None:
        result = supervise(
            [sys.executable, "-c", "raise SystemExit(0)"],
            limit_seconds=2.0,
            soft_stop_seconds=1.0,
            grace_seconds=0.2,
            phase="CLEANUP",
            soft_stop_active=True,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)
        self.assertEqual(result.final_phase, "CLEANUP")
        self.assertIsNone(result.signal_sent)


if __name__ == "__main__":
    unittest.main()
