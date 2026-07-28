from __future__ import annotations

import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

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

    def test_supervisor_does_not_consult_wall_clock(self) -> None:
        with mock.patch("tools.runtime_guard.time.time", side_effect=AssertionError("wall clock consulted")):
            result = supervise(
                [sys.executable, "-c", "raise SystemExit(0)"],
                limit_seconds=2.0,
                soft_stop_seconds=1.0,
                grace_seconds=0.2,
                phase="LOCAL_VALIDATION",
            )

        self.assertEqual(result.exit_code, 0)
        self.assertGreaterEqual(result.elapsed_seconds, 0.0)
        self.assertFalse(result.soft_stop_triggered)
        self.assertFalse(result.hard_kill_triggered)

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

    @unittest.skipUnless(hasattr(os, "killpg") and pathlib.Path("/proc").is_dir(), "requires Linux process groups")
    def test_soft_stop_terminates_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_path = pathlib.Path(directory, "child.pid")
            command = (
                "import pathlib,subprocess,sys,time; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(5)']); "
                f"pathlib.Path({str(pid_path)!r}).write_text(str(child.pid), encoding='utf-8'); "
                "time.sleep(5)"
            )
            result = supervise(
                [sys.executable, "-c", command],
                limit_seconds=2.0,
                soft_stop_seconds=0.2,
                grace_seconds=0.2,
                phase="IMPLEMENTATION",
            )

            self.assertTrue(result.soft_stop_triggered)
            child_pid = int(pid_path.read_text(encoding="utf-8"))
            child_state = pathlib.Path(f"/proc/{child_pid}/stat")
            deadline = time.monotonic() + 1.0
            while child_state.exists() and time.monotonic() < deadline:
                fields = child_state.read_text(encoding="utf-8").split()
                if len(fields) > 2 and fields[2] == "Z":
                    break
                time.sleep(0.02)

            if child_state.exists():
                fields = child_state.read_text(encoding="utf-8").split()
                self.assertGreater(len(fields), 2)
                self.assertEqual(fields[2], "Z")

    def test_cli_emits_structured_result_with_final_phase(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.runtime_guard",
                "--limit-seconds",
                "2",
                "--soft-stop-seconds",
                "1",
                "--grace-seconds",
                "0.2",
                "--phase",
                "LOCAL_VALIDATION",
                "--",
                sys.executable,
                "-c",
                "raise SystemExit(0)",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["final_phase"], "LOCAL_VALIDATION")
        self.assertEqual(payload["exit_code"], 0)
        self.assertFalse(payload["soft_stop_triggered"])
        self.assertFalse(payload["hard_kill_triggered"])
        self.assertIsNone(payload["signal_sent"])
        self.assertEqual(payload["command"][-2:], ["-c", "raise SystemExit(0)"])

    def test_cli_emits_structured_error_for_missing_command(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.runtime_guard",
                "--limit-seconds",
                "2",
                "--soft-stop-seconds",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(json.loads(completed.stderr), {"error": "command must not be empty"})

    def test_cli_emits_structured_error_for_launch_failure(self) -> None:
        missing_command = f"focal-command-that-does-not-exist-{os.getpid()}"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.runtime_guard",
                "--limit-seconds",
                "2",
                "--soft-stop-seconds",
                "1",
                "--",
                missing_command,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        payload = json.loads(completed.stderr)
        self.assertIn(missing_command, payload["error"])

    def test_rejects_empty_command(self) -> None:
        with self.assertRaisesRegex(ValueError, "command must not be empty"):
            supervise([], 2.0, 1.0, 0.2, "IMPLEMENTATION")

    def test_rejects_soft_stop_at_or_after_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "soft stop must occur before"):
            supervise([sys.executable, "-c", "pass"], 1.0, 1.0, 0.2, "IMPLEMENTATION")


if __name__ == "__main__":
    unittest.main()
