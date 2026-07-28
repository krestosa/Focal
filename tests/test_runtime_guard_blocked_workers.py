from __future__ import annotations

import signal
import sys
import unittest

from tools.runtime_guard import supervise


@unittest.skipUnless(hasattr(signal, "SIGTERM"), "requires POSIX signals")
class BlockedWorkerTests(unittest.TestCase):
    def test_blocked_compiler_and_test_workers_stop_at_soft_limit(self) -> None:
        for worker_kind in ("compiler", "test"):
            with self.subTest(worker_kind=worker_kind):
                result = supervise(
                    [sys.executable, "-c", "import time; time.sleep(5)"],
                    limit_seconds=2.0,
                    soft_stop_seconds=0.05,
                    grace_seconds=0.2,
                    phase="LOCAL_VALIDATION",
                )

                self.assertTrue(result.soft_stop_triggered)
                self.assertFalse(result.hard_kill_triggered)
                self.assertEqual(result.final_phase, "LOCAL_VALIDATION")
                self.assertEqual(result.signal_sent, "SIGTERM_SOFT_STOP")
                self.assertIsNotNone(result.exit_code)
                self.assertLess(result.exit_code, 0)
                self.assertLess(result.elapsed_seconds, 2.0)


if __name__ == "__main__":
    unittest.main()
