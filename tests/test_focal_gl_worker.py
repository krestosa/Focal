import json
import os
import signal
import sys
import tempfile
import unittest
from pathlib import Path

from tools import focal_gl
from tools.focal_gl_worker import run_worker


class FocalGlWorkerTests(unittest.TestCase):
    def test_timeout_terminates_worker_and_preserves_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory)
            execution = run_worker(
                [sys.executable, "-c", "import time; print('started', flush=True); time.sleep(30)"],
                timeout=0.1,
                artifacts=artifacts,
            )
            self.assertEqual(execution.returncode, focal_gl.EXIT_TIMEOUT_OR_CONTEXT_LOSS)
            self.assertTrue(execution.timed_out)
            self.assertIsNone(execution.terminated_by_signal)
            self.assertIn("started", execution.stdout)
            self.assertTrue((artifacts / "worker.stdout.log").is_file())
            self.assertTrue((artifacts / "worker.stderr.log").is_file())
            payload = json.loads((artifacts / "worker-execution.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["timed_out"])
            self.assertEqual(payload["returncode"], focal_gl.EXIT_TIMEOUT_OR_CONTEXT_LOSS)

    @unittest.skipIf(os.name == "nt", "negative signal return codes are POSIX-specific")
    def test_signal_termination_is_classified_as_worker_failure(self) -> None:
        execution = run_worker(
            [
                sys.executable,
                "-c",
                "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
            ],
            timeout=2.0,
        )
        self.assertFalse(execution.timed_out)
        self.assertEqual(execution.terminated_by_signal, signal.SIGTERM)
        self.assertEqual(execution.returncode, -signal.SIGTERM)

    def test_normal_worker_exit_is_preserved(self) -> None:
        execution = run_worker(
            [sys.executable, "-c", "print('ok')"],
            timeout=2.0,
        )
        self.assertEqual(execution.returncode, 0)
        self.assertFalse(execution.timed_out)
        self.assertIsNone(execution.terminated_by_signal)
        self.assertEqual(execution.stdout.strip(), "ok")


if __name__ == "__main__":
    unittest.main()
