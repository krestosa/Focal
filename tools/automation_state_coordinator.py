#!/usr/bin/env python3
"""Process commands stored in the canonical Focal automation-state issue.

The trust boundary is GitHub's permission to edit issue #7 plus the command/state
schema and lease invariants. Operational state stores only opaque command and run
identifiers; it must not record the client, model, provider, application, or actor
that submitted a command.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from tools.automation_state_summary import render_issue_body
from tools.stale_lease_watchdog import (
    COMMAND_END,
    COMMAND_START,
    STATE_END,
    STATE_START,
    GitHubApi,
    extract_block,
    parse_timestamp,
)

ALLOWED_OPERATIONS = {
    "acquire",
    "recover",
    "heartbeat",
    "release",
    "inspect",
    "cleanup_branches",
}

# These fields are unnecessary for lease ownership and can expose the execution
# client. Reject them in commands and remove legacy copies from state.
FORBIDDEN_PROVENANCE_FIELDS = {
    "owner",
    "executionSource",
    "client",
    "provider",
    "model",
    "agent",
    "actor",
    "sender",
}


@dataclass(frozen=True)
class ProcessResult:
    state: dict[str, Any]
    accepted: bool
    reason: str
    already_processed: bool = False


def now_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def scrub_provenance(state: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    for key in FORBIDDEN_PROVENANCE_FIELDS:
        updated.pop(key, None)
    updated.pop("lastAbandonedOwner", None)
    return updated


def validate_contract(
    command: dict[str, Any],
    state: dict[str, Any],
    repository: str,
) -> None:
    if command.get("schemaVersion") != 3:
        raise ValueError("command schemaVersion 3 is required")
    if state.get("schemaVersion") != 3:
        raise ValueError("state schemaVersion 3 is required")
    if state.get("repository") != repository:
        raise ValueError("state repository does not match workflow repository")

    present_provenance = sorted(FORBIDDEN_PROVENANCE_FIELDS.intersection(command))
    if present_provenance:
        raise ValueError(
            "operational provenance fields are forbidden: " + ", ".join(present_provenance)
        )

    command_id = command.get("commandId")
    operation = command.get("operation")
    run_id = command.get("runId")
    if not isinstance(command_id, str) or not command_id:
        raise ValueError("commandId is required")
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"unsupported operation: {operation}")
    if operation not in {"inspect", "cleanup_branches"} and (
        not isinstance(run_id, str) or not run_id
    ):
        raise ValueError("runId is required")


def apply_command(
    *,
    command: dict[str, Any],
    state: dict[str, Any],
    repository: str,
    processed_at: datetime,
    cleanup: Callable[[dict[str, Any], dict[str, Any], str], tuple[bool, str]] | None = None,
) -> ProcessResult:
    """Apply one command while preserving unknown non-provenance state fields."""

    validate_contract(command, state, repository)
    command_id = str(command["commandId"])
    if state.get("lastCommandId") == command_id:
        return ProcessResult(scrub_provenance(state), True, "ALREADY_PROCESSED", True)

    updated = scrub_provenance(state)
    operation = command["operation"]
    run_id = command.get("runId")
    current_expiry = parse_timestamp(updated.get("leaseExpiresAt"))
    lease_active = (
        updated.get("status") == "working"
        and current_expiry is not None
        and current_expiry > processed_at
    )
    accepted = False
    reason = ""

    try:
        if operation == "inspect":
            accepted = True
            reason = "STATE_OBSERVED"

        elif operation == "cleanup_branches":
            if cleanup is None:
                raise ValueError("cleanup handler is unavailable")
            accepted, reason = cleanup(command, updated, now_iso(processed_at))

        elif operation in {"acquire", "recover"}:
            requested_expiry = parse_timestamp(command.get("leaseExpiresAt"))
            if requested_expiry is None or requested_expiry <= processed_at:
                raise ValueError("leaseExpiresAt must be in the future")
            if lease_active and updated.get("runId") != run_id:
                reason = "ACTIVE_LEASE"
            else:
                updated.update(
                    {
                        "status": "working",
                        "mode": "recovery" if operation == "recover" else command.get("mode", "normal"),
                        "phase": command.get("phase", "LOCK_ACQUISITION"),
                        "runId": run_id,
                        "startedAt": command.get("startedAt"),
                        "heartbeatAt": command.get("heartbeatAt", command.get("startedAt")),
                        "leaseExpiresAt": command.get("leaseExpiresAt"),
                        "softStopAt": command.get("softStopAt"),
                        "cleanupAt": command.get("cleanupAt"),
                        "hardKillAt": command.get("hardKillAt"),
                        "deadlineAt": command.get("deadlineAt"),
                        "baseMainSha": command.get("baseMainSha"),
                        "workBranch": command.get("workBranch"),
                        "workBranchHeadSha": command.get("workBranchHeadSha"),
                        "pullRequest": command.get("pullRequest"),
                        "checkpointSha": command.get("checkpointSha"),
                        "note": command.get("note"),
                    }
                )
                accepted = True
                reason = "LEASE_ACQUIRED" if operation == "acquire" else "LEASE_RECOVERED"

        elif operation == "heartbeat":
            requested_expiry = parse_timestamp(command.get("leaseExpiresAt"))
            if updated.get("status") != "working" or updated.get("runId") != run_id:
                reason = "NOT_LEASE_OWNER"
            elif requested_expiry is None or requested_expiry <= processed_at:
                raise ValueError("leaseExpiresAt must be in the future")
            else:
                for key in (
                    "phase",
                    "heartbeatAt",
                    "leaseExpiresAt",
                    "workBranch",
                    "workBranchHeadSha",
                    "pullRequest",
                    "checkpointSha",
                    "note",
                ):
                    if key in command:
                        updated[key] = command[key]
                accepted = True
                reason = "HEARTBEAT_ACCEPTED"

        elif operation == "release":
            if updated.get("status") != "working" or updated.get("runId") != run_id:
                reason = "NOT_LEASE_OWNER"
            else:
                previous_run_id = updated.get("runId")
                checkpoint = command.get("checkpointSha", updated.get("checkpointSha"))
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
                        "lastCompletedAt": command.get("completedAt"),
                        "lastResult": command.get("result"),
                        "lastRunId": previous_run_id,
                        "note": command.get("note"),
                    }
                )
                accepted = True
                reason = "LEASE_RELEASED"

    except Exception as exc:
        accepted = False
        reason = f"COMMAND_ERROR: {exc}"

    updated = scrub_provenance(updated)
    updated["lastCommandId"] = command_id
    updated["lastCommandAccepted"] = accepted
    updated["lastCommandReason"] = reason
    updated["lastCommandProcessedAt"] = now_iso(processed_at)
    updated["version"] = int(updated.get("version", 0)) + 1
    return ProcessResult(updated, accepted, reason)


def api_pages(api: GitHubApi, path: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    page = 1
    separator = "&" if "?" in path else "?"
    while True:
        batch = api.request("GET", f"{path}{separator}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError(f"paginated endpoint did not return a list: {path}")
        values.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            return values
        page += 1


def cleanup_branches_handler(
    api: GitHubApi,
    repository: str,
) -> Callable[[dict[str, Any], dict[str, Any], str], tuple[bool, str]]:
    repository_owner = repository.split("/", 1)[0]

    def branch_prs(branch: str, state_name: str) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode(
            {"state": state_name, "head": f"{repository_owner}:{branch}"}
        )
        return api_pages(api, f"/repos/{repository}/pulls?{query}")

    def cleanup(
        command: dict[str, Any],
        state: dict[str, Any],
        processed_at: str,
    ) -> tuple[bool, str]:
        if state.get("status") != "idle":
            return False, "ACTIVE_LEASE"

        legacy = command.get("legacyBranches", ["automation/runtime-state"])
        if not isinstance(legacy, list) or not all(
            isinstance(item, str) and item for item in legacy
        ):
            raise ValueError("legacyBranches must be a list of branch names")
        legacy_names = set(legacy)

        repository_info = api.request("GET", f"/repos/{repository}")
        default_branch = (repository_info or {}).get("default_branch")
        if not isinstance(default_branch, str) or not default_branch:
            raise ValueError("repository default branch is unavailable")

        deleted: list[dict[str, str]] = []
        skipped: list[dict[str, str]] = []
        for branch_info in api_pages(api, f"/repos/{repository}/branches"):
            branch = branch_info.get("name")
            tip_sha = ((branch_info.get("commit") or {}).get("sha"))
            if not isinstance(branch, str) or not isinstance(tip_sha, str):
                continue
            if branch == default_branch:
                skipped.append({"branch": branch, "reason": "DEFAULT_BRANCH"})
                continue
            if branch_info.get("protected"):
                skipped.append({"branch": branch, "reason": "PROTECTED"})
                continue
            if branch_prs(branch, "open"):
                skipped.append({"branch": branch, "reason": "OPEN_PULL_REQUEST"})
                continue

            merged_prs = branch_prs(branch, "closed")
            merged_exact_head = any(
                pr.get("merged_at") and ((pr.get("head") or {}).get("sha") == tip_sha)
                for pr in merged_prs
            )
            base = urllib.parse.quote(branch, safe="")
            head = urllib.parse.quote(default_branch, safe="")
            comparison = api.request("GET", f"/repos/{repository}/compare/{base}...{head}")
            fully_behind = (comparison or {}).get("status") in {"ahead", "identical"}
            is_legacy = branch in legacy_names
            if not (merged_exact_head or fully_behind or is_legacy):
                skipped.append({"branch": branch, "reason": "UNMERGED_WORK_PRESERVED"})
                continue

            encoded = urllib.parse.quote(branch, safe="")
            api.request("DELETE", f"/repos/{repository}/git/refs/heads/{encoded}")
            reason = (
                "LEGACY"
                if is_legacy
                else "FULLY_BEHIND_MAIN"
                if fully_behind
                else "MERGED_PULL_REQUEST"
            )
            deleted.append({"branch": branch, "reason": reason})

        state["lastBranchCleanupAt"] = processed_at
        state["lastBranchCleanupDeleted"] = deleted
        state["lastBranchCleanupSkipped"] = skipped
        state["note"] = command.get("note")
        return True, "BRANCH_CLEANUP_COMPLETED"

    return cleanup


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    issue = api.request("GET", f"/repos/{repository}/issues/{args.issue}")
    body = (issue or {}).get("body") or ""
    command, _, _ = extract_block(body, COMMAND_START, COMMAND_END)
    state, _, _ = extract_block(body, STATE_START, STATE_END)

    result = apply_command(
        command=command,
        state=state,
        repository=repository,
        processed_at=datetime.now(timezone.utc),
        cleanup=cleanup_branches_handler(api, repository),
    )
    if result.already_processed:
        print("command already processed")
        return 0

    updated_body = render_issue_body(command, result.state)
    api.request("PATCH", f"/repos/{repository}/issues/{args.issue}", {"body": updated_body})
    print(
        json.dumps(
            {
                "accepted": result.accepted,
                "reason": result.reason,
                "stateVersion": result.state.get("version"),
                "status": result.state.get("status"),
            },
            sort_keys=True,
        )
    )
    return 0 if result.accepted else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
