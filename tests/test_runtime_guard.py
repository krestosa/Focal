from __future__ import annotations

import signal
import sys
import unittest

from tools.runtime_guard import supervise


class RuntimeGuardTests(unittest.TestCase):
    def test_command_completes_before_soft_stop(self) -> None:
        result = supervise(
            [sys.executable, "-c", "raise SystemExit(0)"],
            limit_seconds=2.0,
            soft_stop_seconds=1.0,
            grace_seconds=0.2,
            phase="IMPLEMENTATION",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)
        self.assertIsNone(result.signal_sent)

    def test_functional_phase_stops_at_soft_stop(self) -> None:
        result = supervise(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            limit_seconds=2.0,
            soft_stop_seconds=0.05,
            grace_seconds=0.2,
            phase="IMPLEMENTATION",
        )

        self.assertTrue(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)
        self.assertEqual(result.signal_sent, "SIGTERM_SOFT_STOP")
        self.assertLess(result.elapsed_seconds, 2.0)

    def test_allowed_phase_continues_after_soft_stop(self) -> None:
        result = supervise(
            [sys.executable, "-c", "import time; time.sleep(0.15)"],
            limit_seconds=1.0,
            soft_stop_seconds=0.03,
            grace_seconds=0.2,
            phase="CLEANUP",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)
        self.assertIsNone(result.signal_sent)

    @unittest.skipUnless(hasattr(signal, "SIGTERM"), "requires POSIX signals")
    def test_hard_limit_escalates_when_sigterm_is_ignored(self) -> None:
        command = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(5)"
        )
        result = supervise(
            [sys.executable, "-c", command],
            limit_seconds=0.5,
            soft_stop_seconds=0.1,
            grace_seconds=0.1,
            phase="CLEANUP",
        )

        self.assertTrue(result.soft_stop_triggered)
        self.assertTrue(result.hard_kill_triggered)
        self.assertEqual(result.signal_sent, "SIGKILL_HARD_LIMIT")
        self.assertLess(result.elapsed_seconds, 1.5)

    def test_rejects_empty_command(self) -> None:
        with self.assertRaisesRegex(ValueError, "command must not be empty"):
            supervise([], 2.0, 1.0, 0.2, "IMPLEMENTATION")

    def test_rejects_soft_stop_at_or_after_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "soft stop must occur before"):
            supervise([sys.executable, "-c", "pass"], 1.0, 1.0, 0.2, "IMPLEMENTATION")


if __name__ == "__main__":
    unittest.main()
