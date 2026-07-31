"""Process isolation and watchdog for the public ``focal-gl`` command."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tools.focal_gl import (
    EXIT_TIMEOUT_OR_CONTEXT_LOSS,
    SCHEMA_VERSION,
    VERSION,
    Result,
    build_parser,
    emit,
)

_WORKER_ENV = "FOCAL_GL_ISOLATED_WORKER"
_TERMINATION_GRACE_SECONDS = 1.0


@dataclass(frozen=True)
class WorkerExecution:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    terminated_by_signal: int | None


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _write_worker_artifacts(
    artifacts: Path | None,
    execution: WorkerExecution,
) -> None:
    if artifacts is None:
        return
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "worker.stdout.log").write_text(execution.stdout, encoding="utf-8")
    (artifacts / "worker.stderr.log").write_text(execution.stderr, encoding="utf-8")
    (artifacts / "worker-execution.json").write_text(
        json.dumps(asdict(execution), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.terminate()
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)


def run_worker(
    command: Sequence[str],
    *,
    timeout: float,
    artifacts: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> WorkerExecution:
    """Run one command in an isolated process and enforce a hard timeout."""
    child_env = dict(os.environ)
    if env:
        child_env.update(env)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        list(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        returncode = process.returncode
        terminated_by_signal = -returncode if returncode < 0 else None
        execution = WorkerExecution(
            returncode=returncode,
            stdout=_as_text(stdout),
            stderr=_as_text(stderr),
            timed_out=False,
            terminated_by_signal=terminated_by_signal,
        )
    except subprocess.TimeoutExpired as exc:
        partial_stdout = _as_text(exc.stdout)
        partial_stderr = _as_text(exc.stderr)
        _terminate_process_tree(process)
        stdout, stderr = process.communicate()
        completed_stdout = _as_text(stdout)
        completed_stderr = _as_text(stderr)
        execution = WorkerExecution(
            returncode=EXIT_TIMEOUT_OR_CONTEXT_LOSS,
            stdout=completed_stdout or partial_stdout,
            stderr=completed_stderr or partial_stderr,
            timed_out=True,
            terminated_by_signal=None,
        )
    _write_worker_artifacts(artifacts, execution)
    return execution


def _worker_failure_result(args, execution: WorkerExecution) -> Result:
    if execution.timed_out:
        message = f"isolated worker exceeded the {args.timeout:g}s timeout and was terminated"
    else:
        message = f"isolated worker terminated by signal {execution.terminated_by_signal}"
    return Result(
        SCHEMA_VERSION,
        VERSION,
        args.command,
        "FAIL",
        EXIT_TIMEOUT_OR_CONTEXT_LOSS,
        "STATIC",
        message,
        str(args.artifacts) if args.artifacts else None,
        {
            "worker": {
                "timedOut": execution.timed_out,
                "terminatedBySignal": execution.terminated_by_signal,
            }
        },
    )


def _dispatch_isolated(arguments: Sequence[str]) -> int:
    from tools.focal_gl_dispatch import main as dispatch_main

    args = build_parser().parse_args(list(arguments))
    if args.command == "probe" and args.backend == "wgl":
        from tools.wgl_dispatch import wgl_probe_result

        result = wgl_probe_result(args)
        emit(result, args.json_output)
        return result.exitCode
    return dispatch_main(arguments)


def main(argv: Sequence[str] | None = None) -> int:
    from tools.focal_gl_dispatch import main as dispatch_main

    arguments = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get(_WORKER_ENV) == "1":
        return _dispatch_isolated(arguments)

    if not arguments or "--help" in arguments or "-h" in arguments or "--version" in arguments:
        return dispatch_main(arguments)

    args = build_parser().parse_args(arguments)
    root_entrypoint = Path(__file__).resolve().parents[1] / "focal-gl"
    execution = run_worker(
        [sys.executable, str(root_entrypoint), *arguments],
        timeout=args.timeout,
        artifacts=args.artifacts,
        env={_WORKER_ENV: "1"},
    )
    if execution.timed_out or execution.terminated_by_signal is not None:
        result = _worker_failure_result(args, execution)
        emit(result, args.json_output)
        if execution.stderr:
            print(execution.stderr, file=sys.stderr, end="")
        return result.exitCode

    if execution.stdout:
        print(execution.stdout, end="")
    if execution.stderr:
        print(execution.stderr, file=sys.stderr, end="")
    return execution.returncode
