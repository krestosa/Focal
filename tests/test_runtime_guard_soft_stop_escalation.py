from __future__ import annotations

import signal
import sys
import unittest

from tools.runtime_guard import supervise


class RuntimeGuardSoftStopEscalationTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(signal, "SIGTERM"), "requires POSIX signals")
    def test_functional_worker_that_ignores_sigterm_is_killed_after_grace(self) -> None:
        command = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(5)"
        )
        result = supervise(
            [sys.executable, "-c", command],
            limit_seconds=2.0,
            soft_stop_seconds=0.5,
            grace_seconds=0.1,
            phase="IMPLEMENTATION",
        )

        self.assertTrue(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)
        self.assertEqual(result.signal_sent, "SIGKILL_SOFT_STOP")
        self.assertIsNotNone(result.exit_code)
        self.assertLess(result.exit_code, 0)
        self.assertLess(result.elapsed_seconds, 1.5)


if __name__ == "__main__":
    unittest.main()
