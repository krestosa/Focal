#!/usr/bin/env python3
"""Safely release an expired Focal automation lease when no remote work is active."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

COMMAND_START = "<!-- focal-command:v3 -->"
COMMAND_END = "<!-- /focal-command -->"
STATE_START = "<!-- focal-state:v3 -->"
STATE_END = "<!-- /focal-state -->"
ACTIVE_RUN_STATUSES = {"queued", "in_progress", "waiting", "pending", "requested"}
IGNORED_WORKFLOW_NAMES = {
    "Automation State Coordinator",
    "Stale Lease Watchdog",
    "Validation",
}


@dataclass(frozen=True)
class Decision:
    repair: bool
    reason: str


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return parsed.astimezone(timezone.utc)


def now_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_block(body: str, start: str, end: str) -> tuple[dict[str, Any], int, int]:
    pattern = re.compile(
        re.escape(start) + r"\s*```json\s*(.*?)\s*```\s*" + re.escape(end),
        flags=re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        raise ValueError(f"missing or malformed block: {start}")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError(f"block must contain a JSON object: {start}")
    return value, match.start(), match.end()


def replace_state(body: str, state: dict[str, Any]) -> str:
    _, start, end = extract_block(body, STATE_START, STATE_END)
    rendered = json.dumps(state, indent=2, sort_keys=False)
    replacement = f"{STATE_START}\n```json\n{rendered}\n```\n{STATE_END}"
    return body[:start] + replacement + body[end:]


def evaluate(
    *,
    command: dict[str, Any],
    state: dict[str, Any],
    now: datetime,
    expiry_grace: timedelta,
    activity_grace: timedelta,
    active_runs: Iterable[dict[str, Any]],
    branch_activity_at: datetime | None,
    pr_activity_at: datetime | None,
) -> Decision:
    if command.get("schemaVersion") != 3 or state.get("schemaVersion") != 3:
        return Decision(False, "INVALID_SCHEMA")
    if state.get("status") == "idle" and state.get("runId") is None:
        return Decision(False, "ALREADY_IDLE")
    if state.get("status") != "working" or not isinstance(state.get("runId"), str):
        return Decision(False, "INVALID_WORKING_STATE")
    if command.get("commandId") != state.get("lastCommandId"):
        return Decision(False, "UNPROCESSED_COMMAND_PRESENT")

    expiry = parse_timestamp(state.get("leaseExpiresAt"))
    if expiry is None:
        return Decision(False, "MISSING_LEASE_EXPIRY")
    if now < expiry + expiry_grace:
        return Decision(False, "LEASE_NOT_EXPIRED")

    meaningful_runs = [
        run
        for run in active_runs
        if run.get("status") in ACTIVE_RUN_STATUSES
        and run.get("name") not in IGNORED_WORKFLOW_NAMES
    ]
    if meaningful_runs:
        return Decision(False, "ACTIVE_MUTATING_WORKFLOW")

    recent_cutoff = now - activity_grace
    if branch_activity_at is not None and branch_activity_at >= recent_cutoff:
        return Decision(False, "RECENT_BRANCH_ACTIVITY")
    if pr_activity_at is not None and pr_activity_at >= recent_cutoff:
        return Decision(False, "RECENT_PULL_REQUEST_ACTIVITY")

    return Decision(True, "EXPIRED_LEASE_WITHOUT_ACTIVE_REMOTE_WORK")


def repaired_state(state: dict[str, Any], *, repaired_at: datetime) -> dict[str, Any]:
    updated = dict(state)
    abandoned_run_id = state.get("runId")
    checkpoint = state.get("checkpointSha") or state.get("workBranchHeadSha")
    repaired_at_text = now_iso(repaired_at)

    updated.update(
        {
            "status": "idle",
            "mode": "normal",
            "phase": "idle",
            "runId": None,
            "owner": None,
            "executionSource": None,
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
            "lastCompletedAt": repaired_at_text,
            "lastResult": "PARTIAL",
            "lastRunId": abandoned_run_id,
            "note": (
                "Stale Lease Watchdog released an expired lease after confirming "
                "no active mutating workflow or recent branch/PR activity."
            ),
            "lastAbandonedRunId": abandoned_run_id,
            "lastAbandonedOwner": state.get("owner"),
            "lastAbandonedPhase": state.get("phase"),
            "lastAbandonedAt": repaired_at_text,
            "lastAbandonedLeaseExpiresAt": state.get("leaseExpiresAt"),
            "lastAbandonedWorkBranch": state.get("workBranch"),
            "lastAbandonedWorkBranchHeadSha": state.get("workBranchHeadSha"),
            "lastAbandonedPullRequest": state.get("pullRequest"),
            "lastAbandonedCheckpointSha": checkpoint,
            "lastAbandonedReason": "EXPIRED_LEASE_WITHOUT_ACTIVE_REMOTE_WORK",
            "lastWatchdogAt": repaired_at_text,
            "lastWatchdogAction": "STALE_LEASE_RELEASED",
            "version": int(state.get("version", 0)) + 1,
        }
    )
    return updated


class GitHubApi:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "focal-stale-lease-watchdog",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API {method} {path} failed: {exc.code} {details}"
            ) from exc
        return json.loads(raw) if raw else None


def active_workflow_runs(api: GitHubApi, repository: str, current_run_id: str | None) -> list[dict[str, Any]]:
    response = api.request("GET", f"/repos/{repository}/actions/runs?per_page=100")
    runs = response.get("workflow_runs", []) if isinstance(response, dict) else []
    result: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        if current_run_id and str(run.get("id")) == current_run_id:
            continue
        if run.get("status") in ACTIVE_RUN_STATUSES:
            result.append(run)
    return result


def branch_activity(api: GitHubApi, repository: str, branch: Any) -> datetime | None:
    if not isinstance(branch, str) or not branch:
        return None
    encoded = urllib.parse.quote(branch, safe="")
    try:
        data = api.request("GET", f"/repos/{repository}/branches/{encoded}")
    except RuntimeError as exc:
        if "failed: 404" in str(exc):
            return None
        raise
    commit = (data or {}).get("commit") or {}
    commit_data = commit.get("commit") or {}
    committer = commit_data.get("committer") or {}
    author = commit_data.get("author") or {}
    return parse_timestamp(committer.get("date") or author.get("date"))


def pull_request_activity(api: GitHubApi, repository: str, number: Any) -> datetime | None:
    if not isinstance(number, int) or number <= 0:
        return None
    data = api.request("GET", f"/repos/{repository}/pulls/{number}")
    return parse_timestamp((data or {}).get("updated_at"))


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    issue = api.request("GET", f"/repos/{repository}/issues/{args.issue}")
    body = (issue or {}).get("body") or ""
    command, _, _ = extract_block(body, COMMAND_START, COMMAND_END)
    state, _, _ = extract_block(body, STATE_START, STATE_END)
    if state.get("repository") != repository:
        raise ValueError("state repository does not match workflow repository")

    now = datetime.now(timezone.utc)
    active_runs = active_workflow_runs(api, repository, os.environ.get("GITHUB_RUN_ID"))
    branch_at = branch_activity(api, repository, state.get("workBranch"))
    pr_at = pull_request_activity(api, repository, state.get("pullRequest"))
    decision = evaluate(
        command=command,
        state=state,
        now=now,
        expiry_grace=timedelta(seconds=args.expiry_grace_seconds),
        activity_grace=timedelta(seconds=args.activity_grace_seconds),
        active_runs=active_runs,
        branch_activity_at=branch_at,
        pr_activity_at=pr_at,
    )

    summary = {
        "action": "none",
        "reason": decision.reason,
        "runId": state.get("runId"),
        "leaseExpiresAt": state.get("leaseExpiresAt"),
        "activeRuns": [
            {"id": run.get("id"), "name": run.get("name"), "status": run.get("status")}
            for run in active_runs
            if run.get("name") not in IGNORED_WORKFLOW_NAMES
        ],
        "branchActivityAt": now_iso(branch_at) if branch_at else None,
        "pullRequestActivityAt": now_iso(pr_at) if pr_at else None,
    }

    if not decision.repair:
        print(json.dumps(summary, sort_keys=True))
        return 0

    new_state = repaired_state(state, repaired_at=now)
    updated_body = replace_state(body, new_state)
    if not args.dry_run:
        api.request("PATCH", f"/repos/{repository}/issues/{args.issue}", {"body": updated_body})
        summary["action"] = "released"
        summary["stateVersion"] = new_state["version"]
    else:
        summary["action"] = "dry-run-release"
    print(json.dumps(summary, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    parser.add_argument("--expiry-grace-seconds", type=int, default=120)
    parser.add_argument("--activity-grace-seconds", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except Exception as exc:
        print(f"stale lease watchdog failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
