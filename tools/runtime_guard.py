"""Bounded process supervisor for autonomous Focal tasks."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Sequence

_ALLOWED_AFTER_SOFT_STOP = {
    "COMMITTING",
    "PUBLISHING",
    "PR_FINALIZATION",
    "MERGING",
    "POST_MERGE",
    "CHECKPOINT_ONLY",
    "CLEANUP",
    "LOCK_RELEASE",
}


@dataclass
class GuardResult:
    command: list[str]
    exit_code: int | None
    elapsed_seconds: float
    soft_stop_triggered: bool
    hard_kill_triggered: bool
    final_phase: str
    signal_sent: str | None


def _positive_seconds(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _terminate_group(pid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        return


def supervise(
    command: Sequence[str],
    limit_seconds: float,
    soft_stop_seconds: float,
    grace_seconds: float,
    phase: str,
) -> GuardResult:
    if not command:
        raise ValueError("command must not be empty")
    if soft_stop_seconds >= limit_seconds:
        raise ValueError("soft stop must occur before the hard limit")

    started = time.monotonic()
    process = subprocess.Popen(list(command), start_new_session=True)
    soft_triggered = False
    hard_triggered = False
    sent: str | None = None

    try:
        while process.poll() is None:
            elapsed = time.monotonic() - started
            if not soft_triggered and elapsed >= soft_stop_seconds:
                soft_triggered = True
                if phase not in _ALLOWED_AFTER_SOFT_STOP:
                    _terminate_group(process.pid, signal.SIGTERM)
                    sent = "SIGTERM_SOFT_STOP"
            if elapsed >= limit_seconds:
                hard_triggered = True
                _terminate_group(process.pid, signal.SIGTERM)
                sent = "SIGTERM_HARD_LIMIT"
                try:
                    process.wait(timeout=grace_seconds)
                except subprocess.TimeoutExpired:
                    _terminate_group(process.pid, signal.SIGKILL)
                    sent = "SIGKILL_HARD_LIMIT"
                break
            time.sleep(min(0.1, max(0.01, limit_seconds - elapsed)))
    finally:
        if process.poll() is None:
            _terminate_group(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                _terminate_group(process.pid, signal.SIGKILL)
                process.wait()

    elapsed = time.monotonic() - started
    return GuardResult(
        list(command),
        process.returncode,
        elapsed,
        soft_triggered,
        hard_triggered,
        phase,
        sent,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-seconds", type=_positive_seconds, default=3510.0)
    parser.add_argument("--soft-stop-seconds", type=_positive_seconds, default=3000.0)
    parser.add_argument("--grace-seconds", type=_positive_seconds, default=8.0)
    parser.add_argument("--phase", default="IMPLEMENTATION")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    try:
        result = supervise(
            command,
            args.limit_seconds,
            args.soft_stop_seconds,
            args.grace_seconds,
            args.phase,
        )
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True))
    return result.exit_code if result.exit_code is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
