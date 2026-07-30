#!/usr/bin/env python3
"""Transactional automation-state coordinator backed by a dedicated Git branch.

The issue remains the command ingress and human-readable mirror. Canonical mutable
state is stored in ``.focal/automation-state.json`` on ``automation/state-v4`` and
is updated with the contents API's blob-SHA compare-and-swap semantics.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from tools.automation_state_coordinator import apply_command, now_iso, scrub_provenance
from tools.automation_state_summary import render_issue_body
from tools.stale_lease_watchdog import (
    COMMAND_END,
    COMMAND_START,
    STATE_END,
    STATE_START,
    GitHubApi,
    extract_block,
)

STATE_BRANCH = "automation/state-v4"
STATE_PATH = ".focal/automation-state.json"
PROCESSED_COMMAND_LIMIT = 64
TERMINAL_REASONS = {
    "LEASE_RELEASED",
    "STALE_LEASE_RELEASED",
    "CLEANUP_DEADLINE_RELEASED",
    "HARD_KILL_RELEASED",
    "TERMINAL_STATE_CONFIRMED",
}


@dataclass(frozen=True)
class StoredState:
    state: dict[str, Any]
    blob_sha: str


@dataclass(frozen=True)
class V4Result:
    state: dict[str, Any]
    accepted: bool
    reason: str
    already_processed: bool = False


def _is_not_found(exc: Exception) -> bool:
    text = str(exc)
    return "failed: 404" in text or '"status":"404"' in text


def _bounded_ids(state: dict[str, Any], command_id: str) -> list[str]:
    current = state.get("processedCommandIds")
    values = [item for item in current if isinstance(item, str)] if isinstance(current, list) else []
    if command_id not in values:
        values.append(command_id)
    return values[-PROCESSED_COMMAND_LIMIT:]


def _record_custom_result(
    state: dict[str, Any],
    *,
    command_id: str,
    accepted: bool,
    reason: str,
    processed_at: datetime,
) -> dict[str, Any]:
    updated = scrub_provenance(state)
    updated["lastCommandId"] = command_id
    updated["lastCommandAccepted"] = accepted
    updated["lastCommandReason"] = reason
    updated["lastCommandProcessedAt"] = now_iso(processed_at)
    updated["processedCommandIds"] = _bounded_ids(updated, command_id)
    updated["version"] = int(updated.get("version", 0)) + 1
    return updated


def _expected_state_matches(command: dict[str, Any], state: dict[str, Any]) -> tuple[bool, str]:
    expected_version = command.get("expectedStateVersion")
    if expected_version is not None and expected_version != state.get("version"):
        return False, "STATE_VERSION_MISMATCH"
    expected_checkpoint = command.get("expectedCheckpointSha")
    if expected_checkpoint is not None and expected_checkpoint != state.get("checkpointSha"):
        return False, "CHECKPOINT_MISMATCH"
    return True, "EXPECTED_STATE_MATCHED"


def _checkpoint_record(command: dict[str, Any], state: dict[str, Any], processed_at: datetime) -> None:
    phase = state.get("phase")
    if not isinstance(phase, str) or not phase:
        return
    checkpoints = state.get("phaseCheckpoints")
    if not isinstance(checkpoints, dict):
        checkpoints = {}
    checkpoints = dict(checkpoints)
    checkpoints[phase] = {
        "commandId": command.get("commandId"),
        "checkpointSha": state.get("checkpointSha"),
        "workBranch": state.get("workBranch"),
        "workBranchHeadSha": state.get("workBranchHeadSha"),
        "pullRequest": state.get("pullRequest"),
        "processedAt": now_iso(processed_at),
    }
    state["phaseCheckpoints"] = checkpoints


def _record_release_handoff(command: dict[str, Any], state: dict[str, Any], processed_at: datetime) -> None:
    checkpoint = command.get("functionalCheckpointSha") or state.get("checkpointSha")
    if checkpoint is not None:
        state["functionalCheckpointSha"] = checkpoint

    reconciliation_pr = command.get("reconciliationPullRequest")
    reconciliation_sha = command.get("reconciliationCheckpointSha")
    reconciliation_branch = command.get("reconciliationBranch")
    if reconciliation_pr is None and reconciliation_sha is None and reconciliation_branch is None:
        state.pop("reconciliation", None)
        return

    state["reconciliation"] = {
        "status": command.get("reconciliationStatus", "pending"),
        "pullRequest": reconciliation_pr,
        "branch": reconciliation_branch,
        "checkpointSha": reconciliation_sha,
        "note": command.get("reconciliationNote"),
        "recordedAt": now_iso(processed_at),
    }


def apply_v4_command(
    *,
    command: dict[str, Any],
    state: dict[str, Any],
    repository: str,
    processed_at: datetime,
) -> V4Result:
    command_id = command.get("commandId")
    if not isinstance(command_id, str) or not command_id:
        raise ValueError("commandId is required")
    if command.get("schemaVersion") != 3:
        raise ValueError("command schemaVersion 3 is required")
    if state.get("schemaVersion") != 3 or state.get("repository") != repository:
        raise ValueError("canonical state contract mismatch")

    processed_ids = state.get("processedCommandIds")
    if isinstance(processed_ids, list) and command_id in processed_ids:
        return V4Result(scrub_provenance(state), True, "ALREADY_PROCESSED", True)

    matches, mismatch_reason = _expected_state_matches(command, state)
    if not matches:
        rejected = _record_custom_result(
            state,
            command_id=command_id,
            accepted=False,
            reason=mismatch_reason,
            processed_at=processed_at,
        )
        return V4Result(rejected, False, mismatch_reason)

    operation = command.get("operation")
    if operation == "assert_terminal":
        requested_run = command.get("runId")
        last_run = state.get("lastRunId")
        terminal = state.get("status") == "idle" and state.get("runId") is None
        same_run = requested_run is None or requested_run == last_run
        accepted = terminal and same_run and state.get("lastCommandReason") in TERMINAL_REASONS
        reason = "TERMINAL_STATE_CONFIRMED" if accepted else "TERMINAL_STATE_NOT_CONFIRMED"
        updated = _record_custom_result(
            state,
            command_id=command_id,
            accepted=accepted,
            reason=reason,
            processed_at=processed_at,
        )
        if accepted:
            updated["terminalVerifiedAt"] = now_iso(processed_at)
            updated["terminalVerifiedRunId"] = requested_run or last_run
        return V4Result(updated, accepted, reason)

    base = apply_command(
        command=command,
        state=state,
        repository=repository,
        processed_at=processed_at,
    )
    updated = dict(base.state)
    before_ids = updated.get("processedCommandIds")
    updated["processedCommandIds"] = _bounded_ids(updated, command_id)
    ledger_changed = updated["processedCommandIds"] != before_ids
    if base.accepted and operation in {"acquire", "recover", "heartbeat"}:
        _checkpoint_record(command, updated, processed_at)
    if base.accepted and operation == "release":
        _record_release_handoff(command, updated, processed_at)
        updated["terminalVerifiedAt"] = None
        updated["terminalVerifiedRunId"] = None
    return V4Result(
        updated,
        base.accepted,
        base.reason,
        base.already_processed and not ledger_changed,
    )


class StateStore:
    def __init__(
        self,
        api: GitHubApi,
        repository: str,
        *,
        branch: str = STATE_BRANCH,
        path: str = STATE_PATH,
    ) -> None:
        self.api = api
        self.repository = repository
        self.branch = branch
        self.path = path

    def _contents_path(self) -> str:
        encoded_path = urllib.parse.quote(self.path, safe="/")
        encoded_ref = urllib.parse.quote(self.branch, safe="")
        return f"/repos/{self.repository}/contents/{encoded_path}?ref={encoded_ref}"

    def _ensure_branch(self) -> None:
        encoded = urllib.parse.quote(self.branch, safe="")
        try:
            self.api.request("GET", f"/repos/{self.repository}/git/ref/heads/{encoded}")
            return
        except RuntimeError as exc:
            if not _is_not_found(exc):
                raise

        repo = self.api.request("GET", f"/repos/{self.repository}")
        default_branch = (repo or {}).get("default_branch")
        if not isinstance(default_branch, str) or not default_branch:
            raise ValueError("default branch unavailable")
        default_ref = self.api.request(
            "GET",
            f"/repos/{self.repository}/git/ref/heads/{urllib.parse.quote(default_branch, safe='')}",
        )
        default_sha = ((default_ref or {}).get("object") or {}).get("sha")
        if not isinstance(default_sha, str):
            raise ValueError("default branch SHA unavailable")
        try:
            self.api.request(
                "POST",
                f"/repos/{self.repository}/git/refs",
                {"ref": f"refs/heads/{self.branch}", "sha": default_sha},
            )
        except RuntimeError as exc:
            if "failed: 422" not in str(exc):
                raise

    def read(self, bootstrap: dict[str, Any] | None = None) -> StoredState:
        self._ensure_branch()
        try:
            payload = self.api.request("GET", self._contents_path())
        except RuntimeError as exc:
            if not _is_not_found(exc) or bootstrap is None:
                raise
            created = self.api.request(
                "PUT",
                self._contents_path().split("?", 1)[0],
                {
                    "message": "Bootstrap transactional automation state",
                    "content": base64.b64encode(
                        (json.dumps(bootstrap, indent=2) + "\n").encode("utf-8")
                    ).decode("ascii"),
                    "branch": self.branch,
                },
            )
            content = (created or {}).get("content") or {}
            sha = content.get("sha")
            if not isinstance(sha, str):
                raise ValueError("bootstrap state blob SHA unavailable")
            return StoredState(dict(bootstrap), sha)

        if not isinstance(payload, dict):
            raise ValueError("state file response is invalid")
        encoded = payload.get("content")
        blob_sha = payload.get("sha")
        if not isinstance(encoded, str) or not isinstance(blob_sha, str):
            raise ValueError("state file content or SHA unavailable")
        state = json.loads(base64.b64decode(encoded).decode("utf-8"))
        if not isinstance(state, dict):
            raise ValueError("state file must contain a JSON object")
        return StoredState(state, blob_sha)

    def write(self, state: dict[str, Any], expected_blob_sha: str, *, message: str) -> StoredState:
        encoded_path = urllib.parse.quote(self.path, safe="/")
        response = self.api.request(
            "PUT",
            f"/repos/{self.repository}/contents/{encoded_path}",
            {
                "message": message,
                "content": base64.b64encode(
                    (json.dumps(state, indent=2) + "\n").encode("utf-8")
                ).decode("ascii"),
                "sha": expected_blob_sha,
                "branch": self.branch,
            },
        )
        content = (response or {}).get("content") or {}
        new_sha = content.get("sha")
        if not isinstance(new_sha, str):
            raise ValueError("updated state blob SHA unavailable")
        return StoredState(state, new_sha)


def _issue_snapshot(api: GitHubApi, repository: str, issue_number: int) -> tuple[dict[str, Any], dict[str, Any]]:
    issue = api.request("GET", f"/repos/{repository}/issues/{issue_number}")
    body = (issue or {}).get("body") or ""
    command, _, _ = extract_block(body, COMMAND_START, COMMAND_END)
    state, _, _ = extract_block(body, STATE_START, STATE_END)
    return command, state


def mirror_state(
    api: GitHubApi,
    repository: str,
    issue_number: int,
    state: dict[str, Any],
) -> None:
    current_command, _ = _issue_snapshot(api, repository, issue_number)
    body = render_issue_body(current_command, state)
    api.request("PATCH", f"/repos/{repository}/issues/{issue_number}", {"body": body})


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    issue_command, issue_state = _issue_snapshot(api, repository, args.issue)
    store = StateStore(api, repository, branch=args.state_branch, path=args.state_path)
    stored = store.read(bootstrap=issue_state)

    if args.mirror_only:
        mirror_state(api, repository, args.issue, stored.state)
        return 0

    result = apply_v4_command(
        command=issue_command,
        state=stored.state,
        repository=repository,
        processed_at=datetime.now(timezone.utc),
    )
    if not result.already_processed:
        stored = store.write(
            result.state,
            stored.blob_sha,
            message=f"Record automation command {issue_command.get('commandId', 'unknown')}",
        )
    mirror_state(api, repository, args.issue, stored.state)
    print(
        json.dumps(
            {
                "accepted": result.accepted,
                "reason": result.reason,
                "status": stored.state.get("status"),
                "stateVersion": stored.state.get("version"),
                "stateBranch": args.state_branch,
            },
            sort_keys=True,
        )
    )
    return 0 if result.accepted else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    parser.add_argument("--state-branch", default=STATE_BRANCH)
    parser.add_argument("--state-path", default=STATE_PATH)
    parser.add_argument("--mirror-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except Exception as exc:
        print(f"transactional automation coordinator failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
