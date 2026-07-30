#!/usr/bin/env python3
"""Independent terminal guard for Focal automation leases.

It uses the transactional state branch. Expired inactive leases are released using
existing watchdog evidence. Once ``hardKillAt`` passes, the lease is released
unconditionally and recoverable remote work is preserved in ``pendingRecovery``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from tools.automation_state_summary import render_issue_body
from tools.automation_state_v4 import StateStore, _issue_snapshot
from tools.stale_lease_watchdog import (
    GitHubApi,
    active_workflow_runs,
    branch_activity,
    evaluate,
    now_iso,
    parse_timestamp,
    pull_request_activity,
)


@dataclass(frozen=True)
class GuardDecision:
    release: bool
    reason: str


def decide(
    *,
    command: dict[str, Any],
    state: dict[str, Any],
    now: datetime,
    expiry_grace: timedelta,
    activity_grace: timedelta,
    active_runs: list[dict[str, Any]],
    branch_activity_at: datetime | None,
    pr_activity_at: datetime | None,
) -> GuardDecision:
    if state.get("status") == "idle" and state.get("runId") is None:
        return GuardDecision(False, "ALREADY_IDLE")
    if state.get("status") != "working" or not isinstance(state.get("runId"), str):
        return GuardDecision(False, "INVALID_WORKING_STATE")

    hard_kill = parse_timestamp(state.get("hardKillAt") or state.get("deadlineAt"))
    if hard_kill is not None and now >= hard_kill:
        return GuardDecision(True, "HARD_KILL_RELEASED")

    legacy = evaluate(
        command=command,
        state=state,
        now=now,
        expiry_grace=expiry_grace,
        activity_grace=activity_grace,
        active_runs=active_runs,
        branch_activity_at=branch_activity_at,
        pr_activity_at=pr_activity_at,
    )
    if legacy.repair:
        return GuardDecision(True, "STALE_LEASE_RELEASED")
    return GuardDecision(False, legacy.reason)


def release_state(state: dict[str, Any], *, reason: str, released_at: datetime) -> dict[str, Any]:
    updated = dict(state)
    released_at_text = now_iso(released_at)
    pending = {
        "runId": state.get("runId"),
        "phase": state.get("phase"),
        "workBranch": state.get("workBranch"),
        "workBranchHeadSha": state.get("workBranchHeadSha"),
        "pullRequest": state.get("pullRequest"),
        "checkpointSha": state.get("checkpointSha") or state.get("workBranchHeadSha"),
        "reason": reason,
        "releasedAt": released_at_text,
    }
    previous_run = state.get("runId")
    checkpoint = pending["checkpointSha"]
    updated.update(
        {
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "runId": None,
            "startedAt": None,
            "heartbeatAt": None,
            "leaseExpiresAt": None,
            "softStopAt": None,
            "cleanupAt": None,
            "hardKillAt": None,
            "deadlineAt": None,
            "baseMainSha": None,
            "workBranch": None,
            "workBranchHeadSha": None,
            "pullRequest": None,
            "checkpointSha": checkpoint,
            "lastCompletedAt": released_at_text,
            "lastResult": "PARTIAL",
            "lastRunId": previous_run,
            "lastCommandAccepted": True,
            "lastCommandReason": reason,
            "lastCommandProcessedAt": released_at_text,
            "lastWatchdogAt": released_at_text,
            "lastWatchdogAction": reason,
            "pendingRecovery": pending,
            "terminalVerifiedAt": None,
            "terminalVerifiedRunId": None,
            "note": (
                "Automation terminal guard released the lease and preserved the last "
                "remote checkpoint for recovery."
            ),
            "version": int(state.get("version", 0)) + 1,
        }
    )
    return updated


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    command, issue_state = _issue_snapshot(api, repository, args.issue)
    store = StateStore(api, repository, branch=args.state_branch, path=args.state_path)
    stored = store.read(bootstrap=issue_state)
    state = stored.state
    now = datetime.now(timezone.utc)
    runs = active_workflow_runs(api, repository, os.environ.get("GITHUB_RUN_ID"))
    branch_at = branch_activity(api, repository, state.get("workBranch"))
    pr_at = pull_request_activity(api, repository, state.get("pullRequest"))
    decision = decide(
        command=command,
        state=state,
        now=now,
        expiry_grace=timedelta(seconds=args.expiry_grace_seconds),
        activity_grace=timedelta(seconds=args.activity_grace_seconds),
        active_runs=runs,
        branch_activity_at=branch_at,
        pr_activity_at=pr_at,
    )

    summary = {
        "action": "none",
        "reason": decision.reason,
        "runId": state.get("runId"),
        "leaseExpiresAt": state.get("leaseExpiresAt"),
        "hardKillAt": state.get("hardKillAt"),
    }
    if not decision.release:
        print(json.dumps(summary, sort_keys=True))
        return 0

    repaired = release_state(state, reason=decision.reason, released_at=now)
    if not args.dry_run:
        stored = store.write(
            repaired,
            stored.blob_sha,
            message=f"Release automation lease: {decision.reason}",
        )
        current_command, _ = _issue_snapshot(api, repository, args.issue)
        body = render_issue_body(current_command, stored.state)
        api.request("PATCH", f"/repos/{repository}/issues/{args.issue}", {"body": body})
        summary["action"] = "released"
        summary["stateVersion"] = stored.state.get("version")
    else:
        summary["action"] = "dry-run-release"
    print(json.dumps(summary, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    parser.add_argument("--state-branch", default="automation/state-v4")
    parser.add_argument("--state-path", default=".focal/automation-state.json")
    parser.add_argument("--expiry-grace-seconds", type=int, default=120)
    parser.add_argument("--activity-grace-seconds", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except Exception as exc:
        print(f"automation terminal guard failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
