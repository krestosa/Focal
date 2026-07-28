from __future__ import annotations

import pathlib
import sys
import tempfile
import time
import unittest

from tools.runtime_guard import supervise


class RuntimeGuardWatcherTests(unittest.TestCase):
    def test_soft_stop_terminates_persistent_watcher(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            heartbeat_path = pathlib.Path(directory, "watcher-heartbeat.txt")
            command = (
                "import pathlib,time; "
                f"path=pathlib.Path({str(heartbeat_path)!r}); "
                "counter=0; "
                "exec(\"while True:\\n counter += 1\\n path.write_text(str(counter), encoding='utf-8')\\n time.sleep(0.02)\")"
            )
            result = supervise(
                [sys.executable, "-c", command],
                limit_seconds=2.0,
                soft_stop_seconds=0.2,
                grace_seconds=0.2,
                phase="IMPLEMENTATION",
            )

            self.assertTrue(result.soft_stop_triggered)
            self.assertFalse(result.hard_kill_triggered)
            self.assertEqual(result.signal_sent, "SIGTERM_SOFT_STOP")
            heartbeat_after_stop = heartbeat_path.read_text(encoding="utf-8")
            time.sleep(0.1)
            self.assertEqual(
                heartbeat_path.read_text(encoding="utf-8"),
                heartbeat_after_stop,
            )


if __name__ == "__main__":
    unittest.main()
